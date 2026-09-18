# Sovereign AI Workbench — Smart India Hackathon Idea Deck

## Problem Statement: PSC26117 | Theme: Smart Automation | Software Edition

This directory contains the **official 6-slide Smart India Hackathon idea presentation** for the **Sovereign AI Workbench**, designed to strict 1920×1080 16:9 geometry, cybersecurity/government-tech visual language, and the verified hybrid demo vs. sovereign deployment architecture.

---

## 📂 Deliverable Structure

```
presentation/
├── index.html         # Complete 6-slide HTML presentation
├── style.css          # Cyber/govtech design system & 1920x1080 print layout
├── app.js             # 16:9 responsive scaler & keyboard controller
├── export_pdf.js      # Automated Puppeteer PDF export script
├── README_EXPORT.md   # Documentation & export guide
└── export/
    └── Sovereign_AI_Workbench_SIH_PSC26117_Deck.pdf  # Generated PDF
```

---

## 🎯 6-Slide Structure (Non-Negotiable SIH Format)

| Slide | Title | Core Focus |
|---|---|---|
| **01** | **TITLE** | Problem Statement `PSC26117`, Positioning, Operational Trust Boundary Box, Claim Legend |
| **02** | **PROPOSED SOLUTION** | Before (Cloud Exposure) vs. After (Sovereign Edge), 5 Differentiator Cards |
| **03** | **TECHNICAL APPROACH** | 5-Layer Stack Architecture, Dual-Execution Policy Switcher, Trust Boundary Map |
| **04** | **FEASIBILITY & VIABILITY** | 3-Column Engineering Matrix: Feasible Now vs. Audited Risks vs. Mitigations |
| **05** | **IMPACT & BENEFITS** | Sensitive Gov Workflow Value Flow, 6 Grounded KPI Cards, DPDP Alignment |
| **06** | **RESEARCH & REFERENCES** | 5 Academic & Government References + 5 Repository Audit & Validation Cards |

---

## 🏷️ Claim Discipline Status Indicators

Every claim, metric, and component is labeled honestly:

- `✓ VERIFIED`: Implemented in the current codebase and verified by audit tests.
- `◐ HYBRID / DEMO`: Used for hackathon live judging acceleration (Cloud LLM gateway).
- `◇ TARGET`: Planned capability on the remediation / production air-gapped roadmap.

---

## 🚀 How to Run the Presentation Locally

Simply double-click `index.html` or open it in any modern browser (Chrome, Edge, Firefox):

```bash
# Or run via local HTTP server
npx serve presentation/
```

### Keyboard Shortcuts
- `→` / `Space` / `PageDown`: Next Slide
- `←` / `Backspace` / `PageUp`: Previous Slide
- `1` – `6`: Direct Jump to Slide
- `F`: Toggle Fullscreen Mode
- `P`: Print / Export to PDF

---

## 🖨️ How to Generate the PDF

### Option A: Automated Puppeteer Script (Recommended)
From the project root:

```bash
node presentation/export_pdf.js
```

This script:
1. Launches headless Chrome at `1920×1080` with retina device pixel ratio.
2. Emulates the `@media print` layout.
3. Exports the PDF with zero margins, zero scrollbars, and no UI controls.
4. Validates that the output contains **exactly 6 pages**.
5. Saves to `presentation/export/Sovereign_AI_Workbench_SIH_PSC26117_Deck.pdf`.

### Option B: Browser Native Print to PDF
1. Open `presentation/index.html` in Google Chrome or Microsoft Edge.
2. Press `Ctrl + P` (or press `P` on your keyboard).
3. Set **Destination**: `Save as PDF`.
4. Set **Layout**: `Landscape`.
5. Under **More settings**:
   - **Paper size**: `16:9` or `Custom (1920 x 1080 px)` or `Tabloid/Ledger`.
   - **Margins**: `None`.
   - **Options**: Check `Background graphics`.
   - **Options**: Uncheck `Headers and footers`.
6. Click **Save**.
