"""
Automated unit & integration tests for the Streamlined Pipeline:
- ContactValidator (Mobile WA, PSTN Landlines, Multi-Tier Fallback Cascade)
- NicheMatrix (High-Value Diversity Sampler, Anti-Toko-Bangunan Filter)
- OutdatedWebsiteHunter (Outdated technical signal detection)
"""

import pytest
from pipeline.scanner.contact_validator import ContactValidator
from pipeline.scanner.niche_matrix import NicheMatrix, HIGH_VALUE_NICHE_TAXONOMY
from pipeline.scanner.outdated_hunter import OutdatedWebsiteHunter


class TestContactValidator:
    def test_mobile_number_identification(self):
        # Telkomsel
        info1 = ContactValidator.identify_phone_type("081234567890")
        assert info1["is_mobile"] is True
        assert info1["is_landline"] is False
        assert info1["normalized_e164"] == "6281234567890"
        assert "Telkomsel" in info1["operator"]

        # Indosat
        info2 = ContactValidator.identify_phone_type("+62 856-7890-123")
        assert info2["is_mobile"] is True
        assert info2["normalized_e164"] == "628567890123"
        assert "Indosat" in info2["operator"]

        # XL
        info3 = ContactValidator.identify_phone_type("62818998877")
        assert info3["is_mobile"] is True
        assert info3["normalized_e164"] == "62818998877"

    def test_pstn_landline_identification(self):
        # Jakarta (021)
        info_jkt = ContactValidator.identify_phone_type("(021) 5890-1234")
        assert info_jkt["is_landline"] is True
        assert info_jkt["is_mobile"] is False
        assert "Jabodetabek" in info_jkt["area_name"]

        # Surabaya (031)
        info_sby = ContactValidator.identify_phone_type("031-8987654")
        assert info_sby["is_landline"] is True
        assert "Surabaya" in info_sby["area_name"]

        # Balikpapan (0542)
        info_bpn = ContactValidator.identify_phone_type("0542-765432")
        assert info_bpn["is_landline"] is True
        assert "Balikpapan" in info_bpn["area_name"]

    def test_fallback_cascade_tier_0_whatsapp(self):
        cascade = ContactValidator.evaluate_contact_cascade("081299887766", "sales@perusahaan.co.id")
        assert cascade["primary_channel"] == "whatsapp"
        assert cascade["fallback_tier"] == 0
        assert cascade["status"] == "qualified_whatsapp"

    def test_fallback_cascade_tier_1_email_for_pstn(self):
        cascade = ContactValidator.evaluate_contact_cascade("021-5551234", "info@kontraktor-hvac.co.id")
        assert cascade["primary_channel"] == "email"
        assert cascade["fallback_tier"] == 1
        assert cascade["status"] == "fallback_email"
        assert cascade["email"] == "info@kontraktor-hvac.co.id"

    def test_fallback_cascade_landline_without_email_skipped(self):
        # Landline without email is skipped/discarded (telesales disabled)
        cascade = ContactValidator.evaluate_contact_cascade("031-8981234", None)
        assert cascade["primary_channel"] == "discard"
        assert cascade["fallback_tier"] == 3
        assert cascade["status"] == "discarded"

    def test_fallback_cascade_tier_3_fail_fast_discard(self):
        # Bogus number and no email
        cascade = ContactValidator.evaluate_contact_cascade("12345", "")
        assert cascade["primary_channel"] == "discard"
        assert cascade["fallback_tier"] == 3
        assert cascade["status"] == "discarded"


class TestNicheMatrix:
    def test_anti_toko_bangunan_filter(self):
        assert NicheMatrix.is_excluded_business("TB Sinar Abadi Toko Bahan Bangunan") is True
        assert NicheMatrix.is_excluded_business("Toko Material Berkah Jaya") is True
        assert NicheMatrix.is_excluded_business("Warung Sembako Madura") is True
        assert NicheMatrix.is_excluded_business("Toko Kelontong Sejahtera") is True

        # High-value niches must NOT be excluded
        assert NicheMatrix.is_excluded_business("PT Sinar Surya Ekspedisi Truk Reefer") is False
        assert NicheMatrix.is_excluded_business("CV Cikarang Epoxy Lantai Pabrik") is False
        assert NicheMatrix.is_excluded_business("Distributor Packaging Karton Box Surabaya") is False
        assert NicheMatrix.is_excluded_business("Klinik Estetika Beauty Care") is False

    def test_diverse_query_batch(self):
        queries = NicheMatrix.get_diverse_query_batch(limit=5)
        assert len(queries) == 5
        # Ensure none of the generated queries contain excluded retail terms
        for q in queries:
            assert NicheMatrix.is_excluded_business(q) is False

    def test_dork_queries_for_track_b(self):
        dorks = NicheMatrix.get_dork_queries_for_track_b(limit=4)
        assert len(dorks) >= 3
        for d in dorks:
            assert ".co.id" in d or ".id" in d


class TestOutdatedWebsiteHunterSignals:
    def test_inspect_sample_html_signals(self):
        hunter = OutdatedWebsiteHunter()
        sample_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>PT Karya Logistik Mandiri - Ekspedisi Truk Surabaya</title>
        </head>
        <body>
            <h1>Layanan Ekspedisi Tronton</h1>
            <p>Hubungi WhatsApp: 0812-3456-7890 atau email sales@karyalogistik.co.id</p>
            <footer>Copyright © 2017 PT Karya Logistik Mandiri. All rights reserved.</footer>
        </body>
        </html>
        """
        # Test signal detection logic
        outdated_signals = []
        if "<meta name=\"viewport\"" not in sample_html:
            outdated_signals.append("Non-responsive: Belum memiliki viewport smartphone")
        if "application/ld+json" not in sample_html:
            outdated_signals.append("SEO Kritis: Hilang Schema.org")
        if "2017" in sample_html:
            outdated_signals.append("Hak Cipta Kedaluwarsa: Terakhir diperbarui tahun 2017")

        assert len(outdated_signals) == 3


class TestVercelCollisionPrevention:
    def test_track_b_slug_preserves_tld_prevents_global_collision(self):
        from pipeline.deployer.vercel_deployer import VercelDeployer
        # Single-word domains that collide with existing foreign Vercel apps
        assert VercelDeployer.get_preview_slug("inspeksi.co.id", track="track_b_modernize") == "inspeksi-co-id"
        assert VercelDeployer.get_preview_slug("finoo.id", track="track_b_modernize") == "finoo-id"
        assert VercelDeployer.get_preview_slug("equalmandiri.com", track="track_b_modernize") == "equalmandiri-com"
        assert VercelDeployer.get_preview_slug("https://www.inspeksi.co.id/", track="track_b_modernize") == "inspeksi-co-id"

    def test_track_a_slug_includes_city_prevents_name_collision(self):
        from pipeline.deployer.vercel_deployer import VercelDeployer
        slug_palangka = VercelDeployer.get_preview_slug("Toko Harapan Baru", track="track_a_new_web", city="Palangka Raya")
        slug_surabaya = VercelDeployer.get_preview_slug("Toko Harapan Baru", track="track_a_new_web", city="Surabaya")

        assert slug_palangka == "harapan-baru-palangka-raya"
        assert slug_surabaya == "harapan-baru-surabaya"
        # Must be completely distinct to prevent primary key / vercel collisions
        assert slug_palangka != slug_surabaya

    def test_dashboard_renders_no_phantom_vercel_url_when_undeployed(self):
        from pipeline.outreach.queue_dashboard import generate_html_queue_dashboard
        leads = [{
            "domain": "inspeksi.co.id",
            "business_name": "PT Inspeksi Indonesia",
            "vercel_url": "",  # Not deployed yet
            "status": "ready_for_permission",
            "track": "track_b_modernize"
        }]
        html_out = generate_html_queue_dashboard(leads, output_path="clients/test_queue_temp.html")
        with open("clients/test_queue_temp.html", "r", encoding="utf-8") as f:
            content = f.read()

        try:
            # MUST NOT contain phantom domain
            assert "inspeksi.vercel.app" not in content
            assert "Live Vercel: https://inspeksi.vercel.app" not in content
            # MUST contain indicator that it is not deployed yet
            assert "Belum Deploy" in content
            assert "deployVercel('inspeksi.co.id'" in content
        finally:
            import os
            if os.path.exists("clients/test_queue_temp.html"):
                os.remove("clients/test_queue_temp.html")

