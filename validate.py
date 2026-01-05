#!/usr/bin/env python3
"""
Simple validation script to check if the API code is correctly structured.
This doesn't require a running server or database.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test if all modules can be imported"""
    print("Testing imports...")
    
    try:
        # Test model imports
        from models import User, Post, Category, Tag, Comment, SiteInfo, Menu
        print("✓ All models imported successfully")
        
        # Test schema imports
        from schemas import (
            UserRegister, UserLogin, TokenResponse,
            PostCreate, PostUpdate, PostOut,
            CategoryCreate, CategoryUpdate, CategoryOut,
            TagCreate, TagUpdate, TagOut,
            CommentCreate, CommentOut
        )
        print("✓ All schemas imported successfully")
        
        # Test utils imports
        from utils.auth import create_access_token, decode_access_token, get_password_hash, verify_password
        print("✓ Auth utils imported successfully")
        
        from utils.dependencies import get_current_user, require_current_user
        print("✓ Dependencies imported successfully")
        
        # Test API imports
        from api import auth, posts, categories, tags, comments, archive, menus, siteinfo, interaction
        print("✓ All API modules imported successfully")
        
        # Test main app
        from main import app
        print("✓ Main app imported successfully")
        
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_schemas():
    """Test if schemas work correctly"""
    print("\nTesting schemas...")
    
    try:
        from schemas import UserRegister, PostCreate, CommentCreate
        
        # Test user schema
        user = UserRegister(username="testuser", password="testpass123")
        assert user.username == "testuser"
        print("✓ UserRegister schema works")
        
        # Test post schema
        post = PostCreate(
            title="Test Post",
            content="Test content",
            summary="Test summary",
            category_id=1,
            tag_ids=[1, 2]
        )
        assert post.title == "Test Post"
        print("✓ PostCreate schema works")
        
        # Test comment schema
        comment = CommentCreate(
            post_id=1,
            author_name="Test Author",
            content="Test comment"
        )
        assert comment.post_id == 1
        print("✓ CommentCreate schema works")
        
        return True
    except Exception as e:
        print(f"✗ Schema test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_auth_utils():
    """Test authentication utilities"""
    print("\nTesting auth utilities...")
    
    try:
        from utils.auth import get_password_hash, verify_password, create_access_token, decode_access_token
        
        # Test password hashing
        password = "testpassword123"
        hashed = get_password_hash(password)
        assert verify_password(password, hashed)
        assert not verify_password("wrongpassword", hashed)
        print("✓ Password hashing works")
        
        # Test JWT token
        token = create_access_token(data={"sub": "123"})
        payload = decode_access_token(token)
        assert payload is not None
        assert payload["sub"] == "123"
        print("✓ JWT token creation and decoding works")
        
        # Test invalid token
        invalid_payload = decode_access_token("invalid.token.here")
        assert invalid_payload is None
        print("✓ Invalid token handling works")
        
        return True
    except Exception as e:
        print(f"✗ Auth utils test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_model_relationships():
    """Test if model relationships are correctly defined"""
    print("\nTesting model relationships...")
    
    try:
        from models import Post, Category, Tag, Comment, User
        
        # Check Post relationships
        assert hasattr(Post, 'category')
        assert hasattr(Post, 'tags')
        assert hasattr(Post, 'author')
        print("✓ Post relationships defined")
        
        # Check Comment relationships
        assert hasattr(Comment, 'post')
        assert hasattr(Comment, 'parent')
        assert hasattr(Comment, 'user')
        print("✓ Comment relationships defined")
        
        # Check Category relationships
        assert hasattr(Category, 'posts')
        print("✓ Category relationships defined")
        
        # Check Tag relationships
        assert hasattr(Tag, 'posts')
        print("✓ Tag relationships defined")
        
        return True
    except Exception as e:
        print(f"✗ Model relationship test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all validation tests"""
    print("=" * 60)
    print("Blog Backend API - Validation Tests")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Schemas", test_schemas()))
    results.append(("Auth Utils", test_auth_utils()))
    results.append(("Model Relationships", test_model_relationships()))
    
    print("\n" + "=" * 60)
    print("Test Results:")
    print("=" * 60)
    
    for name, result in results:
        status = "PASSED" if result else "FAILED"
        symbol = "✓" if result else "✗"
        print(f"{symbol} {name}: {status}")
    
    all_passed = all(result for _, result in results)
    
    print("=" * 60)
    if all_passed:
        print("✓ All validation tests passed!")
        print("\nThe API is ready to deploy. To run the server:")
        print("  uvicorn main:app --reload")
        print("\nAPI documentation will be available at:")
        print("  http://localhost:8000/docs")
        return 0
    else:
        print("✗ Some tests failed. Please check the errors above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
