"""
Pipeline State Machine & Checkpoint Manager.
Tracks execution states of client pipelines and enables seamless resuming on failure.
"""

import os
import json
from enum import Enum
from datetime import datetime
from typing import Dict, Any, Optional


class PipelineState(str, Enum):
    PENDING = "pending"
    SCRAPED = "scraped"
    STYLE_ANALYZED = "style_analyzed"
    AUDITED = "audited"
    QUOTED = "quoted"
    GENERATED = "generated"
    DEPLOYED = "deployed"
    PDF_READY = "pdf_ready"
    PACKAGED = "packaged"
    COMPLETE = "complete"
    FAILED = "failed"


STATE_ORDER = [
    PipelineState.PENDING,
    PipelineState.SCRAPED,
    PipelineState.STYLE_ANALYZED,
    PipelineState.AUDITED,
    PipelineState.QUOTED,
    PipelineState.GENERATED,
    PipelineState.DEPLOYED,
    PipelineState.PDF_READY,
    PipelineState.PACKAGED,
    PipelineState.COMPLETE
]


class PipelineCheckpoint:
    """Manages pipeline checkpoint state in SQLite Database."""

    def __init__(self, domain: str, output_dir: str = ""):
        self.domain = domain
        from pipeline.db.database import get_db
        self.db = get_db()
        self.data = self._load()

    def _load(self) -> Dict[str, Any]:
        state_data = self.db.get_pipeline_state(self.domain)
        if state_data:
            return state_data

        return {
            "state": PipelineState.PENDING.value,
            "last_step": None,
            "steps_completed": [],
            "artifacts": {},
            "history": [],
            "error": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

    def save(
        self,
        state: PipelineState,
        step_name: str,
        artifacts: Optional[Dict[str, str]] = None,
        error: Optional[str] = None
    ) -> None:
        """Records state advancement and persists checkpoint to database."""
        now_str = datetime.now().isoformat()
        self.data["state"] = state.value if isinstance(state, PipelineState) else str(state)
        self.data["last_step"] = step_name
        self.data["updated_at"] = now_str
        self.data["error"] = error

        if step_name and step_name not in self.data["steps_completed"] and not error:
            self.data["steps_completed"].append(step_name)

        if artifacts:
            self.data.setdefault("artifacts", {}).update(artifacts)

        self.data.setdefault("history", []).append({
            "timestamp": now_str,
            "state": self.data["state"],
            "step": step_name,
            "error": error
        })

        self.db.save_pipeline_state(self.domain, self.data)

    @property
    def current_state(self) -> PipelineState:
        try:
            return PipelineState(self.data.get("state", PipelineState.PENDING.value))
        except ValueError:
            return PipelineState.PENDING

    def has_completed(self, step_name: str) -> bool:
        return step_name in self.data.get("steps_completed", [])

    def is_state_reached_or_passed(self, target_state: PipelineState) -> bool:
        curr = self.current_state
        if curr == PipelineState.FAILED:
            return False
        try:
            curr_idx = STATE_ORDER.index(curr)
            target_idx = STATE_ORDER.index(target_state)
            return curr_idx >= target_idx
        except ValueError:
            return False

    def get_artifact(self, name: str) -> Optional[str]:
        return self.data.get("artifacts", {}).get(name)
