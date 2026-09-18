import os
import json
from pipeline.payment.payment_gateway import PaymentGateway

def test_snap_creation():
    from dotenv import load_dotenv
    load_dotenv(override=True)
    
    gw = PaymentGateway()
    inv = gw.create_invoice(
        domain="demoklien.id",
        business_name="PT Sukses Sejahtera Demo",
        whatsapp="+628123456789",
        track="track_b_modernize",
        base_url="http://localhost:8080"
    )
    assert inv.get("invoice_id") is not None
    assert inv.get("amount_idr") == 1490000
    assert "payment_url" in inv
