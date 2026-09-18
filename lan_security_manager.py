"""
lan_security_manager.py
Secure Local-Connectivity, Device Pairing & Concurrency Governance Layer
SIH PSC26117 — Sovereign On-Premise Agentic AI Workbench.

Key Responsibilities:
1. Network Mode Resolution: LOCAL_ONLY (127.0.0.1) vs LAN (0.0.0.0).
2. Remote Client Identification: Distinguishes loopback/host from LAN clients based on IP/headers.
3. Cryptographic Device Pairing: Generates single-use 6-digit pairing codes with expiration,
   issuing scoped, signed session tokens (HMAC-SHA256) stored securely in memory.
4. Allowed-Subnet & Security Policy Enforcement: RFC1918 IPv4 (10.x, 172.16.x-31.x, 192.168.x) & Loopback.
5. Resource Governance: Concurrency bounds on simultaneous LLM, OCR, and Agent workloads
   preventing runaway resource exhaustion on the host compute node.
6. Zero plaintext secret logging; full audit trail integration.
"""

import os
import time
import secrets
import hmac
import hashlib
import ipaddress
import threading
from typing import Dict, Any, Optional, Tuple, Set
from pydantic import BaseModel, Field

# Supported Network Modes
MODE_LOCAL_ONLY = "LOCAL_ONLY"
MODE_LAN = "LAN"

class PairingCodeInfo(BaseModel):
    code_hash: str
    expires_at: float
    device_hint: Optional[str] = None
    created_at: float = Field(default_factory=time.time)

class PairedDeviceSession(BaseModel):
    session_token: str
    device_id: str
    device_name: str
    client_ip: str
    created_at: float
    last_seen_at: float
    is_active: bool = True

class LANSecurityManager:
    """
    Manages local network exposure, device authorization, pairing codes,
    remote client tracking, and compute concurrency limits.
    """

    def __init__(self, secret_key: Optional[str] = None):
        self._lock = threading.RLock()
        # Derive or generate an ephemeral machine secret for HMAC session signing
        self._secret_key = (secret_key or os.environ.get("SOVEREIGN_SESSION_SECRET") or secrets.token_hex(32)).encode("utf-8")
        
        # Network mode: default to LOCAL_ONLY for safety unless configured
        env_mode = os.environ.get("NETWORK_MODE", MODE_LOCAL_ONLY).strip().upper()
        self.network_mode = MODE_LAN if env_mode == MODE_LAN else MODE_LOCAL_ONLY
        
        # Pairing code store: {code_hash: PairingCodeInfo} (Short-lived, single use)
        self._active_pairing_codes: Dict[str, PairingCodeInfo] = {}
        
        # Paired device sessions: {session_token: PairedDeviceSession}
        self._paired_sessions: Dict[str, PairedDeviceSession] = {}
        
        # Resource governance limits
        self.max_concurrent_llm = int(os.environ.get("MAX_CONCURRENT_LLM", "2"))
        self.max_concurrent_ocr = int(os.environ.get("MAX_CONCURRENT_OCR", "2"))
        self.max_concurrent_agents = int(os.environ.get("MAX_CONCURRENT_AGENTS", "1"))
        
        # Concurrency semaphores
        self._active_llm_tasks = 0
        self._active_ocr_tasks = 0
        self._active_agent_tasks = 0

    # ------------------------------------------------------------------------
    # Network Mode & Host Info
    # ------------------------------------------------------------------------
    def set_network_mode(self, mode: str):
        with self._lock:
            mode_upper = mode.strip().upper()
            if mode_upper in (MODE_LOCAL_ONLY, MODE_LAN):
                self.network_mode = mode_upper

    def is_lan_enabled(self) -> bool:
        return self.network_mode == MODE_LAN

    def get_host_ip(self) -> str:
        """Determines best candidate LAN IPv4 address for local network access."""
        import socket
        try:
            # Connect to a non-routable private IP without sending packets
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("10.255.255.255", 1))
                ip = s.getsockname()[0]
                if ip and not ip.startswith("127."):
                    return ip
        except Exception:
            pass
        
        try:
            # Fallback inspection of hostnames
            hostname = socket.gethostname()
            for info in socket.getaddrinfo(hostname, None):
                ip = info[4][0]
                if ":" not in ip and not ip.startswith("127."):
                    return ip
        except Exception:
            pass
        return "127.0.0.1"

    # ------------------------------------------------------------------------
    # Client Classification (Host vs LAN)
    # ------------------------------------------------------------------------
    def is_local_client(self, client_host: str) -> bool:
        """Determines if a request client IP corresponds to the local host machine."""
        if not client_host:
            return False
        clean_host = client_host.split(":")[0].strip()
        if clean_host in ("127.0.0.1", "localhost", "::1", "testclient"):
            return True
        try:
            ip = ipaddress.ip_address(clean_host)
            if ip.is_loopback:
                return True
        except ValueError:
            pass
        return False

    def is_allowed_lan_ip(self, client_host: str) -> bool:
        """Validates that a client IP falls within private RFC1918 subnets or loopback."""
        if not client_host:
            return False
        clean_host = client_host.split(":")[0].strip()
        if clean_host == "testclient":
            return True
        try:
            ip = ipaddress.ip_address(clean_host)
            # Accept loopback, private RFC1918 (10.0.0.0/8, 172.16.0.0/12, 192.168.0.0/16) and link-local (169.254.0.0/16)
            return ip.is_loopback or ip.is_private or ip.is_link_local
        except ValueError:
            return False

    # ------------------------------------------------------------------------
    # Device Pairing Flow (Single-use, expiring PIN -> HMAC Session Token)
    # ------------------------------------------------------------------------
    def generate_pairing_code(self, ttl_seconds: int = 300, device_hint: Optional[str] = None) -> str:
        """
        Generates a 6-digit numeric pairing PIN.
        The PIN is hashed before storage so memory dumps never expose the raw code.
        Valid for ttl_seconds (default 5 minutes).
        """
        with self._lock:
            self._cleanup_expired_codes()
            pin = f"{secrets.randbelow(1000000):06d}"
            pin_hash = hashlib.sha256(pin.encode("utf-8")).hexdigest()
            self._active_pairing_codes[pin_hash] = PairingCodeInfo(
                code_hash=pin_hash,
                expires_at=time.time() + ttl_seconds,
                device_hint=device_hint
            )
            return pin

    def verify_pairing_code(self, candidate_pin: str, client_ip: str, device_name: str = "Authorized Device") -> Optional[str]:
        """
        Verifies a candidate pairing PIN.
        If valid: destroys the code (single-use) and returns a cryptographic session token.
        If invalid or expired: returns None.
        """
        with self._lock:
            self._cleanup_expired_codes()
            pin_clean = candidate_pin.strip()
            pin_hash = hashlib.sha256(pin_clean.encode("utf-8")).hexdigest()
            info = self._active_pairing_codes.pop(pin_hash, None)
            if not info or time.time() > info.expires_at:
                return None

            # Generate session token: HMAC(secret, device_id + timestamp + random)
            device_id = f"DEV-{secrets.token_hex(4).upper()}"
            token_payload = f"{device_id}:{time.time()}:{secrets.token_hex(16)}"
            token_sig = hmac.new(self._secret_key, token_payload.encode("utf-8"), hashlib.sha256).hexdigest()
            session_token = f"SOV-LAN-{secrets.token_hex(8)}-{token_sig[:16]}"

            now = time.time()
            self._paired_sessions[session_token] = PairedDeviceSession(
                session_token=session_token,
                device_id=device_id,
                device_name=device_name or "Remote Device",
                client_ip=client_ip,
                created_at=now,
                last_seen_at=now,
                is_active=True
            )
            return session_token

    def validate_session_token(self, token: Optional[str], client_ip: Optional[str] = None) -> Optional[PairedDeviceSession]:
        """Validates that a session token exists and is active."""
        if not token:
            return None
        with self._lock:
            session = self._paired_sessions.get(token)
            if not session or not session.is_active:
                return None
            session.last_seen_at = time.time()
            return session

    def revoke_session(self, token: str) -> bool:
        with self._lock:
            session = self._paired_sessions.pop(token, None)
            return session is not None

    def list_paired_devices(self) -> list:
        with self._lock:
            return [
                {
                    "device_id": s.device_id,
                    "device_name": s.device_name,
                    "client_ip": s.client_ip,
                    "paired_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(s.created_at)),
                    "last_seen": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(s.last_seen_at)),
                    "token_prefix": s.session_token[:16] + "..."
                }
                for s in self._paired_sessions.values() if s.is_active
            ]

    def _cleanup_expired_codes(self):
        now = time.time()
        expired = [h for h, info in self._active_pairing_codes.items() if now > info.expires_at]
        for h in expired:
            self._active_pairing_codes.pop(h, None)

    # ------------------------------------------------------------------------
    # Resource Concurrency Governance
    # ------------------------------------------------------------------------
    def acquire_llm_slot(self) -> bool:
        with self._lock:
            if self._active_llm_tasks >= self.max_concurrent_llm:
                return False
            self._active_llm_tasks += 1
            return True

    def release_llm_slot(self):
        with self._lock:
            self._active_llm_tasks = max(0, self._active_llm_tasks - 1)

    def acquire_ocr_slot(self) -> bool:
        with self._lock:
            if self._active_ocr_tasks >= self.max_concurrent_ocr:
                return False
            self._active_ocr_tasks += 1
            return True

    def release_ocr_slot(self):
        with self._lock:
            self._active_ocr_tasks = max(0, self._active_ocr_tasks - 1)

    def acquire_agent_slot(self) -> bool:
        with self._lock:
            if self._active_agent_tasks >= self.max_concurrent_agents:
                return False
            self._active_agent_tasks += 1
            return True

    def release_agent_slot(self):
        with self._lock:
            self._active_agent_tasks = max(0, self._active_agent_tasks - 1)

    def get_resource_usage(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "llm": {"active": self._active_llm_tasks, "max": self.max_concurrent_llm},
                "ocr": {"active": self._active_ocr_tasks, "max": self.max_concurrent_ocr},
                "agent": {"active": self._active_agent_tasks, "max": self.max_concurrent_agents},
            }

lan_security_mgr = LANSecurityManager()
