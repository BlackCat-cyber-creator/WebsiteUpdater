"""
Master Autonomous Lead Finder & Outreach Orchestrator ($100 Turn-Key Engine).
Discovers Indonesian SME businesses (Dual-Track: Track A Web Baru vs Track B Modernisasi),
generates Swiss Minimalist websites or audits technical SEO gaps, deploys to Vercel,
packages clean source code for cPanel, and handles live-rate WhatsApp engagement & settlements.

Usage:
  # 1. Setup dedicated WhatsApp account (one-time QR scan):
  python auto_outreach.py --setup-wa

  # 2. Search & harvest SME leads from Google Maps (5 to 1,000 reviews):
  python auto_outreach.py --maps "distributor bahan plastik surabaya" --limit 3 --dry-run

  # 3. Launch Whitespace Minimalist Review Dashboard Server:
  python auto_outreach.py --dashboard

  # 4. Listen for client WhatsApp replies & auto-send demo/options:
  python auto_outreach.py --listen-replies

  # 5. Programmatic deployment to Vercel:
  python auto_outreach.py --deploy-vercel suncargo.sunfrozencargo.com

  # 6. Package clean source code .ZIP & cPanel guide:
  python auto_outreach.py --package suncargo.sunfrozencargo.com

  # 7. Generate $100 live-rate invoice link:
  python auto_outreach.py --create-invoice suncargo.sunfrozencargo.com
"""

import os
import sys
import argparse
import subprocess
import urllib.parse
from typing import Dict, Any, List

from pipeline.scanner.business_scanner import IndonesianBusinessScanner
from pipeline.scanner.agent_reach_enricher import AgentReachContactEnricher
from pipeline.outreach.email_dispatcher import EmailDispatcher
from pipeline.outreach.whatsapp_dispatcher import WhatsAppDispatcher
from pipeline.outreach.tracker import OutreachTracker
from pipeline.deployer.vercel_deployer import VercelDeployer
from pipeline.delivery.code_packager import CodePackager
from pipeline.payment.payment_gateway import PaymentGateway
from pipeline.site_generator import SiteGenerator

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass


def execute_pipeline_for_client(url: str, output_dir: str) -> bool:
    """Executes the complete 7-step website modernization pipeline as a subprocess."""
    print(f"\n[PIPELINE] Running modernization & proposal generation for: {url}")
    cmd = [
        sys.executable,
        "run_pipeline.py",
        "--url", url,
        "--output", output_dir
    ]
    res = subprocess.run(cmd, capture_output=False)
    return res.returncode == 0


MID_TIER_CATEGORIES = {
    "b2b_distributor": [
        "supplier bahan kimia industri cikarang",
        "distributor packaging karton box surabaya",
        "distributor frozen food semarang",
        "supplier alat teknik industri jakarta"
    ],
    "ekspedisi_spesialis": [
        "ekspedisi surabaya makassar",
        "sewa truk reefer pendingin jakarta",
        "jasa tronton trailer bekasi",
        "kargo alat berat balikpapan"
    ],
    "kontraktor_komersial": [
        "kontraktor interior kantor surabaya",
        "kontraktor hvac tata udara cikarang",
        "jasa epoxy lantai pabrik bekasi"
    ],
    "manufaktur_menengah": [
        "karoseri box pendingin bekasi",
        "pabrik plastik kemasan sidoarjo",
        "konveksi seragam kerja pabrik bandung"
    ],
    "klinik_spesialis": [
        "klinik estetika kecantikan surabaya",
        "klinik gigi dental care bandung",
        "laboratorium klinik swasta medan"
    ]
}


def main():
    parser = argparse.ArgumentParser(description="Autonomous Indonesian Mid-Tier Business Scanner & Outreach System ($100 Turn-Key Engine)")
    parser.add_argument("--setup-wa", action="store_true", help="Launch interactive WhatsApp Web QR setup for dedicated account")
    parser.add_argument("--maps", type=str, default="", help="Search local developing SME businesses directly from Google Maps (e.g. 'distributor bahan plastik surabaya')")
    parser.add_argument("--query", type=str, default="", help="Search query (e.g. 'ekspedisi surabaya makassar')")
    parser.add_argument("--category", choices=list(MID_TIER_CATEGORIES.keys()), default=None,
                        help="Target curated mid-tier niche")
    parser.add_argument("--domain", type=str, default="", help="Direct single target domain (e.g. 'suncargo.sunfrozencargo.com')")
    parser.add_argument("--limit", type=int, default=3, help="Maximum number of candidate leads to process per run")
    parser.add_argument("--track", choices=["a", "b", "all"], default="all", help="Filter target processing track (a = Web Baru di Vercel, b = Modernisasi & SEO, all = keduanya)")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Simulate outreach without sending live messages (Default: True)")
    parser.add_argument("--live", action="store_true", help="Enable actual live outreach via dedicated SMTP and WhatsApp")
    parser.add_argument("--test-email", type=str, default="", help="Send a test proposal email to this address to verify SMTP connection")
    parser.add_argument("--generate-queue", action="store_true", help="Regenerate clients/outreach_queue.html from tracker history")
    parser.add_argument("--channel", choices=["all", "whatsapp", "email"], default="all", help="Target communication channel")
    parser.add_argument("--dashboard", action="store_true", help="Launch interactive Review & Approval dashboard server on localhost")
    parser.add_argument("--approve", type=str, default="", help="Approve and send WhatsApp + Email to a specific domain")
    parser.add_argument("--discard", type=str, default="", help="Discard/remove a lead from the outreach queue")
    parser.add_argument("--listen-replies", action="store_true", help="Scan WhatsApp Web for incoming replies and auto-dispatch demo/options")
    parser.add_argument("--deploy-vercel", type=str, default="", help="Deploy a specific client's website to Vercel")
    parser.add_argument("--package", type=str, default="", help="Package clean source code .ZIP and guides for a client domain")
    parser.add_argument("--create-invoice", type=str, default="", help="Generate $100 live-rate invoice with payment link for a client")
    parser.add_argument("--simulate-payment", type=str, default="", help="Simulate a PAID webhook event for an invoice ID to test auto-fulfillment")

    args = parser.parse_args()

    # Determine live vs dry-run
    is_live = bool(args.live)
    dry_run = not is_live

    # Initialize core modules
    tracker = OutreachTracker()
    scanner = IndonesianBusinessScanner()
    enricher = AgentReachContactEnricher()
    email_disp = EmailDispatcher()
    wa_disp = WhatsAppDispatcher()
    site_gen = SiteGenerator()
    vercel_dep = VercelDeployer()
    code_pkg = CodePackager()
    pay_gw = PaymentGateway()

    # 1. Setup WhatsApp Session
    if args.setup_wa:
        wa_disp.setup_dedicated_session()
        return

    # 2. Launch Interactive Web Dashboard Server
    if args.dashboard:
        from pipeline.outreach.dashboard_server import start_dashboard_server
        start_dashboard_server()
        return

    # 3. Listen for Incoming WhatsApp Replies
    if args.listen_replies:
        replies = wa_disp.check_incoming_replies(auto_respond=True)
        print(f"[+] Selesai memeriksa balasan. Total balasan diproses: {len(replies)}")
        return

    # 4. Programmatic Vercel Deploy CLI
    if args.deploy_vercel:
        target_domain = args.deploy_vercel.strip()
        lead = tracker.get_lead(target_domain) or {}
        b_name = lead.get("business_name", target_domain)
        client_slug = target_domain.replace(".", "_").replace("-", "_")
        client_dir = os.path.join("clients", client_slug)
        site_dir = os.path.join(client_dir, "site")

        if not os.path.exists(os.path.join(site_dir, "index.html")):
            site_gen.generate_turnkey_site(business_name=b_name, phone=lead.get("whatsapp", ""), output_dir=client_dir)

        res = vercel_dep.deploy(site_dir, client_slug)
        if res.get("success"):
            lead["vercel_url"] = res.get("url")
            tracker.record_lead(target_domain, lead, status=lead.get("status", "discovered"))
            wa_disp.generate_html_queue_dashboard(list(tracker.get_all_leads().values()))
            print(f"[+] Website berhasil live di Vercel: {res.get('url')}")
        else:
            print(f"[!] Gagal deploy ke Vercel: {res.get('error')}")
        return

    # 5. Package Source Code .ZIP CLI
    if args.package:
        target_domain = args.package.strip()
        lead = tracker.get_lead(target_domain) or {}
        b_name = lead.get("business_name", target_domain)
        client_slug = target_domain.replace(".", "_").replace("-", "_")
        client_dir = os.path.join("clients", client_slug)
        site_dir = os.path.join(client_dir, "site")

        if not os.path.exists(site_dir):
            site_gen.generate_turnkey_site(business_name=b_name, phone=lead.get("whatsapp", ""), output_dir=client_dir)

        res = code_pkg.package_client_code(site_dir, client_slug, output_dir=client_dir, business_name=b_name, domain=target_domain)
        if res.get("success"):
            lead["package_zip"] = res.get("zip_path")
            tracker.record_lead(target_domain, lead, status=lead.get("status", "discovered"))
            print(f"[+] Paket Source Code siap: {res.get('zip_path')} ({res.get('size_mb')} MB)")
            print(f"    Panduan cPanel: {res.get('cpanel_guide')}")
            print(f"    Panduan SEO   : {res.get('seo_guide')}")
        return

    # 6. Create $100 Invoice CLI
    if args.create_invoice:
        target_domain = args.create_invoice.strip()
        lead = tracker.get_lead(target_domain) or {}
        b_name = lead.get("business_name", target_domain)
        inv = pay_gw.create_invoice(
            domain=target_domain,
            business_name=b_name,
            whatsapp=lead.get("whatsapp", ""),
            track=lead.get("track", "track_b_modernize")
        )
        lead["invoice_id"] = inv["invoice_id"]
        lead["payment_status"] = "pending_invoice"
        tracker.record_lead(target_domain, lead, status=lead.get("status", "discovered"))
        wa_disp.generate_html_queue_dashboard(list(tracker.get_all_leads().values()))
        print(f"[+] Link Pembayaran Resmi ({inv['price_display']}):\n    {inv['payment_url']}")
        return

    # 7. Simulate Payment Webhook CLI
    if args.simulate_payment:
        inv_id = args.simulate_payment.strip()
        inv = pay_gw.get_invoice(inv_id)
        if not inv:
            print(f"[!] Invoice {inv_id} tidak ditemukan.")
            return

        pay_gw.mark_as_paid(inv_id)
        domain = inv.get("domain", "")
        lead = tracker.get_lead(domain) or {}
        lead["payment_status"] = "paid"
        lead["status"] = "paid"
        tracker.record_lead(domain, lead, status="paid")

        # Fulfillment
        phone = inv.get("whatsapp") or lead.get("whatsapp")
        b_name = inv.get("business_name", domain)
        price_display = inv.get("price_display", "$100 USD")
        track = inv.get("track") or lead.get("track", "track_b_modernize")
        client_slug = domain.replace(".", "_").replace("-", "_")

        if track == "track_a_new_web":
            v_url = lead.get("vercel_url", f"https://{client_slug}.vercel.app")
            msg = (
                f"Halo Pimpinan *{b_name}*, pembayaran *{price_display}* telah kami terima dengan lunas. Terima kasih banyak! 🙏\n\n"
                f"Website modern resmi Anda di {v_url} kini telah aktif dan resmi menjadi milik bisnis Anda seutuhnya."
            )
            print(f"[SIMULASI FULFILLMENT JALUR A ke {phone}]:\n{msg}")
        else:
            site_dir = os.path.join("clients", client_slug, "site")
            res_pack = code_pkg.package_client_code(site_dir, client_slug, output_dir=os.path.join("clients", client_slug), business_name=b_name, domain=domain)
            msg = (
                f"Halo Pimpinan *{b_name}*, pembayaran *{price_display}* telah kami terima dengan lunas. Terima kasih banyak! 🙏\n\n"
                f"Berikut tautan unduh Source Code resmi Anda:\n📦 http://localhost:8080{res_pack.get('download_url')}"
            )
            print(f"[SIMULASI FULFILLMENT JALUR B ke {phone}]:\n{msg}")

        wa_disp.generate_html_queue_dashboard(list(tracker.get_all_leads().values()))
        print(f"[+] Simulasi webhook sukses! Status invoice {inv_id} kini: PAID.")
        return

    # 8. Approve specific lead via CLI
    if args.approve:
        target_domain = args.approve.strip()
        lead = tracker.get_lead(target_domain)
        if not lead:
            print(f"[!] Lead {target_domain} tidak ditemukan di database.")
            return
        b_name = lead.get("business_name", target_domain)
        pdf_path = lead.get("proposal_pdf", "")
        track = lead.get("track", "track_b_modernize")
        print(f"\n[*] APPROVE & DISPATCH ({track}): {b_name} ({target_domain})")

        if lead.get("email") and track == "track_b_modernize":
            email_disp.dispatch(
                recipient_email=lead["email"],
                business_name=b_name,
                domain=target_domain,
                pdf_path=pdf_path,
                audit_signals=lead.get("outdated_signals", []),
                dry_run=False
            )
        if lead.get("whatsapp"):
            wa_disp.dispatch_live(
                target_phone=lead["whatsapp"],
                business_name=b_name,
                domain=target_domain,
                pdf_path=pdf_path,
                audit_signals=lead.get("outdated_signals", []),
                dry_run=False,
                track=track,
                rating_text=lead.get("gmaps_rating", "")
            )
        tracker.record_lead(target_domain, lead, status="sent_all" if track == "track_b_modernize" else "sent_whatsapp")
        all_leads = list(tracker.get_all_leads().values())
        wa_disp.generate_html_queue_dashboard(all_leads)
        print(f"[+] SELESAI! Penawaran berhasil dikirim ke {target_domain}.")
        return

    # 9. Discard specific lead via CLI
    if args.discard:
        target_domain = args.discard.strip()
        lead = tracker.get_lead(target_domain)
        if not lead:
            print(f"[!] Lead {target_domain} tidak ditemukan di database.")
            return
        tracker.record_lead(target_domain, lead, status="discarded")
        all_leads = list(tracker.get_all_leads().values())
        wa_disp.generate_html_queue_dashboard(all_leads)
        print(f"[+] Lead {target_domain} berhasil di-discard dari antrean.")
        return

    # 10. Regenerate Dashboard Queue Only
    if args.generate_queue:
        all_leads = list(tracker.get_all_leads().values())
        out_html = wa_disp.generate_html_queue_dashboard(all_leads)
        print(f"[+] Outreach Queue Dashboard updated: {out_html}")
        return

    # 11. Test Email Sending
    if args.test_email:
        test_recipient = args.test_email.strip()
        print(f"\n[*] Menguji koneksi SMTP pengiriman email ke: {test_recipient}...")
        sample_pdf = os.path.abspath(os.path.join("clients", "suncargo_sunfrozencargo_com", "client_proposal.pdf"))
        res = email_disp.dispatch(
            recipient_email=test_recipient,
            business_name="Test Enterprise",
            domain="test-bisnis.com",
            pdf_path=sample_pdf if os.path.exists(sample_pdf) else None,
            audit_signals=["Mobile responsiveness", "SEO Meta Structure"],
            dry_run=False
        )
        if res.get("success") and res.get("mode") == "live_sent":
            print(f"\n[+] BERHASIL! {res.get('message')}")
        else:
            print(f"\n[!] GAGAL: {res.get('message')}")
        return

    # Main Lead Harvesting Flow
    mode_label = "🔴 LIVE OUTREACH (DEDICATED ACCOUNTS)" if is_live else "🟢 DRY-RUN SIMULATION (SAFE MODE)"
    print("=" * 80)
    print("  AUTONOMOUS INDONESIAN SME BUSINESS SCANNER & OUTREACH ENGINE ($100 TURN-KEY)")
    print(f"  Mode: {mode_label}")
    print(f"  Track Filter: {args.track.upper()}")
    print("=" * 80)

    candidate_leads: List[Dict[str, Any]] = []

    if args.domain:
        clean_url = args.domain if args.domain.startswith("http") else f"https://{args.domain}"
        print(f"\n[*] Inspecting single target domain: {clean_url}")
        inspected = scanner.inspect_website(clean_url)
        if inspected:
            inspected["track"] = "track_b_modernize"
            candidate_leads.append(inspected)
        else:
            print(f"[!] Unable to fetch or inspect domain: {clean_url}")
    elif args.maps:
        from pipeline.scanner.google_maps_scanner import GoogleMapsBusinessScanner
        maps_scanner = GoogleMapsBusinessScanner()
        print(f"\n[*] Menelusuri Google Maps untuk UKM berkembang: '{args.maps}' (limit: {args.limit})")
        found = maps_scanner.search_local_businesses(args.maps, limit=args.limit)
        candidate_leads.extend(found)
        print(f"[+] Berhasil mengumpulkan {len(candidate_leads)} prospek UKM dari Google Maps.")
    elif args.category:
        print(f"\n[*] Target Kategori Bisnis Menengah: '{args.category}' (Limit: {args.limit})")
        preset_queries = MID_TIER_CATEGORIES.get(args.category, [])
        for q in preset_queries:
            if len(candidate_leads) >= args.limit:
                break
            needed = args.limit - len(candidate_leads)
            found = scanner.search_businesses_by_query(q, limit=needed)
            for f in found:
                if not any(c["domain"] == f["domain"] for c in candidate_leads):
                    f["track"] = "track_b_modernize"
                    candidate_leads.append(f)
        print(f"[+] Berhasil menemukan {len(candidate_leads)} kandidat bisnis menengah.")
    elif args.query:
        print(f"\n[*] Searching for Indonesian business leads with query: '{args.query}' (limit: {args.limit})")
        found = scanner.search_businesses_by_query(args.query, limit=args.limit)
        for f in found:
            f["track"] = "track_b_modernize"
            candidate_leads.append(f)
        print(f"[+] Found {len(candidate_leads)} candidate websites matching criteria.")
    else:
        print("[!] Mohon tentukan target pencarian dengan:")
        print("    1. Google Maps (SME)  : python auto_outreach.py --maps 'distributor plastik surabaya' --limit 3")
        print("    2. Kategori Menengah  : python auto_outreach.py --category ekspedisi_spesialis --limit 3")
        print("    3. Domain Langsung    : python auto_outreach.py --domain contoh-bisnis.com")
        print("    4. Dasbor Interaktif  : python auto_outreach.py --dashboard")
        return

    # Filter candidates by track if requested
    if args.track == "a":
        candidate_leads = [c for c in candidate_leads if c.get("track") == "track_a_new_web"]
    elif args.track == "b":
        candidate_leads = [c for c in candidate_leads if c.get("track") != "track_a_new_web"]

    if not candidate_leads:
        print("[!] Tidak ada prospek baru yang memenuhi kriteria pencarian.")
        return

    # Process candidates
    for idx, lead in enumerate(candidate_leads, 1):
        domain = lead["domain"]
        biz_name = lead["business_name"]
        url = lead.get("website_url", "")
        wa = lead.get("whatsapp", "")
        email = lead.get("email", "")
        signals = lead.get("outdated_signals", [])
        track = lead.get("track", "track_b_modernize")

        print(f"\n" + "-" * 75)
        print(f"[{idx}/{len(candidate_leads)}] MEMPROSES PROSPEK: {biz_name} ({domain})")
        print(f"  Jalur: {'[JALUR A: BUAT WEB BARU]' if track == 'track_a_new_web' else '[JALUR B: MODERNISASI & SEO]'}")
        print(f"  WhatsApp: {wa or 'Belum ditemukan'}")
        print(f"  Email: {email or 'Belum ditemukan'}")
        print("-" * 75)

        # Check duplicate tracker
        if tracker.is_already_contacted(domain, wa, email):
            print(f"[SKIP] Prospek {domain} sudah pernah dihubungi sebelumnya (mencegah spam).")
            continue

        # Social contact enrichment if phone or email missing
        if not wa or not email:
            print("[*] Mencari kontak tambahan melalui Agent-Reach social search...")
            enriched = enricher.enrich_from_social_bio(biz_name)
            if not wa and enriched.get("whatsapp"):
                wa = enriched["whatsapp"]
                lead["whatsapp"] = wa
            if not email and enriched.get("email"):
                email = enriched["email"]
                lead["email"] = email

        client_slug = domain.replace(".", "_").replace("-", "_")
        client_dir = os.path.join("clients", client_slug)
        pdf_path = os.path.join(client_dir, "client_proposal.pdf")

        # Deliverables generation
        if track == "track_a_new_web":
            # Track A: Generate Swiss Minimalist Turnkey Site
            site_dir = os.path.join(client_dir, "site")
            if not os.path.exists(os.path.join(site_dir, "index.html")):
                print(f"[*] Menyiapkan website modern Swiss Minimalist untuk {biz_name}...")
                site_gen.generate_turnkey_site(
                    business_name=biz_name,
                    phone=wa,
                    rating=lead.get("gmaps_rating", "4.9"),
                    review_count=lead.get("gmaps_reviews", 50),
                    output_dir=client_dir
                )
        else:
            # Track B: Run 7-step pipeline if PDF doesn't exist yet
            if not os.path.exists(pdf_path):
                success = execute_pipeline_for_client(url, client_dir)
                if not success or not os.path.exists(pdf_path):
                    print(f"[!] Gagal membuat proposal PDF untuk {domain}. Melewati outreach.")
                    continue

        if os.path.exists(pdf_path):
            lead["proposal_pdf"] = os.path.abspath(pdf_path)

        # Dispatch Email (Track B only)
        email_status = "skipped"
        if track == "track_b_modernize" and args.channel in ["all", "email"] and email:
            print(f"\n[EMAIL] Menyiapkan email proposal ke {email}...")
            e_res = email_disp.dispatch(
                recipient_email=email,
                business_name=biz_name,
                domain=domain,
                pdf_path=pdf_path,
                audit_signals=signals,
                dry_run=dry_run
            )
            email_status = e_res.get("mode", "failed")

        # Dispatch WhatsApp
        wa_status = "skipped"
        if args.channel in ["all", "whatsapp"] and wa:
            print(f"\n[WHATSAPP] Menyiapkan pesan WhatsApp ({track}) ke {wa}...")
            w_res = wa_disp.dispatch_live(
                target_phone=wa,
                business_name=biz_name,
                domain=domain,
                pdf_path=pdf_path if track == "track_b_modernize" else None,
                audit_signals=signals,
                dry_run=dry_run,
                track=track,
                rating_text=lead.get("gmaps_rating", "")
            )
            wa_status = w_res.get("mode", "failed")

        # Record Lead in Tracker
        final_status = "dry_run" if dry_run else (
            "sent_all" if email_status == "live_sent" and wa_status == "live_sent" else (
                "sent_whatsapp" if wa_status == "live_sent" else (
                    "sent_email" if email_status == "live_sent" else "proposal_ready"
                )
            )
        )
        tracker.record_lead(domain, {
            "business_name": biz_name,
            "website_url": url,
            "whatsapp": wa,
            "email": email,
            "track": track,
            "proposal_pdf": os.path.abspath(pdf_path) if os.path.exists(pdf_path) else "",
            "outdated_signals": signals,
            "notes": f"Email: {email_status}, WA: {wa_status}"
        }, status=final_status)

    # Regenerate queue dashboard
    all_leads = list(tracker.get_all_leads().values())
    queue_file = wa_disp.generate_html_queue_dashboard(all_leads)

    print("\n" + "=" * 80)
    print("  [SELESAI] PROSES SCANNING & OUTREACH SELESAI")
    print(f"  - Total Lead di Database : {len(all_leads)}")
    print(f"  - Dasbor 1-Click Antrean  : file:///{queue_file.replace(os.sep, '/')}")
    if dry_run:
        print("  - Mode Simulasi Aktif: Buka dasbor untuk 1-Click WhatsApp manual.")
    print("=" * 80)


if __name__ == "__main__":
    main()
