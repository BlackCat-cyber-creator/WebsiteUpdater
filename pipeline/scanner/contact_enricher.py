"""
Contact & Social Enrichment Module.
Validates Indonesian contact numbers, prioritizes WhatsApp mobile numbers (08... / 628...),
and filters out PSTN landline office numbers (021, 031, 022, etc.).
Enriches missing or landline-only leads via public social profiles (Instagram, Linktree, Facebook, web search).
"""

import re
import urllib.parse
from typing import Dict, Any, Optional, List
from scrapling.fetchers import Fetcher
from pipeline.scanner.business_scanner import is_indonesian_mobile, is_indonesian_landline


class ContactEnricher:
    """
    Enriches and validates Indonesian contact leads with high-priority mobile WhatsApp filtering.
    """

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8"
        }

    def normalize_wa(self, raw_phone: str) -> Optional[str]:
        """
        Normalizes Indonesian phone number to 628xxxxxxxx format.
        Strictly rejects PSTN landlines (021, 031, etc.) and non-mobile numbers.
        """
        if not raw_phone:
            return None
        
        # Immediate rejection of PSTN landlines
        if is_indonesian_landline(raw_phone):
            return None

        digits = re.sub(r"[^\d]", "", raw_phone)
        if not digits:
            return None

        if digits.startswith("08"):
            digits = "62" + digits[1:]
        elif digits.startswith("8"):
            digits = "62" + digits
        elif digits.startswith("6208"):
            digits = "62" + digits[3:]
        elif digits.startswith("628"):
            pass
        else:
            return None

        # Indonesian mobile/WA numbers: 11 to 15 digits
        if digits.startswith("628") and 11 <= len(digits) <= 15:
            return digits
        return None

    def enrich_from_social_bio(self, business_name: str, city: str = "") -> Dict[str, Any]:
        """
        Searches public social pages (Instagram, Linktree, Facebook)
        and Google search snippets to discover authentic owner WhatsApp mobile numbers.
        """
        enriched = {
            "whatsapp": "",
            "email": "",
            "social_profiles": [],
            "source": "social_enrichment"
        }

        search_query = f"{business_name} {city} (instagram OR facebook OR linktr.ee OR whatsapp OR wa.me)"
        encoded = urllib.parse.quote_plus(search_query)
        search_url = f"https://www.google.co.id/search?q={encoded}&hl=id&gl=id"

        try:
            import requests
            r = requests.get(search_url, headers=self.headers, timeout=12)
            if r.status_code != 200:
                return enriched
            html = r.text

            # 1. Direct WhatsApp links in search snippets (wa.me/628... or api.whatsapp.com)
            wa_links = re.findall(r'(?:wa\.me|api\.whatsapp\.com/send\?phone=)(\d+)', html, re.IGNORECASE)
            for w in wa_links:
                norm = self.normalize_wa(w)
                if norm and not enriched["whatsapp"]:
                    enriched["whatsapp"] = norm
                    break

            # 2. Indonesian mobile phone numbers in text (08xx or +628xx)
            if not enriched["whatsapp"]:
                raw_phones = re.findall(r'(?:\+62|62|0)8[0-9\s\-\.\(\)]{8,14}', html)
                for p in raw_phones:
                    norm = self.normalize_wa(p)
                    if norm:
                        enriched["whatsapp"] = norm
                        break

            # 3. Emails in snippets
            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,7}\b', html)
            for e in emails:
                cl = e.lower()
                if not any(d in cl for d in ["example.com", "google", "wix", "duckduckgo"]):
                    if not enriched["email"]:
                        enriched["email"] = cl

            # 4. Social profile links
            links = re.findall(r'href=[\'"]?(https?://[^\'" >]+)', html)
            for l in links:
                if any(k in l for k in ["instagram.com/", "linktr.ee/", "facebook.com/"]):
                    if "uddg=" in l:
                        m = re.search(r'uddg=([^&]+)', l)
                        if m:
                            l = urllib.parse.unquote(m.group(1))
                    if l not in enriched["social_profiles"] and len(enriched["social_profiles"]) < 3:
                        enriched["social_profiles"].append(l)

            # 5. If Linktree found, parse Linktree page for direct wa.me
            for prof in enriched["social_profiles"]:
                if "linktr.ee" in prof and not enriched["whatsapp"]:
                    try:
                        lt_res = Fetcher.get(prof, stealthy_headers=True, timeout=10)
                        lt_html = lt_res.text or ""
                        lt_wa = re.findall(r'(?:wa\.me|api\.whatsapp\.com/send\?phone=)(\d+)', lt_html, re.IGNORECASE)
                        for lw in lt_wa:
                            norm = self.normalize_wa(lw)
                            if norm:
                                enriched["whatsapp"] = norm
                                break
                    except Exception:
                        pass

        except Exception:
            pass

        return enriched

    def enrich_contact(self, business_name: str, city: str = "", current_phone: str = "") -> Dict[str, Any]:
        """
        Evaluates current phone. If it's already a valid mobile number (628...), keeps it.
        If it's a landline (021, 031, etc.) or missing, automatically enriches via social bio.
        """
        # If already a valid mobile number
        norm = self.normalize_wa(current_phone)
        if norm:
            return {
                "whatsapp": norm,
                "email": "",
                "is_mobile": True,
                "source": "direct"
            }

        # If phone is landline or empty, search social bio
        enriched = self.enrich_from_social_bio(business_name, city)
        return {
            "whatsapp": enriched.get("whatsapp", ""),
            "email": enriched.get("email", ""),
            "is_mobile": bool(enriched.get("whatsapp")),
            "source": enriched.get("source", "social_enrichment")
        }

    def crawl_website_contacts(self, website_url: str) -> Dict[str, Any]:
        """
        Crawls a business website directly to extract authentic emails, social profiles
        (Instagram, Facebook, LinkedIn, TikTok, YouTube), and WhatsApp links.
        100% free, local, and requires zero external paid API subscriptions.
        """
        contacts = {
            "whatsapp": "",
            "email": "",
            "social_profiles": [],
            "source": "website_crawl"
        }
        if not website_url or not website_url.startswith("http"):
            return contacts

        try:
            import requests
            r = requests.get(website_url, headers=self.headers, timeout=8, verify=False)
            if r.status_code != 200:
                return contacts
            html = r.text

            # 1. Extract Emails
            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,7}\b', html)
            for e in emails:
                cl = e.lower()
                # Exclude image files, generic fonts, web assets
                if any(cl.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif", ".js", ".css"]):
                    continue
                if not any(ign in cl for ign in ["example.com", "wixpress", "sentry", "bootstrap", "google", "schema.org", "wix.com"]):
                    contacts["email"] = cl
                    break

            # 2. Extract Social Profiles
            social_patterns = [
                r'https?://(?:www\.)?instagram\.com/[A-Za-z0-9_.]+',
                r'https?://(?:www\.)?facebook\.com/[A-Za-z0-9_.]+',
                r'https?://(?:www\.)?linkedin\.com/company/[A-Za-z0-9_-]+',
                r'https?://(?:www\.)?tiktok\.com/@[A-Za-z0-9_.]+',
                r'https?://(?:www\.)?youtube\.com/(?:c/|channel/|@)[A-Za-z0-9_-]+'
            ]
            for pat in social_patterns:
                found_links = re.findall(pat, html, re.IGNORECASE)
                for flink in found_links:
                    clean_l = flink.rstrip("/?,.;")
                    # Exclude share URLs or generic intents
                    if not any(ign in clean_l.lower() for ign in ["sharer", "share.php", "intent", "login"]):
                        if clean_l not in contacts["social_profiles"]:
                            contacts["social_profiles"].append(clean_l)

            # 3. Extract WhatsApp
            wa_links = re.findall(r'(?:wa\.me/|api\.whatsapp\.com/send\?phone=)(\d+)', html, re.IGNORECASE)
            for w in wa_links:
                norm = self.normalize_wa(w)
                if norm:
                    contacts["whatsapp"] = norm
                    break

            # 4. Check if enterprise corporate or modern SPA
            html_lower = html.lower()
            is_corporate = any(k in html_lower for k in [
                "branch list", "our branches", "kantor cabang kami", "daftar cabang kami",
                "10 major cities", "tersebar di seluruh indonesia", "investor relations",
                "annual report", "tata kelola perusahaan"
            ])
            is_spa = any(k in html for k in ["__NUXT__", "__NEXT_DATA__", "data-capo", "react-root", "_next/static"])

            contacts["is_corporate"] = is_corporate
            contacts["is_spa"] = is_spa

        except Exception:
            pass

        return contacts



# Class alias for backward compatibility
AgentReachContactEnricher = ContactEnricher

