# 🏛️ Sovereign On-Premise Agentic AI Workbench (SIH PSC26117)

A fully sovereign, privacy-first, on-premise AI workbench designed for public sector enterprise procurement and document intelligence. Built for **Smart India Hackathon (SIH 2025 - Problem Statement PSC26117)**.

---

## 🌟 Key Features

1. **Dual-Engine LLM Architecture**
   - Fast Free Cloud Tier (Groq / Gemini APIs) for rapid responses.
   - Local Open-Weight Fallback (Ollama - Llama 3 / DeepSeek / Mistral) for 100% offline air-gapped security.

2. **Instant Cookie Session Vault**
   - Bypasses repeated OTP delays during GeM (Government e-Marketplace) portal workflows using encrypted local session token management.

3. **Hybrid RAG & Document Processing**
   - High-throughput OCR, document parsing, chunking, and semantic vector search across local PDFs and spreadsheets.

4. **Tender & Compliance Intelligence Agent**
   - Automated bid matching, eligibility criteria verification, and compliance matrix generation.

5. **Interactive Executive Presentation & PDF Exporter**
   - Neumorphic presentation interface (`index.html`) with interactive 3D wave background animations.
   - High-resolution PDF exporter (`export_pdf.js`) rendering 2× retina slides using Puppeteer.

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** & **npm**
- *(Optional)* **Ollama** installed locally with `llama3` or `deepseek-r1` pulled.

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/sovereign-ai-workbench.git
   cd sovereign-ai-workbench
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Install Node.js dependencies (for PDF export):
   ```bash
   npm install
   ```

---

## 🏃 Usage

### Running the Workbench Backend Server
Double-click `Launch_Sovereign_Workbench.bat` or run:
```bash
python server.py
```
The FastAPI backend server will launch at `http://127.0.0.1:8001`.

### Viewing the Presentation UI
Open `index.html` directly in any web browser to view the 12-slide interactive Neumorphic pitch deck.

### Exporting Presentation to High-Quality PDF
Run the Puppeteer export script:
```bash
node export_pdf.js
```
The generated PDF will be saved into the `output/` folder as `Sovereign_AI_Workbench_Presentation.pdf`.

---

## 📁 Repository Structure

```
.
├── index.html                   # 12-Slide Neumorphic Executive Presentation UI
├── server.py                    # Core FastAPI Server & REST Endpoints
├── dual_engine_llm.py           # Cloud + Local LLM Routing Engine
├── local_rag_engine.py          # Vector RAG & Document Indexing Engine
├── document_processor.py        # OCR & Multi-Format Document Parser
├── tender_agent.py              # GeM Tender Matching & Compliance Agent
├── cookie_vault.py              # Encrypted Session Vault for GeM Portal
├── profile_manager.py           # User Profile & System Configuration Manager
├── ollama_manager.py            # Local Ollama LLM Lifecycle Management
├── export_pdf.js                # Puppeteer High-Res PDF Generator
├── Launch_Sovereign_Workbench.bat # One-Click Windows Launcher Script
├── requirements.txt             # Python Package Dependencies
├── package.json                 # Node.js Package Config
├── static/                      # Workbench Web Frontend UI Assets
│   ├── app.js                   # Frontend Single-Page Application Logic
│   ├── index.html               # Main Web App UI Layout
│   └── style.css                # Neumorphic CSS Styling System
└── test_*.py                    # Unit & Integration Test Suites
```

---

## 🛡️ Privacy & Security

- **Zero External Telemetry**: All data processing remains local.
- **Air-Gap Ready**: Gracefully degrades to local Ollama models when network connection is severed.
- **Session Protection**: Encryption-at-rest for session credentials stored locally.

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for details.
