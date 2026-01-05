# Quick Start Guide

Get your Blog API up and running in 5 minutes!

## Prerequisites

- Python 3.8+
- MySQL running on localhost

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Configure Database

Edit `config.py` and update the database URL:

```python
DATABASE_URL = "mysql+asyncmy://your_user:your_password@localhost/your_database"
```

## Step 3: Start the Server

```bash
uvicorn main:app --reload
```

The server will automatically create all database tables on startup.

## Step 4: (Optional) Seed Test Data

In a new terminal, run:

```bash
python seed_data.py
```

This creates:
- An admin user (username: `admin`, password: `admin123`)
- Sample categories, tags, and posts
- Site info and menu items

## Step 5: Explore the API

Open your browser and visit:

**API Documentation:** http://localhost:8000/docs

## Quick API Test

### 1. Register a User

```bash
curl -X POST "http://localhost:8000/api/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "password123"}'
```

Response:
```json
{
  "code": 201,
  "data": {
    "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "user": {"id": 1, "username": "testuser"}
  },
  "msg": "register success"
}
```

Save the token for authenticated requests!

### 2. Get All Posts

```bash
curl "http://localhost:8000/api/posts?page=1&size=10"
```

### 3. Create a Post (requires authentication)

```bash
curl -X POST "http://localhost:8000/api/posts" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "title": "My First Post",
    "content": "This is the content of my first post",
    "summary": "A brief summary",
    "category_id": 1,
    "tag_ids": [1, 2]
  }'
```

### 4. Get All Categories

```bash
curl "http://localhost:8000/api/categories"
```

### 5. Create a Comment

```bash
curl -X POST "http://localhost:8000/api/comments" \
  -H "Content-Type: application/json" \
  -d '{
    "post_id": 1,
    "author_name": "John Doe",
    "author_email": "john@example.com",
    "content": "Great post!"
  }'
```

### 6. Get Comments for a Post

```bash
curl "http://localhost:8000/api/posts/1/comments"
```

## Available Endpoints

### Authentication
- `POST /api/register` - Register new user
- `POST /api/login` - Login and get JWT token
- `GET /api/me` - Get current user info

### Posts
- `GET /api/posts` - List posts (with filters)
- `GET /api/posts/{id}` - Get single post
- `POST /api/posts` - Create post 🔒
- `PUT /api/posts/{id}` - Update post 🔒
- `DELETE /api/posts/{id}` - Delete post 🔒

### Categories
- `GET /api/categories` - List categories
- `POST /api/categories` - Create category 🔒
- `PUT /api/categories/{id}` - Update category 🔒
- `DELETE /api/categories/{id}` - Delete category 🔒

### Tags
- `GET /api/tags` - List tags
- `POST /api/tags` - Create tag 🔒
- `PUT /api/tags/{id}` - Update tag 🔒
- `DELETE /api/tags/{id}` - Delete tag 🔒

### Comments
- `GET /api/posts/{post_id}/comments` - Get post comments
- `POST /api/comments` - Create comment
- `DELETE /api/comments/{id}` - Delete comment 🔒

### Other
- `GET /api/archive` - Get archive by year
- `GET /api/menus` - Get menu items
- `GET /api/siteinfo` - Get site information
- `POST /api/posts/{id}/view` - Increment view count
- `POST /api/posts/{id}/like` - Increment like count

🔒 = Requires authentication (JWT token)

## Response Format

All endpoints return JSON in this format:

```json
{
  "code": 200,
  "data": { ... },
  "msg": "success"
}
```

## Common HTTP Status Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `409` - Conflict (e.g., duplicate username)
- `500` - Server Error

## Frontend Integration

### Store Token in localStorage

```javascript
// After login/register
const response = await fetch('/api/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username, password })
});

const data = await response.json();
if (data.code === 200) {
  localStorage.setItem('token', data.data.token);
}
```

### Make Authenticated Requests

```javascript
const token = localStorage.getItem('token');

const response = await fetch('/api/posts', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify(postData)
});
```

## Need Help?

- Check the full **README.md** for detailed documentation
- See **DEPLOYMENT.md** for production deployment guide
- Run `python validate.py` to verify your setup
- Visit http://localhost:8000/docs for interactive API documentation

## Troubleshooting

**Can't connect to database?**
- Verify MySQL is running: `mysql -u root -p`
- Check DATABASE_URL in config.py
- Ensure database exists: `CREATE DATABASE your_database;`

**Import errors?**
- Install dependencies: `pip install -r requirements.txt`
- Check Python version: `python --version` (need 3.8+)

**Port 8000 already in use?**
- Change port: `uvicorn main:app --port 8001`
- Or kill the process: `lsof -ti:8000 | xargs kill -9`

Happy coding! 🚀
