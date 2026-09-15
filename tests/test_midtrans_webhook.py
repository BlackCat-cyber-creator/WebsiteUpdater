import os
import io
import json
import hashlib
import zipfile
import pytest
from unittest.mock import patch, MagicMock

from pipeline.payment.payment_gateway import PaymentGateway
from pipeline.delivery.code_packager import CodePackager
from pipeline.db.database import PipelineDatabase
from pipeline.outreach.tracker import OutreachTracker
from pipeline.outreach.dashboard_server import OutreachDashboardHandler, _PUBLIC_PATHS


def test_public_paths_contains_midtrans_webhook():
    """Ensure Midtrans webhook endpoints are declared in _PUBLIC_PATHS."""
    assert "/api/webhook/midtrans" in _PUBLIC_PATHS
    assert "/api/payment-webhook" in _PUBLIC_PATHS


def test_verify_midtrans_notification_dict():
    """Verify verify_midtrans_notification correctly validates dictionary payload."""
    gw = PaymentGateway()
    gw.server_key = "SB-Mid-server-testkey123"

    order_id = "INV-20260914-8888"
    status_code = "200"
    gross_amount = "1650000.00"

    raw = f"{order_id}{status_code}{gross_amount}{gw.server_key}".encode("utf-8")
    valid_sig = hashlib.sha512(raw).hexdigest()

    payload = {
        "order_id": order_id,
        "status_code": status_code,
        "gross_amount": gross_amount,
        "signature_key": valid_sig,
        "transaction_status": "settlement"
    }

    assert gw.verify_midtrans_notification(payload) is True

    # Tampered signature
    tampered_payload = dict(payload)
    tampered_payload["signature_key"] = "tampered_hash_12345"
    assert gw.verify_midtrans_notification(tampered_payload) is False

    # Tampered amount
    tampered_amt_payload = dict(payload)
    tampered_amt_payload["gross_amount"] = "2000000.00"
    assert gw.verify_midtrans_notification(tampered_amt_payload) is False


def test_verify_midtrans_notification_args():
    """Verify verify_midtrans_notification works with individual positional/keyword arguments."""
    gw = PaymentGateway()
    gw.server_key = "SB-Mid-server-testkey123"

    order_id = "INV-20260914-7777"
    status_code = "200"
    gross_amount = "1650000"

    raw = f"{order_id}{status_code}{gross_amount}{gw.server_key}".encode("utf-8")
    valid_sig = hashlib.sha512(raw).hexdigest()

    assert gw.verify_midtrans_notification(
        order_id, status_code=status_code, gross_amount=gross_amount, signature_key=valid_sig
    ) is True


def test_code_packager_package_client(tmp_path):
    """Verify CodePackager.package_client generates clean .zip with required guides in clients/<id>/."""
    client_dir = tmp_path / "test_client_packager"
    client_dir.mkdir(parents=True, exist_ok=True)

    cp = CodePackager()
    res = cp.package_client(
        client_id="test_client_packager",
        business_name="Toko Test Packager",
        domain="testpackager.id",
        output_dir=str(client_dir),
        phone="08123456789"
    )

    assert res["success"] is True
    assert os.path.exists(res["zip_path"])
    assert res["zip_path"].endswith(".zip")
    assert "/api/download-package?client=" in res["download_url"]

    # Verify contents of generated ZIP
    with zipfile.ZipFile(res["zip_path"], "r") as zf:
        namelist = zf.namelist()
        assert "PANDUAN_PEMASANGAN_CPANEL.md" in namelist
        assert "SEO_CONFIGURATION_GUIDE.md" in namelist
        assert any("website_prototype" in name for name in namelist)


class DummyHandler(OutreachDashboardHandler):
    """Mock handler for unit testing HTTP POST routes without starting a socket server."""
    def __init__(self, path, body_dict, headers=None):
        self.path = path
        body_bytes = json.dumps(body_dict).encode("utf-8")
        self.rfile = io.BytesIO(body_bytes)
        self.wfile = io.BytesIO()
        self.headers = headers or {"Content-Length": str(len(body_bytes)), "Host": "localhost:8080"}
        self.response_code = None
        self.response_headers = {}

    def send_response(self, code, message=None):
        self.response_code = code

    def send_header(self, keyword, value):
        self.response_headers[keyword] = value

    def end_headers(self):
        pass


def test_webhook_invalid_signature(tmp_path):
    """Verify POST /api/webhook/midtrans rejects requests with invalid signature (403)."""
    db_file = str(tmp_path / "test_pipe.db")
    db = PipelineDatabase(db_path=db_file)

    with patch("pipeline.payment.payment_gateway.get_db", return_value=db), \
         patch("pipeline.outreach.dashboard_server.CLIENTS_DIR", str(tmp_path)), \
         patch.dict(os.environ, {"MIDTRANS_SERVER_KEY": "SB-Mid-server-secret123"}):

        payload = {
            "order_id": "INV-TEST-9999",
            "status_code": "200",
            "gross_amount": "1650000.00",
            "signature_key": "invalid_fake_sig",
            "transaction_status": "settlement"
        }

        handler = DummyHandler("/api/webhook/midtrans", payload)
        handler.do_POST()

        assert handler.response_code == 403
        response_body = json.loads(handler.wfile.getvalue().decode("utf-8"))
        assert response_body["success"] is False
        assert "Invalid Midtrans signature" in response_body["error"]


def test_webhook_settlement_flow(tmp_path):
    """
    Verify full settlement flow on POST /api/webhook/midtrans:
    - Invoice and lead marked PAID in pipeline.db
    - CodePackager generates .zip
    - HANDOVER_LOG.json is saved
    - WhatsApp notification is triggered
    """
    db_file = str(tmp_path / "test_pipe.db")
    db = PipelineDatabase(db_path=db_file)

    server_key = "SB-Mid-server-secret123"
    order_id = "INV-20260914-1111"
    status_code = "200"
    gross_amount = "1650000.00"
    domain = "kopiunggul.com"

    # Pre-populate invoice and lead
    db.save_invoice({
        "invoice_id": order_id,
        "order_id": order_id,
        "domain": domain,
        "business_name": "Kopi Unggul",
        "whatsapp": "081298765432",
        "status": "PENDING",
        "amount_idr": 1650000,
        "price_display": "$100 USD (setara Rp 1.650.000 kurs live)"
    })

    db.save_lead({
        "domain": domain,
        "business_name": "Kopi Unggul",
        "whatsapp": "081298765432",
        "status": "sent_step2",
        "invoice_id": order_id
    })

    raw = f"{order_id}{status_code}{gross_amount}{server_key}".encode("utf-8")
    sig = hashlib.sha512(raw).hexdigest()

    payload = {
        "order_id": order_id,
        "status_code": status_code,
        "gross_amount": gross_amount,
        "signature_key": sig,
        "transaction_status": "settlement",
        "fraud_status": "accept"
    }

    clients_dir = str(tmp_path / "clients")
    os.makedirs(clients_dir, exist_ok=True)

    with patch("pipeline.payment.payment_gateway.get_db", return_value=db), \
         patch("pipeline.outreach.tracker.get_db", return_value=db), \
         patch("pipeline.outreach.dashboard_server.CLIENTS_DIR", clients_dir), \
         patch.dict(os.environ, {"MIDTRANS_SERVER_KEY": server_key}):

        mock_wa_send = MagicMock(return_value={"success": True})
        with patch("pipeline.outreach.whatsapp_dispatcher.WhatsAppDispatcher.send_custom_message", mock_wa_send):
            handler = DummyHandler("/api/webhook/midtrans", payload)
            handler.do_POST()

            assert handler.response_code == 200
            response_body = json.loads(handler.wfile.getvalue().decode("utf-8"))
            assert response_body["success"] is True
            assert response_body["status"] == "PAID"
            assert response_body["order_id"] == order_id
            assert "download_url" in response_body

            # 1. Check Invoice in DB is PAID
            inv = db.get_invoice(order_id)
            assert inv is not None
            assert inv["status"] == "PAID"
            assert inv["paid_at"] is not None

            # 2. Check Lead in DB is PAID
            lead = db.get_lead(domain)
            assert lead is not None
            assert lead["status"] == "PAID"
            assert lead["payment_status"] == "PAID"
            assert lead["package_zip"] is not None
            assert os.path.exists(lead["package_zip"])

            # 3. Check handover log file exists
            client_folder = os.path.dirname(lead["package_zip"])
            handover_file = os.path.join(client_folder, "HANDOVER_LOG.json")
            assert os.path.exists(handover_file)
            with open(handover_file, "r", encoding="utf-8") as f:
                h_data = json.load(f)
            assert h_data["status"] == "PAID"
            assert h_data["invoice_id"] == order_id
            assert h_data["handover_completed"] is True


def test_webhook_capture_flow(tmp_path):
    """Verify capture status with fraud_status accept marks transaction as PAID."""
    db_file = str(tmp_path / "test_pipe.db")
    db = PipelineDatabase(db_path=db_file)

    server_key = "SB-Mid-server-secret123"
    order_id = "INV-20260914-2222"
    status_code = "200"
    gross_amount = "1650000.00"
    domain = "klinikcantik.com"

    db.save_invoice({
        "invoice_id": order_id,
        "order_id": order_id,
        "domain": domain,
        "business_name": "Klinik Cantik",
        "whatsapp": "081122334455",
        "status": "PENDING"
    })
    db.save_lead({
        "domain": domain,
        "business_name": "Klinik Cantik",
        "whatsapp": "081122334455",
        "status": "discovered",
        "invoice_id": order_id
    })

    raw = f"{order_id}{status_code}{gross_amount}{server_key}".encode("utf-8")
    sig = hashlib.sha512(raw).hexdigest()

    payload = {
        "order_id": order_id,
        "status_code": status_code,
        "gross_amount": gross_amount,
        "signature_key": sig,
        "transaction_status": "capture",
        "fraud_status": "accept"
    }

    clients_dir = str(tmp_path / "clients")
    os.makedirs(clients_dir, exist_ok=True)

    with patch("pipeline.payment.payment_gateway.get_db", return_value=db), \
         patch("pipeline.outreach.tracker.get_db", return_value=db), \
         patch("pipeline.outreach.dashboard_server.CLIENTS_DIR", clients_dir), \
         patch.dict(os.environ, {"MIDTRANS_SERVER_KEY": server_key}):

        with patch("pipeline.outreach.whatsapp_dispatcher.WhatsAppDispatcher.send_custom_message"):
            handler = DummyHandler("/api/webhook/midtrans", payload)
            handler.do_POST()

            assert handler.response_code == 200
            inv = db.get_invoice(order_id)
            assert inv["status"] == "PAID"
            lead = db.get_lead(domain)
            assert lead["status"] == "PAID"
