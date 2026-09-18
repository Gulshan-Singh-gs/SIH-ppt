# Product Requirements Document (PRD)

**Product Name**: Sovereign On-Premise Agentic AI Workbench  
**Problem Statement Reference**: SIH PSC26117  
**Document Version**: 2.0 (Hackathon Engineering Release)  
**Status**: Ready for Hackathon Demonstration & Staging Verification  
**Author**: Principal Product Manager & Lead System Architect  

---

## 1. Product Vision & Value Proposition

To deliver the first personal, sovereign AI assistant for Indian government employees and administrative teams that runs entirely on local machines, performs complex browser-based automation across public portals (GeM, CPPP) without coding, bypasses repetitive OTP delays via instant cookie rehydration, and offers a flexible **Dual-Engine** architecture (Groq and Gemini free-tier APIs for lightning-speed hackathon demos, and local open-weight LLMs for air-gapped sovereign security) at **absolute zero cost**.

---

## 2. User Personas

### Persona 1: Rajesh Sharma (Section Officer, Ministry of Electronics & IT)
- **Role**: Reviews IT procurement bids and ensures timely compliance with ministerial budget mandates.
- **Pain Point**: Must manually check GeM multiple times daily, login through SMS OTPs, and compare multi-page tender criteria.
- **Goal**: Type a natural language query in the morning (*"Check today's tender updates on the government portal"*) and receive a formatted briefing table with actionable deadlines.

### Persona 2: Ananya Sen (Under Secretary, Ministry of Finance)
- **Role**: Authorizes tender approvals, oversees financial compliance, and audits vendor certifications.
- **Pain Point**: Cannot use commercial tools like ChatGPT due to strict data privacy and confidentiality rules.
- **Goal**: Run an autonomous assistant on her standard 8GB RAM government laptop that operates 100% locally with zero data leaks.

### Persona 3: Suresh Patil (Procurement Desk Clerk, Central PSU)
- **Role**: Compiles bidder qualification sheets and extracts numerical data from tables into spreadsheets.
- **Pain Point**: Repetitive copy-pasting across dozens of browser tabs leads to clerical errors and eye strain.
- **Goal**: One-click autonomous scraping of tender tables directly into structured markdown and CSV reports.

### Persona 4: Vikram Malhotra (Cyber Security Auditor, CERT-In Panel)
- **Role**: Audits administrative tools for data exfiltration, unauthorized network sockets, and malicious macros.
- **Goal**: Verify that the workbench operates in an air-gapped sandbox where no prompts, credentials, or documents leave the local device.

---

## 3. MoSCoW Feature Breakdown

### 3.1 Must Have (P0 - Critical for Hackathon Demo & Core MVP)
- **F-01: Natural Language Task Input**: Clean text input bar supporting plain English queries for web workflows.
- **F-02: Instant Cookie Session Vault**: Local secure storage of portal session cookies allowing the AI to launch browsers already authenticated without entering passwords or SMS OTPs.
- **F-03: Autonomous Government Portal Navigation & Scraping**: Playwright-powered browser automation that navigates to procurement portals (GeM/CPPP or local mock portal), parses dynamic HTML tables, and extracts structured records.
- **F-04: Dual-Engine LLM Router (Zero Cost)**:
  - **Hackathon Turbo Engine**: High-speed inference using free-tier Groq (`llama-3.3-70b-versatile` / `llama-3.1-8b-instant`) and Google Gemini (`gemini-1.5-flash`) APIs (<1s latency).
  - **Sovereign Engine**: Local open-weight LLM execution (Ollama / BharatGPT / LLaMA-3) for air-gapped offline environments.
  - **Autonomous Fallback**: Graceful offline synthesizer ensuring continuous demo reliability.
- **F-05: Executive Tender Intelligence Report Generation**: Synthesis of raw tender tables into clean Markdown briefings with summary metrics, urgency badges, and actionable steps.
- **F-06: Control Center Web Dashboard**: Modern dark/light glassmorphic UI displaying live execution telemetry, session status, and interactive report viewer.

### 3.2 Should Have (P1 - Fast Follow)
- **F-07: AST-Sanitized Self-Healing Guardian**: Sandboxed Python script evaluator that inspects browser automation scripts, detects broken selectors, and self-repairs without allowing malicious system imports.
- **F-08: One-Click SDLC Suite Generation**: Instant generation of all 13 SDLC architectural documents via free-tier API endpoints.
- **F-09: Export to PDF/CSV/Markdown**: One-click download of generated tender intelligence reports and documentation.

### 3.3 Could Have (P2 - Post-Hackathon Phase)
- **F-10: Multi-Lingual Support**: Querying and report generation in Hindi, Tamil, Telugu, and other official Indian languages via BharatGPT.
- **F-11: Voice Command Interface**: Speech-to-text input for hands-free query dispatch.

### 3.4 Won't Have (P3 - Explicitly Out of Scope)
- **Commercial Cloud Paid APIs**: No reliance on paid subscriptions (OpenAI GPT-4o, Claude Opus paid plans). The solution must remain 100% free.
- **Automated Financial Bidding**: The agent provides intelligence and report synthesis; final financial transaction approvals require human officer sign-off.

---

## 4. Detailed User Stories & Acceptance Criteria

### Story 1: Daily Tender Tracking Workflow
**As a** Section Officer  
**I want to** type "Check today's tender updates on the government portal"  
**So that** I don't have to manually browse multiple portal pages and log in repeatedly.

- **Given** the user is on the Sovereign Workbench dashboard  
- **When** the user submits the query and clicks "Execute Task"  
- **Then** the system loads preserved cookies from the Cookie Vault, navigates to the portal, extracts active tenders, synthesizes an executive briefing, and renders it in under 10 seconds.

### Story 2: Instant OTP-Less Session Rehydration
**As a** Government Employee  
**I want** my authenticated browser session preserved locally  
**So that** I do not face repeated 2-factor OTP verifications during the workday.

- **Given** an officer has authenticated into GeM once in the browser  
- **When** the agent initiates an automated task  
- **Then** Playwright automatically injects the stored cookies, confirming `Authenticated (Instant Bypass Active)` with zero OTP delay.

### Story 3: Dual-Engine Hackathon Speed Switch
**As a** Hackathon Presenter  
**I want to** switch between Cloud Free API (Groq/Gemini) and Local Sovereign LLM  
**So that** I can show high-speed (<1s) live responses to judges and then demonstrate offline air-gapped execution.

- **Given** the user opens the Engine Settings modal  
- **When** the user selects "Hackathon Turbo (Groq + Gemini API - Free)"  
- **Then** prompts are processed via Groq/Gemini free tiers; if toggled to "Sovereign Air-Gapped", all inference routes to local Ollama/BharatGPT.

---

## 5. Non-Functional Requirements (NFRs)

| Category | Specification | Verification Metric |
| :--- | :--- | :--- |
| **Response Latency (Turbo Mode)** | < 1.0 second per LLM reasoning step | Groq API telemetry benchmark |
| **Response Latency (Sovereign Mode)** | < 15.0 seconds on standard 8GB RAM CPU | Local Ollama GGUF Q4_K_M benchmark |
| **Memory Footprint** | Host RAM consumption < 4.5 GB (Leaving 3.5GB for OS) | Windows Task Manager / `psutil` |
| **Data Privacy** | 0 external network packets transmitted in Sovereign Mode | Wireshark packet capture inspection |
| **Operational Cost** | $0.00 perpetual (Zero licenses, zero API fees) | Verification of Free Tier endpoints |
| **Browser Compatibility** | Chromium, Chrome Enterprise, Edge | Playwright multi-browser matrix |