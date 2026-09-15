import os
import json
import pytest
from pipeline.db.database import PipelineDatabase


@pytest.fixture
def temp_db(tmp_path):
    """Fixture providing an isolated SQLite database for testing."""
    db_file = str(tmp_path / "test_pipeline.db")
    db = PipelineDatabase(db_path=db_file)
    return db


def test_db_schema_initialization(temp_db):
    """Verify that required tables are created on database initialization."""
    with temp_db._get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row[0] for row in cursor.fetchall()}
    assert "leads" in tables
    assert "invoices" in tables


def test_save_and_get_lead(temp_db):
    """Verify saving and retrieving leads in SQLite."""
    lead_data = {
        "domain": "kopikenangan.com",
        "business_name": "Kopi Kenangan",
        "whatsapp": "+628123456789",
        "email": "halo@kopikenangan.com",
        "track": "track_b_modernize",
        "status": "discovered",
        "notes": "Testing lead notes",
        "outdated_signals": ["no_https", "missing_viewport"]
    }

    temp_db.save_lead(lead_data, sync_json=False)

    retrieved = temp_db.get_lead("kopikenangan.com")
    assert retrieved is not None
    assert retrieved["business_name"] == "Kopi Kenangan"
    assert retrieved["status"] == "discovered"
    assert retrieved["track"] == "track_b_modernize"
    assert "no_https" in retrieved["outdated_signals"]

    # Update status
    lead_data["status"] = "sent_whatsapp"
    temp_db.save_lead(lead_data, sync_json=False)
    updated = temp_db.get_lead("kopikenangan.com")
    assert updated["status"] == "sent_whatsapp"


def test_get_all_leads_and_contacted(temp_db):
    """Verify retrieving all leads and contact detection."""
    temp_db.save_lead({
        "domain": "lead1.com",
        "business_name": "Lead One",
        "status": "discovered"
    }, sync_json=False)

    temp_db.save_lead({
        "domain": "lead2.com",
        "business_name": "Lead Two",
        "whatsapp": "+6281111111",
        "status": "sent_whatsapp"
    }, sync_json=False)

    all_leads = temp_db.get_all_leads()
    assert len(all_leads) >= 2
    assert "lead1.com" in all_leads
    assert "lead2.com" in all_leads

    # Test is_already_contacted
    assert temp_db.is_already_contacted("lead1.com") is False
    assert temp_db.is_already_contacted("lead2.com") is True
    assert temp_db.is_already_contacted("unknown.com", phone="+6281111111") is True


def test_save_and_get_invoice(temp_db):
    """Verify invoice creation and status update."""
    inv_data = {
        "invoice_id": "INV-TEST-001",
        "order_id": "ORDER-TEST-001",
        "domain": "kopikenangan.com",
        "business_name": "Kopi Kenangan",
        "usd_price": 100.0,
        "idr_price": 1600000.0,
        "status": "pending",
        "payment_url": "https://app.sandbox.midtrans.com/snap/v2/vtweb/xyz",
        "snap_token": "token-xyz-123"
    }

    temp_db.save_invoice(inv_data, sync_json=False)

    inv = temp_db.get_invoice("INV-TEST-001")
    assert inv is not None
    assert inv["order_id"] == "ORDER-TEST-001"
    assert inv["idr_price"] == 1600000.0
    assert inv["status"] == "pending"

    by_order = temp_db.get_invoice_by_order_id("ORDER-TEST-001")
    assert by_order is not None
    assert by_order["invoice_id"] == "INV-TEST-001"

    # Update invoice to paid
    inv_data["status"] = "settlement"
    inv_data["paid_at"] = "2026-09-11 12:00:00"
    inv_data["payment_method"] = "qris"
    temp_db.save_invoice(inv_data, sync_json=False)

    inv_paid = temp_db.get_invoice("INV-TEST-001")
    assert inv_paid["status"] == "settlement"
    assert inv_paid["payment_method"] == "qris"
    assert inv_paid["paid_at"] == "2026-09-11 12:00:00"
