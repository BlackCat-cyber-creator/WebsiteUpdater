"""
Lead operations command handlers: approve, discard, queue generation, test email.
"""

import os
import shutil
from pipeline.commands.context import CommandContext


def cmd_approve(ctx: CommandContext, args) -> None:
    """Approves and dispatches WhatsApp + Email to a specific domain."""
    target_domain = args.approve.strip()
    lead = ctx.tracker.get_lead(target_domain)
    if not lead:
        print(f"[!] Lead {target_domain} tidak ditemukan di database.")
        return

    b_name = lead.get("business_name", target_domain)
    pdf_path = lead.get("proposal_pdf", "")
    track = lead.get("track", "track_b_modernize")
    print(f"\n[*] APPROVE & DISPATCH ({track}): {b_name} ({target_domain})")

    # Just-In-Time Asset Verification & Generation
    client_clean = ctx.vercel_dep.clean_slug(target_domain).replace("-", "_")
    client_dir = os.path.join("clients", client_clean)
    os.makedirs(client_dir, exist_ok=True)
    site_dir = os.path.join(client_dir, "site")

    if track == "track_a_new_web":
        if not os.path.exists(os.path.join(site_dir, "index.html")):
            ctx.site_gen.generate_turnkey_site(
                business_name=b_name,
                phone=lead.get("whatsapp", ""),
                output_dir=client_dir
            )
        if not lead.get("vercel_url"):
            print(f"[*] [JIT] Deploying Turnkey Website to Vercel for {b_name}...")
            dep_res = ctx.vercel_dep.deploy(site_dir, client_clean, track="track_a_new_web", city=lead.get("city"))
            if dep_res.get("success"):
                lead["vercel_url"] = dep_res.get("url")
                print(f"[+] [VERCEL LIVE] {dep_res.get('url')}")

        print(f"[*] [JIT] Generating Executive PDF Proposal (with QR Code) for {b_name}...")
        pdf_res = ctx.pdf_gen.generate_track_a(lead, client_dir, vercel_url=lead.get("vercel_url", ""))
        pdf_path = pdf_res.get("pdf_path", "")
        lead["proposal_pdf"] = pdf_path
    else:
        if not lead.get("vercel_url") or not pdf_path or not os.path.exists(pdf_path):
            print(f"[*] [JIT] Running modernization pipeline for {target_domain}...")
            from pipeline.commands.context import execute_pipeline_for_client
            target_url = lead.get("website_url") or f"https://{target_domain}"
            execute_pipeline_for_client(target_url, client_dir)
            cand_pdf = os.path.join(client_dir, "client_proposal.pdf")
            if os.path.exists(cand_pdf):
                pdf_path = os.path.abspath(cand_pdf)
                lead["proposal_pdf"] = pdf_path

    if lead.get("email") and track == "track_b_modernize":
        ctx.email_disp.dispatch(
            recipient_email=lead["email"],
            business_name=b_name,
            domain=target_domain,
            pdf_path=pdf_path,
            audit_signals=lead.get("outdated_signals", []),
            dry_run=False
        )
    if lead.get("whatsapp"):
        ctx.wa_disp.dispatch_live(
            target_phone=lead["whatsapp"],
            business_name=b_name,
            domain=target_domain,
            pdf_path=pdf_path,
            audit_signals=lead.get("outdated_signals", []),
            dry_run=False,
            track=track,
            rating_text=lead.get("gmaps_rating", ""),
            step="step_2_delivery"
        )

    ctx.tracker.record_lead(target_domain, lead, status="sent_step2" if track == "track_b_modernize" else "sent_step2")
    all_leads = list(ctx.tracker.get_all_leads().values())
    ctx.wa_disp.generate_html_queue_dashboard(all_leads)
    print(f"[+] SELESAI! Penawaran berhasil dikirim ke {target_domain}.")


def cmd_discard(ctx: CommandContext, args) -> None:
    """Discards a lead and physically removes client scratch folder from disk."""
    target_domain = args.discard.strip()
    lead = ctx.tracker.get_lead(target_domain)
    if not lead:
        print(f"[!] Lead {target_domain} tidak ditemukan di database.")
        return

    clients_dir = os.path.abspath("clients")
    clean_slug = ctx.vercel_dep.clean_slug(target_domain).replace("-", "_")
    cands = set()
    if lead.get("proposal_pdf"):
        cands.add(os.path.dirname(os.path.abspath(lead["proposal_pdf"])))
    if lead.get("package_zip"):
        cands.add(os.path.dirname(os.path.abspath(lead["package_zip"])))
    cands.add(os.path.join(clients_dir, clean_slug))
    cands.add(os.path.join(clients_dir, target_domain.replace(".", "_").replace("-", "_")))
    cands.add(os.path.join(clients_dir, target_domain.replace(".", "_")))
    cands.add(os.path.join(clients_dir, target_domain))

    deleted_dirs = []
    for target_dir in cands:
        try:
            target_dir = os.path.abspath(target_dir)
            if (
                os.path.exists(target_dir)
                and os.path.isdir(target_dir)
                and os.path.commonpath([clients_dir, target_dir]) == clients_dir
                and target_dir != clients_dir
            ):
                bname = os.path.basename(target_dir)
                if not bname.startswith(".") and bname != "outreach_drafts":
                    shutil.rmtree(target_dir, ignore_errors=True)
                    deleted_dirs.append(target_dir)
                    print(f"[*] Folder fisik klien berhasil dihapus: {target_dir}")
        except Exception as e:
            print(f"[!] Error saat menghapus folder {target_dir}: {e}")

    try:
        ctx.vercel_dep.delete_project(target_domain)
    except Exception as ve:
        print(f"[!] Warning deleting Vercel project: {ve}")

    ctx.tracker.record_lead(target_domain, {
        "business_name": lead.get("business_name", target_domain),
        "notes": f"Discarded via CLI. Deleted dirs: {deleted_dirs}"
    }, status="discarded")
    all_leads = list(ctx.tracker.get_all_leads().values())
    ctx.wa_disp.generate_html_queue_dashboard(all_leads)
    print(f"[+] Lead {target_domain} berhasil di-discard dan folder fisik dibersihkan dari disk.")


def cmd_generate_queue(ctx: CommandContext, args) -> None:
    """Regenerates clients/outreach_queue.html from tracker history."""
    all_leads = list(ctx.tracker.get_all_leads().values())
    out_html = ctx.wa_disp.generate_html_queue_dashboard(all_leads)
    print(f"[+] Outreach Queue Dashboard updated: {out_html}")


def cmd_test_email(ctx: CommandContext, args) -> None:
    """Sends a test proposal email to verify SMTP connection."""
    test_recipient = args.test_email.strip()
    print(f"\n[*] Menguji koneksi SMTP pengiriman email ke: {test_recipient}...")
    sample_pdf = os.path.abspath(os.path.join("clients", "suncargo_sunfrozencargo_com", "client_proposal.pdf"))
    res = ctx.email_disp.dispatch(
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
