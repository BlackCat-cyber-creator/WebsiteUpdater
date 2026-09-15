"""
Lead harvesting and automated outreach execution command handlers.
Enhanced with:
- Outdated Website Hunter (Jalur B Revitalizer via SERP Dorking)
- Dynamic High-Value Niche Matrix & Anti-Toko-Bangunan Filter
- Contact Validator & Multi-Tier Fallback Cascade (WhatsApp -> Cold Email -> Telesales PSTN)
- Streamlined Fail-Fast & Just-In-Time (JIT) Generation Architecture
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List
from pipeline.commands.context import CommandContext, execute_pipeline_for_client
from pipeline.scanner.contact_validator import ContactValidator
from pipeline.scanner.niche_matrix import NicheMatrix, HIGH_VALUE_NICHE_TAXONOMY
from pipeline.scanner.outdated_hunter import OutdatedWebsiteHunter

MID_TIER_CATEGORIES = {
    cat: data["sub_niches"] for cat, data in HIGH_VALUE_NICHE_TAXONOMY.items()
}


def cmd_harvest(ctx: CommandContext, args) -> None:
    """Discovers Indonesian SME leads and orchestrates turnkey site building, deployment, and outreach."""
    mode_label = "🔴 LIVE OUTREACH (DEDICATED ACCOUNTS)" if ctx.is_live else "🟢 DRY-RUN SIMULATION (SAFE MODE)"
    partner_info = None
    if getattr(args, "whitelabel", False) or getattr(args, "partner_name", ""):
        partner_info = {
            "name": getattr(args, "partner_name", "") or "Mitra Digital Agency",
            "whatsapp": getattr(args, "partner_wa", ""),
            "logo": getattr(args, "partner_logo", ""),
            "url": getattr(args, "partner_url", ""),
            "team": f"Tim Desain & Rekayasa Web {getattr(args, 'partner_name', '')}" if getattr(args, 'partner_name', '') else "Tim Desain & Web Development",
            "tagline": f"Mitra Rekayasa Web Resmi • {getattr(args, 'partner_name', '')}" if getattr(args, 'partner_name', '') else "Studio Desain & Pengembangan Web Modern"
        }

    print("=" * 80)
    print("  AUTONOMOUS INDONESIAN SME BUSINESS SCANNER & OUTREACH ENGINE (HIGH-CONVERSION TURN-KEY)")
    print(f"  Mode: {mode_label}")
    print(f"  Track Filter: {args.track.upper()}")
    if partner_info:
        print(f"  Whitelabel Mitra: {partner_info['name']} ({partner_info['whatsapp'] or 'No WA'})")
    print("=" * 80)

    candidate_leads: List[Dict[str, Any]] = []

    # Option 1: Direct Single Domain Inspection
    if args.domain:
        clean_url = args.domain if args.domain.startswith("http") else f"https://{args.domain}"
        print(f"\n[*] Inspecting single target domain: {clean_url}")
        hunter = OutdatedWebsiteHunter()
        inspected = hunter.inspect_and_audit_website(clean_url)
        if inspected:
            candidate_leads.append(inspected)
        else:
            print(f"[!] Unable to fetch or inspect domain: {clean_url}")

    # Option 2: Outdated Website Hunter (Jalur B Explicit / Track B Revitalizer)
    elif getattr(args, "hunt_outdated", False) or (args.track == "b" and not args.maps):
        print(f"\n[*] [JALUR B] Memburu website B2B Indonesia lama/outdated via SERP Dorking...")
        hunter = OutdatedWebsiteHunter()
        found = hunter.hunt_outdated_leads(limit=args.limit, target_category=args.category)
        candidate_leads.extend(found)

    # Option 3: Google Maps Scanner (Optimized with Dynamic High-Value Niche Matrix)
    elif args.maps:
        from pipeline.scanner.google_maps_scanner import GoogleMapsBusinessScanner
        maps_scanner = GoogleMapsBusinessScanner()
        target_maps_query = args.maps.strip()

        # Check if broad / auto / general search is requested
        is_broad = target_maps_query.lower() in [
            "general", "umum", "auto", "semua", "broad", "bebas",
            "kalimantan", "borneo", "kalsel", "kaltim", "jawa", "indonesia"
        ]

        if is_broad:
            print(f"\n[*] Mode Rotasi Niche Berdaya Beli Tinggi (Anti-Toko-Bangunan)...")
            dynamic_queries = NicheMatrix.get_diverse_query_batch(
                limit=max(6, args.limit * 2),
                target_category=args.category
            )
            for dq in dynamic_queries:
                if len(candidate_leads) >= args.limit:
                    break
                needed = args.limit - len(candidate_leads)
                found = maps_scanner.search_local_businesses(
                    dq, limit=needed, min_reviews=args.min_reviews, max_reviews=args.max_reviews
                )
                for f in found:
                    # Filter out excluded retail businesses
                    if NicheMatrix.is_excluded_business(f.get("business_name", "")):
                        print(f"  [-] {f.get('business_name')} dilewati: Termasuk kategori retail/toko bangunan yang dikecualikan.")
                        continue
                    if not any(c["domain"] == f["domain"] for c in candidate_leads):
                        candidate_leads.append(f)
        else:
            print(f"\n[*] Menelusuri Google Maps untuk: '{args.maps}' (limit: {args.limit})")
            found = maps_scanner.search_local_businesses(
                args.maps, limit=args.limit, min_reviews=args.min_reviews, max_reviews=args.max_reviews
            )
            query_lower = args.maps.lower()
            is_explicit_retail = any(ex in query_lower for ex in ["bangunan", "material", "toko"])
            for f in found:
                if is_explicit_retail or not NicheMatrix.is_excluded_business(f.get("business_name", "")):
                    candidate_leads.append(f)

        print(f"[+] Berhasil mengumpulkan {len(candidate_leads)} prospek UKM dari Google Maps.")

    # Option 4: Category Target
    elif args.category:
        print(f"\n[*] Target Kategori Bisnis Menengah: '{args.category}' (Limit: {args.limit})")
        hunter = OutdatedWebsiteHunter()
        found = hunter.hunt_outdated_leads(limit=args.limit, target_category=args.category)
        candidate_leads.extend(found)

    # Option 5: Query Target
    elif args.query:
        print(f"\n[*] Searching with query: '{args.query}' (limit: {args.limit})")
        hunter = OutdatedWebsiteHunter()
        found_links = hunter.search_engine_links(args.query, max_links=args.limit * 2)
        for target_url in found_links:
            if len(candidate_leads) >= args.limit:
                break
            inspected = hunter.inspect_and_audit_website(target_url)
            if inspected and not any(c["domain"] == inspected["domain"] for c in candidate_leads):
                candidate_leads.append(inspected)

    else:
        print("[!] Mohon tentukan target pencarian dengan:")
        print("    1. Berburu Web Lama (B) : python auto_outreach.py --hunt-outdated --limit 3")
        print("    2. Google Maps (SME)   : python auto_outreach.py --maps auto --limit 3")
        print("    3. Kategori Menengah   : python auto_outreach.py --category b2b_distributor --limit 3")
        print("    4. Domain Langsung     : python auto_outreach.py --domain contoh-bisnis.com")
        print("    5. Dasbor Interaktif   : python auto_outreach.py --dashboard")
        return

    # Filter candidates by track if requested
    if args.track == "a":
        candidate_leads = [c for c in candidate_leads if c.get("track") == "track_a_new_web"]
    elif args.track == "b":
        candidate_leads = [c for c in candidate_leads if c.get("track") != "track_a_new_web"]

    # Filter out invalid titles
    candidate_leads = [
        c for c in candidate_leads
        if not any(inv in f"{c.get('business_name', '')} {c.get('domain', '')}".lower()
                   for inv in ["share on whatsapp", "whatsapp", "wa.me", "login", "404 not found"])
    ]

    if not candidate_leads:
        print("[!] Tidak ada prospek baru yang memenuhi kriteria pencarian.")
        return

    pre_generate = getattr(args, "pre_generate", False)
    print(f"\n[*] Modus Eksekusi Deliverable: {'[UPFRONT PRE-GENERATE]' if pre_generate else '[FAIL-FAST & JUST-IN-TIME (JIT)]'}")

    # Process candidates
    for idx, lead in enumerate(candidate_leads, 1):
        domain = lead["domain"]
        biz_name = lead["business_name"]
        url = lead.get("website_url", "")
        raw_phone = lead.get("whatsapp") or lead.get("phone", "")
        email = lead.get("email", "")
        signals = lead.get("outdated_signals", [])
        track = lead.get("track", "track_b_modernize")

        print(f"\n" + "-" * 75)
        print(f"[{idx}/{len(candidate_leads)}] MEMPROSES PROSPEK: {biz_name} ({domain})")
        print(f"  Jalur    : {'[JALUR A: BUAT WEB BARU]' if track == 'track_a_new_web' else '[JALUR B: MODERNISASI & SEO]'}")
        print(f"  Telepon  : {raw_phone or 'Belum ditemukan'}")
        print(f"  Email    : {email or 'Belum ditemukan'}")
        print("-" * 75)

        if partner_info:
            lead["partner_info"] = partner_info

        # -------------------------------------------------------------
        # 1. GATEKEEPER: Cek Duplikasi di Database Tracker
        # -------------------------------------------------------------
        if ctx.tracker.is_already_contacted(domain, raw_phone, email):
            print(f"[SKIP] Prospek {domain} sudah pernah dihubungi sebelumnya (mencegah spam).")
            continue

        # -------------------------------------------------------------
        # 2. GATEKEEPER: Evaluasi Kontak & Multi-Tier Fallback Cascade
        # -------------------------------------------------------------
        cascade = ContactValidator.evaluate_contact_cascade(raw_phone, email)
        primary_channel = cascade["primary_channel"]
        phone_info = cascade["phone_info"]

        # FAIL-FAST: Discard leads with zero valid contact points immediately
        if primary_channel == "discard":
            print(f"  [-] [FAIL-FAST SKIP] {biz_name} ({domain}) dilewati: {cascade['notes']}")
            ctx.tracker.record_lead(domain, {
                "business_name": biz_name,
                "website_url": url,
                "notes": cascade["notes"]
            }, status="discarded")
            continue

        # Assign verified contact details
        wa = phone_info["normalized_e164"] if phone_info["is_mobile"] else ""
        lead["whatsapp"] = wa
        if cascade.get("email"):
            email = cascade["email"]
            lead["email"] = email

        target_channel = primary_channel
        if primary_channel == "email":
            print(f"  [✉️] [FALLBACK EMAIL] {biz_name}: Nomor telepon kantor/tidak ada WA. Saluran utama dialihkan ke Cold Email ({email}).")

        # Client Directory Setup
        client_clean = ctx.vercel_dep.clean_slug(domain).replace("-", "_")
        cand1 = os.path.join("clients", client_clean)
        cand2 = os.path.join("clients", domain.replace(".", "_").replace("-", "_"))
        client_dir = cand1 if os.path.exists(cand1) or not os.path.exists(cand2) else cand2
        os.makedirs(client_dir, exist_ok=True)
        pdf_path = os.path.join(client_dir, "client_proposal.pdf")

        # -------------------------------------------------------------
        # 3. DELIVERABLES GENERATION: UPFRONT vs JUST-IN-TIME (JIT)
        # -------------------------------------------------------------
        if pre_generate:
            # Full upfront heavy execution
            if track == "track_a_new_web":
                site_dir = os.path.join(client_dir, "site")
                if not os.path.exists(os.path.join(site_dir, "index.html")):
                    print(f"[*] Menyiapkan website modern Swiss Minimalist untuk {biz_name}...")
                    ctx.site_gen.generate_turnkey_site(
                        business_name=biz_name,
                        phone=wa,
                        rating=lead.get("gmaps_rating", "4.9"),
                        review_count=lead.get("gmaps_reviews", 50),
                        output_dir=client_dir
                    )
                if not lead.get("vercel_url"):
                    dep_res = ctx.vercel_dep.deploy(site_dir, client_clean, track="track_a_new_web", city=lead.get("city"))
                    if dep_res.get("success"):
                        lead["vercel_url"] = dep_res.get("url")
                        print(f"[+] [VERCEL LIVE] Website Jalur A aktif di: {dep_res.get('url')}")

                if not os.path.exists(pdf_path) or not lead.get("proposal_pdf"):
                    pdf_res = ctx.pdf_gen.generate_track_a(lead, client_dir, vercel_url=lead.get("vercel_url", ""), partner_info=partner_info)
                    if pdf_res.get("pdf_path") and os.path.exists(pdf_res["pdf_path"]):
                        lead["proposal_pdf"] = os.path.abspath(pdf_res["pdf_path"])
                        pdf_path = os.path.abspath(pdf_res["pdf_path"])

                pkg_res = ctx.code_pkg.package_client_code(
                    site_dir=site_dir,
                    client_slug=client_clean,
                    output_dir=client_dir,
                    business_name=biz_name,
                    domain=domain
                )
                if pkg_res.get("success"):
                    lead["package_zip"] = pkg_res.get("zip_path")
            else:
                if not os.path.exists(pdf_path) or not lead.get("vercel_url"):
                    success = execute_pipeline_for_client(url, client_dir, partner_info=partner_info)
                    if success and os.path.exists(pdf_path):
                        lead["proposal_pdf"] = os.path.abspath(pdf_path)
        else:
            # FAST JIT MODE (Sub-second preparation for Step 1 Permission Hook)
            site_dir = os.path.join(client_dir, "site")
            if track == "track_a_new_web" and not os.path.exists(os.path.join(site_dir, "index.html")):
                # Generate local prototype instantly without network/Vercel/Chromium delays
                ctx.site_gen.generate_turnkey_site(
                    business_name=biz_name,
                    phone=wa,
                    rating=lead.get("gmaps_rating", "4.9"),
                    review_count=lead.get("gmaps_reviews", 50),
                    output_dir=client_dir
                )
            print(f"  [+] [JIT READY] Persiapan Tahap 1 Selesai. Deliverable Vercel & PDF akan dibuat Just-In-Time saat prospek merespons.")

        # -------------------------------------------------------------
        # 4. OUTREACH DISPATCH (Two-Step Step 1 Permission Hook)
        # -------------------------------------------------------------
        email_status = "skipped"
        wa_status = "skipped"

        # Dispatch Email
        if target_channel == "email" and email:
            print(f"\n[EMAIL] Menyiapkan pesan pengenalan ke {email}...")
            e_res = ctx.email_disp.dispatch(
                recipient_email=email,
                business_name=biz_name,
                domain=domain,
                pdf_path=pdf_path if (pre_generate and os.path.exists(pdf_path)) else None,
                audit_signals=signals,
                dry_run=ctx.dry_run
            )
            email_status = e_res.get("mode", "failed")

        # Dispatch WhatsApp
        if target_channel == "whatsapp" and wa:
            print(f"\n[WHATSAPP] Menyiapkan pesan Izin Tahap 1 ({track}) ke {wa}...")
            w_res = ctx.wa_disp.dispatch_live(
                target_phone=wa,
                business_name=biz_name,
                domain=domain,
                pdf_path=None,  # Step 1 never attaches PDF
                audit_signals=signals,
                dry_run=ctx.dry_run,
                track=track,
                rating_text=lead.get("gmaps_rating", ""),
                step="step_1_permission"
            )
            wa_status = w_res.get("mode", "failed")

        # Record Lead in Tracker
        final_status = "dry_run" if ctx.dry_run else (
            "sent_whatsapp" if wa_status == "live_sent" else (
                "sent_email" if email_status == "live_sent" else "ready_for_permission"
            )
        )
        ctx.tracker.record_lead(domain, {
            "business_name": biz_name,
            "website_url": url,
            "whatsapp": wa,
            "email": email,
            "phone": phone_info.get("normalized_local", raw_phone),
            "primary_channel": target_channel,
            "fallback_tier": cascade["fallback_tier"],
            "track": track,
            "vercel_url": lead.get("vercel_url", ""),
            "proposal_pdf": os.path.abspath(pdf_path) if os.path.exists(pdf_path) else "",
            "outdated_signals": signals,
            "notes": f"Channel: {target_channel}. Email: {email_status}, WA: {wa_status}"
        }, status=final_status)

    # Regenerate queue dashboard
    all_leads = list(ctx.tracker.get_all_leads().values())
    queue_file = ctx.wa_disp.generate_html_queue_dashboard(all_leads)

    print("\n" + "=" * 80)
    print("  [SELESAI] PROSES SCANNING & OUTREACH SELESAI")
    print(f"  - Total Lead di Database : {len(all_leads)}")
    print(f"  - Dasbor 1-Click Antrean  : file:///{queue_file.replace(os.sep, '/')}")
    if ctx.dry_run:
        print("  - Mode Simulasi Aktif: Buka dasbor untuk 1-Click WhatsApp manual.")
    print("=" * 80)
