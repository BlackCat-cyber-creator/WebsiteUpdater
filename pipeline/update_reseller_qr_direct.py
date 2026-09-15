import os
import sys
import time
from playwright.sync_api import sync_playwright

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

session_dir = os.path.abspath("clients/.whatsapp_session")
scratch_dir = r"C:\Users\USER\.gemini\antigravity-ide\brain\634539b8-13d7-461e-93b9-980ab7c10733\scratch"

new_reseller = """Halo Rekan Partner / Freelancer!

Selamat datang di Program Kemitraan Agensi Website Updater Studio. 🚀

Keuntungan & Skema Kemitraan:
• 100% Whitelabel: Proposal PDF 4 halaman, demo live Vercel, hingga nomor WhatsApp closing menggunakan nama & brand Anda. Klien tidak pernah tahu kami yang mengerjakan.
• Rekomendasi Harga Jual: Kami sarankan jual di harga standar resmi Rp 1.490.000 agar sangat mudah closing di UKM (atau bebas Anda naikkan lebih tinggi Rp 2,5jt - Rp 5jt+ jika dibundling jasa Anda).
• Biaya Lisensi ke Kami: Flat hanya Rp 350.000 per website terima beres. Anda kantongi margin bersih Rp 1.140.000 per website (76%+ langsung milik Anda)!
• Terima Beres: Coding, migrasi DNS 15 menit zero-downtime, & garansi teknis 60 hari ditangani tim kami. Anda fokus closing!

Ada target Google Maps atau domain UKM yang mau kita buatkan demo live-nya sekarang?"""

with sync_playwright() as p:
    ctx = p.chromium.launch_persistent_context(
        user_data_dir=session_dir,
        channel="msedge",
        headless=True,
        viewport={"width": 1280, "height": 1050}
    )
    page = ctx.pages[0] if ctx.pages else ctx.new_page()
    page.goto("https://web.whatsapp.com", timeout=60000)
    page.wait_for_selector("#side", timeout=30000)
    time.sleep(2)

    # 1. Click Tools
    tools_btn = page.query_selector('[aria-label="Tools"]')
    if tools_btn:
        tools_btn.click()
        time.sleep(2)

    # 2. Click Quick replies
    page.locator('text="Quick replies"').first.click()
    time.sleep(2)

    # 3. Hover over the item containing 'reseller' to reveal the chevron button
    reseller_row = page.locator('div[role="listitem"]:has-text("reseller")').first
    if reseller_row.count() > 0:
        reseller_row.hover()
        time.sleep(1)
        # Find the chevron or menu button inside this row
        chevron = reseller_row.locator('button, div[role="button"]').last
        chevron.click()
        time.sleep(1)

        # Click Edit
        page.locator('li[role="button"]:has-text("Edit")').click()
        time.sleep(1.5)

        # Find the message editor box
        msg_box = page.locator('div[contenteditable="true"][role="textbox"]').last
        msg_box.click()
        time.sleep(0.5)
        page.keyboard.press("Control+A")
        page.keyboard.press("Backspace")
        time.sleep(0.5)
        page.keyboard.insert_text(new_reseller)
        time.sleep(1)

        # Click Save
        save_btn = page.locator('button:has-text("Save"), button:has-text("Simpan")').first
        save_btn.scroll_into_view_if_needed()
        save_btn.click()
        print("Successfully saved updated /reseller message!")
        time.sleep(3)
    else:
        print("Reseller row not found!")

    page.screenshot(path=os.path.join(scratch_dir, "wa_reseller_price_updated_final.png"))
    print("Screenshot saved")
    ctx.close()
