"""
Vercel deployment and source code packaging command handlers.
"""

import os
from pipeline.commands.context import CommandContext


def cmd_deploy_vercel(ctx: CommandContext, args) -> None:
    """Deploys a specific client's website to Vercel."""
    target_domain = args.deploy_vercel.strip()
    lead = ctx.tracker.get_lead(target_domain) or {}
    b_name = lead.get("business_name", target_domain)
    client_clean = ctx.vercel_dep.clean_slug(target_domain).replace("-", "_")
    cand1 = os.path.join("clients", client_clean)
    cand2 = os.path.join("clients", target_domain.replace(".", "_").replace("-", "_"))
    client_dir = cand1 if os.path.exists(cand1) or not os.path.exists(cand2) else cand2
    site_dir = os.path.join(client_dir, "site")

    if not os.path.exists(os.path.join(site_dir, "index.html")):
        ctx.site_gen.generate_turnkey_site(business_name=b_name, phone=lead.get("whatsapp", ""), output_dir=client_dir)

    res = ctx.vercel_dep.deploy(site_dir, client_clean)
    if res.get("success"):
        vercel_url = res.get("url")
        lead["vercel_url"] = vercel_url

        # Automatically re-generate official proposal PDF with live Vercel link & QR Code
        try:
            track = lead.get("track", "track_b_modernize")
            if track == "track_a_new_web":
                p_res = ctx.pdf_gen.generate_track_a(lead, client_dir, vercel_url=vercel_url)
            else:
                p_res = ctx.pdf_gen.generate_track_b(lead, client_dir, vercel_url=vercel_url)
            if p_res.get("pdf_path") and os.path.exists(p_res["pdf_path"]):
                lead["proposal_pdf"] = os.path.abspath(p_res["pdf_path"])
                print(f"[+] Proposal PDF resmi diperbarui dengan QR Code & Link Demo: {p_res['pdf_path']}")
        except Exception as e_pdf:
            print(f"[!] Warning: Gagal memperbarui PDF setelah deploy: {e_pdf}")

        ctx.tracker.record_lead(target_domain, lead, status=lead.get("status", "discovered"))
        ctx.wa_disp.generate_html_queue_dashboard(list(ctx.tracker.get_all_leads().values()))
        print(f"[+] Website berhasil live di Vercel: {vercel_url}")
    else:
        print(f"[!] Gagal deploy ke Vercel: {res.get('error')}")


def cmd_package(ctx: CommandContext, args) -> None:
    """Packages clean source code .ZIP and deployment guides for a client domain."""
    target_domain = args.package.strip()
    lead = ctx.tracker.get_lead(target_domain) or {}
    b_name = lead.get("business_name", target_domain)
    client_slug = target_domain.replace(".", "_").replace("-", "_")
    client_dir = os.path.join("clients", client_slug)
    site_dir = os.path.join(client_dir, "site")

    if not os.path.exists(site_dir):
        ctx.site_gen.generate_turnkey_site(business_name=b_name, phone=lead.get("whatsapp", ""), output_dir=client_dir)

    res = ctx.code_pkg.package_client_code(site_dir, client_slug, output_dir=client_dir, business_name=b_name, domain=target_domain)
    if res.get("success"):
        lead["package_zip"] = res.get("zip_path")
        ctx.tracker.record_lead(target_domain, lead, status=lead.get("status", "discovered"))
        print(f"[+] Paket Source Code siap: {res.get('zip_path')} ({res.get('size_mb')} MB)")
        print(f"    Panduan cPanel: {res.get('cpanel_guide')}")
        print(f"    Panduan SEO   : {res.get('seo_guide')}")
