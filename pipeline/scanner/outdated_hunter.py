"""
Outdated Website Hunter Engine for Indonesian B2B Businesses (Jalur B Revitalizer).
Hunts established Indonesian commercial domains (.co.id, .id, .com) that have legacy,
unresponsive, or outdated websites in urgent need of modernization.

Utilizes:
1. Targeted Indonesian SERP Dorking (Copyright year footprints, legacy CMS, non-responsive indicators)
2. Indonesian B2B Directory Hubs (Indonetwork, Indotrading company footprints)
3. Deep HTML technical audit for modernization gap signals
4. Contact validation via ContactValidator (identifying mobile WA vs PSTN landline vs email)
"""

import os
import re
import base64
import urllib.parse
from typing import Dict, Any, List, Optional
import requests
from scrapling.fetchers import Fetcher

from pipeline.scanner.contact_validator import ContactValidator
from pipeline.scanner.niche_matrix import NicheMatrix, EXCLUDED_RETAIL_KEYWORDS

EXCLUDED_SEARCH_DOMAINS = [
    # Search engines & Big Tech
    "google.", "bing.", "yahoo.", "msn.", "microsoft.", "wikipedia.", "github.", "youtube.",
    # Social media
    "facebook.", "instagram.", "tiktok.", "twitter.", "x.com", "linkedin.", "pinterest.",
    # Indonesian News & Media Conglomerates
    "detik.", "kompas.", "tribunnews.", "liputan6.", "merdeka.", "idntimes.", "kumparan.",
    "tempo.co", "katadata.", "bisnis.com", "kontan.co.id", "cnbcindonesia.", "cnnindonesia.",
    # Indonesian Marketplaces & Delivery Superapps
    "tokopedia.", "shopee.", "bukalapak.", "lazada.", "blibli.", "olx.", "gojek.", "grab.",
    "traveloka.", "tiket.", "sicepat.", "jne.", "jtexpress.", "tiki.", "posindonesia.", "wahana.",
    # Free blogging platforms
    "wordpress.com", "blogspot.com", "wixsite.com", "weebly.com", "medium.com", "site123.me",
    # Government & Educational
    ".go.id", ".mil.id", ".ac.id", ".sch.id"
]

FOREIGN_TLDS = [
    ".jp", ".cn", ".ru", ".kr", ".vn", ".th", ".my", ".in", ".de", ".fr",
    ".uk", ".br", ".tw", ".it", ".es", ".pl", ".nl", ".au", ".ca"
]

INDONESIAN_MARKERS = [
    "indonesia", "jakarta", "surabaya", "bandung", "medan", "semarang",
    "cikarang", "karawang", "bekasi", "tangerang", "sidoarjo", "balikpapan",
    "samarinda", "batam", "makassar", "palembang", "pekanbaru", "jawa",
    "hubungi", "kontak kami", "tentang kami", "produk", "layanan", "pt.", "cv.", "ud."
]


class OutdatedWebsiteHunter:
    """
    Autonomous hunter for outdated Indonesian commercial websites (Track B Modernization).
    """

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8"
        }

    def _decode_bing_u(self, u_val: str) -> str:
        """Decodes base64-encoded Bing search destination URL."""
        try:
            if u_val.startswith("a1"):
                raw = u_val[2:]
                raw += "=" * (-len(raw) % 4)
                return base64.urlsafe_b64decode(raw).decode("utf-8", errors="ignore")
        except Exception:
            pass
        return ""

    def search_engine_links(self, query: str, max_links: int = 15) -> List[str]:
        """Executes stealth search engine query and harvests unique Indonesian domains."""
        encoded = urllib.parse.quote_plus(query)
        bing_url = f"https://www.bing.com/search?q={encoded}&count=25"
        found = []
        seen_domains = set()

        try:
            resp = requests.get(bing_url, headers=self.headers, timeout=12)
            if resp.status_code == 200:
                raw_matches = re.findall(r'(?:[?&]|&amp;)u=([^&"\']+)', resp.text)
                for m in raw_matches:
                    decoded = self._decode_bing_u(m)
                    if decoded and decoded.startswith("http"):
                        parsed = urllib.parse.urlparse(decoded)
                        dom = parsed.netloc.lower().replace("www.", "")
                        # Reject excluded and foreign domains
                        if any(ex in dom for ex in EXCLUDED_SEARCH_DOMAINS):
                            continue
                        if any(dom.endswith(tld) or f"{tld}/" in decoded for tld in FOREIGN_TLDS):
                            continue
                        if "." in dom and dom not in seen_domains:
                            seen_domains.add(dom)
                            clean_url = f"{parsed.scheme}://{parsed.netloc}"
                            found.append(clean_url)
                            if len(found) >= max_links:
                                break
        except Exception as e:
            print(f"[!] Warning search engine query error: {e}")

        return found

    def inspect_and_audit_website(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Visits candidate website, checks for outdated indicators, extracts contacts,
        and evaluates eligibility for Track B Modernization.
        """
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url

        try:
            parsed = urllib.parse.urlparse(url)
            domain = parsed.netloc.lower().replace("www.", "")
        except Exception:
            return None

        if any(ex in domain for ex in EXCLUDED_SEARCH_DOMAINS):
            return None
        if any(domain.endswith(tld) for tld in FOREIGN_TLDS):
            return None

        try:
            res = Fetcher.get(url, stealthy_headers=True, timeout=12)
            if res.status not in [200, 301, 302]:
                return None

            if hasattr(res, "body") and res.body:
                html = res.body.decode(getattr(res, "encoding", "utf-8") or "utf-8", errors="ignore")
            else:
                html = res.text or ""

            if len(html) < 150:
                return None

            title = res.css("title::text").get() or ""
            t_low = title.lower().strip()
            # Filter non-Latin Asian alphabets (Japanese, Chinese, Cyrillic)
            if re.search(r'[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff\u0400-\u04ff]', title):
                return None

            # Filter bot challenges / cloudflare / parking pages
            if any(inv in t_low for inv in ["just a moment", "cloudflare", "404 not found", "access denied", "domain expired", "parked"]):
                return None

            # Filter retail excluded terms
            if NicheMatrix.is_excluded_business(title):
                return None

            # Authenticity check: if not .id / .co.id, verify Indonesian markers in text
            is_dot_id = any(domain.endswith(ext) for ext in [".id", ".co.id", ".biz.id", ".net.id"])
            if not is_dot_id:
                html_low = html.lower()[:5000]
                if not any(marker in html_low for marker in INDONESIAN_MARKERS):
                    return None

            meta_desc = res.css('meta[name="description"]::attr(content)').get() or ""

            # -------------------------------------------------------------
            # Extract Technical Outdated Signals
            # -------------------------------------------------------------
            outdated_signals = []

            # 1. Viewport / Mobile Responsiveness
            has_viewport = bool(res.css('meta[name="viewport"]'))
            if not has_viewport:
                outdated_signals.append("Non-responsive: Belum memiliki viewport layar sentuh smartphone")

            # 2. Google Schema.org structured data
            has_schema = "application/ld+json" in html
            if not has_schema:
                outdated_signals.append("SEO Kritis: Hilang Google Schema.org LocalBusiness JSON-LD")

            # 3. Old Copyright year detection
            copy_match = re.search(r'(?:copyright|hak cipta|©)\s*(?:[a-zA-Z\s,]+)?(200\d|201\d|202[0-1])\b', html, re.IGNORECASE)
            if copy_match:
                year = copy_match.group(1)
                outdated_signals.append(f"Hak Cipta Kedaluwarsa: Terakhir diperbarui tahun {year}")

            # 4. Legacy CMS Frameworks
            if "wp-content" in html:
                outdated_signals.append("Legacy CMS: Menggunakan instalasi WordPress lawas yang rentan")
            elif "joomla" in html.lower():
                outdated_signals.append("Legacy CMS: Menggunakan framework Joomla lawas")
            elif "opencart" in html.lower():
                outdated_signals.append("Legacy CMS: Menggunakan framework OpenCart lawas")

            # 5. Non-SSL Protocol
            if url.startswith("http://"):
                outdated_signals.append("Keamanan Web: Belum menggunakan enkripsi SSL/HTTPS otomatis")

            # 6. Legacy Tables / Flash / Deprecated Tags
            if "<table" in html.lower() and html.lower().count("<table") > 3:
                outdated_signals.append("Desain Usang: Menggunakan arsitektur layout table berbasis era 2000-an")

            # 7. Metadata completeness
            if len(title) < 18:
                outdated_signals.append("SEO Dasar: Judul halaman terlalu pendek dan minim kata kunci")
            if not meta_desc:
                outdated_signals.append("SEO Dasar: Belum memiliki deskripsi meta pencarian Google")

            # -------------------------------------------------------------
            # Extract Contact Information
            # -------------------------------------------------------------
            # Extract WhatsApp Links
            wa_candidates = set()
            wa_links = re.findall(r'(?:wa\.me/|api\.whatsapp\.com/send\?phone=)(\+?62\d+|08\d+|\d{10,14})', html, re.IGNORECASE)
            for w in wa_links:
                wa_candidates.add(w)

            # Extract Phone Numbers from HTML text
            raw_phones = re.findall(r'(?:\+62|62|0)(?:2[1-9]|3[1-9]|4[1-9]|5[1-9]|6[1-9]|7[1-9]|8[0-9])[0-9\s\-\.\(\)]{6,14}', html)
            
            # Extract Business Emails
            emails = set()
            mailtos = re.findall(r'mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})', html, re.IGNORECASE)
            for m in mailtos:
                if ContactValidator.validate_email(m):
                    emails.add(m.strip().lower())

            raw_emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,7}\b', html)
            for e in raw_emails:
                if ContactValidator.validate_email(e):
                    emails.add(e.strip().lower())

            # Prioritize contact selection
            primary_phone = list(wa_candidates)[0] if wa_candidates else (raw_phones[0] if raw_phones else "")
            primary_email = list(emails)[0] if emails else ""

            # Validate contact via ContactValidator cascade
            cascade = ContactValidator.evaluate_contact_cascade(primary_phone, primary_email)
            if cascade["primary_channel"] == "discard":
                # If primary phone failed, check if other phones pass
                for alt_p in raw_phones[1:5]:
                    alt_cascade = ContactValidator.evaluate_contact_cascade(alt_p, primary_email)
                    if alt_cascade["primary_channel"] != "discard":
                        primary_phone = alt_p
                        cascade = alt_cascade
                        break

            # Clean business name
            biz_name = title.split("|")[0].split("-")[0].split("–")[0].strip() or domain

            return {
                "business_name": biz_name,
                "domain": domain,
                "website_url": url,
                "title": title.strip(),
                "meta_description": meta_desc.strip(),
                "whatsapp": cascade["phone_info"].get("normalized_e164", "") if cascade["phone_info"]["is_mobile"] else "",
                "phone": cascade["phone_info"].get("normalized_local", primary_phone),
                "phone_type": cascade["phone_info"]["type"],
                "email": cascade.get("email", primary_email),
                "primary_channel": cascade["primary_channel"],
                "fallback_tier": cascade["fallback_tier"],
                "contact_notes": cascade["notes"],
                "outdated_signals": outdated_signals,
                "modernization_score_est": max(30, 95 - (len(outdated_signals) * 15)),
                "track": "track_b_modernize"
            }

        except Exception as e:
            return None

    def hunt_outdated_leads(
        self,
        limit: int = 5,
        target_category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Main hunter workflow:
        1. Generates targeted high-value B2B dork queries
        2. Harvests search links
        3. Inspects candidate sites for outdated signals
        4. Validates contact points and assigns outreach channels
        """
        print(f"\n[JALUR B HUNTER] Memburu website B2B Indonesia lama/outdated...")
        print(f"[*] Target Kategori : {target_category or 'Rotasi Niche Berdaya Beli Tinggi'}")
        print(f"[*] Kuota Target   : {limit} website")

        dork_queries = NicheMatrix.get_dork_queries_for_track_b(limit=max(6, limit * 2), target_category=target_category)
        candidates = []
        seen_domains = set()

        for q in dork_queries:
            if len(candidates) >= limit:
                break
            print(f"[*] Dorking SERP: {q}")
            links = self.search_engine_links(q, max_links=10)

            for target_url in links:
                if len(candidates) >= limit:
                    break
                try:
                    dom = urllib.parse.urlparse(target_url).netloc.lower().replace("www.", "")
                    if dom in seen_domains:
                        continue
                    seen_domains.add(dom)
                except Exception:
                    continue

                lead = self.inspect_and_audit_website(target_url)
                if lead and lead.get("primary_channel") != "discard":
                    ch_label = lead["primary_channel"].upper()
                    print(f"  [+] [JALUR B DITEMUKAN] {lead['business_name']} ({lead['domain']}) | Saluran: {ch_label} | {len(lead['outdated_signals'])} Celah Teknis")
                    candidates.append(lead)

        print(f"[+] Berhasil mengumpulkan {len(candidates)} website lama siap modernisasi (Jalur B).\n")
        return candidates
