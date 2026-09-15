"""
Meta WhatsApp Cloud API Client (Jalur 2 Official Integration).
Provides official, 100% legal, and ban-free WhatsApp messaging using
the Meta Graph API (v20.0). No headless browser needed.
"""

import os
import re
import mimetypes
from typing import Dict, Any, List, Optional
import requests

from pipeline.logging_config import get_logger

logger = get_logger("meta_wa_client")

GRAPH_API_BASE = "https://graph.facebook.com"
DEFAULT_API_VERSION = "v20.0"


def normalize_phone_e164(phone: str) -> str:
    """
    Normalizes local and international Indonesian phone numbers to E.164 without '+' or leading '0'.
    Examples:
      '0812-3456-7890' -> '6281234567890'
      '+62 812 3456'   -> '628123456'
      '8123456789'     -> '628123456789'
    """
    digits = re.sub(r"[^\d]", "", phone)
    if digits.startswith("0"):
        digits = "62" + digits[1:]
    elif digits.startswith("8"):
        digits = "62" + digits
    elif digits.startswith("620"):
        digits = "62" + digits[3:]
    return digits


class MetaWhatsAppClient:
    """Official Meta WhatsApp Cloud API Client."""

    def __init__(
        self,
        token: Optional[str] = None,
        phone_number_id: Optional[str] = None,
        api_version: str = DEFAULT_API_VERSION,
        business_account_id: Optional[str] = None
    ):
        self.token = (token or os.environ.get("META_WHATSAPP_TOKEN", "")).strip()
        self.phone_number_id = (phone_number_id or os.environ.get("META_PHONE_NUMBER_ID", "")).strip()
        self.api_version = (os.environ.get("META_API_VERSION", api_version) or DEFAULT_API_VERSION).strip()
        self.business_account_id = (business_account_id or os.environ.get("META_BUSINESS_ACCOUNT_ID", "")).strip()
        self.template_name = os.environ.get("META_TEMPLATE_NAME", "").strip()

    def is_configured(self) -> bool:
        """Returns True if valid token and phone_number_id are set."""
        if not self.token or not self.phone_number_id:
            return False
        if "your_" in self.token.lower() or "your_" in self.phone_number_id.lower():
            return False
        return True

    @property
    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    @property
    def messages_endpoint(self) -> str:
        return f"{GRAPH_API_BASE}/{self.api_version}/{self.phone_number_id}/messages"

    @property
    def media_endpoint(self) -> str:
        return f"{GRAPH_API_BASE}/{self.api_version}/{self.phone_number_id}/media"

    def send_text_message(self, to: str, text: str, preview_url: bool = True) -> Dict[str, Any]:
        """
        Sends free-form text message to a normalized WhatsApp number.
        Note: Free-form text can be sent if a 24-hour customer service window is open,
        or in test mode with registered recipient numbers.
        """
        clean_to = normalize_phone_e164(to)
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": clean_to,
            "type": "text",
            "text": {
                "body": text,
                "preview_url": preview_url
            }
        }
        try:
            resp = requests.post(self.messages_endpoint, headers=self._headers, json=payload, timeout=25)
            data = resp.json()
            if resp.status_code in [200, 201]:
                msg_id = data.get("messages", [{}])[0].get("id", "")
                logger.info(f"Meta WA Text sent successfully to {clean_to} (ID: {msg_id})")
                return {"success": True, "message_id": msg_id, "data": data}
            else:
                err_msg = data.get("error", {}).get("message", resp.text)
                logger.error(f"Meta WA API Error ({resp.status_code}): {err_msg}")
                return {"success": False, "error": err_msg, "status_code": resp.status_code, "data": data}
        except Exception as e:
            logger.error(f"Failed to call Meta WA API: {e}")
            return {"success": False, "error": str(e)}

    def send_template_message(
        self,
        to: str,
        template_name: str,
        language_code: str = "id",
        body_parameters: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Sends an official pre-approved Meta Template message (required for cold outbound).
        """
        clean_to = normalize_phone_e164(to)
        components = []
        if body_parameters:
            components.append({
                "type": "body",
                "parameters": [{"type": "text", "text": str(p)} for p in body_parameters]
            })

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": clean_to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
                "components": components
            }
        }
        try:
            resp = requests.post(self.messages_endpoint, headers=self._headers, json=payload, timeout=25)
            data = resp.json()
            if resp.status_code in [200, 201]:
                msg_id = data.get("messages", [{}])[0].get("id", "")
                logger.info(f"Meta WA Template '{template_name}' sent to {clean_to} (ID: {msg_id})")
                return {"success": True, "message_id": msg_id, "data": data}
            else:
                err_msg = data.get("error", {}).get("message", resp.text)
                logger.error(f"Meta WA Template Error: {err_msg}")
                return {"success": False, "error": err_msg, "status_code": resp.status_code, "data": data}
        except Exception as e:
            logger.error(f"Failed to send template message: {e}")
            return {"success": False, "error": str(e)}

    def upload_media(self, file_path: str, mime_type: Optional[str] = None) -> Optional[str]:
        """
        Uploads a local file to Meta Graph API and returns the media_id.
        """
        if not os.path.exists(file_path):
            logger.error(f"Media file not found: {file_path}")
            return None

        if not mime_type:
            mime_type, _ = mimetypes.guess_type(file_path)
            mime_type = mime_type or "application/pdf"

        filename = os.path.basename(file_path)
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        try:
            with open(file_path, "rb") as f:
                files = {
                    "file": (filename, f, mime_type)
                }
                data = {
                    "messaging_product": "whatsapp",
                    "type": mime_type
                }
                resp = requests.post(self.media_endpoint, headers=headers, data=data, files=files, timeout=40)
                res_json = resp.json()
                media_id = res_json.get("id")
                if media_id:
                    logger.info(f"Media uploaded to Meta WhatsApp Cloud: ID {media_id}")
                    return str(media_id)
                else:
                    logger.error(f"Media upload failed: {res_json}")
                    return None
        except Exception as e:
            logger.error(f"Error uploading media to Meta API: {e}")
            return None

    def send_document(
        self,
        to: str,
        media_id_or_url: str,
        caption: str = "",
        filename: str = "Proposal_Website.pdf"
    ) -> Dict[str, Any]:
        """
        Sends a PDF document using either an uploaded Meta media_id or a public URL.
        """
        clean_to = normalize_phone_e164(to)
        doc_obj: Dict[str, str] = {
            "filename": filename,
            "caption": caption
        }
        if media_id_or_url.startswith("http://") or media_id_or_url.startswith("https://"):
            doc_obj["link"] = media_id_or_url
        else:
            doc_obj["id"] = media_id_or_url

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": clean_to,
            "type": "document",
            "document": doc_obj
        }
        try:
            resp = requests.post(self.messages_endpoint, headers=self._headers, json=payload, timeout=25)
            data = resp.json()
            if resp.status_code in [200, 201]:
                msg_id = data.get("messages", [{}])[0].get("id", "")
                logger.info(f"Document sent successfully to {clean_to} (ID: {msg_id})")
                return {"success": True, "message_id": msg_id, "data": data}
            else:
                err_msg = data.get("error", {}).get("message", resp.text)
                return {"success": False, "error": err_msg, "status_code": resp.status_code}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def send_outreach(
        self,
        target_phone: str,
        business_name: str,
        domain: str,
        pdf_path: Optional[str] = None,
        dry_run: bool = True,
        track: str = "track_b_modernize",
        message_text: str = ""
    ) -> Dict[str, Any]:
        """
        Full outreach dispatcher via Meta Cloud API.
        Handles dry-run logging, message sending, and optional PDF upload/attachment.
        """
        clean_phone = normalize_phone_e164(target_phone)
        if dry_run:
            print(f"[DRY-RUN META WA] Target: +{clean_phone} ({business_name}) | Jalur: {track}")
            print(f"[DRY-RUN META WA] Content: {message_text[:120]}...")
            if pdf_path:
                print(f"[DRY-RUN META WA] PDF Document: {pdf_path}")
            return {
                "success": True,
                "mode": "dry_run",
                "provider": "meta_cloud",
                "phone": clean_phone,
                "business_name": business_name,
                "track": track,
                "message": "Meta Cloud API prepared (Dry-run mode, no live charge)."
            }

        # 1. Send Main Message (Template or Direct Text)
        if self.template_name:
            send_res = self.send_template_message(
                to=clean_phone,
                template_name=self.template_name,
                body_parameters=[business_name, domain]
            )
        else:
            send_res = self.send_text_message(to=clean_phone, text=message_text)

        if not send_res.get("success"):
            return {
                "success": False,
                "mode": "error",
                "provider": "meta_cloud",
                "phone": clean_phone,
                "error": send_res.get("error"),
                "message": f"Meta Cloud API gagal kirim pesan: {send_res.get('error')}"
            }

        # 2. If PDF attachment is provided (for Track B or Track A proposal), upload and send
        if pdf_path and os.path.exists(pdf_path):
            media_id = self.upload_media(pdf_path, mime_type="application/pdf")
            if media_id:
                doc_res = self.send_document(
                    to=clean_phone,
                    media_id_or_url=media_id,
                    caption=f"Dokumen Proposal Resmi Modernisasi Website {business_name}",
                    filename=f"Proposal_{domain.replace('.', '_')}.pdf"
                )
                if not doc_res.get("success"):
                    logger.warning(f"Message sent but PDF attachment failed: {doc_res.get('error')}")

        return {
            "success": True,
            "mode": "live_sent",
            "provider": "meta_cloud",
            "phone": clean_phone,
            "business_name": business_name,
            "track": track,
            "message": f"Pesan resmi WhatsApp Cloud API berhasil terkirim ke {clean_phone}."
        }
