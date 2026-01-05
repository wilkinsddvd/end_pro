# Deployment Guide

This guide will help you deploy the Blog Backend API in a production environment.

## Prerequisites

- Python 3.8 or higher
- MySQL 5.7 or higher
- pip (Python package manager)

## Step 1: Clone the Repository

```bash
git clone <repository-url>
cd end_pro
```

## Step 2: Set Up Virtual Environment (Recommended)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

## Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 4: Configure Database

1. Create a MySQL database:

```sql
CREATE DATABASE db_on_work CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'bloguser'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON db_on_work.* TO 'bloguser'@'localhost';
FLUSH PRIVILEGES;
```

2. Update `config.py` with your database credentials:

```python
DATABASE_URL = "mysql+asyncmy://bloguser:your_password@localhost/db_on_work"
```

Or copy `.env.example` to `.env` and update it (if using environment variables).

## Step 5: Configure JWT Secret

**IMPORTANT**: Change the `SECRET_KEY` in `config.py` to a secure random string:

```python
SECRET_KEY = "generate-a-long-random-string-here"
```

You can generate a secure key using:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Step 6: Initialize Database

The application will automatically create all tables on startup. You can verify this by running:

```bash
uvicorn main:app --reload
```

The tables will be created when the application starts.

## Step 7: Create Initial Admin User

You can create an admin user by calling the register endpoint:

```bash
curl -X POST "http://localhost:8000/api/register" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "secure_password_123"}'
```

Save the returned token for authenticated requests.

## Step 8: Run the Application

### Development Mode

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

For production, use a production-grade ASGI server like Gunicorn with Uvicorn workers:

```bash
pip install gunicorn

gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## Step 9: Set Up Reverse Proxy (Optional)

For production deployments, it's recommended to use Nginx as a reverse proxy:

### Nginx Configuration Example

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Step 10: Set Up SSL (Recommended)

Use Let's Encrypt to get free SSL certificates:

```bash
sudo apt-get update
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## Step 11: Configure CORS

If your frontend is on a different domain, update the `ALLOWED_ORIGINS` in `config.py`:

```python
ALLOWED_ORIGINS = [
    "https://your-frontend-domain.com",
    "http://localhost:3000",  # For development
]
```

## Step 12: Set Up Process Manager (Production)

Use systemd to manage the application as a service:

Create `/etc/systemd/system/blog-api.service`:

```ini
[Unit]
Description=Blog API Service
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/end_pro
Environment="PATH=/path/to/end_pro/venv/bin"
ExecStart=/path/to/end_pro/venv/bin/gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker --bind 127.0.0.1:8000

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable blog-api
sudo systemctl start blog-api
sudo systemctl status blog-api
```

## Testing the Deployment

1. Check if the API is running:

```bash
curl http://localhost:8000/
```

Expected response:
```json
{
  "code": 200,
  "data": {"message": "Welcome to Blog API"},
  "msg": "success"
}
```

2. Access the API documentation:

Open your browser and go to:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Monitoring and Logs

### View Logs (systemd)

```bash
sudo journalctl -u blog-api -f
```

### Application Logs

Consider setting up proper logging in the application:

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/blog-api/app.log'),
        logging.StreamHandler()
    ]
)
```

## Backup Strategy

### Database Backup

Set up automated MySQL backups:

```bash
#!/bin/bash
# backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
mysqldump -u bloguser -p db_on_work > /backups/blog_$DATE.sql
# Keep only last 7 days of backups
find /backups -name "blog_*.sql" -mtime +7 -delete
```

Add to crontab:
```bash
0 2 * * * /path/to/backup.sh
```

## Security Checklist

- [ ] Changed default SECRET_KEY
- [ ] Using strong database password
- [ ] Enabled HTTPS/SSL
- [ ] Configured CORS properly
- [ ] Set up firewall rules
- [ ] Regular database backups
- [ ] Keep dependencies updated
- [ ] Monitor logs for suspicious activity

## Troubleshooting

### Database Connection Issues

```bash
# Test MySQL connection
mysql -u bloguser -p -h localhost db_on_work
```

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000
# Kill the process if needed
kill -9 <PID>
```

### Module Import Errors

```bash
# Verify all dependencies are installed
pip list
pip install -r requirements.txt --upgrade
```

## Support

For issues or questions, please open an issue on the GitHub repository.
