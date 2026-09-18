# API Contract Specification (OpenAPI 3.0.3)

**Product Name**: Sovereign On-Premise Agentic AI Workbench (SIH PSC26117)  
**Specification**: OpenAPI 3.0.3 YAML Contract  
**Base Server URL**: `http://127.0.0.1:8001`  

---

```yaml
openapi: 3.0.3
info:
  title: Sovereign On-Premise Agentic AI Workbench API
  description: |
    Enterprise-grade, zero-cost REST & WebSocket API specification for SIH PSC26117.
    Powers autonomous browser automation across Indian government portals (GeM/CPPP),
    manages the encrypted Cookie Vault, and routes requests across the Dual-Engine LLM tier.
  version: 2.0.0
  contact:
    name: Sovereign AI Workbench Technical Team
    url: https://gulshan-singh-gs.github.io/SIH-ppt/

servers:
  - url: http://127.0.0.1:8001
    description: Local On-Premise Host Server

paths:
  /api/workbench/run-task:
    post:
      summary: Execute Autonomous Natural Language Agentic Task
      description: |
        Primary entry point. Parses natural language instructions (e.g., 'Check today's tender updates on the government portal'),
        rehydrates preserved session cookies from the Cookie Vault, automates browser interaction,
        and synthesizes an executive intelligence briefing via the Dual-Engine LLM.
      operationId: runWorkbenchTask
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TaskExecutionRequest'
      responses:
        '200':
          description: Task executed successfully.
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TaskExecutionResponse'
        '400':
          description: Invalid query or parameter payload.
        '500':
          description: Internal execution failure or portal timeout.

  /api/workbench/sessions:
    get:
      summary: List Preserved Portal Sessions in Cookie Vault
      description: Returns active authenticated portal sessions stored in the encrypted local vault.
      operationId: listSessions
      responses:
        '200':
          description: List of stored portal sessions.
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/PortalSession'

  /api/workbench/status:
    get:
      summary: Get Dual-Engine & System Telemetry Status
      description: Returns configuration and readiness of Groq API, Gemini API, and Local Ollama engines.
      operationId: getEngineStatus
      responses:
        '200':
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/SystemStatus'

  /api/workbench/generate-sdlc:
    post:
      summary: Generate or Refresh SDLC Documents via Free Dual-Engine
      description: Rapidly synthesizes full or partial 13 SDLC specification documents using free-tier Groq/Gemini APIs.
      operationId: generateSDLC
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                project_vision:
                  type: string
                  example: "Sovereign On-Premise Agentic AI Workbench"
                sequences:
                  type: array
                  items:
                    type: integer
                  example: [1, 2, 3, 4, 5]
      responses:
        '200':
          description: Generated SDLC documents.

  /portal/gem-tenders:
    get:
      summary: Mock Government e-Marketplace (GeM) Tender Portal
      description: Built-in high-fidelity government tender board for offline hackathon evaluation.
      operationId: getMockTenders
      responses:
        '200':
          description: Rendered HTML tender board.
          content:
            text/html:
              schema:
                type: string

  /ws/telemetry:
    get:
      summary: WebSocket Live Telemetry Feed
      description: Real-time event stream broadcasting agent actions, Playwright navigation steps, cookie injection, and LLM token timing.
      operationId: wsTelemetry
      responses:
        '101':
          description: Switching Protocols to WebSocket.

components:
  schemas:
    TaskExecutionRequest:
      type: object
      required:
        - query
      properties:
        query:
          type: string
          example: "Check today's tender updates on the government portal"
        portal_target:
          type: string
          example: "http://127.0.0.1:8001/portal/gem-tenders"
        engine_override:
          type: string
          enum: [auto, groq, gemini, local]
          default: auto
        headless:
          type: boolean
          default: true

    TaskExecutionResponse:
      type: object
      properties:
        query:
          type: string
        status:
          type: string
          example: "COMPLETED"
        elapsed_seconds:
          type: number
          example: 8.75
        tenders_found:
          type: integer
          example: 4
        tenders:
          type: array
          items:
            $ref: '#/components/schemas/TenderItem'
        report_markdown:
          type: string
        engine_info:
          type: object

    TenderItem:
      type: object
      properties:
        id:
          type: string
          example: "GeM/2026/B/98210"
        title:
          type: string
          example: "Procurement of 500 Sovereign AI Edge Workstations"
        ministry:
          type: string
          example: "Ministry of Electronics & IT (MeitY)"
        department:
          type: string
          example: "National Informatics Centre (NIC)"
        estimated_value_inr:
          type: string
          example: "₹ 15,00,00,000"
        closing_date:
          type: string
          example: "2026-09-18 15:00 IST"
        eligibility:
          type: string
          example: "Class 1 Local Supplier (50%+ Make in India)"

    PortalSession:
      type: object
      properties:
        domain:
          type: string
          example: "gem.gov.in"
        portal_name:
          type: string
          example: "GeM (Government e-Marketplace)"
        user_role:
          type: string
          example: "Section Officer"
        organization:
          type: string
          example: "MeitY"
        status:
          type: string
          example: "Authenticated (Session Valid)"
        saved_at:
          type: string
        cookie_count:
          type: integer

    SystemStatus:
      type: object
      properties:
        is_running:
          type: boolean
        dual_engine:
          type: object
        vault_sessions_count:
          type: integer

  /api/audit/logs:
    get:
      summary: Retrieve Tamper-Evident SHA-256 Chained Audit Events
      description: Returns recent immutable audit log records with SHA-256 chain links and credential sanitization.
      parameters:
        - name: limit
          in: query
          schema:
            type: integer
            default: 50
      responses:
        '200':
          description: Audit ledger events retrieved.

  /api/audit/verify:
    get:
      summary: Cryptographically Verify Audit Chain Integrity
      description: Re-evaluates the full SHA-256 blockchain from genesis to head, reporting any tampering.
      responses:
        '200':
          description: Chain integrity verification report.

  /api/agent/pending:
    get:
      summary: List Actions Awaiting Human-in-the-Loop Officer Authorization
      description: Lists pending consequential/high-risk agent actions currently paused.
      responses:
        '200':
          description: List of pending authorization requests.

  /api/agent/approval/respond:
    post:
      summary: Submit Human Officer Approval or Rejection Decision
      description: Unblocks or cancels a paused high-risk agent action with officer credentials and rationale.
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [action_id, approved]
              properties:
                action_id:
                  type: string
                approved:
                  type: boolean
                officer_name:
                  type: string
                  default: "Executive User"
      responses:
        '200':
          description: Decision submitted and execution unblocked.

  /api/system/benchmark:
    get:
      summary: Run Sovereign Commodity-Hardware Benchmark Suite
      description: Measures actual evidence extraction throughput, verification latency, contradiction recall, and injection defense.
      responses:
        '200':
          description: Standardized hardware and sovereign subsystem benchmark report.