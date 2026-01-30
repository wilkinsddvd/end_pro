# JWT Authentication - Quick Start Guide

## Overview
This document provides quick examples for using the JWT-based authentication system.

## Environment Setup

1. Copy the example environment file:
```bash
cp .env.example .env
```

2. **IMPORTANT**: In production, set a strong secret key:
```bash
# Generate a secure random key
python3 -c "import secrets; print(secrets.token_hex(32))"

# Set it in .env
JWT_SECRET_KEY=<your-generated-key>
```

## API Usage Examples

### 1. Register a New User

```bash
curl -X POST http://localhost:8000/api/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "password": "secure123"
  }'
```

Response:
```json
{
  "code": 201,
  "data": {
    "id": 1,
    "username": "alice"
  },
  "msg": "register success"
}
```

### 2. Login and Receive JWT Token

```bash
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "alice",
    "password": "secure123"
  }'
```

Response:
```json
{
  "code": 200,
  "data": {
    "id": 1,
    "username": "alice",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOjEsInVzZXJuYW1lIjoiYWxpY2UiLCJleHAiOjE3Njk3ODA3MDB9.abc123..."
  },
  "msg": "login success"
}
```

**Save the token** from `data.token` for use in authenticated requests.

### 3. Get Current User Info (Protected)

```bash
# Set your token as a variable
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl -X GET http://localhost:8000/api/self \
  -H "Authorization: Bearer $TOKEN"
```

Response:
```json
{
  "code": 200,
  "data": {
    "id": 1,
    "username": "alice"
  },
  "msg": "whoami"
}
```

### 4. Create a Ticket (Protected)

```bash
curl -X POST http://localhost:8000/api/tickets \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Unable to login",
    "description": "Getting 401 error when trying to access dashboard",
    "priority": "high",
    "category": "technical"
  }'
```

Response:
```json
{
  "code": 201,
  "data": {
    "id": 1,
    "title": "Unable to login",
    "description": "Getting 401 error when trying to access dashboard",
    "category": "technical",
    "priority": "high",
    "status": "open",
    "created_at": "2026-01-30",
    "user": "alice"
  },
  "msg": "ticket created successfully"
}
```

Note: The ticket is automatically associated with the authenticated user (`alice`).

### 5. Logout (Stateless)

```bash
curl -X POST http://localhost:8000/api/logout
```

Response:
```json
{
  "code": 200,
  "data": {},
  "msg": "logout success"
}
```

**Note**: With JWT, logout is handled client-side by discarding the token. The server endpoint is provided for API consistency.

## Error Responses

### Missing Authorization Header
```json
{
  "code": 401,
  "data": {},
  "msg": "authorization header missing"
}
```

### Invalid Token Format
```json
{
  "code": 401,
  "data": {},
  "msg": "invalid authorization header format"
}
```

### Expired or Invalid Token
```json
{
  "code": 401,
  "data": {},
  "msg": "invalid or expired token"
}
```

### Invalid Credentials (Login)
```json
{
  "code": 401,
  "data": {},
  "msg": "invalid credentials"
}
```

## Token Details

### Token Structure
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9    ← Header
.
eyJzdWIiOjEsInVzZXJuYW1lIjoiYWxpY2UiLCJleHAiOjE3Njk3ODA3MDB9    ← Payload
.
abc123...    ← Signature
```

### Token Payload (decoded)
```json
{
  "sub": 1,                    // User ID
  "username": "alice",         // Username
  "exp": 1769780700           // Expiration timestamp (Unix)
}
```

### Token Expiration
- Default: 30 minutes
- Configurable via `JWT_EXPIRE_MINUTES` environment variable
- After expiration, client must login again to get a new token

## JavaScript/Frontend Example

```javascript
// Login and store token
async function login(username, password) {
  const response = await fetch('http://localhost:8000/api/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  });
  
  const data = await response.json();
  
  if (data.code === 200) {
    // Store token (consider using httpOnly cookies in production)
    localStorage.setItem('jwt_token', data.data.token);
    return data.data;
  }
  throw new Error(data.msg);
}

// Use token for authenticated requests
async function createTicket(ticketData) {
  const token = localStorage.getItem('jwt_token');
  
  const response = await fetch('http://localhost:8000/api/tickets', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify(ticketData)
  });
  
  const data = await response.json();
  
  if (data.code === 401) {
    // Token expired or invalid - redirect to login
    window.location.href = '/login';
  }
  
  return data;
}

// Logout (client-side)
function logout() {
  localStorage.removeItem('jwt_token');
  window.location.href = '/login';
}
```

## Security Best Practices

1. **Always use HTTPS in production** to protect tokens in transit
2. **Set a strong JWT_SECRET_KEY** - use a cryptographically random value
3. **Store tokens securely** - prefer httpOnly cookies over localStorage
4. **Implement token refresh** for better UX (optional enhancement)
5. **Validate token on every request** - done automatically by `get_current_user`
6. **Monitor for suspicious activity** - log failed authentication attempts

## Troubleshooting

### "Using default JWT_SECRET_KEY" warning
- **Solution**: Set `JWT_SECRET_KEY` environment variable in `.env` or system environment

### Token expired too quickly
- **Solution**: Increase `JWT_EXPIRE_MINUTES` in `.env` (e.g., `JWT_EXPIRE_MINUTES=60`)

### "authorization header missing" error
- **Solution**: Include `Authorization: Bearer <token>` header in your request

### Cannot decode token
- **Solution**: Verify you're using the exact token from the login response without modification

## Public vs Protected Endpoints

### Public (No Authentication Required)
- `POST /api/register` - User registration
- `POST /api/login` - User login
- `POST /api/logout` - Logout (stateless)
- `GET /api/tickets` - List tickets
- `GET /api/tickets/{id}` - Get ticket details
- Most content endpoints (posts, categories, tags, etc.)

### Protected (Authentication Required)
- `GET /api/self` - Get current user
- `POST /api/tickets` - Create ticket
- Any future admin-only endpoints

## Next Steps

1. Review the full API documentation in `README.md`
2. Set up proper environment variables for production
3. Implement token refresh if needed for your use case
4. Consider adding role-based access control (RBAC) for admin features
5. Set up monitoring and logging for security events
