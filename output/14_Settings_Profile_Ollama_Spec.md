# Sovereign AI Workbench — Settings Hub, Profile Security & Ollama Engine Specification
**Specification ID:** SIH-PSC26117-SETTINGS-V1  
**Target Milestone:** Comprehensive Settings Bar, User Profile Vault, Automated Ollama Manager, and Interactive Document Hub  

---

## 1. Executive Summary
This document specifies the architecture for four interconnected subsystems in the Sovereign On-Premise Agentic AI Workbench:
1. **User Profile & Air-Gapped Security Vault**: User name, custom avatar, password protection, session lock, and Dual-Layer Sovereign Password Recovery (16-char Master Recovery Key + Local Computer Physical Proof).
2. **Automated Ollama Manager & Device-Aware Model Hub**: OS/RAM/CPU hardware detection, recommended AI models tailored to device specifications, real-time download streaming telemetry with Pause/Cancel/Switch controls, and an "Unload from RAM" button.
3. **Dual Working Engine & Sovereign Network Kill Switch**: Balanced (50/50) vs. Server-Only vs. Browser-Only workload splitting, hardware air-gap network kill switch, and Cookie Vault token expiration alerts.
4. **Enhanced Document Manager (View Documents)**: Table/list view with multi-select checkboxes, "Select All", "Delete Selected", and "Download Selected as ZIP".

---

## 2. Subsystem Architecture

### 2.1 User Profile & Password Recovery Architecture
- **Profile Data (`output/.vault/profile.json`)**:
  - `name`: String (default: "Executive User")
  - `avatar`: String (base64 or preset SVG path)
  - `password_hash`: String (PBKDF2/SHA256 salted hash)
  - `recovery_key_hash`: String (16-char master emergency recovery key)
  - `is_locked`: Boolean
  - `lock_on_idle_minutes`: Integer (default: 15)
- **Recovery Mechanisms**:
  1. **Primary**: User supplies 16-character Emergency Recovery Key (`SOV-XXXX-XXXX-XXXX`).
  2. **Secondary (Physical Workstation)**: An emergency physical reset token is stored in `output/.vault/recovery.key`. Anyone with physical workstation privileges can read or verify the token to unlock the profile without external internet connectivity.

### 2.2 Automated Ollama Manager & Model Hub
- **Hardware Profile Inspection (`/api/system/hardware`)**:
  - `os`: Windows 64-bit (`win32`)
  - `total_ram_gb`: Measured via `psutil` or `ctypes.windll.kernel32.GlobalMemoryStatusEx`
  - `cpu_cores`: Physical & logical count
  - `disk_free_gb`: Free space on drive `C:\`
- **Device-Aware Recommendation Engine**:
  - `< 8 GB RAM`: Llama 3.2 1B (~1.3 GB download, 2.2 GB RAM), Qwen 2.5 1.5B (~980 MB)
  - `8 - 16 GB RAM`: Llama 3.2 3B (~2.0 GB download, 3.8 GB RAM), Llama 3.1 8B (~4.7 GB download, 6.5 GB RAM)
  - `> 16 GB RAM`: DeepSeek-R1 8B (~4.9 GB download, 7.0 GB RAM), Mistral 7B (~4.1 GB download)
- **Live Model Download Telemetry (`/api/ollama/pull`, `/api/ollama/pull-status`, `/api/ollama/pull-cancel`)**:
  - Streams Ollama pull progress events (`status`, `completed`, `total`, `percent`)
  - Provides controls to **Pause**, **Cancel**, and **Switch Model** (aborts previous pull cleanly)
  - **Unload Model from RAM (`/api/ollama/unload`)**: Sends empty keep_alive to Ollama to immediately free memory.

### 2.3 Interactive Documents Hub Multi-Select
- **API Endpoints**:
  - `POST /api/files/batch-delete`: Accepts `{ "files": ["file1.csv", "file2.docx"] }` and removes them safely from `output/uploads/`.
  - `POST /api/files/batch-zip`: Accepts `{ "files": [...] }` and returns a compressed archive of selected files.
- **Frontend UI**:
  - Header with "Select All" checkbox and batch toolbar ("Delete Selected", "Download ZIP", "Total Selected: N").
  - Row checkboxes for each document.

---

## 3. Security & Data Sovereignty Guarantees
- 100% On-Premise: All password hashing, recovery key generation, and file deletion occur locally on the user's computer.
- Strict Network Kill Switch: When activated, `server.py` rejects non-localhost outgoing network calls, ensuring air-gapped isolation.
