import requests
import json
import time

BASE_URL = "http://127.0.0.1:8001"

def test_hardware():
    print("Testing GET /api/system/hardware...")
    r = requests.get(f"{BASE_URL}/api/system/hardware")
    assert r.status_code == 200, f"Failed: {r.text}"
    data = r.json()
    assert "hardware" in data
    hw = data["hardware"]
    assert "recommended_models" in hw
    assert hw["total_ram_gb"] > 0
    print(f"Hardware passed! OS: {hw['os_label']}, Total RAM: {hw['total_ram_gb']} GB, Available: {hw['available_ram_gb']} GB")
    print(f"Total model recommendations: {len(hw['recommended_models'])}")

def test_profile_lifecycle():
    print("\nTesting Profile & Security Vault...")
    # 1. Get profile
    r = requests.get(f"{BASE_URL}/api/profile")
    assert r.status_code == 200
    p = r.json()["profile"]
    print(f"Initial profile: user={p.get('name')}, has_pwd={p.get('has_password')}")

    # 2. Update profile name & role
    r = requests.post(f"{BASE_URL}/api/profile/update", json={"name": "Officer Sharma", "role": "Senior Procurement Lead"})
    assert r.status_code == 200
    p = r.json()["profile"]
    assert p["name"] == "Officer Sharma"
    print("Profile update passed!")

    # 3. Set password
    r = requests.post(f"{BASE_URL}/api/profile/set-password", json={"password": "SecretPassword123!"})
    assert r.status_code == 200
    res = r.json()
    assert res.get("status") == "SUCCESS"
    recovery_key = res.get("recovery_key")
    assert recovery_key and recovery_key.startswith("SOV-")
    print(f"Set password passed! Generated Sovereign Recovery Key: {recovery_key}")

    # 4. Lock
    r = requests.post(f"{BASE_URL}/api/profile/lock")
    assert r.status_code == 200

    # Verify locked
    r = requests.get(f"{BASE_URL}/api/profile")
    assert r.json()["profile"].get("is_locked") == True
    print("Lock screen verified!")

    # 5. Unlock with wrong password
    r = requests.post(f"{BASE_URL}/api/profile/unlock", json={"password": "wrong"})
    assert r.status_code == 401
    print("Wrong password rejected properly!")

    # 6. Unlock with correct password
    r = requests.post(f"{BASE_URL}/api/profile/unlock", json={"password": "SecretPassword123!"})
    assert r.status_code == 200
    print("Unlock with password passed!")

    # 7. Lock again & test recovery key unlock
    requests.post(f"{BASE_URL}/api/profile/lock")
    r = requests.post(f"{BASE_URL}/api/profile/recover", json={"recovery_key": recovery_key, "new_password": "NewSecretPass456!"})
    assert r.status_code == 200
    res = r.json()
    new_recovery_key = res.get("new_recovery_key")
    print(f"Emergency Recovery Key passed! New key: {new_recovery_key}")

    # 8. Remove password for clean state
    r = requests.post(f"{BASE_URL}/api/profile/remove-password", json={"password": "NewSecretPass456!"})
    assert r.status_code == 200
    print("Remove password passed! Profile restored to open state.")

def test_ollama_endpoints():
    print("\nTesting Ollama API endpoints...")
    r = requests.get(f"{BASE_URL}/api/ollama/pull-status")
    assert r.status_code == 200
    status = r.json()
    assert "status" in status
    print(f"Pull status: {status['status']}")

    r = requests.post(f"{BASE_URL}/api/ollama/unload")
    assert r.status_code == 200
    print(f"Ollama unload response: {r.json()}")

def test_files_batch():
    print("\nTesting Documents Multi-Select / Batch operations...")
    r = requests.get(f"{BASE_URL}/api/workbench/files")
    assert r.status_code == 200
    files = r.json().get("uploaded_files", [])
    print(f"Found {len(files)} uploaded documents in workbench.")

    # Test batch delete on a dummy created test file in uploads/
    import os
    upload_dir = os.path.join(os.path.dirname(__file__), "output", "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    test_path = os.path.join(upload_dir, "batch_test_temp.txt")
    with open(test_path, "w") as f:
        f.write("temporary file for batch test")

    r = requests.post(f"{BASE_URL}/api/files/batch-delete", json={"files": ["batch_test_temp.txt"]})
    assert r.status_code == 200
    assert not os.path.exists(test_path)
    print("Batch delete passed!")

if __name__ == "__main__":
    time.sleep(1) # wait for server to bind
    test_hardware()
    test_profile_lifecycle()
    test_ollama_endpoints()
    test_files_batch()
    print("\nALL VERIFICATION TESTS PASSED SUCCESSFULLY!")
