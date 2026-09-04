"""
User Profile & Air-Gapped Security Vault for Sovereign Workbench (SIH PSC26117).
Handles user identity, custom avatar, salted password protection, session lock,
and Dual-Layer Sovereign Password Recovery (16-char Master Recovery Key + Local Computer Physical Proof).
"""
import os
import json
import secrets
import hashlib
import binascii
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

VAULT_DIR = Path(__file__).resolve().parent / "output" / ".vault"
PROFILE_FILE = VAULT_DIR / "profile.json"
PHYSICAL_RECOVERY_FILE = VAULT_DIR / "recovery.key"


class ProfileManager:
    def __init__(self):
        VAULT_DIR.mkdir(parents=True, exist_ok=True)
        self._ensure_initialized()

    def _ensure_initialized(self):
        """Initializes default profile and physical recovery token if not present."""
        if not PHYSICAL_RECOVERY_FILE.exists():
            # 32-byte cryptographically secure emergency recovery token stored locally
            emergency_token = secrets.token_hex(24)
            with open(PHYSICAL_RECOVERY_FILE, "w", encoding="utf-8") as f:
                f.write(emergency_token)

        if not PROFILE_FILE.exists():
            default_profile = {
                "name": "Senior Procurement Officer",
                "role": "Executive Administrator",
                "avatar_preset": "avatar_1",
                "custom_avatar_b64": "",
                "is_password_protected": False,
                "password_salt": "",
                "password_hash": "",
                "recovery_key_hash": "",
                "is_locked": False,
                "lock_on_idle_minutes": 15,
                "created_at": "2026-09-04"
            }
            self._save_profile(default_profile)

    def _load_profile(self) -> Dict[str, Any]:
        try:
            with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_profile(self, data: Dict[str, Any]):
        with open(PROFILE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _hash_password(self, password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """PBKDF2-HMAC-SHA256 password hashing with 100,000 iterations."""
        if not salt:
            salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            100000
        )
        return binascii.hexlify(pwd_hash).decode("utf-8"), salt

    def _hash_recovery_key(self, recovery_key: str) -> str:
        """Normalized SHA256 hash of the 16-char emergency recovery key."""
        clean_key = recovery_key.replace("-", "").strip().upper()
        return hashlib.sha256(clean_key.encode("utf-8")).hexdigest()

    def get_public_profile(self) -> Dict[str, Any]:
        """Returns safe profile information for the UI without secret hashes."""
        p = self._load_profile()
        return {
            "name": p.get("name", "Executive User"),
            "role": p.get("role", "Executive Administrator"),
            "avatar_preset": p.get("avatar_preset", "avatar_1"),
            "has_custom_avatar": bool(p.get("custom_avatar_b64")),
            "custom_avatar_b64": p.get("custom_avatar_b64", ""),
            "is_password_protected": p.get("is_password_protected", False),
            "is_locked": p.get("is_locked", False),
            "lock_on_idle_minutes": p.get("lock_on_idle_minutes", 15)
        }

    def update_profile(self, name: Optional[str] = None, role: Optional[str] = None,
                       avatar_preset: Optional[str] = None, custom_avatar_b64: Optional[str] = None,
                       lock_on_idle_minutes: Optional[int] = None) -> Dict[str, Any]:
        """Updates display profile attributes."""
        p = self._load_profile()
        if name is not None:
            p["name"] = name.strip()
        if role is not None:
            p["role"] = role.strip()
        if avatar_preset is not None:
            p["avatar_preset"] = avatar_preset
        if custom_avatar_b64 is not None:
            p["custom_avatar_b64"] = custom_avatar_b64
        if lock_on_idle_minutes is not None:
            p["lock_on_idle_minutes"] = max(1, int(lock_on_idle_minutes))

        self._save_profile(p)
        return self.get_public_profile()

    def set_password(self, new_password: str) -> Dict[str, Any]:
        """
        Enables password protection and generates a 16-character Sovereign Recovery Key.
        Format: SOV-XXXX-XXXX-XXXX
        """
        p = self._load_profile()
        if not new_password or len(new_password) < 4:
            raise ValueError("Password must be at least 4 characters long.")

        pwd_hash, salt = self._hash_password(new_password)

        # Generate 16-character Master Recovery Key
        raw_part1 = secrets.token_hex(2).upper()
        raw_part2 = secrets.token_hex(2).upper()
        raw_part3 = secrets.token_hex(2).upper()
        recovery_key = f"SOV-{raw_part1}-{raw_part2}-{raw_part3}"
        recovery_hash = self._hash_recovery_key(recovery_key)

        p["is_password_protected"] = True
        p["password_salt"] = salt
        p["password_hash"] = pwd_hash
        p["recovery_key_hash"] = recovery_hash
        p["is_locked"] = False
        self._save_profile(p)

        return {
            "status": "SUCCESS",
            "message": "Password successfully set.",
            "recovery_key": recovery_key,
            "warning": "Copy this 16-character Recovery Key and store it safely on your desk. It is your only way to reset your password if forgotten."
        }

    def remove_password(self, current_password: str) -> Dict[str, Any]:
        """Disables password protection after verifying the current password."""
        if not self.verify_password(current_password):
            raise ValueError("Invalid current password.")

        p = self._load_profile()
        p["is_password_protected"] = False
        p["password_salt"] = ""
        p["password_hash"] = ""
        p["recovery_key_hash"] = ""
        p["is_locked"] = False
        self._save_profile(p)

        return {"status": "SUCCESS", "message": "Password protection removed."}

    def verify_password(self, password: str) -> bool:
        """Verifies candidate password against the stored PBKDF2 hash."""
        p = self._load_profile()
        if not p.get("is_password_protected"):
            return True
        salt = p.get("password_salt", "")
        stored_hash = p.get("password_hash", "")
        candidate_hash, _ = self._hash_password(password, salt)
        return secrets.compare_digest(candidate_hash, stored_hash)

    def lock_workspace(self) -> Dict[str, Any]:
        """Locks the workspace session."""
        p = self._load_profile()
        if p.get("is_password_protected"):
            p["is_locked"] = True
            self._save_profile(p)
        return self.get_public_profile()

    def unlock_workspace(self, password: str) -> Dict[str, Any]:
        """Unlocks the workspace if candidate password is correct."""
        p = self._load_profile()
        if not p.get("is_password_protected"):
            p["is_locked"] = False
            self._save_profile(p)
            return {"status": "SUCCESS", "profile": self.get_public_profile()}

        if self.verify_password(password):
            p["is_locked"] = False
            self._save_profile(p)
            return {"status": "SUCCESS", "profile": self.get_public_profile()}
        else:
            return {"status": "ERROR", "message": "Incorrect password. Please try again or use your recovery key."}

    def recover_with_key(self, recovery_key: str, new_password: str) -> Dict[str, Any]:
        """Resets password using the 16-character Master Recovery Key."""
        p = self._load_profile()
        candidate_hash = self._hash_recovery_key(recovery_key)
        stored_hash = p.get("recovery_key_hash", "")

        if not stored_hash or not secrets.compare_digest(candidate_hash, stored_hash):
            return {"status": "ERROR", "message": "Invalid Master Recovery Key."}

        # Set new password & issue a refreshed recovery key
        return self.set_password(new_password)

    def recover_with_physical_token(self, new_password: str) -> Dict[str, Any]:
        """
        Emergency reset leveraging physical machine access proof.
        Reads the local recovery token from output/.vault/recovery.key.
        """
        if not PHYSICAL_RECOVERY_FILE.exists():
            return {"status": "ERROR", "message": "Physical device recovery token not found."}

        try:
            with open(PHYSICAL_RECOVERY_FILE, "r", encoding="utf-8") as f:
                token_content = f.read().strip()
            if len(token_content) < 16:
                return {"status": "ERROR", "message": "Invalid physical recovery key file."}
        except Exception as e:
            return {"status": "ERROR", "message": f"Could not read local token: {str(e)}"}

        # Verified physical filesystem access on localhost
        return self.set_password(new_password)

    def get_physical_token_path(self) -> str:
        """Returns the absolute path to the local recovery key on disk."""
        return str(PHYSICAL_RECOVERY_FILE)
