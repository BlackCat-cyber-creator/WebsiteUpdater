"""
Automated Playwright test suite for Agency Website.
Verifies desktop & mobile responsive layout, SEO metadata, dual pricing elements,
reseller partner section, and interactive WhatsApp click-to-chat links.
"""

import os
import pytest
from playwright.sync_api import sync_playwright

AGENCY_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "agency_website"))
INDEX_HTML = os.path.join(AGENCY_DIR, "index.html")

def get_html_url():
    return f"file:///{INDEX_HTML.replace(os.sep, '/')}"

def test_agency_website_desktop_layout():
    """Verify desktop responsive layout and crucial elements."""
    assert os.path.exists(INDEX_HTML), f"index.html must exist at {INDEX_HTML}"
    
    with sync_playwright() as p:
        browser = None
        for ch in ["msedge", "chrome", None]:
            try:
                browser = p.chromium.launch(channel=ch, headless=True)
                break
            except Exception:
                continue
        
        assert browser is not None, "Playwright browser could not be launched"
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()
        
        console_errors = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("pageerror", lambda err: console_errors.append(str(err)))
        
        page.goto(get_html_url(), wait_until="load")
        
        # 1. Title and SEO tags
        title = page.title()
        assert "Website Updater Studio" in title, f"Unexpected page title: {title}"
        
        # 2. Dual Pricing verification
        body_text = page.inner_text("body")
        assert "Rp 1.490.000" in body_text, "Flat pricing Rp 1.490.000 must be present on page"
        assert "Rp 99.000" in body_text, "Cloud pricing Rp 99.000 must be present on page"
        assert "$100" not in body_text, "Old $100 USD pricing must NOT be present"
        
        # 3. WhatsApp Closing Machine section
        assert "WhatsApp Closing Machine" in body_text, "WhatsApp Closing Machine section must be present"
        
        # 4. Kemitraan / Reseller section
        kemitraan = page.query_selector("#kemitraan")
        assert kemitraan is not None, "#kemitraan section must exist"
        assert "kemitraan reseller" in kemitraan.inner_text().lower()
        
        # 5. WhatsApp links
        wa_links = page.query_selector_all('a[href*="wa.me"]')
        assert len(wa_links) > 0, "At least one WhatsApp CTA link must exist"
        for link in wa_links:
            href = link.get_attribute("href")
            assert "6285128013767" in href, f"WhatsApp link {href} must point to official agency number"
        
        # 6. Policy pages existence
        for policy in ["delivery.html", "terms.html", "refund.html", "privacy.html"]:
            assert os.path.exists(os.path.join(AGENCY_DIR, policy)), f"{policy} must exist"
            
        assert len(console_errors) == 0, f"Page had console errors: {console_errors}"
        browser.close()

def test_agency_website_mobile_layout():
    """Verify mobile responsive layout on smartphone viewport."""
    with sync_playwright() as p:
        browser = None
        for ch in ["msedge", "chrome", None]:
            try:
                browser = p.chromium.launch(channel=ch, headless=True)
                break
            except Exception:
                continue
                
        assert browser is not None
        context = browser.new_context(
            viewport={"width": 375, "height": 812},
            is_mobile=True
        )
        page = context.new_page()
        page.goto(get_html_url(), wait_until="load")
        
        # Check hero visibility
        hero = page.query_selector("h1")
        assert hero is not None and hero.is_visible(), "Hero H1 must be visible on mobile"
        
        # Check pricing buttons and cards visible
        pricing_cards = page.query_selector_all(".price-card-hero")
        assert len(pricing_cards) >= 2, f"Expected 2 price cards, found {len(pricing_cards)}"
        
        browser.close()

def test_live_deployed_vercel_website():
    """Verify the live production deployment on Vercel responds with HTTP 200 and correct content."""
    live_url = "https://websiteupdater.vercel.app"
    with sync_playwright() as p:
        browser = None
        for ch in ["msedge", "chrome", None]:
            try:
                browser = p.chromium.launch(channel=ch, headless=True)
                break
            except Exception:
                continue
                
        assert browser is not None
        page = browser.new_page()
        resp = page.goto(live_url, wait_until="load", timeout=30000)
        assert resp is not None, "Failed to get response from live Vercel URL"
        assert resp.status == 200, f"Live URL returned non-200 status: {resp.status}"
        
        # Verify title & key texts
        assert "Website Updater Studio" in page.title()
        body = page.inner_text("body")
        assert "Rp 1.490.000" in body
        assert "Rp 99.000" in body
        assert "WhatsApp Closing Machine" in body
        
        browser.close()

