"""
SQLite persistence layer for Website Updater Studio.
Provides atomic transactions, thread safety, and auto-migration from existing JSON history files.
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional

DEFAULT_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "clients", "pipeline.db"))
HISTORY_JSON_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "clients", "outreach_history.json"))
INVOICES_JSON_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "clients", "invoices.json"))


class PipelineDatabase:
    """Manages SQLite storage for leads and invoices with WAL mode and JSON fallback compatibility."""

    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = os.path.abspath(db_path)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()
        self._auto_migrate_from_json()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        return conn

    def _init_db(self) -> None:
        with self._get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS leads (
                    domain TEXT PRIMARY KEY,
                    business_name TEXT,
                    website_url TEXT,
                    whatsapp TEXT,
                    email TEXT,
                    track TEXT DEFAULT 'track_b_modernize',
                    status TEXT DEFAULT 'discovered',
                    payment_status TEXT DEFAULT 'unpaid',
                    proposal_pdf TEXT,
                    vercel_url TEXT,
                    invoice_id TEXT,
                    package_zip TEXT,
                    outdated_signals TEXT,
                    notes TEXT,
                    address TEXT DEFAULT '',
                    city TEXT DEFAULT '',
                    created_at TEXT,
                    updated_at TEXT,
                    logs TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status);
                CREATE INDEX IF NOT EXISTS idx_leads_whatsapp ON leads(whatsapp);
                CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);
            """)

            # Dynamic migration for existing databases missing address, city, phone, area_name, primary_channel
            cur = conn.cursor()
            cur.execute("PRAGMA table_info(leads);")
            existing_cols = [row[1] for row in cur.fetchall()]
            if "address" not in existing_cols:
                conn.execute("ALTER TABLE leads ADD COLUMN address TEXT DEFAULT '';")
            if "city" not in existing_cols:
                conn.execute("ALTER TABLE leads ADD COLUMN city TEXT DEFAULT '';")
            if "phone" not in existing_cols:
                conn.execute("ALTER TABLE leads ADD COLUMN phone TEXT DEFAULT '';")
            if "area_name" not in existing_cols:
                conn.execute("ALTER TABLE leads ADD COLUMN area_name TEXT DEFAULT '';")
            if "primary_channel" not in existing_cols:
                conn.execute("ALTER TABLE leads ADD COLUMN primary_channel TEXT DEFAULT '';")

            conn.executescript("""

                CREATE TABLE IF NOT EXISTS invoices (
                    invoice_id TEXT PRIMARY KEY,
                    order_id TEXT UNIQUE,
                    domain TEXT,
                    business_name TEXT,
                    whatsapp TEXT,
                    track TEXT DEFAULT 'track_b_modernize',
                    usd_price REAL,
                    idr_price REAL,
                    rate REAL,
                    price_display TEXT,
                    payment_url TEXT,
                    snap_token TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT,
                    expires_at TEXT,
                    paid_at TEXT,
                    payment_method TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_invoices_status ON invoices(status);
                CREATE INDEX IF NOT EXISTS idx_invoices_domain ON invoices(domain);

                CREATE TABLE IF NOT EXISTS pipeline_states (
                    domain TEXT PRIMARY KEY,
                    state TEXT,
                    last_step TEXT,
                    steps_completed TEXT,
                    artifacts TEXT,
                    history TEXT,
                    error TEXT,
                    created_at TEXT,
                    updated_at TEXT
                );
            """)

    def _auto_migrate_from_json(self) -> None:
        """Migrates legacy JSON files to SQLite on first initialization."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM leads")
            leads_count = cursor.fetchone()[0]

            # Migrate leads
            if leads_count == 0 and os.path.exists(HISTORY_JSON_PATH):
                try:
                    with open(HISTORY_JSON_PATH, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    legacy_leads = data.get("leads", {})
                    for dom, item in legacy_leads.items():
                        self.save_lead(item, sync_json=False)
                    if legacy_leads:
                        print(f"[Database] Migrated {len(legacy_leads)} leads from outreach_history.json to SQLite.")
                except Exception as e:
                    print(f"[Database] Error migrating leads from JSON: {e}")

            # Migrate invoices
            cursor.execute("SELECT COUNT(*) FROM invoices")
            inv_count = cursor.fetchone()[0]
            if inv_count == 0 and os.path.exists(INVOICES_JSON_PATH):
                try:
                    with open(INVOICES_JSON_PATH, "r", encoding="utf-8") as f:
                        inv_data = json.load(f)
                    legacy_invoices = inv_data.get("invoices", {})
                    for iid, item in legacy_invoices.items():
                        self.save_invoice(item, sync_json=False)
                    if legacy_invoices:
                        print(f"[Database] Migrated {len(legacy_invoices)} invoices from invoices.json to SQLite.")
                except Exception as e:
                    print(f"[Database] Error migrating invoices from JSON: {e}")

    # --- Leads API ---

    def save_lead(self, data: Dict[str, Any], sync_json: bool = False) -> None:
        domain = data.get("domain", "").strip()
        if not domain:
            return

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        signals = json.dumps(data.get("outdated_signals", []), ensure_ascii=False)
        logs = json.dumps(data.get("logs", []), ensure_ascii=False)

        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO leads (
                    domain, business_name, website_url, whatsapp, email, track,
                    status, payment_status, proposal_pdf, vercel_url, invoice_id,
                    package_zip, outdated_signals, notes, address, city, phone, area_name, primary_channel, created_at, updated_at, logs
                ) VALUES (
                    :domain, :business_name, :website_url, :whatsapp, :email, :track,
                    :status, :payment_status, :proposal_pdf, :vercel_url, :invoice_id,
                    :package_zip, :outdated_signals, :notes, :address, :city, :phone, :area_name, :primary_channel, :created_at, :updated_at, :logs
                )
                ON CONFLICT(domain) DO UPDATE SET
                    business_name=COALESCE(excluded.business_name, leads.business_name),
                    website_url=COALESCE(excluded.website_url, leads.website_url),
                    whatsapp=COALESCE(excluded.whatsapp, leads.whatsapp),
                    email=COALESCE(excluded.email, leads.email),
                    track=COALESCE(excluded.track, leads.track),
                    status=excluded.status,
                    payment_status=COALESCE(excluded.payment_status, leads.payment_status),
                    proposal_pdf=COALESCE(excluded.proposal_pdf, leads.proposal_pdf),
                    vercel_url=COALESCE(excluded.vercel_url, leads.vercel_url),
                    invoice_id=COALESCE(excluded.invoice_id, leads.invoice_id),
                    package_zip=COALESCE(excluded.package_zip, leads.package_zip),
                    outdated_signals=excluded.outdated_signals,
                    notes=COALESCE(excluded.notes, leads.notes),
                    address=COALESCE(NULLIF(excluded.address, ''), leads.address),
                    city=COALESCE(NULLIF(excluded.city, ''), leads.city),
                    phone=COALESCE(NULLIF(excluded.phone, ''), leads.phone),
                    area_name=COALESCE(NULLIF(excluded.area_name, ''), leads.area_name),
                    primary_channel=COALESCE(NULLIF(excluded.primary_channel, ''), leads.primary_channel),
                    updated_at=excluded.updated_at,
                    logs=excluded.logs;
            """, {
                "domain": domain,
                "business_name": data.get("business_name", domain),
                "website_url": data.get("website_url", f"https://{domain}"),
                "whatsapp": data.get("whatsapp", ""),
                "email": data.get("email", ""),
                "track": data.get("track", "track_b_modernize"),
                "status": data.get("status", "discovered"),
                "payment_status": data.get("payment_status", "unpaid"),
                "proposal_pdf": data.get("proposal_pdf", ""),
                "vercel_url": data.get("vercel_url", ""),
                "invoice_id": data.get("invoice_id", ""),
                "package_zip": data.get("package_zip", ""),
                "outdated_signals": signals,
                "notes": data.get("notes", ""),
                "address": data.get("address", ""),
                "city": data.get("city", ""),
                "phone": data.get("phone", ""),
                "area_name": data.get("area_name", ""),
                "primary_channel": data.get("primary_channel", ""),
                "created_at": data.get("created_at", now_str),
                "updated_at": now_str,
                "logs": logs
            })

        if sync_json:
            self.sync_leads_to_json()

    def get_lead(self, domain: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM leads WHERE domain = ?", (domain.strip(),)).fetchone()
            if not row:
                return None
            d = dict(row)
            d["outdated_signals"] = json.loads(d["outdated_signals"]) if d["outdated_signals"] else []
            d["logs"] = json.loads(d["logs"]) if d["logs"] else []
            return d

    def get_all_leads(self) -> Dict[str, Dict[str, Any]]:
        res = {}
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM leads ORDER BY created_at DESC, updated_at DESC").fetchall()
            for r in rows:
                d = dict(r)
                d["outdated_signals"] = json.loads(d["outdated_signals"]) if d["outdated_signals"] else []
                d["logs"] = json.loads(d["logs"]) if d["logs"] else []
                res[d["domain"]] = d
        return res

    def is_already_contacted(self, domain: str, phone: Optional[str] = None, email: Optional[str] = None) -> bool:
        with self._get_connection() as conn:
            # Check domain
            row = conn.execute("SELECT status FROM leads WHERE domain = ?", (domain.strip(),)).fetchone()
            if row and row["status"] in ["sent_whatsapp", "sent_email", "sent_all"]:
                return True

            # Check phone
            if phone and phone.strip():
                p_row = conn.execute(
                    "SELECT 1 FROM leads WHERE whatsapp = ? AND status IN ('sent_whatsapp', 'sent_all')",
                    (phone.strip(),)
                ).fetchone()
                if p_row:
                    return True

            # Check email
            if email and email.strip():
                e_row = conn.execute(
                    "SELECT 1 FROM leads WHERE lower(email) = ? AND status IN ('sent_email', 'sent_all')",
                    (email.strip().lower(),)
                ).fetchone()
                if e_row:
                    return True

        return False

    def sync_leads_to_json(self, output_path: str = HISTORY_JSON_PATH) -> None:
        """Syncs SQLite leads to outreach_history.json for external file inspection."""
        leads = self.get_all_leads()
        data = {
            "leads": leads,
            "last_updated": datetime.now().isoformat()
        }
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    # --- Invoices API ---

    def save_invoice(self, data: Dict[str, Any], sync_json: bool = False) -> None:
        inv_id = data.get("invoice_id", "").strip()
        if not inv_id:
            return

        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO invoices (
                    invoice_id, order_id, domain, business_name, whatsapp, track,
                    usd_price, idr_price, rate, price_display, payment_url, snap_token,
                    status, created_at, expires_at, paid_at, payment_method
                ) VALUES (
                    :invoice_id, :order_id, :domain, :business_name, :whatsapp, :track,
                    :usd_price, :idr_price, :rate, :price_display, :payment_url, :snap_token,
                    :status, :created_at, :expires_at, :paid_at, :payment_method
                )
                ON CONFLICT(invoice_id) DO UPDATE SET
                    order_id=COALESCE(excluded.order_id, invoices.order_id),
                    status=excluded.status,
                    payment_url=COALESCE(excluded.payment_url, invoices.payment_url),
                    snap_token=COALESCE(excluded.snap_token, invoices.snap_token),
                    paid_at=COALESCE(excluded.paid_at, invoices.paid_at),
                    payment_method=COALESCE(excluded.payment_method, invoices.payment_method);
            """, {
                "invoice_id": inv_id,
                "order_id": data.get("order_id", ""),
                "domain": data.get("domain", ""),
                "business_name": data.get("business_name", ""),
                "whatsapp": data.get("whatsapp", ""),
                "track": data.get("track", "track_b_modernize"),
                "usd_price": data.get("usd_price", 100.0),
                "idr_price": data.get("idr_price", 0.0),
                "rate": data.get("rate", 0.0),
                "price_display": data.get("price_display", ""),
                "payment_url": data.get("payment_url", ""),
                "snap_token": data.get("snap_token", ""),
                "status": data.get("status", "pending"),
                "created_at": data.get("created_at", datetime.now().isoformat()),
                "expires_at": data.get("expires_at", ""),
                "paid_at": data.get("paid_at", ""),
                "payment_method": data.get("payment_method", "")
            })

        if sync_json:
            self.sync_invoices_to_json()

    def get_invoice(self, invoice_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM invoices WHERE invoice_id = ?", (invoice_id.strip(),)).fetchone()
            return dict(row) if row else None

    def get_invoice_by_order_id(self, order_id: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM invoices WHERE order_id = ?", (order_id.strip(),)).fetchone()
            return dict(row) if row else None

    def get_all_invoices(self) -> Dict[str, Dict[str, Any]]:
        res = {}
        with self._get_connection() as conn:
            rows = conn.execute("SELECT * FROM invoices ORDER BY created_at DESC").fetchall()
            for r in rows:
                d = dict(r)
                res[d["invoice_id"]] = d
        return res

    def sync_invoices_to_json(self, output_path: str = INVOICES_JSON_PATH) -> None:
        """Syncs SQLite invoices to invoices.json for external file inspection."""
        invoices = self.get_all_invoices()
        data = {
            "invoices": invoices,
            "last_updated": datetime.now().isoformat()
        }
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    # --- Pipeline State API ---

    def save_pipeline_state(self, domain: str, state_data: Dict[str, Any]) -> None:
        with self._get_connection() as conn:
            conn.execute("""
                INSERT INTO pipeline_states (
                    domain, state, last_step, steps_completed, artifacts,
                    history, error, created_at, updated_at
                ) VALUES (
                    :domain, :state, :last_step, :steps_completed, :artifacts,
                    :history, :error, :created_at, :updated_at
                )
                ON CONFLICT(domain) DO UPDATE SET
                    state=excluded.state,
                    last_step=excluded.last_step,
                    steps_completed=excluded.steps_completed,
                    artifacts=excluded.artifacts,
                    history=excluded.history,
                    error=excluded.error,
                    updated_at=excluded.updated_at;
            """, {
                "domain": domain,
                "state": state_data.get("state", "pending"),
                "last_step": state_data.get("last_step", ""),
                "steps_completed": json.dumps(state_data.get("steps_completed", [])),
                "artifacts": json.dumps(state_data.get("artifacts", {})),
                "history": json.dumps(state_data.get("history", [])),
                "error": state_data.get("error", ""),
                "created_at": state_data.get("created_at", datetime.now().isoformat()),
                "updated_at": state_data.get("updated_at", datetime.now().isoformat())
            })

    def get_pipeline_state(self, domain: str) -> Optional[Dict[str, Any]]:
        with self._get_connection() as conn:
            row = conn.execute("SELECT * FROM pipeline_states WHERE domain = ?", (domain.strip(),)).fetchone()
            if not row:
                return None
            d = dict(row)
            d["steps_completed"] = json.loads(d["steps_completed"]) if d["steps_completed"] else []
            d["artifacts"] = json.loads(d["artifacts"]) if d["artifacts"] else {}
            d["history"] = json.loads(d["history"]) if d["history"] else []
            return d


# Singleton instance
_db_instance: Optional[PipelineDatabase] = None


def get_db() -> PipelineDatabase:
    global _db_instance
    if _db_instance is None:
        _db_instance = PipelineDatabase()
    return _db_instance
