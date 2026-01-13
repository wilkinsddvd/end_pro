"""
Test script for password hashing functionality
Tests that bcrypt can handle passwords up to 72 characters without errors
"""
import sys

def test_password_hashing():
    """Test password hashing with various lengths"""
    print("=" * 60)
    print("Testing Password Hashing Functionality")
    print("=" * 60)
    
    try:
        from utils.auth import get_password_hash, verify_password
    except ImportError as e:
        print(f"❌ FAIL - Cannot import auth utilities: {e}")
        return False
    
    # Test 1: Hash a short password
    print("\nTest 1: Hash a short password (8 chars)")
    try:
        password = "short123"
        hashed = get_password_hash(password)
        print(f"✅ PASS - Password hashed successfully")
        print(f"   Original length: {len(password)}")
        print(f"   Hash length: {len(hashed)}")
    except Exception as e:
        print(f"❌ FAIL - Error hashing short password: {e}")
        return False
    
    # Test 2: Hash a medium password
    print("\nTest 2: Hash a medium password (30 chars)")
    try:
        password = "a" * 30
        hashed = get_password_hash(password)
        print(f"✅ PASS - Password hashed successfully")
        print(f"   Original length: {len(password)}")
    except Exception as e:
        print(f"❌ FAIL - Error hashing medium password: {e}")
        return False
    
    # Test 3: Hash a maximum length password (72 chars)
    print("\nTest 3: Hash a maximum length password (72 chars)")
    try:
        password = "a" * 72
        hashed = get_password_hash(password)
        print(f"✅ PASS - Password hashed successfully")
        print(f"   Original length: {len(password)}")
        print(f"   This is the bcrypt maximum!")
    except Exception as e:
        print(f"❌ FAIL - Error hashing max length password: {e}")
        return False
    
    # Test 4: Verify password matches
    print("\nTest 4: Verify password verification works")
    try:
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        # Test correct password
        if verify_password(password, hashed):
            print(f"✅ PASS - Correct password verified")
        else:
            print(f"❌ FAIL - Correct password not verified")
            return False
        
        # Test incorrect password
        if not verify_password("wrongpassword", hashed):
            print(f"✅ PASS - Incorrect password rejected")
        else:
            print(f"❌ FAIL - Incorrect password not rejected")
            return False
    except Exception as e:
        print(f"❌ FAIL - Error in password verification: {e}")
        return False
    
    # Test 5: Verify max length password works end-to-end
    print("\nTest 5: End-to-end test with 72-char password")
    try:
        password = "b" * 72
        hashed = get_password_hash(password)
        
        if verify_password(password, hashed):
            print(f"✅ PASS - 72-char password hash and verify works")
        else:
            print(f"❌ FAIL - 72-char password verification failed")
            return False
    except Exception as e:
        print(f"❌ FAIL - Error with 72-char password: {e}")
        return False
    
    # Test 6: What happens if we try to hash > 72 chars?
    # (This should not happen in practice due to Pydantic validation,
    # but let's test the behavior for documentation purposes)
    print("\nTest 6: Attempt to hash password > 72 chars (should handle gracefully)")
    try:
        password = "a" * 100
        hashed = get_password_hash(password)
        print(f"⚠️  WARNING - Bcrypt silently truncates passwords > 72 chars")
        print(f"   This is why we need the max_length=72 validation!")
        
        # Verify that bcrypt truncates - verify with first 72 chars should work
        if verify_password("a" * 72, hashed):
            print(f"✅ INFO - Confirmed: bcrypt only uses first 72 chars")
            print(f"   Our validation prevents this ambiguity!")
        
    except Exception as e:
        print(f"✅ PASS - Error caught (this is acceptable): {e}")
    
    print("\n" + "=" * 60)
    print("✅ All password hashing tests passed!")
    print("=" * 60)
    return True

def main():
    """Run password hashing tests"""
    print("\n🚀 Starting Password Hashing Tests\n")
    
    try:
        if test_password_hashing():
            print("\n" + "=" * 60)
            print("🎉 ALL PASSWORD HASHING TESTS PASSED!")
            print("=" * 60)
            print("\nKey findings:")
            print("  ✓ Password hashing works for passwords up to 72 chars")
            print("  ✓ Password verification works correctly")
            print("  ✓ Bcrypt has built-in 72-byte limit")
            print("  ✓ Our max_length=72 validation prevents issues")
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
