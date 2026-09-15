"""
Contact Validation & Multi-Tier Fallback Cascade Engine for Indonesian Businesses.
Performs pre-flight qualification on contact channels:
- Indonesian mobile prefix identification (Telkomsel, Indosat, XL, Tri, Smartfren)
- Regional PSTN landline detection (021, 022, 031, 0542, 061, 0778, etc.)
- Multi-tier fallback routing:
  * Valid Mobile -> WhatsApp Primary Channel
  * Landline (021/031) or Non-WA + Email -> Auto-Switch to Cold Email (Fallback Tier 1)
  * Landline without Email -> Auto-Switch to Direct Dial Telesales Sheet (Fallback Tier 2)
  * Invalid/Dead Numbers without Email -> Discard / Blacklist (Fail-Fast)
"""

import re
from typing import Dict, Any, Optional

# Indonesian Mobile Prefixes (4 digits)
INDONESIAN_MOBILE_OPERATORS = {
    # Telkomsel / By.U
    "0811": "Telkomsel (Halo)", "0812": "Telkomsel (SimPATI)", "0813": "Telkomsel (SimPATI)",
    "0821": "Telkomsel (SimPATI)", "0822": "Telkomsel (Loop)", "0823": "Telkomsel (AS)",
    "0851": "Telkomsel (By.U/AS)", "0852": "Telkomsel (AS)", "0853": "Telkomsel (AS)",
    # Indosat Ooredoo Hutchison (IM3)
    "0814": "Indosat (M2)", "0815": "Indosat (Matrix/Mentari)", "0816": "Indosat (Matrix)",
    "0855": "Indosat (Matrix)", "0856": "Indosat (IM3)", "0857": "Indosat (IM3)", "0858": "Indosat (Mentari)",
    # XL Axiata
    "0817": "XL", "0818": "XL", "0819": "XL", "0859": "XL", "0877": "XL", "0878": "XL",
    # Axis
    "0831": "Axis", "0832": "Axis", "0833": "Axis", "0838": "Axis",
    # Tri (3)
    "0895": "Tri (3)", "0896": "Tri (3)", "0897": "Tri (3)", "0898": "Tri (3)", "0899": "Tri (3)",
    # Smartfren
    "0881": "Smartfren", "0882": "Smartfren", "0883": "Smartfren", "0884": "Smartfren",
    "0885": "Smartfren", "0886": "Smartfren", "0887": "Smartfren", "0888": "Smartfren", "0889": "Smartfren"
}

# Major Indonesian Regional PSTN Area Codes
INDONESIAN_PSTN_AREAS = {
    "021": "Jabodetabek (Jakarta, Bogor, Depok, Tangerang, Bekasi)",
    "022": "Bandung & Cimahi",
    "0231": "Cirebon", "0232": "Kuningan", "0233": "Majalengka", "0234": "Indramayu",
    "024": "Semarang",
    "0251": "Bogor", "0252": "Lebak", "0253": "Pandeglang", "0254": "Serang & Cilegon",
    "0260": "Subang", "0261": "Sumedang", "0262": "Garut", "0263": "Cianjur", "0264": "Purwakarta",
    "0265": "Tasikmalaya, Ciamis, Banjar", "0266": "Sukabumi", "0267": "Karawang",
    "0271": "Solo (Surakarta)", "0272": "Klaten", "0273": "Wonogiri", "0274": "Yogyakarta",
    "0275": "Purworejo", "0276": "Boyolali",
    "0281": "Purwokerto & Banyumas", "0282": "Cilacap", "0283": "Tegal & Brebes", "0285": "Pekalongan",
    "0291": "Kudus & Jepara", "0293": "Magelang", "0294": "Kendal", "0295": "Pati & Rembang",
    "031": "Surabaya, Sidoarjo, Gresik",
    "0321": "Mojokerto & Jombang", "0331": "Jember", "0333": "Banyuwangi", "0335": "Probolinggo",
    "0341": "Malang & Batu", "0342": "Blitar", "0343": "Pasuruan",
    "0351": "Madiun", "0354": "Kediri", "0356": "Tuban",
    "0361": "Denpasar & Badung (Bali)", "0370": "Mataram & Lombok",
    "0411": "Makassar & Maros", "0431": "Manado", "0451": "Palu",
    "0511": "Banjarmasin & Banjarbaru", "0541": "Samarinda", "0542": "Balikpapan",
    "0561": "Pontianak", "0536": "Palangka Raya", "0551": "Tarakan",
    "061": "Medan & Deli Serdang", "0651": "Banda Aceh",
    "0711": "Palembang", "0721": "Bandar Lampung", "0741": "Jambi",
    "0751": "Padang", "0761": "Pekanbaru", "0778": "Batam", "0771": "Tanjungpinang"
}


class ContactValidator:
    """
    Validates Indonesian contact points and orchestrates the multi-tier fallback cascade.
    """

    @staticmethod
    def clean_digits(phone: str) -> str:
        """Strips all non-digit characters."""
        if not phone:
            return ""
        return re.sub(r"[^\d]", "", str(phone))

    @staticmethod
    def normalize_to_local_0(phone: str) -> str:
        """Converts international +62 or raw digits to standard 0-prefixed local format."""
        digits = ContactValidator.clean_digits(phone)
        if not digits:
            return ""
        if digits.startswith("620"):
            return "0" + digits[3:]
        elif digits.startswith("62"):
            return "0" + digits[2:]
        elif digits.startswith("0"):
            return digits
        elif digits.startswith("8"):
            return "0" + digits
        return digits

    @staticmethod
    def normalize_to_e164(phone: str) -> str:
        """Converts to international E.164 without '+' (e.g. 628123456789)."""
        local = ContactValidator.normalize_to_local_0(phone)
        if not local:
            return ""
        if local.startswith("0"):
            return "62" + local[1:]
        return local

    @classmethod
    def identify_phone_type(cls, raw_phone: str) -> Dict[str, Any]:
        """
        Analyzes an Indonesian phone number.
        Returns phone classification, operator/area info, and validation flags.
        """
        if not raw_phone:
            return {
                "raw": "",
                "normalized_local": "",
                "normalized_e164": "",
                "type": "none",
                "is_mobile": False,
                "is_landline": False,
                "operator": None,
                "area_name": None,
                "is_valid": False
            }

        local = cls.normalize_to_local_0(raw_phone)
        e164 = cls.normalize_to_e164(raw_phone)

        # 1. Check Mobile (08xx)
        if local.startswith("08") and 10 <= len(local) <= 14:
            prefix4 = local[:4]
            operator = INDONESIAN_MOBILE_OPERATORS.get(prefix4, "Operator Seluler Indonesia")
            return {
                "raw": raw_phone,
                "normalized_local": local,
                "normalized_e164": e164,
                "type": "mobile",
                "is_mobile": True,
                "is_landline": False,
                "operator": operator,
                "area_name": None,
                "is_valid": True
            }

        # 2. Check Landline (02x, 03x, 04x, 05x, 06x, 07x, 09x)
        area_name = None
        if len(local) >= 8:
            prefix4 = local[:4]
            prefix3 = local[:3]
            if prefix4 in INDONESIAN_PSTN_AREAS:
                area_name = INDONESIAN_PSTN_AREAS[prefix4]
            elif prefix3 in INDONESIAN_PSTN_AREAS:
                area_name = INDONESIAN_PSTN_AREAS[prefix3]
            elif re.match(r"^0[2345679]\d+", local):
                area_name = "PSTN Kantor / Rumah Indonesia"

            if area_name:
                return {
                    "raw": raw_phone,
                    "normalized_local": local,
                    "normalized_e164": e164,
                    "type": "landline",
                    "is_mobile": False,
                    "is_landline": True,
                    "operator": "Telkom PSTN",
                    "area_name": area_name,
                    "is_valid": True
                }

        # Invalid or unclassifiable
        return {
            "raw": raw_phone,
            "normalized_local": local,
            "normalized_e164": e164,
            "type": "invalid",
            "is_mobile": False,
            "is_landline": False,
            "operator": None,
            "area_name": None,
            "is_valid": False
        }

    @classmethod
    def validate_email(cls, email: Optional[str]) -> bool:
        """Validates email format and filters out bogus/dummy addresses."""
        if not email:
            return False
        clean = email.strip().lower()
        if not re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,7}$", clean):
            return False
        if any(clean.endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif"]):
            return False
        if any(dom in clean for dom in ["example.com", "domain.com", "email.com", "wix.com", "wordpress.com"]):
            return False
        return True

    @classmethod
    def evaluate_contact_cascade(
        cls,
        raw_phone: Optional[str],
        email: Optional[str],
        wa_verified: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Executes the Multi-Tier Fallback Cascade:
        - Tier 0: Valid mobile number with WhatsApp -> channel: 'whatsapp'
        - Tier 1: PSTN landline (021/031) or unverified WA, but has Email -> channel: 'email'
        - Tier 2: PSTN landline without Email -> channel: 'cold_call' (Direct Dial Telesales Queue)
        - Tier 3: Invalid / No Contact -> channel: 'discard' (Fail-Fast)
        """
        phone_info = cls.identify_phone_type(raw_phone or "")
        has_valid_email = cls.validate_email(email)
        clean_email = email.strip().lower() if has_valid_email else ""

        # Case 1: Active Mobile / WhatsApp Number
        if phone_info["is_mobile"]:
            if wa_verified is False:
                if has_valid_email:
                    return {
                        "primary_channel": "email",
                        "phone_info": phone_info,
                        "email": clean_email,
                        "fallback_tier": 1,
                        "status": "fallback_email",
                        "notes": f"Nomor HP {phone_info['normalized_local']} tidak terdaftar di WhatsApp. Fallback otomatis ke Cold Email."
                    }
                else:
                    return {
                        "primary_channel": "discard",
                        "phone_info": phone_info,
                        "email": "",
                        "fallback_tier": 3,
                        "status": "invalid_contact",
                        "notes": f"Nomor HP {phone_info['normalized_local']} tidak terdaftar di WhatsApp dan tidak memiliki email bisnis."
                    }

            return {
                "primary_channel": "whatsapp",
                "phone_info": phone_info,
                "email": clean_email,
                "fallback_tier": 0,
                "status": "qualified_whatsapp",
                "notes": f"Nomor WhatsApp HP valid ({phone_info['operator'] or 'Mobile'})."
            }

        # Case 2: PSTN Landline (021, 022, 031, etc.)
        if phone_info["is_landline"]:
            if has_valid_email:
                return {
                    "primary_channel": "email",
                    "phone_info": phone_info,
                    "email": clean_email,
                    "fallback_tier": 1,
                    "status": "fallback_email",
                    "notes": f"Nomor kantor PSTN ({phone_info['area_name']}). Fallback otomatis ke Cold Email: {clean_email}."
                }
            else:
                return {
                    "primary_channel": "discard",
                    "phone_info": phone_info,
                    "email": "",
                    "fallback_tier": 3,
                    "status": "discarded",
                    "notes": f"Nomor telepon kantor PSTN ({phone_info['area_name']}) tanpa WhatsApp/Email dilewati (Telesales dinonaktifkan)."
                }

        # Case 3: No valid phone, but valid email exists
        if has_valid_email:
            return {
                "primary_channel": "email",
                "phone_info": phone_info,
                "email": clean_email,
                "fallback_tier": 1,
                "status": "fallback_email",
                "notes": f"Tidak ada nomor telepon valid. Fallback ke Cold Email: {clean_email}."
            }

        # Case 4: Complete dead end
        return {
            "primary_channel": "discard",
            "phone_info": phone_info,
            "email": "",
            "fallback_tier": 3,
            "status": "discarded",
            "notes": "Tidak ditemukan nomor HP/PSTN valid maupun alamat email bisnis."
        }


COLD_CALL_RECEPTIONIST_SCRIPT = """
================================================================================
SCRIPT RESEPSIONIS / PIC PANGGILAN 30 DETIK (NOMOR PSTN KANTOR)
Target: {business_name} ({domain})
Telepon: {phone} ({area_name})
================================================================================

[Salam Pembuka & Otoritas Konsultatif]
"Halo, selamat siang. Dengan PT/CV {business_name}?"
(Tunggu respon: "Iya betul, ada yang bisa dibantu?")

[Alasan Menghubungi - Kredibilitas Singkat]
"Saya [Nama Sales/Engineer] dari tim web engineering. Mau konfirmasi singkat, kami baru saja
meninjau profil bisnis {business_name} yang sangat baik di Google, dan tim kami telah
menyiapkan prototipe pembaruan website {domain} agar tampil responsif di ponsel dan
terindeks optimal di pencarian Google."

[The Ask - Meminta Nomor WhatsApp Marketing / Owner]
"Agar berkas ringkasan dan tautan preview-nya bisa kami kirimkan, boleh saya minta
nomor WhatsApp bagian marketing, penanggung jawab kantor, atau pimpinan?"

[Jika Diberikan Nomor WA:]
"Terima kasih banyak, segera kami kirimkan via WhatsApp untuk ditinjau. Selamat siang."
-> Masukkan nomor tersebut ke Dasbor di bagian: 'Konversi ke WhatsApp'.
================================================================================
"""
