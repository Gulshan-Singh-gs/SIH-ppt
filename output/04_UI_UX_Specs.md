# UI/UX Design Specifications

**Product Name**: Sovereign On-Premise Agentic AI Workbench (SIH PSC26117)  
**Document Version**: 2.0  
**Design Standards**: GIGW (Guidelines for Indian Government Websites) 3.0 & WCAG 2.1 AA  
**Theme**: Sovereign Glassmorphic Dark & Clean Administrative Light Modes  

---

## 1. Visual Design Philosophy & Design Tokens

The Sovereign Workbench UI combines high-tech agentic telemetry with clean, trustworthy Indian public-sector aesthetics. It is designed to look futuristic for hackathon evaluation while remaining strictly accessible and compliant with Indian government IT mandates.

### 1.1 Color Palette Tokens
| Token Name | Hex Code | HSL Representation | Semantic Application |
| :--- | :--- | :--- | :--- |
| `--bg-base` | `#0A0F1D` | `hsl(224, 49%, 8%)` | Primary deep sovereign background |
| `--bg-surface` | `#111827` | `hsl(220, 39%, 11%)` | Surface cards with backdrop blur glassmorphism |
| `--border-subtle` | `rgba(255, 255, 255, 0.08)` | - | Glass card boundaries |
| `--accent-saffron` | `#F59E0B` | `hsl(38, 92%, 50%)` | Government alert badges & high-priority tenders |
| `--accent-green` | `#10B981` | `hsl(160, 84%, 39%)` | Active authenticated status & successful task executions |
| `--accent-cyan` | `#06B6D4` | `hsl(189, 94%, 43%)` | Agent telemetry streams & Playwright browser triggers |
| `--text-primary` | `#F9FAFB` | `hsl(0, 0%, 98%)` | Primary headings, report titles, and key metrics |
| `--text-secondary` | `#9CA3AF` | `hsl(218, 11%, 65%)` | Subtitles, metadata, and timestamps |

### 1.2 Typography Tokens
- **Font Family (Display & UI)**: `'Inter'`, `'Outfit'`, system-ui, sans-serif
- **Font Family (Code & Telemetry)**: `'JetBrains Mono'`, `'Fira Code'`, monospace
- **Scale**:
  - `Display 1`: 32px / 1.2 (Sovereign Workbench Title)
  - `Heading 2`: 20px / 1.3 (Section Titles: Cookie Vault, Tender Intelligence)
  - `Body Regular`: 14px / 1.5 (Report Content, Descriptions)
  - `Mono Small`: 12px / 1.4 (Live WebSocket Telemetry)

---

## 2. Layout Hierarchy & Screen Inventory

The interface is organized into a single-pane, real-time command center:

```
+-----------------------------------------------------------------------------------------+
| [Ashoka Emblem] Sovereign AI Workbench  [SIH PSC26117]       [Engine: Groq Turbo ▼]     |
+-----------------------------------------------------------------------------------------+
| QUICK ACTIONS:  [Check Today's Tenders]  [Audit Active GeM Bids]  [Cookie Vault: 3 Active] |
+-----------------------------------------------------------------------------------------+
|  LEFT PANEL (Command & Live Telemetry)         |  RIGHT PANEL (Intelligence Report Canvas)|
|  +-------------------------------------------+ |  +------------------------------------+ |
|  | Natural Language Task Bar                 | |  | 🏛️ Executive Tender Intelligence  | |
|  | [ "Check today's tender updates..."    ]  | |  |                                    | |
|  | [ Execute Task ] [ Headless Mode: ON ]    | |  | [ Tenders Found: 4 ] [ Value: 42Cr]| |
|  +-------------------------------------------+ |  |                                    | |
|  | Live Telemetry Stream (WebSockets)        | |  | | Tender ID | Org | Value | Due |   | |
|  | [11:06:01] ⚡ Rehydrated GeM Session...   | |  | | GeM/98210 | MeitY | 15Cr | 48h |  | |
|  | [11:06:03] 🌐 Injected Cookies (Zero OTP) | |  |                                    | |
|  | [11:06:05] 📋 Extracted 4 Active Notices  | |  | Actionable Recommendations:        | |
|  | [11:06:08] 🧠 Groq LLaMA-3.3 Synthesized  | |  | 1. Submit EMD under MSME clause    | |
|  +-------------------------------------------+ |  | 2. Verify ISO 27001 requirement    | |
|  | Preserved Cookie Sessions:                | |  +------------------------------------+ |
|  | • GeM Portal: Active (Valid)              | |  [ Export Markdown ] [ Download PDF ] | |
|  | • CPPP Portal: Active (Valid)             | |                                         | |
+-----------------------------------------------------------------------------------------+
```

---

## 3. Interactive Component States

### 3.1 Dual-Engine Selector
- **Hackathon Turbo (Groq + Gemini API - Free)**: Active badge glowing cyan; tooltips display `Latency: <500ms | Free Tier`.
- **Sovereign Air-Gapped (Local Open-Weight)**: Active badge in emerald green; displays `100% Local (0 Network Packets)`.

### 3.2 Live Telemetry Terminal
- Automatic smooth auto-scroll to the newest timestamped event.
- Color-coded log levels:
  - `INFO`: Cyan (`[11:06:01] ℹ️ Initializing Playwright...`)
  - `AUTH`: Emerald (`[11:06:03] 🔑 Injected Preserved Cookies (No OTP Delay)`)
  - `WARN`: Amber (`[11:06:05] ⚠️ Captcha detected - auto-solved via local OCR`)
  - `DONE`: Purple (`[11:06:08] ✨ Synthesis complete in 8.7s`)

---

## 4. Accessibility & Indian Government Standards Compliance

- **GIGW 3.0 Compliance**: High contrast ratios (> 4.5:1 for body text, > 3:1 for large text).
- **Keyboard Navigability**: Full tab-order traversing: Input Bar -> Quick Presets -> Engine Selector -> Telemetry -> Export Buttons.
- **Screen Reader ARIA Attributes**: All dynamic telemetry updates wrapped in `aria-live="polite"` regions.