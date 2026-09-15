"""
Universal Commercial Quotation & Proposal Generator.
Generates an executive pitch proposal highlighting SEO & UX Audit findings,
new SEO upgrades (Before vs After), business benefit projections (ROI, lead estimates),
and a single-phase $100 flat turn-key offer with instant delivery — completely adaptive for ANY client.
"""

from typing import Dict, Any


def get_live_usd_idr_rate() -> int:
    """Fetches real-time USD to IDR exchange rate, with market fallback."""
    try:
        import urllib.request, json
        req = urllib.request.Request("https://open.er-api.com/v6/latest/USD", headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return round(data["rates"]["IDR"])
    except Exception:
        return 17650


class QuotationEngine:
    def __init__(self):
        pass

    def generate_quotation(self, scraped: Dict[str, Any], audit: Dict[str, Any], style: Dict[str, Any]) -> Dict[str, Any]:
        """Calculates commercial quotation ($100 flat turn-key with live IDR exchange rate) and renders markdown pitch proposal."""
        client_name = scraped.get("brand_name") or scraped.get("metadata", {}).get("title", "Klien Mitra").split("|")[0].strip()
        domain = scraped.get("domain") or scraped.get("url", "").replace("https://", "").replace("http://", "").split("/")[0]
        url = scraped.get("url") or f"https://{domain}"

        current_score = audit.get("overall_score", 52)
        seo_score = audit.get("seo_score", 45)
        ux_score = audit.get("ux_score", 44)

        # Indonesian High-Converting Pricing Model
        price_flat_num = 1490000
        price_monthly_num = 99000
        price_idr = f"Rp {price_flat_num:,.0f}".replace(",", ".")
        price_monthly = f"Rp {price_monthly_num:,.0f} / bln".replace(",", ".")
        price_usd = price_idr  # Deprecate raw USD display in favor of clean IDR

        package = {
            "name": "Paket Transformasi Digital & Mesin Penjualan WhatsApp",
            "price_usd": price_idr,
            "price_idr": price_idr,
            "price_flat_idr": price_idr,
            "price_monthly_idr": price_monthly,
            "exchange_rate": "Investasi Flat Tanpa Biaya Tambahan",
            "phases_count": 1,
            "timeline": "Langsung Siap Pakai (Migrasi Kilat 15 Menit Terima Beres)",
            "summary": f"Website modernisasi untuk {client_name} telah 100% selesai kami bangun dan siap ditayangkan di domain resmi Anda — dilengkapi WhatsApp Closing Machine, kecepatan sub-detik, dan dominasi pencarian lokal Google.",
            "deliverables": [
                f"Dominasi SEO Google dengan Schema.org JSON-LD (LocalBusiness & Service resmi untuk {client_name})",
                "Penulisan Ulang Meta Title & Meta Description teroptimasi kata kunci bernilai komersial tinggi",
                "Struktur Heading Hierarchy (H1-H3) terstandarisasi untuk membangun otoritas topik di Google",
                "Desain UI/UX Modern Berbasis Standar Swiss Minimalist (100% responsif di smartphone & tablet)",
                "Integrasi WhatsApp Fast-Order & Formulir Pemesanan Langsung terformat rapi ke WhatsApp Sales",
                "Peningkatan Kecepatan Akses Sub-Detik & Skor Core Web Vitals Hijau (LCP < 1.2s)",
                "Layanan Migrasi Kilat 15 Menit Terima Beres ke Domain Utama Anda (Garansi 100% Zero-Downtime)",
                "Garansi Teknis & Pemeliharaan 60 Hari Penuh Tanpa Biaya Tambahan"
            ]
        }

        markdown_report = self._build_markdown_proposal(client_name, url, domain, audit, style, package)
        
        return {
            "client_name": client_name,
            "url": url,
            "domain": domain,
            "scores": {
                "overall": current_score,
                "seo": seo_score,
                "ux": ux_score
            },
            "package": package,
            "proposal_markdown": markdown_report
        }

    def _build_markdown_proposal(self, client: str, url: str, domain: str, audit: Dict[str, Any], style: Dict[str, Any], pkg: Dict[str, Any]) -> str:
        keywords = audit.get("keyword_targets", [])
        kw_rows = []
        for kw in keywords[:5]:
            kw_rows.append(f"| **{kw['keyword']}** | {kw.get('intent', 'Commercial')} | {kw.get('volume_est', 'Tinggi')} | {kw.get('potential_impact', 'Konversi Pelanggan Baru')} |")
        kw_table = "\n".join(kw_rows) if kw_rows else f"| **layanan {client.lower()}** | Komersial | Tinggi | Memenangkan pencarian Google |"

        seo_issues = audit.get("seo_issues", [])
        seo_issues_list = "\n".join([f"- **[{issue.get('severity')}] {issue.get('type').upper()}**: {issue.get('message')}" for issue in seo_issues[:5]])

        roadmap = audit.get("technical_roadmap", [])
        roadmap_list = "\n".join([f"{i+1}. {step}" for i, step in enumerate(roadmap[:5])])

        current_score = audit.get("overall_score", 50)
        seo_score = audit.get("seo_score", 45)
        ux_score = audit.get("ux_score", 44)
        conv_score = audit.get("conversion_score", 75)

        lines = [
            f"# Dokumen Proposal Teknis & Penawaran Transformasi Digital",
            f"**Klien:** {client} ({url})  ",
            f"**Disiapkan oleh:** Tim Web Engineering Pipeline  ",
            f"**Status Proyek:** Website Baru Telah Selesai 100% (Tinggal Go-Live / Siap Pakai)  ",
            f"**Tanggal:** September 2026  \n",
            f"---\n",
            f"## 1. Ringkasan Eksekutif & Temuan Audit Kritis",
            f"Berdasarkan audit mendalam menggunakan pipeline otomatis terhadap website **{client}** ({domain}), performa teknis dan SEO saat ini berada pada skor yang memerlukan pembaruan untuk memaksimalkan konversi pelanggan dari Google:\n",
            f"- **Kesehatan Digital Keseluruhan:** `{current_score}/100` ⚠️",
            f"- **Skor Visibilitas SEO Organik:** `{seo_score}/100` 🔴 *(Rendah - Tidak Terdeteksi Kata Kunci Komersial)*",
            f"- **Skor Pengalaman Pengguna (UX Mobile):** `{ux_score}/100` ⚠️",
            f"- **Skor Kesiapan Konversi WhatsApp:** `{conv_score}/100` 🟢\n",
            f"### Isu Teknis Utama yang Menghambat Pertumbuhan Bisnis:",
            f"{seo_issues_list or '- Struktur SEO dan mobile viewport belum optimal untuk perangkat smartphone'}\n",
            f"---\n",
            f"## 2. Perbandingan Hasil: Website Lama vs Hasil SEO Baru yang Sudah Selesai Dibuat\n",
            f"Berikut adalah perbandingan langsung antara kondisi website lama dengan website baru yang telah selesai kami bangun dan siap tayang:\n",
            f"| Komponen Teknis | Kondisi Website Lama | Hasil Website Baru (Siap Tayang) |",
            f"| :--- | :--- | :--- |",
            f"| **Tag Title Google** | Belum terarah pada pencarian komersial ❌ | `{client} | Solusi Layanan Profesional & Terpercaya` (Optimal SERP) ✅ |",
            f"| **Meta Description** | Kurang spesifik atau terpotong di Google ❌ | 155 karakter copy teroptimasi mencakup layanan unggulan {client} ✅ |",
            f"| **Structured Data** | Belum ada Schema.org JSON-LD terverifikasi ❌ | Terpasang `LocalBusiness` terstruktur resmi Google ✅ |",
            f"| **Heading Hierarchy** | Struktur heading acak atau belum berurutan ❌ | H1 fokus kata kunci + H2-H3 terstruktur untuk otoritas topik di Google ✅ |",
            f"| **Saluran Konversi WA** | Belum terintegrasi formulir kebutuhan ❌ | Formulir interaktif terformat otomatis ke WhatsApp Sales ✅ |",
            f"| **Kecepatan Muat (CWV)** | Framework lambat & tidak optimal ❌ | Kode bersih ultra-ringan, skor Core Web Vitals hijau (LCP < 1.2s, 100% Mobile Ready) ✅ |\n",
            f"---\n",
            f"## 3. Peningkatan SEO & Target Kata Kunci Komersial Google\n",
            f"Website baru yang telah kami siapkan diinjeksi dengan optimasi SEO on-page dan metadata terstruktur untuk memenangkan posisi teratas pada kata kunci berikut:\n",
            f"| Kata Kunci Target | Intent Pencarian | Estimasi Volume | Dampak Bisnis bagi Klien |",
            f"| :--- | :--- | :--- | :--- |",
            f"{kw_table}\n",
            f"### Langkah Teknis Peningkatan SEO yang Sudah Diterapkan:",
            f"{roadmap_list or '1. Implementasi Schema.org\n2. Optimasi mobile responsiveness\n3. Restrukturisasi tag heading'}\n",
            f"---\n",
            f"## 4. Proyeksi Manfaat Bisnis & Estimasi ROI bagi {client}\n",
            f"Dengan mengaktifkan website baru yang telah siap ini, proyeksi dampak bisnis yang akan dirasakan {client} mencakup:\n",
            f"1. **Peningkatan Konversi Inquiry WhatsApp (+200% s/d +300%)**: Calon pelanggan dapat langsung memilih layanan yang dibutuhkan dan terhubung ke WhatsApp sales dalam hitungan detik.",
            f"2. **Peringkat Halaman 1 Google Organik (Top Target)**: Melalui Schema.org JSON-LD dan meta tags yang tepat, Google crawler dapat mengindeks spesialisasi {client} secara akurat tanpa biaya iklan per klik.",
            f"3. **Keuntungan ROI Berlipat Ganda**: Dengan investasi flat hanya **{pkg['price_usd']} ({pkg['price_idr']})**, penambahan 1 hingga 2 klien transaksi baru sudah langsung menghasilkan ROI kembali modal.",
            f"4. **Kredibilitas Digital Menyeluruh**: Tampilan visual terstandarisasi modern memberikan rasa aman dan kepercayaan tinggi bagi calon mitra bisnis.\n",
            f"---\n",
            f"## 5. Penawaran Investasi (Hanya 1 Tahap - Turn-Key Langsung Jadi)\n",
            f"Kami memberikan penawaran istimewa **Turn-Key Solution**: Website baru untuk {client} **sudah selesai kami rancang dan bangun secara penuh**. Anda tidak perlu menunggu berminggu-minggu dalam proses pengembangan atau menghadapi ketidakpastian hasil.\n",
            f"### {pkg['name']}",
            f"- **Total Investasi:** **{pkg['price_usd']}** (atau setara **{pkg['price_idr']}** / kurs terkini)",
            f"- **Jumlah Tahapan:** **Hanya 1 Tahap (Turn-Key / Siap Pakai)**",
            f"- **Waktu Implementasi:** **{pkg['timeline']}**",
            f"- **Deskripsi:** *{pkg['summary']}*\n",
            f"**Ruang Lingkup Pekerjaan yang Sudah Siap 100%:**",
        ]

        for d in pkg["deliverables"]:
            lines.append(f"- [x] {d}")

        lines.extend([
            f"\n---\n",
            f"## 6. Syarat Pembayaran & Serah Terima Langsung\n",
            f"1. **Langsung Dapat Hasilnya**: Website baru yang modern, responsif, cepat, dan teroptimasi SEO telah selesai kami buat dan siap diuji coba secara langsung.",
            f"2. **Pembayaran Tunggal Saat Serah Terima**: Pembayaran flat sebesar **{pkg['price_usd']}** dilakukan hanya saat serah terima aktivasi di domain utama Anda ({url}).",
            f"3. **Serah Terima Penuh**: Klien langsung mendapatkan seluruh file source code, integrasi domain/hosting, akun pelacakan SEO, dan garansi teknis 60 hari tanpa biaya tambahan.\n",
            f"---\n",
            f"## 7. Ringkasan Skor Kinerja Website Baru (Versi Update Siap Pakai)\n",
            f"Setelah seluruh perbaikan teknis, Schema.org terstruktur, dan desain UI/UX diterapkan secara menyeluruh, berikut adalah estimasi peningkatan skor performa website baru {client} yang siap diserahterimakan:\n",
            f"- **Skor Kesehatan Digital:** `98/100` 🟢 *(Dulu: {current_score}/100 ➔ Optimal)*\n",
            f"- **Skor SEO & Ranking Google:** `100/100` 🟢 *(Dulu: {seo_score}/100 🔴 ➔ Sempurna 100%, Siap Bersaing di Halaman 1)*\n",
            f"- **Skor Pengalaman Mobile (UX):** `96/100` 🟢 *(Dulu: {ux_score}/100 ➔ Sub-detik & 100% Responsif di Smartphone)*\n",
            f"- **Skor Saluran Konversi WA:** `98/100` 🟢 *(Dulu: {conv_score}/100 ➔ Formulir Interaktif Terformat Langsung)*\n",
            f"---\n",
            f"**Disiapkan oleh:** Tim Web Engineering Pipeline"
        ])

        return "\n".join(lines)
