"""
Indonesian Business & Lead Scanner Module.
Scans businesses across Indonesian markets and cities, extracts authentic contact information
(WhatsApp numbers, business emails, physical addresses), and evaluates website modernization needs.
Powered by Scrapling with stealth headers and adaptive parsing.
"""

import re
import urllib.parse
from typing import Dict, Any, List, Optional
from scrapling.fetchers import Fetcher


class IndonesianBusinessScanner:
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7"
        }

    def normalize_indonesian_phone(self, raw_phone: str) -> Optional[str]:
        """Normalizes Indonesian phone/WhatsApp numbers to international 628xxxxxxxx format."""
        if not raw_phone:
            return None
        # Extract digits
        digits = re.sub(r"[^\d]", "", raw_phone)
        if not digits:
            return None
        
        # Convert local 08xx to 628xx
        if digits.startswith("08"):
            digits = "62" + digits[1:]
        elif digits.startswith("8"):
            digits = "62" + digits
        elif digits.startswith("6208"):
            digits = "62" + digits[3:]
        elif digits.startswith("628"):
            pass
        elif digits.startswith("021") or digits.startswith("022") or digits.startswith("031"):
            # Landline
            digits = "62" + digits[1:]
        else:
            if len(digits) < 10 or len(digits) > 15:
                return None
            
        # Indonesian mobile numbers (628...) must be 11 to 14 digits long
        if digits.startswith("628"):
            if 11 <= len(digits) <= 14:
                return digits
            return None

        # Landlines (6221..., 6231...)
        if len(digits) >= 10 and len(digits) <= 13:
            return digits
        return None

    def extract_contacts_from_html(self, html: str, url: str) -> Dict[str, Any]:
        """Extracts email, phone, and WhatsApp numbers from website HTML."""
        emails = set()
        phones = set()
        whatsapps = set()

        # 1. WhatsApp link patterns (wa.me, api.whatsapp.com)
        wa_links = re.findall(r'(?:wa\.me|api\.whatsapp\.com/send\?phone=)(\d+)', html, re.IGNORECASE)
        for w in wa_links:
            norm = self.normalize_indonesian_phone(w)
            if norm:
                whatsapps.add(norm)

        # 2. Mailto links
        mailtos = re.findall(r'mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})', html, re.IGNORECASE)
        for m in mailtos:
            clean_email = m.strip().lower()
            if not any(clean_email.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif"]):
                emails.add(clean_email)

        # 3. Plaintext emails
        raw_emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,7}\b', html)
        for e in raw_emails:
            clean = e.strip().lower()
            # Ignore dummy or library emails
            if not any(d in clean for d in ["example.com", "domain.com", "email.com", "wix.com", "wordpress"]):
                if not any(clean.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif"]):
                    emails.add(clean)

        # 4. Indonesian phone numbers in text
        raw_phones = re.findall(r'(?:\+62|62|0)8[0-9\s\-\.\(\)]{8,14}', html)
        for p in raw_phones:
            norm = self.normalize_indonesian_phone(p)
            if norm:
                phones.add(norm)
                # In Indonesia, 628xx numbers are almost always WhatsApp active
                if norm.startswith("628"):
                    whatsapps.add(norm)

        primary_wa = list(whatsapps)[0] if whatsapps else (list(phones)[0] if phones else "")
        primary_email = list(emails)[0] if emails else ""

        return {
            "primary_whatsapp": primary_wa,
            "all_whatsapps": list(whatsapps),
            "primary_email": primary_email,
            "all_emails": list(emails),
            "all_phones": list(phones)
        }

    def inspect_website(self, url: str) -> Optional[Dict[str, Any]]:
        """Visits a candidate website and gathers metadata, contacts, and modernization indicators."""
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url

        domain = urllib.parse.urlparse(url).netloc.lower().replace("www.", "")

        try:
            res = Fetcher.get(url, stealthy_headers=True, timeout=12)
            if res.status != 200:
                return None
            
            if hasattr(res, "body") and res.body:
                html = res.body.decode(getattr(res, "encoding", "utf-8") or "utf-8", errors="ignore")
            else:
                html = res.text or ""

            if len(html) < 100:
                return None

            title = res.css("title::text").get() or ""
            meta_desc = res.css('meta[name="description"]::attr(content)').get() or ""
            contacts = self.extract_contacts_from_html(html, url)

            # Modernization gaps indicators
            has_viewport = bool(res.css('meta[name="viewport"]'))
            has_schema = "application/ld+json" in html
            has_wa_button = bool(contacts["primary_whatsapp"])
            title_length = len(title)

            outdated_signals = []
            if not has_viewport:
                outdated_signals.append("Non-responsive / missing mobile viewport")
            if not has_schema:
                outdated_signals.append("Missing Google Schema.org structured data")
            if title_length < 20:
                outdated_signals.append("Title too short or lacking commercial keywords")
            if not meta_desc:
                outdated_signals.append("Missing Google meta description")
            if "wp-content" in html:
                outdated_signals.append("Legacy CMS framework detected")

            return {
                "business_name": title.split("|")[0].split("-")[0].strip() or domain,
                "website_url": url,
                "domain": domain,
                "title": title.strip(),
                "meta_description": meta_desc.strip(),
                "whatsapp": contacts["primary_whatsapp"],
                "all_whatsapps": contacts["all_whatsapps"],
                "email": contacts["primary_email"],
                "all_emails": contacts["all_emails"],
                "outdated_signals": outdated_signals,
                "modernization_score_est": max(30, 95 - (len(outdated_signals) * 15))
            }
        except Exception as e:
            return None

    def search_businesses_by_query(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Discovers candidate Indonesian business websites from search queries.
        Supports Indonesian localized Google queries and directories.
        """
        results = []
        seen_domains = set()

        # Build search queries
        encoded_q = urllib.parse.quote_plus(query)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8"
        }
        
        found_links = []
        import requests, base64

        def decode_bing_link(u_val):
            try:
                if u_val.startswith('a1'):
                    raw = u_val[2:]
                    raw += '=' * (-len(raw) % 4)
                    return base64.urlsafe_b64decode(raw).decode('utf-8', errors='ignore')
            except Exception:
                pass
            return ""

        # Query Bing Search (reliable, fast, no JS challenge)
        try:
            bing_url = f"https://www.bing.com/search?q={encoded_q}&count=20"
            r = requests.get(bing_url, headers=headers, timeout=10)
            if r.status_code == 200:
                raw_matches = re.findall(r'(?:[?&]|&amp;)u=([^&"\']+)', r.text)
                for match in raw_matches:
                    decoded = decode_bing_link(match)
                    if decoded and decoded.startswith("http"):
                        parsed = urllib.parse.urlparse(decoded)
                        dom = parsed.netloc.lower().replace("www.", "")
                        excluded = [
                            # Big tech & search engines
                            "bing.", "msn.", "microsoft.", "google.", "yahoo.", "wikipedia.", "github.",
                            # Social media & video
                            "youtube.", "facebook.", "instagram.", "twitter.", "linkedin.", "tiktok.", "pinterest.",
                            # E-commerce marketplaces
                            "tokopedia.", "shopee.", "bukalapak.", "lazada.", "blibli.", "zalora.", "olx.",
                            # Giant National Couriers & Mass Delivery (Excluded: 100+ in-house IT, bureaucratic tender)
                            "sicepat.", "jne.", "jtexpress.", "jet.co.id", "jtcargo.", "tiki.", "posindonesia.", "wahana.",
                            "lionparcel.", "anteraja.", "ninjaexpress.", "ninjaxpress.", "paxel.", "idexpress.",
                            "sentralcargo.", "dakotacargo.", "sapx.id", "sap-express.", "spx.co.id", "kargo.tech",
                            "lalamove.", "deliveree.", "borzo.", "fedex.", "dhl.", "ups.",
                            # Tech Unicorns, OTA, & Superapps
                            "traveloka.", "tiket.", "gojek.", "grab.", "kredivo.", "akulaku.", "dana.id", "ovo.id",
                            # National Banks & Telco Conglomerates
                            "bca.co.id", "mandiri.", "bni.co.id", "bri.co.id", "cimbniaga.", "danamon.", "permata.",
                            "telkom.", "telkomsel.", "indosat.", "xl.co.id", "smartfren.",
                            # Healthcare & Lab Conglomerates
                            "prodia.co.id", "siloam", "hermina", "mitrakeluarga", "mayapada", "halodoc.", "alodokter.", "klikdokter.",
                            # Property Portals & Real Estate Aggregators
                            "rumah123.", "99.co", "lamudi.", "sewa-apartemen.", "mamikos.", "rumah.com",
                            # SaaS, ERP, & Generic Article/Blog Hubs
                            "jurnal.id", "mekari.", "hashmicro.", "accurate.id", "kledo.", "majoo.id", "bee.id",
                            "scaleocean.", "dealls.", "mas-software.",
                            # Free Blog Platforms
                            "wordpress.com", "blogspot.com", "wixsite.com", "weebly.com",
                            # Media, news portals, & job aggregators
                            "kompas.", "detik.", "tribunnews.", "liputan6.", "merdeka.", "idntimes.", "kumparan.",
                            "tempo.co", "katadata.", "glints.", "jobstreet.", "karir.", "brainly.", "bisnis.com", "kontan.co.id",
                            # Government & Educational institutions
                            ".go.id", ".mil.id", ".ac.id", ".sch.id"
                        ]
                        if not any(ex in dom for ex in excluded) and "." in dom:
                            clean_url = f"{parsed.scheme}://{parsed.netloc}"
                            if dom not in seen_domains:
                                seen_domains.add(dom)
                                found_links.append(clean_url)
        except Exception:
            pass

        # Inspect found candidate websites (prioritizing mid-tier businesses with valid WhatsApp contacts)
        for target_url in found_links:
            if len(results) >= limit:
                break
            inspected = self.inspect_website(target_url)
            if inspected and inspected.get("whatsapp"):
                # Qualified mid-tier business with active mobile WhatsApp
                results.append(inspected)

        # Fallback: if not enough with direct WA, take other valid candidates
        if len(results) < limit:
            for target_url in found_links:
                if len(results) >= limit:
                    break
                if any(r["website_url"] == target_url for r in results):
                    continue
                inspected = self.inspect_website(target_url)
                if inspected:
                    results.append(inspected)

        return results


if __name__ == "__main__":
    scanner = IndonesianBusinessScanner()
    # Test contact normalizer
    print("Normalizer test:")
    print("0811572228 ->", scanner.normalize_indonesian_phone("0811572228"))
    print("+62 812-3456-7890 ->", scanner.normalize_indonesian_phone("+62 812-3456-7890"))
    
    # Test inspect suncargo
    print("\nInspecting suncargo.sunfrozencargo.com:")
    info = scanner.inspect_website("https://suncargo.sunfrozencargo.com")
    if info:
        print("Business:", info["business_name"])
        print("WhatsApp:", info["whatsapp"])
        print("Signals:", info["outdated_signals"])
