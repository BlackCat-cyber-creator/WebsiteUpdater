"""
Dedicated Kalimantan SME Harvester & Turn-Key Processor.
Specialized for discovering local small-to-medium businesses across East, West,
South, and Central Kalimantan on Google Maps (10 - 1,000 reviews, mobile WhatsApp 08...),
automatically generating Swiss Minimalist websites, deploying to Vercel, creating
executive PDF proposals, and adding them to the Review Dashboard.
"""

import os
import re
import json
import time
import random
from datetime import datetime
from typing import Dict, Any, List, Optional

from pipeline.scanner.google_maps_scanner import GoogleMapsBusinessScanner, clean_business_brand_name
from pipeline.scanner.agent_reach_enricher import AgentReachContactEnricher
from pipeline.site_generator import SiteGenerator
from pipeline.deployer.vercel_deployer import VercelDeployer
from pipeline.pdf_generator import ProposalPdfGenerator
from pipeline.delivery.code_packager import CodePackager
from pipeline.outreach.tracker import OutreachTracker
from pipeline.outreach.whatsapp_dispatcher import WhatsAppDispatcher

KALIMANTAN_PRESETS = {
    "balikpapan": [
        "kargo alat berat balikpapan",
        "supplier alat teknik industri balikpapan",
        "ekspedisi balikpapan surabaya",
        "kontraktor baja gudang balikpapan",
        "supplier bahan kimia industri balikpapan",
        "klinik estetika spesialis balikpapan",
        "bengkel bubut industri balikpapan"
    ],
    "samarinda": [
        "distributor packaging karton box samarinda",
        "sewa truk tronton fuso samarinda",
        "kontraktor hvac tata udara samarinda",
        "supplier pipa hdpe samarinda",
        "klinik gigi spesialis samarinda",
        "distributor frozen food samarinda"
    ],
    "pontianak": [
        "ekspedisi kargo pontianak jakarta",
        "supplier bahan kimia pontianak",
        "distributor packaging plastik pontianak",
        "jasa kontraktor interior pontianak",
        "klinik estetika kecantikan pontianak"
    ],
    "banjarmasin": [
        "sewa truk reefer pendingin banjarmasin",
        "distributor genset industri banjarmasin",
        "kontraktor epoxy lantai pabrik banjarmasin",
        "supplier safety industri banjarmasin"
    ],
    "palangkaraya": [
        "ekspedisi kargo palangka raya",
        "supplier alat teknik palangka raya",
        "kontraktor komersial palangka raya",
        "distributor packaging karton palangka raya"
    ]
}


def scan_and_process_kalimantan_smes(
    city: Optional[str] = None,
    limit: int = 2,
    min_reviews: int = 10,
    max_reviews: int = 1000
) -> Dict[str, Any]:
    """
    Executes end-to-end Kalimantan SME discovery:
    1. Queries Google Maps for verified local SMEs with 10-1000 reviews & mobile phone.
    2. Builds customized Swiss Minimalist website.
    3. Deploys to Vercel with clean short-form slug.
    4. Generates 4-page Executive PDF proposal.
    5. Packages clean client source code ZIP.
    6. Records in OutreachTracker and refreshes the Dashboard.
    """
    tracker = OutreachTracker()
    maps_scanner = GoogleMapsBusinessScanner()
    enricher = AgentReachContactEnricher()
    site_gen = SiteGenerator()
    vercel_dep = VercelDeployer()
    pdf_gen = ProposalPdfGenerator()
    code_pkg = CodePackager()
    wa_disp = WhatsAppDispatcher()

    # Determine query pool
    selected_city = (city or "all").strip().lower()
    queries = []
    if selected_city in KALIMANTAN_PRESETS:
        queries = list(KALIMANTAN_PRESETS[selected_city])
    else:
        # Mix across all major cities
        for c_queries in KALIMANTAN_PRESETS.values():
            queries.extend(c_queries)
    
    random.shuffle(queries)

    print(f"\n" + "=" * 80)
    print(f"  🔍 SCANNING KALIMANTAN SMES (Target: {selected_city.upper()}, Limit: {limit})")
    print("=" * 80)

    candidates: List[Dict[str, Any]] = []
    for q in queries:
        if len(candidates) >= limit:
            break
        needed = limit - len(candidates)
        print(f"[*] Query Google Maps: '{q}' (butuh {needed} lagi)...")
        found = maps_scanner.search_local_businesses(
            q, limit=needed, min_reviews=min_reviews, max_reviews=max_reviews, track_only="track_a_new_web"
        )
        for f in found:
            if f.get("track") != "track_a_new_web":
                continue
            f["business_name"] = clean_business_brand_name(f.get("business_name", ""))
            from pipeline.researcher.business_researcher import BusinessResearcher
            city_hint = f.get("city") or BusinessResearcher().extract_city(f.get("address", ""), f["business_name"])
            f["domain"] = vercel_dep.get_preview_slug(f["business_name"], track="track_a_new_web", city=city_hint)
            domain = f["domain"]
            wa = f.get("whatsapp", "")
            
            # Filter invalid messaging leads
            check_str = f"{f['business_name']} {domain}".lower()
            if any(inv in check_str for inv in ["share on whatsapp", "whatsapp", "wa.me", "login", "404 not found"]):
                continue

            # Skip if already in tracker
            if tracker.is_already_contacted(domain, wa) or tracker.get_lead(domain):
                print(f"    [-] Skip {domain} (sudah ada di database).")
                continue
            if not any(c["domain"] == domain for c in candidates):
                candidates.append(f)

    if not candidates:
        print("[!] Tidak ada prospek baru yang ditemukan di Google Maps.")
        return {
            "success": True,
            "count": 0,
            "leads": [],
            "message": "Tidak ada prospek baru yang memenuhi kriteria ulasan 10-1000 atau semua sudah tersimpan di antrean."
        }

    processed_leads = []
    for idx, lead in enumerate(candidates, 1):
        domain = lead["domain"]
        biz_name = lead["business_name"]
        wa = lead.get("whatsapp", "")
        track = lead.get("track", "track_a_new_web")
        rating = lead.get("gmaps_rating", "4.9")
        review_count = lead.get("gmaps_reviews", 50)
        signals = lead.get("outdated_signals", [])

        print(f"\n[*] [{idx}/{len(candidates)}] Memproses Deliverables: {biz_name} ({domain})")

        # Enrich contact if missing
        if not wa:
            enriched = enricher.enrich_from_social_bio(biz_name)
            if enriched.get("whatsapp"):
                wa = enriched["whatsapp"]
                lead["whatsapp"] = wa

        client_clean = vercel_dep.clean_slug(domain).replace("-", "_")
        client_dir = os.path.abspath(os.path.join("clients", client_clean))
        site_dir = os.path.join(client_dir, "site")
        os.makedirs(client_dir, exist_ok=True)

        # Download authentic logo/photo if available
        logo_url = lead.get("logo_url") or lead.get("image_url")
        if logo_url and logo_url.startswith("http"):
            try:
                import urllib.request
                req = urllib.request.Request(logo_url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                with urllib.request.urlopen(req, timeout=10) as r:
                    img_data = r.read()
                    if len(img_data) > 200:
                        os.makedirs(os.path.join(client_dir, "assets"), exist_ok=True)
                        with open(os.path.join(client_dir, "assets", "logo.png"), "wb") as f_img:
                            f_img.write(img_data)
                        print("    [+] Foto bisnis autentik Google Maps tersimpan.")
            except Exception:
                pass

        # 1. Generate Turnkey Site (Track A)
        if not os.path.exists(os.path.join(site_dir, "index.html")):
            site_gen.generate_turnkey_site(
                business_name=biz_name,
                category=lead.get("category", ""),
                phone=wa,
                address=lead.get("address", ""),
                rating=rating,
                review_count=review_count,
                output_dir=client_dir
            )
            print(f"    [+] Website Swiss Minimalist siap di: {site_dir}")

        # 2. Deploy to Vercel
        vercel_url = lead.get("vercel_url")
        if not vercel_url:
            dep_res = vercel_dep.deploy(site_dir, client_clean, track="track_a_new_web", city=lead.get("city"))
            if dep_res.get("success"):
                vercel_url = dep_res.get("url")
                lead["vercel_url"] = vercel_url
                print(f"    [+] Live di Vercel: {vercel_url}")

        # 3. Generate Executive Proposal PDF
        pdf_path = os.path.join(client_dir, "client_proposal.pdf")
        if not os.path.exists(pdf_path) or not lead.get("proposal_pdf"):
            pdf_res = pdf_gen.generate_track_a(lead, client_dir, vercel_url=vercel_url)
            if pdf_res.get("pdf_path") and os.path.exists(pdf_res["pdf_path"]):
                lead["proposal_pdf"] = os.path.abspath(pdf_res["pdf_path"])
                print(f"    [+] Dokumen Proposal PDF 4 Halaman siap: {lead['proposal_pdf']}")

        # 4. Package Clean Source Code ZIP
        pkg_res = code_pkg.package_client_code(
            site_dir=site_dir,
            client_slug=client_clean,
            output_dir=client_dir,
            business_name=biz_name,
            domain=domain
        )
        if pkg_res.get("success"):
            lead["package_zip"] = pkg_res.get("zip_path")
            print(f"    [+] Paket Serah Terima ZIP siap ({pkg_res.get('size_mb')} MB)")

        # 5. Record in Tracker
        tracker.record_lead(domain, {
            "domain": domain,
            "business_name": biz_name,
            "website_url": "",
            "whatsapp": wa,
            "email": lead.get("email", ""),
            "track": "track_a_new_web",
            "address": lead.get("address", ""),
            "city": lead.get("city", "") or selected_city.title(),
            "proposal_pdf": lead.get("proposal_pdf", pdf_path),
            "vercel_url": vercel_url,
            "package_zip": lead.get("package_zip", ""),
            "outdated_signals": signals or ["Belum memiliki website resmi di Google Search", "Peluang jangkauan pasar baru via Google Search & Mobile WhatsApp"],
            "gmaps_rating": rating,
            "gmaps_reviews": review_count,
            "notes": f"Scanned from Google Maps ({selected_city.capitalize()})"
        }, status="discovered")

        processed_leads.append({
            "domain": domain,
            "business_name": biz_name,
            "whatsapp": wa,
            "vercel_url": vercel_url,
            "rating": rating,
            "reviews": review_count
        })

    # Refresh Dashboard HTML
    all_leads = list(tracker.get_all_leads().values())
    wa_disp.generate_html_queue_dashboard(all_leads)

    print(f"\n[+] Sukses menambahkan {len(processed_leads)} prospek UKM Kalimantan ke dasbor antrean!")
    return {
        "success": True,
        "count": len(processed_leads),
        "leads": processed_leads,
        "message": f"Berhasil memindai dan memproses {len(processed_leads)} UKM baru di Kalimantan!"
    }
