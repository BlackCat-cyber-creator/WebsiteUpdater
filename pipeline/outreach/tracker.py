"""
Outreach Tracker Module.
Maintains history of scanned and contacted businesses in SQLite (`clients/pipeline.db`)
with automatic mirror sync to `clients/outreach_history.json` for external file inspection.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from pipeline.db import get_db, PipelineDatabase


class OutreachTracker:
    def __init__(self, db: Optional[PipelineDatabase] = None):
        self.db = db or get_db()

    def is_already_contacted(self, domain: str, phone: Optional[str] = None, email: Optional[str] = None) -> bool:
        """Checks if a domain, phone number, or email has already been reached out to."""
        return self.db.is_already_contacted(domain, phone=phone, email=email)

    def record_lead(self, domain: str, data: Dict[str, Any], status: str = "discovered") -> None:
        """Records or updates a lead entry with contact timestamps and pipeline outputs."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        existing = self.db.get_lead(domain) or {}

        entry = {
            "domain": domain,
            "business_name": data.get("business_name", existing.get("business_name", domain)),
            "website_url": data.get("website_url", existing.get("website_url", f"https://{domain}")),
            "whatsapp": data.get("whatsapp", existing.get("whatsapp", "")),
            "phone": data.get("phone", existing.get("phone", "")),
            "area_name": data.get("area_name", existing.get("area_name", "")),
            "primary_channel": data.get("primary_channel", existing.get("primary_channel", "")),
            "email": data.get("email", existing.get("email", "")),
            "track": data.get("track", existing.get("track", "track_b_modernize")),
            "proposal_pdf": data.get("proposal_pdf") or existing.get("proposal_pdf", ""),
            "vercel_url": data.get("vercel_url") or existing.get("vercel_url", ""),
            "invoice_id": data.get("invoice_id") or existing.get("invoice_id", ""),
            "package_zip": data.get("package_zip") or existing.get("package_zip", ""),
            "payment_status": data.get("payment_status") or existing.get("payment_status", "unpaid"),
            "outdated_signals": data.get("outdated_signals", existing.get("outdated_signals", [])),
            "status": status,
            "created_at": existing.get("created_at", now_str),
            "updated_at": now_str,
            "logs": existing.get("logs", [])
        }

        entry["logs"].append({
            "timestamp": now_str,
            "action": status,
            "notes": data.get("notes", "")
        })

        self.db.save_lead(entry)

    def get_lead(self, domain: str) -> Optional[Dict[str, Any]]:
        return self.db.get_lead(domain)

    def get_all_leads(self) -> Dict[str, Any]:
        return self.db.get_all_leads()
