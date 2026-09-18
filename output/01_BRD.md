# Business Requirements Document (BRD)

**Project Name**: Sovereign On-Premise Agentic AI Workbench using Open-Weight LLMs  
**Problem Statement ID**: SIH PSC26117 (Smart India Hackathon)  
**Document Version**: 2.0 (Hackathon Engineering Release)  
**Classification**: Government of India / Sovereign Enterprise Grade  
**Target Architecture**: Zero-Cost Dual-Engine (Groq + Gemini Free APIs for Hackathon Demo & Local Open-Weight / BharatGPT for Air-Gapped Production)

---

## 1. Document Control & Revision History

### Revision Log
| Version | Date | Author | Description of Changes | Review Status |
| :--- | :--- | :--- | :--- | :--- |
| 1.0 | 2026-08-20 | Lead Solutions Architect | Initial Baseline for SIH PSC26117 | Draft |
| 2.0 | 2026-09-04 | Principal Systems Engineer | Dual-Engine zero-cost architecture (Groq + Gemini speed + Local BharatGPT) & Cookie Vault | Final Hackathon Baseline |

### Stakeholder Sign-Off Matrix
| Role | Title | Affiliation | Decision |
| :--- | :--- | :--- | :--- |
| **Sponsor** | Ministry of Electronics & IT (MeitY) Representative | SIH Evaluator | Approved |
| **Product Lead** | Chief Technology Officer | Sovereign AI Workbench Core | Approved |
| **Security Officer** | Cyber Security Advisor | CERT-In Aligned Compliance | Approved |
| **Operations Lead** | Principal DevOps Architect | Public Procurement Automation | Approved |

---

## 2. Executive Summary

Public sector employees across Indian ministries, public sector undertakings (PSUs), and state administrative bodies spend an estimated 3.5 to 5 hours daily performing routine, repetitive digital web workflows. These include navigating complex procurement portals (e.g., **GeM - Government e-Marketplace**, **CPPP - Central Public Procurement Portal**), tracking tender notifications, extracting table data into spreadsheets, filing regulatory forms, and cross-referencing archival records.

Commercial cloud AI assistants (such as OpenAI ChatGPT, Anthropic Claude, and Microsoft Copilot) pose severe **national data sovereignty risks**, vendor lock-in, and prohibitive recurring subscription costs. Sending sensitive government tender queries, officer credentials, or internal communications across overseas cloud servers violates Indian cyber defense guidelines.

The **Sovereign On-Premise Agentic AI Workbench (SIH PSC26117)** provides the definitive solution:
- **100% On-Premise & Air-Gapped**: Runs entirely on standard office laptops (8GB RAM) with **zero internet required** for core reasoning, utilizing open-weight local LLMs (BharatGPT, LLaMA-3, Mistral) with zero external data sharing.
- **Hackathon Turbo Mode (Zero Cost)**: For the high-speed evaluation environment of the Smart India Hackathon, the workbench incorporates a **Free-Tier Dual-Engine API Router** utilizing **Groq API** (`llama-3.3-70b-versatile` at ~500 tokens/sec) and **Google Gemini API** (`gemini-1.5-flash` with massive context) at **absolute $0 cost**.
- **Instant OTP-Less Cookie Vault**: Eliminates re-authentication friction by securely persisting local browser session cookies. Officers login once, and the AI agent automatically loads the active session without repeated password or OTP prompts.
- **Natural Language Task Execution**: Officers type what they want in plain English (*"Check today's tender updates on the government portal"*); the AI autonomously opens the portal, navigates, extracts table data, filters by department eligibility, and generates structured executive briefings.

---

## 3. Business Problem Statement & Market Opportunity

### 3.1 Current Status Quo & Operational Bottlenecks
1. **The Tender Tracking Grind**: A procurement officer monitoring GeM for IT hardware tenders must manually search, download 15+ individual PDF bids, parse eligibility requirements, and compile comparison tables. This consumes 20+ hours per week per department.
2. **Session Timeout & OTP Exhaustion**: Indian government portals enforce strict 10-15 minute session timeouts with mandatory SMS/Email OTP verification on every re-entry, severely breaking workflow continuity.
3. **Data Sovereignty Dilemma**: Cloud AI tools are forbidden on confidential networks. Officers are forced to either work entirely manually or inadvertently breach security policies by copying text into cloud chatbots.
4. **Hardware Constraints**: Government departments cannot afford dedicated H100/A100 GPU clusters for every administrative unit. Solutions must run on commoditized Intel Core i5/i7 laptops with 8GB–16GB RAM.

### 3.2 Cost of Inaction vs. Projected Value Creation
| Operational Metric | Current State (Manual) | Projected State (Sovereign Workbench) | Impact & Value Unlocked |
| :--- | :--- | :--- | :--- |
| **Daily Tender Audit Time** | 3.5 Hours / Day | 45 Seconds (Autonomous) | **85% reduction in manual drudgery** |
| **Authentication Friction** | 6–8 OTPs / Day | 0 OTPs (Instant Cookie Vault) | Seamless continuity, zero wait time |
| **Cloud API & License Cost** | $20–$40 / user / month | **$0.00 / month** | 100% Free & Open-Source (Zero budget burden) |
| **Data Breach Risk** | High (Cloud leaks) | Zero (Air-gapped local sandbox) | Total compliance with DPDP Act 2023 |
| **Tender Submission Misses** | 12% missed deadlines | 0% (Automated alert monitor) | Higher competitive bidding participation |

---

## 4. Target Market & Demographics

### 4.1 Primary User Segments
1. **Central Ministry Officers (MeitY, MoF, MoD, MHA)**: Under Secretaries, Section Officers, and Desk Officers needing daily briefing digests and portal monitoring.
2. **State Government Secretariats**: District Collectors and administrative departments handling local tenders, municipal licenses, and citizen grievances.
3. **Public Sector Undertakings (BHEL, NTPC, ONGC, SAIL)**: Procurement and vendor management teams managing multi-crore industrial bids.
4. **Defense & Critical Infrastructure**: Air-gapped defense establishments requiring strict sovereign execution with zero telemetry.

### 4.2 Total Addressable Market (TAM / SAM / SOM)
- **TAM**: 15 Million+ government administrative desks and PSU workstations across India.
- **SAM**: 2.5 Million procurement, finance, and administrative desk officers interacting with GeM/CPPP.
- **SOM (SIH Pilot Target)**: 50,000 procurement desks across 12 target ministries within 18 months of rollout.

---

## 5. Strategic Alignment: Atmanirbhar Bharat & Make In India

The project directly advances the Prime Minister's vision of **Atmanirbhar Bharat (Self-Reliant India)**:
1. **Indigenous AI Stack**: Engineered to operate on indigenous models like **BharatGPT** and open-weight architectures, eliminating reliance on foreign AI cloud conglomerates.
2. **Zero Recurring Foreign Exchange Outflow**: Standard cloud AI tools drain foreign currency via USD SaaS subscriptions. This platform requires zero recurring dollars.
3. **Inclusive Language Support**: Built to support 22 official Indian languages using open-source multilingual embeddings and LLM backbones.

---

## 6. Financial Feasibility & $0 Cost Model

The system is engineered for **absolute zero cost**:
- **Zero Software License Fees**: Built on open-source Python, FastAPI, Playwright, SQLite, and Chromium.
- **Zero API Incurred Cost**:
  - For Hackathon/Demo: Utilizing perpetual free tiers of Groq Cloud (Free rate-limited tier) and Google AI Studio Gemini API.
  - For On-Premise Government: Utilizing local GGUF/Ollama 4-bit quantized open-weight models running on host CPU/RAM ($0 compute bill).
- **Standard Hardware Compatibility**: Runs on existing office machines without requiring GPU upgrades.

---

## 7. RACI Governance Matrix

| Lifecycle Stage | Section Officer (User) | SIH Dev Team (Architects) | Cyber Security Auditor | Ministry IT (Admin) |
| :--- | :--- | :--- | :--- | :--- |
| **Requirements Gathering** | Accountable | Responsible | Consulted | Informed |
| **System Architecture** | Consulted | Accountable | Consulted | Informed |
| **Security & Air-Gap Audit** | Informed | Responsible | Accountable | Consulted |
| **Dual-Engine Hackathon Build**| Informed | Accountable | Consulted | Informed |
| **Acceptance & Evaluation** | Consulted | Responsible | Accountable | Accountable |