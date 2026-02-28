# End Pro - FastAPI Backend with JWT Authentication

A FastAPI-based backend application with JWT Bearer Token authentication.

## Features

- **JWT Authentication**: Secure authentication using JSON Web Tokens (JWT)
- **User Management**: User registration, login, and profile management
- **Ticket System**: Create and manage support tickets with user-specific ownership
- **RESTful API**: Consistent JSON response format

## Authentication

This application uses JWT-based Bearer Token authentication.

### Authentication Flow

1. **Register** a new user via `POST /api/register`
2. **Login** via `POST /api/login` to receive a JWT access token
3. **Use the token** in subsequent requests by including it in the `Authorization` header

### API Response Format

All API responses follow this consistent format:

```json
{
  "code": <int>,      // HTTP-like status code (200, 401, etc.)
  "data": <object>,   // Response data (varies by endpoint)
  "msg": <string>     // Human-readable message
}
```

### JWT Token Structure

The JWT token contains the following claims:

- `sub`: User ID (subject)
- `username`: Username
- `exp`: Expiration timestamp

### Configuration

JWT settings can be configured via environment variables:

- `JWT_SECRET_KEY`: Secret key for signing tokens (MUST be changed in production!)
- `JWT_ALGORITHM`: Algorithm for token signing (default: HS256)
- `JWT_EXPIRE_MINUTES`: Token expiration time in minutes (default: 30)

Copy `.env.example` to `.env` and update the values:

```bash
cp .env.example .env
# Edit .env with your configuration
```

## API Endpoints

### Authentication Endpoints

#### POST /api/register
Register a new user.

**Request:**
```json
{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:**
```json
{
  "code": 201,
  "data": {
    "id": 1,
    "username": "your_username"
  },
  "msg": "register success"
}
```

#### POST /api/login
Login and receive a JWT access token.

**Request:**
```json
{
  "username": "your_username",
  "password": "your_password"
}
```

**Response:**
```json
{
  "code": 200,
  "data": {
    "id": 1,
    "username": "your_username",
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  },
  "msg": "login success"
}
```

#### GET /api/self
Get current authenticated user information.

**Requires Authentication**: Yes

**Headers:**
```
Authorization: Bearer <your_jwt_token>
```

**Response:**
```json
{
  "code": 200,
  "data": {
    "id": 1,
    "username": "your_username"
  },
  "msg": "whoami"
}
```

#### POST /api/logout
Logout (client-side token disposal).

**Note**: Logout is stateless with JWT. The client should simply discard the token.

**Response:**
```json
{
  "code": 200,
  "data": {},
  "msg": "logout success"
}
```

### Protected Endpoints

#### POST /api/tickets
Create a new ticket (requires authentication).

**Requires Authentication**: Yes

**Headers:**
```
Authorization: Bearer <your_jwt_token>
```

**Request:**
```json
{
  "title": "Issue with login",
  "description": "Cannot login to my account",
  "category": "technical",
  "priority": "high"
}
```

**Response:**
```json
{
  "code": 201,
  "data": {
    "id": 1,
    "title": "Issue with login",
    "description": "Cannot login to my account",
    "category": "technical",
    "priority": "high",
    "status": "open",
    "created_at": "2026-01-30",
    "user": "your_username"
  },
  "msg": "ticket created successfully"
}
```

### Public Endpoints

The following endpoints do NOT require authentication:

- `GET /api/tickets` - List all tickets (public view)
- `GET /api/tickets/{id}` - Get ticket details
- Other content endpoints (posts, categories, tags, etc.)

## Using the API with cURL

### Register a new user:
```bash
curl -X POST http://localhost:8000/api/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass"}'
```

### Login and get token:
```bash
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass"}'
```

### Use token for authenticated requests:
```bash
# Save token from login response
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Get current user info
curl -X GET http://localhost:8000/api/self \
  -H "Authorization: Bearer $TOKEN"

# Create a ticket
curl -X POST http://localhost:8000/api/tickets \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test ticket", "priority": "high"}'
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your settings
```

3. Run the application:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## Security Notes

- **IMPORTANT**: Change `JWT_SECRET_KEY` in production to a strong random value
- Tokens are signed with HS256 algorithm by default
- Tokens expire after 30 minutes by default (configurable)
- Always use HTTPS in production to protect tokens in transit
- Store tokens securely on the client side (e.g., httpOnly cookies or secure storage)

## Dependencies

- FastAPI: Modern web framework
- SQLAlchemy: ORM for database operations
- PyJWT: JWT token encoding/decoding
- asyncmy: Async MySQL driver
- Uvicorn: ASGI server

## License

[Your License Here]
