# Website Updater Studio

> **Autonomous Indonesian SME Modernization & Technical SEO Outreach Engine**
>
> *Mesin Otomatisasi Modernisasi UKM Indonesia & Mesin SEO Teknis*

---

## 🇺🇸 English Documentation

### Architecture Overview

Website Updater Studio is an end-to-end automation pipeline designed to discover, analyze, and modernize Indonesian SMEs (Small and Medium Enterprises) who are either lacking a digital presence or have outdated websites. It leverages AI and automation to generate modern, 2026-standard, high-converting websites optimized for local technical SEO.

```text
[Google Maps Scanner] -> [Business Researcher (Gemini AI)]
                               |
            +------------------+------------------+
            |                                     |
    [Track A: New Website]              [Track B: Modernization]
(Businesses without websites)        (SEO Audit for existing sites)
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

### Key Features & Standard 2026 Focus

- **Robust Orchestration Pipeline**: Uses asynchronous batch processing with robust error handling (`cmd_auto_modernize.py`) that forces the pipeline to continue even if a single lead fails.
- **2026 Standard Web Design**: Uses modern CSS variables, Aurora Mesh background glow, glassmorphism, responsive grid layouts, and mobile-first liquid architecture.
- **Micro-Animations & Effects**: Employs tactile micro-animations, scroll-reveal intersection observers, and intelligent image fallbacks for a premium user feel.
- **Technical SEO (Search Engine Optimization) Engine**:
  - Validates and generates Schema.org JSON-LD (LocalBusiness, Organization, PostalAddress, OfferCatalog).
  - Optimizes `og:title`, `og:image`, and semantic HTML (H1/H2 hierarchy).
  - Automatically manages canonical links and meta descriptions based on the client's commercial keywords to improve Google Knowledge Panel discovery.
- **AI-Powered Lead Generation**: Uses Playwright and Google Maps scraping to find 10–1000 review "sweet spot" businesses, then sanitizes the brand names and prevents phantom leads (wa.me, linktr.ee).
- **Executive PDF Pitch & Automated Deployments**: Instantly generates proposals using Jinja2 and pushes the customized site preview to Vercel.

### Getting Started (Local Development)

#### 1. Prerequisites
- Python 3.10+
- Microsoft Edge or Google Chrome (for local PDF printing & WhatsApp Web)

#### 2. Installation
```bash
# Clone and enter directory
git clone <repository_url>
cd Websiteupdater

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browser binaries
playwright install chromium
```

#### 3. Environment Variables
Copy `.env.example` to `.env` and fill in your API keys:
```bash
cp .env.example .env
```
Key variables:
- `GEMINI_API_KEY`: For business profiling and SEO audit generation.
- `VERCEL_TOKEN`: For automated live demo deployment.
- `MIDTRANS_SERVER_KEY`: For payment generation.

#### 4. Running the Pipeline
```bash
# 1. Search & harvest SME leads from Google Maps:
python auto_outreach.py --maps "toko bahan bangunan balikpapan" --limit 3

# 2. Batch modernize leads in queue (robust auto-retry on failure):
python auto_outreach.py --auto-modernize

# 3. Launch dynamic review dashboard server:
python auto_outreach.py --dashboard
```

---

## 🇮🇩 Dokumentasi Bahasa Indonesia

### Gambaran Arsitektur

Website Updater Studio adalah *pipeline* otomasi end-to-end yang dirancang untuk menemukan, menganalisis, dan memodernisasi Usaha Kecil dan Menengah (UKM) di Indonesia yang belum memiliki atau memiliki website yang sudah usang. Sistem ini memanfaatkan AI dan otomasi untuk menghasilkan website standar 2026 yang modern, berkonversi tinggi, serta optimal untuk *Technical SEO* lokal.

### Fitur Utama & Standar 2026

- **Pipeline Orkestrasi yang Tangguh (Robust)**: Menggunakan pemrosesan *batch* asinkron dengan penanganan *error* yang tangguh (`cmd_auto_modernize.py`) yang memaksa *pipeline* untuk terus berjalan bahkan jika ada satu prospek (lead) yang gagal diproses.
- **Desain Web Standar 2026**: Menggunakan variabel CSS modern, efek *Aurora Mesh background glow*, *glassmorphism*, tata letak *grid* responsif, dan arsitektur *liquid mobile-first*.
- **Mikro-Animasi & Efek Keren**: Menerapkan animasi sentuhan mikro, pemantauan gulir (scroll-reveal), dan fallback gambar cerdas untuk memberikan nuansa premium pada pengguna.
- **Mesin Optimasi SEO Teknis (Jual SEO)**:
  - Memvalidasi dan membuat data terstruktur Schema.org JSON-LD (LocalBusiness, Organization, PostalAddress, OfferCatalog).
  - Mengoptimalkan `og:title`, `og:image`, dan HTML semantik (hierarki H1/H2).
  - Secara otomatis mengelola tautan kanonikal (canonical) dan deskripsi meta berdasarkan kata kunci komersial klien untuk meningkatkan penemuan di Google Knowledge Panel.
- **Pencarian Prospek Berbasis AI**: Menggunakan Playwright dan scraping Google Maps untuk menemukan bisnis dengan jumlah ulasan 10–1000, lalu membersihkan nama *brand* dan mencegah kontak palsu (seperti tautan wa.me, linktr.ee).
- **Proposal PDF & Implementasi Otomatis**: Secara instan membuat proposal eksekutif menggunakan Jinja2 dan melakukan publikasi (deploy) pratinjau situs ke Vercel.

### Cara Memulai (Pengembangan Lokal)

#### 1. Persyaratan
- Python 3.10+
- Microsoft Edge atau Google Chrome (untuk pencetakan PDF lokal & WhatsApp Web)

#### 2. Instalasi
```bash
# Kloning dan masuk ke direktori
git clone <repository_url>
cd Websiteupdater

# Instalasi dependensi Python
pip install -r requirements.txt

# Instalasi browser Playwright
playwright install chromium
```

#### 3. Variabel Lingkungan (Environment Variables)
Salin `.env.example` ke `.env` dan isi kunci API Anda:
```bash
cp .env.example .env
```
Variabel kunci:
- `GEMINI_API_KEY`: Untuk pembuatan profil bisnis dan pembuatan audit SEO.
- `VERCEL_TOKEN`: Untuk publikasi (deploy) demo langsung otomatis.
- `MIDTRANS_SERVER_KEY`: Untuk pembuatan pembayaran.

#### 4. Menjalankan Pipeline
```bash
# 1. Cari & kumpulkan prospek UKM dari Google Maps:
python auto_outreach.py --maps "toko bahan bangunan balikpapan" --limit 3

# 2. Modernisasi antrean prospek secara massal (otomatis tangguh jika gagal):
python auto_outreach.py --auto-modernize

# 3. Luncurkan server dasbor peninjauan dinamis:
python auto_outreach.py --dashboard
```

---

## License / Lisensi
Copyright © 2026 Website Updater Studio. All rights reserved / Seluruh hak cipta dilindungi undang-undang.
