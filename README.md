# Blog Backend API

A comprehensive FastAPI + MySQL async backend for a blog system with JWT authentication.

## Features

- **RESTful API Design**: All endpoints return a standard `{code, data, msg}` format
- **JWT Authentication**: Short-term token-based authentication compatible with localStorage
- **Async MySQL**: Fully asynchronous database operations using SQLAlchemy
- **Auto Table Creation**: Database tables are created automatically on startup
- **Comprehensive Modules**:
  - Posts (CRUD with tags and categories)
  - Categories (CRUD)
  - Tags (CRUD)
  - Comments (Multi-level hierarchical comments)
  - Archive (Year-based post grouping)
  - Menus
  - Site Info
  - User Authentication (Register/Login)

## Project Structure

```
.
├── api/                    # API route handlers
│   ├── auth.py            # Authentication endpoints
│   ├── posts.py           # Post CRUD operations
│   ├── categories.py      # Category CRUD operations
│   ├── tags.py            # Tag CRUD operations
│   ├── comments.py        # Comment operations with hierarchy
│   ├── archive.py         # Archive listings
│   ├── menus.py           # Menu management
│   ├── siteinfo.py        # Site information
│   └── interaction.py     # Post views and likes
├── utils/                  # Utility modules
│   ├── auth.py            # JWT token utilities
│   └── dependencies.py    # FastAPI dependencies
├── models.py              # SQLAlchemy database models
├── schemas.py             # Pydantic request/response schemas
├── db.py                  # Database configuration
├── main.py                # FastAPI application entry point
└── requirements.txt       # Python dependencies
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure database in `db.py`:
```python
DATABASE_URL = "mysql+asyncmy://user:password@host/database"
```

3. Start the server:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### Authentication
- `POST /api/register` - Register a new user
- `POST /api/login` - Login and receive JWT token
- `POST /api/logout` - Logout (client discards token)
- `GET /api/me` - Get current user info

### Posts
- `GET /api/posts` - List posts with pagination and filtering
- `GET /api/posts/{id}` - Get a single post
- `POST /api/posts` - Create a post (requires auth)
- `PUT /api/posts/{id}` - Update a post (requires auth)
- `DELETE /api/posts/{id}` - Delete a post (requires auth)

### Categories
- `GET /api/categories` - List all categories with post counts
- `POST /api/categories` - Create a category (requires auth)
- `PUT /api/categories/{id}` - Update a category (requires auth)
- `DELETE /api/categories/{id}` - Delete a category (requires auth)

### Tags
- `GET /api/tags` - List all tags with post counts
- `POST /api/tags` - Create a tag (requires auth)
- `PUT /api/tags/{id}` - Update a tag (requires auth)
- `DELETE /api/tags/{id}` - Delete a tag (requires auth)

### Comments
- `GET /api/posts/{post_id}/comments` - Get all comments for a post (hierarchical)
- `POST /api/comments` - Create a comment
- `DELETE /api/comments/{id}` - Delete a comment (requires auth)

### Other
- `GET /api/archive` - Get posts grouped by year
- `GET /api/menus` - Get menu items
- `GET /api/siteinfo` - Get site information
- `POST /api/posts/{id}/view` - Increment post view count
- `POST /api/posts/{id}/like` - Increment post like count

## Response Format

All endpoints return a consistent JSON format:

```json
{
  "code": 200,
  "data": { ... },
  "msg": "success"
}
```

## Authentication

Protected endpoints require a JWT token in the Authorization header:

```
Authorization: Bearer <token>
```

The token is returned upon successful login/registration and should be stored in localStorage on the frontend.

## Database Models

### User
- id, username, password_hash, created_at

### Post
- id, title, summary, content, category_id, author_id, date, views, likes
- Relationships: category, tags (many-to-many), author

### Category
- id, name
- Relationship: posts

### Tag
- id, name
- Relationship: posts (many-to-many)

### Comment
- id, post_id, parent_id, author_name, author_email, content, created_at, user_id
- Relationships: post, parent, replies (self-referential)

### Menu
- id, title, path, url

### SiteInfo
- id, title, description, icp, footer

## Security Features

- Password hashing using bcrypt
- JWT token expiration (24 hours)
- Authentication required for write operations
- Authorization checks for user-owned resources
- Comprehensive exception handling
- Input validation using Pydantic schemas

## Multi-level Comments

Comments support hierarchical threading:
- Top-level comments have `parent_id = null`
- Replies have `parent_id` set to the parent comment's ID
- The GET endpoint returns a nested tree structure with all replies

## Development

The application uses:
- FastAPI for the web framework
- SQLAlchemy 2.0 with async support
- asyncmy for async MySQL driver
- Pydantic v2 for data validation
- python-jose for JWT handling
- passlib for password hashing

## License

MIT License
