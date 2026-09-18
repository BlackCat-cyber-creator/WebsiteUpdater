"""
Autonomous Gemini AI Business Intelligence & UI/UX Pro Max Synthesizer.
Uses Google Gemini API to analyze any Indonesian SME from Google Maps (regardless of niche),
and dynamically synthesizes deep, trade-specific business profiles, concrete products/services,
about narratives, competitive advantages, and FAQs matching ui-ux-pro-max design intelligence.
"""

import os
import json
import re
import hashlib
import socket
import urllib.request
import urllib.parse
import urllib.error
from typing import Dict, Any, Optional, Tuple

try:
    import dotenv
    dotenv.load_dotenv()
except Exception:
    pass

OFFICIAL_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash"
]


class GeminiBusinessSynthesizer:
    _quota_exhausted: bool = False
    _cache_file: str = os.path.normpath(os.path.join(os.path.dirname(__file__), '..', 'data', 'gemini_cache.json'))
    _cache: Optional[Dict[str, Any]] = None
    _last_api_call_ts: float = 0.0
    _min_call_interval: float = 1.5

    def __init__(self, api_key: Optional[str] = None):
        self._explicit_key = api_key

    @classmethod
    def reset_quota_state(cls) -> None:
        """Resets the quota exhausted flag, enabling API attempts again."""
        cls._quota_exhausted = False

    @classmethod
    def mark_quota_exhausted(cls) -> None:
        """Sets the quota exhausted flag to immediately bypass API calls in this session."""
        cls._quota_exhausted = True

    @classmethod
    def _enforce_rate_limit(cls) -> None:
        """Paces API calls to ensure RPM never exceeds Google's free tier threshold."""
        import time
        now = time.time()
        elapsed = now - cls._last_api_call_ts
        if elapsed < cls._min_call_interval:
            time.sleep(cls._min_call_interval - elapsed)
        cls._last_api_call_ts = time.time()

    @property
    def preferred_model(self) -> str:
        try:
            import dotenv
            dotenv.load_dotenv(override=True)
        except Exception:
            pass
        model = os.environ.get("GEMINI_MODEL", "gemini-3.8-flash").strip()
        return model if model else "gemini-3.8-flash"

    @property
    def api_key(self) -> str:
        if self._explicit_key:
            return self._explicit_key
        try:
            import dotenv
            dotenv.load_dotenv(override=True)
        except Exception:
            pass
        return os.environ.get("GEMINI_API_KEY", "").strip()

    def is_available(self) -> bool:
        """Returns True if an API key is present and quota has not been exhausted."""
        if self._quota_exhausted:
            return False
        return bool(self.api_key)

    @classmethod
    def _compute_hashes(cls, business_name: str, category: str, city: str) -> Tuple[str, Optional[str]]:
        """Generates deterministic hashes for business-level and niche-level caching."""
        clean_name = re.split(r'[|\-–•—]', business_name or "")[0].strip().lower()
        norm_cat = (category or "").strip().lower()
        norm_city = (city or "lokal").strip().lower()

        b_key = f"{clean_name}|{norm_cat}|{norm_city}"
        b_hash = hashlib.md5(b_key.encode("utf-8")).hexdigest()[:16]

        n_hash = None
        if norm_cat:
            n_key = f"{norm_cat}|{norm_city}"
            n_hash = hashlib.md5(n_key.encode("utf-8")).hexdigest()[:16]

        return b_hash, n_hash

    def _ensure_cache_loaded(self) -> Dict[str, Any]:
        """Loads the disk cache JSON into memory if not already cached in-memory."""
        if GeminiBusinessSynthesizer._cache is not None:
            return GeminiBusinessSynthesizer._cache
        try:
            if os.path.exists(self._cache_file):
                with open(self._cache_file, "r", encoding="utf-8") as f:
                    GeminiBusinessSynthesizer._cache = json.load(f)
            else:
                GeminiBusinessSynthesizer._cache = {}
        except Exception:
            GeminiBusinessSynthesizer._cache = {}
        return GeminiBusinessSynthesizer._cache

    def get_from_cache(
        self,
        business_name: str,
        category: str = "",
        city: str = ""
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieves cached synthesis profile by business hash, or adapts
        a cached similar niche synthesis in the same city.
        """
        cache = self._ensure_cache_loaded()
        b_hash, n_hash = self._compute_hashes(business_name, category, city)

        # 1. Exact business hash hit
        if b_hash in cache:
            entry = dict(cache[b_hash])
            if entry.get("services") and len(entry["services"]) >= 3:
                model_info = entry.get("model_used", "cached")
                entry["source"] = f"gemini_ai_cache ({model_info})"
                return entry

        # 2. Similar niche/category in the same city hit
        if n_hash and n_hash in cache:
            template = dict(cache[n_hash])
            if template.get("services") and len(template["services"]) >= 3:
                clean_name = re.split(r'[|\-–•—]', business_name)[0].strip()
                effective_city = city or "Lokal & Sekitarnya"
                old_name = template.get("business_name", "")

                adapted = dict(template)
                adapted["business_name"] = clean_name
                adapted["city"] = effective_city
                if old_name and clean_name:
                    for field in ["headline", "tagline", "about_p1", "about_p2"]:
                        if field in adapted and isinstance(adapted[field], str):
                            adapted[field] = adapted[field].replace(old_name, clean_name)
                model_info = template.get("model_used", "cached")
                adapted["source"] = f"gemini_ai_cache_niche ({model_info})"
                return adapted

        return None

    def save_to_cache(
        self,
        business_name: str,
        category: str,
        city: str,
        data: Dict[str, Any],
        model_name: str = ""
    ) -> None:
        """Saves synthesized profile to disk cache under business and niche hashes."""
        try:
            cache = self._ensure_cache_loaded()
            b_hash, n_hash = self._compute_hashes(business_name, category, city)

            save_payload = dict(data)
            save_payload["model_used"] = model_name

            cache[b_hash] = save_payload
            if n_hash:
                cache[n_hash] = save_payload

            os.makedirs(os.path.dirname(self._cache_file), exist_ok=True)
            with open(self._cache_file, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
        except Exception:
            # Disk caching should never halt the execution pipeline
            pass

    def synthesize(
        self,
        business_name: str,
        category: str = "",
        address: str = "",
        city: str = "",
        rating: str = "",
        review_count: int = 0,
        query: str = ""
    ) -> Optional[Dict[str, Any]]:
        """
        Calls Google Gemini API with structured JSON output to produce a
        complete, rich, sector-specific UI/UX Pro Max profile for ANY Indonesian business.
        Uses Disk Caching and protects against 429/404/timeouts with seamless zero-delay fallback.
        """
        if not self.is_available():
            return None

        clean_name = re.split(r'[|\-–•—]', business_name)[0].strip()
        effective_city = city or "Lokal & Sekitarnya"

        # UI/UX Pro Max Full Database Context & Anti-Patterns
        from pipeline.researcher.ui_ux_integrator import UIUXProMaxIntegrator
        ui_ux = UIUXProMaxIntegrator()
        sanitized = ui_ux.sanitize_ratings(rating, review_count)
        rating_display = sanitized["rating_display"]
        actual_rating_str = sanitized["metric_rating_text"]
        reviews_display = sanitized["reviews_display"]
        ui_ctx = ui_ux.get_synthesis_context(clean_name, category, query)

        # 1. Check Disk Cache first to save API quota
        cached = self.get_from_cache(clean_name, category, effective_city)
        if cached:
            print(f"    [+] [Gemini Cache] Hit disk cache untuk '{clean_name}' (Hemat kuota API).")
            cached["rating_display"] = rating_display
            cached["reviews_display"] = reviews_display
            if cached.get("metrics") and len(cached["metrics"]) > 0:
                cached["metrics"][0] = {"val": actual_rating_str, "lbl": f"Google Maps ({reviews_display})"}
            return cached

        system_instruction = (
            "Anda adalah Lead UI/UX Designer dan Senior Web Architect dari tim konsultan pengembangan website profesional. "
            "Tugas Anda adalah membuat data konten website landing page untuk UKM Indonesia agar terlihat sangat profesional, "
            "konkret, meyakinkan (high-converting), berorientasi konversi WhatsApp, dan 100% relevan dengan industrinya.\n\n"
            f"{ui_ctx['prompt_injection']}\n\n"
            "PANDUAN KETAT & ANTI-KLONING:\n"
            "1. BLACKLIST KLISE: DILARANG KERAS menggunakan frasa hampa seperti 'Layanan Utama', 'Pelayanan Terbaik', 'Harga Bersaing', 'Solusi Lengkap', 'Pilihan Terbaik', 'Kualitas Terjamin'.\n"
            "2. SPESIFIK & KONKRET: Tulis nama produk fisik riil, merek terkenal di Indonesia (misal Semen Gresik, Rucika, Omron, Blackmores, Daikin, LG, Royal Canin, dll.), varian ukuran/tipe, dan spesifikasi teknis.\n"
            "3. TEPAT 6 LAYANAN / PRODUK: Tiap item WAJIB memiliki field 'items' berisi 3-4 butir checklist konkret dengan spesifikasi jelas, bukan deskripsi umum.\n"
            "4. REVIEW PERSONA ASLI: Tulis 3 ulasan pelanggan dengan nama realistis Indonesia dan badge profesi/kebutuhan yang sangat relevan dengan industri bisnis (misal untuk Apotek: 'dr. Hendrawan (Dokter Praktik Mandiri)', untuk Toko Bangunan: 'Bambang P. (Mandor Proyek)', untuk Salon: 'Nadia (Member Perawatan)', untuk Kuliner: 'Fitri (Panitia Acara Kantor)'). JANGAN gunakan nama generic berulang.\n"
            "5. METRIK DAN REPUTASI JUJUR: Sesuaikan metrik dengan data Google Maps riil yang diberikan (rating dan jumlah ulasan). Jangan hardcode angka 5.0 jika rating riil berbeda.\n"
            "6. Output HARUS dalam format JSON murni sesuai schema yang diminta."
        )

        user_prompt = f"""
Profil Bisnis Target:
- Nama Bisnis: {clean_name}
- Kategori/Industri: {category or 'Bisnis Lokal'}
- Profil Industri UI/UX Pro Max: {ui_ctx['product_type']}
- Alamat/Wilayah: {address or effective_city}
- Kota: {effective_city}
- Rating Google Maps: {actual_rating_str} ({reviews_display})
- Query Penelusuran: {query}

Hasilkan JSON dengan struktur berikut:
{{
  "trade_name": "Label kategori formal toko/usaha (contoh: Toko Bahan Bangunan & Material Proyek, Apotek & Alat Kesehatan Resmi, dsb)",
  "headline": "Headline konversi yang kuat dan spesifik (maksimal 10-12 kata)",
  "tagline": "Subheadline / proposisi nilai yang menjelaskan produk utama dan layanan antar/konsultasi",
  "about_p1": "Paragraf 1 tentang profil bisnis, spesialisasi, dan komitmen melayani pelanggan di kota setempat",
  "about_p2": "Paragraf 2 tentang keandalan stok, transparansi harga, atau profesionalisme tenaga kerja",
  "services": [
    {{
      "title": "Nama Layanan/Produk Konkret 1",
      "desc": "Penjelasan detail produk, varian, dan spesifikasi riil",
      "icon": "Slug icon (drumstick / fish / cooking-pot / utensils / wheat / snowflake / flame / store / activity / bone / first-aid / pill / stethoscope / building / steel-beam / pipe-plumbing / paint-bucket / roof-home / tiles-floor / wrench / car / scissors / sparkles / coffee / shopping-bag / package)",
      "items": ["Item/spesifikasi 1", "Item/spesifikasi 2", "Item/spesifikasi 3"]
    }},
    {{
      "title": "Nama Layanan/Produk Konkret 2",
      "desc": "Penjelasan detail produk, varian, dan spesifikasi riil",
      "icon": "Slug icon (drumstick / fish / cooking-pot / utensils / wheat / snowflake / flame / store / activity / bone / first-aid / pill / stethoscope / building / steel-beam / pipe-plumbing / paint-bucket / roof-home / tiles-floor / wrench / car / scissors / sparkles / coffee / shopping-bag / package)",
      "items": ["Item/spesifikasi 1", "Item/spesifikasi 2", "Item/spesifikasi 3"]
    }},
    {{
      "title": "Nama Layanan/Produk Konkret 3",
      "desc": "Penjelasan detail produk, varian, dan spesifikasi riil",
      "icon": "Slug icon (drumstick / fish / cooking-pot / utensils / wheat / snowflake / flame / store / activity / bone / first-aid / pill / stethoscope / building / steel-beam / pipe-plumbing / paint-bucket / roof-home / tiles-floor / wrench / car / scissors / sparkles / coffee / shopping-bag / package)",
      "items": ["Item/spesifikasi 1", "Item/spesifikasi 2", "Item/spesifikasi 3"]
    }},
    {{
      "title": "Nama Layanan/Produk Konkret 4",
      "desc": "Penjelasan detail produk, varian, dan spesifikasi riil",
      "icon": "Slug icon (drumstick / fish / cooking-pot / utensils / wheat / snowflake / flame / store / activity / bone / first-aid / pill / stethoscope / building / steel-beam / pipe-plumbing / paint-bucket / roof-home / tiles-floor / wrench / car / scissors / sparkles / coffee / shopping-bag / package)",
      "items": ["Item/spesifikasi 1", "Item/spesifikasi 2", "Item/spesifikasi 3"]
    }},
    {{
      "title": "Nama Layanan/Produk Konkret 5",
      "desc": "Penjelasan detail produk, varian, dan spesifikasi riil",
      "icon": "Slug icon (drumstick / fish / cooking-pot / utensils / wheat / snowflake / flame / store / activity / bone / first-aid / pill / stethoscope / building / steel-beam / pipe-plumbing / paint-bucket / roof-home / tiles-floor / wrench / car / scissors / sparkles / coffee / shopping-bag / package)",
      "items": ["Item/spesifikasi 1", "Item/spesifikasi 2", "Item/spesifikasi 3"]
    }},
    {{
      "title": "Nama Layanan/Produk Konkret 6",
      "desc": "Penjelasan detail produk, varian, dan spesifikasi riil",
      "icon": "Slug icon (drumstick / fish / cooking-pot / utensils / wheat / snowflake / flame / store / activity / bone / first-aid / pill / stethoscope / building / steel-beam / pipe-plumbing / paint-bucket / roof-home / tiles-floor / wrench / car / scissors / sparkles / coffee / shopping-bag / package)",
      "items": ["Item/spesifikasi 1", "Item/spesifikasi 2", "Item/spesifikasi 3"]
    }}
  ],
  "metrics": [
    {{"val": "{actual_rating_str}", "lbl": "Google Maps ({reviews_display})"}},
    {{"val": "Nilai metrik 2 (misal 1.500+ / 100% Asli)", "lbl": "Label metrik 2"}},
    {{"val": "Nilai metrik 3 (misal SNI Resmi / BPOM / Bergaransi)", "lbl": "Label metrik 3"}},
    {{"val": "Nilai metrik 4 (misal Siap Kirim / Teknisi Siaga)", "lbl": "Label metrik 4"}}
  ],
  "reviews": [
    {{"name": "Nama Pelanggan Spesifik 1", "badge": "Profesi / Kebutuhan Relevan Toko", "stars": "★★★★★", "text": "Ulasan pengalaman positif mendalam yang memuji kecepatan, keaslian barang, atau konsultasi..."}},
    {{"name": "Nama Pelanggan Spesifik 2", "badge": "Profesi / Kebutuhan Relevan Toko", "stars": "★★★★★", "text": "Ulasan pengalaman positif..."}},
    {{"name": "Nama Pelanggan Spesifik 3", "badge": "Profesi / Kebutuhan Relevan Toko", "stars": "★★★★★", "text": "Ulasan pengalaman positif..."}}
  ],
  "advantages": [
    {{"title": "Keunggulan Konkret 1", "desc": "Penjelasan konkret tanpa klise"}},
    {{"title": "Keunggulan Konkret 2", "desc": "Penjelasan konkret tanpa klise"}},
    {{"title": "Keunggulan Konkret 3", "desc": "Penjelasan konkret tanpa klise"}},
    {{"title": "Keunggulan Konkret 4", "desc": "Penjelasan konkret tanpa klise"}}
  ],
  "faqs": [
    {{"q": "Pertanyaan realistis 1 yang sering ditanya pembeli di WhatsApp?", "a": "Jawaban jelas dan solutif"}},
    {{"q": "Pertanyaan realistis 2?", "a": "Jawaban jelas dan solutif"}},
    {{"q": "Pertanyaan realistis 3?", "a": "Jawaban jelas dan solutif"}}
  ]
}}
"""

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": user_prompt}
                    ]
                }
            ],
            "systemInstruction": {
                "parts": [
                    {"text": system_instruction}
                ]
            },
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.7
            }
        }

        # Hierarchy: preferred model first (if specified and valid), then remaining official models
        candidate_models = []
        pref = self.preferred_model
        if pref:
            candidate_models.append(pref)
        for m in OFFICIAL_MODELS:
            if m not in candidate_models:
                candidate_models.append(m)

        had_quota_limit = False
        for model_name in candidate_models:
            endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}"
            try:
                self._enforce_rate_limit()
                req = urllib.request.Request(
                    endpoint,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=18) as resp:
                    resp_data = json.loads(resp.read().decode("utf-8"))

                candidates = resp_data.get("candidates", [])
                if not candidates:
                    continue

                content_parts = candidates[0].get("content", {}).get("parts", [])
                if not content_parts:
                    continue

                raw_json_str = ""
                for part in content_parts:
                    if "text" in part:
                        raw_json_str = part["text"].strip()
                        break
                if not raw_json_str:
                    continue

                data = json.loads(raw_json_str)

                # Validate mandatory structure
                if not data.get("services") or len(data["services"]) < 4:
                    continue

                services = data["services"][:6]
                service_options = [s.get("title", f"Layanan {i+1}") for i, s in enumerate(services)]

                # Honest metrics
                m_list = data.get("metrics")
                if not m_list or len(m_list) < 4:
                    metrics = [
                        {"val": actual_rating_str, "lbl": f"Google Maps ({reviews_display})"},
                        {"val": "100% Asli", "lbl": "Standar Mutu Terjamin"},
                        {"val": "Resmi", "lbl": "Pelayanan Terpercaya"},
                        {"val": "Hari Ini", "lbl": "Respon & Pengiriman Cepat"}
                    ]
                else:
                    metrics = [
                        {"val": actual_rating_str, "lbl": f"Google Maps ({reviews_display})"},
                        m_list[1],
                        m_list[2],
                        m_list[3]
                    ]

                result_profile = {
                    "business_name": clean_name,
                    "city": effective_city,
                    "trade_name": data.get("trade_name", category or "Penyedia Layanan Terpercaya"),
                    "headline": data.get("headline", f"Pusat Layanan {clean_name} Terpercaya di {effective_city}"),
                    "tagline": data.get("tagline", "Menyediakan produk dan layanan berkualitas dengan konsultasi langsung via WhatsApp."),
                    "about_p1": data.get("about_p1", f"{clean_name} adalah penyedia layanan terpercaya di {effective_city}."),
                    "about_p2": data.get("about_p2", "Kami mengutamakan kualitas, ketepatan waktu, dan kepuasan pelanggan."),
                    "services": services,
                    "metrics": metrics,
                    "reviews": data.get("reviews") or [],
                    "advantages": data.get("advantages", [
                        {"title": "Kualitas Terjamin", "desc": "Standar pengerjaan profesional dan bermutu tinggi."},
                        {"title": "Konsultasi Cepat", "desc": "Respon langsung via WhatsApp resmi kami."},
                        {"title": "Harga Transparan", "desc": "Estimasi biaya terbuka tanpa biaya tersembunyi."},
                        {"title": "Pelayanan Ramah", "desc": "Dukungan penuh untuk seluruh pelanggan setia."}
                    ]),
                    "faqs": data.get("faqs", [
                        {"q": "Bagaimana cara melakukan pemesanan?", "a": "Hubungi kami langsung via WhatsApp untuk konsultasi dan pemesanan cepat."},
                        {"q": "Apakah melayani pengiriman?", "a": "Ya, kami melayani pengiriman langsung ke alamat Anda."},
                        {"q": "Metode pembayaran apa saja yang didukung?", "a": "Kami menerima transfer bank dan pembayaran digital resmi."}
                    ]),
                    "service_options": service_options,
                    "rating_display": rating_display,
                    "reviews_display": reviews_display,
                    "operating_hours": "Senin - Sabtu: 08.00 - 17.00 WIB",
                    "source": f"gemini_ai ({model_name})"
                }

                # Save successful synthesis to Disk Cache
                self.save_to_cache(clean_name, category, effective_city, result_profile, model_name=model_name)
                return result_profile

            except urllib.error.HTTPError as he:
                error_body = ""
                try:
                    error_body = he.read().decode("utf-8")
                except Exception:
                    pass

                # Check HTTP 503 High Demand / Capacity Limits (Common during traffic peaks on 3.8-flash)
                if he.code == 503 or "high demand" in error_body.lower() or "capacity" in error_body.lower():
                    print(f"    [!] [Gemini API] Model '{model_name}' sedang padat / high-demand (503). Beralih instan ke model cadangan.")
                    continue

                # Check HTTP 429 ResourceExhausted / Per-Model Quota Limit (e.g. 3.8-flash free tier limit: 20/day)
                if he.code == 429 or "RESOURCE_EXHAUSTED" in error_body or "quota" in error_body.lower():
                    print(f"    [!] [Gemini API] Model '{model_name}' mencapai kuota (429 ResourceExhausted). Beralih ke model hierarki berikutnya.")
                    had_quota_limit = True
                    continue

                # Check HTTP 404 NotFound
                if he.code == 404 or "NOT_FOUND" in error_body:
                    print(f"    [!] [Gemini API] Model '{model_name}' tidak ditemukan (404 NotFound). Beralih ke model hierarki berikutnya.")
                    continue

                print(f"    [!] [Gemini API] HTTP Error {he.code} pada model '{model_name}'. Beralih ke model berikutnya.")
                continue

            except (urllib.error.URLError, TimeoutError, socket.timeout) as te:
                print(f"    [!] [Gemini API] Timeout / koneksi lambat pada model '{model_name}' ({te}). Beralih ke model berikutnya.")
                continue

            except Exception as e:
                print(f"    [!] [Gemini API] Error tak terduga pada model '{model_name}': {e}.")
                continue

        if had_quota_limit:
            GeminiBusinessSynthesizer.mark_quota_exhausted()
        print("    [!] [GeminiSynthesizer] Seluruh model AI tidak tersedia atau kuota habis. Seketika fallback ke Rule-Based Engine.")
        return None
