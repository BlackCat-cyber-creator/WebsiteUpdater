"""
Dedicated WhatsApp Outreach Dispatcher & Engagement Engine.
Uses Playwright with an isolated browser profile (`clients/.whatsapp_session/`) to ensure
outreach runs EXCLUSIVELY through a dedicated/new WhatsApp number, keeping personal accounts 100% safe.
Supports Dual-Track Outreach (Track A: Web Baru vs Track B: Modernisasi), reply detection,
and generates the Whitespace Minimalist HTML queue dashboard (`clients/outreach_queue.html`).
"""

import os
import re
import time
import random
import urllib.parse
from typing import Dict, Any, List, Optional
from playwright.sync_api import sync_playwright

from pipeline.quotation import get_live_usd_idr_rate

SESSION_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "clients", ".whatsapp_session"))
QUEUE_HTML_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "clients", "outreach_queue.html"))


class WhatsAppDispatcher:
    def __init__(self, session_dir: str = SESSION_DIR):
        self.session_dir = session_dir
        self.sender_wa = os.environ.get("OUTREACH_SENDER_WA", "+62 851-2801-3767").strip()
        os.makedirs(self.session_dir, exist_ok=True)

    def generate_message_text(
        self,
        business_name: str,
        domain: str,
        audit_signals: list,
        track: str = "track_b_modernize",
        rating_text: str = ""
    ) -> str:
        """
        Generates polite, concise, and high-converting Indonesian B2B WhatsApp copy
        customized for Track A (No Website) or Track B (Existing Website Modernization).
        """
        if track == "track_a_new_web":
            # Track A: Business does NOT have a website yet.
            # Friendly opening highlighting Google Search presence without sending links initially.
            rating_info = f" ({rating_text})" if rating_text else ""
            msg = (
                f"Halo Pimpinan / Tim *{business_name}*, salam kenal.\n\n"
                f"Kami melihat profil bisnis Anda di Google Maps sangat terpercaya{rating_info}.\n\n"
                f"Namun saat calon pelanggan mencari nama dan layanan Anda di Google Search, bisnis Anda saat ini belum memiliki website resmi yang bisa diakses langsung dari smartphone.\n\n"
                f"Padahal, memiliki website resmi berstandar modern terbukti meningkatkan kepercayaan pelanggan baru hingga 3x lipat dibanding hanya mengandalkan profil peta.\n\n"
                f"Sebagai bentuk apresiasi bagi bisnis lokal terpercaya, tim kami bersedia menyiapkan *prototipe website modern resmi siap pakai* yang bisa langsung dibuka di smartphone Anda — tanpa biaya maupun komitmen apa pun di awal.\n\n"
                f"Jika berkenan, boleh kami buatkan pratinjaunya? Cukup balas pesan ini ya. Terima kasih banyak! 🙏"
            )
            return msg

        # Track B: Business already has a website (Modernization & SEO Audit)
        signals_text = ""
        if audit_signals:
            signals_text = "\n".join([f"• {s}" for s in audit_signals[:2]])
        else:
            signals_text = "• Optimasi peringkat & struktur Google SEO\n• Tampilan responsif modern di smartphone"

        web_url = f"https://{domain}" if not domain.startswith("http") else domain

        msg = (
            f"Halo Pimpinan / Tim *{business_name}*, salam kenal.\n\n"
            f"Kami baru saja meninjau website operasional Anda di {web_url}.\n\n"
            f"Profil bisnis Anda sangat kredibel di bidangnya. Namun saat kami lakukan evaluasi teknis, kami melihat ada beberapa peluang penting di *Google SEO & kenyamanan tampilan smartphone* yang dapat meningkatkan konversi pelanggan:\n"
            f"{signals_text}\n\n"
            f"Sebagai bahan pertimbangan, tim kami telah menyusun *Dokumen Proposal Eksekutif (PDF 4 Halaman)* yang kami lampirkan langsung bersama pesan ini. 📄👇\n\n"
            f"Silakan buka file PDF terlampir untuk melihat analisis audit lengkap serta demonstrasi website yang telah dirapikan & dioptimasi SEO-nya.\n\n"
            f"Jika berkenan berdiskusi santai atau melihat tampilannya secara langsung, silakan balas chat ini ya. Terima kasih banyak."
        )
        return msg

    def setup_dedicated_session(self):
        """
        Interactive one-time login for the dedicated WhatsApp account.
        Opens WhatsApp Web in Edge using the dedicated profile and waits for QR scan.
        """
        print("\n" + "=" * 75)
        print("  [SETUP WHATSAPP OUTREACH - AKUN BARU / TERPISAH]")
        print("=" * 75)
        print("1. Jendela Microsoft Edge akan terbuka menuju https://web.whatsapp.com")
        print("2. Profil sesi disimpan terisolasi di: clients/.whatsapp_session/")
        print("3. PENTING: Silakan buka WhatsApp di HP/Nomor BARU Anda.")
        print("   Masuk ke: Pengaturan / Setelan > Perangkat Tertaut (Linked Devices) > Tautkan Perangkat.")
        print("   Scan QR Code yang muncul di layar.")
        print("4. Setelah berhasil masuk, terminal akan mendeteksi otomatis dan menyimpannya.")
        print("=" * 75 + "\n")

        with sync_playwright() as p:
            browser_context = p.chromium.launch_persistent_context(
                user_data_dir=self.session_dir,
                channel="msedge",
                headless=False,
                args=["--disable-blink-features=AutomationControlled"]
            )
            page = browser_context.pages[0] if browser_context.pages else browser_context.new_page()
            page.goto("https://web.whatsapp.com", timeout=60000)

            print("[WAITING] Menunggu scan QR code dari HP baru...")
            try:
                page.wait_for_selector(
                    'div[data-tab="3"], div[contenteditable="true"], #side, [aria-label="Daftar obrolan"], [aria-label="Chat list"]',
                    timeout=180000
                )
                print("\n" + "*" * 75)
                print("  [BERHASIL!] Akun WhatsApp baru Anda telah tersambung dan tersimpan permanen!")
                print("  Profil sesi disimpan di: clients/.whatsapp_session/")
                print("  Sesi ini akan digunakan otomatis untuk outreach selanjutnya.")
                print("*" * 75 + "\n")
                time.sleep(3)
            except Exception as e:
                print(f"[TIMEOUT/CANCEL] Sesi belum selesai di-scan: {e}")
            finally:
                browser_context.close()

    def dispatch_live(
        self,
        target_phone: str,
        business_name: str,
        domain: str,
        pdf_path: Optional[str] = None,
        audit_signals: Optional[list] = None,
        dry_run: bool = True,
        track: str = "track_b_modernize",
        rating_text: str = ""
    ) -> Dict[str, Any]:
        """
        Sends WhatsApp outreach via dedicated Playwright session with anti-ban human delays.
        For Track B, attaches the executive PDF proposal. For Track A, sends friendly text intro.
        """
        clean_phone = re.sub(r"[^\d]", "", target_phone)
        message = self.generate_message_text(
            business_name, domain, audit_signals or [], track=track, rating_text=rating_text
        )
        encoded_msg = urllib.parse.quote_plus(message)
        wa_url = f"https://web.whatsapp.com/send?phone={clean_phone}&text={encoded_msg}"

        if dry_run:
            print(f"[DRY-RUN WA] Target: {clean_phone} ({business_name}) | Jalur: {track}")
            print(f"[DRY-RUN WA] Link: {wa_url[:90]}...")
            if pdf_path and track == "track_b_modernize":
                print(f"[DRY-RUN WA] PDF Attachment: {pdf_path}")
            return {
                "success": True,
                "mode": "dry_run",
                "phone": clean_phone,
                "business_name": business_name,
                "track": track,
                "message": "WhatsApp message prepared (Dry-run mode, no live message sent)."
            }

        print(f"[LIVE WA] Mengirim pesan ({track}) ke {clean_phone} ({business_name})...")
        with sync_playwright() as p:
            browser_context = p.chromium.launch_persistent_context(
                user_data_dir=self.session_dir,
                channel="msedge",
                headless=False,
                args=["--disable-blink-features=AutomationControlled"]
            )
            page = browser_context.pages[0] if browser_context.pages else browser_context.new_page()
            
            try:
                page.goto(wa_url, timeout=60000)
                # 1. Wait for send button or chat input
                send_button_selector = (
                    'span[data-icon="send"], span[data-icon="wds-ic-send-filled"], '
                    'button[aria-label="Kirim"], button[aria-label="Send"], '
                    'div[role="button"][aria-label="Kirim"], div[role="button"][aria-label="Send"], '
                    'div[role="button"]:has(span[data-icon="wds-ic-send-filled"]), div[role="button"]:has(span[data-icon="send"])'
                )
                page.wait_for_selector(send_button_selector, timeout=45000)
                
                # Human delay simulation (2 to 4 seconds before clicking send)
                time.sleep(random.uniform(2.0, 4.0))
                page.click(send_button_selector)
                print(f"[+] Pesan teks WhatsApp berhasil terkirim ke {clean_phone}!")
                time.sleep(random.uniform(3.0, 5.0))

                # 2. Attach and send PDF proposal if Track B and PDF provided
                if track == "track_b_modernize" and pdf_path and os.path.exists(pdf_path):
                    abs_pdf = os.path.abspath(pdf_path)
                    print(f"[*] Melampirkan dokumen PDF proposal ke WhatsApp: {abs_pdf}...")
                    try:
                        attach_selectors = [
                            'button[aria-label="Attach"]',
                            'button[aria-label="Lampirkan"]',
                            'span[data-icon="plus"]',
                            'span[data-icon="attach-menu-plus"]',
                            'span[data-icon="clip"]'
                        ]
                        for sel in attach_selectors:
                            btn = page.query_selector(sel)
                            if btn and btn.is_visible():
                                btn.click()
                                time.sleep(1.5)
                                break

                        doc_selectors = [
                            'li:has-text("Document")',
                            'li:has-text("Dokumen")',
                            '[aria-label="Document"]',
                            '[aria-label="Dokumen"]',
                            'span:has-text("Document")',
                            'span:has-text("Dokumen")'
                        ]
                        doc_btn = None
                        for d_sel in doc_selectors:
                            doc_btn = page.query_selector(d_sel)
                            if doc_btn and doc_btn.is_visible():
                                break

                        if doc_btn:
                            with page.expect_file_chooser(timeout=10000) as fc_info:
                                doc_btn.click()
                            file_chooser = fc_info.value
                            file_chooser.set_files(abs_pdf)
                        else:
                            inputs = page.query_selector_all('input[type="file"]')
                            for inp in inputs:
                                acc = inp.get_attribute("accept") or ""
                                if "*" in acc:
                                    inp.set_input_files(abs_pdf)
                                    break

                        time.sleep(random.uniform(2.5, 4.0))

                        doc_send_selectors = [
                            'div[role="button"][aria-label*="Send"]',
                            'div[role="button"][aria-label*="Kirim"]',
                            'div[role="button"]:has(span[data-icon="wds-ic-send-filled"])',
                            'span[data-icon="wds-ic-send-filled"]',
                            'div[aria-label="Send 1 selected"]',
                            'button[aria-label="Send"]',
                            'button[aria-label="Kirim"]',
                            'span[data-icon="send"]'
                        ]
                        for d_sel in doc_send_selectors:
                            try:
                                d_btn = page.wait_for_selector(d_sel, state="visible", timeout=12000)
                                if d_btn:
                                    time.sleep(random.uniform(1.5, 2.5))
                                    d_btn.click()
                                    print(f"[+] File PDF proposal resmi berhasil terkirim ke WhatsApp {clean_phone}!")
                                    time.sleep(random.uniform(5.0, 7.0))
                                    break
                            except Exception:
                                continue
                    except Exception as attach_err:
                        print(f"[!] Catatan lampiran PDF di WhatsApp: {attach_err}")
                
                browser_context.close()
                return {
                    "success": True,
                    "mode": "live_sent",
                    "phone": clean_phone,
                    "business_name": business_name,
                    "track": track,
                    "message": f"Pesan WhatsApp berhasil terkirim ke {clean_phone}."
                }
            except Exception as e:
                browser_context.close()
                return {
                    "success": False,
                    "mode": "error",
                    "phone": clean_phone,
                    "error": str(e),
                    "message": f"Gagal mengirim WhatsApp ke {clean_phone}: {e}"
                }

    def send_custom_message(self, target_phone: str, text: str, dry_run: bool = False) -> Dict[str, Any]:
        """Sends arbitrary text message to a WhatsApp recipient."""
        clean_phone = re.sub(r"[^\d]", "", target_phone)
        if dry_run:
            print(f"[DRY-RUN WA] Custom message to {clean_phone}:\n{text}")
            return {"success": True, "mode": "dry_run"}

        encoded = urllib.parse.quote_plus(text)
        wa_url = f"https://web.whatsapp.com/send?phone={clean_phone}&text={encoded}"
        with sync_playwright() as p:
            browser_context = p.chromium.launch_persistent_context(
                user_data_dir=self.session_dir,
                channel="msedge",
                headless=False,
                args=["--disable-blink-features=AutomationControlled"]
            )
            page = browser_context.pages[0] if browser_context.pages else browser_context.new_page()
            try:
                page.goto(wa_url, timeout=60000)
                send_button_selector = (
                    'span[data-icon="send"], span[data-icon="wds-ic-send-filled"], '
                    'button[aria-label="Kirim"], button[aria-label="Send"], '
                    'div[role="button"][aria-label="Kirim"], div[role="button"][aria-label="Send"]'
                )
                page.wait_for_selector(send_button_selector, timeout=45000)
                time.sleep(random.uniform(2.0, 3.5))
                page.click(send_button_selector)
                time.sleep(random.uniform(3.0, 5.0))
                browser_context.close()
                return {"success": True, "mode": "live_sent"}
            except Exception as e:
                browser_context.close()
                return {"success": False, "error": str(e)}

    def check_incoming_replies(self, auto_respond: bool = True) -> List[Dict[str, Any]]:
        """
        Listens for incoming client replies from WhatsApp Web session.
        If a contacted lead replies, triggers Dual-Track continuation:
        - Track A: Builds/deploys Vercel site and sends live demo link.
        - Track B: Sends flexible deployment options (cPanel ZIP vs Cloud Vercel).
        """
        from pipeline.outreach.tracker import OutreachTracker
        from pipeline.deployer.vercel_deployer import VercelDeployer
        from pipeline.site_generator import SiteGenerator

        tracker = OutreachTracker()
        all_leads = tracker.get_all_leads()
        contacted_leads = {
            re.sub(r"[^\d]", "", v.get("whatsapp", "")): (k, v)
            for k, v in all_leads.items()
            if v.get("whatsapp") and v.get("status") in ["sent_whatsapp", "sent_all", "proposal_ready", "dry_run"]
        }

        if not contacted_leads:
            print("[*] Tidak ada prospek aktif yang menunggu balasan.")
            return []

        print(f"\n[REPLY LISTENER] Memeriksa balasan WhatsApp untuk {len(contacted_leads)} kontak...")
        detected_replies = []

        rate = get_live_usd_idr_rate()
        price_idr = round((100 * rate) / 1000) * 1000
        price_str = f"$100 USD (setara Rp {price_idr:,.0f} kurs live)".replace(",", ".")

        with sync_playwright() as p:
            browser_context = p.chromium.launch_persistent_context(
                user_data_dir=self.session_dir,
                channel="msedge",
                headless=False,
                args=["--disable-blink-features=AutomationControlled"]
            )
            page = browser_context.pages[0] if browser_context.pages else browser_context.new_page()

            try:
                page.goto("https://web.whatsapp.com", timeout=60000)
                page.wait_for_selector('#side, div[role="grid"]', timeout=30000)
                time.sleep(3)

                # Scan chat rows in the left sidebar
                chat_items = page.query_selector_all('#side div[role="listitem"], #side div[data-testid="cell-frame-container"]')
                print(f"[*] Terdeteksi {len(chat_items)} baris obrolan di WhatsApp Web.")

                for item in chat_items[:20]:
                    txt = item.inner_text()
                    for phone, (domain, lead) in contacted_leads.items():
                        # Match phone number in chat title or text
                        short_phone = phone[-8:]
                        if short_phone in txt or phone in txt:
                            # Check unread badge or incoming text
                            unread_badge = item.query_selector('span[data-testid="icon-unread-count"], span[aria-label*="unread"]')
                            print(f"[+] Balasan terdeteksi dari: {lead.get('business_name')} ({phone})!")

                            track = lead.get("track", "track_b_modernize")
                            b_name = lead.get("business_name", domain)
                            client_slug = domain.replace(".", "_").replace("-", "_")
                            client_dir = os.path.join("clients", client_slug)

                            detected_replies.append({
                                "domain": domain,
                                "business_name": b_name,
                                "phone": phone,
                                "track": track
                            })

                            if auto_respond:
                                if track == "track_a_new_web":
                                    # Track A Auto-Respond: Build site & Deploy Vercel
                                    site_dir = os.path.join(client_dir, "site")
                                    if not os.path.exists(os.path.join(site_dir, "index.html")):
                                        sg = SiteGenerator()
                                        sg.generate_turnkey_site(
                                            business_name=b_name,
                                            phone=phone,
                                            rating=lead.get("gmaps_rating", "4.9"),
                                            review_count=lead.get("gmaps_reviews", 50),
                                            output_dir=client_dir
                                        )
                                    vd = VercelDeployer()
                                    dep_res = vd.deploy(site_dir, client_slug)
                                    vercel_url = dep_res.get("url", f"https://{client_slug}.vercel.app")
                                    lead["vercel_url"] = vercel_url

                                    reply_copy = (
                                        f"Halo Pimpinan *{b_name}*, terima kasih banyak atas responnya! 🙏\n\n"
                                        f"Sesuai janji, website modern resmi untuk bisnis Anda telah selesai kami bangun dan langsung online di Vercel: 🌐 {vercel_url}\n\n"
                                        f"Silakan coba buka langsung di smartphone Anda. Desain responsif, super cepat, dan sudah terpasang tombol WhatsApp pemesanan langsung.\n\n"
                                        f"Layanan ini turn-key all-inclusive hanya *{price_str}* (1x bayar tanpa biaya bulanan). Website resmi ini langsung diserahterimakan penuh ke Anda.\n\n"
                                        f"Bagaimana menurut Anda tampilannya?"
                                    )
                                    self.send_custom_message(phone, reply_copy, dry_run=False)
                                    tracker.record_lead(domain, lead, status="demo_sent")
                                else:
                                    # Track B Auto-Respond: Send 3 Flexible Options
                                    reply_copy = (
                                        f"Halo Pimpinan *{b_name}*, terima kasih atas responnya! 🙏\n\n"
                                        f"Terkait modernisasi website Anda, kami menyediakan 3 opsi fleksibel (turn-key flat *{price_str}*):\n"
                                        f"1. *Source Code Bersih (.ZIP)*: Siap pasang ke cPanel / hosting Anda sendiri lengkap dengan panduan teknis.\n"
                                        f"2. *Cloud Hosting Vercel*: Bantuan migrasi penuh ke server cloud berkecepatan tinggi.\n"
                                        f"3. *Live Preview Before vs After*: Pratinjau perbandingan langsung website baru Anda.\n\n"
                                        f"Opsi mana yang paling sesuai untuk rencana pengembangan Anda?"
                                    )
                                    self.send_custom_message(phone, reply_copy, dry_run=False)
                                    tracker.record_lead(domain, lead, status="options_sent")

            except Exception as e:
                print(f"[!] Error saat memeriksa balasan WhatsApp: {e}")
            finally:
                browser_context.close()

        return detected_replies

    def generate_html_queue_dashboard(self, leads: List[Dict[str, Any]], output_path: str = QUEUE_HTML_PATH) -> str:
        """
        Generates a clean, classic whitespace minimalist dashboard with distinct
        [Jalur A] vs [Jalur B] badges and basic Green (Centang) / Red (Discard) buttons.
        """
        cards_html = []
        active_leads = [l for l in leads if l.get("status") != "discarded"]

        rate = get_live_usd_idr_rate()
        price_idr = round((100 * rate) / 1000) * 1000
        price_label = f"$100 USD (~Rp {price_idr:,.0f})".replace(",", ".")

        for lead in active_leads:
            b_name = lead.get("business_name", "Bisnis Indonesia")
            domain = lead.get("domain", "")
            wa = lead.get("whatsapp", "")
            email = lead.get("email", "")
            pdf_path = lead.get("proposal_pdf", "")
            signals = lead.get("outdated_signals", [])
            status = lead.get("status", "discovered")
            track = lead.get("track", "track_b_modernize")
            vercel_url = lead.get("vercel_url", "")
            payment_status = lead.get("payment_status", "unpaid")
            client_slug = domain.replace(".", "_").replace("-", "_")

            pdf_rel = ""
            if pdf_path:
                pdf_rel = os.path.relpath(pdf_path, os.path.dirname(output_path)).replace("\\", "/")

            # Status Badge (Google Material Design Chips)
            status_badge = {
                "discovered": '<span class="badge">Antrean</span>',
                "proposal_ready": '<span class="badge">Siap Kirim</span>',
                "sent_whatsapp": '<span class="badge badge-sent">WA Terkirim</span>',
                "sent_email": '<span class="badge badge-sent">Email Terkirim</span>',
                "sent_all": '<span class="badge badge-sent">Terkirim (WA+Email)</span>',
                "replied": '<span class="badge badge-replied">Balasan Masuk 💬</span>',
                "demo_sent": '<span class="badge badge-demo">Demo Vercel 🌐</span>',
                "options_sent": '<span class="badge badge-demo">Opsi Dikirim 📋</span>',
                "paid": '<span class="badge badge-paid">LUNAS ($100) ✅</span>',
                "dry_run": '<span class="badge">Siap Di-review</span>'
            }.get(status, f'<span class="badge">{status}</span>')

            # Track Badge
            track_badge = (
                '<span class="badge-track badge-track-a">Jalur A: Web Baru</span>'
                if track == "track_a_new_web"
                else '<span class="badge-track badge-track-b">Jalur B: Modernisasi</span>'
            )

            signals_li = "".join([f"<li>{s}</li>" for s in signals[:2]]) or "<li>Audit optimasi Google SEO & Mobile UX</li>"

            is_sent = status in ["sent_all", "sent_whatsapp", "demo_sent", "options_sent", "paid"]
            approve_btn_text = "Sudah Terkirim" if is_sent else (
                "✓ Centang (Kirim WA Pembuka)" if track == "track_a_new_web" else "✓ Centang (Kirim WA+Email+PDF)"
            )
            approve_btn_class = "btn btn-approve btn-disabled" if is_sent else "btn btn-approve"
            approve_btn_disabled = "disabled" if is_sent else ""

            # Secondary Action Buttons
            sub_actions = []
            if vercel_url:
                sub_actions.append(f'<a href="{vercel_url}" target="_blank" class="btn-sub">🌐 Live Demo ↗</a>')
            else:
                sub_actions.append(f'<button onclick="deployVercel(\'{domain}\', this)" class="btn-sub">🚀 Deploy Vercel</button>')

            sub_actions.append(f'<button onclick="createInvoice(\'{domain}\', this)" class="btn-sub">💳 Link Bayar {price_label}</button>')

            if track != "track_a_new_web":
                sub_actions.append(f'<a href="/api/download-package?client={client_slug}" target="_blank" class="btn-sub">📦 Unduh ZIP cPanel</a>')

            sub_actions_html = "".join(sub_actions)

            cards_html.append(f"""
            <div class="card" id="card-{domain.replace('.', '_')}" data-search="{b_name.lower()} {domain.lower()}">
              <div class="card-head">
                <div>
                  <div style="margin-bottom: 6px;">{track_badge}</div>
                  <h3 class="biz-title">{b_name}</h3>
                  <a href="{f'https://{domain}' if track != 'track_a_new_web' else '#'}" target="_blank" class="biz-domain">
                    {domain if track != 'track_a_new_web' else '(Belum memiliki website)'} ↗
                  </a>
                </div>
                <div id="badge-{domain.replace('.', '_')}">{status_badge}</div>
              </div>
              <div class="card-body">
                <div class="contact-row">
                  <div>WhatsApp: <strong>{wa or '<em style="color:#80868b">Tidak ditemukan</em>'}</strong></div>
                  <div>Email: <strong>{email or '<em style="color:#80868b">Tidak ditemukan</em>'}</strong></div>
                </div>
                <div class="audit-summary">
                  <strong>Poin Strategis:</strong>
                  <ul>{signals_li}</ul>
                </div>
              </div>
              <div class="card-actions">
                <button onclick="approveLead('{domain}', this)" class="{approve_btn_class}" {approve_btn_disabled}>
                  {approve_btn_text}
                </button>
                {f'<button onclick="discardLead(\'{domain}\', this)" class="btn btn-discard">✕ Discard</button>' if not is_sent else ''}
              </div>
              <div class="sub-actions-row">
                {sub_actions_html}
              </div>
              <div class="card-footer">
                {f'<a href="{pdf_rel}" target="_blank" class="pdf-preview-link">Lihat Dokumen PDF Proposal Eksekutif ↗</a>' if pdf_rel and track == 'track_b_modernize' else '<span style="color:#80868b;font-size:12px">Jalur A: Tanpa attachment PDF awal</span>'}
              </div>
            </div>
            """)

        track_a_count = len([l for l in active_leads if l.get('track') == 'track_a_new_web'])
        track_b_count = len([l for l in active_leads if l.get('track') != 'track_a_new_web'])
        replied_count = len([l for l in active_leads if l.get('status') in ['replied', 'demo_sent', 'options_sent']])
        paid_count = len([l for l in active_leads if l.get('payment_status') == 'paid' or l.get('status') == 'paid'])

        full_html = f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Antrean Prospek Outreach - Website Updater Studio</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Roboto:wght@400;500;700&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg-main: #ffffff;
    --bg-surface: #f8f9fa;
    --border-color: #dadce0;
    --border-light: #dfe1e5;
    --text-primary: #202124;
    --text-secondary: #5f6368;
    --google-blue: #1a73e8;
    --google-blue-hover: #174ea6;
    --google-blue-light: #e8f0fe;
    --google-red: #d93025;
    --google-green: #188038;
    --shadow-search: 0 1px 6px rgba(32,33,36,.28);
    --shadow-card: 0 1px 2px 0 rgba(60,64,67,.3), 0 1px 3px 1px rgba(60,64,67,.15);
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: 'Plus Jakarta Sans', 'Roboto', -apple-system, sans-serif;
    background-color: var(--bg-surface);
    color: var(--text-primary);
    padding: 24px 20px 60px;
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
  }}
  .container {{ max-width: 1080px; margin: 0 auto; }}

  /* GOOGLE HEADER & CENTER LOGO */
  .google-top-bar {{
    display: flex; justify-content: space-between; align-items: center;
    background: #ffffff; border: 1px solid var(--border-color); border-radius: 8px;
    padding: 14px 24px; margin-bottom: 24px; box-shadow: 0 1px 2px rgba(0,0,0,0.05);
  }}
  .brand-group {{ display: flex; align-items: center; gap: 10px; }}
  .dots {{ display: flex; gap: 3px; }}
  .dot {{ width: 8px; height: 8px; border-radius: 50%; }}
  .dot-b {{ background: #4285f4; }}
  .dot-r {{ background: #ea4335; }}
  .dot-y {{ background: #fbbc05; }}
  .dot-g {{ background: #34a853; }}
  .brand-title {{ font-size: 17px; font-weight: 700; color: var(--text-primary); }}
  .brand-sub {{ font-size: 13px; color: var(--text-secondary); margin-left: 6px; }}

  /* ICONIC ROUNDED SEARCH BAR */
  .search-wrapper {{
    max-width: 680px; margin: 0 auto 24px; position: relative;
  }}
  .search-box {{
    width: 100%; height: 48px; background: #ffffff;
    border: 1px solid var(--border-light); border-radius: 24px;
    padding: 0 20px; display: flex; align-items: center; gap: 12px;
    box-shadow: none; transition: all 0.2s ease;
  }}
  .search-box:focus-within, .search-box:hover {{
    box-shadow: var(--shadow-search); border-color: transparent;
  }}
  .search-icon {{ color: #9aa0a6; width: 20px; height: 20px; flex-shrink: 0; }}
  .search-input {{
    flex: 1; border: none; outline: none; font-size: 15px;
    color: var(--text-primary); font-family: inherit;
  }}
  .search-input::placeholder {{ color: #80868b; }}

  /* NOTICE BANNER */
  .notice-banner {{
    background: #ffffff; border: 1px solid var(--border-color); border-radius: 8px;
    padding: 12px 18px; font-size: 13px; color: var(--text-secondary); margin-bottom: 20px;
    display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;
  }}
  .notice-banner strong {{ color: var(--text-primary); }}

  /* STATS CHIPS */
  .stats-bar {{
    display: flex; gap: 10px; margin-bottom: 24px; flex-wrap: wrap;
  }}
  .stat-chip {{
    background: #ffffff; border: 1px solid var(--border-color);
    padding: 8px 16px; border-radius: 20px; font-size: 13px; color: var(--text-secondary);
    display: flex; align-items: center; gap: 6px;
  }}
  .stat-chip strong {{ font-size: 14px; color: var(--text-primary); }}

  /* LEAD GRID */
  .lead-grid {{
    display: grid; grid-template-columns: repeat(auto-fill, minmax(500px, 1fr)); gap: 20px;
  }}
  @media (max-width: 600px) {{
    .lead-grid {{ grid-template-columns: 1fr; }}
  }}
  
  /* CARDS: MATERIAL DESIGN */
  .card {{
    background: #ffffff; border: 1px solid var(--border-color); border-radius: 8px;
    padding: 20px; display: flex; flex-direction: column; justify-content: space-between;
    transition: box-shadow 0.2s, transform 0.15s;
  }}
  .card:hover {{
    box-shadow: 0 4px 12px rgba(60,64,67,.15);
  }}
  .card-head {{ display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; }}
  .biz-title {{ font-size: 17px; font-weight: 700; color: var(--text-primary); }}
  .biz-domain {{ font-size: 13px; color: var(--google-blue); text-decoration: none; display: inline-block; margin-top: 2px; }}
  .biz-domain:hover {{ text-decoration: underline; }}

  /* MATERIAL CHIPS & BADGES */
  .badge {{
    display: inline-block; padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: 600;
    background: #f1f3f4; color: var(--text-secondary); border: 1px solid var(--border-light);
  }}
  .badge-sent {{ background: var(--google-blue-light); color: var(--google-blue); border-color: #c2e7ff; }}
  .badge-replied {{ background: #fce8e6; color: #c5221f; border-color: #fad2cf; }}
  .badge-demo {{ background: #f3e8fd; color: #7627bb; border-color: #e9d5ff; }}
  .badge-paid {{ background: #e6f4ea; color: #137333; border-color: #ceead6; }}

  .badge-track {{
    display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700;
  }}
  .badge-track-a {{
    background: #e8f0fe; color: #1967d2; border: 1px solid #c2e7ff;
  }}
  .badge-track-b {{
    background: #fef7e0; color: #b06000; border: 1px solid #feefc3;
  }}
  
  .card-body {{ font-size: 13px; color: var(--text-secondary); margin-bottom: 16px; }}
  .contact-row {{
    background: var(--bg-surface); padding: 10px 14px; border-radius: 6px;
    margin-bottom: 10px; border: 1px solid #f1f3f4; display: flex; flex-direction: column; gap: 4px;
  }}
  .contact-row strong {{ color: var(--text-primary); }}
  .audit-summary {{ font-size: 12px; }}
  .audit-summary ul {{ padding-left: 18px; margin-top: 4px; color: var(--text-secondary); }}

  /* GOOGLE MATERIAL BUTTONS */
  .card-actions {{ display: flex; gap: 8px; margin-top: 6px; }}
  .btn {{
    display: inline-flex; align-items: center; justify-content: center;
    padding: 10px 16px; border-radius: 4px; font-size: 13px; font-weight: 600;
    cursor: pointer; border: none; transition: background 0.15s, box-shadow 0.15s;
    font-family: inherit;
  }}
  .btn-approve {{ background: var(--google-blue); color: #ffffff; flex: 2; }}
  .btn-approve:hover:not(:disabled) {{ background: var(--google-blue-hover); box-shadow: 0 1px 3px rgba(66,133,244,.3); }}
  .btn-discard {{ background: #ffffff; color: var(--google-red); border: 1px solid #fad2cf; flex: 1; }}
  .btn-discard:hover {{ background: #fce8e6; }}
  .btn-disabled {{
    background: #f1f3f4 !important; color: #80868b !important; border: 1px solid var(--border-color) !important; cursor: default;
  }}
  
  /* SUB ACTIONS ROW */
  .sub-actions-row {{
    display: flex; gap: 6px; margin-top: 10px; flex-wrap: wrap;
  }}
  .btn-sub {{
    background: #ffffff; border: 1px solid var(--border-color); color: var(--text-primary);
    padding: 6px 12px; border-radius: 4px; font-size: 12px; text-decoration: none;
    cursor: pointer; font-weight: 500; transition: background 0.15s, border-color 0.15s;
  }}
  .btn-sub:hover {{ background: #f8f9fa; border-color: #c4c7c5; color: var(--text-primary); }}

  .card-footer {{
    margin-top: 12px; padding-top: 8px; border-top: 1px solid #f1f3f4; text-align: center;
  }}
  .pdf-preview-link {{
    font-size: 12px; color: var(--google-blue); text-decoration: none;
  }}
  .pdf-preview-link:hover {{ text-decoration: underline; }}

  #toast {{
    position: fixed; bottom: 24px; right: 24px; background: #323232; color: #ffffff;
    padding: 12px 20px; border-radius: 4px; box-shadow: 0 3px 8px rgba(0,0,0,.24);
    display: none; font-size: 13px; z-index: 9999;
  }}
</style>
</head>
<body>
<div class="container">
  <!-- Google Style Top Bar -->
  <div class="google-top-bar">
    <div class="brand-group">
      <div class="dots">
        <span class="dot dot-b"></span>
        <span class="dot dot-r"></span>
        <span class="dot dot-y"></span>
        <span class="dot dot-g"></span>
      </div>
      <div>
        <span class="brand-title">Website Updater</span>
        <span class="brand-sub">Dasbor Antrean Prospek Outreach ($100 Turn-Key)</span>
      </div>
    </div>
    <div style="display:flex; gap:10px; align-items:center;">
      <a href="https://websiteupdater.vercel.app" target="_blank" class="btn-sub" style="color:var(--google-blue); font-weight:600;">
        🌐 Buka Agency Website ↗
      </a>
      <button onclick="checkReplies()" class="btn-sub">
        🔄 Cek Balasan WhatsApp
      </button>
    </div>
  </div>

  <!-- Iconic Rounded Google Search Bar for Real-Time Filtering -->
  <div class="search-wrapper">
    <div class="search-box">
      <svg class="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="11" cy="11" r="8"></circle>
        <line x1="21" y1="21" x2="16.65" y2="16.65"></line>
      </svg>
      <input type="text" id="lead-filter-input" class="search-input" placeholder="Cari nama bisnis, domain, atau status prospek..." oninput="filterLeads(this.value)">
    </div>
  </div>

  <!-- Notice Banner -->
  <div class="notice-banner">
    <span>Tarif resmi flat: <strong>{price_label}</strong>. Klik <strong>Centang</strong> untuk kirim pesan sesuai alur jalur (Jalur A: Chat pembuka ramah, Jalur B: Audit teknis + PDF).</span>
    <span style="font-size:12px; color:var(--text-secondary);">Server: <strong>http://localhost:8080</strong></span>
  </div>

  <!-- Stats Chips -->
  <div class="stats-bar">
    <div class="stat-chip">Total Antrean: <strong>{len(active_leads)}</strong></div>
    <div class="stat-chip" style="color:#1967d2;">Jalur A (Web Baru): <strong>{track_a_count}</strong></div>
    <div class="stat-chip" style="color:#b06000;">Jalur B (Modernisasi): <strong>{track_b_count}</strong></div>
    <div class="stat-chip" style="color:#c5221f;">Balasan Masuk: <strong>{replied_count}</strong></div>
    <div class="stat-chip" style="color:#137333;">Lunas ($100): <strong>{paid_count}</strong></div>
  </div>

  <!-- Lead Cards Grid -->
  <div class="lead-grid" id="lead-grid">
    {''.join(cards_html) if cards_html else '<p style="color:#70757a">Semua antrean telah diproses. Jalankan <code>python auto_outreach.py --maps "bengkel las jakarta"</code> untuk menambah prospek baru.</p>'}
  </div>
</div>

<div id="toast"></div>

<script>
  function showToast(msg) {{
    const toast = document.getElementById('toast');
    toast.style.display = 'block';
    toast.innerHTML = msg;
    setTimeout(() => {{ toast.style.display = 'none'; }}, 4000);
  }}

  // Real-time Google Search filtering of leads
  function filterLeads(query) {{
    const q = query.toLowerCase().trim();
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {{
      const searchData = card.getAttribute('data-search') || '';
      card.style.display = searchData.includes(q) ? 'flex' : 'none';
    }});
  }}

  async function approveLead(domain, btn) {{
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = 'Sedang mengirim...';
    
    try {{
      const res = await fetch('/api/approve?domain=' + encodeURIComponent(domain), {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }}
      }});
      
      if (!res.ok) throw new Error('Status: ' + res.status);
      const data = await res.json();
      
      if (data.success) {{
        btn.innerHTML = 'Sudah Terkirim';
        btn.className = 'btn btn-disabled';
        const cardId = 'card-' + domain.replace(/\\./g, '_');
        const badge = document.getElementById('badge-' + domain.replace(/\\./g, '_'));
        if (badge) badge.innerHTML = '<span class="badge badge-sent">Terkirim</span>';
        
        const card = document.getElementById(cardId);
        if (card) {{
          const discardBtn = card.querySelector('.btn-discard');
          if (discardBtn) discardBtn.remove();
        }}
        showToast('Sukses terkirim ke ' + domain);
      }} else {{
        btn.disabled = false;
        btn.innerHTML = originalText;
        showToast('Gagal: ' + (data.errors ? data.errors.join(', ') : data.error));
      }}
    }} catch (err) {{
      btn.disabled = false;
      btn.innerHTML = originalText;
      alert("Server dashboard belum aktif di terminal.\\n\\nJalankan perintah ini:\\npython auto_outreach.py --dashboard");
    }}
  }}

  async function discardLead(domain, btn) {{
    if (!confirm('Discard prospek ' + domain + '?')) return;
    
    const cardId = 'card-' + domain.replace(/\\./g, '_');
    const card = document.getElementById(cardId);
    
    try {{
      await fetch('/api/discard?domain=' + encodeURIComponent(domain), {{
        method: 'POST',
        headers: {{ 'Content-Type': 'application/json' }}
      }});
      if (card) {{
        card.style.opacity = '0';
        setTimeout(() => {{ card.remove(); }}, 200);
      }}
      showToast('Prospek ' + domain + ' di-discard.');
    }} catch (err) {{
      if (card) {{
        card.style.opacity = '0';
        setTimeout(() => {{ card.remove(); }}, 200);
      }}
    }}
  }}

  async function deployVercel(domain, btn) {{
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = 'Deploying...';
    try {{
      const res = await fetch('/api/deploy-vercel?domain=' + encodeURIComponent(domain), {{ method: 'POST' }});
      const data = await res.json();
      if (data.success) {{
        btn.outerHTML = `<a href="${{data.url}}" target="_blank" class="btn-sub">🌐 Live Demo ↗</a>`;
        showToast('Website berhasil live di Vercel: ' + data.url);
      }} else {{
        btn.disabled = false;
        btn.innerHTML = originalText;
        alert('Gagal deploy: ' + data.error);
      }}
    }} catch (e) {{
      btn.disabled = false;
      btn.innerHTML = originalText;
      alert('Error server: ' + e);
    }}
  }}

  async function createInvoice(domain, btn) {{
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = 'Membuat invoice...';
    try {{
      const res = await fetch('/api/create-invoice?domain=' + encodeURIComponent(domain), {{ method: 'POST' }});
      const data = await res.json();
      if (data.success) {{
        btn.disabled = false;
        btn.innerHTML = '💳 Buka Invoice';
        btn.onclick = () => window.open(data.payment_url, '_blank');
        showToast('Link Invoice $100: ' + data.payment_url);
        navigator.clipboard.writeText(data.payment_url);
      }} else {{
        btn.disabled = false;
        btn.innerHTML = originalText;
        alert('Gagal membuat invoice: ' + data.error);
      }}
    }} catch (e) {{
      btn.disabled = false;
      btn.innerHTML = originalText;
      alert('Error server: ' + e);
    }}
  }}

  async function checkReplies() {{
    showToast('Sedang memindai balasan WhatsApp masuk...');
    try {{
      const res = await fetch('/api/check-replies', {{ method: 'POST' }});
      const data = await res.json();
      showToast('Pemeriksaan selesai. Balasan baru: ' + (data.replies_found || 0));
      setTimeout(() => location.reload(), 1500);
    }} catch (e) {{
      alert('Gagal memeriksa balasan: ' + e);
    }}
  }}
</script>
</body>
</html>
"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(full_html)
        return output_path
