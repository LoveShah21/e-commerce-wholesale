import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def log(msg, status="INFO"):
    print(f"[{status}] {msg}")

def run_comprehensive_tests():
    bugs_found = []
    
    # 1. Login as customer
    log("=== CUSTOMER TESTS ===")
    resp = requests.post(f"{BASE_URL}/api/users/login/", json={
        "email": "qa_hostile_01@example.com",
        "password": "TestPass123!"
    })
    if resp.status_code != 200:
        log(f"Customer login failed: {resp.status_code}", "FAIL")
        return
    
    customer_tokens = resp.json()
    customer_headers = {"Authorization": f"Bearer {customer_tokens['access']}"}
    log("Customer login successful", "PASS")
    
    # 2. Add to cart with correct variant_size_id
    log("Adding to cart with variant_size_id=1...")
    resp = requests.post(f"{BASE_URL}/api/cart-items/", 
        headers=customer_headers,
        json={"variant_size_id": 1, "quantity": 1})
    log(f"Add to cart: {resp.status_code}", "PASS" if resp.status_code in [200, 201] else "FAIL")
    if resp.status_code not in [200, 201]:
        log(f"Add to cart error: {resp.text[:300]}", "INFO")
        bugs_found.append(f"Add to cart failed: {resp.status_code}")
    
    # 3. View cart
    resp = requests.get(f"{BASE_URL}/api/cart/", headers=customer_headers)
    if resp.status_code == 200:
        cart_data = resp.json()
        log(f"Cart has {len(cart_data.get('items', []))} items", "INFO")
    
    # 4. Permission tests
    log("=== PERMISSION TESTS ===")
    
    # Test Admin Orders endpoint
    resp = requests.get(f"{BASE_URL}/api/admin/orders/", headers=customer_headers)
    if resp.status_code not in [403, 401]:
        bugs_found.append(f"Admin Orders returns {resp.status_code} instead of 403")
    log(f"Customer -> Admin Orders: {resp.status_code}", "PASS" if resp.status_code in [403, 401] else "FAIL")
    
    resp = requests.get(f"{BASE_URL}/api/manufacturing/inventory/", headers=customer_headers)
    log(f"Customer -> Manufacturing Inventory: {resp.status_code}", "PASS" if resp.status_code == 403 else "FAIL")
    
    resp = requests.get(f"{BASE_URL}/api/dashboard/stats/", headers=customer_headers)
    log(f"Customer -> Dashboard Stats: {resp.status_code}", "PASS" if resp.status_code == 403 else "FAIL")
    
    # 5. Login as admin (correct email)
    log("=== ADMIN TESTS ===")
    resp = requests.post(f"{BASE_URL}/api/users/login/", json={
        "email": "admin@vaitikan.com",
        "password": "admin123"
    })
    if resp.status_code != 200:
        log(f"Admin login failed: {resp.status_code} - trying different password", "INFO")
        # Try common passwords
        for pwd in ["Admin123!", "password123", "vaitikan123"]:
            resp = requests.post(f"{BASE_URL}/api/users/login/", json={
                "email": "admin@vaitikan.com",
                "password": pwd
            })
            if resp.status_code == 200:
                log(f"Admin login with '{pwd}' successful", "PASS")
                break
        else:
            log("Admin login failed with all passwords", "FAIL")
            bugs_found.append("Admin account password unknown/not working")
            return bugs_found
    else:
        log("Admin login successful", "PASS")
    
    admin_tokens = resp.json()
    admin_headers = {"Authorization": f"Bearer {admin_tokens['access']}"}
    
    # 6. Admin access tests
    resp = requests.get(f"{BASE_URL}/api/dashboard/stats/", headers=admin_headers)
    log(f"Admin -> Dashboard Stats: {resp.status_code}", "PASS" if resp.status_code == 200 else "FAIL")
    
    # 7. Unauthenticated tests
    log("=== UNAUTHENTICATED TESTS ===")
    resp = requests.get(f"{BASE_URL}/api/cart/")
    log(f"No token -> Cart: {resp.status_code}", "PASS" if resp.status_code == 401 else "FAIL")
    
    resp = requests.get(f"{BASE_URL}/api/orders/")
    log(f"No token -> Orders: {resp.status_code}", "PASS" if resp.status_code == 401 else "FAIL")
    
    # 8. Token refresh
    log("=== TOKEN REFRESH TEST ===")
    resp = requests.post(f"{BASE_URL}/api/users/token/refresh/", json={
        "refresh": customer_tokens.get('refresh')
    })
    log(f"Token refresh: {resp.status_code}", "PASS" if resp.status_code == 200 else "FAIL")
    
    # 9. Invalid data tests
    log("=== INPUT VALIDATION TESTS ===")
    resp = requests.post(f"{BASE_URL}/api/cart-items/", 
        headers=customer_headers,
        json={"variant_size_id": 99999, "quantity": 1})
    log(f"Add invalid variant to cart: {resp.status_code}", "PASS" if resp.status_code in [400, 404] else "FAIL")
    
    resp = requests.post(f"{BASE_URL}/api/cart-items/", 
        headers=customer_headers,
        json={"variant_size_id": 1, "quantity": -5})
    log(f"Add negative quantity: {resp.status_code}", "PASS" if resp.status_code == 400 else "FAIL")
    if resp.status_code != 400:
        bugs_found.append("Negative quantity accepted in cart")
    
    log("=== TESTS COMPLETE ===")
    if bugs_found:
        log(f"BUGS FOUND: {len(bugs_found)}", "FAIL")
        for bug in bugs_found:
            log(f"  - {bug}", "BUG")
    
    return bugs_found

if __name__ == "__main__":
    run_comprehensive_tests()
