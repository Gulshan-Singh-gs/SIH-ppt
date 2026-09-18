# User Journey Maps & Flowcharts

**Product Name**: Sovereign On-Premise Agentic AI Workbench (SIH PSC26117)  
**Document Version**: 2.0  
**Status**: Approved Architecture Baseline  

---

## 1. Executive Overview

This document visualizes the exact interaction flows for government personnel using the Sovereign AI Workbench. It captures the four core user journeys:
1. **Journey 1**: The Morning Government Tender Audit (Primary SIH Demo Flow)
2. **Journey 2**: One-Time Session Capture & Encrypted Cookie Vault Storage
3. **Journey 3**: Dual-Engine Task Execution (Groq/Gemini Turbo vs Local Air-Gapped)
4. **Journey 4**: Edge-Case Handling (Portal Downtime, Session Expiry, and Captcha Fallback)

---

## 2. Journey 1: The Morning Tender Audit ("Check today's tender updates on the government portal")

### 2.1 Journey Table
| Stage | Officer Action | AI Workbench Action | Emotional State | Friction Removed |
| :--- | :--- | :--- | :--- | :--- |
| **1. Query Dispatch** | Types *"Check today's tender updates on the government portal"* into text box or clicks preset. | Validates syntax, parses intent into semantic target (`GeM Portal -> Active Tenders`). | Optimistic, curious | No complex search filters needed. |
| **2. Auth Rehydration** | Sits back and watches live telemetry status. | Retrieves pre-saved cookies from Cookie Vault; prepares Playwright context. | Relieved | **No password typing, no SMS OTP wait.** |
| **3. Autonomous Crawl**| Observes browser status indicator (`Scanning tables...`). | Launches browser headlessly (or visible), injects cookies, navigates to portal, extracts table DOM. | Confident | Eliminates 20+ manual tab clicks. |
| **4. Synthesis** | Views progress indicator on dashboard. | Routes structured rows to Dual-Engine LLM; filters by department priority. | Impressed | Instant synthesis replaces tedious reading. |
| **5. Briefing Review** | Reads formatted executive briefing, reviews urgency badges, clicks "Export PDF/MD". | Saves markdown report to local disk; alerts officer of 48-hour deadline on NIC tender. | Empowered | 3.5 hours of daily toil reduced to 10 seconds. |

### 2.2 Mermaid Sequence Diagram: Primary Tender Discovery Flow
```mermaid
sequenceDiagram
    autonumber
    actor Officer as Government Officer (MeitY)
    participant UI as Workbench Control Center (Web UI)
    participant Agent as Autonomous Tender Agent
    participant Vault as Cookie Session Vault
    participant Browser as Playwright Browser Engine
    participant Portal as Government Portal (GeM / CPPP)
    participant LLM as Dual-Engine Router (Groq/Gemini/Local)

    Officer->>UI: Types "Check today's tender updates on government portal"
    UI->>Agent: Dispatch Task Request (query, engine_preference)
    Agent->>UI: Stream Telemetry: "Analyzing Intent..."
    
    Agent->>Vault: Query active session for "gem.gov.in"
    Vault-->>Agent: Return preserved session cookies
    Agent->>UI: Stream Telemetry: "Bypassing OTP via Cookie Vault..."

    Agent->>Browser: Launch Chromium Context with Injected Cookies
    Browser->>Portal: GET /portal/gem-tenders (Authenticated Request)
    Portal-->>Browser: HTTP 200 OK (Full Access, No Login Required)
    
    Browser->>Agent: Extract Raw DOM Table Rows (Tender ID, Org, Value, Deadline)
    Agent->>UI: Stream Telemetry: "Extracted 4 Active Tender Notices"

    Agent->>LLM: Send Extracted Data + Executive Synthesis Prompt
    Note over LLM: Groq LLaMA-3.3 (0.4s) OR Local BharatGPT (Air-Gapped)
    LLM-->>Agent: Formatted Executive Markdown Briefing
    
    Agent->>UI: Telemetry: "Task Completed in 8.7s"
    Agent->>UI: Render Interactive Report on Officer Dashboard
    Officer->>UI: Clicks "Download Report (.md)"
```

---

## 3. Journey 2: One-Time Session Capture & Cookie Vault Storage

### 3.1 Mermaid Flowchart: Cookie Vault Lifecycle
```mermaid
flowchart TD
    Start([Officer Opens Portal in Browser]) --> Login[Officer Authenticates Manually Once via SSO / OTP]
    Login --> Verify[Portal Issues Session Cookies: GEM_SSO_SESSION, NIC_ID]
    Verify --> Capture[Workbench Auto-Captures Browser Storage State]
    Capture --> Encrypt[Encrypt Cookies with AES-256-GCM]
    Encrypt --> Store[(Local Encrypted Store: portal_sessions.json)]
    Store --> Ready([Vault Status: Authenticated - Zero OTP Active])
    
    Ready --> AutonomousRun[Autonomous Agent Runs Next Morning]
    AutonomousRun --> Load[Read portal_sessions.json]
    Load --> Inject[Inject Cookies into Playwright Context]
    Inject --> DirectAccess[Direct Authenticated Access to Portal]
```

---

## 4. Journey 3: Dual-Engine LLM Selection & Self-Healing Execution

### 4.1 Flowchart: Free Cloud Turbo vs Local Sovereign Mode
```mermaid
flowchart TD
    Prompt[Officer / Hackathon Prompt Received] --> CheckEngine{Selected Engine Mode?}
    
    CheckEngine -->|Hackathon Turbo| CheckGroq{Groq API Key Configured?}
    CheckGroq -->|Yes| RunGroq[Execute Groq LLaMA-3.3-70B\n~500 t/s, Latency < 500ms]
    CheckGroq -->|No / Limit Hit| CheckGemini{Gemini API Key Configured?}
    
    CheckGemini -->|Yes| RunGemini[Execute Gemini 1.5 Flash Free API\n~200 t/s, Latency < 1.2s]
    CheckGemini -->|No / Limit Hit| LocalOllama[Execute Local Sovereign Model\nOllama / BharatGPT / LLaMA-3]
    
    CheckEngine -->|Sovereign Air-Gapped| LocalOllama
    
    RunGroq --> EvalResponse{Response Complete & Valid?}
    RunGemini --> EvalResponse
    LocalOllama --> EvalResponse
    
    EvalResponse -->|Valid| Deliver[Render Final Markdown Report to UI]
    EvalResponse -->|Malformed/Stalled| SelfHeal[Trigger AST-Sanitized Self-Healer]
    SelfHeal --> LocalFallback[Deterministic Local Synthesizer Fallback]
    LocalFallback --> Deliver
```

---

## 5. Journey 4: Edge-Case Handling (Session Expiry & Captcha Fallback)

### 5.1 Recovery Flow
```mermaid
stateDiagram-v2
    [*] --> InjectedNavigation: Load Cookies & Navigate
    InjectedNavigation --> PortalLoaded: HTTP 200 (Active Session)
    InjectedNavigation --> SessionExpired: HTTP 401 / Redirect to Login
    InjectedNavigation --> CaptchaDetected: Captcha Challenge Encountered

    PortalLoaded --> Scraping: Parse Tender Tables
    Scraping --> [*]: Output Generated

    SessionExpired --> AlertUser: Emit WebSocket Telemetry: "Session Expired"
    AlertUser --> ManualReauth: Prompt Officer for Quick 1-Click Re-Login
    ManualReauth --> InjectedNavigation: Save New Cookies to Vault

    CaptchaDetected --> LocalOCR: Attempt Local Tesseract OCR on Captcha
    LocalOCR --> SubmitCaptcha: Enter Solved Captcha
    SubmitCaptcha --> PortalLoaded: Success
    SubmitCaptcha --> HumanEscalation: 2 Consecutive Fails -> Prompt Officer
```