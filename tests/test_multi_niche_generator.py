import os
import re
import tempfile
from unittest.mock import patch
import pytest
from pipeline.site_generator import SiteGenerator
from pipeline.researcher.business_researcher import BusinessResearcher


def mock_research_business(self, business_name, category="", address="", phone="", rating="", review_count=0):
    return self._rule_based_synthesis(
        business_name=business_name,
        category=category,
        address=address,
        rating=rating,
        review_count=review_count
    )


@patch.object(BusinessResearcher, "research_business", mock_research_business)
def test_multi_niche_turnkey_generation_and_safeguards():
    sg = SiteGenerator()

    test_cases = [
        {
            "niche": "frozen_food",
            "business_name": "Lafarew Frozen Food Grosir Dan Eceran",
            "category": "Distributor Frozen Food",
            "address": "Jl. Raya Taman Suko Asri AA-9, Sukodono, Sidoarjo",
            "expected_form_name": "Nama Pemesan / Nama Usaha",
            "expected_img_present": True,
            "forbidden_words": ["pengerjaan terstandar mutu", "kontraktor", "mandor", "proyek ruko"],
            "expected_guarantee_keyword": "Rantai Dingin"
        },
        {
            "niche": "fisioterapi_klinik",
            "business_name": "Praktek Fisioterapi Spectrum",
            "category": "Klinik Fisioterapi",
            "address": "Jl. Ahmad Yani No. 12, Surabaya",
            "expected_form_name": "Nama Pasien",
            "expected_img_present": False,  # Should use clean SVG icons, no food stock photos
            "forbidden_words": ["kartonan", "grosir", "pengerjaan cor", "mandor"],
            "expected_guarantee_keyword": "Fisioterapis"
        },
        {
            "niche": "layanan_profesional",
            "business_name": "Kantor Hukum Adidarma & Partners",
            "category": "Advokat & Konsultan Hukum",
            "address": "Jl. Basuki Rahmat No. 45, Surabaya",
            "expected_form_name": "Nama Lengkap / Nama Perusahaan",
            "expected_img_present": False,
            "forbidden_words": ["pengerjaan", "kartonan", "grosir", "pasien"],
            "expected_guarantee_keyword": "Kerahasiaan"
        },
        {
            "niche": "jasa_teknik",
            "business_name": "Kurnia Mandiri Teknik Servis AC",
            "category": "Servis AC & Pendingin",
            "address": "Jl. Pahlawan No. 8, Sidoarjo",
            "expected_form_name": "Nama Pelanggan",
            "expected_img_present": False,
            "forbidden_words": ["kartonan", "pasien", "obat resmi", "resep dokter"],
            "expected_guarantee_keyword": "Teknisi"
        }
    ]

    for tc in test_cases:
        with tempfile.TemporaryDirectory() as tmpdir:
            site_dir = sg.generate_turnkey_site(
                business_name=tc["business_name"],
                category=tc["category"],
                phone="081234567890",
                address=tc["address"],
                rating="4.8",
                review_count=95,
                output_dir=tmpdir
            )

            html_file = os.path.join(site_dir, "index.html")
            assert os.path.exists(html_file), f"index.html not found in {site_dir}"

            with open(html_file, "r", encoding="utf-8") as f:
                content = f.read()

            # 1. Universal CSS & Token Integrity
            assert "--border-card:" in content, "Missing --border-card declaration in :root or dark mode"
            metric_css = re.search(r'\.metric-val\s*\{([^}]+)\}', content)
            assert metric_css and "font-family: 'Rubik'" not in metric_css.group(1), ".metric-val should use imported display font ('Outfit'), not orphan 'Rubik'"
            
            # Check zero duplicate base floating-wa-widget CSS (1 desktop + 1 mobile media hide)
            wa_css_matches = re.findall(r'\.floating-wa-widget\s*\{', content)
            assert len(wa_css_matches) == 2, f"Found {len(wa_css_matches)} .floating-wa-widget CSS blocks, expected 2 (1 base + 1 mobile hide)"

            # Check floating WA widget non-intrusive elements
            assert "wa-bubble-close" in content, "Missing close button on wa-bubble-prompt"
            assert "dismissWaBubble" in content, "Missing dismissWaBubble function"
            assert "initWaBubbleScroll" in content, "Missing auto-dismiss scroll listener"

            # 2. Form Niche Safeguards
            assert tc["expected_form_name"] in content, f"Expected form label '{tc['expected_form_name']}' in {tc['niche']}"

            # 3. Card Visual Layout Integrity
            if tc["expected_img_present"]:
                assert "catalog-card-image" in content, f"Expected card image for {tc['niche']}"
                assert "onerror=" in content, "Card image must have fail-safe onerror attribute"
                assert "aspect-ratio: 16 / 9" in content, "Card image must have explicit 16/9 aspect-ratio"
                assert "card-glass-badge" in content, "Expected floating glass badge on card image"
                assert "catalog-header-clean" in content, "Expected clean header without duplicate 50px icon box"
            else:
                assert "catalog-icon" in content, f"Service niche {tc['niche']} should retain clean SVG catalog-icon"

            # 4. Tone & Terminology Leak Prevention
            content_lower = content.lower()
            for forbidden in tc["forbidden_words"]:
                assert forbidden not in content_lower, f"Forbidden phrase '{forbidden}' leaked into {tc['niche']}"

            # 5. Guarantee / Review Quality
            assert tc["expected_guarantee_keyword"].lower() in content_lower, f"Expected guarantee keyword '{tc['expected_guarantee_keyword']}' in {tc['niche']}"
            assert "cs" not in re.findall(r'<div class="reviewer-avatar">(CS|QC|OP)</div>', content), "Robotic CS/QC/OP avatars must not appear"


@patch.object(BusinessResearcher, "research_business", mock_research_business)
def test_zero_undefined_css_variables_in_output():
    sg = SiteGenerator()
    with tempfile.TemporaryDirectory() as tmpdir:
        site_dir = sg.generate_turnkey_site(
            business_name="Test General Business",
            category="Toko Retail Modern",
            phone="08111111111",
            address="Jl. Pemuda No. 1, Surabaya",
            rating="4.9",
            review_count=50,
            output_dir=tmpdir
        )
        html_file = os.path.join(site_dir, "index.html")
        assert os.path.exists(html_file)
        with open(html_file, "r", encoding="utf-8") as f:
            content = f.read()

        root_vars = set(re.findall(r'(--[a-zA-Z0-9_-]+)\s*:', content))
        used_vars = set(re.findall(r'var\((--[a-zA-Z0-9_-]+)', content))
        missing = used_vars - root_vars
        assert not missing, f"Undefined CSS variables found in output HTML: {missing}"


@patch.object(BusinessResearcher, "research_business", mock_research_business)
def test_mobile_first_responsive_architecture():
    sg = SiteGenerator()
    with tempfile.TemporaryDirectory() as tmpdir:
        site_dir = sg.generate_turnkey_site(
            business_name="Lafarew Frozen Food Grosir Dan Eceran",
            category="Distributor Frozen Food",
            phone="081990111606",
            address="Jl. Raya Taman Suko Asri AA-9, Sukodono, Sidoarjo",
            output_dir=tmpdir
        )
        with open(os.path.join(site_dir, "index.html"), "r", encoding="utf-8") as f:
            html = f.read()

        # 1. Default Light Mode
        assert "const theme = savedTheme || 'light';" in html, "Default theme must be strictly light mode"
        assert 'data-theme="light"' in html, "Root html tag should default to light theme"

        # 2. Mobile App-like Navbar: Hide duplicate header WhatsApp button
        assert ".btn-header-wa" in html
        assert "display: none !important" in html, "Header WhatsApp button must be hidden on mobile to avoid duplication"

        # 3. Horizontal Scroll Snap Pills
        assert "scroll-snap-type: x mandatory" in html, "Pills wrap must have scroll-snap for mobile"
        assert "overflow-x: auto" in html, "Pills wrap must be horizontally scrollable on mobile"
        assert "scroll-snap-align: start" in html, "Filter pills must snap on scroll"

        # 4. Anti-Collapse Image Fallback
        assert "img-fallback-active" in html, "Card image must support graceful non-collapsing fallback"

        # 5. Mobile Safe Area Inset
        assert "env(safe-area-inset-bottom)" in html, "Mobile sticky bar must respect safe area insets"

        # 6. WCAG 2.5.5 Touch Target Compliance (min 44px)
        assert "min-height: 44px" in html, "Interactive elements on mobile must satisfy min 44px touch-target"
        assert ".theme-toggle-btn {\n        width: 44px;\n        height: 44px;" in html or "width: 44px" in html, "Theme toggle button must have min 44px touch target on mobile"

        # 7. iOS Safari Form Zoom Prevention (16px font-size)
        assert "font-size: 16px !important" in html, "Mobile inputs must use 16px font to prevent unwanted iOS auto-zoom"

        # 8. 2026 Catalog Conversion Recovery (Empty State & Tactile)
        assert "catalogEmptyState" in html, "Catalog must include real-time empty-state conversion rescue"
        assert "catalog-empty-state" in html, "Empty state CSS styling must be present"
        assert "btn-empty-wa" in html, "Empty state must include direct WhatsApp recovery CTA"
        assert "transform: scale(0.96)" in html, "Tactile tap animations must be declared in CSS"


@patch.object(BusinessResearcher, "research_business", mock_research_business)
def test_all_fourteen_niches_generation_and_leak_free():
    """Validates that all 14 niche sectors generate cleanly with zero niche leaks."""
    import json
    sg = SiteGenerator()
    themes_path = os.path.normpath(os.path.join(os.path.dirname(os.path.dirname(__file__)), "pipeline", "data", "niche_themes.json"))
    with open(themes_path, "r", encoding="utf-8") as f:
        niches = json.load(f)

    assert len(niches) >= 14, f"Expected at least 14 niches, found {len(niches)}"

    for niche_key, niche_data in niches.items():
        with tempfile.TemporaryDirectory() as tmpdir:
            site_dir = sg.generate_turnkey_site(
                business_name=f"Demo {niche_data['name']}",
                category=niche_data["name"],
                phone="081234567890",
                address="Jl. Raya Utama No. 12, Surabaya",
                rating="4.9",
                review_count=80,
                output_dir=tmpdir
            )
            html_file = os.path.join(site_dir, "index.html")
            assert os.path.exists(html_file), f"index.html failed to generate for {niche_key}"

            with open(html_file, "r", encoding="utf-8") as f:
                html = f.read().lower()

            # Zero Niche Leak Assertions
            strictly_no_stock_niches = ["fisioterapi_klinik", "layanan_profesional", "jasa_teknik", "edukasi"]
            if niche_key in strictly_no_stock_niches:
                assert "stok" not in html, f"Niche leak: 'stok' found in service niche {niche_key}"
            
            assert "keunggulan toko" not in html, f"Niche leak: 'keunggulan toko' leaked into {niche_key}"

            if niche_key in ["layanan_profesional", "fisioterapi_klinik", "kesehatan", "edukasi", "jasa_teknik"]:
                assert "ambil langsung di toko" not in html, f"Niche leak: 'ambil langsung di toko' leaked into {niche_key}"

            if niche_key not in ["frozen_food"]:
                assert "tanya harga & stok" not in html, f"Niche leak: hardcoded hero CTA leaked into {niche_key}"

            if niche_key in ["layanan_profesional", "fisioterapi_klinik", "kesehatan", "edukasi", "properti"]:
                assert "wilayah pengiriman" not in html, f"Niche leak: 'wilayah pengiriman' leaked into {niche_key}"

            # CRO & Empty State Check
            assert "catalogemptystate" in html, f"Catalog empty state missing in {niche_key}"

