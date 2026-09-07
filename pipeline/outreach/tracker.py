"""
Outreach Tracker Module.
Maintains history of scanned and contacted businesses in `clients/outreach_history.json`
to prevent duplicate outreach and track lead conversion statuses.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

HISTORY_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "clients", "outreach_history.json")


class OutreachTracker:
    def __init__(self, history_path: Optional[str] = None):
        self.history_path = os.path.abspath(history_path or HISTORY_FILE)
        os.makedirs(os.path.dirname(self.history_path), exist_ok=True)
        self.history = self._load_history()

    def _load_history(self) -> Dict[str, Any]:
        if os.path.exists(self.history_path):
            try:
                with open(self.history_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"leads": {}, "last_updated": None}

    def _save_history(self):
        self.history["last_updated"] = datetime.now().isoformat()
        with open(self.history_path, "w", encoding="utf-8") as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)

    def is_already_contacted(self, domain: str, phone: Optional[str] = None, email: Optional[str] = None) -> bool:
        """Checks if a domain, phone number, or email has already been reached out to."""
        leads = self.history.get("leads", {})
        
        # Check by domain key
        if domain in leads:
            status = leads[domain].get("status", "")
            if status in ["sent_whatsapp", "sent_email", "sent_all"]:
                return True

        # Check by phone or email across all records
        clean_phone = phone.strip() if phone else ""
        clean_email = email.strip().lower() if email else ""

        for d_key, record in leads.items():
            if clean_phone and record.get("whatsapp") == clean_phone and record.get("status") in ["sent_whatsapp", "sent_all"]:
                return True
            if clean_email and record.get("email") == clean_email and record.get("status") in ["sent_email", "sent_all"]:
                return True

        return False

    def record_lead(self, domain: str, data: Dict[str, Any], status: str = "discovered") -> None:
        """Records or updates a lead entry with contact timestamps and pipeline outputs."""
        if "leads" not in self.history:
            self.history["leads"] = {}

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        existing = self.history["leads"].get(domain, {})

        entry = {
            "domain": domain,
            "business_name": data.get("business_name", existing.get("business_name", domain)),
            "website_url": data.get("website_url", existing.get("website_url", f"https://{domain}")),
            "whatsapp": data.get("whatsapp", existing.get("whatsapp", "")),
            "email": data.get("email", existing.get("email", "")),
            "track": data.get("track", existing.get("track", "track_b_modernize")),
            "proposal_pdf": data.get("proposal_pdf", existing.get("proposal_pdf", "")),
            "vercel_url": data.get("vercel_url", existing.get("vercel_url", "")),
            "invoice_id": data.get("invoice_id", existing.get("invoice_id", "")),
            "package_zip": data.get("package_zip", existing.get("package_zip", "")),
            "payment_status": data.get("payment_status", existing.get("payment_status", "unpaid")),
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

        self.history["leads"][domain] = entry
        self._save_history()

    def get_lead(self, domain: str) -> Optional[Dict[str, Any]]:
        return self.history.get("leads", {}).get(domain)

    def get_all_leads(self) -> Dict[str, Any]:
        return self.history.get("leads", {})
