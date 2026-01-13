"""
Test script for authentication endpoints
Tests registration, login, and JWT authentication
"""
import os
import sys
import traceback
import json
import requests

BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

def test_register():
    """Test user registration endpoint"""
    print("=" * 50)
    print("Testing POST /api/register")
    print("=" * 50)
    
    # Test successful registration
    response = requests.post(
        f"{BASE_URL}/api/register",
        json={"username": "demouser", "password": "demo123456"}
    )
    result = response.json()
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
    assert response.status_code == 200
    assert result["code"] == 200
    assert result["msg"] == "注册成功"
    print("✅ Registration successful!")
    
    # Test duplicate username
    print("\nTesting duplicate username...")
    response = requests.post(
        f"{BASE_URL}/api/register",
        json={"username": "demouser", "password": "another123"}
    )
    result = response.json()
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
    assert response.status_code == 409
    assert result["code"] == 409
    assert result["msg"] == "用户名已存在"
    print("✅ Duplicate username properly rejected!")
    print()

def test_login():
    """Test user login endpoint"""
    print("=" * 50)
    print("Testing POST /api/login")
    print("=" * 50)
    
    # Test successful login
    response = requests.post(
        f"{BASE_URL}/api/login",
        json={"username": "demouser", "password": "demo123456"}
    )
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
    assert response.status_code == 200
    assert result["code"] == 200
    assert result["msg"] == "登录成功"
    assert "token" in result["data"]
    assert "user" in result["data"]
    print("✅ Login successful!")
    
    token = result["data"]["token"]
    
    # Test invalid password
    print("\nTesting invalid password...")
    response = requests.post(
        f"{BASE_URL}/api/login",
        json={"username": "demouser", "password": "wrongpass"}
    )
    result = response.json()
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
    assert response.status_code == 401
    assert result["code"] == 401
    assert result["msg"] == "用户名或密码错误"
    print("✅ Invalid password properly rejected!")
    
    # Test non-existent user
    print("\nTesting non-existent user...")
    response = requests.post(
        f"{BASE_URL}/api/login",
        json={"username": "nonexistent", "password": "anypass"}
    )
    result = response.json()
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
    assert response.status_code == 401
    assert result["code"] == 401
    assert result["msg"] == "用户名或密码错误"
    print("✅ Non-existent user properly rejected!")
    print()
    
    return token

def test_jwt_auth(token):
    """Test JWT authentication"""
    print("=" * 50)
    print("Testing GET /api/me (JWT Authentication)")
    print("=" * 50)
    
    # Test with valid token
    response = requests.get(
        f"{BASE_URL}/api/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    result = response.json()
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
    assert response.status_code == 200
    assert result["code"] == 200
    assert "username" in result["data"]
    print("✅ JWT authentication working!")
    
    # Test without token
    print("\nTesting without token...")
    response = requests.get(f"{BASE_URL}/api/me")
    result = response.json()
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(result, ensure_ascii=False, indent=2)}")
    assert result["code"] == 401
    print("✅ Properly rejects unauthenticated requests!")
    print()

if __name__ == "__main__":
    try:
        print("\n🚀 Starting API tests...\n")
        test_register()
        token = test_login()
        test_jwt_auth(token)
        print("=" * 50)
        print("🎉 All tests passed!")
        print("=" * 50)
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        traceback.print_exc()
        sys.exit(1)
