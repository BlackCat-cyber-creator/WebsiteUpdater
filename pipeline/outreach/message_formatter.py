"""
High-Converting Sales Psychology B2B Copywriting Engine for Indonesian SME WhatsApp Outreach.
Synthesizes cutting-edge persuasion psychology:
- Chris Voss's Low-Friction / No-Oriented Permission Framing (Never Split the Difference)
- Robert Cialdini's Micro-Commitment & Reciprocity (Pre-made value gift)
- The WhatsApp Closing Machine (Direct PO / fast-order routing)
- Zero-Friction Handover (Terima Beres 15 Menit ke domain klien)
- Micro-Question Close (Menggantikan CTA pasif 'silakan dilihat santai')
- Culturally tailored respect & warmth for Indonesian SME owners/operators.
- STRICT RULE: ZERO internal tool jargon. ZERO USD/$100 mentions. ZERO zip/cPanel headache.
"""

from typing import List, Optional
import urllib.parse


def generate_outreach_message(
    business_name: str,
    domain: str,
    audit_signals: Optional[List[str]] = None,
    track: str = "track_b_modernize",
    rating_text: str = "",
    step: str = "step_1_permission",
    demo_url: str = ""
) -> str:
    """
    Generates high-converting, psychologically calibrated WhatsApp B2B copy.
    
    Steps:
    - 'step_1_permission': Low-friction micro-commitment hook confirming management contact.
    - 'step_2_delivery': Live demo link delivery, WhatsApp fast-order highlight, and micro-question.
    - 'step_3_followup': Consultative follow-up nudge for leads that opened the demo.
    - 'legacy_one_shot': Single-shot high-status consultative pitch with direct clickable link.
    """
    if audit_signals is None:
        audit_signals = []

    clean_url = f"https://{domain}" if not domain.startswith("http") else domain
    
    # Resolve live demo URL fallback if not explicitly provided
    if not demo_url:
        if "vercel.app" in domain:
            demo_url = clean_url
        else:
            # Clean slug heuristic
            slug = domain.replace("https://", "").replace("http://", "").split("/")[0].replace(".", "-")
            demo_url = f"https://{slug}.vercel.app"

    # =========================================================================
    # JALUR A: WEB BARU (Bisnis berpotensi besar di Google Maps, belum punya web resmi)
    # Sales Psychology: Micro-Commitment -> WhatsApp Closing Engine -> Micro-Question
    # =========================================================================
    if track == "track_a_new_web":
        if step == "step_1_permission":
            return f"Halo, selamat siang. Izin memastikan, apakah betul ini nomor kontak manajemen {business_name}?"

        elif step == "step_2_delivery":
            return (
                f"Baik, terima kasih responnya Pak/Bu.\n\n"
                f"Begini, kami perhatikan reputasi bisnis {business_name} di Google Maps sudah sangat bagus. Sayangnya di Google Search belum ada website resminya, jadi calon pembeli baru seringkali kesulitan cek katalog lengkap dan ragu bertransaksi.\n\n"
                f"Tanpa biaya apapun di awal, tim kami berinisiatif membuatkan satu prototipe website siap pakai khusus untuk {business_name}.\n\n"
                f"Di dalamnya sudah kami pasang fitur **WhatsApp Fast-Order**, jadi calon klien bisa langsung pilih layanan dan kirim format pesanan rapi ke WhatsApp ini.\n\n"
                f"Boleh langsung dicoba di HP Bapak/Ibu:\n"
                f"👉 {demo_url}\n\n"
                f"Rincian lengkap juga kami sertakan di PDF terlampir. Kira-kira nomor WhatsApp di tombol pemesanan demo tersebut sudah pas ke nomor admin order Bapak, atau mau diarahkan ke nomor sales yang berbeda Pak/Bu? 🙏"
            )

        elif step == "step_3_followup":
            return (
                f"Selamat siang Pak/Bu manajemen {business_name}.\n\n"
                f"Izin menanyakan perihal prototipe website {business_name} kemarin di {demo_url}. Rencana tim kami akan merapikan alokasi domain dan optimasi pencarian lokal Google untuk area ini minggu ini.\n\n"
                f"Apakah demonya sempat dicoba di HP, atau ada katalog dan nomor kontak yang ingin disesuaikan dengan tim sales Bapak/Ibu? Terima kasih banyak 🙏"
            )

        else:  # legacy_one_shot
            return (
                f"Halo, selamat siang manajemen {business_name}.\n\n"
                f"Ulasan bisnis {business_name} di Google Maps sudah sangat bagus, namun di Google Search belum tersedia website resmi untuk memvalidasi katalog usaha Anda.\n\n"
                f"Sebagai referensi, tim kami sudah buatkan satu contoh website modern siap pakai dengan fitur pesan cepat ke WhatsApp:\n"
                f"👉 {demo_url}\n\n"
                f"Dokumen audit dan rinciannya kami rangkum pada PDF terlampir. Kira-kira tombol pemesanan di demo tersebut sudah sesuai mengarah ke nomor WhatsApp ini, atau ada nomor tim sales lain Pak/Bu? 🙏"
            )

    # =========================================================================
    # JALUR B: MODERNISASI WEBSITE & AUDIT TEKNIS (Website lama lambat / belum responsif)
    # Sales Psychology: Diagnostic Authority -> Speed & Mobile Contrast -> Micro-Question
    # =========================================================================
    else:
        if step == "step_1_permission":
            return f"Halo, selamat siang. Izin memastikan, apakah betul ini nomor kontak manajemen {business_name}?"

        elif step == "step_2_delivery":
            return (
                f"Baik, terima kasih responnya Pak/Bu.\n\n"
                f"Begini, profil dan website {business_name} di {clean_url} sebenarnya sudah sangat bagus. Sayangnya saat kami uji di smartphone, aksesnya terasa cukup berat dan ada celah teknis SEO yang rawan membuat calon pembeli beralih ke kompetitor.\n\n"
                f"Tanpa mengubah identitas asli usaha Anda, tim kami telah merapikan struktur teknisnya menjadi jauh lebih kilat (skor performa 95+) dan menyematkan fitur **WhatsApp Direct-Order** agar calon klien lebih mudah bertransaksi.\n\n"
                f"Bapak/Ibu bisa coba langsung kecepatannya di HP:\n"
                f"👉 {demo_url}\n\n"
                f"Tabel perbandingan teknis lengkap sudah kami rangkum di PDF terlampir (Halaman 2-3). Kira-kira tombol pemesanan di versi baru ini sudah tepat mengarah ke nomor ini, atau sebaiknya ke nomor sales lain Pak/Bu? 🙏"
            )

        elif step == "step_3_followup":
            return (
                f"Selamat siang Pak/Bu manajemen {business_name}.\n\n"
                f"Izin konfirmasi singkat terkait hasil pembaruan website {business_name} di {demo_url}.\n\n"
                f"Jika Bapak/Ibu berminat menayangkan versi kilat ini di domain resmi {domain}, tim kami siap bantu migrasikan dalam 15 menit terima beres (tanpa ada website mati sedetik pun).\n\n"
                f"Kira-kira apakah ada masukan terkait tampilan atau daftar layanan yang ingin disesuaikan Pak/Bu? Terima kasih 🙏"
            )

        else:  # legacy_one_shot
            return (
                f"Halo, selamat siang manajemen {business_name}.\n\n"
                f"Profil bisnis {business_name} di {clean_url} sebenarnya sudah sangat bagus. Sayangnya akses di smartphone terasa cukup berat dan ada celah teknis SEO yang rawan mengalihkan calon klien ke kompetitor.\n\n"
                f"Tanpa mengubah identitas usaha Anda, tim kami telah memperbaiki performanya menjadi sub-detik dan menyematkan integrasi WhatsApp order:\n"
                f"👉 {demo_url}\n\n"
                f"Tabel perbandingan dan berkas evaluasinya ada di PDF terlampir. Kira-kira nomor WhatsApp di tombol pemesanan demo ini sudah pas mengarah ke tim sales Bapak/Ibu? 🙏"
            )


