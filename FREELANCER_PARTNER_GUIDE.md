# PANDUAN LENGKAP KEMITRAAN RESELLER & FREELANCER WHITELABEL ENGINE
**Sistem "Dropship Website B2B" Otomatis Tanpa Koding untuk Freelancer & Digital Agency Indonesia**

---

## 1. MENGAPA MODEL INI SANGAT MENGUNTUNGKAN?

### Masalah Utama Freelancer Web & Agensi di Indonesia:
1. **Capek Prospek Tanpa Bukti:** Pitching proposal mentah berlembar-lembar sering diabaikan atau dibaca tanpa tindakan.
2. **Terjebak Waktu Koding:** Menghabiskan waktu 2-4 minggu mengerjakan website klien dari nol menggunakan WordPress atau coding manual.
3. **Revisi Tanpa Henti:** Klien UKM sering menuntut revisi tak berujung padahal bayarannya murah.
4. **Pendapatan Tidak Stabil:** Menghabiskan 80% energi untuk teknis koding sehingga tidak sempat fokus jualan (*sales*).

### Solusi "Dropship Website" Website Updater:
- **0 Menit Koding:** Mesin otomatis meng-scrape profil bisnis target, menyusun katalog produk nyata, men-deploy ke Vercel Cloud (<0.5 detik), dan mengintegrasikan WhatsApp Closing Machine.
- **100% Whitelabel:** Dokumen Proposal PDF resmi dan website live 100% menyandang nama agensi, nomor WhatsApp, dan logo freelancer. Klien tidak pernah tahu kami yang mengerjakannya di belakang layar.
- **Margin Bersih Rp 2.000.000+ Per Prospek:**
  - Freelancer menjual ke klien: **Rp 2.500.000 – Rp 4.900.000** (atau skema langganan **Rp 250.000/bulan**)
  - Biaya lisensi fulfillment ke kita: **Rp 490.000** (flat sekali bayar)
  - **Keuntungan bersih langsung masuk ke kantong freelancer:** **Rp 2.000.000 – Rp 4.400.000 per closing!**

---

## 2. CARA MENJALANKAN WHITELABEL ENGINE VIA CLI

Sistem telah dilengkapi parameter resmi `--whitelabel`:

### A. Memodernisasi Website Klien Tertentu (Jalur B)
Untuk klien yang sudah punya website lama tapi lambat/jadul:
```bash
python run_pipeline.py --url https://klienlama.com --output clients/klien_modern --whitelabel --partner-name "Studio Digital Anda" --partner-wa "08123456789"
```
*Hasil:*
- Website modern live di Vercel.
- Proposal PDF resmi 4 halaman dengan kop, logo, kontak, dan tanda tangan agensi Anda.
- Arsip siap serah terima.

### B. Memburu Bisnis Lokal dari Google Maps (Jalur A)
Untuk UKM yang sudah memiliki ulasan Google Maps bagus tapi belum punya website:
```bash
python auto_outreach.py --maps "distributor frozen food surabaya" --limit 3 --whitelabel --partner-name "Studio Digital Anda" --partner-wa "08123456789"
```
*Hasil:*
- Sistem menelusuri data Google Maps, mengekstrak nomor WhatsApp dan ulasan asli bintang 5.
- Otomatis membuat website prototipe lengkap dengan katalog dan format pemesanan WhatsApp terstruktur.
- Otomatis menghasilkan proposal PDF atas nama agensi Anda.

---

## 3. TEMPLATE POSTING REKRUTMEN FREELANCER (COPY-PASTE READY)

Gunakan materi promosi di bawah ini untuk diposting di grup Facebook (*Komunitas Web Developer Indonesia*, *Freelancer Indonesia*, *Grup Bisnis Online*), Telegram, atau LinkedIn:

### 📢 Template 1: Grup Facebook Freelancer / Web Developer
**Judul:** *Bongkar Rahasia Jual Jasa Website Rp 2,5 Juta - Rp 5 Juta ke UKM Tanpa Ngetik 1 Baris Koding pun (Sistem Dropship Website)*

> Halo rekan-rekan freelancer web & marketer! 🤝
>
> Selama ini pasti sering ngalamin:
> - Ngerjain 1 website klien butuh waktu 2-3 minggu sampai pusing begadang.
> - Klien bolak-balik minta revisi padahal bayaran cuma 1-2 jutaan.
> - Kehabisan waktu buat cari klien baru karena sibuk urusan teknis server & plugin.
>
> Kami dari **Website Updater Studio** membuka program kemitraan tertutup: **Whitelabel Reseller Engine**.
>
> 💡 **Cara Kerjanya Sederhana:**
> 1. Anda cukup berikan nama bisnis target klien Anda (misal: distributor, klinik, ekspedisi, pabrik).
> 2. Mesin otomatis kami akan membangun **Website Modern Super Cepat (<0.5 detik)** + **PDF Proposal Resmi** lengkap atas nama agensi/brand Anda sendiri dalam 1 menit!
> 3. Anda kirimkan live demo & PDF tersebut ke calon klien. Begitu klien bayar Rp 2.500.000, Anda hanya membayar biaya fulfillment ke kami Rp 490.000.
> 4. **Profit bersih Rp 2.000.000+ langsung milik Anda 100%!**
>
> 🏷️ **100% Whitelabel:** Nama kami tidak akan pernah muncul. Seluruh kredit pembuatan, footer, dan dokumen proposal menyandang brand Anda.
>
> Tertarik jadi mitra awal kami? 
> Hubungi kami via WhatsApp resmi: **https://wa.me/6285128013767?text=Halo%20saya%20tertarik%20Program%20Kemitraan%20Reseller%20Website**
> *(Kuota terbatas untuk 15 mitra pertama per kota)*

---

### 📢 Template 2: Direct Message ke Freelancer Fastwork / LinkedIn
> "Halo Kak [Nama], salam kenal!
> 
> Saya perhatikan portofolio jasa digital marketing & website kakak sangat bagus di [Platform].
> 
> Kami punya infrastruktur *Whitelabel Web Generator Engine* yang memungkinkan agensi/freelancer bikin prototipe website interaktif & proposal PDF resmi dalam hitungan menit untuk klien korporat/UKM. 
>
> Sistem ini 100% whitelabel atas nama brand Kakak sendiri, dengan margin profit Rp 2-3 juta per klien tanpa kakak harus coding manual dari nol.
> 
> Boleh kami kirimkan contoh prototipe live dan skema kemitraan santai via WhatsApp? 
> Link WhatsApp kami: https://wa.me/6285128013767"

---

## 4. SOP & SIKLUS TRANSAKSI DENGAN FREELANCER

1. **Pendaftaran Mitra:** Freelancer mengisi nama agensi, nomor WhatsApp bisnis, dan logo (opsional).
2. **Generate Pitching Kit:** Mitra menjalankan CLI atau mengirimkan link website lama / link Google Maps target klien mereka ke sistem.
3. **Closing ke Klien:** Mitra mengirimkan pesan pendekatan WhatsApp (SOP Step 1 Permission Hook) + Live Demo Vercel + PDF Proposal.
4. **Pembayaran Klien:** Klien membayar Rp 2.500.000 langsung ke rekening/VA mitra freelancer.
5. **Aktivasi ke Sistem Kami:** Mitra membayar Rp 490.000 (via Midtrans QRIS/VA) ke sistem kami.
6. **Migrasi Kilat 15 Menit:** Tim teknis kami mengarahkan DNS domain resmi klien sampai live tanpa downtime.
7. **Selesai:** Klien puas karena prosesnya kilat, mitra freelancer untung bersih Rp 2.000.000+ tanpa pusing teknis.
