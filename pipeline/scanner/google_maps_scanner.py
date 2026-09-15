"""
Google Maps Business Scanner & Qualified SME Harvester.
Scrapes local Indonesian businesses directly from Google Maps, extracts authentic
contact information (WhatsApp, Website, Phone, Physical Address), filters specifically
for developing small-to-medium businesses ($100 budget sweet spot: 10 to 1,000 reviews),
and strictly prioritizes Indonesian mobile/WhatsApp numbers (08... / +628...) while
automatically rejecting PSTN office landline numbers (021, 031, 022, etc.).
"""

import os
import re
import sys
import time
import urllib.parse
from typing import Dict, Any, List, Optional
from playwright.sync_api import sync_playwright

from pipeline.scanner.business_scanner import (
    IndonesianBusinessScanner,
    is_indonesian_landline,
    is_indonesian_mobile
)
from pipeline.scanner.contact_enricher import ContactEnricher

# Enterprise, marketplaces, messaging, and directory aggregators to discard immediately
EXCLUDED_MAPS_DOMAINS = [
    "google.", "facebook.com", "instagram.com", "tiktok.com", "youtube.com", "t.me", "telegram.me",
    "wa.me", "whatsapp.com", "api.whatsapp.com", "linktr.ee", "bit.ly", "s.id", "bio.link",
    "campsite.bio", "taplink.cc", "desty.page", "lynk.id", "msha.ke",
    "tokopedia.com", "shopee.co.id", "lazada.co.id", "bukalapak.com", "blibli.com", "olx.co.id",
    "jne.co.id", "sicepat.com", "jtexpress.co.id", "tiki.id", "posindonesia.co.id", "wahana.com",
    "halodoc.com", "alodokter.com", "klikdokter.com", "rumah123.com", "99.co", "lamudi.co.id",
    "traveloka.com", "tiket.com", "gojek.com", "grab.com", "indonetwork.co.id", "yellowpages.co.id"
]


def clean_business_brand_name(raw_name: str) -> str:
    """
    Cleans raw Google Maps business names into pristine, professional brand names.
    - Strips parenthetical descriptions: 'SENTRAL PLASTIK (Part of Budi Abadi Plastik)' -> 'Sentral Plastik'
    - Strips brackets: 'Budi Plastik [Buka 24 Jam]' -> 'Budi Plastik'
    - Splits on marketing dividers (|, -, –, —, •, ~)
    - Converts ALL CAPS shouting into crisp Title Case while preserving Indonesian acronyms (PT, CV, UD, TB, etc.)
    - Strips redundant trailing branch/legal tags
    """
    if not raw_name:
        return ""
    name = raw_name.strip()
    # 1. Remove parenthetical descriptions, branches, or parent notes: (...) and [...]
    name = re.sub(r'[\(\[\{].*?[\)\]\}]', '', name).strip()
    
    # 2. Split on common marketing delimiters: |, -, –, —, •, ~, /
    parts = re.split(r'\s+[|\-–•—~]\s+|[|•~]', name)
    if parts and parts[0].strip():
        name = parts[0].strip()
        
    # 3. Clean trailing punctuation
    name = re.sub(r'[,.\-_–—\s]+$', '', name).strip()
    
    # 4. Remove unwanted trailing keywords
    name = re.sub(r'\s+(?:cabang|branch|pusat|official|store|gudang|depo)\b.*$', '', name, flags=re.IGNORECASE).strip()
    
    # 5. Smart Title Casing for ALL CAPS text
    words = name.split()
    if name.isupper() or (len(words) > 1 and sum(1 for w in words if w.isupper()) >= len(words) - 1):
        clean_words = []
        acronyms = {'PT', 'CV', 'UD', 'TB', 'PD', 'PO', 'KSU', 'BPR', 'TPA', 'LPG', 'SPBU', 'AC', 'PVC', 'LED', 'CCTV', 'CNC'}
        for w in words:
            w_clean = re.sub(r'[^A-Za-z]', '', w)
            if w_clean.upper() in acronyms:
                clean_words.append(w_clean.upper())
            else:
                clean_words.append(w.capitalize())
        name = ' '.join(clean_words)
    return name


class GoogleMapsBusinessScanner:
    def __init__(self):
        self.biz_scanner = IndonesianBusinessScanner()
        self.contact_enricher = ContactEnricher()

    def _parse_review_count(self, rating_text: str) -> int:
        """
        Robustly extracts integer review count from strings like:
        - '4,8 (51)' or '4.5 (1.234)'
        - '4,8 bintang 51 ulasan' or '51 ulasan'
        - '4.8 stars 1,234 reviews' or '12 reviews'
        """
        if not rating_text:
            return 0

        # Pattern 1: Count inside parentheses e.g. (51) or (1.234)
        m = re.search(r'\(([\d\.\,]+)\)', rating_text)
        if m:
            raw = m.group(1).replace(".", "").replace(",", "")
            try:
                return int(raw)
            except ValueError:
                pass

        # Pattern 2: Count before 'ulasan' or 'reviews' e.g. '51 ulasan'
        m2 = re.search(r'([\d\.\,]+)\s*(?:ulasan|reviews|review)', rating_text, re.IGNORECASE)
        if m2:
            raw = m2.group(1).replace(".", "").replace(",", "")
            try:
                return int(raw)
            except ValueError:
                pass

        # Pattern 3: 'bintang [count]' where count > 5 (to distinguish from 1-5 rating score)
        m3 = re.search(r'bintang\s+([\d\.\,]+)', rating_text, re.IGNORECASE)
        if m3:
            raw = m3.group(1).replace(".", "").replace(",", "")
            try:
                val = int(raw)
                if val > 5:
                    return val
            except ValueError:
                pass

        return 0

    def search_local_businesses(
        self,
        query: str,
        limit: int = 5,
        min_reviews: int = 10,
        max_reviews: int = 1000,
        track_only: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Searches Google Maps for local developing businesses.
        Filters specifically for active SMEs (review count between min_reviews and max_reviews),
        strictly prioritizes Indonesian mobile/WhatsApp numbers (08... / 628...),
        automatically rejects PSTN office landlines (021, 031, etc.),
        and detects Dual-Track (Track A: Web Baru vs Track B: Modernisasi).
        """
        print(f"\n[GMAPS SCANNER] Mencari bisnis berkembang di Google Maps untuk: '{query}'...")
        print(f"[*] Filter Ulasan : {min_reviews} s/d {max_reviews} review")
        print(f"[*] Filter Kontak : Wajib Nomor HP/WhatsApp (08... / +628...), Tolak PSTN kantor (021/031)")
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

                # Wait for results (either feed of multiple cards or direct single place detail)
                page.wait_for_selector('div[role="feed"], div[role="article"], a[href*="/maps/place/"], h1.fontHeadlineLarge, div.TIHn2, h1', timeout=20000)

                # Scroll down results feed 2-3 times to load more items if feed is present
                feed = page.query_selector('div[role="feed"]')
                if feed:
                    for _ in range(2):
                        feed.evaluate('el => el.scrollBy(0, 1000)')
                        time.sleep(1.5)

                cards = page.query_selector_all('a[href*="/maps/place/"]')
                is_direct_place = False
                if not cards and (page.query_selector('h1') or "/maps/place/" in page.url):
                    is_direct_place = True
                    print(f"[*] Terdeteksi langsung halaman detail lokasi tunggal Google Maps: {page.title()}")
                    cards = [page]  # Use page directly as the target
                else:
                    print(f"[*] Ditemukan {len(cards)} listing lokasi di Google Maps. Memeriksa detail bisnis...")

                seen_names = set()

                for idx, card in enumerate(cards):
                    if len(candidates) >= limit:
                        break

                    try:
                        if is_direct_place:
                            h1_elem = page.query_selector('h1')
                            raw_name = h1_elem.inner_text().strip() if h1_elem else clean_business_brand_name(query)
                            card_label = raw_name
                        else:
                            raw_name = card.get_attribute("aria-label") or card.inner_text().split("\n")[0].strip()
                            if not raw_name or raw_name in seen_names:
                                continue
                            seen_names.add(raw_name)
                            card_label = card.get_attribute("aria-label") or ""

                            # Click card to open detail pane
                            card.click()
                            time.sleep(2.0)

                        # Filter out invalid, generic or messaging listings immediately
                        raw_lower = raw_name.lower().strip()
                        if any(inv in raw_lower for inv in ["share on whatsapp", "whatsapp", "login", "sign in", "just a moment", "cloudflare", "404 not found"]):
                            print(f"  [-] {raw_name} dilewati: Nama generic / messaging invalid.")
                            continue

                        if not is_direct_place:
                            # Check card aria-label for initial review count hint
                            card_label = card.get_attribute("aria-label") or ""
                            # Click card to open detail pane
                            card.click()
                            time.sleep(2.0)

                        # Check operational status (Reject permanently or temporarily closed businesses)
                        closed_el = page.query_selector('span.fontBodyMedium[style*="color: rgb(217, 48, 37)"], div.m6QErb span[aria-label*="Tutup"], div.m6QErb span[aria-label*="Closed"]')
                        status_str = closed_el.inner_text().strip().lower() if closed_el else ""
                        if any(c_word in status_str for c_word in ["tutup sementara", "tutup permanen", "permanently closed", "temporarily closed"]):
                            print(f"  [-] {raw_name} dilewati: Status bisnis terdata Tutup ({status_str})")
                            continue

                        # Extract authentic high-resolution photo/logo from Google Maps hero
                        img_el = page.query_selector('button[jsaction*="heroHeaderImage"] img, img.hero-header-image, div.Z6G2Ge img, div.lRq1Sc img, img[src*="googleusercontent.com"]')
                        image_url = ""
                        if img_el:
                            raw_src = img_el.get_attribute("src") or ""
                            if "googleusercontent.com" in raw_src:
                                # Convert to crisp high-res 1024px banner/logo
                                base_img = re.sub(r'=[swh\d\-cpkno]+$', '', raw_src.split('?')[0])
                                image_url = f"{base_img}=s1024"
                            elif raw_src.startswith("http"):
                                image_url = raw_src

                        # Extract phone & website
                        phone_el = page.query_selector('button[data-item-id*="phone"], button[aria-label*="Telepon"]')
                        raw_phone = ""
                        if phone_el:
                            aria_p = phone_el.get_attribute("aria-label") or ""
                            raw_phone = aria_p.replace("Telepon:", "").replace("Phone:", "").strip()
                            if not raw_phone:
                                raw_phone = phone_el.inner_text().strip()

                        # Extract website
                        web_el = page.query_selector('a[data-item-id="authority"], a[aria-label*="Situs Web"], a[aria-label*="Website"]')
                        website_url = web_el.get_attribute("href") if web_el else ""

                        # Check if website is a WhatsApp direct chat link (wa.me / whatsapp.com) or link-in-bio
                        if website_url:
                            web_lower = website_url.lower()
                            if "wa.me" in web_lower or "whatsapp.com" in web_lower:
                                wa_match = re.search(r'(?:wa\.me/|phone=|send\?phone=)(\+?62\d+|08\d+|\d{10,14})', website_url)
                                if wa_match and not raw_phone:
                                    raw_phone = wa_match.group(1)
                                website_url = ""  # A WhatsApp link is NOT an official website; qualifies for Track A!

                        rating_el = page.query_selector('div.F7nice, span.ceNzKf')
                        rating_text = rating_el.inner_text().replace("\n", " ").strip() if rating_el else ""
                        review_count = self._parse_review_count(rating_text)

                        # If detail pane had 0, check rating_el aria-label
                        if review_count == 0 and rating_el:
                            aria_r = rating_el.get_attribute("aria-label") or ""
                            review_count = self._parse_review_count(aria_r)

                        # Fallback to card label if still 0
                        if review_count == 0 and card_label:
                            review_count = self._parse_review_count(card_label)

                        # Extract address
                        addr_el = page.query_selector('button[data-item-id="address"], button[aria-label*="Alamat:"], button[aria-label*="Address:"]')
                        raw_address = ""
                        if addr_el:
                            aria_a = addr_el.get_attribute("aria-label") or ""
                            raw_address = aria_a.replace("Alamat:", "").replace("Address:", "").strip()
                            if not raw_address:
                                raw_address = addr_el.inner_text().strip()

                        # Extract category
                        cat_el = page.query_selector('button[jsaction*="category"], div.fontBodyMedium button.DkEaL, span.YhemCb')
                        raw_category = cat_el.inner_text().strip() if cat_el else ""

                        # Extract opening hours
                        hours_el = page.query_selector('button[data-item-id*="oh"], div[aria-label*="Jam buka"], div[aria-label*="Buka"], span.ZDu9vd')
                        raw_hours = hours_el.inner_text().replace("\n", " ").strip() if hours_el else ""

                        # 1. Filter: SME Sweet Spot Review Count (10 s/d 1,000 reviews)
                        if review_count > max_reviews:
                            print(f"  [-] {raw_name} dilewati: Skala terlalu besar ({review_count} review > {max_reviews})")
                            continue
                        if review_count < min_reviews:
                            print(f"  [-] {raw_name} dilewati: Jumlah review di bawah batas minimum ({review_count} review < {min_reviews})")
                            continue

                        # Clean business title with dedicated brand cleaner & slugifier
                        from pipeline.deployer.vercel_deployer import VercelDeployer
                        from pipeline.researcher.business_researcher import BusinessResearcher
                        clean_name = clean_business_brand_name(raw_name)
                        detected_city = BusinessResearcher().extract_city(raw_address or "", clean_name)
                        slug_name = VercelDeployer.get_preview_slug(clean_name, track="track_a_new_web", city=detected_city)

                        # Reject Corporate Chain / Multi-Branch indicators in Name
                        clean_lower = raw_name.lower()
                        if any(b_ind in clean_lower for b_ind in [
                            "cabang", "branch", "perwakilan", "depo resmi", "kantor cabang",
                            "kantor perwakilan", "distrik", "regional office", "head office"
                        ]):
                            print(f"  [-] {raw_name} dilewati: Terdeteksi cabang korporasi nasional (Bukan UKM lokal)")
                            continue

                        # 1.5 Early Track Filter (Bypass non-matching tracks immediately)
                        if website_url and website_url.startswith("http"):
                            site_host = urllib.parse.urlparse(website_url).netloc.lower().replace("www.", "")
                            has_real_site = not any(ex in site_host for ex in EXCLUDED_MAPS_DOMAINS) and "business.site" not in site_host
                            if has_real_site and track_only == "track_a_new_web":
                                print(f"  [-] {clean_name} dilewati: Sudah memiliki website ({site_host}), bukan target Jalur A (Web Baru).")
                                continue
                            elif not has_real_site and track_only == "track_b_modernize":
                                print(f"  [-] {clean_name} dilewati: Belum memiliki website resmi, bukan target Jalur B (Modernisasi).")
                                continue
                        elif track_only == "track_b_modernize":
                            print(f"  [-] {clean_name} dilewati: Belum memiliki website, bukan target Jalur B (Modernisasi).")
                            continue

                        # 2. Contact & Social Enrichment
                        found_email = ""
                        social_profiles = []

                        # Crawl website contacts if website exists
                        if website_url and website_url.startswith("http"):
                            site_c = self.contact_enricher.crawl_website_contacts(website_url)

                            # Filter out national corporations with multi-branch networks
                            if site_c.get("is_corporate"):
                                print(f"  [-] {clean_name} dilewati: Website korporasi nasional multi-cabang (Bukan target UKM)")
                                continue

                            # Filter out websites that already use modern SPA tech
                            if site_c.get("is_spa"):
                                print(f"  [-] {clean_name} dilewati: Website sudah modern (Framework Nuxt/Next.js/React)")
                                continue

                            found_email = site_c.get("email", "")
                            social_profiles = site_c.get("social_profiles", [])
                            if not raw_phone and site_c.get("whatsapp"):
                                raw_phone = site_c["whatsapp"]


                        # 3. Filter Kontak: Wajib Nomor HP/WhatsApp (08... / +628...) & Tolak PSTN kantor (021/031/05x)
                        norm_phone = self.biz_scanner.normalize_indonesian_phone(raw_phone, mobile_only=True)
                        if not norm_phone:
                            if is_indonesian_landline(raw_phone):
                                print(f"  [!] {clean_name}: Nomor PSTN kantor terdeteksi ({raw_phone}). Mencari nomor HP WhatsApp owner...")
                                enrich_res = self.contact_enricher.enrich_from_social_bio(clean_name, raw_address[:30] if raw_address else "")
                                found_wa = enrich_res.get("whatsapp")
                                if not found_email:
                                    found_email = enrich_res.get("email", "")
                                if not social_profiles:
                                    social_profiles = enrich_res.get("social_profiles", [])

                                if found_wa and is_indonesian_mobile(found_wa):
                                    norm_phone = found_wa
                                    print(f"      [+] Ditemukan WhatsApp HP dari media sosial/bio: {norm_phone}")
                                else:
                                    print(f"  [-] {clean_name} dilewati: Hanya memiliki nomor telepon kantor PSTN ({raw_phone}), bukan WhatsApp HP (08...).")
                                    continue
                            else:
                                enrich_res = self.contact_enricher.enrich_from_social_bio(clean_name, raw_address[:30] if raw_address else "")
                                found_wa = enrich_res.get("whatsapp")
                                if not found_email:
                                    found_email = enrich_res.get("email", "")
                                if not social_profiles:
                                    social_profiles = enrich_res.get("social_profiles", [])

                                if found_wa and is_indonesian_mobile(found_wa):
                                    norm_phone = found_wa
                                if not norm_phone:
                                    print(f"  [-] {clean_name} dilewati: Tidak ditemukan nomor HP/WhatsApp Indonesia (08... / +628...).")
                                    continue

                        # 4. Determine Track A (No Website) vs Track B (Has Website)
                        is_track_a = False
                        parsed_dom = ""
                        if not website_url or not website_url.startswith("http"):
                            is_track_a = True
                        else:
                            parsed_dom = urllib.parse.urlparse(website_url).netloc.lower().replace("www.", "")
                            if any(ex in parsed_dom for ex in EXCLUDED_MAPS_DOMAINS) or "business.site" in parsed_dom:
                                is_track_a = True

                        if is_track_a:
                            if track_only == "track_b_modernize":
                                continue
                            track = "track_a_new_web"
                            parsed_dom = slug_name
                            website_url = ""
                            print(f"  [+] [JALUR A: BELUM ADA WEB] {clean_name} ({raw_category or 'Bisnis Lokal'})")
                        else:
                            if track_only == "track_a_new_web":
                                print(f"  [-] {clean_name} dilewati: Sudah memiliki website ({parsed_dom}), bukan target Jalur A (Web Baru).")
                                continue
                            track = "track_b_modernize"
                            print(f"  [+] [JALUR B: MODERNISASI] {clean_name} ({parsed_dom})")

                        print(f"      WhatsApp: {norm_phone} | Review: {rating_text or f'{review_count} ulasan'} | Alamat: {raw_address[:40] if raw_address else 'Indonesia'}")
                        if image_url:
                            print(f"      Foto Maps: {image_url[:65]}...")

                        candidates.append({
                            "name": clean_name,
                            "full_title": raw_name,
                            "website_url": website_url,
                            "domain": parsed_dom,
                            "phone": norm_phone,
                            "email": found_email,
                            "rating": rating_text or f"4.8 ({review_count})",
                            "review_count": review_count,
                            "category": raw_category,
                            "address": raw_address,
                            "image_url": image_url,
                            "logo_url": image_url,
                            "opening_hours": raw_hours,
                            "social_profiles": social_profiles,
                            "track": track,
                            "city": detected_city,
                            "gmaps_url": page.url
                        })

                    except Exception as card_err:
                        print(f"  [DEBUG] Card error on {raw_name}: {card_err}")
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
                    "whatsapp": cand["phone"],
                    "email": cand.get("email", ""),
                    "track": "track_a_new_web",
                    "category": cand.get("category", ""),
                    "address": cand.get("address", ""),
                    "image_url": cand.get("image_url", ""),
                    "logo_url": cand.get("logo_url", ""),
                    "opening_hours": cand.get("opening_hours", ""),
                    "social_profiles": cand.get("social_profiles", []),
                    "gmaps_url": cand.get("gmaps_url", ""),
                    "outdated_signals": [
                        "Belum memiliki website resmi di pencarian Google",
                        "Peluang jangkauan pasar baru via Google Search & Mobile WhatsApp"
                    ],
                    "gmaps_rating": cand["rating"],
                    "gmaps_reviews": cand["review_count"]
                })
            else:
                # Track B: Deep Website Inspection for SEO Gaps
                inspected = self.biz_scanner.inspect_website(cand["website_url"])
                if inspected:
                    # PRESERVE genuine, clean brand name from Google Maps!
                    if cand.get("name"):
                        inspected["business_name"] = cand["name"]
                    inspected["track"] = "track_b_modernize"
                    inspected["gmaps_rating"] = cand["rating"]
                    inspected["gmaps_reviews"] = cand["review_count"]
                    inspected["category"] = cand.get("category", "")
                    inspected["address"] = cand.get("address", "")
                    inspected["image_url"] = cand.get("image_url", "")
                    inspected["logo_url"] = cand.get("logo_url", "")
                    inspected["opening_hours"] = cand.get("opening_hours", "")
                    inspected["gmaps_url"] = cand.get("gmaps_url", "")
                    if cand.get("social_profiles"):
                        inspected["social_profiles"] = cand["social_profiles"]
                    if not inspected.get("whatsapp") and cand.get("phone"):
                        inspected["whatsapp"] = cand["phone"]
                    if not inspected.get("email") and cand.get("email"):
                        inspected["email"] = cand["email"]
                    qualified_leads.append(inspected)
                else:
                    qualified_leads.append({
                        "business_name": cand["name"],
                        "website_url": cand["website_url"],
                        "domain": cand["domain"],
                        "title": cand["name"],
                        "whatsapp": cand["phone"],
                        "email": cand.get("email", ""),
                        "track": "track_b_modernize",
                        "category": cand.get("category", ""),
                        "address": cand.get("address", ""),
                        "image_url": cand.get("image_url", ""),
                        "logo_url": cand.get("logo_url", ""),
                        "opening_hours": cand.get("opening_hours", ""),
                        "social_profiles": cand.get("social_profiles", []),
                        "gmaps_url": cand.get("gmaps_url", ""),
                        "outdated_signals": ["Audit optimasi struktur Google SEO & Tampilan Smartphone"],
                        "gmaps_rating": cand["rating"],
                        "gmaps_reviews": cand["review_count"]
                    })

        # Strict validation: Filter out invalid, generic, or messaging candidates
        valid_leads = []
        for lead in qualified_leads:
            name_check = str(lead.get("business_name", "")).lower()
            dom_check = str(lead.get("domain", "")).lower()
            combined = f"{name_check} {dom_check}"
            if any(inv in combined for inv in ["share on whatsapp", "whatsapp", "wa.me", "login", "sign in", "just a moment", "404 not found"]):
                print(f"  [-] Menolak prospek tidak valid: {lead.get('business_name')} ({lead.get('domain')})")
                continue
            valid_leads.append(lead)
        qualified_leads = valid_leads

        print(f"[+] Total Prospek Bisnis Berkembang Terkualifikasi: {len(qualified_leads)}")
        return qualified_leads

