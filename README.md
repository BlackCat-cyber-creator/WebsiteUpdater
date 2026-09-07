# 🚀 Autonomous Web Engineering & SEO Optimization Pipeline

> **Sistem Otomasi Pengambilan Website Klien, Pelestarian Tema Asli 100%, Optimasi SEO Google Mendalam, Proposal Eksekutif PDF 4 Halaman, & Outreach WhatsApp/Email Terisolasi.**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Scrapling](https://img.shields.io/badge/Crawler-Scrapling-FF5722?logo=github)](https://github.com/D4Vinci/Scrapling)
[![OpenSEO](https://img.shields.io/badge/Audit-OpenSEO%20Engine-00C49F)](https://github.com/every-app/open-seo)
[![Playwright](https://img.shields.io/badge/Automation-Playwright-2EAD33?logo=playwright)](https://playwright.dev/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Pipeline rekayasa web otomatis (*end-to-end*) yang dirancang khusus untuk pasar bisnis di Indonesia. Sistem ini mengikis website klien secara langsung (*live scraping*), **mempertahankan 100% tema, warna, dan tata letak asli klien**, merapikan seluruh aset gambar/skrip agar tidak rusak, menginjeksi standar teknis Google SEO tingkat tinggi, menghasilkan proposal PDF eksekutif 4 halaman bernilai $100 flat (turn-key), dan menyiapkan antrean pesan WhatsApp/Email secara otomatis tanpa menyentuh akun pribadi Anda.

---

## 🎯 Prinsip Utama Sistem (Core Philosophy)

> **"Ambil semua website milik klien, jangan ubah tema/desain/warnanya sama sekali. Cukup rapikan asetnya dan maksimalkan teknis SEO-nya saja. Itu saja."**

1. **100% Preservasi Desain Asli Klien:**
   * Kami **TIDAK** mendesain ulang website klien menjadi tema gelap/SaaS generik.
   * Warna latar, header, logo asli, navigasi, form resi, tab pelacakan, marquee mitra, dan susunan konten tetap dipertahankan persis seperti aslinya.
2. **Rapikan (Asset & Media Tidying):**
   * Semua tautan relatif (`href`, `src`, `poster`, `srcset`) diubah otomatis menjadi URL absolut resmi (`urllib.parse.urljoin`).
   * Seluruh gambar, icon SVG, stylesheet CDN, font, dan script eksternal tetap ter-load utuh saat dibuka secara lokal maupun saat di-hosting online.
   * Gambar kosong diberikan atribut `alt` deskriptif untuk indeks Google Image.
3. **Baguskan SEO-nya (Technical Google SEO Injections):**
   * **Meta Viewport:** Memastikan halaman 100% responsif dan lolos uji *Mobile-Friendly* Google.
   * **Title & Meta Description:** Diformulasikan dengan rasio CTR tinggi dan kata kunci komersial terarah.
   * **Tag Canonical:** Mencegah penalti konten duplikat Google (`<link rel="canonical">`).
   * **OpenGraph & Twitter Card:** Tampilan pratinjau tautan (thumbnail & ringkasan) tampil elegan saat dibagikan ke WhatsApp dan media sosial.
   * **Schema.org Structured Data (JSON-LD):** Data mikro terverifikasi (`LocalBusiness` / `Organization`) dengan nama, alamat, nomor telepon, dan profil bisnis agar memicu *Knowledge Graph* dan *Rich Snippet* di hasil pencarian Google.
   * **Semantic H1 Hierarchy:** Memastikan crawler mesin pencari menemukan tepat 1 tag `<h1>` topik utama yang valid tanpa mengganggu tata letak visual.
   * **Robots.txt & Sitemap.xml:** Di-generate otomatis di dalam direktori `site/`.

---

## ❓ Pertanyaan Penting: "Jika Saya Tutup Proyek Ini Lalu Buka & Jalankan Lagi, Apa yang Terjadi?"

Semua sistem dalam pipeline ini dirancang dengan **State Persistence (Status Tersimpan Permanen)**. Anda dapat menutup VS Code, mematikan terminal, atau mematikan laptop kapan saja tanpa khawatir data hilang:

### 1. Sesi WhatsApp TETAP LOGIN (Tidak Perlu Scan QR Ulang)
* Sesi login akun WhatsApp khusus disimpan di folder `clients/.whatsapp_session/`.
* Data browser Microsoft Edge, cookies, dan token otentikasi WhatsApp tersimpan aman di disk lokal.
* Saat Anda membuka kembali proyek ini di hari berikutnya dan menjalankan pengiriman, **WhatsApp langsung terbuka dalam keadaan login tanpa perlu scan QR lagi**.

### 2. Kredensial Email TETAP AKTIF
* Alamat email pengirim (`websiteupdater888@gmail.com`) dan Google App Password tersimpan aman di file `.env`.
* Pengiriman email proposal via SMTP langsung siap digunakan kapan pun.

### 3. Seluruh File & Hasil Kerja Klien TETAP UTUH
* Di dalam folder `clients/` untuk setiap domain klien (contoh: `clients/sicepat_com/` atau `clients/sentralcargo_co_id/`), semua berkas tersimpan rapi:
  * `site/index.html`: Website asli klien yang sudah dirapikan & SEO-optimized.
  * `client_proposal.pdf`: Dokumen proposal eksekutif 4 halaman siap kirim.
  * `client_proposal.html`: Tampilan web proposal yang interaktif.
  * `scraped_data.json` & `audit_report.json`: Rekam audit teknis lengkap.
  * `*_Client_Package.zip`: Paket arsip ZIP mandiri.

### 4. Riwayat Outreach TERSIMPAN (Mencegah Duplikasi Pesan)
* File `clients/outreach_history.json` mencatat domain dan nomor WhatsApp mana saja yang sudah diproses atau dikirimi pesan.
* Pipeline tidak akan pernah mengirimkan pesan berulang ke klien yang sama.

### 5. Dasbor Antrean Langsung Siap Dipakai
* Anda cukup membuka file [`clients/outreach_queue.html`](file:///c:/Users/USER/Downloads/Websiteupdater/clients/outreach_queue.html) langsung di browser kapan pun untuk melihat prospek dan mengklik tombol WhatsApp 1-click.

---

## 🏗️ Alur Kerja 7-Tahap Pipeline

```
[ Target URL: https://client-domain.com ]
                      │
                      ▼
[Step 1: Scrapling Crawler] ──────> Unduh HTML asli, logo, kontak, navigasi (anti-bot stealth)
                      │
                      ▼
[Step 2: Style Analyzer]    ──────> Analisis identitas warna, font, dan elemen visual asli
                      │
                      ▼
[Step 3: OpenSEO Auditor]   ──────> Audit teknis SEO (Headings, Schema.org, NAP, Core Web Vitals)
                      │
                      ▼
[Step 4: Quotation Engine]  ──────> Penawaran flat $100 turn-key (kurs live USD ke IDR)
                      │
                      ▼
[Step 5: Site Generator]    ──────> Preservasi tema asli 100% + Resolusi link absolut + Injeksi SEO
                      │
                      ▼
[Step 6: PDF Generator]     ──────> Kompilasi proposal eksekutif 4 halaman A4 (Headless Edge/Chrome)
                      │
                      ▼
[Step 7: Client Packager]   ──────> Bungkus berkas deliverable ke arsip ZIP mandiri
```

---

---

## 🎯 Strategi Penargetan: Bisnis Menengah & Menengah ke Atas (The Golden Sweet Spot)

Sistem ini **TIDAK** menyasar perusahaan konglomerat raksasa nasional (seperti SiCepat, Sentral Cargo, JNE, Indofood, atau Bank BCA), melainkan secara spesifik dirancang untuk **Bisnis Menengah (Mid-Tier) dan Menengah ke Atas (Upper-Mid)** di Indonesia.

### Mengapa Bukan Raksasa Konglomerat?
1. **Birokrasi & Tender Berlapis:** Perusahaan raksasa mewajibkan proses e-procurement, tender vendor, legal compliance, dan persetujuan direksi berbulan-bulan.
2. **Tim IT Internal Raksasa:** Mereka telah memiliki divisi in-house developer dan SEO spesialis puluhan hingga ratusan orang.
3. **Nomor WhatsApp CS / Bot Ticketing:** Nomor kontak yang tertera di website mereka adalah CS keluhan barang/paket yang tidak memiliki otoritas pembelian atau wewenang membalas penawaran bisnis.
4. **Mismatched Pricing:** Penawaran jasa $100 flat tidak relevan untuk anggaran enterprise bernilai miliaran rupiah.

### Mengapa Bisnis Menengah & Menengah ke Atas adalah "Sweet Spot"?
1. **Akses Langsung ke Pengambil Keputusan (Decision Maker):** Nomor WhatsApp di website bisnis menengah biasanya dipegang langsung oleh **Owner / Founder, Direktur Operasional, atau Kepala Marketing**. Chat kita langsung dibaca oleh orang yang berhak memutuskan.
2. **Kebutuhan Nyata (Real Pain Point):** Website mereka umumnya dibangun 3–7 tahun lalu oleh freelancer atau vendor lama. Desainnya sudah mereka sukai (sehingga prinsip **100% Preservasi Desain Asli** sangat memikat bagi mereka), namun SEO teknikal dan optimasi mobilenya tertinggal jauh.
3. **Keputusan Cepat (Impulse Closing):** Biaya turn-key **$100 (~Rp 1,6 – 1,7 Juta all-in)** bagi pemilik bisnis menengah adalah angka yang sangat terjangkau (setara petty cash / biaya operasional ringan). Mereka bisa langsung menyetujui tanpa proses rapat yang bertele-tele.

### 5 Kategori Niche Paling Potensial & Perintah Eksekusinya:

| Kategori | Contoh Niche Bisnis Menengah | Perintah Otomasi |
| :--- | :--- | :--- |
| **`ekspedisi_spesialis`** | Ekspedisi rute khusus (Surabaya-Makassar, Jawa-Kalimantan), truk pendingin reefer, kargo tronton | `python auto_outreach.py --category ekspedisi_spesialis --limit 2` |
| **`b2b_distributor`** | Supplier bahan kimia industri, distributor packaging kardus box, distributor frozen food | `python auto_outreach.py --category b2b_distributor --limit 2` |
| **`kontraktor_komersial`** | Kontraktor interior kantor & showroom, kontraktor HVAC tata udara, epoxy lantai pabrik | `python auto_outreach.py --category kontraktor_komersial --limit 2` |
| **`manufaktur_menengah`** | Karoseri box pendingin/dump truck, pabrik plastik kemasan, konveksi seragam pabrik | `python auto_outreach.py --category manufaktur_menengah --limit 2` |
| **`klinik_spesialis`** | Klinik estetika kecantikan swasta, klinik gigi spesialis / dental care, laboratorium diagnostik | `python auto_outreach.py --category klinik_spesialis --limit 2` |

---

## ⚡ Panduan Menjalankan Perintah (Cheat-Sheet)

### 1. Menjalankan Scanning & Outreach Otomatis per Kategori
Pilih salah satu kategori bisnis menengah untuk menemukan prospek terkurasi dan membuat proposal otomatis:
```powershell
# Mode Simulasi Aman (Dry-Run):
python auto_outreach.py --category ekspedisi_spesialis --limit 2 --dry-run

# Atau dengan pencarian kata kunci spesifik:
python auto_outreach.py --query "supplier bahan kimia cikarang" --limit 2 --dry-run
```

### 2. Menjalankan Pipeline untuk Website Klien Tertentu
Jika Anda sudah memiliki nama domain target bisnis menengah:
```powershell
python run_pipeline.py --url https://karyapratamacargo.co.id --output clients/karyapratamacargo_co_id
```
*(Contoh lain: `https://suncargo.sunfrozencargo.com`)*

### 3. Membuka & Menguji Website Hasil Optimasi Secara Lokal
Anda dapat membuka file `index.html` langsung di browser, atau melalui web server lokal:
```powershell
python -m http.server 3000 --directory clients/karyapratamacargo_co_id/site
```
Lalu buka di browser: `http://localhost:3000`

### 4. Setup Akun WhatsApp Khusus (Cukup Sekali Saja)
Scan QR code menggunakan nomor WhatsApp khusus outreach:
```powershell
python auto_outreach.py --setup-wa
```
*(Setelah sukses, sesi tersimpan permanen di `clients/.whatsapp_session/`)*

### 5. Membuka Dasbor Antrean Interaktif (Centang / Discard)
Buka dasbor antrean bersih dengan tombol **✅ Centang** dan **❌ Discard**:
```powershell
python auto_outreach.py --dashboard
```
*Browser akan otomatis terbuka di `http://127.0.0.1:8080`. Di sana:*
* Klik **✅ Centang (Kirim WA & Email + PDF)**: Sistem langsung mengirimkan email via Gmail SMTP dan pesan WhatsApp via Edge Playwright, lengkap dengan **dokumen proposal PDF 4 halaman terlampir di kedua saluran**.
* Klik **❌ Discard**: Menghapus prospek dari antrean dan menandainya sebagai discarded.

### 6. Eksekusi Cepat via Terminal (CLI Approval)
Jika tidak ingin membuka browser, Anda juga bisa meng-approve atau discard langsung via terminal:
```powershell
# Kirim WA + Email + PDF ke domain tertentu:
python auto_outreach.py --approve karyapratamacargo.co.id

# Atau hapus prospek dari antrean:
python auto_outreach.py --discard karyapratamacargo.co.id
```

### 7. Menguji Kirim Proposal via Email
```powershell
python auto_outreach.py --test-email emailanda@gmail.com
```

---

## 📁 Struktur Direktori Proyek

```
Websiteupdater/
├── .env                              # Konfigurasi rahasia (Email SMTP, nomor WhatsApp, Vercel Token)
├── .env.example                      # Template konfigurasi environment
├── run_pipeline.py                   # Master Pipeline CLI Runner (7 Tahap)
├── auto_outreach.py                  # Master Outreach CLI Runner ($100 Turn-Key Dual-Track)
├── README.md                         # Dokumentasi Lengkap Sistem
├── pipeline/                         # Mesin Pemroses Utama
│   ├── scraper.py                    # Scraper adaptif live (Scrapling)
│   ├── style_analyzer.py             # Analisis warna & tipografi
│   ├── auditor.py                    # Auditor teknis Google SEO & UX dinamis
│   ├── quotation.py                  # Mesin penawaran $100 flat turn-key & kurs live
│   ├── site_generator.py             # Preservasi tema 100% & generator Swiss Minimalist (Jalur A)
│   ├── pdf_generator.py              # Generator proposal PDF eksekutif 4 halaman
│   ├── deployer/                     # Auto-Deployer Cloud
│   │   └── vercel_deployer.py        # Programmatic Vercel CLI & REST API deployer
│   ├── delivery/                     # Source Code Packaging & Panduan
│   │   └── code_packager.py          # Generator ZIP cPanel & Panduan SEO resmi
│   ├── payment/                      # Gateway Pembayaran Kurs Live
│   │   └── payment_gateway.py        # Generator Invoice $100 live-rate & VA / QRIS
│   ├── scanner/                      # Harvester Prospek
│   │   ├── google_maps_scanner.py    # Dual-Track Google Maps SME Harvester (5-1.000 review)
│   │   └── business_scanner.py       # Scanner domain & ekstraktor kontak
│   └── outreach/                     # Modul Pengiriman & Interaksi Terisolasi
│       ├── whatsapp_dispatcher.py    # Playwright WhatsApp dispatcher & reply listener
│       ├── dashboard_server.py       # Micro-server dasbor antrean & webhook payment
│       ├── email_dispatcher.py       # SMTP Gmail dispatcher
│       └── tracker.py                # Database status prospek & histori outreach
└── clients/                          # Arsip Deliverable Klien
    ├── .whatsapp_session/            # Sesi login WhatsApp terisolasi (cookies & token)
    ├── outreach_history.json         # Log riwayat outreach & status settlement
    ├── invoices.json                 # Log invoice resmi pembayaran $100 kurs live
    ├── outreach_queue.html           # Dasbor interaktif monokrom 1-Click WhatsApp
    └── {client_slug}/                # Folder deliverable masing-masing klien
        ├── site/                     # Website modern (HTML, CSS, Assets)
        ├── client_proposal.pdf       # Proposal eksekutif 4 halaman (Jalur B)
        ├── PANDUAN_PEMASANGAN_CPANEL.md # Panduan mandiri upload cPanel
        ├── SEO_CONFIGURATION_GUIDE.md   # Panduan Google Search Console
        └── *_Clean_Source_Code.zip   # Paket ZIP deliverable final
```

---

## ⚡ Perintah Cepat CLI ($100 Turn-Key Dual-Track)

```bash
# 1. Jalankan Dasbor Review Monokrom (Whitespace Minimalist):
python auto_outreach.py --dashboard

# 2. Cari prospek UKM dari Google Maps (Otomatis memisahkan Jalur A vs Jalur B):
python auto_outreach.py --maps "distributor bahan plastik surabaya" --limit 3 --dry-run

# 3. Dengarkan balasan chat WhatsApp & kirim demo/opsi secara otomatis:
python auto_outreach.py --listen-replies

# 4. Deploy website klien langsung ke Vercel secara terprogram:
python auto_outreach.py --deploy-vercel domain-klien.com

# 5. Bungkus source code bersih (.ZIP) lengkap dengan panduan cPanel & SEO:
python auto_outreach.py --package domain-klien.com

# 6. Buat invoice resmi $100 USD (kurs live otomatis) dengan Virtual Account:
python auto_outreach.py --create-invoice domain-klien.com

# 7. Uji coba simulasi webhook pembayaran lunas:
python auto_outreach.py --simulate-payment INV-XXXXXXXX-XXXX
```

---

## 🔒 Strategi Outreach WhatsApp yang Aman & Berkonversi Tinggi

Format pesan cold chat WhatsApp dipisahkan berdasarkan dua jalur operasional:

### Jalur A: Bisnis Tanpa Website
1. **Menyapa dan memuji reputasi Google Maps klien** ({rating_text} ulasan).
2. **Menyoroti pentingnya website resmi di pencarian Google** untuk meningkatkan konversi hingga 3x lipat.
3. **Mengajak interaksi ramah tanpa mengirimkan link terlebih dahulu** agar tidak terdeteksi spam.
4. **Auto-Trigger Balasan:** Begitu klien membalas chat apa pun, sistem otomatis men-deploy website modern ke Vercel dan mengirimkan link demo (`https://{slug}.vercel.app`) dengan penawaran $100 USD (kurs live).

### Jalur B: Bisnis yang Sudah Memiliki Website
1. **Menyapa dan menyampaikan URL website operasional klien** (`https://{domain}`).
2. **Menyampaikan temuan audit Google SEO teknis & kenyamanan smartphone**.
3. **Melampirkan dokumen proposal eksekutif PDF 4 halaman**.
4. **Auto-Trigger Balasan:** Saat klien membalas chat, sistem menawarkan 3 opsi fleksibel:
   - **Opsi 1:** Beli Source Code bersih (.ZIP) siap pasang di cPanel hosting sendiri.
   - **Opsi 2:** Bantuan migrasi penuh ke cloud hosting Vercel.
   - **Opsi 3:** Pratinjau Before vs After.

---

## 👨‍💻 Tim Pengembang
*Dikembangkan oleh **Tim Web Engineering Pipeline** — Sistem Otomasi Preservasi Web, Turn-Key Agency & Dominasi SEO.*

