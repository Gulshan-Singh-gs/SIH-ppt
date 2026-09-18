# Architecture Decision Records (ADRs)

**Product Name**: Sovereign On-Premise Agentic AI Workbench (SIH PSC26117)  
**Document Version**: 2.0  
**Format**: MADR 3.0.0 (Markdown Architectural Decision Records)  

---

## ADR-001: Dual-Engine LLM Router Architecture

### Status
Accepted

### Context & Problem Statement
The Smart India Hackathon evaluation requires instantaneous, snappy (<1 second) demonstrations before a judging panel to prove capability. However, government deployment regulations mandate strict on-premise execution using open-weight models (BharatGPT / LLaMA-3) on standard 8GB RAM office laptops without external data transmission. Running a 7B/8B model locally on an 8GB CPU yields ~10–15 tokens/sec, which is too slow for a 3-minute hackathon pitch.

### Considered Options
1. **Cloud Paid Only (OpenAI GPT-4o / Claude 3.5)**: Fast, but incurs recurring subscription costs and violates the core problem statement.
2. **Local CPU Only (Ollama 8B)**: 100% sovereign, but sluggish during live hackathon stage demos.
3. **Dual-Engine Hybrid Router (Groq + Gemini Free Cloud APIs + Local Open-Weight Fallback)**: Best of both worlds.

### Decision Outcome
Chosen option: **Option 3 (Dual-Engine Hybrid Router)**.
- **Hackathon Mode**: Uses Groq Cloud API (`llama-3.3-70b-versatile` at ~500 tokens/sec) and Google Gemini 1.5 Flash at **$0 cost** to deliver instant, stunning live demo results.
- **Sovereign Mode**: Routes directly to local Ollama / BharatGPT on-premise without touching the internet.
- **Cost**: $0.00 perpetual.

---

## ADR-002: Client-Side Session Cookie Persistence vs. Storing Plaintext Passwords

### Status
Accepted

### Context & Problem Statement
Government portals (GeM, CPPP) require multi-factor SMS/Email OTP verification on every login. Having an autonomous AI agent prompt an officer for an OTP every morning destroys the seamless assistant experience. Storing officer passwords in plaintext is a catastrophic security violation.

### Decision Outcome
Chosen option: **Encrypted Cookie Vault**.
- The officer authenticates once in their browser.
- The workbench captures the resulting session cookies (`GEM_SSO_SESSION`, `NIC_ID`) and encrypts them locally using AES-256-GCM.
- When launching automated tasks, Playwright injects the cookies directly into the browser context, achieving instant authentication with zero password storage and zero OTP delay.

---

## ADR-003: Playwright CDP vs. Selenium WebDriver

### Status
Accepted

### Context & Problem Statement
The autonomous agent must manage headless/headed browser sessions, inject pre-saved cookies, parse dynamic DOM trees, and handle government portal popups reliably.

### Decision Outcome
Chosen option: **Playwright with Chrome DevTools Protocol (CDP)**.
- Native async Python support with zero external driver binaries needed (unlike `chromedriver` version mismatch hell in Selenium).
- Native cookie injection (`context.add_cookies()`) with instantaneous execution.
- Superior auto-waiting and selector resilience for dynamic JavaScript government portals.

---

## ADR-004: AST Static Inspection for Sandboxed Browser Self-Healing

### Status
Accepted

### Context & Problem Statement
When government portal layouts change, the AI supervisor attempts to self-heal the browser script. Allowing an LLM to generate and execute arbitrary Python code on an officer's workstation creates a major remote code execution (RCE) risk.

### Decision Outcome
Chosen option: **AST (Abstract Syntax Tree) Static Inspector Sandbox**.
- All self-repair code is parsed via Python's built-in `ast` module before execution.
- Any attempt to import modules (`import os`, `sys`, `subprocess`, `shutil`), make network sockets, or access the filesystem is strictly blocked.
- Only a sealed whitelist of safe browser primitives (`safe_click()`, `safe_wait()`, `safe_press_key()`, `safe_reload_tab()`) can be executed.

---

## ADR-005: 100% Free-Tier Architecture & Zero Licensing Cost

### Status
Accepted

### Context & Problem Statement
The SIH problem statement mandates feasibility across all government departments without introducing budgetary strain or foreign exchange drain.

### Decision Outcome
Chosen option: **100% Open-Source & Perpetual Free-Tier Stack**.
- Python 3.11 (PSF), FastAPI (MIT), Playwright (Apache 2.0), SQLite (Public Domain).
- Groq Cloud API free tier & Google Gemini API free tier for hackathon development.
- Zero paid licenses, zero monthly API fees, zero vendor lock-in.

---

## ADR-006: Local Embedded SQLite vs. Remote Database

### Status
Accepted

### Context & Problem Statement
The workbench needs to persist task histories, extracted tender records, and audit logs on the user's laptop. Setting up PostgreSQL or MongoDB creates huge installation friction for non-technical government staff.

### Decision Outcome
Chosen option: **Local SQLite 3 with Write-Ahead Logging (WAL)**.
- Embedded zero-configuration database; zero services to install or configure.
- Single `.db` file stored locally on the laptop, ensuring full air-gapped data retention.