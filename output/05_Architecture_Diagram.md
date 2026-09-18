# System Architecture Diagram (High-Level)

**Product Name**: Sovereign On-Premise Agentic AI Workbench (SIH PSC26117)  
**Document Version**: 2.0  
**Scope**: C4 System Context, Container & Component Topology  

---

## 1. Architectural Principles

1. **Dual-Engine Flexibility ($0 Cost)**: High-speed cloud free APIs (Groq LLaMA-3.3-70B & Google Gemini Flash) for hackathon judging, paired with air-gapped on-premise open-weight LLMs (BharatGPT / Ollama) for sovereign deployments.
2. **Strict Host Boundary (Air-Gapped Sovereign Mode)**: In sovereign mode, zero bytes leave the physical machine. All vector embeddings, cookies, logs, and inferences remain local.
3. **Instant Cookie-Driven Authentication**: Bypass multi-factor authentication (MFA) bottlenecks via local AES-256 cookie vault injection.
4. **Sandboxed AST Execution**: All self-repair code is inspected by a static Abstract Syntax Tree (AST) analyzer before execution to prevent malicious OS operations.

---

## 2. C4 Context Diagram (System Context)

```mermaid
C4Context
    title System Context Diagram - Sovereign Agentic AI Workbench (SIH PSC26117)

    Person(officer, "Government Officer", "Desk Officer / Procurement Clerk / Section Officer")

    System(workbench, "Sovereign AI Workbench", "Autonomous local assistant running on 8GB RAM host machine")

    System_Ext(gem_portal, "Government e-Marketplace (GeM)", "National public procurement portal (gem.gov.in)")
    System_Ext(cppp_portal, "CPPP Procurement Portal", "Central Public Procurement Portal (eprocure.gov.in)")
    System_Ext(groq_api, "Groq Cloud (Free Tier)", "Ultra-fast LLaMA 3.3 70B inference engine (~500 t/s)")
    System_Ext(gemini_api, "Google Gemini (Free Tier)", "Gemini 1.5 Flash API with 1M context")

    Rel(officer, workbench, "Interacts via plain English queries & views briefings", "HTTP / WebSockets")
    Rel(workbench, gem_portal, "Automates browsing using preserved cookies (No OTP)", "Playwright CDP / HTTPS")
    Rel(workbench, cppp_portal, "Extracts tender notices and bid files", "Playwright CDP / HTTPS")
    Rel(workbench, groq_api, "Sends sanitized prompts for sub-second synthesis (Hackathon Mode)", "REST API")
    Rel(workbench, gemini_api, "Fallback for high-context document analysis (Hackathon Mode)", "REST API")
```

---

## 3. C4 Container Diagram (Workbench Subsystems)

```mermaid
flowchart TB
    subgraph HostMachine["Host Machine (Standard 8GB RAM Government Laptop)"]
        subgraph FrontendLayer["Presentation & Telemetry Tier"]
            UI["Control Center Web UI\n(HTML5, Vanilla CSS Glassmorphism, JS)"]
            WSClient["WebSocket Client\n(Real-Time Streaming Telemetry)"]
        end

        subgraph BackendLayer["Agentic Core (FastAPI / Python 3.11+)"]
            Server["FastAPI Orchestrator Server\n(server.py)"]
            TenderAgent["Autonomous Tender Agent\n(tender_agent.py)"]
            DualEngine["Dual-Engine LLM Router\n(dual_engine_llm.py)"]
            CookieVault["Instant Cookie Session Vault\n(cookie_vault.py)"]
            SandboxGuardian["AST Static Inspector & Sandbox\n(sandbox_runner.py)"]
        end

        subgraph AutomationLayer["Browser Execution Engine"]
            Playwright["Playwright CDP Engine\n(Headless/Headed Chromium)"]
            DOMParser["DOM Table & Form Extractor"]
        end

        subgraph StorageLayer["Local Sovereign Storage"]
            SessionStore[("Encrypted Cookie Vault\n(portal_sessions.json)")]
            OutputStore[("Generated Reports & SDLC\n(./output/)")]
            LocalLLM[("Local Open-Weight LLM\n(Ollama / BharatGPT Q4_K_M)")]
        end
    end

    subgraph ExternalFreeAPIs["External Free-Tier APIs (Hackathon Turbo Mode)"]
        GroqCloud["Groq Cloud API\n(LLaMA-3.3-70B @ 500 t/s)"]
        GeminiCloud["Google AI Studio\n(Gemini 1.5 Flash)"]
    end

    UI <-->|HTTP REST & WS| Server
    Server --> TenderAgent
    TenderAgent --> CookieVault
    CookieVault <--> SessionStore
    TenderAgent --> Playwright
    Playwright --> DOMParser
    TenderAgent --> DualEngine
    
    DualEngine -->|Mode: Turbo| GroqCloud
    DualEngine -->|Mode: Turbo Fallback| GeminiCloud
    DualEngine -->|Mode: Sovereign Air-Gap| LocalLLM
    
    TenderAgent --> OutputStore
    Server --> SandboxGuardian
```

---

## 4. Component Topology & Data Flow

1. **Client Command Dispatch**: User enters prompt on Web UI. Sent via `/api/workbench/run-task`.
2. **Session Vault Access**: `TenderAgent` requests authenticated cookies from `CookieVault` matching the portal domain.
3. **Browser Context Rehydration**: Playwright initializes an isolated Chromium context and injects cookies, bypassing all SMS/email OTP prompts.
4. **Autonomous Navigation & Extraction**: Chromium loads the target portal table, extracts row cells (Tender ID, Ministry, Value, Deadline), and closes the context.
5. **Dual-Engine Synthesis**:
   - In **Hackathon Turbo Mode**, the structured payload is dispatched to Groq API (`llama-3.3-70b-versatile`), returning an executive intelligence briefing in ~400ms.
   - In **Sovereign Air-Gapped Mode**, the payload routes directly to local Ollama/BharatGPT on `http://127.0.0.1:11434`.
6. **Telemetry & Rendering**: Step-by-step execution status is streamed via WebSockets to the Web UI, rendering the final briefing on the officer's dashboard.