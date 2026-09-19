import unittest
from fastapi.testclient import TestClient
from server import app, vault

class TestOfficerCredentialsAirGapVault(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_list_officer_credentials(self):
        res = self.client.get("/api/workbench/sessions")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "SUCCESS")
        self.assertIsInstance(data["sessions"], list)
        self.assertGreaterEqual(len(data["sessions"]), 1)

    def test_create_and_delete_officer_credential(self):
        domain = "mock-airgap-portal.gov.in"
        payload = {
            "domain": domain,
            "portal_name": "Mock Air-Gap Portal",
            "user_role": "Chief Procurement Officer",
            "organization": "National Informatics Centre",
            "raw_cookies": "SSO_SESSION=mock_sso_val_123; CSRF_TOKEN=mock_csrf_456"
        }

        # 1. Save
        res_save = self.client.post("/api/workbench/sessions", json=payload)
        self.assertEqual(res_save.status_code, 200)
        save_data = res_save.json()
        self.assertEqual(save_data["status"], "SUCCESS")

        # Verify in vault directly
        saved_session = vault.get_session(domain)
        self.assertIsNotNone(saved_session)
        self.assertEqual(saved_session["portal_name"], "Mock Air-Gap Portal")
        self.assertEqual(saved_session["user_role"], "Chief Procurement Officer")
        self.assertEqual(len(saved_session["cookies"]), 2)

        # 2. Delete
        res_del = self.client.delete(f"/api/workbench/sessions/{domain}")
        self.assertEqual(res_del.status_code, 200)
        del_data = res_del.json()
        self.assertEqual(del_data["status"], "SUCCESS")

        # Verify deletion
        self.assertIsNone(vault.get_session(domain))

if __name__ == "__main__":
    unittest.main()
