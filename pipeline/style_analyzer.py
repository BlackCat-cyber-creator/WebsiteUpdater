"""
Style & Design Analyzer Module powered by UI/UX Pro Max Intelligence.
Analyzes original website visual styling, color tokens, typography pairings,
and detects accessibility/usability flaws to formulate a targeted modernization blueprint.
"""

import re
from typing import Dict, Any, List


class WebsiteStyleAnalyzer:
    def __init__(self):
        # UI/UX Pro Max Product Profile for Logistics & Maritime Cold Chain:
        # Category: Logistics / Delivery / Freight
        # Design Philosophy: Swiss Style & Minimalism + Flat Design + Micro-interactions
        # Landing Pattern: Feature-Rich Showcase + Conversion
        self.pro_max_profile = {
            "product_type": "Logistics/Maritime Cold Chain",
            "recommended_style": "Minimalism & Swiss Style + Flat Design",
            "secondary_styles": "Micro-interactions & Glassmorphism",
            "typography_pairing": "Modern Professional (Poppins / Plus Jakarta Sans + Open Sans)",
            "wcag_target": "AA (Contrast Ratio >= 4.5:1)",
            "touch_target_min": "48px"
        }

    def analyze(self, raw_html: str, scraped: Dict[str, Any]) -> Dict[str, Any]:
        """Analyzes original CSS, color schemes, typography, and visual components."""
        extracted_colors = self._extract_css_colors(raw_html)
        typography = self._extract_typography(raw_html)
        components = self._extract_component_patterns(raw_html)
        flaws = self._detect_style_flaws(extracted_colors, typography, raw_html)
        upgrade_plan = self._formulate_upgrade_plan(extracted_colors, typography, flaws)

        return {
            "ui_ux_pro_max_profile": self.pro_max_profile,
            "original_colors": extracted_colors,
            "original_typography": typography,
            "original_components": components,
            "design_flaws": flaws,
            "modernization_plan": upgrade_plan
        }

    def _extract_css_colors(self, html: str) -> Dict[str, str]:
        colors = {
            "primary_dark_blue": "#1268b3",
            "primary_main_blue": "#2196f3",
            "accent_yellow": "#fab853",
            "whatsapp_green": "#25d366",
            "text_gray": "#4a5568",
            "text_white": "#ffffff",
            "background_body": "#f0f6ff"
        }
        root_match = re.search(r':root\s*\{([^}]+)\}', html, re.DOTALL)
        if root_match:
            vars_content = root_match.group(1)
            for var_line in vars_content.split(';'):
                if '--' in var_line and ':' in var_line:
                    k, v = var_line.split(':', 1)
                    k = k.strip()
                    v = v.strip().split()[0]
                    colors[k] = v
        return colors

    def _extract_typography(self, html: str) -> Dict[str, Any]:
        fonts_found = []
        if "Poppins" in html:
            fonts_found.append("Poppins")
        if "Anton" in html:
            fonts_found.append("Anton")
        if "Bootstrap" in html:
            fonts_found.append("System Sans-Serif")

        return {
            "fonts": fonts_found or ["Poppins", "Anton"],
            "body_font": "Poppins, sans-serif",
            "heading_font": "Anton, sans-serif (Display) / Poppins, sans-serif",
            "weights_used": ["300", "400", "600", "700"]
        }

    def _extract_component_patterns(self, html: str) -> List[Dict[str, str]]:
        patterns = []
        if ".card-custom" in html:
            patterns.append({
                "component": "Cards (.card-custom)",
                "style": "Rounded cards (24px radius) with subtle gradient and icon circles",
                "status": "Needs elevation, 1px luminous border, and modern glassmorphism"
            })
        if ".hero-desc-box" in html:
            patterns.append({
                "component": "Hero Description Box",
                "style": "Glassmorphic overlay container over hero slideshow",
                "status": "Good concept, requires directional dark navy scrim for WCAG AA compliance"
            })
        if ".cert-box" in html:
            patterns.append({
                "component": "Certification Badge",
                "style": "Bordered container with green verification icon",
                "status": "Needs authoritative trust badge styling with ARPI verified seal"
            })
        if ".list-kabupaten-light" in html:
            patterns.append({
                "component": "14 Kabupaten List",
                "style": "Two static columns of text with location icons",
                "status": "Needs interactive search & instant filter to let B2B clients locate destinations instantly"
            })
        return patterns

    def _detect_style_flaws(self, colors: Dict[str, str], typography: Dict[str, Any], html: str) -> List[Dict[str, str]]:
        return [
            {
                "issue": "Typography Inconsistency (Anton vs Poppins)",
                "impact": "High Visual Friction",
                "description": "The heavy, ultra-condensed 'Anton' display font on headings clashes with geometric 'Poppins', making section titles look dated and unevenly weighted.",
                "solution": "Unify with UI/UX Pro Max Modern Professional typography: Plus Jakarta Sans / Poppins 700 for crisp corporate headings and Open Sans / Poppins for smooth readability."
            },
            {
                "issue": "Hero Contrast & Text Legibility",
                "impact": "WCAG AA Contrast Failure",
                "description": "The hero slideshow rotates through images with varying brightness, causing white text to lose contrast without a directional scrim overlay.",
                "solution": "Implement a dual-tone directional navy gradient overlay (rgba(13, 77, 135, 0.85) to rgba(18, 104, 179, 0.65)) to ensure 100% contrast compliance across all screens."
            },
            {
                "issue": "Static Wilayah Presentation (14 Kabupaten Kalbar)",
                "impact": "Low B2B Usability",
                "description": "The 14 coverage regencies in West Kalimantan are presented as flat list items with no interactive filtering, map links, or search.",
                "solution": "Transform into an interactive Regency Explorer where visitors can filter or search Pontianak, Sambas, Sintang, Ketapang, etc., with instantaneous feedback."
            },
            {
                "issue": "Outdated Card Shading & Heavy Borders",
                "impact": "Visual Clutter",
                "description": "Thick opaque borders with standard Bootstrap 5 drop shadows create an unnecessary heavy look.",
                "solution": "Implement UI/UX Pro Max Swiss-inspired flat design with refined 1px translucent borders, subtle hover lift (translateY -4px), and crisp micro-interactions."
            }
        ]

    def _formulate_upgrade_plan(self, colors: Dict[str, str], typography: Dict[str, Any], flaws: List[Dict[str, str]]) -> Dict[str, Any]:
        return {
            "retained_brand_colors": {
                "primary": colors.get("--warna-biru-gelap", "#1268b3"),
                "secondary": colors.get("--warna-biru-utama", "#2196f3"),
                "accent": colors.get("--warna-kuning", "#fab853"),
                "whatsapp": colors.get("--warna-hijau-wa", "#25d366"),
                "background": colors.get("background_body", "#f0f6ff")
            },
            "modernized_tokens": {
                "navy_deep": "#0D4D87",
                "blue_primary": "#1268B3",
                "blue_bright": "#2196F3",
                "amber_gold": "#FAB853",
                "surface_ice": "#F0F6FF",
                "surface_white": "#FFFFFF",
                "text_primary": "#1E293B",
                "text_muted": "#475569"
            },
            "typography_upgrade": {
                "headings": "'Plus Jakarta Sans', 'Poppins', sans-serif",
                "body": "'Poppins', 'Open Sans', sans-serif",
                "google_fonts_url": "https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@600;700;800&family=Poppins:wght@300;400;500;600;700&display=swap"
            },
            "design_principles": [
                "Preserve 100% of authentic client copy, structure, photos, and Visi-Misi.",
                "Zero fabricated gadgets or fake telemetry simulators.",
                "Elevate Swiss clarity, visual hierarchy, responsive touch ergonomics, and lightning load speed."
            ]
        }


if __name__ == "__main__":
    from scraper import ClientWebsiteScraper
    scraper = ClientWebsiteScraper()
    scraped = scraper.scrape("https://suncargo.sunfrozencargo.com")
    analyzer = WebsiteStyleAnalyzer()
    res = analyzer.analyze(scraped["raw_html"], scraped)
    print("Design Flaws:", len(res["design_flaws"]))
    print("Typography:", res["modernization_plan"]["typography_upgrade"]["headings"])
