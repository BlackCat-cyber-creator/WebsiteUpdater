"""
Interactive Local Dashboard Server for Web Outreach Pipeline.
Serves the clean Review & Approval Queue (clients/outreach_queue.html),
interactive checkout pages (/pay/{invoice_id}), payment webhook handlers,
and automatic client fulfillment dispatches.
"""

import os
import re
import json
import secrets
import shutil
import urllib.parse
import webbrowser
import threading
from datetime import datetime
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

# Dashboard authentication token (set DASHBOARD_TOKEN in .env or auto-generated)
_DASHBOARD_TOKEN = os.environ.get("DASHBOARD_TOKEN", "").strip()
if not _DASHBOARD_TOKEN:
    _DASHBOARD_TOKEN = secrets.token_urlsafe(24)
    print(f"[SECURITY] Dashboard auto-generated auth token: {_DASHBOARD_TOKEN}")
    print(f"[SECURITY] Access dashboard at: http://localhost:8080/?token={_DASHBOARD_TOKEN}")
    print(f"[SECURITY] Set DASHBOARD_TOKEN in .env to use a fixed token.")

# Public paths that don't require auth (client-facing checkout pages & webhooks)
_PUBLIC_PATHS = ["/pay/", "/api/wa/webhook", "/api/webhook/midtrans", "/api/payment-webhook"]


def is_authenticated_request(path: str, headers: Dict[str, str], token: str, client_ip: str = "") -> bool:
    """Checks for valid auth token in query string, Authorization header, or Cookie. Always allows localhost."""
    # Local loopback on admin machine is always trusted
    if client_ip in ("127.0.0.1", "::1", "localhost"):
        return True
    if not token:
        return True
    parsed = urllib.parse.urlparse(path)
    query = urllib.parse.parse_qs(parsed.query)
    if query.get("token", [""])[0] == token:
        return True
    auth_header = headers.get("Authorization", "") or headers.get("authorization", "")
    if auth_header.startswith("Bearer ") and auth_header[7:].strip() == token:
        return True
    cookie_header = headers.get("Cookie", "") or headers.get("cookie", "")
    if f"auth_token={token}" in cookie_header:
        return True
    return False


class OutreachDashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=CLIENTS_DIR, **kwargs)

    def _is_authenticated(self) -> bool:
        """Checks for valid auth token in query string, Cookie, or Authorization header. Always allows localhost."""
        client_ip = getattr(self, "client_address", [""])[0] if hasattr(self, "client_address") else ""
        return is_authenticated_request(self.path, self.headers, _DASHBOARD_TOKEN, client_ip=client_ip)

    def _is_public_path(self) -> bool:
        """Returns True for paths that don't require authentication (e.g. client checkout pages)."""
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        return any(path.startswith(pp) for pp in _PUBLIC_PATHS)

    def do_GET(self):
        # Enforce authentication on non-public paths
        if not self._is_public_path() and not self._is_authenticated():
            self.send_error(401, "Unauthorized — append ?token=YOUR_TOKEN to the URL")
            return

        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)
        has_token_qs = query.get("token", [""])[0] == _DASHBOARD_TOKEN

        # 0. Meta WhatsApp Cloud API Webhook Handshake Verification
        if path == "/api/wa/webhook":
            mode = query.get("hub.mode", [""])[0]
            token = query.get("hub.verify_token", [""])[0]
            challenge = query.get("hub.challenge", [""])[0]
            expected_token = os.environ.get("META_WEBHOOK_VERIFY_TOKEN", "website_updater_verify_token")

            if mode == "subscribe" and token == expected_token:
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(challenge.encode("utf-8"))
                print(f"[META WEBHOOK] Verification handshake SUCCESS (challenge: {challenge})")
                return
            else:
                self.send_error(403, "Verification token mismatch")
                return

        # 1. Serve Outreach Queue Dashboard (Dynamically regenerated from SQLite DB on every access)
        if path in ["/", "/index.html", "/queue", "/dashboard", "/outreach_queue.html"]:
            try:
                tracker = OutreachTracker()
                all_leads = list(tracker.get_all_leads().values())
                wa_disp = WhatsAppDispatcher()
                wa_disp.generate_html_queue_dashboard(all_leads)
            except Exception as e:
                print(f"[!] Error saat regenerate dashboard: {e}")

            queue_file = os.path.join(CLIENTS_DIR, "outreach_queue.html")
            if os.path.exists(queue_file):
                with open(queue_file, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Cache-Control", "no-cache, no-store, must-revalidate, max-age=0")
                self.send_header("Pragma", "no-cache")
                self.send_header("Set-Cookie", f"auth_token={_DASHBOARD_TOKEN}; Path=/; SameSite=Lax")
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

            tracker = OutreachTracker()
            lead = tracker.get_lead(client_param) or {}

            vd = VercelDeployer()
            clean_slug = vd.clean_slug(client_param).replace("-", "_")
            client_slug = client_param.replace(".", "_").replace("-", "_")

            target_zip = lead.get("package_zip")
            if target_zip and not os.path.exists(target_zip):
                target_zip = None

            # Look in candidate client folders
            candidate_dirs = [
                os.path.join(CLIENTS_DIR, clean_slug),
                os.path.join(CLIENTS_DIR, client_slug),
                os.path.join(CLIENTS_DIR, client_param)
            ]
            if lead.get("proposal_pdf"):
                candidate_dirs.insert(0, os.path.dirname(os.path.abspath(lead["proposal_pdf"])))

            client_dir = candidate_dirs[0]
            for cd in candidate_dirs:
                if os.path.exists(cd):
                    client_dir = cd
                    break

            if not target_zip and os.path.exists(client_dir):
                for f in os.listdir(client_dir):
                    if f.endswith(".zip"):
                        target_zip = os.path.join(client_dir, f)
                        break

            # If not yet created, package on the fly
            if not target_zip:
                site_dir = os.path.join(client_dir, "site")
                if not os.path.exists(site_dir):
                    sg = SiteGenerator()
                    sg.generate_turnkey_site(
                        business_name=lead.get("business_name", client_param),
                        phone=lead.get("whatsapp", ""),
                        output_dir=client_dir
                    )
                cp = CodePackager()
                res = cp.package_client_code(
                    site_dir,
                    clean_slug,
                    output_dir=client_dir,
                    business_name=lead.get("business_name", client_param),
                    domain=client_param
                )
                target_zip = res.get("zip_path")
                if target_zip and lead:
                    lead["package_zip"] = target_zip
                    tracker.record_lead(client_param, lead, status=lead.get("status", "discovered"))

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
        # Enforce authentication on non-public POST endpoints
        if not self._is_public_path() and not self._is_authenticated():
            self._send_json({"success": False, "error": "Unauthorized"}, 401)
            return

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
        # 0. META WHATSAPP CLOUD API WEBHOOK
        # -------------------------------------------------------------
        if path == "/api/wa/webhook":
            try:
                entries = body.get("entry", [])
                for entry in entries:
                    changes = entry.get("changes", [])
                    for change in changes:
                        val = change.get("value", {})
                        messages = val.get("messages", [])
                        for msg in messages:
                            from_phone = msg.get("from", "")
                            msg_type = msg.get("type", "")
                            msg_text = msg.get("text", {}).get("body", "") if msg_type == "text" else f"[{msg_type}]"
                            print(f"[META WEBHOOK] Pesan masuk dari +{from_phone}: {msg_text}")

                            # Mark matching lead as replied in database
                            tracker = OutreachTracker()
                            all_leads = tracker.get_all_leads()
                            for d, lead_data in all_leads.items():
                                lead_wa = re.sub(r"[^\d]", "", lead_data.get("whatsapp", ""))
                                if lead_wa and (lead_wa == from_phone or from_phone.endswith(lead_wa) or lead_wa.endswith(from_phone)):
                                    lead_data["status"] = "replied"
                                    lead_data["reply_text"] = msg_text
                                    lead_data["replied_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                    tracker.save_lead(d, lead_data)
                                    print(f"[META WEBHOOK] Lead {d} status diperbarui -> 'replied'")
                                    break
                self._send_json({"status": "EVENT_RECEIVED"}, 200)
            except Exception as e:
                print(f"[META WEBHOOK] Error processing event: {e}")
                self._send_json({"status": "EVENT_RECEIVED", "warning": str(e)}, 200)
            return

        # -------------------------------------------------------------
        # 1. ACTION: APPROVE & DISPATCH (WhatsApp + Proposal PDF)
        # -------------------------------------------------------------
        if path == "/api/approve":
            try:
                domain = body.get("domain") or (query.get("domain", [""])[0])
                domain = domain.strip()
                if not domain:
                    self._send_json({"success": False, "error": "Domain parameter missing"}, 400)
                    return

                step = body.get("step") or (query.get("step", ["step_1_permission"])[0])

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

                vd = VercelDeployer()
                client_clean = vd.clean_slug(domain).replace("-", "_")
                cands = [
                    os.path.join(CLIENTS_DIR, client_clean),
                    os.path.join(CLIENTS_DIR, domain.replace(".", "_").replace("-", "_")),
                    os.path.join(CLIENTS_DIR, domain.replace(".", "_")),
                    os.path.join(CLIENTS_DIR, domain)
                ]
                client_dir = cands[0]
                for c in cands:
                    if os.path.exists(c):
                        client_dir = c
                        break

                site_dir = os.path.join(client_dir, "site")

                # If Step 2 (Delivery) or legacy one-shot, ensure website is deployed to Vercel first!
                if step in ["step_2_delivery", "legacy_one_shot"] and not lead.get("vercel_url"):
                    if track == "track_a_new_web":
                        if not os.path.exists(os.path.join(site_dir, "index.html")):
                            sg = SiteGenerator()
                            sg.generate_turnkey_site(
                                business_name=b_name,
                                phone=wa,
                                rating=lead.get("gmaps_rating", "4.9"),
                                review_count=lead.get("gmaps_reviews", 50),
                                output_dir=client_dir
                            )
                        dep_res = vd.deploy(site_dir, client_clean, track=track, city=lead.get("city"))
                        if dep_res.get("success"):
                            lead["vercel_url"] = dep_res.get("url")
                            logger.info(f"Auto-deployed {domain} to Vercel before Step 2: {lead['vercel_url']}")
                    else:
                        # Track B: Run authentic scraping & modernization pipeline (Scrapling, style analyzer, SEO repair)
                        from pipeline.commands.context import execute_pipeline_for_client
                        target_url = lead.get("website_url") or f"https://{domain}"
                        execute_pipeline_for_client(target_url, client_dir)
                        fresh_lead = tracker.get_lead(domain)
                        if fresh_lead and fresh_lead.get("vercel_url"):
                            lead["vercel_url"] = fresh_lead.get("vercel_url")
                            if fresh_lead.get("proposal_pdf"):
                                lead["proposal_pdf"] = fresh_lead.get("proposal_pdf")
                                pdf_path = fresh_lead.get("proposal_pdf")

                # Verify and ensure proposal_pdf exists and has Vercel URL
                needs_pdf_gen = False
                if not pdf_path or not os.path.exists(pdf_path):
                    cand_pdf = os.path.join(client_dir, "client_proposal.pdf")
                    if os.path.exists(cand_pdf):
                        pdf_path = os.path.abspath(cand_pdf)
                    else:
                        needs_pdf_gen = True

                # When delivering Step 2 with active vercel_url, always regenerate PDF to ensure fresh QR Code & link
                if lead.get("vercel_url") and (needs_pdf_gen or step in ["step_2_delivery", "legacy_one_shot"]):
                    needs_pdf_gen = True

                if needs_pdf_gen:
                    os.makedirs(client_dir, exist_ok=True)
                    try:
                        from pipeline.pdf_generator import ProposalPdfGenerator
                        pdf_gen = ProposalPdfGenerator()
                        if track == "track_a_new_web":
                            p_res = pdf_gen.generate_track_a(lead, client_dir, vercel_url=lead.get("vercel_url", ""))
                        else:
                            p_res = pdf_gen.generate_track_b(lead, client_dir, vercel_url=lead.get("vercel_url", ""))
                        new_pdf = p_res.get("pdf_path", "")
                        if new_pdf and os.path.exists(new_pdf):
                            pdf_path = os.path.abspath(new_pdf)
                    except Exception as e_pdf:
                        logger.warning(f"PDF generation error for lead {domain}: {e_pdf}")
                        if not pdf_path:
                            pdf_path = ""

                lead["proposal_pdf"] = pdf_path

                email_disp = EmailDispatcher()
                wa_disp = WhatsAppDispatcher()

                email_sent = False
                wa_sent = False
                is_restricted = False
                countdown_info = ""
                errors = []

                # A. Send Email (Track B only, if email exists and delivery step)
                if email and track == "track_b_modernize" and step in ["step_2_delivery", "legacy_one_shot"]:
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

                is_invalid_phone = False
                # B. Send WhatsApp (Supports Two-Step Permission Outreach)
                if wa:
                    w_res = wa_disp.dispatch_live(
                        target_phone=wa,
                        business_name=b_name,
                        domain=domain,
                        pdf_path=pdf_path,
                        audit_signals=signals,
                        dry_run=False,
                        track=track,
                        rating_text=lead.get("gmaps_rating", ""),
                        step=step
                    )
                    if w_res.get("success") and w_res.get("mode") == "live_sent":
                        wa_sent = True
                    elif w_res.get("mode") == "restricted":
                        is_restricted = True
                        countdown_info = w_res.get("countdown", "")
                        errors.append(f"WhatsApp: {w_res.get('message')}")
                    elif w_res.get("mode") == "invalid_phone":
                        is_invalid_phone = True
                        errors.append(f"WhatsApp: {w_res.get('message')}")
                    else:
                        errors.append(f"WhatsApp: {w_res.get('message')}")
                else:
                    errors.append("WhatsApp: Nomor telepon kontak kosong atau bukan nomor WhatsApp.")

                if is_restricted:
                    final_status = "wa_cooldown"
                elif is_invalid_phone:
                    final_status = "invalid_phone"
                else:
                    final_status = "sent_whatsapp" if wa_sent and not email_sent else (
                        "sent_all" if (wa_sent and email_sent) else ("sent_email" if email_sent else "failed")
                    )

                step_desc = "Izin Tahap 1" if step == "step_1_permission" else "Proposal Tahap 2"
                tracker.record_lead(domain, {
                    "business_name": b_name,
                    "whatsapp": wa,
                    "email": email,
                    "track": track,
                    "proposal_pdf": pdf_path,
                    "outdated_signals": signals,
                    "notes": f"Approved via Dashboard ({step_desc}). WA: {wa_sent}, Email: {email_sent}, Restricted: {is_restricted}"
                }, status=final_status)

                all_leads = list(tracker.get_all_leads().values())
                wa_disp.generate_html_queue_dashboard(all_leads)

                success_msg = f"Pesan {step_desc} sukses dikirim! (WA: {'✅' if wa_sent else '❌'})"
                self._send_json({
                    "success": (email_sent or wa_sent),
                    "mode": "restricted" if is_restricted else ("live_sent" if wa_sent else "error"),
                    "status": final_status,
                    "countdown": countdown_info,
                    "email_sent": email_sent,
                    "wa_sent": wa_sent,
                    "errors": errors,
                    "message": (
                        f"⚠️ WhatsApp Web cooldown Meta ({countdown_info}). Silakan kirim langsung via HP."
                        if is_restricted else
                        success_msg
                    )
                })
            except Exception as approve_err:
                print(f"[!] Error saat eksekusi /api/approve: {approve_err}")
                self._send_json({
                    "success": False,
                    "mode": "error",
                    "error": str(approve_err),
                    "message": f"Terjadi kesalahan saat memproses pengiriman: {approve_err}"
                }, 500)
            return

        # -------------------------------------------------------------
        # 1.5 ACTION: TANDAI TERKIRIM MANUAL (Untuk pengiriman via HP)
        # -------------------------------------------------------------
        if path == "/api/mark-sent":
            domain = body.get("domain") or (query.get("domain", [""])[0])
            domain = domain.strip()
            if not domain:
                self._send_json({"success": False, "error": "Domain parameter missing"}, 400)
                return

            step_param = body.get("step") or (query.get("step", [""])[0])
            tracker = OutreachTracker()
            lead = tracker.get_lead(domain) or {}
            curr_status = lead.get("status", "discovered")

            # Intelligent progression: If already in step 1 or replied, advance to step 2 (Proposal & Demo)
            if step_param == "step_2_delivery" or curr_status in ["sent_whatsapp", "sent_step1", "replied"]:
                new_status = "sent_step2"
                notes = "Tahap 2 (Proposal & Demo) terkirim manual via WhatsApp HP"
                msg_feedback = f"Prospek {domain} berhasil ditandai: Proposal & Demo (Tahap 2) Terkirim."
            else:
                new_status = "sent_whatsapp"
                notes = "Tahap 1 (Izin) terkirim manual via WhatsApp HP"
                msg_feedback = f"Prospek {domain} berhasil ditandai: Izin Tahap 1 Terkirim."

            lead["status"] = new_status
            lead["notes"] = notes
            tracker.record_lead(domain, lead, status=new_status)

            all_leads = list(tracker.get_all_leads().values())
            wa_disp = WhatsAppDispatcher()
            wa_disp.generate_html_queue_dashboard(all_leads)

            self._send_json({
                "success": True,
                "status": new_status,
                "message": msg_feedback
            })
            return

        # -------------------------------------------------------------
        # 1.58 ACTION: HUNT OUTDATED B2B WEBSITES (Jalur B Revitalizer)
        # -------------------------------------------------------------
        if path == "/api/hunt-outdated":
            category = body.get("category") or (query.get("category", ["auto"])[0])
            limit_val = int(body.get("limit") or (query.get("limit", [3])[0]) or 3)
            limit_val = max(1, min(limit_val, 5))

            try:
                from pipeline.scanner.outdated_hunter import OutdatedWebsiteHunter
                from pipeline.scanner.contact_validator import ContactValidator
                hunter = OutdatedWebsiteHunter()
                tracker = OutreachTracker()
                vd = VercelDeployer()

                leads = hunter.hunt_outdated_leads(target_category=category, limit=limit_val)
                added_leads = []
                for lead in leads:
                    dom = lead.get("domain", "")
                    if not dom:
                        continue
                    if tracker.is_already_contacted(dom, lead.get("whatsapp"), lead.get("email")) or tracker.get_lead(dom):
                        continue

                    cascade = ContactValidator.evaluate_contact_cascade(lead.get("whatsapp") or lead.get("phone", ""), lead.get("email", ""))
                    primary_ch = cascade["primary_channel"]
                    if primary_ch == "discard":
                        continue

                    p_info = cascade["phone_info"]
                    if primary_ch == "email":
                        lead_status = "fallback_email"
                    else:
                        lead_status = "ready_for_permission"
                        lead["whatsapp"] = p_info["normalized_e164"]

                    # JIT preparation of client folder
                    client_clean = vd.clean_slug(dom).replace("-", "_")
                    client_dir = os.path.join(CLIENTS_DIR, client_clean)
                    os.makedirs(client_dir, exist_ok=True)

                    tracker.record_lead(dom, lead, status=lead_status)
                    added_leads.append(lead)

                all_leads = list(tracker.get_all_leads().values())
                WhatsAppDispatcher().generate_html_queue_dashboard(all_leads)

                self._send_json({
                    "success": True,
                    "count": len(added_leads),
                    "leads": added_leads,
                    "message": f"Berhasil menjaring {len(added_leads)} website lama siap modernisasi (Jalur B)."
                })
            except Exception as e:
                print(f"[!] Error hunting outdated websites: {e}")
                self._send_json({"success": False, "error": str(e)}, 500)
            return

        # -------------------------------------------------------------
        # 1.6 ACTION: SCAN HIGH-VALUE NICHES / GMAPS (Jalur A Nationwide)
        # -------------------------------------------------------------
        if path in ["/api/scan-niche", "/api/scan-kalimantan"]:
            scope = body.get("scope") or body.get("city") or (query.get("scope", [query.get("city", ["auto"])[0]])[0])
            limit_val = int(body.get("limit") or (query.get("limit", [3])[0]) or 3)
            limit_val = max(1, min(limit_val, 5))

            try:
                from pipeline.scanner.google_maps_scanner import GoogleMapsBusinessScanner, clean_business_brand_name
                from pipeline.scanner.niche_matrix import NicheMatrix, HIGH_VALUE_NICHE_TAXONOMY
                from pipeline.scanner.contact_validator import ContactValidator

                maps_scanner = GoogleMapsBusinessScanner()
                tracker = OutreachTracker()
                vd = VercelDeployer()
                site_gen = SiteGenerator()

                scope_str = (scope or "auto").strip().lower()

                REGION_PRESETS = {
                    "jabodetabek": [
                        "distributor packaging cikarang", "kontraktor hvac bekasi", "supplier bahan kimia tangerang",
                        "jasa epoxy lantai pabrik cikarang", "sewa truk wingbox jakarta utara", "klinik estetika jakarta selatan"
                    ],
                    "surabaya_jatim": [
                        "distributor genset industri surabaya", "sewa truk reefer pendingin surabaya", "kontraktor baja gudang sidoarjo",
                        "supplier pipa hdpe surabaya", "klinik gigi spesialis surabaya", "distributor frozen food sidoarjo"
                    ],
                    "kalimantan": [
                        "kargo alat berat balikpapan", "supplier alat teknik industri balikpapan", "kontraktor hvac samarinda",
                        "distributor packaging karton box samarinda", "ekspedisi balikpapan surabaya", "klinik spesialis balikpapan"
                    ],
                    "sumatera": [
                        "ekspedisi kargo logistik medan", "jasa kargo proyek batam", "distributor packaging batam",
                        "supplier alat teknik medan", "kontraktor interior kantor medan", "klinik estetika pekanbaru"
                    ]
                }

                if scope_str in REGION_PRESETS:
                    queries = list(REGION_PRESETS[scope_str])
                    import random
                    random.shuffle(queries)
                elif scope_str in HIGH_VALUE_NICHE_TAXONOMY:
                    queries = NicheMatrix.get_diverse_query_batch(limit=max(6, limit_val * 2), target_category=scope_str)
                elif scope_str in ["balikpapan", "samarinda", "pontianak", "banjarmasin", "palangkaraya"]:
                    from pipeline.scanner.kalimantan_scanner import scan_and_process_kalimantan_smes
                    res = scan_and_process_kalimantan_smes(city=scope_str, limit=limit_val)
                    self._send_json(res)
                    return
                else:
                    queries = NicheMatrix.get_diverse_query_batch(limit=max(6, limit_val * 2))

                candidates = []
                for q in queries:
                    if len(candidates) >= limit_val:
                        break
                    needed = limit_val - len(candidates)
                    found = maps_scanner.search_local_businesses(q, limit=needed, track_only="track_a_new_web")
                    for f in found:
                        if NicheMatrix.is_excluded_business(f.get("business_name", "")):
                            continue
                        if f.get("track") != "track_a_new_web":
                            continue
                        f["business_name"] = clean_business_brand_name(f.get("business_name", ""))
                        f["track"] = "track_a_new_web"
                        f["domain"] = f.get("domain") or vd.get_preview_slug(f["business_name"], track="track_a_new_web", city=f.get("city"))
                        dom = f.get("domain", "")
                        if not dom:
                            continue
                        if tracker.is_already_contacted(dom, f.get("whatsapp"), f.get("email")) or tracker.get_lead(dom):
                            continue
                        if not any(c["domain"] == dom for c in candidates):
                            candidates.append(f)

                added_leads = []
                for lead in candidates:
                    dom = lead["domain"]
                    biz_name = lead["business_name"]
                    raw_phone = lead.get("whatsapp") or lead.get("phone", "")

                    cascade = ContactValidator.evaluate_contact_cascade(raw_phone, lead.get("email", ""))
                    primary_ch = cascade["primary_channel"]
                    if primary_ch == "discard":
                        continue

                    p_info = cascade["phone_info"]
                    if primary_ch == "email":
                        lead_status = "fallback_email"
                        lead["whatsapp"] = ""
                    else:
                        lead_status = "ready_for_permission"
                        lead["whatsapp"] = p_info["normalized_e164"]

                    client_clean = vd.clean_slug(dom).replace("-", "_")
                    client_dir = os.path.join(CLIENTS_DIR, client_clean)
                    os.makedirs(client_dir, exist_ok=True)
                    site_dir = os.path.join(client_dir, "site")
                    if not os.path.exists(os.path.join(site_dir, "index.html")):
                        site_gen.generate_turnkey_site(
                            business_name=biz_name,
                            phone=lead.get("whatsapp", ""),
                            rating=lead.get("gmaps_rating", "4.9"),
                            review_count=lead.get("gmaps_reviews", 50),
                            output_dir=client_dir
                        )

                    lead["track"] = "track_a_new_web"
                    tracker.record_lead(dom, lead, status=lead_status)
                    added_leads.append(lead)

                all_leads = list(tracker.get_all_leads().values())
                WhatsAppDispatcher().generate_html_queue_dashboard(all_leads)

                self._send_json({
                    "success": True,
                    "count": len(added_leads),
                    "leads": added_leads,
                    "message": f"Berhasil menambahkan {len(added_leads)} UKM berdaya beli tinggi ke antrean (Jalur A)."
                })
            except Exception as e:
                print(f"[!] Error scanning nationwide leads: {e}")
                self._send_json({"success": False, "error": str(e)}, 500)
            return

        # -------------------------------------------------------------
        # 2. ACTION: DISCARD (Komprehensif: hapus folder fisik + tandai discarded)
        # -------------------------------------------------------------
        if path == "/api/discard":
            domain = body.get("domain") or (query.get("domain", [""])[0])
            domain = domain.strip()
            if not domain:
                self._send_json({"success": False, "error": "Domain parameter required"}, 400)
                return

            tracker = OutreachTracker()
            lead = tracker.get_lead(domain)
            deleted_dirs = []

            # 1. Locate and delete physical client folders
            vd = VercelDeployer()
            clean_slug = vd.clean_slug(domain).replace("-", "_")
            cands = set()

            if lead:
                if lead.get("proposal_pdf"):
                    cands.add(os.path.dirname(os.path.abspath(lead["proposal_pdf"])))
                if lead.get("package_zip"):
                    cands.add(os.path.dirname(os.path.abspath(lead["package_zip"])))

            cands.add(os.path.join(CLIENTS_DIR, clean_slug))
            cands.add(os.path.join(CLIENTS_DIR, domain.replace(".", "_").replace("-", "_")))
            cands.add(os.path.join(CLIENTS_DIR, domain.replace(".", "_")))
            cands.add(os.path.join(CLIENTS_DIR, domain))

            for target_dir in cands:
                try:
                    target_dir = os.path.abspath(target_dir)
                    # Security checks: must be inside CLIENTS_DIR, not CLIENTS_DIR itself, not hidden folder, not outreach_drafts
                    if (
                        os.path.exists(target_dir)
                        and os.path.isdir(target_dir)
                        and os.path.commonpath([CLIENTS_DIR, target_dir]) == CLIENTS_DIR
                        and target_dir != CLIENTS_DIR
                    ):
                        bname = os.path.basename(target_dir)
                        if not bname.startswith(".") and bname != "outreach_drafts":
                            shutil.rmtree(target_dir, ignore_errors=True)
                            deleted_dirs.append(target_dir)
                            print(f"[DISCARD] Folder fisik klien berhasil dihapus: {target_dir}")
                except Exception as e:
                    print(f"[!] Error saat menghapus folder fisik {target_dir}: {e}")

            # 1.5 Delete cloud Vercel project
            try:
                vd.delete_project(domain)
            except Exception as ve:
                print(f"[!] Warning deleting Vercel project: {ve}")

            # 2. Update status in outreach_history.json
            b_name = lead.get("business_name", domain) if lead else domain
            tracker.record_lead(domain, {
                "business_name": b_name,
                "notes": f"Discarded from dashboard. Deleted folders: {deleted_dirs}"
            }, status="discarded")

            # 3. Regenerate outreach_queue.html immediately
            all_leads = list(tracker.get_all_leads().values())
            wa_disp = WhatsAppDispatcher()
            wa_disp.generate_html_queue_dashboard(all_leads)

            self._send_json({
                "success": True,
                "domain": domain,
                "deleted_dirs": deleted_dirs,
                "message": f"Prospek {domain} dan folder fisik berhasil dibersihkan dari disk."
            })
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

            track = lead.get("track", "track_b_modernize")

            # If Track B and site not generated yet, run authentic scraping & modernization pipeline
            if track == "track_b_modernize" and not os.path.exists(os.path.join(site_dir, "index.html")):
                from pipeline.commands.context import execute_pipeline_for_client
                target_url = lead.get("website_url") or f"https://{domain}"
                execute_pipeline_for_client(target_url, client_dir)
                fresh_lead = tracker.get_lead(domain)
                if fresh_lead and fresh_lead.get("vercel_url"):
                    all_leads = list(tracker.get_all_leads().values())
                    WhatsAppDispatcher().generate_html_queue_dashboard(all_leads)
                    self._send_json({"success": True, "url": fresh_lead.get("vercel_url")})
                    return

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
            dep_res = vd.deploy(site_dir, client_slug, track=lead.get("track", "track_b_modernize"), city=lead.get("city"))
            if dep_res.get("success"):
                vercel_url = dep_res.get("url")
                lead["vercel_url"] = vercel_url

                # Automatically re-generate official proposal PDF with live Vercel link & QR Code
                try:
                    from pipeline.pdf_generator import ProposalPdfGenerator
                    pdf_gen = ProposalPdfGenerator()
                    track = lead.get("track", "track_b_modernize")
                    if track == "track_a_new_web":
                        p_res = pdf_gen.generate_track_a(lead, client_dir, vercel_url=vercel_url)
                    else:
                        p_res = pdf_gen.generate_track_b(lead, client_dir, vercel_url=vercel_url)
                    if p_res.get("pdf_path") and os.path.exists(p_res["pdf_path"]):
                        lead["proposal_pdf"] = os.path.abspath(p_res["pdf_path"])
                except Exception as e_pdf:
                    logger.warning(f"Error regenerating PDF after Vercel deploy for {domain}: {e_pdf}")

                tracker.record_lead(domain, lead, status=lead.get("status", "discovered"))
                all_leads = list(tracker.get_all_leads().values())
                WhatsAppDispatcher().generate_html_queue_dashboard(all_leads)
                self._send_json({"success": True, "url": vercel_url})
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
        # 5. ACTION: MIDTRANS PAYMENT WEBHOOK (SETTLEMENT & AUTO-FULFILLMENT)
        # -------------------------------------------------------------
        if path in ["/api/webhook/midtrans", "/api/payment-webhook"]:
            # Support both Midtrans official webhook (order_id, transaction_status) and internal test simulator (invoice_id, status)
            inv_id = body.get("order_id") or body.get("invoice_id") or (query.get("invoice_id", [""])[0])
            raw_status = body.get("transaction_status") or body.get("status") or (query.get("status", [""])[0])
            fraud_status = body.get("fraud_status", "accept")

            if not inv_id:
                self._send_json({"success": False, "error": "invoice_id or order_id missing"}, 400)
                return

            pg = PaymentGateway()

            # Verify Midtrans signature key via PaymentGateway.verify_midtrans_notification
            # hashlib.sha512(order_id + status_code + gross_amount + ServerKey)
            if pg.server_key or body.get("signature_key"):
                if not pg.verify_midtrans_notification(body):
                    self._send_json({"success": False, "error": "Invalid Midtrans signature"}, 403)
                    return

            inv = pg.get_invoice(inv_id)
            if not inv:
                self._send_json({"success": False, "error": f"Invoice {inv_id} not found"}, 404)
                return

            is_paid = False
            if raw_status:
                st = str(raw_status).lower()
                if st in ["settlement", "paid"]:
                    is_paid = True
                elif st == "capture" and str(fraud_status).lower() == "accept":
                    is_paid = True

            if is_paid:
                # 1. Update status invoice di database (pipeline.db) menjadi PAID
                pg.mark_as_paid(inv_id)

                # 2. Cari data lead terkait di database (pipeline.db)
                tracker = OutreachTracker()
                domain = inv.get("domain", "")
                lead = tracker.get_lead(domain) if domain else None
                if not lead:
                    all_leads = tracker.get_all_leads()
                    for d, l in all_leads.items():
                        if l.get("invoice_id") == inv_id or d == domain:
                            domain = d
                            lead = l
                            break

                b_name = (lead.get("business_name") if lead else "") or inv.get("business_name", domain) or domain or "Klien"
                phone = (lead.get("whatsapp") if lead else "") or inv.get("whatsapp", "")
                price_display = inv.get("price_display", "$100 USD")

                vd = VercelDeployer()
                client_clean = vd.clean_slug(domain or b_name or "client").replace("-", "_")
                client_id = client_clean

                # 3. Otomatis trigger CodePackager().package_client() untuk menghasilkan .zip di clients/<id>/
                cp = CodePackager()
                res_pack = cp.package_client(
                    client_id=client_id,
                    business_name=b_name,
                    domain=domain,
                    phone=phone
                )
                zip_path = res_pack.get("zip_path", "")

                host_header = self.headers.get("Host", "localhost:8080")
                dl_url = f"http://{host_header}{res_pack.get('download_url')}"

                # 4. Update status lead di database (pipeline.db) menjadi PAID
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if domain or lead:
                    target_dom = domain or client_clean
                    lead_data = lead or {}
                    lead_data["status"] = "PAID"
                    lead_data["payment_status"] = "PAID"
                    lead_data["package_zip"] = zip_path
                    lead_data["notes"] = f"Lunas via Midtrans ({raw_status}). Handover ZIP siap di {zip_path}"
                    tracker.record_lead(target_dom, lead_data, status="PAID")

                # 5. Simpan log serah terima di folder clients/<id>/HANDOVER_LOG.json
                client_dir = os.path.dirname(zip_path) if zip_path else os.path.join(CLIENTS_DIR, client_id)
                os.makedirs(client_dir, exist_ok=True)
                handover_log_path = os.path.join(client_dir, "HANDOVER_LOG.json")
                handover_entry = {
                    "invoice_id": inv_id,
                    "order_id": inv.get("order_id", inv_id),
                    "domain": domain,
                    "business_name": b_name,
                    "whatsapp": phone,
                    "status": "PAID",
                    "transaction_status": raw_status,
                    "paid_at": now_str,
                    "zip_path": zip_path,
                    "download_url": dl_url,
                    "price_display": price_display,
                    "handover_completed": True
                }
                try:
                    with open(handover_log_path, "w", encoding="utf-8") as hf:
                        json.dump(handover_entry, hf, indent=2, ensure_ascii=False)
                    print(f"[HANDOVER] Log serah terima tersimpan: {handover_log_path}")
                except Exception as log_err:
                    print(f"[!] Warning saving handover log: {log_err}")

                # 6. Kirim notifikasi / link ZIP ke WhatsApp klien jika nomor aktif
                clean_phone = re.sub(r"[^\d]", "", phone or "")
                wa_disp = WhatsAppDispatcher()
                if len(clean_phone) >= 9:
                    fulfillment_msg = (
                        f"Halo Pimpinan *{b_name}*, pembayaran resmi invoice *{inv_id}* ({price_display}) telah kami terima dengan lunas (PAID). Terima kasih banyak atas kepercayaannya! 🙏\n\n"
                        f"Berikut adalah tautan unduh resmi paket Source Code bersih website baru Anda:\n"
                        f"📦 {dl_url}\n\n"
                        f"Paket berkas telah mencakup:\n"
                        f"1. Seluruh source code website modern (HTML, CSS, Assets)\n"
                        f"2. PANDUAN_PEMASANGAN_CPANEL.md (Langkah upload ke hosting sendiri)\n"
                        f"3. SEO_CONFIGURATION_GUIDE.md (Verifikasi Google Search Console & Schema)\n\n"
                        f"Tim kami siap mendampingi proses pemasangan hingga selesai. Sukses selalu untuk {b_name}!"
                    )
                    def _send_fulfillment_async():
                        try:
                            print(f"\n[FULFILLMENT DISPATCH ke {phone}]:\n{fulfillment_msg[:120]}...")
                            wa_disp.send_custom_message(phone, fulfillment_msg, dry_run=False)
                        except Exception as fe:
                            print(f"[!] Fulfillment WhatsApp dispatch error: {fe}")

                    threading.Thread(target=_send_fulfillment_async, daemon=True).start()

                all_leads = list(tracker.get_all_leads().values())
                wa_disp.generate_html_queue_dashboard(all_leads)

                self._send_json({
                    "success": True,
                    "status": "PAID",
                    "order_id": inv_id,
                    "zip_path": zip_path,
                    "download_url": dl_url,
                    "message": f"Settlement confirmed, package created, and fulfillment sent to {phone}."
                })
                return

            # Non-settlement statuses (pending, expire, cancel, deny)
            if raw_status:
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                inv["status"] = str(raw_status).upper()
                inv["updated_at"] = now_str
                pg.db.save_invoice(inv)
                self._send_json({
                    "success": True,
                    "status": inv["status"],
                    "order_id": inv_id,
                    "message": f"Transaction status updated to {inv['status']}."
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
        midtrans_token = inv.get("midtrans_token", "")

        pg = PaymentGateway()
        client_key = pg.client_key or "SB-Mid-client-sample"
        is_midtrans_prod = pg.is_production
        snap_script_url = (
            "https://app.midtrans.com/snap/snap.js"
            if is_midtrans_prod
            else "https://app.sandbox.midtrans.com/snap/snap.js"
        )

        return f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Invoice Pembayaran Resmi - {inv_id}</title>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap" rel="stylesheet">
{f'<script src="{snap_script_url}" data-client-key="{client_key}"></script>' if midtrans_token else ''}
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

  .btn-snap {{
    width: 100%; background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%); color: #ffffff; border: 1px solid #38bdf8;
    padding: 14px; border-radius: 8px; font-weight: 700; font-size: 14px;
    cursor: pointer; margin-top: 18px; transition: 0.2s; box-shadow: 0 4px 12px rgba(2, 132, 199, 0.3);
  }}
  .btn-snap:hover {{ background: linear-gradient(135deg, #0369a1 0%, #075985 100%); }}

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
    cursor: pointer; margin-top: 14px; transition: 0.2s;
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
  {f"""
  <button onclick="payWithSnap('{midtrans_token}')" class="btn-snap">
    ⚡ Bayar Instan via Midtrans Snap (QRIS, VA, Kartu Kredit) ↗
  </button>
  """ if midtrans_token else ""}

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
  function payWithSnap(token) {{
    if (window.snap) {{
      window.snap.pay(token, {{
        onSuccess: function(result) {{
          alert('Pembayaran berhasil!');
          location.reload();
        }},
        onPending: function(result) {{
          alert('Menunggu penyelesaian pembayaran.');
          location.reload();
        }},
        onError: function(result) {{
          alert('Pembayaran gagal atau dibatalkan.');
        }}
      }});
    }} else {{
      alert('Midtrans Snap SDK sedang dimuat...');
    }}
  }}

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


def get_lan_ip() -> str:
    """Detects primary local network IPv4 address."""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip


def start_dashboard_server(port: int = 8080, open_browser: bool = True):
    """Starts the ThreadingHTTPServer accessible on localhost and local Wi-Fi network."""
    server = None
    actual_port = port
    for p in range(port, port + 10):
        try:
            # Bind to 0.0.0.0 so phone on same Wi-Fi can connect directly
            server = ThreadingHTTPServer(("0.0.0.0", p), OutreachDashboardHandler)
            actual_port = p
            break
        except OSError:
            continue

    if not server:
        print(f"[!] Gagal memulai dashboard server pada port {port}-{port+10}.")
        return

    lan_ip = get_lan_ip()
    local_url = f"http://localhost:{actual_port}/"
    mobile_url = f"http://{lan_ip}:{actual_port}/"

    print("\n" + "=" * 80)
    print("  🚀 LEADS OUTREACH DASHBOARD & PAYMENT SERVER RUNNING")
    print(f"  💻 Akses di Laptop           : {local_url}")
    print(f"  📱 Akses di HP (Wi-Fi sama)  : {mobile_url}")
    print("  (Buka URL HP di browser smartphone Anda untuk review & kirim via WhatsApp HP)")
    print("  Tekan Ctrl+C di terminal kapan saja untuk menghentikan server.")
    print("=" * 80 + "\n")

    if open_browser:
        try:
            webbrowser.open(f"{local_url}?token={_DASHBOARD_TOKEN}")
        except Exception:
            pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[*] Dashboard server dihentikan.")
        server.server_close()


if __name__ == "__main__":
    start_dashboard_server()
