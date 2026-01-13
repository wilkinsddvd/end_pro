# Authentication API Documentation

## Overview
Backend login and registration API implemented with FastAPI + SQLAlchemy + MySQL, providing JWT-based authentication for the frontend.

## Technology Stack
- **Framework**: FastAPI (async)
- **Database**: MySQL with AsyncMy driver
- **ORM**: SQLAlchemy 2.0 (async)
- **Authentication**: JWT (JSON Web Tokens)
- **Password Encryption**: bcrypt via passlib

## Database Schema

### User Table
```sql
CREATE TABLE user (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(128) UNIQUE NOT NULL,
    password_hash VARCHAR(256) NOT NULL,
    created_at DATE NOT NULL DEFAULT CURRENT_DATE,
    INDEX idx_username (username)
);
```

## API Endpoints

### 1. User Registration

**Endpoint:** `POST /api/register`

**Request Body:**
```json
{
  "username": "string (3-50 chars)",
  "password": "string (min 6 chars)"
}
```

**Success Response (200):**
```json
{
  "code": 200,
  "data": {
    "id": 1,
    "username": "testuser"
  },
  "msg": "注册成功"
}
```

**Error Response - Duplicate Username (409):**
```json
{
  "code": 409,
  "data": null,
  "msg": "用户名已存在"
}
```

**Error Response - Validation Error (422):**
```json
{
  "detail": [
    {
      "type": "string_too_short",
      "loc": ["body", "username"],
      "msg": "String should have at least 3 characters"
    }
  ]
}
```

### 2. User Login

**Endpoint:** `POST /api/login`

**Request Body:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Success Response (200):**
```json
{
  "code": 200,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 1,
      "username": "testuser"
    }
  },
  "msg": "登录成功"
}
```

**Error Response - Invalid Credentials (401):**
```json
{
  "code": 401,
  "data": null,
  "msg": "用户名或密码错误"
}
```

### 3. Get Current User Info

**Endpoint:** `GET /api/me`

**Headers:**
```
Authorization: Bearer <JWT_TOKEN>
```

**Success Response (200):**
```json
{
  "code": 200,
  "data": {
    "id": 1,
    "username": "testuser"
  },
  "msg": "success"
}
```

**Error Response - Unauthorized (401):**
```json
{
  "code": 401,
  "data": {},
  "msg": "not authenticated"
}
```

### 4. User Logout

**Endpoint:** `POST /api/logout`

**Success Response (200):**
```json
{
  "code": 200,
  "data": {},
  "msg": "logout success"
}
```

**Note:** Logout is client-side only. The client should discard the JWT token from localStorage/sessionStorage.

## JWT Configuration

- **Algorithm:** HS256
- **Token Expiration:** 24 hours (1440 minutes)
- **Token Payload:** `{"sub": "user_id", "exp": timestamp}`

## Security Features

1. **Password Hashing:** All passwords are hashed using bcrypt with automatic salt generation
2. **Unique Usernames:** Database constraint ensures username uniqueness
3. **JWT Tokens:** Stateless authentication with expiration
4. **CORS Protection:** Configurable allowed origins
5. **Input Validation:** Pydantic schemas validate all inputs

## CORS Configuration

The API is configured to accept requests from:
- `http://localhost:3000`
- `http://localhost:8080`

To add more origins, update `ALLOWED_ORIGINS` in `config.py`.

## Environment Variables

Create a `.env` file (see `.env.example`):

```env
DATABASE_URL=mysql+asyncmy://root:password@localhost/db_on_work
SECRET_KEY=your-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440
```

## Testing

Run the test script to verify all endpoints:

```bash
python3 test_auth_api.py
```

This will test:
- ✅ User registration with unique username validation
- ✅ User login with credential verification
- ✅ JWT token generation and validation
- ✅ Password encryption (bcrypt)
- ✅ Error handling for invalid inputs

## Frontend Integration

### Example: Registration

```javascript
const register = async (username, password) => {
  const response = await fetch('http://localhost:8000/api/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  
  const data = await response.json();
  if (data.code === 200) {
    console.log('注册成功:', data.data);
  } else {
    console.error('注册失败:', data.msg);
  }
};
```

### Example: Login

```javascript
const login = async (username, password) => {
  const response = await fetch('http://localhost:8000/api/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  
  const data = await response.json();
  if (data.code === 200) {
    // Store token in localStorage
    localStorage.setItem('token', data.data.token);
    localStorage.setItem('user', JSON.stringify(data.data.user));
    console.log('登录成功');
  } else {
    console.error('登录失败:', data.msg);
  }
};
```

### Example: Authenticated Request

```javascript
const getCurrentUser = async () => {
  const token = localStorage.getItem('token');
  
  const response = await fetch('http://localhost:8000/api/me', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  const data = await response.json();
  if (data.code === 200) {
    return data.data;
  } else {
    // Token expired or invalid - redirect to login
    localStorage.removeItem('token');
    window.location.href = '/login';
  }
};
```

## Implementation Details

### Password Hashing
- Uses `passlib[bcrypt]` for secure password hashing
- Bcrypt automatically generates and manages salts
- Password hash format: `$2b$12$...` (60 characters)

### JWT Middleware
- Located in `utils/dependencies.py`
- Two modes available:
  - `get_current_user`: Optional authentication (returns None if no token)
  - `require_current_user`: Required authentication (raises 401 if no token)

### Response Format
All API responses follow the standard format:
```json
{
  "code": 200,      // HTTP status code
  "data": {...},    // Response data (null on error)
  "msg": "string"   // Human-readable message
}
```

## Files Modified/Created

1. **api/auth.py** - Authentication endpoints with Chinese messages
2. **test_auth_api.py** - Comprehensive test script
3. **AUTH_API_README.md** - This documentation file

## Notes

- The User model already existed in `models.py` with all required fields
- JWT configuration already set in `config.py` with 24-hour expiration
- Password hashing utilities already implemented in `utils/auth.py`
- All response messages updated to Chinese as specified in requirements
