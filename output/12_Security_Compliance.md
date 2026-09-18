# Security, Threat Model & Compliance Matrix

**Product Name**: Sovereign On-Premise Agentic AI Workbench (SIH PSC26117)  
**Document Version**: 2.0  
**Compliance Standards**: Digital Personal Data Protection (DPDP) Act 2023 & CERT-In Guidelines  

---

## 1. STRIDE Threat Modeling for On-Premise Government AI

| STRIDE Threat Category | Potential Attack Vector | Severity | Sovereign Workbench Engineering Countermeasure |
| :--- | :--- | :--- | :--- |
| **Spoofing** | Attacker attempts to impersonate government officer to steal portal access. | High | Session cookies encrypted locally with host-bound PBKDF2 key; accessible only by the local OS user process. |
| **Tampering** | Rogue script alters extracted tender figures to mislead procurement decisions. | Critical | Raw HTML snapshots hashed with SHA-256 upon capture; cryptographic checksum verified before LLM synthesis. |
| **Repudiation** | Officer denies initiating an automated portal crawl or report generation. | Medium | Immutable SQLite `audit_logs` table records every prompt, timestamp, and action with local hash-chaining. |
| **Information Disclosure** | Sensitive tender queries or draft bid numbers leaked to overseas cloud LLMs. | Critical | **Sovereign Air-Gap Mode**: Zero external internet packets transmitted; all processing occurs strictly in host RAM. |
| **Denial of Service (DoS)** | Endless browser loops or memory leak crashing the 8GB RAM host machine. | High | Playwright browser contexts hard-capped with 30-second execution timeouts and automatic process disposal. |
| **Elevation of Privilege** | Self-healing LLM attempts to execute arbitrary OS commands via Python `exec()`. | Critical | **AST Static Inspector Sandbox**: Blocks all `import`, `os`, `sys`, `subprocess`, and filesystem write primitives before execution. |

---

## 2. Regulatory Compliance Readiness

### 2.1 Digital Personal Data Protection (DPDP) Act 2023 (India)
- **Data Minimization (Section 6)**: The workbench extracts only public procurement notices and explicit user-requested fields; zero background biometric or personal profiling data is retained.
- **Sovereign Boundary (Section 16)**: Sovereign Mode guarantees that no Indian administrative data crosses international geopolitical borders.
- **Purpose Limitation (Section 4)**: Processed tender intelligence is used exclusively for internal decision support and is purged upon task archive.

### 2.2 CERT-In (Indian Computer Emergency Response Team) Cyber Directives
- **Zero Inbound Attack Surface**: The web server binds strictly to loopback interface `127.0.0.1`. No external ports are opened on LAN or WAN.
- **Strict Log Retention**: Local audit logs maintained in SQLite with timestamps synchronized to Indian Standard Time (IST).
- **Vulnerability Isolation**: Python dependencies locked with deterministic hashes to prevent supply-chain tampering.

---

## 3. Cookie Vault Security & Memory Sanitization Protocol

1. **At-Rest Protection**: Stored session cookies in `portal_sessions.json` are encrypted using AES-256-GCM. Plaintext cookies are never serialized.
2. **In-Flight Protection**: Cookies are injected directly into Chromium memory buffers via Chrome DevTools Protocol; no intermediate temporary files are written to disk.
3. **Memory Zeroization**: Upon Playwright browser context close, in-memory cookie representations are explicitly overwritten with null bytes to prevent memory dump extraction.