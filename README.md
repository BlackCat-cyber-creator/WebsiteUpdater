# 🚀 Website Updater Studio — Autonomous Web Agency Pipeline

> **Mesin Otomasi Rekayasa Web & Outreach B2B End-to-End untuk UKM Indonesia dengan Model Turn-Key Flat $100 USD (Kurs Live IDR), Integrasi Midtrans Snap Gateway, & Deployer Otomatis Vercel.**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Playwright](https://img.shields.io/badge/Browser-Playwright%20Stealth-2EAD33?logo=playwright)](https://playwright.dev/)
[![Midtrans Verified](https://img.shields.io/badge/Payment-Midtrans%20Snap-008ABF?logo=mastercard)](https://midtrans.com/)
[![Vercel Edge](https://img.shields.io/badge/Cloud-Vercel%20Edge%20Hosting-black?logo=vercel)](https://vercel.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Website Updater Studio adalah platform otomatisasi agensi rekayasa web yang dirancang khusus untuk memodernisasi kehadiran digital bisnis dan UKM di Indonesia. Sistem ini mengombinasikan *stealth web crawling*, analisis performa Google Core Web Vitals, generator website *mobile-first*, auto-deployment cloud Vercel, pembuatan invoice resmi Midtrans berlisensi Bank Indonesia, dan pengiriman proposal penawaran via WhatsApp & Email tanpa menyentuh akun pribadi Anda.

---

## 🌐 1. Website Agency Resmi (`agency_website/`)

Sistem ini dilengkapi landing page agensi produksi berstandar *Swiss Minimalist* dan performa tinggi di folder `agency_website/`:
- **Live URL**: [https://websiteupdater.vercel.app](https://websiteupdater.vercel.app)
- **Desain & Arsitektur Visual**:
  - Background shader ambient dinamis berbasis **WebGPU WGSL** dengan fallback Canvas 2D (< 4KB script weight).
  - 3D Gyroscope & Cursor Parallax Terminal interaktif yang menampilkan metrik *Google PageSpeed 99/100* dan kecepatan *0.48s LCP*.
  - Kalkulator konversi kurs $100 USD &rarr; Rupiah secara *real-time*.
  - 100% responsif dan teruji bebas *horizontal overflow* pada seluruh resolusi layar (320px, 360px, 375px, 768px, 1024px, 1440px).
  - Halaman legal & kepatuhan resmi: [Terms](/terms), [Privacy](/privacy), [Refund](/refund), dan [Delivery](/delivery).

---

## 🎯 2. Dua Jalur Operasi Utama (Dual-Track Model)

Sistem membedakan prospek bisnis menjadi dua jalur operasional yang jelas:

```
                              [ PROSPEK UKM INDONESIA ]
                                          │
                  ┌───────────────────────┴───────────────────────┐
                  ▼                                               ▼
      [ JALUR A: BISNIS TANPA WEB ]                   [ JALUR B: WEB LAMA / USANG ]
   - Terdaftar di Google Maps                    - Memiliki website lama
   - Belum memiliki website resmi                - Lambat / tidak mobile-friendly
   - Dibuatkan landing page baru                 - Direkayasa ulang total (PageSpeed 95+)
   - Vercel cloud hosting instan                 - Proposal PDF 4 Halaman dikirim via WA
   - $100 Flat Turn-Key                          - $100 Flat Turn-Key
```

### Jalur A: Pembuatan Website Baru dari Nol
- **Target**: Bisnis menengah yang memiliki Google Business Profile / Google Maps dengan banyak ulasan positif namun belum memiliki website resmi.
- **Solusi**: Membangun landing page baru dengan desain elegan, mobile-first, integrasi Google Search Console, dan hosting cloud gratis selamanya di Vercel.

### Jalur B: Rekayasa Ulang & Modernisasi Website Usang
- **Target**: Bisnis yang website-nya lambat, dibangun dengan template lama (WordPress/Blogger/Custom lawas), atau rusak di layar smartphone.
- **Solusi**: Mengikis (*scrape*) seluruh konten asli tanpa merusak identitas brand, mengoptimalkan skor Google PageSpeed dari merah ke hijau (95+), mengompilasi gambar modern WebP/AVIF, dan melampirkan dokumen proposal audit eksekutif PDF 4 halaman.

---

## 💳 3. Gerbang Pembayaran Resmi Midtrans ($100 Turn-Key)

Sistem terintegrasi langsung dengan API Midtrans Snap ([pipeline/payment/payment_gateway.py](pipeline/payment/payment_gateway.py)):
- **Kalkulasi Kurs Live**: Otomatis mengonversi biaya flat $100 USD menjadi Rupiah dengan pembulatan ribuan (contoh: Rp 1.766.000).
- **Metode Pembayaran**:
  - **QRIS**: GoPay, OVO, DANA, ShopeePay, LinkAja, BCA Mobile QR.
  - **Virtual Account Bank**: BCA, Mandiri, BRI, BNI, Permata.
  - **Kartu Kredit / Debit**: Standar keamanan PCI-DSS Level 1 & 3D Secure.
- **Webhook & Auto-Fulfillment**: Endpoint `/api/payment-webhook` memverifikasi signature SHA-512 resmi. Saat pembayaran berstatus `settlement`, invoice otomatis ditandai `PAID` dan bot WhatsApp langsung mengirimkan berkas/tautan serah terima kepada klien.

---

## 📂 4. Struktur Direktori Proyek

```
Websiteupdater/
├── .env                              # Kredensial rahasia (SMTP Email, WhatsApp, Vercel, Midtrans)
├── .env.example                      # Template variabel lingkungan
├── auto_outreach.py                  # CLI Runner Utama (Harvesting, Outreach, Dashboard)
├── run_pipeline.py                   # Pipeline Runner untuk 1 URL Spesifik
├── PROMPT_REFINE_PIPELINE.md         # Master Prompt AI Agent & Panduan Eksekusi Lengkap
├── README.md                         # Dokumentasi Lengkap Proyek
├── agency_website/                   # Source Code Website Agency Resmi (Vercel Ready)
│   ├── index.html                    # Landing Page Utama (WebGPU + 3D Parallax Terminal)
│   ├── terms.html                    # Syarat & Ketentuan Layanan
│   ├── privacy.html                  # Kebijakan Privasi Data & Midtrans
│   ├── refund.html                   # Kebijakan Garansi 60 Hari & Refund
│   ├── delivery.html                 # Kebijakan Serah Terima Digital
│   └── vercel.json                   # Konfigurasi Routing & Clean URLs Vercel
├── pipeline/                         # Mesin Pemroses Inti
│   ├── scanner/                      # Harvester Google Maps & Pengaya Kontak (Enricher)
│   ├── scraper.py                    # Scraper adaptif konten & aset asli (Scrapling)
│   ├── auditor.py                    # Auditor teknis Google PageSpeed & SEO
│   ├── style_analyzer.py             # Analisis identitas warna, font, dan elemen visual
│   ├── quotation.py                  # Mesin kurs real-time USD ke IDR
│   ├── site_generator.py             # Generator website modern Jalur A & Jalur B
│   ├── pdf_generator.py              # Generator proposal eksekutif PDF 4 halaman
│   ├── deployer/                     # Auto-deployer instan ke Vercel Cloud
│   ├── delivery/                     # Packaging source code ZIP & panduan cPanel
│   ├── payment/                      # Gateway pembayaran Midtrans Snap & Webhook
│   └── outreach/                     # Modul pengirim WhatsApp, Email, & Dashboard Web
└── clients/                          # Direktori Penyimpanan Data & Deliverables
    ├── .whatsapp_session/            # Sesi login browser WhatsApp (Tersimpan Permanen)
    ├── invoices.json                 # Database status invoice Midtrans
    ├── outreach_history.json         # Database prospek & riwayat interaksi
    └── {client_slug}/                # Berkas deliverable masing-masing klien
```

---

## ⚡ 5. Panduan Perintah Cepat (Quickstart Commands)

### 1. Buka Dasbor Web Lokal (Command Center):
```powershell
python auto_outreach.py --dashboard
```
Buka browser di `http://localhost:8080` untuk melihat antrean klien, pratinjau live demo, status pembayaran, dan tombol aksi 1-klik.

### 2. Berburu Prospek UKM dari Google Maps:
```powershell
# Mencari bisnis lokal yang belum punya website atau websitenya usang:
python auto_outreach.py --scan-gmaps "bengkel mobil jakarta barat" --max-leads 10
python auto_outreach.py --scan-gmaps "klinik gigi surabaya" --max-leads 5
```

### 3. Otomatisasi Bangun Website & Deploy Demo ke Vercel:
```powershell
python auto_outreach.py --auto-modernize
```

### 4. Memproses 1 Website Tertentu Secara Cepat:
```powershell
python run_pipeline.py --url https://bisnisklien.com --output clients/bisnisklien
```

### 5. Setup & Pengiriman Pesan Penawaran (Outreach):
```powershell
# Setup WhatsApp Web (Hanya perlu scan QR sekali saja):
python auto_outreach.py --setup-wa

# Kirim pesan penawaran otomatis via WhatsApp:
python auto_outreach.py --send-wa

# Kirim pesan penawaran via Email:
python auto_outreach.py --send-email
```

---

## 🤖 6. Panduan Menyempurnakan Pipeline (AI Refinement)

Untuk panduan menyempurnakan kode, menambahkan fitur baru dengan AI Agent, atau troubleshooting mendalam, silakan rujuk dokumen:
👉 **[PROMPT_REFINE_PIPELINE.md](PROMPT_REFINE_PIPELINE.md)**

---

## 🔒 7. Keamanan & Persistensi Data (State Persistence)

- **Sesi WhatsApp**: Disimpan dalam folder `clients/.whatsapp_session/` menggunakan profil Microsoft Edge terisolasi. Setelah login sekali, Anda tidak perlu scan QR lagi selamanya.
- **Kredensial Sensitif**: Seluruh API Key (Vercel, Midtrans, Email SMTP) berada di file lokal `.env` dan tidak pernah masuk ke git commit (`.gitignore`).
- **Pencegahan Spam**: Log `clients/outreach_history.json` mencatat setiap nomor kontak dan domain untuk mencegah pengiriman pesan ganda.

---

## 👨‍💻 Tim Pengembang
*Website Updater Studio — High-Performance Web Engineering, Mobile-First Modernization & Local SEO Dominance.*
