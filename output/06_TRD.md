# Technical Requirements Document (TRD)

**Product Name**: Sovereign On-Premise Agentic AI Workbench (SIH PSC26117)  
**Document Version**: 2.0  
**Target Environment**: Standard Indian Government Laptops (Windows 11 / Ubuntu 22.04 LTS / Bharat Operating System Solutions - BOSS)  

---

## 1. Technology Stack & Version Constraints

| Layer / Component | Technology Choice | Version Constraint | Justification & Licensing |
| :--- | :--- | :--- | :--- |
| **Backend Runtime** | Python | `>= 3.10, < 3.15` | Cross-platform, extensive AI library ecosystem (PSF License). |
| **Web Framework** | FastAPI | `>= 0.100.0` | Asynchronous ASGI framework, native OpenAPI docs (MIT). |
| **ASGI Web Server** | Uvicorn | `>= 0.23.0` | Lightning-fast async server with WebSockets (BSD-3). |
| **Browser Engine** | Playwright Chromium | `>= 1.40.0` | Direct CDP protocol control, session injection, resilient headless (Apache 2.0). |
| **Data Validation** | Pydantic | `>= 2.0.0` | High-performance Rust-backed schema validation (MIT). |
| **HTTP Async Client** | HTTPX | `>= 0.25.0` | Async HTTP client for Groq, Gemini & Ollama REST endpoints (BSD-3). |
| **Local Database** | SQLite 3 | Built-in | Zero-admin, single-file ACID transactional database (Public Domain). |
| **Hackathon Engine** | Groq Cloud API | REST API | Ultra-low latency LLaMA-3.3-70B inference ($0 Free Tier). |
| **Hackathon Fallback**| Google Gemini API | REST API / SDK | High-context window fallback ($0 Free Tier). |
| **Sovereign Engine** | Ollama / BharatGPT | `>= 0.3.0` | 100% on-premise open-weight GGUF runner ($0 Compute). |

---

## 2. Hardware Resource Envelope (Standard 8GB RAM Laptop)

Government workstations typically feature budget hardware (e.g. Intel Core i5 8th–11th Gen, 8GB DDR4 RAM, 256GB SSD). The workbench is strictly engineered to fit within this envelope:

| Subsystem | CPU Utilization | Peak RAM Consumption | Disk Space Allocation |
| :--- | :--- | :--- | :--- |
| **FastAPI Core & Telemetry** | < 2% CPU | 85 MB | 25 MB (Codebase) |
| **Playwright Headless Browser**| 15% – 30% (During crawl) | 280 MB | 450 MB (Chromium binary) |
| **Cookie Vault & SQLite DB** | < 1% CPU | 15 MB | 10 MB (Local storage) |
| **Hackathon Turbo (Groq/Gemini)**| < 1% CPU (Offloaded) | 40 MB (Network buffer) | 0 MB |
| **Sovereign Local Model (Ollama)**| 60% – 80% (4 cores) | 3.8 GB (Q4_K_M 7B/8B model)| 4.7 GB (Model weights) |
| **TOTAL (Turbo Mode)** | **< 30% CPU Peak** | **~420 MB Total RAM** | **< 500 MB Disk** |
| **TOTAL (Sovereign Local Mode)**| **< 85% CPU Peak** | **~4.2 GB Total RAM** | **~5.2 GB Disk** |

*Verdict: 4.2 GB peak RAM leaves 3.8 GB completely free for Windows OS and background services on an 8GB laptop.*

---

## 3. Network Architecture & Security Boundaries

### 3.1 Dual-Mode Network Configuration
1. **Hackathon Turbo Mode**:
   - Outbound HTTPS (Port 443) permitted exclusively to:
     - `api.groq.com` (Groq Inference)
     - `generativelanguage.googleapis.com` (Gemini API)
   - Zero inbound ports exposed to the public internet; Web UI bound to `127.0.0.1:8001`.
2. **Sovereign Air-Gapped Mode**:
   - Completely offline capable.
   - Host network card can be disabled or isolated on an intranet LAN.
   - All AI calls route to `http://127.0.0.1:11434` (Local Ollama).

---

## 4. Service Level Objectives (SLOs) & Performance SLAs

| Operational Metric | Target SLO (Turbo Mode) | Target SLO (Sovereign Mode) | Measurement Mechanism |
| :--- | :--- | :--- | :--- |
| **Time-to-First-Token (TTFT)** | < 350 ms | < 2,500 ms | API Gateway latency timer |
| **Tender Crawl Duration** | < 4.0 seconds | < 4.0 seconds | Playwright page audit timer |
| **Full Report Generation** | < 6.0 seconds | < 18.0 seconds | Total elapsed clock |
| **Cookie Rehydration Time** | < 50 ms | < 50 ms | Browser context setup timer |
| **Server Availability** | 99.99% on local host | 99.99% on local host | Uptime probe `/api/status` |
| **Evidence Extraction Latency** | < 15 ms | < 25 ms | Provenance Engine stopwatch |
| **AI Verification Claim Evaluation** | < 10 ms | < 15 ms | Deterministic Concordance Engine |
| **Audit Ledger Block Hashing** | < 1 ms | < 1 ms | SHA-256 Chained Hash Digest |

---

## 5. Sovereign Defensibility & Governance Subsystems

### 5.1 Evidence & Provenance Architecture (`provenance_engine.py`)
- **Granularity**: Page number, section clause identifier, character start/end span, snippet SHA-256 hash.
- **Coverage Metric**: Quantifies percentage of inquiry terms grounded in cited passages; triggers explicit abstention if coverage < 30%.

### 5.2 Deterministic AI Verification & Anti-Hallucination (`verification_engine.py`)
- **States**: `SUPPORTED`, `PARTIALLY_SUPPORTED`, `UNSUPPORTED`, `CONTRADICTED`, `INSUFFICIENT_EVIDENCE`, `REQUIRES_HUMAN_REVIEW`.
- **Numeric Fact Checker**: Regex-driven concordance on tenders, currency, turnover, EMD, and deadlines. Detects conflicting numerical claims before display.

### 5.3 Controlled Agent Policy & Human-in-the-Loop Gating (`governed_agent.py`)
- **Risk Tiers**:
  - **LOW**: Read-only portal scans, summarization, local indexing (Auto-cleared).
  - **MEDIUM**: Local draft creation, report export (Logged).
  - **HIGH**: Submitting bids, portal writes, file deletions, cloud bursts (Execution halts; requires officer modal authorization).

### 5.4 Tamper-Evident Cryptographic Audit Ledger (`audit_ledger.py`)
- **Storage**: Append-only `output/.vault/audit_trail.jsonl`.
- **Integrity**: SHA-256 blockchain linking every event hash to predecessor block hash.
- **Sanitization**: Recursive redaction of passwords, tokens, cookies, and secrets.