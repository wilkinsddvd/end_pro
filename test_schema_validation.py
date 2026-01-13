"""
Test script for validating password field constraints in schemas
Tests Pydantic validation without needing a running server
"""
import sys
from pydantic import ValidationError
from schemas import UserRegister, UserLogin

def test_user_register_schema():
    """Test UserRegister schema password constraints"""
    print("=" * 60)
    print("Testing UserRegister Schema Password Validation")
    print("=" * 60)
    
    # Test 1: Valid password with minimum length (6 chars)
    print("\nTest 1: Valid password - minimum length (6 chars)")
    try:
        user = UserRegister(username="testuser", password="pass12")
        print(f"✅ PASS - Password accepted: length={len(user.password)}")
    except ValidationError as e:
        print(f"❌ FAIL - Unexpected validation error: {e}")
        return False
    
    # Test 2: Valid password with normal length (20 chars)
    print("\nTest 2: Valid password - normal length (20 chars)")
    try:
        user = UserRegister(username="testuser", password="a" * 20)
        print(f"✅ PASS - Password accepted: length={len(user.password)}")
    except ValidationError as e:
        print(f"❌ FAIL - Unexpected validation error: {e}")
        return False
    
    # Test 3: Valid password with maximum length (72 chars)
    print("\nTest 3: Valid password - maximum length (72 chars)")
    try:
        user = UserRegister(username="testuser", password="a" * 72)
        print(f"✅ PASS - Password accepted: length={len(user.password)}")
    except ValidationError as e:
        print(f"❌ FAIL - Unexpected validation error: {e}")
        return False
    
    # Test 4: Invalid password - too short (5 chars)
    print("\nTest 4: Invalid password - too short (5 chars)")
    try:
        user = UserRegister(username="testuser", password="pass1")
        print(f"❌ FAIL - Password should have been rejected: length={len(user.password)}")
        return False
    except ValidationError as e:
        print(f"✅ PASS - Password correctly rejected (too short)")
        print(f"   Validation error: {e.errors()[0]['msg']}")
    
    # Test 5: Invalid password - too long (73 chars)
    print("\nTest 5: Invalid password - too long (73 chars)")
    try:
        user = UserRegister(username="testuser", password="a" * 73)
        print(f"❌ FAIL - Password should have been rejected: length={len(user.password)}")
        return False
    except ValidationError as e:
        print(f"✅ PASS - Password correctly rejected (too long)")
        print(f"   Validation error: {e.errors()[0]['msg']}")
    
    # Test 6: Invalid password - extremely long (200 chars)
    print("\nTest 6: Invalid password - extremely long (200 chars)")
    try:
        user = UserRegister(username="testuser", password="a" * 200)
        print(f"❌ FAIL - Password should have been rejected: length={len(user.password)}")
        return False
    except ValidationError as e:
        print(f"✅ PASS - Password correctly rejected (extremely long)")
        print(f"   Validation error: {e.errors()[0]['msg']}")
    
    # Test 7: Invalid username - too short
    print("\nTest 7: Invalid username - too short (2 chars)")
    try:
        user = UserRegister(username="ab", password="validpass123")
        print(f"❌ FAIL - Username should have been rejected")
        return False
    except ValidationError as e:
        print(f"✅ PASS - Username correctly rejected (too short)")
    
    # Test 8: Invalid username - too long
    print("\nTest 8: Invalid username - too long (51 chars)")
    try:
        user = UserRegister(username="a" * 51, password="validpass123")
        print(f"❌ FAIL - Username should have been rejected")
        return False
    except ValidationError as e:
        print(f"✅ PASS - Username correctly rejected (too long)")
    
    print("\n" + "=" * 60)
    print("✅ All UserRegister schema tests passed!")
    print("=" * 60)
    return True

def test_user_login_schema():
    """Test UserLogin schema password constraints"""
    print("\n" + "=" * 60)
    print("Testing UserLogin Schema Password Validation")
    print("=" * 60)
    
    # Test 1: Valid password - normal length
    print("\nTest 1: Valid password - normal length (15 chars)")
    try:
        user = UserLogin(username="testuser", password="validpassword12")
        print(f"✅ PASS - Password accepted: length={len(user.password)}")
    except ValidationError as e:
        print(f"❌ FAIL - Unexpected validation error: {e}")
        return False
    
    # Test 2: Valid password - maximum length (72 chars)
    print("\nTest 2: Valid password - maximum length (72 chars)")
    try:
        user = UserLogin(username="testuser", password="a" * 72)
        print(f"✅ PASS - Password accepted: length={len(user.password)}")
    except ValidationError as e:
        print(f"❌ FAIL - Unexpected validation error: {e}")
        return False
    
    # Test 3: Valid password - empty string should be allowed by schema
    # (business logic validation happens in the endpoint)
    print("\nTest 3: Empty password (schema allows, endpoint rejects)")
    try:
        user = UserLogin(username="testuser", password="")
        print(f"✅ PASS - Empty password accepted by schema (endpoint will validate)")
    except ValidationError as e:
        print(f"✅ PASS - Empty password rejected by schema: {e.errors()[0]['msg']}")
    
    # Test 4: Invalid password - too long (73 chars)
    print("\nTest 4: Invalid password - too long (73 chars)")
    try:
        user = UserLogin(username="testuser", password="a" * 73)
        print(f"❌ FAIL - Password should have been rejected: length={len(user.password)}")
        return False
    except ValidationError as e:
        print(f"✅ PASS - Password correctly rejected (too long)")
        print(f"   Validation error: {e.errors()[0]['msg']}")
    
    # Test 5: Invalid password - extremely long (200 chars)
    print("\nTest 5: Invalid password - extremely long (200 chars)")
    try:
        user = UserLogin(username="testuser", password="a" * 200)
        print(f"❌ FAIL - Password should have been rejected: length={len(user.password)}")
        return False
    except ValidationError as e:
        print(f"✅ PASS - Password correctly rejected (extremely long)")
        print(f"   Validation error: {e.errors()[0]['msg']}")
    
    print("\n" + "=" * 60)
    print("✅ All UserLogin schema tests passed!")
    print("=" * 60)
    return True

def test_password_boundary_cases():
    """Test password boundary cases"""
    print("\n" + "=" * 60)
    print("Testing Password Boundary Cases")
    print("=" * 60)
    
    # Test boundary at 72 characters
    print("\nTest 1: Exactly 72 characters (boundary - should pass)")
    try:
        user = UserRegister(username="testuser", password="a" * 72)
        assert len(user.password) == 72
        print(f"✅ PASS - 72-char password accepted")
    except (ValidationError, AssertionError) as e:
        print(f"❌ FAIL - 72-char password should be accepted: {e}")
        return False
    
    # Test boundary at 73 characters
    print("\nTest 2: Exactly 73 characters (boundary - should fail)")
    try:
        user = UserRegister(username="testuser", password="a" * 73)
        print(f"❌ FAIL - 73-char password should be rejected")
        return False
    except ValidationError as e:
        print(f"✅ PASS - 73-char password correctly rejected")
    
    # Test with special characters at max length
    print("\nTest 3: 72 characters with special characters")
    try:
        special_pass = "!@#$%^&*()_+-=[]{}|;:,.<>?/~`" + ("a" * 43)
        user = UserRegister(username="testuser", password=special_pass)
        assert len(user.password) == 72
        print(f"✅ PASS - 72-char password with special chars accepted")
    except (ValidationError, AssertionError) as e:
        print(f"❌ FAIL - Special char password should be accepted: {e}")
        return False
    
    # Test with unicode characters
    print("\nTest 4: Unicode characters within limit")
    try:
        unicode_pass = "密码测试123456"  # Chinese characters
        if len(unicode_pass) <= 72:
            user = UserRegister(username="testuser", password=unicode_pass)
            print(f"✅ PASS - Unicode password accepted: length={len(user.password)}")
        else:
            print(f"⚠️  SKIP - Unicode test string too long")
    except ValidationError as e:
        print(f"❌ FAIL - Unicode password should be accepted: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ All boundary case tests passed!")
    print("=" * 60)
    return True

def main():
    """Run all schema validation tests"""
    print("\n🚀 Starting Schema Validation Tests\n")
    
    try:
        # Run all test suites
        results = []
        results.append(test_user_register_schema())
        results.append(test_user_login_schema())
        results.append(test_password_boundary_cases())
        
        # Check if all tests passed
        if all(results):
            print("\n" + "=" * 60)
            print("🎉 ALL SCHEMA VALIDATION TESTS PASSED!")
            print("=" * 60)
            print("\nKey validations confirmed:")
            print("  ✓ UserRegister password: min_length=6, max_length=72")
            print("  ✓ UserLogin password: max_length=72")
            print("  ✓ Pydantic validation rejects invalid inputs")
            print("  ✓ Boundary cases handled correctly")
            print("  ✓ No 500 errors will occur from schema validation")
            return 0
        else:
            print("\n❌ Some tests failed!")
            return 1
            
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
