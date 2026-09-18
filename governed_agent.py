"""
governed_agent.py
Controlled Agent Architecture & Human-in-the-Loop (HITL) Governance.
SIH PSC26117 — Sovereign On-Premise Agentic AI Workbench.

Enforces deterministic risk classification:
- LOW RISK: Read-only portal scans, public tender summaries, local text processing. (Auto-executed)
- MEDIUM RISK: Preparing local drafts, modifying workspace indexes. (Validated & Logged)
- HIGH RISK: Submitting official bid proposals, injecting credentials, deleting files, external cloud data offloading.
  (Halts execution -> Requests explicit human officer sign-off -> Continues only upon cryptographic or explicit approval)
"""

from enum import Enum
import asyncio
import time
import uuid
from typing import Dict, Any, List, Optional, Callable
from pydantic import BaseModel, Field


class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ActionPolicyDecision(BaseModel):
    action_id: str = Field(default_factory=lambda: f"ACT-{uuid.uuid4().hex[:8].upper()}")
    action_type: str
    target: str = ""
    parameters: Dict[str, Any] = Field(default_factory=dict)
    risk_level: str = "LOW"
    is_allowed: bool = True
    requires_human_approval: bool = False
    human_approval_granted: Optional[bool] = None
    policy_reason: str = ""
    reviewed_by: Optional[str] = None


class AgentActionRequest(BaseModel):
    action_id: str = Field(default_factory=lambda: f"ACT-{uuid.uuid4().hex[:8].upper()}")
    action_type: str  # browse_read, ocr_extract, summarize, file_modify, submit_bid, portal_write, cloud_burst
    description: str = ""
    target: str = ""
    payload: Dict[str, Any] = Field(default_factory=dict)
    risk_level: str = "LOW"  # LOW, MEDIUM, HIGH
    requires_approval: bool = False
    status: str = "PENDING"  # PENDING, APPROVED, REJECTED, EXECUTED, FAILED
    requested_at: str = Field(default_factory=lambda: time.strftime("%Y-%m-%d %H:%M:%S"))
    decision_reason: str = ""
    approved_by: Optional[str] = None
    decided_at: Optional[str] = None

    @property
    def request_id(self) -> str:
        return self.action_id

    def dict(self, *args, **kwargs):
        d = super().dict(*args, **kwargs)
        d["request_id"] = self.action_id
        return d

    @property
    def is_allowed(self) -> bool:
        return self.status in ["APPROVED", "EXECUTED"]

    @property
    def human_approval_granted(self) -> bool:
        return self.status in ["APPROVED", "EXECUTED"]

    @property
    def policy_reason(self) -> str:
        return self.decision_reason

    @property
    def reviewed_by(self) -> Optional[str]:
        return self.approved_by


class GovernedAgentController:
    """
    Deterministic safety policy wrapper for TenderAgent and browser automation tools.
    Prevents autonomous agents from executing consequential or irreversible actions
    without explicit Human-in-the-Loop authorization.
    """

    # Deterministic Risk Policy Table
    HIGH_RISK_KEYWORDS = {
        "submit", "post", "send", "upload", "delete", "purchase", "pay", "order",
        "tender_submit", "bid_submit", "cloud_transfer", "commit_record", "publish", "approve"
    }

    MEDIUM_RISK_KEYWORDS = {
        "export", "download", "write_file", "save_draft", "update_config", "reindex"
    }

    def __init__(self):
        self.pending_approvals: Dict[str, AgentActionRequest] = {}
        self.approval_futures: Dict[str, asyncio.Future] = {}

    def classify_risk(self, action_type: str, description: str, payload: Dict[str, Any]) -> str:
        """
        Determines deterministic risk level: LOW, MEDIUM, or HIGH.
        Does not allow LLM output to self-grant authority.
        """
        combined = f"{action_type} {description} {json_summary(payload)}".lower()

        # High risk checks
        if any(k in combined for k in self.HIGH_RISK_KEYWORDS):
            return "HIGH"

        # Explicit action types
        if action_type in {"submit_bid", "portal_write", "cloud_burst", "file_delete"}:
            return "HIGH"

        # Medium risk checks
        if any(k in combined for k in self.MEDIUM_RISK_KEYWORDS) or action_type in {"file_modify", "export"}:
            return "MEDIUM"

        return "LOW"

    def evaluate_risk(
        self,
        action_type: str,
        target_url: str = "",
        parameters: Optional[Dict[str, Any]] = None,
        description: str = ""
    ) -> ActionPolicyDecision:
        """Synchronous risk classifier returning an ActionPolicyDecision."""
        params = parameters or {}
        desc = description or f"Execute {action_type} on {target_url}"
        risk = self.classify_risk(action_type, desc, params)
        requires_approval = (risk == "HIGH")
        return ActionPolicyDecision(
            action_type=action_type,
            target=target_url,
            parameters=params,
            risk_level=risk,
            is_allowed=not requires_approval,
            requires_human_approval=requires_approval,
            policy_reason="High risk action requires human authorization" if requires_approval else "Low risk clearance"
        )

    async def evaluate_and_gate(
        self,
        action_type: str,
        description: str = "",
        target: str = "",
        payload: Optional[Dict[str, Any]] = None,
        telemetry_cb: Optional[Callable[[Dict[str, Any]], Any]] = None,
        timeout_seconds: float = 60.0,
        target_url: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None
    ) -> AgentActionRequest:
        """
        Evaluates action risk. If HIGH, pauses execution and waits for human approval.
        """
        resolved_target = target or target_url or ""
        resolved_payload = payload or parameters or {}
        resolved_desc = description or f"Execute {action_type} on {resolved_target}"

        risk_level = self.classify_risk(action_type, resolved_desc, resolved_payload)
        requires_approval = (risk_level == "HIGH")

        action = AgentActionRequest(
            action_type=action_type,
            description=resolved_desc,
            target=resolved_target,
            payload=resolved_payload,
            risk_level=risk_level,
            requires_approval=requires_approval,
            status="PENDING" if requires_approval else "APPROVED",
            decision_reason="Automatic low-risk clearance" if not requires_approval else "High-risk action requires human authorization"
        )

        if not requires_approval:
            action.status = "EXECUTED"
            if telemetry_cb:
                await emit(telemetry_cb, {
                    "step": "POLICY_CHECK",
                    "status": "APPROVED",
                    "message": f"Action [{action.action_id}] auto-approved: {resolved_desc} (Risk: {risk_level})",
                    "action": action.dict()
                })
            return action

        # Action is HIGH risk -> Enter Human-in-the-Loop Approval Gate
        self.pending_approvals[action.action_id] = action
        loop = asyncio.get_event_loop()
        fut = loop.create_future()
        self.approval_futures[action.action_id] = fut

        if telemetry_cb:
            await emit(telemetry_cb, {
                "step": "APPROVAL_REQUIRED",
                "status": "PAUSED",
                "message": f"PAUSED: Officer authorization required for '{resolved_desc}'.",
                "action": action.dict()
            })

        try:
            # Wait for human officer decision via REST / WebSocket
            approved = await asyncio.wait_for(fut, timeout=timeout_seconds)
            action.status = "APPROVED" if approved else "REJECTED"
            action.decided_at = time.strftime("%Y-%m-%d %H:%M:%S")
            action.decision_reason = "Approved by authorized officer" if approved else "Rejected by officer"
        except asyncio.TimeoutError:
            action.status = "REJECTED"
            action.decided_at = time.strftime("%Y-%m-%d %H:%M:%S")
            action.decision_reason = f"Human approval timed out after {timeout_seconds}s. Safe fallback enforced."
        finally:
            self.pending_approvals.pop(action.action_id, None)
            self.approval_futures.pop(action.action_id, None)

        if telemetry_cb:
            await emit(telemetry_cb, {
                "step": "APPROVAL_DECISION",
                "status": "SUCCESS" if action.status == "APPROVED" else "WARNING",
                "message": f"Action [{action.action_id}] {action.status}: {action.decision_reason}",
                "action": action.dict()
            })

        return action

    def submit_decision(
        self,
        action_id: str = "",
        approved: bool = False,
        officer_name: str = "Executive User",
        request_id: str = "",
        reviewed_by: Optional[str] = None,
        reason: Optional[str] = None
    ) -> bool:
        """Called when user clicks 'Approve' or 'Reject' on the UI modal."""
        act_id = request_id or action_id
        officer = reviewed_by or officer_name
        if act_id in self.approval_futures and not self.approval_futures[act_id].done():
            action = self.pending_approvals.get(act_id)
            if action:
                action.approved_by = officer
                if reason:
                    action.decision_reason = reason
            self.approval_futures[act_id].set_result(approved)
            return True
        return False

    def list_pending(self) -> List[Dict[str, Any]]:
        return [a.dict() for a in self.pending_approvals.values()]

    def get_pending_requests(self) -> List[Dict[str, Any]]:
        return self.list_pending()


def json_summary(d: Dict[str, Any]) -> str:
    try:
        return " ".join(f"{k}:{v}" for k, v in d.items())
    except Exception:
        return ""


async def emit(cb, payload: Dict[str, Any]):
    if cb:
        if asyncio.iscoroutinefunction(cb):
            await cb(payload)
        else:
            cb(payload)


# Singleton instance
governed_agent = GovernedAgentController()
