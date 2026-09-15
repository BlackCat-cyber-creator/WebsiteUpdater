# Website Updater Studio ($100 Turn-Key Engine)

> **Autonomous Indonesian SME Modernization & Technical SEO Outreach Engine**  
> Discovers high-potential local Indonesian businesses on Google Maps, generates modern high-converting websites, deploys live previews to Vercel, generates executive PDF proposals, and handles client engagement & Midtrans settlements.

---

## Architecture Overview

```
[Google Maps Scanner] -> [Business Researcher (Gemini AI)]
                               |
            +------------------+------------------+
            |                                     |
    [Track A: Web Baru]                  [Track B: Modernisasi]
(Bisnis tanpa website resmi)           (Audit SEO website lama)
            |                                     |
            +------------------+------------------+
                               |
          [Jinja2 Template Engine (pipeline/templates)]
            |                                     |
   (site/turnkey.html)                  (pdf/proposal_*.html)
            |                                     |
   [Vercel Cloud Deploy]                 [Executive PDF Pitch]
            |                                     |
            +------------------+------------------+
                               |
                    [Review Dashboard Server]
                               |
                   [WhatsApp & Email Dispatch]
```

### Key Components
- **`auto_outreach.py`**: CLI orchestrator for lead harvesting, modernization, review dashboard, and outreach dispatch.
- **`pipeline/scanner/google_maps_scanner.py`**: Local Indonesian SME harvester with:
  - **Brand Sanitizer (`clean_business_brand_name`)**: Strips parenthetical noise e.g. `(Part of ...)` / `(Cabang ...)`, normalizes ALL CAPS to Title Case, and protects Indonesian legal acronyms (`PT`, `CV`, `UD`, `TB`, `PD`).
  - **Phantom Lead Shield (`EXCLUDED_MAPS_DOMAINS`)**: Intercepts `wa.me`, `linktr.ee`, and bio links, extracts the direct mobile phone number, clears website URL, and routes accurately to **Track A (Web Baru)**.
- **`pipeline/deployer/vercel_deployer.py`**: Automated Vercel cloud deployer with brand-first concise slugification (`clean_slug`).
- **`pipeline/templates/`**: Centralized Jinja2 template repository for:
  - `site/turnkey.html`: Modern responsive client website template.
  - `pdf/proposal_track_a.html`: 4-page executive proposal for businesses without a website.
  - `pdf/proposal_track_b.html`: Executive technical SEO audit proposal for website modernizations.
- **`pipeline/outreach/message_formatter.py`**: High-Status Minimalist copywriting engine (cold outreach psychology, zero false flattery, directing prospect to Page 3 of attached PDF).
- **`pipeline/outreach/whatsapp_dispatcher.py`**: WhatsApp Web Playwright dispatcher with persistent session (`clients/.whatsapp_session`), instant non-WA number detection, and Meta cooldown handling.
- **`pipeline/db/database.py`**: Thread-safe SQLite persistence layer (`pipeline.db`) with WAL mode, tracking lead statuses and invoices.
- **`pipeline/outreach/dashboard_server.py`**: Dynamic, real-time review dashboard server with no-cache headers, token security, and 1-click approvals.

---

## Getting Started (Local Development)

### 1. Prerequisites
- Python 3.10+
- Microsoft Edge or Google Chrome (for local PDF printing & WhatsApp Web)

### 2. Installation
```bash
# Clone and enter directory
cd Websiteupdater

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browser binaries
playwright install chromium
```

### 3. Environment Variables
Copy `.env.example` to `.env` and fill in your API keys:
```bash
cp .env.example .env
```
Key variables:
- `GEMINI_API_KEY`: For business profiling, copywriting, and SEO audit generation.
- `VERCEL_TOKEN`: For automated live demo deployment.
- `MIDTRANS_SERVER_KEY`: For $100 live-rate invoice generation.
- `DASHBOARD_TOKEN`: Secret token for securing the review dashboard.
- `WA_PROVIDER`: Set to `meta` for Official Meta WhatsApp Cloud API (or `playwright` for old browser mode).
- `META_WHATSAPP_TOKEN`: Permanent System User Access Token dari Meta Business Manager.
- `META_PHONE_NUMBER_ID`: Phone Number ID dari Meta App dashboard.
- `META_WEBHOOK_VERIFY_TOKEN`: Token rahasia verifikasi webhook (default: `website_updater_verify_token`).

### Panduan Singkat Setup Meta WhatsApp Cloud API (Jalur 2 Official)
1. Buka [Meta for Developers](https://developers.facebook.com/) dan buat App bertipe **Other > Business**.
2. Di dashboard App, tambahkan produk **WhatsApp** lalu klik **API Setup**.
3. Anda akan langsung mendapatkan:
   - **Temporary Access Token** (atau buat permanent token via *Business Settings > System Users*).
   - **Phone Number ID** (salin ke `META_PHONE_NUMBER_ID`).
4. Di bagian **Configuration > Webhook**:
   - Masukkan Callback URL: `https://domain-anda.com/api/wa/webhook` (atau URL Ngrok untuk testing lokal).
   - Masukkan Verify Token: `website_updater_verify_token` (sama dengan `META_WEBHOOK_VERIFY_TOKEN` di `.env`).
   - Subscribe ke event field: **`messages`**.
5. Selesai! Pesan outreach akan dikirim secara instan lewat server resmi Meta tanpa membuka browser sama sekali.

### 4. Running the Pipeline
```bash
# 1. Setup dedicated WhatsApp account (one-time QR scan):
python auto_outreach.py --setup-wa

# 2. Search & harvest SME leads from Google Maps (10 to 1,000 reviews & mobile HP):
python auto_outreach.py --maps "toko bahan bangunan balikpapan" --limit 3

# 3. Batch modernize leads in queue (generate websites, Vercel deploys, PDF proposals, ZIP packages):
python auto_outreach.py --auto-modernize

# 4. Launch dynamic review dashboard server (Laptop: http://localhost:8080 & HP LAN sync):
python auto_outreach.py --dashboard
```

---

## 24/7 Cloud Deployment (Docker & VPS)

To run continuously and autonomously on a Linux VPS (Ubuntu 22.04+):

```bash
# Build and run containers
docker compose up -d updater-dashboard

# Check logs
docker compose logs -f updater-dashboard
```
*Note: The official Playwright Docker base image (`mcr.microsoft.com/playwright/python:v1.40.0-jammy`) packages all required Linux GUI & audio libraries out of the box, eliminating headless browser dependency issues.*

---

## 🚀 ROADMAP & NEXT PLANS (Prioritas Utama)

Berdasarkan evaluasi operasional lapangan dan umpan balik sistem, berikut adalah ringkasan peningkatan strategis yang telah dan sedang diimplementasikan:

### 1. Kualitas Output & Error Prevention (Human-in-the-Loop Workflow)

> **Catatan Operasional:** Desain visual website dibangun berstandar tinggi menggunakan intelligence **`ui-ux-pro-max`**. Sistem beroperasi dengan model **Human-in-the-Loop**:
> 1. AI & Scanner otomatis melakukan pencarian leads, ekstraksi kontak, pembuatan website Swiss Minimalist, dan proposal PDF.
> 2. Hasilnya masuk ke **Review Dashboard (`auto_outreach.py --dashboard`)**.
> 3. Pengguna melakukan review visual cepat, lalu klik **✓ Centang** untuk mengirim via Playwright/Meta API, atau klik **📱 Buka Chat di HP / Web** untuk mengirim langsung lewat aplikasi WhatsApp di smartphone.

**Checklist Integrasi & Audit Error:**
- [x] **UI/UX Pro Max Intelligence:** Terintegrasi di `gemini_synthesizer.py` (blacklist klise, 6 item spesifik, persona ulasan realistis) dan `niche_themes.json` (palet warna psikologi industri).
- [x] **Brand Cleaning & Sanitization Engine:** Membersihkan teks kurung/cabang `(Part of ...)` / `(Cabang ...)` / `(Pusat)` dan mengubah huruf kapital teriak (ALL CAPS) menjadi Title Case elegan dengan perlindungan akronim hukum (`PT`, `CV`, `UD`, `TB`, `PD`, dll.) via `clean_business_brand_name()`.
- [x] **Phantom Lead Shield & Exclusion Filter:** Menghentikan phantom lead seperti *"Share on WhatsApp"* dengan memfilter link WhatsApp (`wa.me`, `whatsapp.com`) dan bio link (`linktr.ee`, `bit.ly`, dll.) dari kolom website Google Maps, mengekstrak nomor HP langsung, dan menetapkannya secara akurat ke **Jalur A (Web Baru)**.
- [x] **Copywriting Psikologi Penjualan (High-Status Minimalist & PDF-First):** Menghapus false flattery murahan, menerapkan peer-to-peer cold calling psychology, dan menempatkan link demo serta QR code smartphone eksklusif di **Halaman 3 PDF Proposal**, bukan di teks chat mentah (mencegah spam flag dan meningkatkan perceived value).
- [x] **Deteksi Cepat Nomor Non-WhatsApp:** Otomatis mendeteksi popup dialog nomor tidak terdaftar di WhatsApp dalam 1 detik, menutup popup secara aman, dan menandai status sebagai `invalid_phone` (`Bukan Nomor WA ✕`).
- [x] **Dynamic Review Dashboard & Anti-Caching:** Dashboard memuat data segar langsung dari SQLite (`pipeline.db`) pada setiap request tanpa caching statis, dengan integrasi token auth yang aman pada aksi `Discard` dan `Approve`.
- [x] **Kalimantan SME Harvester:** Modul pencarian regional khusus UKM berkembang di Kalimantan (Balikpapan, Samarinda, Pontianak, Banjarmasin, Palangka Raya) dengan filter ulasan sweet spot 10–1.000 review.
- [x] **Perbaikan Bug `site_generator.py` & Header `turnkey.html`:** Menghilangkan potensi `NameError` dan menutup blok komentar ASCII.

---

### 2. Realita Anti-Ban WhatsApp: Apakah Benar-Benar Bisa Anti-Ban?

> **Pertanyaan Kritis:** *Apakah WhatsApp benar-benar bisa 100% Anti-Ban jika menggunakan script otomasi?*

**Fakta Nyata Keamanan WhatsApp:**
1. **Mitos "Script Anti-Ban":** Tidak ada otomasi browser (Playwright/Selenium) yang 100% anti-ban. WhatsApp (Meta) memiliki AI pendeteksi spam yang menganalisis bukan hanya browser, tetapi **pola interaksi manusia**.
2. **Pemicu Utama Banned Bukan Kode, Tapi Manusia:**
   Sekitar **80-90% banned terjadi karena penerima menekan tombol "Laporkan & Blokir" (Report Spam)**. Jika kita mengirim link proposal dan dokumen PDF panjang secara tiba-tiba ke nomor yang belum menyimpan kontak kita, penerima akan menganggapnya spam mencurigakan.

**Strategi Nyata yang Terbukti Bertahan:**
- [ ] **Two-Step Permission Outreach (Sangat Krusial):**
  - **Pesan 1:** Hanya sapaan ramah dan meminta izin (tanpa link / tanpa lampiran):
    > *"Selamat siang Pak/Bu [Nama Usaha]. Salam kenal, saya dari tim Web Studio. Kami sedang meninjau kehadiran digital bisnis di [Kota], apakah ini nomor resmi manajemen yang bisa kami hubungi?"*
  - **Pesan 2:** Link demo Vercel dan PDF **hanya dikirim jika mereka membalas**. Begitu ada balasan dua arah, WhatsApp menganggapnya percakapan valid antar-manusia (resiko banned turun drastis).
- [ ] **Batas Volume Harian:** Maksimal 15–20 kontak baru per hari per nomor WhatsApp.
- [ ] **Human Keystroke Simulation:** Mengetik dengan delay acak 40–110ms per karakter dan jeda 60–180 detik antar nomor.

---

### 3. Evaluasi & Riset Alternatif Playwright (Arsitektur Lebih Ringan & Tahan Banting)

Playwright saat ini digunakan untuk 3 fungsi berbeda. Berikut hasil riset dan opsi alternatif yang jauh lebih efisien:

| Fungsi | Playwright Saat Ini | Alternatif Terbaik | Keunggulan Alternatif |
| :--- | :--- | :--- | :--- |
| **WhatsApp Outreach** | Playwright Chromium (Berat, rawan ban) | **1. Official WhatsApp Cloud API**<br>**2. Baileys / Evolution API** | **Resiko ban 0% (Official API)**, tanpa browser, konsumsi RAM hemat (~30MB vs 500MB), webhook instan untuk respon cepat. |
| **Generate Proposal PDF** | Playwright Headless PDF | **1. Direct Chrome CLI (`--print-to-pdf`)**<br>**2. WeasyPrint**<br>**3. Gotenberg Container** | Sudah ada fallback direct CLI bawaan. WeasyPrint atau Gotenberg tidak membutuhkan runtime Python Playwright sama sekali. |
| **Harvest Leads Google Maps** | Playwright Browser Scrape | **1. Google Places API (New)**<br>**2. Scrapling / curl_cffi** | Eksekusi JSON instan dalam hitungan milidetik, tanpa overhead memuat elemen UI Google Maps. |

#### Rekomendasi Roadmap WhatsApp:
1. **Opsi Teraman (100% Anti-Ban): Meta Official WhatsApp Cloud API**
   - Menggunakan API resmi Meta Graph API (`POST https://graph.facebook.com/...`).
   - Gratis 1.000 percakapan pertama per bulan.
   - Tidak memerlukan server browser sama sekali.
2. **Opsi Self-Hosted (Tanpa Browser): Evolution API (Baileys Engine)**
   - Microservice Docker berbasis Node.js yang berkomunikasi langsung via protokol WebSocket multi-device WhatsApp (bukan otomasi browser UI).
   - Menyediakan REST API lokal (`http://localhost:8080/message/sendText`) yang dapat dipanggil langsung oleh Python.

---

## Menjalankan Pengujian (Testing)

Proyek ini dilengkapi dengan rangkaian automated unit & integration test untuk memastikan stabilitas:

```bash
# Menjalankan seluruh test suite
python -m pytest

# Menjalankan test modul tertentu
python -m pytest tests/test_pdf.py
python -m pytest tests/test_templates.py
python -m pytest tests/test_database.py
```

---

## Lisensi & Hak Milik
Hak Cipta © 2026 Website Updater Studio. Seluruh hak cipta dilindungi undang-undang.
