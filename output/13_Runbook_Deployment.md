# Runbook & Deployment Playbook

**Product Name**: Sovereign On-Premise Agentic AI Workbench (SIH PSC26117)  
**Document Version**: 2.0  
**Target Environment**: Windows 10/11, Ubuntu 22.04 LTS, BOSS Linux  
**Operational Cost**: $0.00 Perpetual  

---

## 1. Zero-Cost Quick Setup & Launch

The entire system requires zero paid licenses, zero subscriptions, and installs on standard 8GB RAM laptops in under 5 minutes.

### 1.1 Prerequisites
- Python 3.10, 3.11, or 3.12 (Free download from python.org)
- Google Chrome or Chromium (Pre-installed on almost all devices)
- (Optional for Hackathon Turbo Mode): Free API key from [console.groq.com](https://console.groq.com) and/or [aistudio.google.com](https://aistudio.google.com)
- (Optional for Sovereign Air-Gapped Mode): Ollama with `llama3:latest` or `bharatgpt`

### 1.2 Installation Commands
```powershell
# 1. Clone or navigate to the project directory
cd C:\Sovereign_AI_Workbench

# 2. Install lightweight dependencies
pip install -r requirements.txt
playwright install chromium

# 3. (Optional) Set free API keys for Hackathon Turbo Mode
$env:GROQ_API_KEY="gsk_free_key_here"
$env:GEMINI_API_KEY="AIza_free_key_here"

# 4. Launch the Sovereign Workbench Control Center
python server.py
```
*The local server starts at **`http://127.0.0.1:8001`** and automatically opens the dashboard in your default browser.*

---

## 2. Pre-Flight Verification Checklist

Before presenting to Smart India Hackathon evaluators, run through this 60-second checklist:
- [x] **FastAPI Health Check**: Navigate to `http://127.0.0.1:8001/api/status` -> verifies `"is_running": false`, status OK.
- [x] **Cookie Vault Check**: Navigate to `http://127.0.0.1:8001/api/workbench/sessions` -> verifies GeM, CPPP, and Local Mock portal sessions are active.
- [x] **Dual-Engine Status**: Ensure Groq/Gemini keys are recognized or local fallback is active.
- [x] **Offline Mock Portal Check**: Navigate to `http://127.0.0.1:8001/portal/gem-tenders` -> verifies the built-in government tender board is rendering correctly.

---

## 3. Step-by-Step Hackathon Live Demonstration Runbook

1. **Step 1: Open Dashboard**: Display the Sovereign AI Workbench Control Center on screen (`http://127.0.0.1:8001`).
2. **Step 2: Highlight Sovereignty & Cookie Vault**: Show the judging jury the **Cookie Session Vault** indicator on screen, highlighting: *"Notice our session is pre-authenticated for the Government e-Marketplace. No passwords to type, no SMS OTP delays."*
3. **Step 3: Submit Natural Language Query**:
   - Click the preset card: **"Check today's tender updates on the government portal"** (or type it in plain English).
   - Click **"Execute Autonomous Task"**.
4. **Step 4: Observe Live Agentic Telemetry**:
   - Point out the real-time WebSocket log stream:
     - `[11:06:01] Analyzing Intent -> Target: GeM Portal`
     - `[11:06:03] Injecting Cookies from Encrypted Vault (Zero OTP)`
     - `[11:06:05] Navigating to portal and extracting dynamic tender rows`
     - `[11:06:07] Dual-Engine LLM Synthesizing Executive Briefing`
5. **Step 5: Review Executive Intelligence Report**:
   - Show the generated briefing on the right panel.
   - Highlight the high-value tenders (₹ 15 Cr NIC AI Workstations, ₹ 28.5 Cr MHA Sovereign LLM Appliance).
   - Point out the actionable deadline alerts and MSME exemption recommendations.
6. **Step 6: Pitch 1-Minute Conclusion**: Emphasize that all data stayed strictly local, zero subscription dollars were spent, and the solution saves Indian desk officers 3.5 hours every day.

---

## 4. Incident Response & Troubleshooting Runbooks

### Runbook A: Groq or Gemini Free API Rate Limit Exceeded (HTTP 429)
- **Symptom**: Telemetry shows `Groq generation failed: 429 Too Many Requests`.
- **Automated Fix**: The `DualEngineLLM` router automatically detects HTTP 429 and cascades immediately to Google Gemini Flash. If Gemini also hits a ceiling, it falls back to the embedded local synthesizer. The UI never crashes.
- **Manual Override**: Toggle the engine selector on the UI header from `Hackathon Turbo` to `Sovereign Air-Gapped`.

### Runbook B: Headless Playwright Launch Failure on Windows
- **Symptom**: `playwright._impl._errors.TargetClosedError`.
- **Immediate Resolution**:
  ```powershell
  python -m playwright install --with-deps chromium
  ```
  Or ensure no orphaned background `chrome.exe` processes are locking the user profile by running:
  ```powershell
  taskkill /F /IM chrome.exe /T
  ```

### Runbook C: Portal Session Cookie Invalidation (HTTP 401)
- **Symptom**: Portal redirects to SSO login screen.
- **Resolution**: Click "Update Session" in the Cookie Vault modal on the dashboard, perform a one-time login in the opened browser window, and click "Save Session". The new session cookies are instantly encrypted and persisted.

---

## 5. Local Network (LAN) Connectivity & Multi-Device Deployment Runbook

### 5.1 Architecture Overview
The Workbench workstation acts as the sovereign compute node (LLM inference, RAG embeddings, OCR, ASR, Agents). Authorized devices (laptops, iPads, tablets, mobile) connect as thin clients via the local Wi-Fi router / switch without requiring internet access.

```
                    SOVEREIGN HOST WORKSTATION
              [Local LLM + RAG + OCR + Agents + Audit]
                                │
                        LAN Gateway (0.0.0.0)
                                │
          ┌─────────────────────┼─────────────────────┐
     mDNS Discovery         Port 8001            Subnet Guard
  (ai-workbench.local)   (HTTP/WebSocket)      (RFC1918 Private)
          │                     │                     │
          └─────────────────────┼─────────────────────┘
                                │
                    AUTHENTICATED LOCAL LAN
                                │
               ┌────────────────┼────────────────┐
         Remote Laptop     Field Tablet     Mobile Device
```

### 5.2 Launch Modes
- **LOCAL_ONLY Mode (Default):** Server binds to `127.0.0.1:8001`. Remote LAN packets are rejected at socket and application layers.
  ```powershell
  $env:NETWORK_MODE="LOCAL_ONLY"
  python server.py
  ```
- **LAN Mode:** Server binds to `0.0.0.0:8001`, advertises `ai-workbench.local` over mDNS (`_http._tcp.local.`), and activates the Device Pairing gate.
  ```powershell
  $env:NETWORK_MODE="LAN"
  python server.py
  ```

### 5.3 Device Pairing Procedure
1. On the primary workstation: Open **Settings** &rarr; **Local Connectivity**.
2. Click **Generate Pairing PIN** (issues single-use 6-digit PIN with 5-minute TTL).
3. On the remote tablet/laptop connected to the same Wi-Fi:
   - Navigate to `http://ai-workbench.local:8001` (or the host LAN IP `http://<host-ip>:8001`).
   - Enter the 6-digit PIN and friendly device label.
   - Click **Authenticate & Connect**.
4. An authenticated HMAC-SHA256 session token is stored in the remote browser cookie/storage.

### 5.4 Windows Firewall Policy
To permit LAN devices to reach port 8001 on Windows:
```powershell
# Run in Administrator PowerShell to allow inbound traffic on private networks:
New-NetFirewallRule -DisplayName "Sovereign AI Workbench LAN Gateway" `
    -Direction Inbound -LocalPort 8001 -Protocol TCP -Action Allow `
    -Profile Private
```

### 5.5 Bluetooth (BLE & Classic) Hardware Status
- **Classic Bluetooth / RFCOMM:** Intentionally not used. RFCOMM offers low throughput, lacks native web browser transport without custom drivers, and duplicates existing authenticated HTTP/WebSocket capabilities.
- **Bluetooth Low Energy (BLE):** Abstracted for future proximity authorization. Standard Windows/Linux cross-platform GATT peripheral/server support in user-space Python requires elevated system daemon pairing. Primary production transport remains high-speed LAN + HTTP/WebSocket + mDNS.