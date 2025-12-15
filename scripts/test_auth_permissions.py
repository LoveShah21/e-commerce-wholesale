
import requests
import sys

BASE_URL = "http://localhost:8000"
EMAIL = "qa_hostile_01@example.com"
PASSWORD = "TestPass123!"

def log(msg, status="INFO"):
    print(f"[{status}] {msg}")

def test_auth_and_permissions():
    # 1. Login
    log(f"Attempting login for {EMAIL}...")
    try:
        resp = requests.post(f"{BASE_URL}/api/users/login/", json={"email": EMAIL, "password": PASSWORD})
        if resp.status_code != 200:
            log(f"Login failed: {resp.status_code} - {resp.text}", "FAIL")
            return
        
        data = resp.json()
        access_token = data.get("access")
        if not access_token:
            log("No access token returned", "FAIL")
            return
            
        log("Login successful. Token obtained.", "PASS")
        headers = {"Authorization": f"Bearer {access_token}"}
        
    except Exception as e:
        log(f"Login exception: {str(e)}", "FAIL")
        return

    # 2. Test Customer Access (Should Succeed)
    # Checking a known customer endpoint, e.g., Products or Cart
    log("Testing Customer Access (GET /api/cart/)...")
    resp = requests.get(f"{BASE_URL}/api/cart/", headers=headers)
    if resp.status_code == 200:
        log("Customer access verified (200 OK)", "PASS")
    else:
        log(f"Customer access failed: {resp.status_code} - {resp.text}", "FAIL")

    # 3. Test Admin Access (Should Fail)
    # Checking an admin endpoint
    log("Testing Admin Access (GET /api/admin/orders/)...")
    resp = requests.get(f"{BASE_URL}/api/admin/orders/", headers=headers)
    if resp.status_code == 403:
        log("Admin access correctly denied (403 Forbidden)", "PASS")
    else:
        log(f"Admin access check failed: Expected 403, got {resp.status_code}", "FAIL")
        
    # 4. Test Operator Access (Should Fail)
    log("Testing Operator Access (GET /api/manufacturing/inventory/)...")
    resp = requests.get(f"{BASE_URL}/api/manufacturing/inventory/", headers=headers)
    if resp.status_code == 403:
        log("Operator access correctly denied (403 Forbidden)", "PASS")
    else:
        log(f"Operator access check failed: Expected 403, got {resp.status_code}", "FAIL")

if __name__ == "__main__":
    test_auth_and_permissions()
