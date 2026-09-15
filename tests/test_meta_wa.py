"""
Unit tests for Meta WhatsApp Cloud API Client and Webhook integration.
"""

import os
import json
from unittest.mock import patch, MagicMock
import pytest

from pipeline.outreach.meta_wa_client import normalize_phone_e164, MetaWhatsAppClient
from pipeline.outreach.whatsapp_dispatcher import WhatsAppDispatcher


class TestPhoneNormalization:
    def test_local_leading_zero(self):
        assert normalize_phone_e164("081234567890") == "6281234567890"

    def test_international_plus(self):
        assert normalize_phone_e164("+62 812-3456-7890") == "6281234567890"

    def test_leading_eight(self):
        assert normalize_phone_e164("81234567890") == "6281234567890"

    def test_already_normalized(self):
        assert normalize_phone_e164("6281234567890") == "6281234567890"


class TestMetaWhatsAppClient:
    def test_is_configured_false(self):
        client = MetaWhatsAppClient(token="", phone_number_id="")
        assert not client.is_configured()

    def test_is_configured_true(self):
        client = MetaWhatsAppClient(token="EAAB...", phone_number_id="123456789")
        assert client.is_configured()

    def test_send_outreach_dry_run(self):
        client = MetaWhatsAppClient(token="test_token", phone_number_id="123456")
        res = client.send_outreach(
            target_phone="081234567890",
            business_name="Bengkel Maju",
            domain="bengkelmaju.com",
            dry_run=True,
            message_text="Halo Bengkel Maju"
        )
        assert res["success"] is True
        assert res["mode"] == "dry_run"
        assert res["provider"] == "meta_cloud"
        assert res["phone"] == "6281234567890"

    @patch("requests.post")
    def test_send_text_message_success(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"messages": [{"id": "wamid.12345"}]}
        mock_post.return_value = mock_resp

        client = MetaWhatsAppClient(token="valid_token", phone_number_id="100200300")
        res = client.send_text_message("081234567890", "Halo ini test")

        assert res["success"] is True
        assert res["message_id"] == "wamid.12345"
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        assert "100200300/messages" in args[0]
        assert kwargs["json"]["to"] == "6281234567890"
        assert kwargs["json"]["text"]["body"] == "Halo ini test"

    @patch("requests.post")
    def test_send_template_message(self, mock_post):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {"messages": [{"id": "wamid.tpl.123"}]}
        mock_post.return_value = mock_resp

        client = MetaWhatsAppClient(token="valid_token", phone_number_id="100200300")
        res = client.send_template_message(
            to="081234567890",
            template_name="website_intro",
            language_code="id",
            body_parameters=["Bengkel Maju", "bengkelmaju.com"]
        )

        assert res["success"] is True
        assert res["message_id"] == "wamid.tpl.123"
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["template"]["name"] == "website_intro"
        assert kwargs["json"]["template"]["components"][0]["parameters"][0]["text"] == "Bengkel Maju"


class TestDispatcherMetaRouting:
    def test_dispatcher_detects_meta_provider(self, monkeypatch):
        monkeypatch.setenv("WA_PROVIDER", "meta")
        disp = WhatsAppDispatcher()
        assert disp.is_using_meta() is True

    def test_dispatcher_dry_run_routes_to_meta(self, monkeypatch):
        monkeypatch.setenv("WA_PROVIDER", "meta")
        disp = WhatsAppDispatcher()
        res = disp.dispatch_live(
            target_phone="081234567890",
            business_name="Test Toko",
            domain="testtoko.com",
            dry_run=True
        )
        assert res["success"] is True
        assert res["mode"] == "dry_run"
        assert res["provider"] == "meta_cloud"
