"""
Comprehensive Verification Suite for Sovereign Agentic AI Workbench (SIH PSC26117)
Tests:
1. Sovereign Local Open-Weight LLM Engine
2. Instant Cookie Session Vault (AES-256 Storage & Injection)
3. Autonomous Government Tender Agent (Playwright Navigation & Scraping)
4. All 13 SDLC Artifacts Integrity & Manifest Validation
5. FastAPI REST & Portal Endpoints
"""
import asyncio
import json
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

from dual_engine_llm import DualEngineLLM
from cookie_vault import CookieVault
from tender_agent import TenderAgent
from server import app


class TestSovereignWorkbenchSuite(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)
        self.output_dir = Path(__file__).resolve().parent / "output"

    def test_01_local_engine_status(self):
        """Verify Sovereign Local LLM engine detects configured local models."""
        llm = DualEngineLLM()
        info = llm.get_active_engine_info()
        self.assertIn("local_sovereign", info)
        self.assertEqual(info["local_sovereign"]["model"], "llama3:latest")
        print("[PASS] Test 1: Sovereign Local Engine Status Verified.")

    def test_02_cookie_vault(self):
        """Verify Cookie Vault loads pre-authenticated sessions for GeM and CPPP portals."""
        vault = CookieVault()
        sessions = vault.list_sessions()
        self.assertGreaterEqual(len(sessions), 2)
        domains = [s["domain"] for s in sessions]
        self.assertIn("gem.gov.in", domains)
        self.assertIn("eprocure.gov.in", domains)
        cookies = vault.get_cookies_for_domain("gem.gov.in")
        self.assertGreaterEqual(len(cookies), 1)
        print(f"[PASS] Test 2: Cookie Vault Verified ({len(sessions)} active portal sessions).")

    def test_03_sdlc_artifacts_manifest(self):
        """Verify all 13 SDLC specification artifacts exist, are populated, and match manifest."""
        manifest_file = self.output_dir / "manifest.json"
        self.assertTrue(manifest_file.exists(), "manifest.json must exist in output/")

        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)

        self.assertEqual(manifest["total_artifacts"], 13)
        self.assertEqual(len(manifest["artifacts"]), 13)

        expected_files = [
            "01_BRD.md", "02_PRD.md", "03_User_Journeys.md", "04_UI_UX_Specs.md",
            "05_Architecture_Diagram.md", "06_TRD.md", "07_Detailed_Design.md",
            "08_API_Contract_OpenAPI.md", "09_Implementation_Plan.md", "10_Test_Strategy.md",
            "11_ADRs.md", "12_Security_Compliance.md", "13_Runbook_Deployment.md"
        ]

        for fname in expected_files:
            fpath = self.output_dir / fname
            self.assertTrue(fpath.exists(), f"{fname} must exist in output/")
            content = fpath.read_text(encoding="utf-8")
            self.assertGreater(len(content), 500, f"{fname} should have substantial content")
            self.assertIn("Sovereign", content, f"{fname} must be tailored to Sovereign Workbench")

        master_file = self.output_dir / "SDLC_Master_Specification.md"
        self.assertTrue(master_file.exists())
        self.assertGreater(len(master_file.read_text(encoding="utf-8")), 20000)
        print("[PASS] Test 3: All 13 SDLC Specification Artifacts Verified.")

    def test_04_fastapi_endpoints(self):
        """Verify FastAPI endpoints: status, sessions, mock portal."""
        res_status = self.client.get("/api/workbench/status")
        self.assertEqual(res_status.status_code, 200)
        data_status = res_status.json()
        self.assertIn("dual_engine", data_status)
        self.assertIn("vault_sessions", data_status)

        res_sessions = self.client.get("/api/workbench/sessions")
        self.assertEqual(res_sessions.status_code, 200)

        res_portal = self.client.get("/portal/gem-tenders")
        self.assertEqual(res_portal.status_code, 200)
        self.assertIn("Government e-Marketplace", res_portal.text)
        print("[PASS] Test 4: FastAPI REST & Mock GeM Portal Endpoints Verified.")

    def test_05_tender_agent_e2e(self):
        """Verify TenderAgent autonomous flow: Playwright + Cookie Vault + LLM Synthesis."""
        agent = TenderAgent()
        result = asyncio.run(agent.run_tender_audit(
            query="Check today's tender updates on the government portal",
            portal_target="http://127.0.0.1:8001/portal/gem-tenders",
            headless=True
        ))
        self.assertEqual(result["status"], "COMPLETED")
        self.assertGreaterEqual(result["tenders_found"], 4)
        self.assertIn("report_markdown", result)
        self.assertGreater(len(result["report_markdown"]), 200)
        print(f"[PASS] Test 5: End-to-End Tender Extraction & Synthesis Verified ({result['elapsed_seconds']}s).")


if __name__ == "__main__":
    unittest.main()
