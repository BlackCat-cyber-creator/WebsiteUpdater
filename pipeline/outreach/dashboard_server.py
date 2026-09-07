"""
Interactive Local Dashboard Server for Web Outreach Pipeline.
Serves the clean Review & Approval Queue (clients/outreach_queue.html),
interactive checkout pages (/pay/{invoice_id}), payment webhook handlers,
and automatic client fulfillment dispatches.
"""

import os
import json
import urllib.parse
import webbrowser
import threading
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from typing import Optional, Dict, Any, List

from pipeline.outreach.tracker import OutreachTracker
from pipeline.outreach.email_dispatcher import EmailDispatcher
from pipeline.outreach.whatsapp_dispatcher import WhatsAppDispatcher
from pipeline.deployer.vercel_deployer import VercelDeployer
from pipeline.delivery.code_packager import CodePackager
from pipeline.payment.payment_gateway import PaymentGateway
from pipeline.site_generator import SiteGenerator

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CLIENTS_DIR = os.path.join(BASE_DIR, "clients")


class OutreachDashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=CLIENTS_DIR, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # 1. Serve Outreach Queue Dashboard
        if path in ["/", "/index.html", "/queue", "/dashboard"]:
            queue_file = os.path.join(CLIENTS_DIR, "outreach_queue.html")
            if os.path.exists(queue_file):
                with open(queue_file, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
            else:
                self.send_error(404, "outreach_queue.html not found")
                return

        # 2. Interactive Payment Checkout Page (/pay/{invoice_id})
        if path.startswith("/pay/"):
            inv_id = path.replace("/pay/", "").strip()
            pg = PaymentGateway()
            inv = pg.get_invoice(inv_id)
            if not inv:
                self.send_error(404, f"Invoice {inv_id} tidak ditemukan.")
                return

            html_page = self._render_checkout_page(inv)
            content = html_page.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
            return

        # 3. Direct Source Code Package Download (/api/download-package?client=...)
        if path == "/api/download-package":
            client_param = query.get("client", [""])[0].strip()
            if not client_param:
                self._send_json({"success": False, "error": "Client parameter required"}, 400)
                return

            client_slug = client_param.replace(".", "_").replace("-", "_")
            client_dir = os.path.join(CLIENTS_DIR, client_slug)

            # Look for existing zip
            target_zip = None
            if os.path.exists(client_dir):
                for f in os.listdir(client_dir):
                    if f.endswith(".zip"):
                        target_zip = os.path.join(client_dir, f)
                        break

            # If not yet created, package on the fly
            if not target_zip:
                site_dir = os.path.join(client_dir, "site")
                if os.path.exists(site_dir):
                    cp = CodePackager()
                    res = cp.package_client_code(site_dir, client_slug, output_dir=client_dir)
                    target_zip = res.get("zip_path")

            if target_zip and os.path.exists(target_zip):
                with open(target_zip, "rb") as f:
                    zip_data = f.read()
                filename = os.path.basename(target_zip)
                self.send_response(200)
                self.send_header("Content-Type", "application/zip")
                self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
                self.send_header("Content-Length", str(len(zip_data)))
                self.end_headers()
                self.wfile.write(zip_data)
                return
            else:
                self._send_json({"success": False, "error": "Source code package not found or not yet generated"}, 404)
                return

        # 4. Status API
        if path == "/api/status":
            tracker = OutreachTracker()
            leads = tracker.get_all_leads()
            active = [l for l in leads.values() if l.get("status") != "discarded"]
            payload = json.dumps({"active_leads": len(active), "total_leads": len(leads)}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        # Fallback to static file serving from clients/
        return super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # Read JSON body if present
        content_len = int(self.headers.get("Content-Length", 0))
        body = {}
        if content_len > 0:
            try:
                raw_body = self.rfile.read(content_len).decode("utf-8")
                body = json.loads(raw_body)
            except Exception:
                pass

        # -------------------------------------------------------------
        # 1. ACTION: APPROVE & DISPATCH
        # -------------------------------------------------------------
        if path == "/api/approve":
            domain = body.get("domain") or (query.get("domain", [""])[0])
            domain = domain.strip()
            if not domain:
                self._send_json({"success": False, "error": "Domain parameter missing"}, 400)
                return

            tracker = OutreachTracker()
            lead = tracker.get_lead(domain)
            if not lead:
                self._send_json({"success": False, "error": f"Lead {domain} not found in database"}, 404)
                return

            b_name = lead.get("business_name", domain)
            wa = lead.get("whatsapp", "")
            email = lead.get("email", "")
            signals = lead.get("outdated_signals", [])
            pdf_path = lead.get("proposal_pdf", "")
            track = lead.get("track", "track_b_modernize")

            email_disp = EmailDispatcher()
            wa_disp = WhatsAppDispatcher()

            email_sent = False
            wa_sent = False
            errors = []

            # A. Send Email (Track B only, if email exists)
            if email and track == "track_b_modernize":
                e_res = email_disp.dispatch(
                    recipient_email=email,
                    business_name=b_name,
                    domain=domain,
                    pdf_path=pdf_path,
                    audit_signals=signals,
                    dry_run=False
                )
                if e_res.get("success") and e_res.get("mode") == "live_sent":
                    email_sent = True
                else:
                    errors.append(f"Email: {e_res.get('message')}")

            # B. Send WhatsApp (Both Track A & Track B)
            if wa:
                w_res = wa_disp.dispatch_live(
                    target_phone=wa,
                    business_name=b_name,
                    domain=domain,
                    pdf_path=pdf_path,
                    audit_signals=signals,
                    dry_run=False,
                    track=track,
                    rating_text=lead.get("gmaps_rating", "")
                )
                if w_res.get("success") and w_res.get("mode") == "live_sent":
                    wa_sent = True
                else:
                    errors.append(f"WhatsApp: {w_res.get('message')}")

            final_status = "sent_all" if (email_sent and wa_sent) else (
                "sent_whatsapp" if wa_sent else ("sent_email" if email_sent else "failed")
            )

            tracker.record_lead(domain, {
                "business_name": b_name,
                "whatsapp": wa,
                "email": email,
                "track": track,
                "proposal_pdf": pdf_path,
                "outdated_signals": signals,
                "notes": f"Approved via Dashboard. Email: {email_sent}, WA: {wa_sent}"
            }, status=final_status)

            all_leads = list(tracker.get_all_leads().values())
            wa_disp.generate_html_queue_dashboard(all_leads)

            self._send_json({
                "success": (email_sent or wa_sent),
                "status": final_status,
                "email_sent": email_sent,
                "wa_sent": wa_sent,
                "errors": errors,
                "message": f"Penawaran sukses dikirim! (WA: {'✅' if wa_sent else '❌'})"
            })
            return

        # -------------------------------------------------------------
        # 2. ACTION: DISCARD
        # -------------------------------------------------------------
        if path == "/api/discard":
            domain = body.get("domain") or (query.get("domain", [""])[0])
            domain = domain.strip()
            tracker = OutreachTracker()
            lead = tracker.get_lead(domain)
            if lead:
                tracker.record_lead(domain, {
                    "business_name": lead.get("business_name", domain),
                    "notes": "Discarded from dashboard"
                }, status="discarded")

                all_leads = list(tracker.get_all_leads().values())
                wa_disp = WhatsAppDispatcher()
                wa_disp.generate_html_queue_dashboard(all_leads)

            self._send_json({"success": True, "message": f"Prospek {domain} di-discard."})
            return

        # -------------------------------------------------------------
        # 3. ACTION: DEPLOY VERCEL
        # -------------------------------------------------------------
        if path == "/api/deploy-vercel":
            domain = body.get("domain") or (query.get("domain", [""])[0])
            domain = domain.strip()
            tracker = OutreachTracker()
            lead = tracker.get_lead(domain)
            if not lead:
                self._send_json({"success": False, "error": f"Lead {domain} not found"}, 404)
                return

            client_slug = domain.replace(".", "_").replace("-", "_")
            client_dir = os.path.join(CLIENTS_DIR, client_slug)
            site_dir = os.path.join(client_dir, "site")

            # If Track A and site not generated yet, generate turnkey site
            if not os.path.exists(os.path.join(site_dir, "index.html")):
                sg = SiteGenerator()
                sg.generate_turnkey_site(
                    business_name=lead.get("business_name", domain),
                    phone=lead.get("whatsapp", ""),
                    rating=lead.get("gmaps_rating", "4.9"),
                    review_count=lead.get("gmaps_reviews", 50),
                    output_dir=client_dir
                )

            vd = VercelDeployer()
            dep_res = vd.deploy(site_dir, client_slug)
            if dep_res.get("success"):
                lead["vercel_url"] = dep_res.get("url")
                tracker.record_lead(domain, lead, status=lead.get("status", "discovered"))
                all_leads = list(tracker.get_all_leads().values())
                WhatsAppDispatcher().generate_html_queue_dashboard(all_leads)
                self._send_json({"success": True, "url": dep_res.get("url")})
            else:
                self._send_json({"success": False, "error": dep_res.get("error", "Deployment failed")}, 500)
            return

        # -------------------------------------------------------------
        # 4. ACTION: CREATE INVOICE
        # -------------------------------------------------------------
        if path == "/api/create-invoice":
            domain = body.get("domain") or (query.get("domain", [""])[0])
            domain = domain.strip()
            tracker = OutreachTracker()
            lead = tracker.get_lead(domain)
            if not lead:
                self._send_json({"success": False, "error": f"Lead {domain} not found"}, 404)
                return

            pg = PaymentGateway()
            inv = pg.create_invoice(
                domain=domain,
                business_name=lead.get("business_name", domain),
                whatsapp=lead.get("whatsapp", ""),
                track=lead.get("track", "track_b_modernize")
            )
            lead["invoice_id"] = inv["invoice_id"]
            lead["payment_status"] = "pending_invoice"
            tracker.record_lead(domain, lead, status=lead.get("status", "discovered"))

            all_leads = list(tracker.get_all_leads().values())
            WhatsAppDispatcher().generate_html_queue_dashboard(all_leads)

            self._send_json({
                "success": True,
                "invoice_id": inv["invoice_id"],
                "payment_url": inv["payment_url"],
                "price_display": inv["price_display"]
            })
            return

        # -------------------------------------------------------------
        # 5. ACTION: PAYMENT WEBHOOK (SETTLEMENT & AUTO-FULFILLMENT)
        # -------------------------------------------------------------
        if path == "/api/payment-webhook":
            # Support both Midtrans official webhook (order_id, transaction_status) and internal test simulator (invoice_id, status)
            inv_id = body.get("order_id") or body.get("invoice_id") or (query.get("invoice_id", [""])[0])
            raw_status = body.get("transaction_status") or body.get("status") or (query.get("status", [""])[0])
            fraud_status = body.get("fraud_status", "accept")

            if not inv_id:
                self._send_json({"success": False, "error": "invoice_id or order_id missing"}, 400)
                return

            pg = PaymentGateway()
            inv = pg.get_invoice(inv_id)
            if not inv:
                self._send_json({"success": False, "error": f"Invoice {inv_id} not found"}, 404)
                return

            # Verify Midtrans signature if provided
            sig_key = body.get("signature_key", "")
            if sig_key:
                status_code = str(body.get("status_code", "200"))
                gross_amount = str(body.get("gross_amount", ""))
                if not pg.verify_midtrans_signature(inv_id, status_code, gross_amount, sig_key):
                    self._send_json({"success": False, "error": "Invalid Midtrans signature"}, 403)
                    return

            is_paid = False
            if raw_status:
                st = str(raw_status).lower()
                if st in ["settlement", "paid"]:
                    is_paid = True
                elif st == "capture" and fraud_status.lower() == "accept":
                    is_paid = True

            if is_paid:
                pg.mark_as_paid(inv_id)
                domain = inv.get("domain", "")
                tracker = OutreachTracker()
                lead = tracker.get_lead(domain) or {}

                lead["payment_status"] = "paid"
                lead["status"] = "paid"
                tracker.record_lead(domain, lead, status="paid")

                # Auto-Fulfillment Dispatch
                wa_disp = WhatsAppDispatcher()
                phone = inv.get("whatsapp") or lead.get("whatsapp")
                b_name = inv.get("business_name", domain)
                price_display = inv.get("price_display", "$100 USD")
                track = inv.get("track") or lead.get("track", "track_b_modernize")
                client_slug = domain.replace(".", "_").replace("-", "_")

                if phone:
                    def _send_fulfillment_async():
                        try:
                            if track == "track_a_new_web":
                                # Track A Fulfillment Handover
                                v_url = lead.get("vercel_url", f"https://{client_slug}.vercel.app")
                                fulfillment_msg = (
                                    f"Halo Pimpinan *{b_name}*, pembayaran *{price_display}* telah kami terima dengan lunas. Terima kasih banyak atas kepercayaannya! 🙏\n\n"
                                    f"Website modern resmi Anda di {v_url} kini telah aktif dan resmi menjadi aset digital bisnis Anda seutuhnya.\n\n"
                                    f"Untuk menghubungkan website ini ke domain resmi bisnis Anda (contoh: www.{client_slug.replace('_', '')}.com), silakan infokan nama domain yang Anda kehendaki agar tim teknis kami bantu arahkan hingga live sempurna."
                                )
                                print(f"\n[FULFILLMENT DISPATCH JALUR A ke {phone}]:\n{fulfillment_msg[:120]}...")
                                wa_disp.send_custom_message(phone, fulfillment_msg, dry_run=False)
                            else:
                                # Track B Fulfillment Handover
                                cp = CodePackager()
                                site_dir = os.path.join(CLIENTS_DIR, client_slug, "site")
                                res_pack = cp.package_client_code(site_dir, client_slug, output_dir=os.path.join(CLIENTS_DIR, client_slug), business_name=b_name, domain=domain)
                                dl_url = f"http://localhost:8080{res_pack.get('download_url')}"

                                fulfillment_msg = (
                                    f"Halo Pimpinan *{b_name}*, pembayaran *{price_display}* telah kami terima dengan lunas. Terima kasih banyak atas kerjasamanya! 🙏\n\n"
                                    f"Berikut adalah tautan unduh resmi paket Source Code bersih website baru Anda:\n"
                                    f"📦 {dl_url}\n\n"
                                    f"Paket berkas telah mencakup:\n"
                                    f"1. Seluruh source code website modern (HTML, CSS, Assets)\n"
                                    f"2. PANDUAN_PEMASANGAN_CPANEL.md (Langkah upload ke hosting sendiri)\n"
                                    f"3. SEO_CONFIGURATION_GUIDE.md (Verifikasi Google Search Console & Schema)\n\n"
                                    f"Tim kami siap mendampingi proses pemasangan hingga selesai. Sukses selalu untuk {b_name}!"
                                )
                                print(f"\n[FULFILLMENT DISPATCH JALUR B ke {phone}]:\n{fulfillment_msg[:120]}...")
                                wa_disp.send_custom_message(phone, fulfillment_msg, dry_run=False)
                        except Exception as fe:
                            print(f"[!] Fulfillment background error: {fe}")

                    threading.Thread(target=_send_fulfillment_async, daemon=True).start()

                all_leads = list(tracker.get_all_leads().values())
                wa_disp.generate_html_queue_dashboard(all_leads)

                self._send_json({
                    "success": True,
                    "status": "PAID",
                    "message": f"Settlement confirmed and fulfillment sent to {phone}."
                })
                return

            self._send_json({"success": False, "error": "Invalid webhook status"}, 400)
            return

        # -------------------------------------------------------------
        # 6. ACTION: CHECK WHATSAPP REPLIES
        # -------------------------------------------------------------
        if path == "/api/check-replies":
            wa_disp = WhatsAppDispatcher()
            replies = wa_disp.check_incoming_replies(auto_respond=True)
            self._send_json({"success": True, "replies_found": len(replies), "replies": replies})
            return

        self._send_json({"success": False, "error": "Unknown API endpoint"}, 404)

    def _render_checkout_page(self, inv: Dict[str, Any]) -> str:
        """Renders modern, high-converting Swiss Minimalist checkout page."""
        b_name = inv.get("business_name", "Klien")
        domain = inv.get("domain", "")
        inv_id = inv.get("invoice_id", "")
        amount_idr = f"Rp {inv.get('amount_idr', 1650000):,.0f}".replace(",", ".")
        price_display = inv.get("price_display", "$100 USD")
        status = inv.get("status", "PENDING")
        is_paid = status == "PAID"
        vas = inv.get("virtual_accounts", {})

        return f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Invoice Pembayaran Resmi - {inv_id}</title>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Plus Jakarta Sans', -apple-system, sans-serif;
    background: #0d0f14; color: #f1f5f9; min-height: 100vh;
    display: flex; align-items: center; justify-content: center; padding: 20px;
  }}
  .checkout-card {{
    background: #141721; border: 1px solid #232838; border-radius: 16px;
    max-width: 480px; width: 100%; padding: 32px; box-shadow: 0 20px 40px rgba(0,0,0,0.4);
  }}
  .header {{ text-align: center; margin-bottom: 24px; }}
  .tag {{
    display: inline-block; padding: 4px 12px; border-radius: 99px;
    font-size: 12px; font-weight: 700; text-transform: uppercase;
    background: {'rgba(22, 163, 74, 0.15)' if is_paid else 'rgba(234, 179, 8, 0.15)'};
    color: {'#4ade80' if is_paid else '#facc15'};
    border: 1px solid {'rgba(22, 163, 74, 0.4)' if is_paid else 'rgba(234, 179, 8, 0.4)'};
  }}
  h1 {{ font-size: 24px; font-weight: 800; margin-top: 12px; }}
  .inv-num {{ color: #94a3b8; font-size: 13px; margin-top: 4px; }}
  
  .pricing-box {{
    background: #0a0c10; border: 1px solid #1e2330; border-radius: 12px;
    padding: 20px; text-align: center; margin: 20px 0;
  }}
  .amount {{ font-size: 32px; font-weight: 800; color: #ffffff; }}
  .amount-sub {{ font-size: 13px; color: #10b981; margin-top: 4px; font-weight: 600; }}
  
  .detail-row {{
    display: flex; justify-content: space-between; font-size: 13px;
    padding: 10px 0; border-bottom: 1px solid #1c212d; color: #94a3b8;
  }}
  .detail-row strong {{ color: #ffffff; }}

  /* VA List */
  .va-section {{ margin-top: 20px; }}
  .va-title {{ font-size: 13px; font-weight: 700; margin-bottom: 10px; color: #cbd5e1; }}
  .va-item {{
    background: #0a0c10; border: 1px solid #1e2330; border-radius: 8px;
    padding: 12px 14px; display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 8px; font-size: 13px;
  }}
  .va-bank {{ font-weight: 700; color: #ffffff; }}
  .va-number {{ font-family: monospace; font-size: 14px; color: #38bdf8; }}
  .btn-copy {{
    background: #1e2330; border: none; color: #cbd5e1; padding: 4px 10px;
    border-radius: 4px; font-size: 11px; cursor: pointer;
  }}
  .btn-copy:hover {{ background: #283042; color: #fff; }}

  .btn-simulate {{
    width: 100%; background: #16a34a; color: #ffffff; border: none;
    padding: 14px; border-radius: 8px; font-weight: 700; font-size: 14px;
    cursor: pointer; margin-top: 24px; transition: 0.2s;
  }}
  .btn-simulate:hover {{ background: #15803d; }}
  .paid-notice {{
    background: rgba(22, 163, 74, 0.1); border: 1px solid #16a34a;
    border-radius: 8px; padding: 14px; text-align: center; color: #4ade80;
    font-size: 14px; font-weight: 600; margin-top: 20px;
  }}
</style>
</head>
<body>
<div class="checkout-card">
  <div class="header">
    <span class="tag">{'LUNAS (PAID)' if is_paid else 'MENUNGGU PEMBAYARAN'}</span>
    <h1>{b_name}</h1>
    <div class="inv-num">No. Invoice: <strong>{inv_id}</strong></div>
  </div>

  <div class="pricing-box">
    <div class="amount">{amount_idr}</div>
    <div class="amount-sub">{price_display}</div>
  </div>

  <div class="detail-row">
    <span>Item Layanan</span>
    <strong>Turn-Key Modern Website + SEO</strong>
  </div>
  <div class="detail-row">
    <span>Ketentuan Biaya</span>
    <strong>1x Bayar (Tanpa Biaya Bulanan)</strong>
  </div>
  <div class="detail-row">
    <span>Domain Prospek</span>
    <strong>{domain}</strong>
  </div>

  {f'''
  <div class="paid-notice">
    ✅ Pembayaran Telah Diterima. Paket website resmi telah diserahterimakan ke WhatsApp klien.
  </div>
  ''' if is_paid else f'''
  <div class="va-section">
    <div class="va-title">Transfer Virtual Account Resmi (Verifikasi Instan 24 Jam):</div>
    <div class="va-item">
      <span class="va-bank">BCA</span>
      <span class="va-number">{vas.get("BCA")}</span>
      <button class="btn-copy" onclick="copyText('{vas.get("BCA")}')">Salin</button>
    </div>
    <div class="va-item">
      <span class="va-bank">Mandiri</span>
      <span class="va-number">{vas.get("Mandiri")}</span>
      <button class="btn-copy" onclick="copyText('{vas.get("Mandiri")}')">Salin</button>
    </div>
    <div class="va-item">
      <span class="va-bank">BRI</span>
      <span class="va-number">{vas.get("BRI")}</span>
      <button class="btn-copy" onclick="copyText('{vas.get("BRI")}')">Salin</button>
    </div>
  </div>

  <button onclick="simulatePayment('{inv_id}')" class="btn-simulate">
    Simulasi Pembayaran Lunas (Test Mode Webhook) ↗
  </button>
  '''}
</div>

<script>
  function copyText(txt) {{
    navigator.clipboard.writeText(txt);
    alert('Nomor Virtual Account disalin: ' + txt);
  }}

  async function simulatePayment(invId) {{
    if (!confirm('Jalankan simulasi pembayaran lunas untuk ' + invId + '?\\n\\nIni akan memicu webhook POST /api/payment-webhook dan otomatis mengirim paket ke WhatsApp.')) return;
    try {{
      const res = await fetch('/api/payment-webhook', {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }},
        body: JSON.stringify({{ invoice_id: invId, status: 'PAID' }})
      }});
      const data = await res.json();
      if (data.success) {{
        alert('Sukses! Pembayaran terverifikasi dan paket handover terkirim.');
        location.reload();
      }} else {{
        alert('Gagal: ' + data.error);
      }}
    }} catch (e) {{
      alert('Error: ' + e);
    }}
  }}
</script>
</body>
</html>
"""

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _send_json(self, data: dict, code: int = 200):
        payload = json.dumps(data).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def start_dashboard_server(port: int = 8080, open_browser: bool = True):
    """Starts the ThreadingHTTPServer and opens the browser."""
    server = None
    actual_port = port
    for p in range(port, port + 10):
        try:
            server = ThreadingHTTPServer(("127.0.0.1", p), OutreachDashboardHandler)
            actual_port = p
            break
        except OSError:
            continue

    if not server:
        print(f"[!] Gagal memulai dashboard server pada port {port}-{port+10}.")
        return

    url = f"http://127.0.0.1:{actual_port}/"
    print("\n" + "=" * 80)
    print("  🚀 LEADS OUTREACH DASHBOARD & PAYMENT SERVER RUNNING")
    print(f"  URL Dasbor Antrean : {url}")
    print("  Tekan Ctrl+C di terminal kapan saja untuk menghentikan server.")
    print("=" * 80 + "\n")

    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Dashboard server dihentikan.")
        server.server_close()


if __name__ == "__main__":
    start_dashboard_server()
