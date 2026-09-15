import os
import json
import pytest
from pipeline.researcher.business_researcher import BusinessResearcher


def test_trade_profiles_data_file_exists():
    """Verify that trade_profiles.json exists and is valid JSON."""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    profiles_path = os.path.join(base_dir, "pipeline", "data", "trade_profiles.json")
    assert os.path.exists(profiles_path)

    with open(profiles_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, dict)
    assert len(data) >= 10
    assert "toko_bangunan" in data
    assert "bengkel_las" in data
    assert "distributor_sembako" in data


def test_business_researcher_trade_profile_loading():
    """Verify that BusinessResearcher loads trade profiles on initialization."""
    researcher = BusinessResearcher()
    assert hasattr(researcher, "TRADE_PROFILES")
    assert len(researcher.TRADE_PROFILES) >= 10
    assert "toko_bangunan" in researcher.TRADE_PROFILES
    profile = researcher.TRADE_PROFILES["toko_bangunan"]
    assert "headline" in profile or "headlines" in profile
    assert "services" in profile
    assert len(profile["services"]) > 0


def test_business_researcher_rule_based_synthesis():
    """Verify that research_business produces a complete, rich profile without errors."""
    researcher = BusinessResearcher()
    # Force rule-based engine by marking synth unavailable in this test
    researcher.gemini_synth.mark_quota_exhausted()
    profile = researcher.research_business(
        business_name="Toko Bangunan Sumber Rejeki",
        category="Toko Bahan Bangunan",
        address="Jl. Raya Rungkut No. 45, Surabaya",
        phone="08123456789",
        rating="4.8",
        review_count=65
    )
    researcher.gemini_synth.reset_quota_state()

    assert isinstance(profile, dict)
    assert "headline" in profile
    assert "tagline" in profile
    assert "trade_name" in profile
    assert "services" in profile
    assert "advantages" in profile
    assert "faqs" in profile
    assert len(profile["services"]) >= 3
    assert len(profile["advantages"]) >= 3
    assert len(profile["faqs"]) >= 2
