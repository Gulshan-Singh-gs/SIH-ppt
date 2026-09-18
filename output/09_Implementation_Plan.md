# Implementation Plan & Sprint Breakdown

**Product Name**: Sovereign On-Premise Agentic AI Workbench (SIH PSC26117)  
**Document Version**: 2.0  
**Scope**: 24–48 Hour Hackathon Sprint Execution & 3-Week Ministry Pilot Rollout  

---

## 1. 24–48 Hour Smart India Hackathon Execution Sprint

To guarantee a hackathon-winning presentation before the judging jury, the engineering work is partitioned into four 12-hour high-impact milestones:

```
+---------------------------------------------------------------------------------------------------+
| SPRINT 1 (Hours 0-12)      | SPRINT 2 (Hours 12-24)     | SPRINT 3 (Hours 24-36)     | SPRINT 4 (36-48h)  |
| Dual-Engine & Cookie Vault | Tender Agent & Playwright  | Control Center Web UI      | Hardening & Rehearsal|
+---------------------------------------------------------------------------------------------------+
```

### Sprint 1 (Hours 00–12): Dual-Engine & Cookie Vault Setup
- **Deliverable 1.1**: Construct `dual_engine_llm.py` supporting Groq LLaMA-3.3-70B (<500ms latency) and Gemini 1.5 Flash at $0 cost.
- **Deliverable 1.2**: Implement `cookie_vault.py` with default pre-authenticated sessions for GeM and CPPP portals.
- **Deliverable 1.3**: Set up local SQLite embedded database schema with WAL mode.

### Sprint 2 (Hours 12–24): Tender Agent & Autonomous Browser Crawl
- **Deliverable 2.1**: Build `tender_agent.py` using Playwright async context with direct cookie injection.
- **Deliverable 2.2**: Create the local Mock GeM Government Tender Portal (`/portal/gem-tenders`) to guarantee 100% offline uptime.
- **Deliverable 2.3**: Verify end-to-end task dispatch: Natural language prompt -> Cookie injection -> Table scrape -> Groq synthesis.

### Sprint 3 (Hours 24–36): Futuristic Control Center Web UI
- **Deliverable 3.1**: Build glassmorphic dashboard in `static/index.html` with real-time WebSocket telemetry stream.
- **Deliverable 3.2**: Add the one-click primary demo card: *"Check today's tender updates on the government portal"*.
- **Deliverable 3.3**: Embed live Tender Intelligence Report renderer with Markdown and PDF export.

### Sprint 4 (Hours 36–48): Air-Gap Hardening, Benchmarking & Pitch Rehearsal
- **Deliverable 4.1**: Execute automated latency and cost benchmark tests (Groq vs Gemini vs Ollama).
- **Deliverable 4.2**: Verify AST sandbox security guardrails (blocking all unauthorized OS imports).
- **Deliverable 4.3**: Final dry-run of the 1-Minute Pitch matching the SIH PPT presentation.

---

## 2. 3-Week Ministry Pilot Rollout (Post-Hackathon)

| Week | Phase Focus | Key Deliverables & Milestones |
| :--- | :--- | :--- |
| **Week 1** | **Air-Gapped Containerization** | Build standalone Docker appliance packaging Ollama + BharatGPT Q4_K_M weights for air-gapped installation. |
| **Week 2** | **Multi-Portal Integration** | Add native cookie adapters for Indian Railways IREPS, Defense CPPP, and state municipal tender boards. |
| **Week 3** | **Security Audit & Pilot Deployment** | Undergo CERT-In empanelled third-party vulnerability assessment; deploy pilot desks across 50 MeitY workstations. |

---

## 3. Work Breakdown Structure (WBS) & Story Points

| WBS ID | Work Package Title | Owner | Story Points | Risk Level |
| :--- | :--- | :--- | :--- | :--- |
| **WBS-1.1** | Groq & Gemini Free API Integration | Backend Lead | 3 SP | Low |
| **WBS-1.2** | AES-256 Encrypted Cookie Session Vault | Security Eng | 5 SP | Medium |
| **WBS-2.1** | Playwright CDP Navigation & Table Scraper | Automation Eng | 8 SP | High |
| **WBS-2.2** | Offline High-Fidelity Mock Tender Portal | Full-Stack Dev | 3 SP | Low |
| **WBS-3.1** | WebSocket Real-Time Telemetry Broadcaster | Backend Lead | 5 SP | Medium |
| **WBS-3.2** | Glassmorphic Dashboard & Report Renderer | UI/UX Dev | 5 SP | Low |
| **WBS-4.1** | AST-Sanitized Self-Healing Sandbox | Security Eng | 8 SP | High |
| **WBS-4.2** | Complete 13 SDLC Document Authoring | Solutions Arch | 5 SP | Low |
| **TOTAL** | **Full Sovereign Workbench Release** | **Team** | **42 SP** | - |