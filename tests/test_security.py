import hashlib
import pytest
from pipeline.payment.payment_gateway import PaymentGateway
from pipeline.outreach.dashboard_server import is_authenticated_request


def test_midtrans_signature_empty_server_key():
    """Security check: verify_midtrans_signature must reject when server_key is empty."""
    gw = PaymentGateway()
    gw.server_key = ""

    result = gw.verify_midtrans_signature(
        order_id="INV-TEST-001",
        status_code="200",
        gross_amount="1600000.00",
        signature_key="some_signature_here"
    )
    assert result is False


def test_midtrans_signature_valid():
    """Verify that a valid SHA512 signature is correctly accepted."""
    gw = PaymentGateway()
    gw.server_key = "SB-Mid-server-testkey123"

    order_id = "INV-TEST-001"
    status_code = "200"
    gross_amount = "1600000.00"

    raw = f"{order_id}{status_code}{gross_amount}{gw.server_key}".encode("utf-8")
    valid_sig = hashlib.sha512(raw).hexdigest()

    result = gw.verify_midtrans_signature(
        order_id=order_id,
        status_code=status_code,
        gross_amount=gross_amount,
        signature_key=valid_sig
    )
    assert result is True


def test_midtrans_signature_tampered():
    """Verify that a tampered payload or signature is rejected."""
    gw = PaymentGateway()
    gw.server_key = "SB-Mid-server-testkey123"

    result = gw.verify_midtrans_signature(
        order_id="INV-TEST-001",
        status_code="200",
        gross_amount="1600000.00",
        signature_key="tampered_fake_signature_hash"
    )
    assert result is False


def test_dashboard_token_auth_behavior():
    """Verify dashboard token authentication logic."""
    secret = "secure-secret-token"

    # Missing token
    assert is_authenticated_request(path="/", headers={}, token=secret) is False

    # Invalid token in header
    assert is_authenticated_request(path="/", headers={"Authorization": "Bearer wrong-token"}, token=secret) is False

    # Valid token in header
    assert is_authenticated_request(path="/", headers={"Authorization": "Bearer secure-secret-token"}, token=secret) is True

    # Valid token in query param
    assert is_authenticated_request(path="/?token=secure-secret-token", headers={}, token=secret) is True

    # When no token configured (empty)
    assert is_authenticated_request(path="/", headers={}, token="") is True
