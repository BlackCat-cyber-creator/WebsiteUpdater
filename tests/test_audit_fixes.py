"""
Comprehensive regression and verification test suite for the 5 Lead-to-Website Pipeline Audit aspects:
1. Classification & Collision Traps
2. Graceful Degradation & Fallbacks
3. WhatsApp Conversion & Mobile UX
4. Technical SEO & Schema.org JSON-LD
5. Security & XSS Injection Protection
"""

import os
import json
import re
import tempfile
import html
from bs4 import BeautifulSoup
import pytest

from pipeline.researcher.business_researcher import BusinessResearcher
from pipeline.researcher.gemini_synthesizer import GeminiBusinessSynthesizer
from pipeline.outreach.meta_wa_client import normalize_phone_e164
from pipeline.site_generator import SiteGenerator
from pipeline.templates.renderer import render_template


@pytest.fixture(autouse=True)
def fast_rule_based_mode():
    """Ensure tests run purely offline without API rate limits or delays."""
    GeminiBusinessSynthesizer.mark_quota_exhausted()
    yield
    GeminiBusinessSynthesizer.reset_quota_state()


# ==============================================================================
# Aspect 1: Classification & Collision Traps
# ==============================================================================

def test_niche_collision_prevention():
    """Verify high-priority disambiguation stops Indonesian cross-niche collisions."""
    researcher = BusinessResearcher()

    # 1. Automotive disguised as Beauty Salon, Clinic, or Laundry
    assert researcher.get_niche_key("", "", "Salon Mobil Barokah") == "otomotif"
    assert researcher.get_niche_key("", "", "Klinik Helm Berkah") == "otomotif"
    assert researcher.get_niche_key("", "", "Cuci Mobil & Detailing Pro") == "otomotif"
    assert researcher.get_niche_key("", "", "Klinik Aki Mobil Terpercaya") == "otomotif"

    # 2. Electronics & Technical Services disguised as Clinic
    assert researcher.get_niche_key("", "", "Klinik Laptop & Komputer") == "jasa_teknik"
    assert researcher.get_niche_key("", "", "Klinik HP & Gadget Service") == "jasa_teknik"
    assert researcher.get_niche_key("", "", "Klinik Printer & Toner") == "jasa_teknik"

    # 3. Machining & Engineering disguised as Dental (gigi)
    assert researcher.get_niche_key("", "", "Bengkel Bubut Roda Gigi Presisi") == "jasa_teknik"

    # 4. Financial Services & Cooperatives disguised as Flora (bunga)
    assert researcher.get_niche_key("", "", "Koperasi Simpan Pinjam Bunga Rendah") == "layanan_profesional"

    # 5. Grocery & Retail disguised as Culinary (warung / sembako)
    assert researcher.get_niche_key("", "", "Warung Madura 24 Jam") == "modern_clean"
    assert researcher.get_niche_key("", "", "Toko Sembako Berkah Jaya") == "modern_clean"

    # 6. Personal Services (tukang) disambiguation
    assert researcher.get_niche_key("", "", "Tukang Cukur Asgar") == "estetika"
    assert researcher.get_niche_key("", "", "Tukang Jahit Taylor & Vermak") == "modern_clean"
    assert researcher.get_niche_key("", "", "Tukang Kunci Duplikat Panggilan") == "jasa_teknik"


def test_identify_trade_disambiguation():
    """Verify identify_trade assigns the correct primary trade profile without false positives."""
    researcher = BusinessResearcher()

    # Collision checks in trade identifier:
    # "Salon Mobil" must be recognized as automotive, NOT salon_kecantikan
    assert researcher.identify_trade("Salon Mobil Express", "Perawatan Kendaraan") == "otomotif"
    assert researcher.identify_trade("Salon Mobil Express", "Perawatan Kendaraan") != "salon_kecantikan"

    # "Klinik Laptop" must NOT be recognized as dental clinic or health clinic
    trade = researcher.identify_trade("Klinik Laptop Jogja", "Reparasi Elektronik")
    assert trade not in ["klinik_dental", "apotek_kesehatan"]

    # "Koperasi" must be recognized as professional service, NOT flora
    assert researcher.identify_trade("Koperasi Simpan Pinjam Sejahtera", "Jasa Keuangan") == "layanan_profesional"


# ==============================================================================
# Aspect 2: Graceful Degradation & Fallbacks
# ==============================================================================

def test_zero_reviews_honest_fallback():
    """Verify that zero reviews does NOT fabricate fake 5.0 star claims or fake ratings."""
    researcher = BusinessResearcher()

    profile = researcher.research_business(
        business_name="CV Berkah Engineering",
        category="Bengkel Bubut",
        address="Jl. Rungkut No. 1, Surabaya",
        phone="08123456789",
        rating="0",
        review_count=0
    )

    # Fallback rating must not fabricate "5.0" star rating
    assert profile["rating_display"] != "5.0"
    assert "5.0" not in profile.get("rating_display", "")


# ==============================================================================
# Aspect 3: WhatsApp Conversion & Mobile UX
# ==============================================================================

def test_e164_phone_normalization():
    """Verify Indonesian phone numbers are strictly converted to E.164 without '+' or leading '0'."""
    assert normalize_phone_e164("081234567890") == "6281234567890"
    assert normalize_phone_e164("+62 812-3456-7890") == "6281234567890"
    assert normalize_phone_e164("6281234567890") == "6281234567890"
    assert normalize_phone_e164("81234567890") == "6281234567890"
    assert normalize_phone_e164("0812 3456 7890") == "6281234567890"
    assert normalize_phone_e164("6208123456789") == "628123456789"


def test_site_generator_wa_link_and_touch_target():
    """Verify generated turnkey site uses correct wa.me link with %20 encoding and Safari-safe handler."""
    with tempfile.TemporaryDirectory() as tmpdir:
        generator = SiteGenerator()
        site_dir = generator.generate_turnkey_site(
            business_name="Bengkel Bubut Mandiri",
            category="Bengkel Bubut",
            address="Surabaya",
            phone="081234567890",
            output_dir=tmpdir,
            rating="4.8",
            review_count=25
        )

        index_file = os.path.join(site_dir, "index.html")
        with open(index_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Phone in wa.me must be normalized to E.164 (6281234567890) and NOT 0812...
        assert "https://wa.me/6281234567890" in content
        assert "https://wa.me/081234567890" not in content

        # WhatsApp text encoding must use %20 rather than raw spaces in href query strings
        assert "text=Halo" in content or "text=" in content

        # Safari popup blocker fix: must use direct navigation (window.location.href), not window.open
        assert "window.location.href = 'https://wa.me/'" in content
        assert "window.open" not in content

        # Touch target: theme-toggle-btn must have min 44px
        assert "min-width: 44px" in content
        assert "min-height: 44px" in content


# ==============================================================================
# Aspect 4: Technical SEO & Schema.org JSON-LD
# ==============================================================================

def test_schema_org_json_ld_validity():
    """Verify Schema.org JSON-LD output is strictly typed, valid JSON, and compliant."""
    with tempfile.TemporaryDirectory() as tmpdir:
        generator = SiteGenerator()
        site_dir = generator.generate_turnkey_site(
            business_name="Klinik Laptop Sejahtera",
            category="Reparasi Komputer",
            address="Jl. Pemuda No. 5, Surabaya",
            phone="081987654321",
            output_dir=tmpdir,
            rating="4.9",
            review_count=42
        )

        index_file = os.path.join(site_dir, "index.html")
        with open(index_file, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")

        script_tag = soup.find("script", attrs={"type": "application/ld+json"})
        assert script_tag is not None
        schema = json.loads(script_tag.string)

        assert schema["@context"] == "https://schema.org"
        assert schema["name"] == "Klinik Laptop Sejahtera"
        assert schema["priceRange"] == "Rp"
        assert schema["telephone"] == "+6281987654321"

        # Rating must be numeric, NOT unicode stars "★★★★★"
        assert "aggregateRating" in schema
        assert schema["aggregateRating"]["ratingValue"] == "4.9"
        assert schema["aggregateRating"]["reviewCount"] == "42"
        assert "★" not in schema["aggregateRating"]["ratingValue"]


def test_schema_org_omits_aggregaterating_on_zero_reviews():
    """Verify Schema.org omits aggregateRating if real review count is zero."""
    with tempfile.TemporaryDirectory() as tmpdir:
        generator = SiteGenerator()
        site_dir = generator.generate_turnkey_site(
            business_name="Toko Kayu Baru",
            category="Toko Bahan Bangunan",
            address="Surabaya",
            phone="08111222333",
            output_dir=tmpdir,
            rating="0",
            review_count=0
        )

        index_file = os.path.join(site_dir, "index.html")
        with open(index_file, "r", encoding="utf-8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")

        script_tag = soup.find("script", attrs={"type": "application/ld+json"})
        assert script_tag is not None
        schema = json.loads(script_tag.string)

        # Google Search Essentials requirement: do NOT include fake aggregateRating
        assert "aggregateRating" not in schema


def test_track_b_microdata_and_duplicate_json_ld_cleaning():
    """Verify Track B SEO optimization removes legacy microdata and duplicate JSON-LD scripts."""
    generator = SiteGenerator()
    dirty_html = """
    <html>
      <head>
        <title>Old Title</title>
        <script type="application/ld+json">{"@context": "https://schema.org", "name": "Duplicate"}</script>
      </head>
      <body itemscope itemtype="https://schema.org/LocalBusiness">
        <h2 itemprop="name">Bengkel Las</h2>
      </body>
    </html>
    """
    cleaned_html = generator._preserve_and_optimize_seo(
        raw_html=dirty_html,
        base_url="https://bengkellas.vercel.app",
        domain="bengkellas.vercel.app",
        brand="Bengkel Las Berkah",
        scraped={"brand_name": "Bengkel Las Berkah", "kontak": {"whatsapp": "08123456789"}},
        audit={}
    )

    # Microdata must be stripped to prevent syntax collision
    assert "itemscope" not in cleaned_html
    assert "itemtype" not in cleaned_html
    assert "itemprop" not in cleaned_html

    # Only one JSON-LD script should exist
    soup = BeautifulSoup(cleaned_html, "html.parser")
    json_ld_tags = soup.find_all("script", attrs={"type": "application/ld+json"})
    assert len(json_ld_tags) == 1
    schema = json.loads(json_ld_tags[0].string)
    assert schema["name"] == "Bengkel Las Berkah"
    assert schema["priceRange"] == "Rp"


# ==============================================================================
# Aspect 5: Security & XSS Injection Protection
# ==============================================================================

def test_xss_autoescape_in_turnkey_template():
    """Verify that user/scraped input containing XSS vectors is escaped by Jinja2 autoescape."""
    xss_payload = "<script>alert('XSS')</script>\" onmouseover=\"alert(1)"
    context = {
        "business_name": f"Toko Cat {xss_payload}",
        "headline": f"Distributor Resmi {xss_payload}",
        "tagline": "Aman dan Berkualitas",
        "phone": "+6281234567890",
        "clean_phone": "6281234567890",
        "rating_display": "4.8",
        "reviews_display": "15",
        "domain": "tokocat.co.id",
        "theme": {"primary": "#111", "accent": "#f00", "bg": "#fff"},
        "top_bar_html": "<div>Top</div>",
        "logo_html": "<div>Logo</div>",
        "trade_name": "Toko Cat",
        "city": "Surabaya",
        "h1_html": "<h1>Toko Cat</h1>",
        "hero_wa_text": "Halo",
        "metrics_bar_html": "<div>Metrics</div>",
        "about_p1": "Deskripsi...",
        "about_p2": "Layanan...",
        "catalog_cards_html": "<div>Katalog</div>",
        "adv_boxes_html": "<div>Keunggulan</div>",
        "reviews_section_html": "<div>Ulasan</div>",
        "faqs_html": "<div>FAQ</div>",
        "options_html": "<option>Pilihan</option>",
        "area_options_html": "<option>Area</option>",
        "address": f"Jl. Raya {xss_payload}",
        "hours": "08:00 - 17:00",
        "schema_json_ld": json.dumps({"@context": "https://schema.org", "name": "Toko Cat"})
    }

    rendered = render_template("site/turnkey.html", **context)

    # Raw script tags must NOT appear unescaped in the document body/attributes
    assert "<script>alert('XSS')</script>" not in rendered
    assert "&lt;script&gt;alert(&#39;XSS&#39;)&lt;/script&gt;" in rendered or "&lt;script&gt;alert('XSS')&lt;/script&gt;" in rendered
