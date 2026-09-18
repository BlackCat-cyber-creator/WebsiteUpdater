"""
Invoice generation and payment simulation command handlers.
"""

import os
from pipeline.commands.context import CommandContext


def cmd_create_invoice(ctx: CommandContext, args) -> None:
    """Generates Rp 1.490.000 flat invoice link for a client."""
    target_domain = args.create_invoice.strip()
    lead = ctx.tracker.get_lead(target_domain) or {}
    b_name = lead.get("business_name", target_domain)
    inv = ctx.pay_gw.create_invoice(
        domain=target_domain,
        business_name=b_name,
        whatsapp=lead.get("whatsapp", ""),
        track=lead.get("track", "track_b_modernize")
    )
    lead["invoice_id"] = inv["invoice_id"]
    lead["payment_status"] = "pending_invoice"
    ctx.tracker.record_lead(target_domain, lead, status=lead.get("status", "discovered"))
    ctx.wa_disp.generate_html_queue_dashboard(list(ctx.tracker.get_all_leads().values()))
    print(f"[+] Link Pembayaran Resmi ({inv['price_display']}):\n    {inv['payment_url']}")


def cmd_simulate_payment(ctx: CommandContext, args) -> None:
    """Simulates a PAID webhook event for an invoice ID to test auto-fulfillment."""
    inv_id = args.simulate_payment.strip()
    inv = ctx.pay_gw.get_invoice(inv_id)
    if not inv:
        print(f"[!] Invoice {inv_id} tidak ditemukan.")
        return

    ctx.pay_gw.mark_as_paid(inv_id)
    domain = inv.get("domain", "")
    lead = ctx.tracker.get_lead(domain) or {}
    lead["payment_status"] = "paid"
    lead["status"] = "paid"
    ctx.tracker.record_lead(domain, lead, status="paid")

    # Fulfillment
    phone = inv.get("whatsapp") or lead.get("whatsapp")
    b_name = inv.get("business_name", domain)
    price_display = inv.get("price_display", "Rp 1.490.000")
    track = inv.get("track") or lead.get("track", "track_b_modernize")
    client_clean = ctx.vercel_dep.clean_slug(domain).replace("-", "_")
    cand1 = os.path.join("clients", client_clean)
    cand2 = os.path.join("clients", domain.replace(".", "_").replace("-", "_"))
    client_dir = cand1 if os.path.exists(cand1) or not os.path.exists(cand2) else cand2

    if track == "track_a_new_web":
        clean_dom_slug = ctx.vercel_dep.get_preview_slug(domain, track=track, city=lead.get("city"))
        v_url = lead.get("vercel_url") or f"https://{clean_dom_slug}.vercel.app"
        msg = (
            f"Halo Pimpinan *{b_name}*, pembayaran paket website resmi sebesar *{price_display}* telah kami terima lunas. Terima kasih banyak! 🙏\n\n"
            f"Tim web engineering kami sedang memproses integrasi ke domain resmi pilihan Anda. Website live aktif di: {v_url}\n"
            f"Layanan terima beres dan garansi teknis 60 hari resmi aktif per hari ini."
        )
        print(f"[SIMULASI FULFILLMENT JALUR A ke {phone}]:\n{msg}")
    else:
        site_dir = os.path.join(client_dir, "site")
        res_pack = ctx.code_pkg.package_client_code(site_dir, client_clean, output_dir=client_dir, business_name=b_name, domain=domain)
        msg = (
            f"Halo Pimpinan *{b_name}*, pembayaran pembaruan website sebesar *{price_display}* telah kami terima lunas. Terima kasih banyak! 🙏\n\n"
            f"Tim kami sedang menghubungkan versi kilat ini ke domain resmi {domain} dalam 15 menit terima beres (Zero-Downtime Guarantee).\n\n"
            f"Sebagai arsip kepemilikan Anda, berkas cadangan juga dapat diunduh di:\n📦 http://localhost:8080{res_pack.get('download_url')}"
        )
        print(f"[SIMULASI FULFILLMENT JALUR B ke {phone}]:\n{msg}")

    ctx.wa_disp.generate_html_queue_dashboard(list(ctx.tracker.get_all_leads().values()))
    print(f"[+] Simulasi webhook sukses! Status invoice {inv_id} kini: PAID.")
