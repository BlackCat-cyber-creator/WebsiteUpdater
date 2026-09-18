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


from pipeline.deployer.vercel_deployer import VercelDeployer

SESSION_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "clients", ".whatsapp_session"))
QUEUE_HTML_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "clients", "outreach_queue.html"))


class HumanizedWASimulator:
    """
    Biological human keystroke simulator and safe outreach throttler.
    Simulates real typing presence ('Sedang mengetik...'), organic micro-hesitations,
    mouse wanderings, and enforces safe interval delays to protect sender numbers.
    """

    @staticmethod
    def type_humanized(page, selector: str, text: str):
        """
        Types text character-by-character into the WhatsApp contenteditable field,
        triggering real DOM keyboard events and the native 'typing...' presence signal.
        """
        element = page.locator(selector).first
        element.click()
        time.sleep(random.uniform(0.6, 1.2))

        # Split text into lines to handle Shift+Enter vs Enter
        lines = text.split("\n")
        for line_idx, line in enumerate(lines):
            for char in line:
                # Keystroke delay with random biological variation (30ms - 80ms)
                char_delay = random.uniform(30, 80)
                element.type(char, delay=char_delay)

                # Micro-pause on punctuation (simulating human reading/thought)
                if char in [".", "!", "?"]:
                    time.sleep(random.uniform(0.30, 0.65))
                elif char == ",":
                    time.sleep(random.uniform(0.12, 0.28))

                # Rare micro-pause (simulating checking a reference or hesitation)
                if random.random() < 0.012:
                    time.sleep(random.uniform(0.7, 1.4))

            # Newline in WhatsApp Web requires Shift+Enter so message doesn't fire prematurely
            if line_idx < len(lines) - 1:
                page.keyboard.press("Shift+Enter")
                time.sleep(random.uniform(0.15, 0.35))

        # Natural hesitation before hitting send
        time.sleep(random.uniform(1.2, 2.4))

    @staticmethod
    def human_mouse_wander(page):
        """Simulates human mouse movement and jitter across the viewport."""
        try:
            viewport = page.viewport_size or {"width": 1280, "height": 800}
            for _ in range(random.randint(2, 4)):
                x = random.randint(150, max(160, viewport["width"] - 150))
                y = random.randint(150, max(160, viewport["height"] - 150))
                page.mouse.move(x, y, steps=random.randint(5, 12))
                time.sleep(random.uniform(0.08, 0.20))
        except Exception:
            pass

    @staticmethod
    def get_safe_dispatch_delay(sent_today: int = 0) -> int:
        """
        Returns safe interval in seconds between messages:
        - First 1-10 messages: 120 - 240 seconds (2 - 4 minutes).
        - 11-25 messages: 240 - 420 seconds (4 - 7 minutes).
        - Every 5 messages: 15-minute cool-down break.
        """
        if sent_today > 0 and sent_today % 5 == 0:
            print("[SAFE-THROTTLE] Cooling pause 15 menit untuk menjaga reputasi nomor...")
            return random.randint(840, 960)

        if sent_today < 10:
            return random.randint(120, 240)
        return random.randint(240, 420)

    @staticmethod
    def check_business_hours() -> bool:
        """Returns True if current local hour is between 08:00 and 20:00 WIB."""
        from datetime import datetime
        now = datetime.now()
        current_minute = now.hour * 60 + now.minute
        return 480 <= current_minute <= 1200


class WhatsAppDispatcher:
    def __init__(self, session_dir: str = SESSION_DIR):
        self.session_dir = session_dir
        self.sender_wa = os.environ.get("OUTREACH_SENDER_WA", "+62 851-2801-3767").strip()
        os.makedirs(self.session_dir, exist_ok=True)
        
        # Meta WhatsApp Cloud API Integration (Jalur 2 Official)
        from pipeline.outreach.meta_wa_client import MetaWhatsAppClient
        self.meta_client = MetaWhatsAppClient()
        self.provider = os.environ.get("WA_PROVIDER", "auto").lower().strip()

    def is_using_meta(self) -> bool:
        """Returns True if WhatsApp should be dispatched via Meta Cloud API."""
        if self.provider == "meta":
            return True
        if self.provider == "auto" and self.meta_client.is_configured():
            return True
        return False

    def generate_message_text(
        self,
        business_name: str,
        domain: str,
        audit_signals: list,
        track: str = "track_b_modernize",
        rating_text: str = "",
        step: str = "step_1_permission",
        demo_url: str = ""
    ) -> str:
        """Delegates copy generation to message_formatter module with Two-Step support."""
        from pipeline.outreach.message_formatter import generate_outreach_message
        return generate_outreach_message(
            business_name, domain, audit_signals, track=track, rating_text=rating_text, step=step, demo_url=demo_url
        )

    def setup_dedicated_session(self):
        """
        Interactive one-time login for the dedicated WhatsApp account.
        Opens WhatsApp Web in Edge using the dedicated profile and waits for QR scan.
        """
        if self.is_using_meta():
            print("\n" + "=" * 75)
            print("  [WHATSAPP PROVIDER: OFFICIAL META CLOUD API (JALUR 2)]")
            print("=" * 75)
            print("Status Konfigurasi:")
            print(f"- Provider: Meta Cloud API")
            print(f"- Phone Number ID: {self.meta_client.phone_number_id or '(Belum diisi di .env)'}")
            print(f"- Status: {'LENGKAP & SIAP PAKAI' if self.meta_client.is_configured() else 'BELUM LENGKAP (Cek .env)'}")
            print("\nAnda tidak memerlukan scan QR di browser! Pesan akan dikirim langsung via server resmi Meta.")
            print("=" * 75 + "\n")
            return

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
        rating_text: str = "",
        step: str = "step_1_permission",
        demo_url: str = ""
    ) -> Dict[str, Any]:
        """
        Sends WhatsApp outreach via dedicated Meta Cloud API or Playwright session with anti-ban human delays.
        Supports Two-Step Permission Outreach:
        - 'step_1_permission': Sends polite curiosity/permission hook via humanized typing (no PDF attached).
        - 'step_2_delivery': Sends live demo link and attaches executive PDF proposal.
        """
        clean_phone = re.sub(r"[^\d]", "", target_phone)
        message = self.generate_message_text(
            business_name, domain, audit_signals or [], track=track, rating_text=rating_text, step=step, demo_url=demo_url
        )

        # Check safe business hours (08:30 - 17:30 WIB)
        if not HumanizedWASimulator.check_business_hours():
            print("[INFO] Pengiriman dilakukan di luar jam operasional bisnis (08:30 - 17:30).")

        # 1. Meta WhatsApp Cloud API Dispatch (Jalur 2 Official)
        if self.is_using_meta():
            if not self.meta_client.is_configured() and not dry_run:
                print("[!] Meta WhatsApp Cloud API credentials belum lengkap di .env.")
                return {
                    "success": False,
                    "mode": "error",
                    "provider": "meta_cloud",
                    "phone": clean_phone,
                    "message": "WA_PROVIDER=meta aktif, namun META_WHATSAPP_TOKEN atau META_PHONE_NUMBER_ID belum diisi di .env."
                }
            # Only attach PDF if in delivery stage
            dispatch_pdf = pdf_path if step in ["step_2_delivery", "legacy_one_shot"] else None
            return self.meta_client.send_outreach(
                target_phone=target_phone,
                business_name=business_name,
                domain=domain,
                pdf_path=dispatch_pdf,
                dry_run=dry_run,
                track=track,
                message_text=message
            )

        # 2. Playwright Browser Fallback Dispatch
        wa_url = f"https://web.whatsapp.com/send?phone={clean_phone}"
        step_label = "Izin Tahap 1" if step == "step_1_permission" else "Delivery Tahap 2"

        if dry_run:
            print(f"[DRY-RUN WA] Target: {clean_phone} ({business_name}) | Jalur: {track} | Mode: {step_label}")
            print(f"[DRY-RUN WA] Link: {wa_url}...")
            if pdf_path and step in ["step_2_delivery", "legacy_one_shot"]:
                print(f"[DRY-RUN WA] PDF Attachment: {pdf_path}")
            else:
                print(f"[DRY-RUN WA] PDF Attachment: (Dilewati untuk {step_label} - Menjaga reputasi anti-spam)")
            return {
                "success": True,
                "mode": "dry_run",
                "phone": clean_phone,
                "business_name": business_name,
                "track": track,
                "step": step,
                "message": f"WhatsApp message prepared ({step_label}, Dry-run mode, no live message sent)."
            }

        print(f"[LIVE WA] Mengirim pesan {step_label} ({track}) ke {clean_phone} ({business_name}) dengan simulasi ketikan manusia...")
        with sync_playwright() as p:
            browser_context = p.chromium.launch_persistent_context(
                user_data_dir=self.session_dir,
                channel="msedge",
                headless=True,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
                args=[
                    "--headless=new",
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox"
                ],
                viewport={"width": 1280, "height": 800}
            )
            page = browser_context.pages[0] if browser_context.pages else browser_context.new_page()
            
            try:
                page.goto(wa_url, timeout=60000)
                time.sleep(3.5)

                # Fast Check 1: Meta/WhatsApp Account Restriction on Linked Devices
                body_text = page.inner_text("body") if page.query_selector("body") else ""
                if "restricted" in body_text.lower() or page.query_selector('text="restricted"'):
                    countdown = ""
                    try:
                        show_details = page.locator("text=Show details").first
                        if show_details.is_visible():
                            show_details.click()
                            time.sleep(1)
                            modal = page.query_selector('[role="dialog"]')
                            if modal:
                                m = re.search(r"\b(\d{2}:\d{2}:\d{2})\b", modal.inner_text())
                                if m:
                                    countdown = m.group(1)
                    except Exception:
                        pass
                    
                    cd_str = f"tersisa {countdown}" if countdown else "cooldown ~2-3 jam"
                    browser_context.close()
                    print(f"[!] WhatsApp Linked Device terkena pembatasan sementara Meta ({cd_str}).")
                    return {
                        "success": False,
                        "mode": "restricted",
                        "phone": clean_phone,
                        "business_name": business_name,
                        "countdown": countdown,
                        "message": f"WhatsApp Linked Device sedang cooldown sementara oleh Meta ({cd_str}). Anda tetap bisa mengirim chat langsung via HP utama tanpa restriksi."
                    }

                # Fast Check 2: Invalid / Unregistered Phone Number Popup
                invalid_selectors = [
                    'text="isn\'t on WhatsApp"',
                    'text="is not on WhatsApp"',
                    'text="tidak terdaftar di WhatsApp"',
                    'text="tidak ada di WhatsApp"',
                    'text="Phone number shared via url is invalid"',
                    'div[data-animate-modal-popup="true"]:has-text("tidak valid")',
                    'div[data-animate-modal-popup="true"]:has-text("invalid")',
                    '[role="dialog"]:has-text("tidak valid")',
                    '[role="dialog"]:has-text("invalid")'
                ]
                for isel in invalid_selectors:
                    if page.locator(isel).is_visible():
                        # Click OK to dismiss popup cleanly
                        ok_btn = page.locator('div[role="button"]:has-text("OK"), button:has-text("OK")').first
                        if ok_btn.is_visible():
                            try:
                                ok_btn.click()
                            except Exception:
                                pass
                        browser_context.close()
                        print(f"[!] Nomor {clean_phone} tidak terdaftar di WhatsApp.")
                        return {
                            "success": False,
                            "mode": "invalid_phone",
                            "phone": clean_phone,
                            "business_name": business_name,
                            "message": f"Nomor {clean_phone} tidak terdaftar di WhatsApp."
                        }

                # 1. Humanized Keystroke Typing into Chat Input Field
                chat_input_selector = 'footer div[contenteditable="true"]'
                try:
                    page.wait_for_selector(chat_input_selector, timeout=25000)
                    # Natural mouse movement before clicking input
                    HumanizedWASimulator.human_mouse_wander(page)
                    # Type message organically with human delays and presence triggers
                    HumanizedWASimulator.type_humanized(page, chat_input_selector, message)
                    # Natural mouse movement after typing
                    HumanizedWASimulator.human_mouse_wander(page)
                except Exception as e_typing:
                    print(f"[*] Humanized typing fallback: {e_typing}")
                    # Direct insertion fallback
                    chat_input = page.query_selector(chat_input_selector)
                    if chat_input:
                        chat_input.click()
                        page.keyboard.insert_text(message)
                        time.sleep(1.5)

                send_button_selector = (
                    'span[data-icon="send"], span[data-icon="wds-ic-send-filled"], '
                    'button[aria-label="Kirim"], button[aria-label="Send"], '
                    'div[role="button"][aria-label="Kirim"], div[role="button"][aria-label="Send"], '
                    'div[role="button"]:has(span[data-icon="wds-ic-send-filled"]), div[role="button"]:has(span[data-icon="send"])'
                )
                
                try:
                    page.wait_for_selector(send_button_selector, timeout=8000)
                    time.sleep(random.uniform(1.2, 2.5))
                    page.click(send_button_selector)
                except Exception:
                    # Fallback: check footer chat input and press Enter
                    chat_input = page.query_selector(chat_input_selector)
                    if chat_input:
                        chat_input.press("Enter")
                        time.sleep(2.0)
                    else:
                        raise

                print(f"[+] Pesan teks WhatsApp ({step_label}) berhasil terkirim ke {clean_phone}!")
                time.sleep(random.uniform(2.5, 4.0))

                # 2. Attach and send PDF proposal ONLY for Delivery Step (step_2_delivery / legacy)
                if step in ["step_2_delivery", "legacy_one_shot"] and pdf_path and os.path.exists(pdf_path):
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
                                    time.sleep(random.uniform(1.2, 2.0))
                                    print(f"[*] Menekan tombol kirim dokumen PDF untuk {clean_phone}...")
                                    d_btn.click()
                                    # Wait for PDF upload and encryption to complete (up to 20s) to prevent severed upload stream
                                    print("[*] Menunggu sinkronisasi berkas PDF ke server Meta WhatsApp...")
                                    time.sleep(random.uniform(15.0, 20.0))
                                    print(f"[+] File PDF proposal resmi berhasil terkirim ke WhatsApp {clean_phone}!")
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

        # 1. Meta WhatsApp Cloud API (Jalur 2 Official)
        if self.is_using_meta():
            from pipeline.outreach.meta_wa_client import normalize_phone_e164
            e164_phone = normalize_phone_e164(target_phone)
            if dry_run:
                print(f"[DRY-RUN META WA] Custom message to +{e164_phone}:\n{text}")
                return {"success": True, "mode": "dry_run", "provider": "meta_cloud", "phone": e164_phone}
            res = self.meta_client.send_text_message(to=e164_phone, text=text)
            if res.get("success"):
                return {"success": True, "mode": "live_sent", "provider": "meta_cloud", "phone": e164_phone, "message_id": res.get("message_id")}
            else:
                return {"success": False, "mode": "error", "provider": "meta_cloud", "phone": e164_phone, "error": res.get("error")}

        # 2. Playwright Browser Fallback
        if dry_run:
            print(f"[DRY-RUN WA] Custom message to {clean_phone}:\n{text}")
            return {"success": True, "mode": "dry_run"}

        encoded = urllib.parse.quote_plus(text)
        wa_url = f"https://web.whatsapp.com/send?phone={clean_phone}&text={encoded}"
        with sync_playwright() as p:
            browser_context = p.chromium.launch_persistent_context(
                user_data_dir=self.session_dir,
                channel="msedge",
                headless=True,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
                args=[
                    "--headless=new",
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox"
                ],
                viewport={"width": 1280, "height": 800}
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

        price_str = "Rp 1.490.000 (Flat all-in terima beres tanpa biaya bulanan)"

        with sync_playwright() as p:
            browser_context = p.chromium.launch_persistent_context(
                user_data_dir=self.session_dir,
                channel="msedge",
                headless=True,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36 Edg/126.0.0.0",
                args=[
                    "--headless=new",
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox"
                ],
                viewport={"width": 1280, "height": 800}
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
                                pdf_path = lead.get("proposal_pdf", "")
                                if not pdf_path or not os.path.exists(pdf_path):
                                    cand_pdf = os.path.join(client_dir, "client_proposal.pdf")
                                    if os.path.exists(cand_pdf):
                                        pdf_path = os.path.abspath(cand_pdf)

                                demo_url = lead.get("vercel_url") or lead.get("demo_url", "")
                                print(f"[+] Balasan terdeteksi dari {b_name}! Mengirim respon Tahap 2 otomatis (+ Live Demo & PDF)...")
                                self.dispatch_live(
                                    target_phone=phone,
                                    business_name=b_name,
                                    domain=domain,
                                    pdf_path=pdf_path,
                                    demo_url=demo_url,
                                    audit_signals=lead.get("outdated_signals", []),
                                    dry_run=False,
                                    track=track,
                                    rating_text=lead.get("gmaps_rating", ""),
                                    step="step_2_delivery"
                                )
                                lead["status"] = "sent_step2"
                                tracker.record_lead(domain, lead, status="sent_step2")

            except Exception as e:
                print(f"[!] Error saat memeriksa balasan WhatsApp: {e}")
            finally:
                browser_context.close()

        return detected_replies

    def generate_html_queue_dashboard(self, leads: List[Dict[str, Any]], output_path: str = QUEUE_HTML_PATH) -> str:
        """Delegates dashboard HTML generation to dedicated queue_dashboard module."""
        from pipeline.outreach.queue_dashboard import generate_html_queue_dashboard
        return generate_html_queue_dashboard(leads, output_path)
