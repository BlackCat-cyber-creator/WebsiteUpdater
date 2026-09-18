"""
Tests for Frozen Food niche mapping, avatar initials sanitization,
and contractor leak prevention in the Website Updater pipeline.
"""

import pytest
import re
from pipeline.researcher.business_researcher import BusinessResearcher
from pipeline.site_generator import SiteGenerator


def test_frozen_food_trade_and_niche_identification():
    researcher = BusinessResearcher()
    business_name = "Lafarew Frozen Food Grosir Dan Eceran"
    
    trade = researcher.identify_trade(business_name, category="Distributor & Grosir Frozen Food")
    assert trade == "frozen_food", f"Expected 'frozen_food' trade, got '{trade}'"
    
    niche = researcher.get_niche_key(trade, "", business_name)
    assert niche == "frozen_food", f"Expected 'frozen_food' niche, got '{niche}'"


def test_reviewer_initials_sanitization():
    names_to_test = [
        ("Nadia (Ibu Rumah Tangga)", "NI"),
        ("dr. Budi Santoso", "DB"),
        ("CV. Sentosa Abadi", "CS"),
        ("Ibu Sari (Pemilik Catering)", "IS"),
        ("Maya", "MA"),
        ("   ", "PL"),
    ]
    
    for rname, expected in names_to_test:
        clean_words = [re.sub(r'[^A-Za-z0-9]', '', w) for w in rname.split() if re.sub(r'[^A-Za-z0-9]', '', w)]
        if len(clean_words) >= 2:
            rinitials = (clean_words[0][0] + clean_words[1][0]).upper()
        elif clean_words:
            rinitials = clean_words[0][:2].upper()
        else:
            rinitials = "PL"
        
        assert "(" not in rinitials, f"Initials should not contain '(': {rinitials}"
        assert rinitials == expected, f"Expected '{expected}', got '{rinitials}' for '{rname}'"


def test_frozen_food_rule_based_synthesis_no_contractor_leak():
    researcher = BusinessResearcher()
    profile = researcher._rule_based_synthesis(
        business_name="Lafarew Frozen Food Grosir Dan Eceran",
        category="Distributor Frozen Food",
        address="Jl. Raya Taman Suko Asri AA-9, Sukodono, Sidoarjo",
        rating="4.4",
        review_count=136
    )
    
    assert profile["trade_name"] == "Distributor & Grosir Frozen Food Resmi"
    assert "Pusat Grosir" in profile["headline"]
    assert "Sidoarjo" in profile["headline"]
    
    profile_text = str(profile).lower()
    assert "kontraktor" not in profile_text
    assert "mandor" not in profile_text
    assert "proyek" not in profile_text
    assert "pabrik manufaktur" not in profile_text
    assert "coa/msds" not in profile_text
    assert "bahan kimia" not in profile_text


def test_card_image_resolution():
    sg = SiteGenerator()
    img_sausage = sg._resolve_card_image("frozen_food", "Olahan Daging & Sosis Premium")
    assert img_sausage is not None
    assert "unsplash" in img_sausage
    
    img_fries = sg._resolve_card_image("frozen_food", "Kentang Olahan & Sayuran Beku")
    assert img_fries is not None
    assert "1576107232684" not in img_fries, "Should not use broken 404 image ID"
    assert "1573080496219" in img_fries, "Should use verified working 200 OK fries image"
    
    img_other = sg._resolve_card_image("konstruksi", "Besi Beton SNI")
    assert img_other is None
