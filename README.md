# Sovereign On-Premise Agentic AI Workbench (SIH PSC26117)

A fully sovereign, privacy-first, on-premise AI workbench designed for public sector enterprise procurement and document intelligence. Built for Smart India Hackathon (SIH 2025 - Problem Statement PSC26117).

---

## Key Features

1. **Sovereign Local LLM Architecture**
   - 100% On-Premise Local LLM Execution Engine powered by local open-weight models (Ollama - Llama 3 / DeepSeek / Mistral) for air-gapped security and data sovereignty.

2. **Instant Cookie Session Vault**
   - Eliminates repeated OTP verification friction during portal workflows via local encrypted session token management.

3. **Hybrid RAG & Document Processing**
   - High-throughput OCR, document parsing, text chunking, and semantic vector search across local PDFs and spreadsheets.

4. **Tender & Compliance Intelligence Agent**
   - Automated bid matching, eligibility criteria verification, and compliance matrix generation.

5. **Executive Presentation & PDF Exporter**
   - Neumorphic presentation interface (`index.html`) with dynamic background wave renderers.
   - High-resolution PDF exporter (`export_pdf.js`) rendering retina slides via Puppeteer.

---

## Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- Ollama installed locally with Llama 3 or DeepSeek model instances.

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/Gulshan-Singh-gs/SIH-ppt.git
   cd SIH-ppt
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

## Usage

### Running the Backend Server
Execute the launcher script or run:
```bash
python server.py
```
The FastAPI backend server will launch at `http://127.0.0.1:8001`.

### Viewing the Presentation UI
Open `index.html` directly in any standard web browser to view the 12-slide executive presentation.

### Exporting Presentation to High-Quality PDF
Run the Puppeteer export script:
```bash
node export_pdf.js
```
The generated PDF will be saved in the `output/` directory as `Sovereign_AI_Workbench_Presentation.pdf`.

---

## Repository Structure

```
.
├── index.html                   # 12-Slide Neumorphic Executive Presentation UI
├── server.py                    # Core FastAPI Server & REST Endpoints
├── dual_engine_llm.py           # On-Premise Local LLM Routing Engine
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

## Privacy & Security

- Zero External Telemetry: Data processing remains strictly local to the execution environment.
- Air-Gap Native: Operates 100% offline on local open-weight models without external network dependencies.
- Local Credential Encryption: Session tokens are stored using local AES encryption-at-rest.

---

## License

Distributed under the MIT License.
