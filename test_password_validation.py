"""
Test script for password length validation
Tests registration and login with various password lengths
"""
import os
import sys
import traceback
import json
import requests
import string
import random

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

def generate_random_username():
    """Generate a random username for testing"""
    return f"testuser_{random.randint(10000, 99999)}"

def test_register_valid_password():
    """Test registration with valid password lengths"""
    print("=" * 50)
    print("Testing registration with valid passwords")
    print("=" * 50)
    
    # Test with minimum length password (6 characters)
    print("\nTest 1: Minimum length password (6 chars)")
    username = generate_random_username()
    response = requests.post(
        f"{BASE_URL}/api/register",
        json={"username": username, "password": "pass12"}
    )
    result = response.json()
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
    assert response.status_code == 200
    assert result["code"] == 200
    assert result["msg"] == "注册成功"
    print("✅ Minimum length password accepted!")
    
    # Test with normal length password (20 characters)
    print("\nTest 2: Normal length password (20 chars)")
    username = generate_random_username()
    response = requests.post(
        f"{BASE_URL}/api/register",
        json={"username": username, "password": "a" * 20}
    )
    result = response.json()
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
    assert response.status_code == 200
    assert result["code"] == 200
    assert result["msg"] == "注册成功"
    print("✅ Normal length password accepted!")
    
    # Test with maximum length password (72 characters)
    print("\nTest 3: Maximum length password (72 chars)")
    username = generate_random_username()
    max_password = "a" * 72
    response = requests.post(
        f"{BASE_URL}/api/register",
        json={"username": username, "password": max_password}
    )
    result = response.json()
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
    assert response.status_code == 200
    assert result["code"] == 200
    assert result["msg"] == "注册成功"
    print("✅ Maximum length password accepted!")
    print()

def test_register_invalid_password():
    """Test registration with invalid password lengths"""
    print("=" * 50)
    print("Testing registration with invalid passwords")
    print("=" * 50)
    
    # Test with password too short (less than 6 characters)
    print("\nTest 1: Password too short (5 chars)")
    username = generate_random_username()
    response = requests.post(
        f"{BASE_URL}/api/register",
        json={"username": username, "password": "pass1"}
    )
    result = response.json()
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
    # Pydantic validation should reject this
    assert response.status_code == 422 or response.status_code == 400
    print("✅ Password too short properly rejected!")
    
    # Test with password too long (73 characters)
    print("\nTest 2: Password too long (73 chars)")
    username = generate_random_username()
    long_password = "a" * 73
    response = requests.post(
        f"{BASE_URL}/api/register",
        json={"username": username, "password": long_password}
    )
    result = response.json()
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
    # Should be rejected with 422 (pydantic) or 400 (our validation)
    assert response.status_code in [422, 400]
    print("✅ Password too long properly rejected!")
    
    # Test with extremely long password (200 characters)
    print("\nTest 3: Extremely long password (200 chars)")
    username = generate_random_username()
    extreme_password = "a" * 200
    response = requests.post(
        f"{BASE_URL}/api/register",
        json={"username": username, "password": extreme_password}
    )
    result = response.json()
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
    # Should be rejected with 422 (pydantic) or 400 (our validation)
    assert response.status_code in [422, 400]
    # Ensure it's not a 500 error
    assert response.status_code != 500
    print("✅ Extremely long password properly rejected without 500 error!")
    print()

def test_login_valid_password():
    """Test login with valid password"""
    print("=" * 50)
    print("Testing login with valid passwords")
    print("=" * 50)
    
    # Create a user first
    username = generate_random_username()
    password = "validpassword123"
    register_response = requests.post(
        f"{BASE_URL}/api/register",
        json={"username": username, "password": password}
    )
    assert register_response.status_code == 200
    
    # Test login with correct password
    print("\nTest 1: Login with correct password")
    response = requests.post(
        f"{BASE_URL}/api/login",
        json={"username": username, "password": password}
    )
    result = response.json()
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
    assert response.status_code == 200
    assert result["code"] == 200
    assert result["msg"] == "登录成功"
    assert "token" in result["data"]
    print("✅ Login successful with valid password!")
    
    # Create another user with maximum length password
    username2 = generate_random_username()
    max_password = "b" * 72
    register_response = requests.post(
        f"{BASE_URL}/api/register",
        json={"username": username2, "password": max_password}
    )
    assert register_response.status_code == 200
    
    # Test login with maximum length password
    print("\nTest 2: Login with maximum length password (72 chars)")
    response = requests.post(
        f"{BASE_URL}/api/login",
        json={"username": username2, "password": max_password}
    )
    result = response.json()
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
    assert response.status_code == 200
    assert result["code"] == 200
    assert result["msg"] == "登录成功"
    print("✅ Login successful with maximum length password!")
    print()

def test_login_invalid_password():
    """Test login with invalid password lengths"""
    print("=" * 50)
    print("Testing login with invalid passwords")
    print("=" * 50)
    
    # Create a user first
    username = generate_random_username()
    password = "validpassword123"
    register_response = requests.post(
        f"{BASE_URL}/api/register",
        json={"username": username, "password": password}
    )
    assert register_response.status_code == 200
    
    # Test login with extremely long password
    print("\nTest 1: Login with extremely long password (200 chars)")
    extreme_password = "a" * 200
    response = requests.post(
        f"{BASE_URL}/api/login",
        json={"username": username, "password": extreme_password}
    )
    result = response.json()
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
    # Should be rejected with 422 (pydantic) or 400 (our validation)
    assert response.status_code in [422, 400]
    # Ensure it's not a 500 error
    assert response.status_code != 500
    print("✅ Extremely long password properly rejected without 500 error!")
    
    # Test login with password length 73
    print("\nTest 2: Login with password length 73")
    long_password = "a" * 73
    response = requests.post(
        f"{BASE_URL}/api/login",
        json={"username": username, "password": long_password}
    )
    result = response.json()
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
    # Should be rejected with 422 (pydantic) or 400 (our validation)
    assert response.status_code in [422, 400]
    assert response.status_code != 500
    print("✅ Password length 73 properly rejected without 500 error!")
    print()

def test_response_format_consistency():
    """Test that all responses maintain consistent JSON format"""
    print("=" * 50)
    print("Testing response format consistency")
    print("=" * 50)
    
    # Test various scenarios and verify response format
    test_cases = [
        ("Valid registration", "register", {"username": generate_random_username(), "password": "validpass"}),
        ("Invalid long password registration", "register", {"username": generate_random_username(), "password": "a" * 200}),
        ("Invalid login", "login", {"username": "nonexistent", "password": "anypass"}),
        ("Invalid long password login", "login", {"username": "anyuser", "password": "a" * 200}),
    ]
    
    for test_name, endpoint, payload in test_cases:
        print(f"\nTest: {test_name}")
        response = requests.post(f"{BASE_URL}/api/{endpoint}", json=payload)
        result = response.json()
        
        # Verify response has standard structure
        assert "code" in result, f"Response missing 'code' field: {result}"
        assert "data" in result or "detail" in result, f"Response missing 'data' or 'detail' field: {result}"
        assert "msg" in result or "detail" in result, f"Response missing 'msg' or 'detail' field: {result}"
        
        # Verify no 500 errors for validation issues
        if "password" in str(payload) and len(payload.get("password", "")) > 72:
            assert response.status_code != 500, f"Got 500 error for long password: {result}"
        
        print(f"✅ Response format consistent for: {test_name}")
    
    print("\n✅ All responses maintain consistent JSON format!")
    print()

if __name__ == "__main__":
    try:
        print("\n🚀 Starting password validation tests...\n")
        test_register_valid_password()
        test_register_invalid_password()
        test_login_valid_password()
        test_login_invalid_password()
        test_response_format_consistency()
        print("=" * 50)
        print("🎉 All password validation tests passed!")
        print("=" * 50)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        traceback.print_exc()
        sys.exit(1)
