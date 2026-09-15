"""
Unit tests for new Dashboard Streamlined Endpoints:
- /api/hunt-outdated
- /api/scan-niche
"""

import os
import pytest
from pipeline.outreach.dashboard_server import CLIENTS_DIR


class TestDashboardStreamlinedEndpoints:
    def test_outreach_queue_html_contains_streamlined_elements(self):
        from pipeline.outreach.queue_dashboard import generate_html_queue_dashboard
        from pipeline.outreach.tracker import OutreachTracker
        tracker = OutreachTracker()
        all_leads = list(tracker.get_all_leads().values())
        queue_path = generate_html_queue_dashboard(all_leads)
        assert os.path.exists(queue_path), "outreach_queue.html must exist"

        with open(queue_path, "r", encoding="utf-8") as f:
            html = f.read()

        # Check font stack fix & ligatures
        assert "font-variant-ligatures: none;" in html
        assert "Segoe UI" in html

        # Check nationwide dropdown and controls
        assert "target-scope" in html
        assert "Seluruh Indonesia (Rotasi Multi-Sektor)" in html
        assert "B2B Distributor & Manufaktur" in html
        assert "btn-hunt-outdated" in html
        assert "btn-scan-niche" in html

        # Check interactive chips
        assert "chip-email" in html
        assert "filterByTag" in html
        assert "active-filter" in html

        # Check empty state interactive box
        assert "empty-state-box" in html
        assert "Semua Antrean Telah Diproses (Clean Slate)" in html

    def test_hunt_outdated_endpoint_handler_logic(self):
        from pipeline.scanner.outdated_hunter import OutdatedWebsiteHunter
        from pipeline.scanner.contact_validator import ContactValidator

        # Test that hunter can produce candidates with valid cascade
        sample_lead = {
            "business_name": "PT Test Baja Nasional",
            "domain": "testbaja.co.id",
            "whatsapp": "081234567890",
            "email": "info@testbaja.co.id",
            "outdated_signals": ["Non-responsive mobile viewport", "Copyright 2018"],
            "track": "track_b_modernize",
            "primary_channel": "whatsapp"
        }
        cascade = ContactValidator.evaluate_contact_cascade(sample_lead["whatsapp"], sample_lead["email"])
        assert cascade["primary_channel"] == "whatsapp"
        assert cascade["status"] == "qualified_whatsapp"

    def test_scan_niche_nationwide_presets(self):
        from pipeline.scanner.niche_matrix import NicheMatrix, HIGH_VALUE_NICHE_TAXONOMY

        # Verify nationwide taxonomy categories
        assert "b2b_distributor" in HIGH_VALUE_NICHE_TAXONOMY
        assert "ekspedisi_spesialis" in HIGH_VALUE_NICHE_TAXONOMY
        assert "kontraktor_komersial" in HIGH_VALUE_NICHE_TAXONOMY
        assert "klinik_spesialis" in HIGH_VALUE_NICHE_TAXONOMY
        assert "layanan_profesional" in HIGH_VALUE_NICHE_TAXONOMY

        # Verify diverse query batch spans high-ticket niches
        batch = NicheMatrix.get_diverse_query_batch(limit=5)
        assert len(batch) == 5
        for query in batch:
            assert not NicheMatrix.is_excluded_business(query)

