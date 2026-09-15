"""
Dynamic High-Value Niche Matrix & Diversity Sampler Engine for Indonesian B2B Lead Hunting.
Replaces static single-category scans with weighted round-robin rotation across high-ticket niches:
- B2B Distributors & Industrial Suppliers (High AOV, large margin, catalog requirements)
- Specialized Freight & Heavy Logistics (Cold chain reefer, tronton, project cargo)
- Commercial & Industrial Contractors (HVAC, epoxy lantai pabrik, interior kantor, baja gudang)
- Healthcare & Aesthetics Specialists (Dental clinics, aesthetic clinics, diagnostic labs)
- Professional B2B Services (ISO certification, AMDAL, tax/accounting, calibration)

Includes negative keyword filtering to strictly exclude low-ticket retail (toko bangunan, sembako, warung).
"""

import random
from typing import Dict, List, Optional

EXCLUDED_RETAIL_KEYWORDS = [
    "bahan bangunan", "toko material", "material bangunan", "toko bangunan",
    "toko kelontong", "sembako", "warung", "toko atk", "toko pulsa",
    "counter hp", "laundry kiloan", "fotocopy", "foto copy", "warung madura",
    "toko pakan", "toko burung", "toko serba ada"
]

HIGH_VALUE_NICHE_TAXONOMY = {
    "b2b_distributor": {
        "title": "B2B Distributor & Industrial Supplier",
        "description": "Distributor bahan baku, packaging, dan perlengkapan industri dengan nilai transaksi tinggi.",
        "sub_niches": [
            "distributor packaging karton box",
            "supplier bahan kimia industri",
            "distributor plastik kemasan pabrik",
            "supplier alat teknik industri safety",
            "distributor genset industri",
            "distributor pipa hdpe dan fitting",
            "supplier baut dan mur industri",
            "distributor frozen food horeka"
        ],
        "target_cities": ["cikarang", "surabaya", "karawang", "semarang", "sidoarjo", "medan", "bekasi"]
    },
    "ekspedisi_spesialis": {
        "title": "Logistik & Ekspedisi B2B Spesialis",
        "description": "Perusahaan kargo dan logistik armada berat untuk pengiriman antarpulau dan rantai dingin.",
        "sub_niches": [
            "sewa truk reefer pendingin",
            "ekspedisi surabaya makassar",
            "jasa tronton fuso trailer",
            "kargo alat berat balikpapan",
            "ekspedisi kapal laut fcl lcl",
            "jasa sewa truk wingbox",
            "ekspedisi jakarta pontianak",
            "jasa kargo proyek batam"
        ],
        "target_cities": ["surabaya", "balikpapan", "makassar", "batam", "jakarta utara", "semarang", "pontianak"]
    },
    "kontraktor_komersial": {
        "title": "Kontraktor Komersial & Industri",
        "description": "Jasa kontraktor spesialis pabrik, gedung, dan fasilitas komersial beranggaran besar.",
        "sub_niches": [
            "kontraktor hvac tata udara",
            "jasa epoxy lantai pabrik",
            "kontraktor interior kantor",
            "fabrikasi konstruksi baja gudang",
            "kontraktor fire protection hydrant",
            "jasa waterproofing membran bakar",
            "kontraktor mekanikal elektrikal gedung",
            "jasa renovasi pabrik dan gudang"
        ],
        "target_cities": ["cikarang", "bekasi", "tangerang", "surabaya", "sidoarjo", "bandung", "karawang"]
    },
    "klinik_spesialis": {
        "title": "Klinik & Laboratorium Spesialis",
        "description": "Fasilitas kesehatan swasta bernilai per-kunjungan tinggi yang membutuhkan web profil profesional.",
        "sub_niches": [
            "klinik estetika kecantikan",
            "klinik gigi spesialis dental care",
            "laboratorium klinik diagnostik swasta",
            "klinik fisioterapi rehabilitasi medik",
            "klinik mata spesialis",
            "klinik fertilitas dan ivf"
        ],
        "target_cities": ["surabaya", "bandung", "medan", "jakarta selatan", "semarang", "makassar", "denpasar"]
    },
    "layanan_profesional": {
        "title": "Layanan Korporat & Konsultan B2B",
        "description": "Jasa konsultasi perizinan, sertifikasi, perpajakan, dan inspeksi berstandar nasional.",
        "sub_niches": [
            "konsultan sertifikasi iso smk3",
            "konsultan amdal lingkungan hidup",
            "kantor konsultan pajak akuntansi",
            "jasa kalibrasi alat industri",
            "jasa surveyor dan audit teknik",
            "kantor konsultan hukum bisnis"
        ],
        "target_cities": ["jakarta pusat", "surabaya", "batam", "balikkpapan", "bandung", "medan"]
    }
}


class NicheMatrix:
    """
    Orchestrates diverse, high-value keyword rotation and negative filtering.
    """

    @staticmethod
    def is_excluded_business(title: str, category_str: str = "") -> bool:
        """
        Checks whether a business title or category matches low-ticket excluded retail terms.
        """
        combined = f"{title or ''} {category_str or ''}".lower()
        for kw in EXCLUDED_RETAIL_KEYWORDS:
            if kw in combined:
                return True
        return False

    @staticmethod
    def get_diverse_query_batch(
        limit: int = 5,
        target_category: Optional[str] = None,
        shuffle: bool = True
    ) -> List[str]:
        """
        Generates a round-robin interleaved batch of high-value search queries.
        Guarantees that a batch of `limit` items spans multiple different niches and cities.
        """
        categories = list(HIGH_VALUE_NICHE_TAXONOMY.keys())
        if target_category and target_category in HIGH_VALUE_NICHE_TAXONOMY:
            categories = [target_category]

        queries = []
        # Cycle through categories in round-robin fashion
        cat_idx = 0
        used_combinations = set()

        max_attempts = limit * 6
        attempts = 0

        while len(queries) < limit and attempts < max_attempts:
            attempts += 1
            cat_key = categories[cat_idx % len(categories)]
            cat_idx += 1

            cat_info = HIGH_VALUE_NICHE_TAXONOMY[cat_key]
            sub_niche = random.choice(cat_info["sub_niches"])
            city = random.choice(cat_info["target_cities"])

            # Avoid redundant city if sub_niche already contains a city name
            if any(c in sub_niche for c in ["surabaya", "balikpapan", "jakarta", "batam", "makassar", "pontianak"]):
                query = sub_niche
            else:
                query = f"{sub_niche} {city}"

            if query not in used_combinations and not NicheMatrix.is_excluded_business(query):
                used_combinations.add(query)
                queries.append(query)

        return queries

    @staticmethod
    def get_dork_queries_for_track_b(
        limit: int = 5,
        target_category: Optional[str] = None
    ) -> List[str]:
        """
        Generates targeted Indonesian SERP dorks designed to uncover outdated B2B websites (.co.id / .id).
        """
        dork_templates = [
            'site:.co.id "{niche}" "hubungi kami" "081"',
            'site:.co.id "{niche}" "Copyright 201" -inurl:blog',
            'site:.id "distributor" "{niche}" "telepon"',
            'site:.co.id intext:"profil perusahaan" "{niche}" "alamat"',
            'site:.co.id "{niche}" "produk kami" inurl:index.php'
        ]

        categories = list(HIGH_VALUE_NICHE_TAXONOMY.keys())
        if target_category and target_category in HIGH_VALUE_NICHE_TAXONOMY:
            categories = [target_category]

        dorks = []
        for _ in range(limit):
            cat_key = random.choice(categories)
            cat_info = HIGH_VALUE_NICHE_TAXONOMY[cat_key]
            niche_raw = random.choice(cat_info["sub_niches"])
            # Extract core keyword from sub_niche
            core_keyword = niche_raw.replace("distributor ", "").replace("supplier ", "").replace("kontraktor ", "").replace("jasa ", "")
            tpl = random.choice(dork_templates)
            dork = tpl.format(niche=core_keyword)
            if dork not in dorks:
                dorks.append(dork)

        return dorks
