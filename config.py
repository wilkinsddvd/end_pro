"""
Configuration settings for the Blog API
Update these values according to your environment

IMPORTANT: For production, use environment variables instead of hardcoding credentials.
Example:
    import os
    DATABASE_URL = os.getenv("DATABASE_URL", "mysql+asyncmy://...")
    SECRET_KEY = os.getenv("SECRET_KEY", "fallback-key")
"""

import os

# Database Configuration
# SECURITY: Use environment variables in production
DATABASE_URL = os.getenv("DATABASE_URL", "mysql+asyncmy://root:123456@localhost/db_on_work")

# JWT Configuration
# SECURITY: Generate a secure random key and use environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production-to-a-long-random-string")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Server Configuration
API_TITLE = "Blog API"
API_DESCRIPTION = "RESTful API for blog system with JWT authentication"
API_VERSION = "1.0.0"

# CORS Configuration (if needed for frontend)
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:8080",
]
