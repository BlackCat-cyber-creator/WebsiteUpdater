import os
import json
import tempfile
import urllib.error
from unittest.mock import patch, MagicMock
import pytest
from pipeline.researcher.gemini_synthesizer import GeminiBusinessSynthesizer, OFFICIAL_MODELS
from pipeline.researcher.business_researcher import BusinessResearcher


def test_official_model_hierarchy():
    """Verify that official model hierarchy matches latest 2026 specifications."""
    expected = ["gemini-3.8-flash", "gemini-3.6-flash", "gemini-3.5-flash"]
    assert OFFICIAL_MODELS == expected

    synth = GeminiBusinessSynthesizer()
    assert synth.preferred_model in OFFICIAL_MODELS or synth.preferred_model != ""


def test_disk_caching_mechanism(tmp_path):
    """Verify disk caching saves and returns results using business hash and niche adaptation."""
    cache_file = tmp_path / "test_gemini_cache.json"
    synth = GeminiBusinessSynthesizer()
    synth._cache_file = str(cache_file)
    GeminiBusinessSynthesizer._cache = None  # Reset in-memory cache

    # Save mock profile with complete services
    mock_profile = {
        "business_name": "Toko Bangunan Makmur",
        "city": "Surabaya",
        "trade_name": "Toko Bahan Bangunan",
        "headline": "Pusat Bahan Bangunan Terlengkap",
        "tagline": "Sedia aneka semen dan pasir",
        "about_p1": "Toko Bangunan Makmur berdiri sejak 2010.",
        "about_p2": "Melayani pengiriman cepat.",
        "services": [
            {"title": "Semen Portland", "desc": "Semen berkualitas", "icon": "building", "items": ["Item 1"]},
            {"title": "Besi Beton SNI", "desc": "Besi ulir dan polos", "icon": "steel", "items": ["Item 2"]},
            {"title": "Cat Tembok", "desc": "Cat tahan cuaca", "icon": "paint", "items": ["Item 3"]},
            {"title": "Pipa PVC", "desc": "Pipa berkualitas", "icon": "pipe", "items": ["Item 4"]}
        ],
        "metrics": [{"val": "4.8", "lbl": "Google Maps"}],
        "reviews": [{"name": "Pak Budi", "badge": "Mandor", "stars": "★★★★★", "text": "Bagus"}],
        "advantages": [{"title": "SNI", "desc": "Pasti asli"}],
        "faqs": [{"q": "Bisa kirim?", "a": "Bisa langsung kirim"}],
        "service_options": ["Semen Portland", "Besi Beton SNI", "Cat Tembok", "Pipa PVC"]
    }

    synth.save_to_cache(
        business_name="Toko Bangunan Makmur",
        category="Toko Bahan Bangunan",
        city="Surabaya",
        data=mock_profile,
        model_name="gemini-2.5-flash"
    )

    assert os.path.exists(str(cache_file))

    # 1. Exact match hit
    hit = synth.get_from_cache(
        business_name="Toko Bangunan Makmur",
        category="Toko Bahan Bangunan",
        city="Surabaya"
    )
    assert hit is not None
    assert hit["business_name"] == "Toko Bangunan Makmur"
    assert "gemini_ai_cache" in hit["source"]

    # 2. Similar niche in same city adaptation
    niche_hit = synth.get_from_cache(
        business_name="Toko Bangunan Sejahtera",
        category="Toko Bahan Bangunan",
        city="Surabaya"
    )
    assert niche_hit is not None
    assert niche_hit["business_name"] == "Toko Bangunan Sejahtera"
    assert "gemini_ai_cache_niche" in niche_hit["source"]

    # Reset cache state after test
    GeminiBusinessSynthesizer._cache = None


def test_resource_exhausted_429_zero_delay_fallback():
    """Verify that HTTP 429 / ResourceExhausted immediately sets quota_exhausted and returns None."""
    synth = GeminiBusinessSynthesizer(api_key="fake_test_key")
    synth.reset_quota_state()
    assert synth.is_available() is True

    # Mock HTTP 429 error
    err_fp = MagicMock()
    err_fp.read.return_value = b'{"error": {"code": 429, "status": "RESOURCE_EXHAUSTED", "message": "Quota exceeded"}}'
    http_429_err = urllib.error.HTTPError(
        url="https://api",
        code=429,
        msg="Too Many Requests",
        hdrs={},
        fp=err_fp
    )

    with patch("urllib.request.urlopen", side_effect=http_429_err):
        result = synth.synthesize(business_name="Apotek Sehat", city="Surabaya")
        assert result is None
        # Quota should now be permanently exhausted for this session
        assert synth.is_available() is False
        assert GeminiBusinessSynthesizer._quota_exhausted is True

        # Subsequent call should immediately return None without calling urlopen
        with patch("urllib.request.urlopen") as mock_open:
            result2 = synth.synthesize(business_name="Apotek Farma", city="Jakarta")
            assert result2 is None
            mock_open.assert_not_called()

    synth.reset_quota_state()


def test_model_not_found_404_cascade():
    """Verify that 404 NotFound skips to next candidate model without fatal crash."""
    synth = GeminiBusinessSynthesizer(api_key="fake_test_key")
    synth.reset_quota_state()

    err_fp = MagicMock()
    err_fp.read.return_value = b'{"error": {"code": 404, "status": "NOT_FOUND", "message": "Model not found"}}'
    http_404_err = urllib.error.HTTPError(
        url="https://api",
        code=404,
        msg="Not Found",
        hdrs={},
        fp=err_fp
    )

    with patch("urllib.request.urlopen", side_effect=http_404_err) as mock_open:
        result = synth.synthesize(business_name="Klinik Dental", city="Medan")
        assert result is None
        # All models in hierarchy were tried
        assert mock_open.call_count == len(OFFICIAL_MODELS)
        # 404 does NOT exhaust quota
        assert synth.is_available() is True


def test_business_researcher_rule_based_synthesis_method():
    """Verify that _rule_based_synthesis produces rich, concrete output directly."""
    researcher = BusinessResearcher()
    profile = researcher._rule_based_synthesis(
        business_name="Distributor Karton Cikarang",
        category="distributor packaging karton box",
        city="Cikarang",
        query="distributor packaging karton box cikarang"
    )

    assert isinstance(profile, dict)
    assert profile["business_name"] == "Distributor Karton Cikarang"
    assert "Distributor" in profile["trade_name"]
    assert len(profile["services"]) == 6
    assert len(profile["advantages"]) >= 3
    assert len(profile["faqs"]) >= 2
    assert "source" in profile
    assert "rule_based" in profile["source"]


def test_business_researcher_seamless_fallback_when_quota_exhausted():
    """Verify that research_business seamlessly falls back to _rule_based_synthesis when quota exhausted."""
    researcher = BusinessResearcher()
    GeminiBusinessSynthesizer.mark_quota_exhausted()

    profile = researcher.research_business(
        business_name="PT Logistik Reefer Nusantara",
        category="ekspedisi spesialis",
        address="Kawasan Industri Rungkut, Surabaya",
        phone="081234567890",
        rating="4.9",
        review_count=80,
        query="sewa truk reefer pendingin surabaya"
    )

    assert isinstance(profile, dict)
    assert profile["business_name"] == "PT Logistik Reefer Nusantara"
    assert profile["city"] == "Surabaya"
    assert "services" in profile
    assert len(profile["services"]) >= 4
    assert "source" in profile
    assert "rule_based" in profile["source"]

    GeminiBusinessSynthesizer.reset_quota_state()
