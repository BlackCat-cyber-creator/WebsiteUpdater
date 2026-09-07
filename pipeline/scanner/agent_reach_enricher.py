"""
Social & Contact Enrichment Module powered by Agent-Reach & Playwright.
Enriches business leads with missing WhatsApp, email, and social profiles by inspecting
Instagram, Facebook, LinkedIn, and Linktree bios without paid API fees.
"""

import re
import urllib.parse
from typing import Dict, Any, Optional
from scrapling.fetchers import Fetcher


class AgentReachContactEnricher:
    def __init__(self):
        pass

    def normalize_wa(self, raw_phone: str) -> Optional[str]:
        digits = re.sub(r"[^\d]", "", raw_phone)
        if not digits:
            return None
        if digits.startswith("08"):
            digits = "62" + digits[1:]
        elif digits.startswith("8"):
            digits = "62" + digits
        elif digits.startswith("6208"):
            digits = "62" + digits[3:]
        if len(digits) >= 10 and len(digits) <= 15:
            return digits
        return None

    def enrich_from_social_bio(self, business_name: str, city: str = "") -> Dict[str, Any]:
        """
        Searches public social pages and bio aggregators (Instagram, Linktree, Facebook)
        for the given business to find missing WhatsApp or email.
        """
        enriched = {
            "whatsapp": "",
            "email": "",
            "social_profiles": [],
            "source": "social_enrichment"
        }

        search_query = f"{business_name} {city} (instagram OR facebook OR linktr.ee OR whatsapp)"
        encoded = urllib.parse.quote_plus(search_query)
        search_url = f"https://www.google.co.id/search?q={encoded}&hl=id&gl=id"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        }

        try:
            import requests
            r = requests.get(search_url, headers=headers, timeout=12)
            if r.status_code != 200:
                return enriched
            html = r.text

            # Check for direct WhatsApp links in search snippets
            wa_links = re.findall(r'(?:wa\.me|api\.whatsapp\.com/send\?phone=)(\d+)', html, re.IGNORECASE)
            for w in wa_links:
                norm = self.normalize_wa(w)
                if norm and not enriched["whatsapp"]:
                    enriched["whatsapp"] = norm

            # Check for emails in snippets
            emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,7}\b', html)
            for e in emails:
                cl = e.lower()
                if not any(d in cl for d in ["example.com", "duckduckgo", "google", "wix"]):
                    if not enriched["email"]:
                        enriched["email"] = cl

            # Check for Instagram or Linktree handles
            links = re.findall(r'href=[\'"]?(https?://[^\'" >]+)', html)
            for l in links:
                if "instagram.com/" in l or "linktr.ee/" in l or "facebook.com/" in l:
                    # Clean redirect
                    if "uddg=" in l:
                        m = re.search(r'uddg=([^&]+)', l)
                        if m:
                            l = urllib.parse.unquote(m.group(1))
                    if l not in enriched["social_profiles"] and len(enriched["social_profiles"]) < 3:
                        enriched["social_profiles"].append(l)

            # If we found a Linktree link, inspect it directly
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


if __name__ == "__main__":
    enricher = AgentReachContactEnricher()
    print("Testing social enrichment for 'CV. SUNCARGO'...")
    res = enricher.enrich_from_social_bio("SUNCARGO", "Pontianak")
    print("Enrichment Result:", res)
