"""
Batch auto-modernization command handler.
"""

import os
import json
import urllib.request
from datetime import datetime
from pipeline.commands.context import CommandContext, execute_pipeline_for_client


def cmd_auto_modernize(ctx: CommandContext, args) -> None:
    """Batch processes and modernizes all leads in queue (generate websites, deploy to Vercel, generate PDF proposals)."""
    all_leads = ctx.tracker.get_all_leads()
    print("\n" + "=" * 80)
    print("  [AUTO-MODERNIZE] MEMPROSES SELURUH ANTREAN PROSPEK SECARA OTOMATIS")
    print("=" * 80)
    processed_cnt = 0

    def process_lead(domain_lead_tuple):
        domain, lead = domain_lead_tuple
        if lead.get("status") in ["discarded", "paid"]:
            return False

        track = lead.get("track", "track_b_modernize")
        b_name = lead.get("business_name", domain)
        client_clean = ctx.vercel_dep.clean_slug(domain).replace("-", "_")
        cand1 = os.path.join("clients", client_clean)
        cand2 = os.path.join("clients", domain.replace(".", "_").replace("-", "_"))
        client_dir = cand1 if os.path.exists(cand1) or not os.path.exists(cand2) else cand2
        site_dir = os.path.join(client_dir, "site")
        pdf_path = lead.get("proposal_pdf") or os.path.join(client_dir, "client_proposal.pdf")

        print(f"\n[*] Modernizing [{track}]: {b_name} ({domain})...")

        # Download authentic Google Maps hero photo / logo if available
        os.makedirs(os.path.join(client_dir, "assets"), exist_ok=True)
        logo_target = os.path.join(client_dir, "assets", "logo.png")
        cand_logo = lead.get("logo_url") or lead.get("image_url")
        if not os.path.exists(logo_target) and cand_logo and cand_logo.startswith("http"):
            try:
                req = urllib.request.Request(cand_logo, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
                with urllib.request.urlopen(req, timeout=10) as r:
                    c_data = r.read()
                    if len(c_data) > 200:
                        with open(logo_target, "wb") as lf:
                            lf.write(c_data)
                        print(f"    [+] Foto bisnis autentik Google Maps tersimpan: {logo_target}")
            except Exception:
                pass

        if track == "track_a_new_web":
            # Track A: Turnkey Site & Vercel Deploy & Proposal PDF & Client Package ZIP
            if not os.path.exists(os.path.join(site_dir, "index.html")):
                ctx.site_gen.generate_turnkey_site(
                    business_name=b_name,
                    category=lead.get("category", ""),
                    phone=lead.get("whatsapp", ""),
                    address=lead.get("address", ""),
                    rating=lead.get("gmaps_rating") or lead.get("rating", "4.9"),
                    review_count=lead.get("gmaps_reviews") or lead.get("review_count", 50),
                    output_dir=client_dir
                )
            if not lead.get("vercel_url"):
                dep_res = ctx.vercel_dep.deploy(site_dir, client_clean, track="track_a_new_web", city=lead.get("city"))
                if dep_res.get("success"):
                    lead["vercel_url"] = dep_res.get("url")
                    print(f"    [+] Live di Vercel: {dep_res.get('url')}")

            # Executive Proposal PDF (Track A)
            if not os.path.exists(pdf_path) or not lead.get("proposal_pdf"):
                pdf_res = ctx.pdf_gen.generate_track_a(lead, client_dir, vercel_url=lead.get("vercel_url", ""))
                if pdf_res.get("pdf_path") and os.path.exists(pdf_res["pdf_path"]):
                    lead["proposal_pdf"] = os.path.abspath(pdf_res["pdf_path"])
                    pdf_path = os.path.abspath(pdf_res["pdf_path"])

            # Package Client ZIP (clean, website_prototype/ only, 0 proposals inside)
            pkg_res = ctx.code_pkg.package_client_code(
                site_dir=site_dir,
                client_slug=client_clean,
                output_dir=client_dir,
                business_name=b_name,
                domain=domain
            )
            if pkg_res.get("success"):
                lead["package_zip"] = pkg_res.get("zip_path")

            # Save pipeline_result.json
            pipe_res = {
                "domain": domain,
                "track": "track_a_new_web",
                "business_name": b_name,
                "vercel_url": lead.get("vercel_url", ""),
                "proposal_pdf": lead.get("proposal_pdf", ""),
                "proposal_html": os.path.join(client_dir, "client_proposal.html"),
                "package_zip": lead.get("package_zip", ""),
                "timestamp": datetime.now().isoformat()
            }
            with open(os.path.join(client_dir, "pipeline_result.json"), "w", encoding="utf-8") as rf:
                json.dump(pipe_res, rf, indent=2)

            lead["status"] = "proposal_ready"
            ctx.tracker.record_lead(domain, lead, status="proposal_ready")
            return True
        else:
            # Track B: Run 7-Step Pipeline (Scrape -> Audit -> Redesign -> Vercel -> PDF -> ZIP)
            target_url = lead.get("website_url") or f"https://{domain}"
            if not os.path.exists(pdf_path) or not lead.get("vercel_url"):
                execute_pipeline_for_client(target_url, client_dir)
                res_json_path = os.path.join(client_dir, "pipeline_result.json")
                if os.path.exists(res_json_path):
                    try:
                        with open(res_json_path, "r", encoding="utf-8") as rf:
                            res_data = json.load(rf)
                            if res_data.get("vercel_url"):
                                lead["vercel_url"] = res_data.get("vercel_url")
                            if res_data.get("proposal_pdf"):
                                lead["proposal_pdf"] = res_data.get("proposal_pdf")
                    except Exception:
                        pass
                if os.path.exists(pdf_path):
                    lead["proposal_pdf"] = os.path.abspath(pdf_path)
                lead["status"] = "proposal_ready"
                ctx.tracker.record_lead(domain, lead, status="proposal_ready")
                return True
        return False

    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_lead, item) for item in list(all_leads.items())]
        for future in concurrent.futures.as_completed(futures):
            try:
                if future.result():
                    processed_cnt += 1
            except Exception as exc:
                print(f"[!] Error processing lead: {exc}")

    all_updated = list(ctx.tracker.get_all_leads().values())
    out_dash = ctx.wa_disp.generate_html_queue_dashboard(all_updated)
    print("\n" + "=" * 80)
    print(f"  [SELESAI] Auto-modernisasi tuntas untuk {processed_cnt} prospek.")
    print(f"  Dasbor antrean terbarukan: {out_dash}")
    print("=" * 80)
