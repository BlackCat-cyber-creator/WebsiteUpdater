# 🛠️ Master Prompt & Playbook: Pipeline Refinement & Execution Guide

Dokumen ini berisi **Master Prompt AI Agent** untuk menyempurnakan (*refine*) pipeline, arsitektur modul lengkap, serta **panduan operasional langkah-demi-langkah** untuk menjalankan setiap komponen sistem Website Updater Studio.

---

## 🤖 1. Master Prompt untuk AI / Developer (Copy-Paste Ready)

Gunakan prompt berikut saat Anda ingin meminta AI (Claude, GPT, Antigravity, dll.) melakukan audit, optimasi, atau pengembangan fitur baru pada pipeline:

```markdown
Anda adalah Principal Software Engineer & Automation Architect kelas dunia yang mengkhususkan diri pada Web Engineering, Headless Browser Automation, dan B2B Growth Engines.

Tugas Anda adalah meninjau, menyempurnakan (refine), dan mengoptimalkan pipeline autonomous agency di repository ini:
Repositori: Website Updater Studio (Turn-Key $100 USD Web Agency Engine)

Konteks Sistem:
1. Memiliki 2 Jalur Operasi:
   - Jalur A (Web Baru): Scan Google Maps UKM tanpa website -> Buat website baru high-performance (PageSpeed 95+) -> Deploy Vercel -> Outreach WA/Email.
   - Jalur B (Modernisasi): Scrape website usang (WordPress/Blogger lama) -> Audit teknis SEO & Core Web Vitals -> Rekayasa ulang kode bersih -> Deploy Vercel -> Proposal PDF -> Outreach WA/Email.
2. Payment Gateway: Midtrans Snap API ($100 USD flat dikonversi live ke IDR, mendukung QRIS, Virtual Account BCA/Mandiri/BRI/BNI, Credit Card, dan webhook auto-settlement dengan verifikasi SHA-512).
3. Agency Landing Page: folder `agency_website/` (HTML/CSS/JS murni ultra-ringan, WebGPU background shader, zero heavy libraries, deployed di Vercel).

Aturan Pengembangan (Engineering Standards):
1. LIGHTWEIGHT & ZERO BLOAT: Jangan pernah menambahkan library atau bundle berat jika bisa diselesaikan dengan Vanilla Python / Vanilla JS.
2. STATE PERSISTENCE: Semua sesi (WhatsApp, Vercel token, invoice history, tracker) harus tersimpan lokal dan tidak boleh hilang saat program dihentikan.
3. ANTI-BOT & STEALTH: Scraping harus menggunakan browser stealth mode (Playwright/Scrapling) dengan random delay agar tidak terkena blokir atau CAPTCHA.
4. MOBILE-FIRST: Setiap website yang dihasilkan wajib 100% responsif tanpa horizontal overflow pada resolusi 320px hingga 1440px.

Fokus Pekerjaan Anda:
[TULISKAN TUGAS SPESIFIK ANDA DI SINI, contoh:
- Optimalkan modul crawler scanner agar dapat mengekstrak media sosial Instagram/TikTok bisnis secara otomatis.
- Tambahkan integrasi Midtrans Snap Popup JS langsung di landing page agency.
- Perbaiki kecepatan render proposal PDF dengan caching template.]
```

---

## 🚀 2. Panduan Lengkap Cara Menjalankan Pipeline (Execution Guide)

### Persiapan Awal (Prerequisites)
Pastikan Python 3.10+ sudah terpasang, lalu pastikan dependensi siap:
```powershell
# 1. Install dependensi
pip install playwright requests
playwright install chromium
```

Pastikan file `.env` sudah terisi minimal:
```env
# Email Outreach (Gunakan Google App Password 16-digit)
OUTREACH_EMAIL_HOST=smtp.gmail.com
OUTREACH_EMAIL_PORT=587
OUTREACH_EMAIL_USER=emailanda@gmail.com
OUTREACH_EMAIL_PASSWORD=xxxx xxxx xxxx xxxx
OUTREACH_SENDER_NAME=Studio Modernisasi Web
OUTREACH_SENDER_WA=+62 851-xxxx-xxxx

# Token Vercel (dari vercel.com/account/tokens)
VERCEL_TOKEN=vcp_xxxxxxxxxxxxxxxxxxxx

# Midtrans (Opsional untuk testing, ambil di dashboard.midtrans.com)
MIDTRANS_SERVER_KEY=SB-Mid-server-xxxx
MIDTRANS_CLIENT_KEY=SB-Mid-client-xxxx
MIDTRANS_IS_PRODUCTION=false
```

---

### Alur Kerja 1: Menjalankan Local Command Center (Dashboard Web)
Dashboard web lokal menyediakan tampilan visual seluruh prospek, status pipeline, tombol kirim pesan 1-klik, dan simulator pembayaran Midtrans:
```powershell
python auto_outreach.py --dashboard
```
Buka browser di: **`http://localhost:8080`**

Fitur dashboard:
- Memantau semua klien yang sudah di-scan / di-audit.
- Melihat tautan live demo Vercel dan file proposal PDF.
- Tombol 1-klik buat invoice Midtrans Snap resmi.
- Webhook receiver di `http://localhost:8080/api/payment-webhook`.

---

### Alur Kerja 2: Berburu Klien Baru dari Google Maps (Jalur A & B)
Mencari bisnis lokal di kota tertentu yang belum memiliki website atau memiliki website lama:
```powershell
# Contoh 1: Cari bengkel mobil di Jakarta
python auto_outreach.py --scan-gmaps "bengkel mobil jakarta" --max-leads 10

# Contoh 2: Cari klinik kecantikan di Surabaya
python auto_outreach.py --scan-gmaps "klinik kecantikan surabaya" --max-leads 10

# Contoh 3: Cari jasa ekspedisi atau katering
python auto_outreach.py --scan-gmaps "catering bandung" --max-leads 5
```
Output:
- Prospek tersimpan otomatis ke `clients/outreach_history.json`.
- Nomor WhatsApp dan data kontak otomatis diperkaya (*enriched*).

---

### Alur Kerja 3: Otomatisasi Rekayasa Ulang & Deploy Demo (Auto-Modernize)
Membangun website demo untuk semua prospek yang ada di antrean, menguploadnya langsung ke cloud Vercel, dan membuatkan proposal PDF:
```powershell
python auto_outreach.py --auto-modernize
```
Hasil yang didapatkan:
- Website modern live di `https://[nama-bisnis].vercel.app`.
- Skor Google PageSpeed 95+ (Desktop & Mobile).
- File proposal PDF 4 halaman siap kirim di `clients/[nama_bisnis]/client_proposal.pdf`.

---

### Alur Kerja 4: Memproses 1 Website Klien Tertentu Secara Mandiri
Jika Anda sudah memiliki URL website klien tertentu dan ingin langsung memprosesnya secara instan:
```powershell
python run_pipeline.py --url https://bisnisklien.com --output clients/bisnisklien
```
Tahapan yang otomatis berjalan:
1. `Scraper`: Mengambil konten teks, logo, dan aset asli.
2. `Style Analyzer`: Menganalisis palet warna dan identitas visual.
3. `Auditor`: Audit teknis Google Core Web Vitals & SEO.
4. `Quotation`: Menghitung kurs live Rupiah untuk paket $100 USD.
5. `Site Generator`: Menghasilkan website modern berstandar Google SEO.
6. `PDF Generator`: Mengompilasi dokumen proposal eksekutif 4 halaman A4.
7. `Packager`: Mengemas kode menjadi arsip ZIP siap serah-terima.

---

### Alur Kerja 5: Setup & Pengiriman Pesan Otomatis (Outreach)

#### A. Setup Sesi WhatsApp (Hanya 1 Kali):
```powershell
python auto_outreach.py --setup-wa
```
- Jendela browser Edge akan terbuka menampilkan QR code WhatsApp Web.
- Scan QR menggunakan WhatsApp di smartphone Anda.
- Sesi login akan tersimpan **permanen** di `clients/.whatsapp_session/`. Anda tidak perlu scan lagi selamanya.

#### B. Mengirim Penawaran WhatsApp Otomatis:
```powershell
# Mode Kirim Sungguhan
python auto_outreach.py --send-wa

# Mode Simulasi (Dry Run - tanpa kirim chat sungguhan)
python auto_outreach.py --send-wa --dry-run
```

#### C. Mengirim Penawaran Email Otomatis:
```powershell
python auto_outreach.py --send-email
```

---

### Alur Kerja 6: Mengetes Pembuatan Invoice Midtrans Snap
Anda dapat memverifikasi modul pembayaran Midtrans langsung lewat Python terminal:
```powershell
python -c "
from pipeline.payment.payment_gateway import PaymentGateway
pg = PaymentGateway()
inv = pg.create_invoice('toko-anda.com', 'Toko Anda', '08123456789')
print('Invoice ID  :', inv['invoice_id'])
print('Nominal     :', inv['price_display'])
print('Payment URL :', inv['payment_url'])
"
```

---

## 🔍 3. Rencana Penyempurnaan Pipeline (Next Roadmap Recommendations)

Untuk meningkatkan efektivitas pipeline ke tahap berikutnya:

1. **Midtrans Embedded Snap Popup di Website Agency**:
   - Menambahkan event listener pada tombol "Klaim Jadwal Pengerjaan Sekarang" di [agency_website/index.html](file:///c:/Users/USER/Downloads/Websiteupdater/agency_website/index.html) yang langsung memanggil `snap.pay(snapToken)` ketika klien ingin membayar langsung secara mandiri di web.
2. **Multi-Region Local Business Keywords**:
   - Membuat batch script untuk men-scan 10 kota besar sekaligus di Indonesia (Jakarta, Surabaya, Bandung, Medan, Semarang, Makassar, Bali, Yogyakarta, Palembang, Balikpapan) dengan berbagai kategori UKM berdaya beli tinggi (klinik gigi, kontraktor interior, konsultan hukum, ekspedisi logistik, supplier industri).
3. **AI Follow-up Auto-Responder**:
   - Menghubungkan WhatsApp session dengan LLM prompt khusus untuk membalas pertanyaan umum klien seperti: *"Berapa lama pengerjaannya?", "Apakah bisa pakai domain .co.id milik saya sendiri?", "Bagaimana cara bayarnya?"*.
