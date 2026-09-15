import pytest
from pipeline.researcher.ui_ux_integrator import UIUXProMaxIntegrator
from pipeline.style_analyzer import WebsiteStyleAnalyzer


def test_ui_ux_pro_max_database_loading():
    """Verify all 11+ UI/UX Pro Max databases are loaded with positive record counts."""
    u = UIUXProMaxIntegrator()
    assert len(u.products) >= 190
    assert len(u.colors) >= 190
    assert len(u.styles) >= 80
    assert len(u.typography) >= 70
    assert len(u.landing) >= 30
    assert len(u.ui_reasoning) >= 190
    assert len(u.ux_guidelines) >= 100
    assert len(u.motion) >= 15
    assert len(u.icons) >= 100
    assert len(u.charts) >= 20
    assert len(u.google_fonts) >= 1900


def test_design_system_resolution_construction():
    u = UIUXProMaxIntegrator()
    ds = u.resolve_design_system("Toko Bangunan Sumber Mufakat", "Toko Bahan Bangunan")
    assert ds["product_type"] == "Construction/Architecture"
    assert "Rubik" in ds["typography"]["heading_font"]
    assert "Plus Jakarta Sans" in ds["typography"]["body_font"]
    assert ds["colors"]["primary"].startswith("#")
    assert ds["colors"]["accent"].startswith("#")
    assert ds["colors"]["wa_green"] == "#059669"
    assert "2D-only layouts" in ds["anti_patterns"]


def test_design_system_resolution_pharmacy():
    u = UIUXProMaxIntegrator()
    ds = u.resolve_design_system("Apotek K-24 Palangka Raya", "Apotek")
    assert ds["product_type"] in ["Pharmacy/Drug Store", "Medical Clinic"]
    assert ds["typography"]["heading_font"] == "Inter"


def test_rating_sanitizer():
    u = UIUXProMaxIntegrator()
    # Test messy comma + count string
    s1 = u.sanitize_ratings("4,4 (73)", 73)
    assert s1["rating_float"] == 4.4
    assert s1["review_count_int"] == 73
    assert "4.4 / 5.0" in s1["trust_badge_text"]
    assert "73+ Ulasan" in s1["trust_badge_text"]

    # Test clean float
    s2 = u.sanitize_ratings("5.0 (10)", 10)
    assert s2["rating_float"] == 5.0
    assert s2["review_count_int"] == 10

    # Test empty string fallback
    s3 = u.sanitize_ratings("", 0)
    assert s3["rating_float"] == 4.5
    assert s3["rating_display"] == "Terverifikasi"


def test_svg_vector_engine_zero_emojis():
    u = UIUXProMaxIntegrator()
    icon_slugs = ["building", "steel-beam", "pipe-plumbing", "pill", "wrench", "car", "scissors", "coffee", "package"]
    for slug in icon_slugs:
        svg = u.get_svg_icon(slug, size=24, cls="test-svg")
        assert svg.startswith("<svg")
        assert svg.endswith("</svg>")
        assert 'class="test-svg"' in svg
        # Ensure no raw emojis
        assert not any(ord(char) > 0x1F000 for char in svg)


def test_style_analyzer_track_b_integration():
    sa = WebsiteStyleAnalyzer()
    res = sa.analyze("<html><body><h1>Test</h1></body></html>", {"brand_name": "Toko Bangunan Sumber Mufakat", "category": "Material Konstruksi"})
    profile = res["ui_ux_pro_max_profile"]
    assert profile["product_type"] == "Construction/Architecture"
    assert "Rubik" in profile["typography_pairing"]
    assert res["modernization_plan"]["modernized_tokens"]["wa_green"] == "#059669"
