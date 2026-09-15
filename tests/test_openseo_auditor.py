"""
Unit and integration tests for the codified OpenSEO Audit Engine (pipeline/auditor.py).
Validates OpenSEO 5-bucket taxonomy, 'The One Thing' framework, and Keyword Clusters.
"""

import pytest
from pipeline.auditor import WebsiteAuditor


class TestOpenSEOAuditor:
    def setup_method(self):
        self.auditor = WebsiteAuditor()

    def test_openseo_five_bucket_taxonomy_present(self):
        """Ensures all 5 OpenSEO standard categories exist in audit output."""
        scraped_data = {
            "metadata": {
                "title": "Toko Kertas Maju",
                "meta_description": "Distributor kertas terlengkap",
                "viewport": "width=device-width, initial-scale=1.0"
            },
            "headings": {
                "h1": ["Distributor Kertas Berkualitas"]
            },
            "all_images": [
                {"src": "logo.png", "alt": "Logo Toko Kertas Maju"},
                {"src": "banner.jpg", "alt": ""}
            ],
            "kontak": {"telepon": "08123456789"},
            "layanan": [{"title": "Grosir Kertas HVS"}, {"title": "Kertas Karton"}]
        }

        report = self.auditor.audit(scraped_data)

        # 1. Verify 5 buckets
        categories = report.get("openseo_categories", {})
        expected_buckets = [
            "head_and_headings",
            "indexability_and_schema",
            "content_and_media",
            "local_seo_and_maps",
            "ux_and_conversion"
        ]
        for bucket in expected_buckets:
            assert bucket in categories, f"Missing OpenSEO bucket: {bucket}"

        # 2. Verify 'The One Thing' framework
        one_thing = report.get("one_thing", {})
        assert "title" in one_thing
        assert "why" in one_thing
        assert "impact" in one_thing
        assert len(one_thing["title"]) > 0

        # 3. Verify High-Intent Commercial Keyword Clusters
        keyword_targets = report.get("keyword_targets", [])
        assert len(keyword_targets) >= 3
        clusters = [kw.get("cluster") for kw in keyword_targets]
        assert any("Layanan Utama" in c for c in clusters)
        assert any("Brand & Solusi" in c for c in clusters)

    def test_openseo_critical_defects_detection(self):
        """Validates detection of critical defects according to OpenSEO protocols."""
        broken_data = {
            "metadata": {
                "title": "Short",  # Too short (< 25 chars)
                "meta_description": "",  # Missing
                "viewport": ""  # Missing viewport
            },
            "headings": {
                "h1": []  # Missing H1
            },
            "all_images": [
                {"src": "test.jpg", "alt": ""}
            ]
        }

        report = self.auditor.audit(broken_data)
        critical_count = report["summary"]["critical_defects"]
        assert critical_count >= 3

        # Missing H1 and Schema must be flagged
        schema_issues = [i for i in report["openseo_categories"]["indexability_and_schema"] if i["type"] == "schema_org"]
        assert len(schema_issues) > 0
        assert schema_issues[0]["severity"] == "CRITICAL"
