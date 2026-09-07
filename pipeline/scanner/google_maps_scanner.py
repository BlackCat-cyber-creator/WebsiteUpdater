"""
Google Maps Business Scanner & Qualified SME Harvester.
Scrapes local Indonesian businesses directly from Google Maps, extracts authentic
contact information (WhatsApp, Website, Phone, Physical Address), and filters specifically
for developing small-to-medium businesses ($100 budget sweet spot: 5 to 1,000 reviews).
"""

import os
import re
import sys
import time
import urllib.parse
from typing import Dict, Any, List, Optional
from playwright.sync_api import sync_playwright

from pipeline.scanner.business_scanner import IndonesianBusinessScanner

# Enterprise, marketplaces, and directory aggregators to discard immediately
EXCLUDED_MAPS_DOMAINS = [
    "google.", "facebook.com", "instagram.com", "tiktok.com", "youtube.com",
    "tokopedia.com", "shopee.co.id", "lazada.co.id", "bukalapak.com", "blibli.com", "olx.co.id",
    "jne.co.id", "sicepat.com", "jtexpress.co.id", "tiki.id", "posindonesia.co.id", "wahana.com",
    "halodoc.com", "alodokter.com", "klikdokter.com", "rumah123.com", "99.co", "lamudi.co.id",
    "traveloka.com", "tiket.com", "gojek.com", "grab.com", "indonetwork.co.id", "yellowpages.co.id"
]


class GoogleMapsBusinessScanner:
    def __init__(self):
        self.biz_scanner = IndonesianBusinessScanner()

    def _parse_review_count(self, rating_text: str) -> int:
        """Extracts integer review count from strings like '4,8 (51)' or '4.5 (1.234)'."""
        m = re.search(r'\(([\d\.\,]+)\)', rating_text)
        if m:
            raw = m.group(1).replace(".", "").replace(",", "")
            try:
                return int(raw)
            except ValueError:
                return 0
        return 0

    def search_local_businesses(
        self,
        query: str,
        limit: int = 5,
        min_reviews: int = 3,
        max_reviews: int = 2000
    ) -> List[Dict[str, Any]]:
        """
        Searches Google Maps for local developing businesses.
        Filters specifically for active SMEs (review count between min_reviews and max_reviews),
        extracts valid website URLs, and audits SEO/mobile gaps.
        """
        print(f"\n[GMAPS SCANNER] Mencari bisnis berkembang di Google Maps untuk: '{query}'...")
        encoded = urllib.parse.quote_plus(query)
        maps_url = f"https://www.google.com/maps/search/{encoded}"

        candidates = []

        with sync_playwright() as p:
            browser = p.chromium.launch(channel="msedge", headless=True)
            page = browser.new_page(
                locale="id-ID",
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
            )
            try:
                page.goto(maps_url, timeout=45000)
                time.sleep(3)

                # Wait for results
                page.wait_for_selector('div[role="feed"], div[role="article"], a[href*="/maps/place/"]', timeout=20000)

                # Scroll down results feed 2-3 times to load more items
                feed = page.query_selector('div[role="feed"]')
                if feed:
                    for _ in range(2):
                        feed.evaluate('el => el.scrollBy(0, 1000)')
                        time.sleep(1.5)

                cards = page.query_selector_all('a[href*="/maps/place/"]')
                print(f"[*] Ditemukan {len(cards)} listing lokasi di Google Maps. Memeriksa detail bisnis...")

                seen_names = set()

                for idx, card in enumerate(cards):
                    if len(candidates) >= limit:
                        break

                    try:
                        raw_name = card.get_attribute("aria-label") or card.inner_text().split("\n")[0].strip()
                        if not raw_name or raw_name in seen_names:
                            continue
                        seen_names.add(raw_name)

                        # Click card to open detail pane
                        card.click()
                        time.sleep(2.0)

                        # Extract website
                        web_el = page.query_selector('a[data-item-id="authority"], a[aria-label*="Situs Web"], a[aria-label*="Website"]')
                        website_url = web_el.get_attribute("href") if web_el else ""

                        # Extract phone & rating
                        phone_el = page.query_selector('button[data-item-id*="phone"], button[aria-label*="Telepon"]')
                        raw_phone = ""
                        if phone_el:
                            aria_p = phone_el.get_attribute("aria-label") or ""
                            raw_phone = aria_p.replace("Telepon:", "").replace("Phone:", "").strip()
                            if not raw_phone:
                                raw_phone = phone_el.inner_text().strip()

                        rating_el = page.query_selector('div.F7nice, span.ceNzKf')
                        rating_text = rating_el.inner_text().replace("\n", " ").strip() if rating_el else ""
                        review_count = self._parse_review_count(rating_text)

                        # Filter: SME Sweet Spot (5 s/d 1,000 reviews)
                        if review_count > max_reviews:
                            print(f"  [-] {raw_name} dilewati: Skala terlalu besar ({review_count} review)")
                            continue
                        if review_count < min_reviews and rating_text:
                            # Might be inactive/unrated
                            continue

                        norm_phone = self.biz_scanner.normalize_indonesian_phone(raw_phone)
                        if not norm_phone and not raw_phone:
                            # Skip if no contact phone at all
                            continue

                        # Clean business title
                        clean_name = re.split(r'[|\-–•—]', raw_name)[0].strip()
                        slug_name = re.sub(r'[^a-zA-Z0-9]', '-', clean_name).lower().strip('-')

                        # Determine Track A (No Website) vs Track B (Has Website)
                        is_track_a = False
                        parsed_dom = ""
                        if not website_url or not website_url.startswith("http"):
                            is_track_a = True
                        else:
                            parsed_dom = urllib.parse.urlparse(website_url).netloc.lower().replace("www.", "")
                            if any(ex in parsed_dom for ex in EXCLUDED_MAPS_DOMAINS):
                                is_track_a = True

                        if is_track_a:
                            track = "track_a_new_web"
                            parsed_dom = f"{slug_name}.vercel.app"
                            website_url = ""
                            print(f"  [+] [JALUR A: BELUM ADA WEB] {clean_name}")
                        else:
                            track = "track_b_modernize"
                            print(f"  [+] [JALUR B: MODERNISASI] {clean_name} ({parsed_dom})")

                        print(f"      Telepon : {norm_phone or raw_phone} | Review: {rating_text or 'Aktif'}")

                        candidates.append({
                            "name": clean_name,
                            "full_title": raw_name,
                            "website_url": website_url,
                            "domain": parsed_dom,
                            "phone": norm_phone or raw_phone,
                            "rating": rating_text,
                            "review_count": review_count,
                            "track": track
                        })

                    except Exception as card_err:
                        continue

            except Exception as e:
                print(f"[!] Error saat scraping Google Maps: {e}")
            finally:
                browser.close()

        # Step 2: Inspection & Standardization
        qualified_leads = []
        print(f"\n[*] Memproses dan standardisasi {len(candidates)} kandidat prospek...")

        for cand in candidates:
            if cand["track"] == "track_a_new_web":
                # Track A: Ready for new Swiss Minimalist website generation
                qualified_leads.append({
                    "business_name": cand["name"],
                    "website_url": "",
                    "domain": cand["domain"],
                    "title": cand["name"],
                    "whatsapp": cand["phone"] if cand["phone"].startswith("628") else "",
                    "email": "",
                    "track": "track_a_new_web",
                    "outdated_signals": [
                        "Belum memiliki website resmi di pencarian Google",
                        "Kenyamanan pemesanan langsung smartphone via WhatsApp"
                    ],
                    "gmaps_rating": cand["rating"],
                    "gmaps_reviews": cand["review_count"]
                })
            else:
                # Track B: Deep Website Inspection for SEO Gaps
                inspected = self.biz_scanner.inspect_website(cand["website_url"])
                if inspected:
                    inspected["track"] = "track_b_modernize"
                    inspected["gmaps_rating"] = cand["rating"]
                    inspected["gmaps_reviews"] = cand["review_count"]
                    if not inspected.get("whatsapp") and cand.get("phone"):
                        if cand["phone"].startswith("628"):
                            inspected["whatsapp"] = cand["phone"]
                    if inspected.get("whatsapp") or cand.get("phone"):
                        qualified_leads.append(inspected)
                else:
                    if cand.get("phone"):
                        qualified_leads.append({
                            "business_name": cand["name"],
                            "website_url": cand["website_url"],
                            "domain": cand["domain"],
                            "title": cand["name"],
                            "whatsapp": cand["phone"] if cand["phone"].startswith("628") else "",
                            "email": "",
                            "track": "track_b_modernize",
                            "outdated_signals": ["Audit optimasi struktur Google SEO & Tampilan Smartphone"],
                            "gmaps_rating": cand["rating"],
                            "gmaps_reviews": cand["review_count"]
                        })

        print(f"[+] Total Prospek Bisnis Berkembang Terkualifikasi: {len(qualified_leads)}")
        return qualified_leads

