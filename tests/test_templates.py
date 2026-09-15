import os
import json
import pytest
from pipeline.templates.renderer import render_template


def test_niche_themes_json_exists():
    """Verify that niche_themes.json exists and contains theme profiles."""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    themes_path = os.path.join(base_dir, "pipeline", "data", "niche_themes.json")
    assert os.path.exists(themes_path)

    with open(themes_path, "r", encoding="utf-8") as f:
        themes = json.load(f)

    assert isinstance(themes, dict)
    assert "kesehatan" in themes
    assert "konstruksi" in themes
    assert "kuliner" in themes
    assert "estetika" in themes


def test_render_turnkey_template():
    """Verify rendering turnkey.html using the Jinja2 engine."""
    context = {
        "business_name": "PT Sejahtera Cargo",
        "headline": "Solusi Ekspedisi Andal Terpercaya di Seluruh Indonesia",
        "tagline": "Kirim barang cepat, aman, dan bergaransi.",
        "phone": "+6281234567890",
        "clean_phone": "6281234567890",
        "rating_display": "4.9",
        "reviews_display": "120",
        "domain": "sejahteracargo.co.id",
        "theme": {
            "primary": "#0f2042",
            "accent": "#f59e0b",
            "bg": "#ffffff"
        },
        "top_bar_html": "<div>Top Bar</div>",
        "logo_html": "<div>Logo</div>",
        "trade_name": "Ekspedisi & Kargo",
        "city": "Surabaya",
        "h1_html": "<h1>Ekspedisi Surabaya</h1>",
        "hero_wa_text": "Halo+Sejahtera+Cargo",
        "metrics_bar_html": "<div>Metrics</div>",
        "about_p1": "Tentang perusahaan kami...",
        "about_p2": "Pengalaman melayani pelanggan...",
        "catalog_cards_html": "<div class='card'>Layanan Kargo</div>",
        "adv_boxes_html": "<div>Keunggulan</div>",
        "reviews_section_html": "<div>Testimoni Pelanggan</div>",
        "faqs_html": "<div>Pertanyaan Umum</div>",
        "options_html": "<option>Pilihan 1</option>",
        "area_options_html": "<option>Surabaya Pusat</option>",
        "address": "Jl. Perak No. 10, Surabaya",
        "hours": "Senin - Sabtu: 08.00 - 17.00"
    }

    rendered = render_template("site/turnkey.html", **context)
    assert "<!DOCTYPE html>" in rendered
    assert "PT Sejahtera Cargo" in rendered
    assert "Layanan Kargo" in rendered
    assert "sejahteracargo.co.id" in rendered
    assert "Jl. Perak No. 10, Surabaya" in rendered
