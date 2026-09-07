"""
Clean Source Code Packager & Client Delivery Handover Module.
Bundles modernized website assets into clean, deployable .zip archives with
comprehensive cPanel installation and Google SEO configuration guides.
"""

import os
import zipfile
import re
from datetime import datetime
from typing import Dict, Any, Optional


CPANEL_GUIDE_TEMPLATE = """# PANDUAN RESMI PEMASANGAN WEBSITE DI CPANEL HOSTING
**Klien:** {business_name} ({domain})  
**Tanggal Rilis:** {date_str}  
**Paket:** Source Code Bersih Berstandar Swiss Minimalist + Google SEO Schema  

---

Selamat atas kepemilikan website modern baru Anda! Dokumen ini memandu Anda atau tim teknis Anda untuk memasang website ini ke hosting cPanel milik sendiri dalam waktu kurang dari 5 menit.

## A. PERSIAPAN
File ZIP ini berisi seluruh kode sumber website yang telah teroptimasi 100%:
- `index.html` : Halaman utama website dengan struktur Google SEO Schema.org
- `assets/` : Gambar, logo, icon, dan styling responsif
- `robots.txt` : Petunjuk perayapan untuk mesin pencari Google
- `sitemap.xml` : Peta situs otomatis untuk Google Search Console

---

## B. LANGKAH-LANGKAH PEMASANGAN DI CPANEL

### 1. Masuk ke cPanel
1. Buka browser dan ketik alamat cPanel hosting Anda (biasanya `https://domainanda.com:2083` atau melalui dasbor penyedia hosting seperti Niagahoster, DomaiNesia, Rumahweb, dsb).
2. Masukkan Username dan Password cPanel Anda.

### 2. Cadangkan (Backup) File Lama (Jika Ada)
1. Di cPanel, cari dan klik menu **File Manager**.
2. Masuk ke folder **`public_html`**.
3. Jika sudah ada website lama, Anda bisa membuat folder baru bernama `backup_lama` dan memindahkan file lama ke folder tersebut untuk berjaga-jaga.

### 3. Unggah (Upload) File ZIP Website Baru
1. Pastikan Anda berada di dalam folder **`public_html`**.
2. Klik tombol **Upload** pada menu bagian atas.
3. Seret (drag & drop) atau pilih file ZIP website baru ini.
4. Tunggu hingga bilah progres mencapai **100% (berwarna hijau)**.

### 4. Ekstrak (Extract) Berkas
1. Kembali ke tab File Manager, klik tombol **Reload**.
2. Klik kanan pada file ZIP yang baru saja diunggah, lalu pilih opsi **Extract**.
3. Pastikan lokasi ekstraksi ditujukan langsung ke **`/public_html`**.
4. Klik **Extract File(s)** lalu tutup pop-up konfirmasi.

> ⚠️ **PENTING:** Pastikan file `index.html`, `robots.txt`, `sitemap.xml`, dan folder `assets/` berada LANGSUNG di dalam folder `public_html`, BUKAN di dalam sub-folder ekstra.

### 5. Aktifkan Sertifikat Keamanan SSL Gratis (HTTPS)
1. Kembali ke halaman utama cPanel.
2. Cari dan klik menu **SSL/TLS Status**.
3. Pilih nama domain Anda, lalu klik tombol **Run AutoSSL** di bagian atas.
4. Dalam 2-5 menit, ikon gembok hijau (*Connection Secure*) akan aktif secara otomatis.

### 6. Uji Coba Tampilan
Buka `https://domainanda.com` di smartphone dan laptop Anda. Pastikan tombol WhatsApp sales berfungsi langsung mengarahkan ke nomor resmi Anda.

---

## C. BANTUAN TEKNIS
Jika Anda membutuhkan bantuan teknis dalam proses pointing domain atau upload cPanel, tim Web Engineering Pipeline siap mendampingi Anda hingga online sempurna.
"""

SEO_GUIDE_TEMPLATE = """# PANDUAN OPTIMASI & VERIFIKASI GOOGLE SEARCH CONSOLE
**Klien:** {business_name} ({domain})  
**Tanggal Rilis:** {date_str}  
**Standar SEO:** Google Helpful Content & Rich Results Schema 2026  

---

Website baru Anda telah dilengkapi fondasi teknis SEO kelas dunia. Untuk memastikan Google mengindeks dan menaikkan peringkat bisnis Anda secara maksimal, ikuti langkah-langkah di bawah ini:

## 1. VERIFIKASI DOMAIN DI GOOGLE SEARCH CONSOLE
1. Kunjungi [Google Search Console](https://search.google.com/search-console).
2. Masuk menggunakan akun Google / Gmail bisnis Anda.
3. Klik **Tambahkan Properti (Add Property)**.
4. Masukkan URL domain resmi Anda: `https://{domain}`.
5. Pilih metode verifikasi yang termudah:
   - **Metode Tag HTML:** Salin kode meta yang diberikan Google, lalu tempelkan di bagian `<head>` pada file `index.html`.
   - **Metode DNS Record:** Tambahkan TXT Record di panel DNS domain Anda.
6. Klik **Verifikasi**.

---

## 2. SUBMIT PETA SITUS (SITEMAP.XML)
Website ini sudah dilengkapi file `sitemap.xml` yang valid.
1. Pada menu sebelah kiri Google Search Console, klik **Peta Situs (Sitemaps)**.
2. Pada kolom "Tambahkan peta situs baru", ketik: `sitemap.xml`.
3. Klik tombol **Kirim (Submit)**.
4. Google akan membaca sitemap dalam beberapa jam dan mulai mengindeks seluruh halaman.

---

## 3. SINKRONISASI GOOGLE BUSINESS PROFILE (GOOGLE MAPS)
Untuk memenangkan pencarian lokal:
1. Buka akun **Google Profil Bisnis (Google Maps)** Anda.
2. Masukkan link website resmi: `https://{domain}`.
3. Pastikan Nama Bisnis, Alamat Fisik, dan Nomor WhatsApp di Google Maps 100% IDENTIK dengan data yang tercantum pada website baru.
4. Konsistensi NAP (*Name, Address, Phone*) adalah sinyal peringkat lokal nomor 1 bagi Google.

---

## 4. VALIDASI STRUKTUR SCHEMA.ORG
Website baru Anda telah ditanamkan Schema.org JSON-LD tipe `LocalBusiness` / `Service`.
1. Anda dapat menguji validitasnya di [Google Rich Results Test](https://search.google.com/test/rich-results).
2. Masukkan alamat website Anda untuk memastikan tidak ada error dan fitur rich snippets aktif.

---

## 5. OPTIMASI KONVERSI WHATSAPP SALES
Seluruh tombol kontak di website telah dipasang *Direct WhatsApp Routing* dengan pesan salam otomatis. Pastikan admin WhatsApp merespons chat masuk dalam waktu maksimal 5 menit untuk menjaga tingkat konversi tetap tinggi.
"""


class CodePackager:
    def __init__(self):
        pass

    def package_client_code(
        self,
        site_dir: str,
        client_slug: str,
        output_dir: Optional[str] = None,
        business_name: str = "",
        domain: str = ""
    ) -> Dict[str, Any]:
        """
        Creates a clean .zip package containing all site assets and comprehensive documentation.
        """
        if not os.path.exists(site_dir):
            return {
                "success": False,
                "error": f"Site directory not found: {site_dir}",
                "zip_path": ""
            }

        target_out_dir = output_dir or os.path.dirname(os.path.normpath(site_dir))
        os.makedirs(target_out_dir, exist_ok=True)

        clean_slug = re.sub(r"[^a-zA-Z0-9_\-]", "_", client_slug).strip("_")
        zip_filename = f"{clean_slug}_Clean_Source_Code.zip"
        zip_path = os.path.join(target_out_dir, zip_filename)

        biz_name = business_name or clean_slug.replace("_", " ").title()
        dom = domain or f"{clean_slug.lower()}.com"
        today_str = datetime.now().strftime("%d %B %Y")

        # Generate custom guides
        cpanel_md = CPANEL_GUIDE_TEMPLATE.format(business_name=biz_name, domain=dom, date_str=today_str)
        seo_md = SEO_GUIDE_TEMPLATE.format(business_name=biz_name, domain=dom, date_str=today_str)

        # Also write guides to disk in target_out_dir for instant reading
        cpanel_path = os.path.join(target_out_dir, "PANDUAN_PEMASANGAN_CPANEL.md")
        seo_path = os.path.join(target_out_dir, "SEO_CONFIGURATION_GUIDE.md")
        with open(cpanel_path, "w", encoding="utf-8") as f:
            f.write(cpanel_md)
        with open(seo_path, "w", encoding="utf-8") as f:
            f.write(seo_md)

        # Build ZIP archive
        print(f"\n[CODE PACKAGER] Membuat arsip delivery untuk: {biz_name}...")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            # 1. Add documentation at root of ZIP
            zipf.writestr("PANDUAN_PEMASANGAN_CPANEL.md", cpanel_md)
            zipf.writestr("SEO_CONFIGURATION_GUIDE.md", seo_md)

            # 2. Add all site files
            for root, dirs, files in os.walk(site_dir):
                if ".git" in root.split(os.sep):
                    continue
                for f in files:
                    full_p = os.path.join(root, f)
                    rel_p = os.path.relpath(full_p, site_dir)
                    zipf.write(full_p, rel_p)

        file_size_mb = os.path.getsize(zip_path) / (1024 * 1024)
        print(f"[+] [SUCCESS] Paket Source Code berhasil dibuat: {zip_path} ({file_size_mb:.2f} MB)")

        return {
            "success": True,
            "zip_path": os.path.abspath(zip_path),
            "filename": zip_filename,
            "size_mb": round(file_size_mb, 2),
            "cpanel_guide": os.path.abspath(cpanel_path),
            "seo_guide": os.path.abspath(seo_path),
            "download_url": f"/api/download-package?client={clean_slug}"
        }
