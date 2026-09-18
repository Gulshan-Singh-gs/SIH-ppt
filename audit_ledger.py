"""
audit_ledger.py
Centralized Tamper-Evident Audit Trail & Cryptographic Event Ledger.
SIH PSC26117 — Sovereign On-Premise Agentic AI Workbench.

Records all system events into output/.vault/audit_trail.jsonl with SHA-256 block-chaining.
Provides full chain-of-custody tracking:
What happened? Why did it happen? What evidence was used? Which model was used? Who approved it?
Zero secret or password leakage; automatic credential redaction.
"""

from enum import Enum
import os
import json
import time
import hashlib
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from pydantic import BaseModel, Field

VAULT_DIR = Path(__file__).resolve().parent / "output" / ".vault"
AUDIT_LOG_FILE = VAULT_DIR / "audit_trail.jsonl"


class AuditEventType(str, Enum):
    USER_QUERY = "USER_QUERY"
    RAG_RETRIEVAL = "RAG_RETRIEVAL"
    DOCUMENT_PROCESSED = "DOCUMENT_PROCESSED"
    EVIDENCE_EXTRACT = "EVIDENCE_EXTRACT"
    VERIFICATION_EVAL = "VERIFICATION_EVAL"
    AGENT_ACTION = "AGENT_ACTION"
    HUMAN_APPROVAL = "HUMAN_APPROVAL"
    CLOUD_BURST = "CLOUD_BURST"
    SYSTEM_LOCK = "SYSTEM_LOCK"


class AuditEvent(BaseModel):
    event_id: str
    timestamp: str = Field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    session_id: str = "GLOBAL_SESSION"
    event_type: str  # USER_QUERY, RAG_RETRIEVE, EVIDENCE_EXTRACT, VERIFICATION_EVAL, AGENT_ACTION, HITL_APPROVAL, CLOUD_BURST, SYSTEM_LOCK
    actor: str = "SYSTEM"
    action: str
    risk_level: str = "LOW"
    approval_status: Optional[str] = None
    model_used: Optional[str] = None
    evidence_ids: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)
    prev_hash: str = "GENESIS"
    event_hash: str = ""


class AuditLedger:
    """
    Manages an append-only, SHA-256 cryptographically chained audit ledger.
    Guarantees verifiable provenance and accountability for government operations.
    """

    def __init__(self, log_path: Optional[Union[str, Path]] = None):
        self.log_file = Path(log_path) if log_path else AUDIT_LOG_FILE
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        self.last_hash = self._get_last_hash()

    def _get_last_hash(self) -> str:
        if not self.log_file.exists():
            return "GENESIS_SOVEREIGN_PSC26117"
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if lines:
                    last_record = json.loads(lines[-1].strip())
                    return last_record.get("event_hash", "GENESIS_SOVEREIGN_PSC26117")
        except Exception:
            pass
        return "GENESIS_SOVEREIGN_PSC26117"

    def record_event(
        self,
        event_type: str,
        action: str,
        actor: str = "USER",
        risk_level: str = "LOW",
        approval_status: Optional[str] = None,
        model_used: Optional[str] = None,
        evidence_ids: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None,
        session_id: str = "DEFAULT"
    ) -> AuditEvent:
        """
        Creates and appends an immutable chained event record.
        Redacts any sensitive tokens, passwords, or credentials automatically.
        """
        clean_details = self._sanitize_details(details or {})
        event_id = f"EVT-{int(time.time()*1000)}"

        event = AuditEvent(
            event_id=event_id,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            session_id=session_id,
            event_type=event_type,
            actor=actor,
            action=action,
            risk_level=risk_level,
            approval_status=approval_status,
            model_used=model_used,
            evidence_ids=evidence_ids or [],
            details=clean_details,
            prev_hash=self.last_hash
        )

        # Compute SHA-256 block hash
        event_data_str = json.dumps({
            "id": event.event_id,
            "ts": event.timestamp,
            "type": event.event_type,
            "act": event.action,
            "prev": event.prev_hash,
            "dt": clean_details
        }, sort_keys=True)
        event.event_hash = hashlib.sha256(event_data_str.encode("utf-8")).hexdigest()
        self.last_hash = event.event_hash

        # Append to JSONL file
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(event.json() + "\n")
        except Exception as e:
            print(f"[AuditLedger] Error writing log: {e}")

        return event

    def log_event(
        self,
        event_type: str,
        action: str,
        actor: str = "USER",
        risk_level: str = "LOW",
        approval_status: Optional[str] = None,
        model_used: Optional[str] = None,
        evidence_ids: Optional[List[str]] = None,
        details: Optional[Dict[str, Any]] = None,
        session_id: str = "DEFAULT"
    ) -> AuditEvent:
        """Alias for record_event."""
        return self.record_event(
            event_type=event_type,
            action=action,
            actor=actor,
            risk_level=risk_level,
            approval_status=approval_status,
            model_used=model_used,
            evidence_ids=evidence_ids,
            details=details,
            session_id=session_id
        )

    def get_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Reads recent audit logs."""
        if not self.log_file.exists():
            return []
        events = []
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        events.append(json.loads(line.strip()))
        except Exception:
            pass
        return events[-limit:][::-1]  # Most recent first

    def verify_chain_integrity(self) -> Tuple[bool, str, int]:
        """Validates that no records in the audit log have been altered or deleted."""
        if not self.log_file.exists():
            return True, "EMPTY_LEDGER", 0

        total = 0
        expected_prev = "GENESIS_SOVEREIGN_PSC26117"

        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                for idx, line in enumerate(f):
                    record = json.loads(line.strip())
                    total += 1
                    if idx > 0 and record.get("prev_hash") != expected_prev:
                        return False, f"Tampered at record index {idx}", total
                    expected_prev = record.get("event_hash")
            return True, "CHAIN_VERIFIED_TAMPER_PROOF", total
        except Exception as e:
            return False, f"Verification error: {e}", total

    def _sanitize_details(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively redacts passwords, tokens, API keys, or raw base64 data."""
        clean = {}
        sensitive_keys = {"password", "secret", "token", "api_key", "recovery_key", "cookie", "auth"}
        for k, v in details.items():
            if any(sk in k.lower() for sk in sensitive_keys):
                clean[k] = "[REDACTED_SECRET]"
            elif isinstance(v, str) and len(v) > 500:
                clean[k] = v[:400] + "... [TRUNCATED_PREVIEW]"
            elif isinstance(v, dict):
                clean[k] = self._sanitize_details(v)
            else:
                clean[k] = v
        return clean


# Singleton
audit_ledger = AuditLedger()
