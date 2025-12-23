# Incident Management System - Deployment & Integration Guide

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Fresh Installation](#fresh-installation)
3. [Integration into Existing Django Project](#integration-into-existing-django-project)
4. [Database Configuration](#database-configuration)
5. [Email Configuration](#email-configuration)
6. [Environment Variables](#environment-variables)
7. [Deployment to Production](#deployment-to-production)
8. [API Endpoints Reference](#api-endpoints-reference)
9. [Testing the Application](#testing-the-application)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software
- **Python**: 3.8 or higher (tested with 3.14.0)
- **pip**: Latest version
- **Database**: SQLite (default), PostgreSQL, or Oracle
- **Virtual Environment**: `venv` or `virtualenv`

### Required Python Packages
```txt
Django>=6.0
djangorestframework>=3.15.0
djangorestframework-simplejwt>=5.3.0
psycopg2-binary>=2.9.9  # For PostgreSQL
cx_Oracle>=8.3.0         # For Oracle
python-decouple>=3.8     # For environment variables (recommended)
gunicorn>=21.2.0         # For production deployment
```

---

## Fresh Installation

### Step 1: Clone/Copy the Project
```bash
# Copy the entire Management folder to your desired location
cp -r Management /path/to/your/project/
cd /path/to/your/project/Management
```

### Step 2: Create Virtual Environment
```bash
# Windows
python -m venv env
env\Scripts\activate

# Linux/Mac
python3 -m venv env
source env/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure Settings
Edit `Incident/settings.py` and update:
```python
# SECURITY WARNING: Update this in production!
SECRET_KEY = 'your-secret-key-here'

# SECURITY WARNING: Don't run with debug turned on in production!
DEBUG = False  # Set to False in production

# Update with your domain
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com', 'localhost']

# Update frontend URL
FRONTEND_URL = 'https://yourdomain.com'
```

### Step 5: Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 6: Create Superuser
```bash
python manage.py createsuperuser
```

### Step 7: Create User Profiles
```bash
python manage.py shell
```
```python
from django.contrib.auth.models import User
from core.models import UserProfile

# For superuser
admin = User.objects.get(username='your_admin_username')
UserProfile.objects.create(
    user=admin,
    role='ADMIN',
    phone_number='+1234567890',
    whatsapp_number='+1234567890',
    department='IT'
)

# Create additional users as needed
```

### Step 8: Run Development Server
```bash
python manage.py runserver
```

---

## Integration into Existing Django Project

### Option 1: Copy Core App (Recommended)

1. **Copy the `core` app** into your existing Django project:
```bash
cp -r Management/core /path/to/your/existing/project/
```

2. **Update your project's `settings.py`:**
```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    
    # Your existing apps
    'your_app_1',
    'your_app_2',
    
    # Incident Management
    'core',  # Add this
]

# Add REST Framework configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# Add JWT configuration
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=2),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=2),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
}

# Email configuration (see Email Configuration section)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
DEFAULT_FROM_EMAIL = 'your-email@gmail.com'

# Frontend URL for email links
FRONTEND_URL = 'https://yourdomain.com'
```

3. **Update your project's `urls.py`:**
```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Your existing URLs
    path('your-app/', include('your_app_1.urls')),
    
    # Incident Management URLs
    path('api/', include('core.urls')),  # Add this
]
```

4. **Run migrations:**
```bash
python manage.py makemigrations core
python manage.py migrate
```

5. **Register admin** (if not auto-registered):
```python
# In your project's admin.py or core/admin.py
from django.contrib import admin
from core.admin import *  # This imports all admin configurations
```

### Option 2: Use as Separate Microservice

If you prefer to keep it as a separate service:

1. **Run the Incident Management system on a different port:**
```bash
python manage.py runserver 8001
```

2. **Configure CORS** in your main project to communicate with it:
```bash
pip install django-cors-headers
```

```python
# settings.py
INSTALLED_APPS = [
    ...
    'corsheaders',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    ...
]

CORS_ALLOWED_ORIGINS = [
    'http://localhost:8000',  # Your main app
    'http://localhost:8001',  # Incident Management
]
```

3. **Call APIs** from your main application using requests:
```python
import requests

# Get JWT token
response = requests.post('http://localhost:8001/api/auth/login/', {
    'username': 'admin',
    'password': 'password'
})
token = response.json()['access']

# Create ticket
headers = {'Authorization': f'Bearer {token}'}
response = requests.post(
    'http://localhost:8001/api/tickets/',
    headers=headers,
    json={
        'title': 'New Issue',
        'description': 'Description here',
        'priority': 'HIGH',
        'category': 'BUG',
        'project_name': 'My Project'
    }
)
```

---

## Database Configuration

### SQLite (Default - Development Only)
```python
# Incident/settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### PostgreSQL (Recommended for Production)

1. **Install PostgreSQL driver:**
```bash
pip install psycopg2-binary
```

2. **Create PostgreSQL database:**
```bash
# Login to PostgreSQL
psql -U postgres

# Create database and user
CREATE DATABASE incident_management;
CREATE USER incident_user WITH PASSWORD 'strong_password_here';
ALTER ROLE incident_user SET client_encoding TO 'utf8';
ALTER ROLE incident_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE incident_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE incident_management TO incident_user;
\q
```

3. **Update settings.py:**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'incident_management',
        'USER': 'incident_user',
        'PASSWORD': 'strong_password_here',
        'HOST': 'localhost',  # Or your DB server IP
        'PORT': '5432',       # Default PostgreSQL port
    }
}
```

4. **Run migrations:**
```bash
python manage.py migrate
```

### Oracle Database

1. **Install Oracle Instant Client:**
   - Download from [Oracle Website](https://www.oracle.com/database/technologies/instant-client/downloads.html)
   - Extract and set environment variables

2. **Install cx_Oracle:**
```bash
pip install cx_Oracle
```

3. **Update settings.py:**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.oracle',
        'NAME': 'your_oracle_service_name',  # Or SID
        'USER': 'incident_user',
        'PASSWORD': 'strong_password_here',
        'HOST': 'oracle-server-ip',
        'PORT': '1521',  # Default Oracle port
    }
}
```

4. **Create Oracle user and grant permissions:**
```sql
-- Connect as SYSDBA
CREATE USER incident_user IDENTIFIED BY strong_password_here;
GRANT CONNECT, RESOURCE TO incident_user;
GRANT CREATE SESSION TO incident_user;
GRANT CREATE TABLE TO incident_user;
GRANT CREATE SEQUENCE TO incident_user;
ALTER USER incident_user QUOTA UNLIMITED ON USERS;
```

5. **Run migrations:**
```bash
python manage.py migrate
```

### MySQL/MariaDB (Alternative)

1. **Install MySQL driver:**
```bash
pip install mysqlclient
```

2. **Create database:**
```sql
CREATE DATABASE incident_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'incident_user'@'localhost' IDENTIFIED BY 'strong_password_here';
GRANT ALL PRIVILEGES ON incident_management.* TO 'incident_user'@'localhost';
FLUSH PRIVILEGES;
```

3. **Update settings.py:**
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'incident_management',
        'USER': 'incident_user',
        'PASSWORD': 'strong_password_here',
        'HOST': 'localhost',
        'PORT': '3306',
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'"
        }
    }
}
```

---

## Email Configuration

### Gmail SMTP (Development & Production)

1. **Enable 2-Step Verification** on your Gmail account
2. **Generate App Password:**
   - Go to Google Account → Security → 2-Step Verification
   - Scroll to "App passwords"
   - Generate password for "Mail" application

3. **Update settings.py:**
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-16-digit-app-password'
DEFAULT_FROM_EMAIL = 'Incident Management <your-email@gmail.com>'
```

### Other Email Providers

**SendGrid:**
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'apikey'
EMAIL_HOST_PASSWORD = 'your-sendgrid-api-key'
```

**AWS SES:**
```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'email-smtp.us-east-1.amazonaws.com'  # Your region
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-smtp-username'
EMAIL_HOST_PASSWORD = 'your-smtp-password'
```

### Console Backend (Development Only)
```python
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

---

## Environment Variables

### Using python-decouple (Recommended)

1. **Install:**
```bash
pip install python-decouple
```

2. **Create `.env` file** in project root:
```env
# Security
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=incident_management
DB_USER=incident_user
DB_PASSWORD=strong_password_here
DB_HOST=localhost
DB_PORT=5432

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com

# Application
FRONTEND_URL=https://yourdomain.com
```

3. **Update settings.py:**
```python
from decouple import config, Csv

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', cast=Csv())

DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE'),
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
    }
}

EMAIL_HOST = config('EMAIL_HOST')
EMAIL_PORT = config('EMAIL_PORT', cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL')

FRONTEND_URL = config('FRONTEND_URL')
```

4. **Add `.env` to `.gitignore`:**
```
.env
```

---

## Deployment to Production

### Step 1: Prepare for Production

**Update settings.py:**
```python
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com', 'www.yourdomain.com']

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Static files
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATIC_URL = '/static/'
```

**Collect static files:**
```bash
python manage.py collectstatic --noinput
```

### Step 2: Using Gunicorn (Linux/Mac)

1. **Install Gunicorn:**
```bash
pip install gunicorn
```

2. **Test Gunicorn:**
```bash
gunicorn Incident.wsgi:application --bind 0.0.0.0:8000
```

3. **Create systemd service** (`/etc/systemd/system/incident.service`):
```ini
[Unit]
Description=Incident Management Django App
After=network.target

[Service]
User=your-user
Group=www-data
WorkingDirectory=/path/to/Management
Environment="PATH=/path/to/Management/env/bin"
ExecStart=/path/to/Management/env/bin/gunicorn \
          --workers 3 \
          --bind unix:/path/to/Management/incident.sock \
          Incident.wsgi:application

[Install]
WantedBy=multi-user.target
```

4. **Start service:**
```bash
sudo systemctl start incident
sudo systemctl enable incident
sudo systemctl status incident
```

### Step 3: Nginx Configuration

**Create Nginx config** (`/etc/nginx/sites-available/incident`):
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias /path/to/Management/staticfiles/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/path/to/Management/incident.sock;
    }
}
```

**Enable site:**
```bash
sudo ln -s /etc/nginx/sites-available/incident /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 4: SSL with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

### Step 5: Using Docker (Alternative)

**Create Dockerfile:**
```dockerfile
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/

RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "Incident.wsgi:application"]
```

**Create docker-compose.yml:**
```yaml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: incident_management
      POSTGRES_USER: incident_user
      POSTGRES_PASSWORD: strong_password_here
    volumes:
      - postgres_data:/var/lib/postgresql/data

  web:
    build: .
    command: gunicorn Incident.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - .:/app
      - static_volume:/app/staticfiles
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db

  nginx:
    image: nginx:alpine
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - static_volume:/app/staticfiles
    ports:
      - "80:80"
    depends_on:
      - web

volumes:
  postgres_data:
  static_volume:
```

**Deploy:**
```bash
docker-compose up -d
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

---

## API Endpoints Reference

### Authentication
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/api/auth/login/` | Login and get JWT tokens | No |
| POST | `/api/auth/token/refresh/` | Refresh access token | No |
| GET | `/api/auth/me/` | Get current user details | Yes |
| PUT/PATCH | `/api/auth/me/` | Update user profile | Yes |

### Tickets
| Method | Endpoint | Description | Role |
|--------|----------|-------------|------|
| GET | `/api/tickets/` | List tickets | All |
| POST | `/api/tickets/` | Create ticket | CLIENT |
| GET | `/api/tickets/{id}/` | Get ticket details | All |
| PUT/PATCH | `/api/tickets/{id}/` | Update ticket | ADMIN |
| DELETE | `/api/tickets/{id}/` | Delete ticket | ADMIN |
| POST | `/api/tickets/{id}/open_ticket/` | Open ticket | ADMIN |
| POST | `/api/tickets/{id}/assign/` | Assign developer | ADMIN |
| POST | `/api/tickets/{id}/start_work/` | Start working | SUPPORT |
| POST | `/api/tickets/{id}/finish_work/` | Finish work | SUPPORT |
| POST | `/api/tickets/{id}/approve/` | Approve ticket | CLIENT |
| POST | `/api/tickets/{id}/reject/` | Reject ticket | CLIENT |
| GET | `/api/tickets/developers/` | List developers | ADMIN |

### User Profiles
| Method | Endpoint | Description | Role |
|--------|----------|-------------|------|
| GET | `/api/profiles/` | List user profiles | ADMIN |
| GET | `/api/profiles/{id}/` | Get profile details | All |
| PUT/PATCH | `/api/profiles/{id}/` | Update profile | ADMIN |

### Notifications
| Method | Endpoint | Description | Role |
|--------|----------|-------------|------|
| GET | `/api/notifications/` | List notifications | All |
| GET | `/api/notifications/{id}/` | Get notification | All |
| POST | `/api/notifications/{id}/mark_read/` | Mark as read | All |

---

## Testing the Application

### 1. Using Postman

**Import Collection:**
- Create requests for all endpoints
- Use environment variables for base URL and tokens

**Example Test Flow:**

1. **Login as Admin:**
```json
POST http://localhost:8000/api/auth/login/
{
    "username": "admin",
    "password": "admin123"
}
```

2. **Create Ticket (as Client):**
```json
POST http://localhost:8000/api/tickets/
Authorization: Bearer <client_token>
{
    "title": "Application Crash",
    "description": "App crashes when clicking submit",
    "priority": "HIGH",
    "category": "BUG",
    "project_name": "Web Portal"
}
```

3. **Open Ticket (as Admin):**
```json
POST http://localhost:8000/api/tickets/1/open_ticket/
Authorization: Bearer <admin_token>
{
    "admin_notes": "Reviewed and approved"
}
```

4. **Assign Developer (as Admin):**
```json
POST http://localhost:8000/api/tickets/1/assign/
Authorization: Bearer <admin_token>
{
    "assigned_to": 4,
    "resolution_due_at": "2025-12-25T10:00:00Z",
    "estimated_resolution_time": "2025-12-25T09:00:00Z"
}
```

### 2. Using Django Admin Panel

1. Navigate to: `http://localhost:8000/admin/`
2. Login with superuser credentials
3. Create users with different roles
4. Create and manage tickets
5. View notification logs

### 3. Automated Testing

**Create tests** (`core/tests.py`):
```python
from django.test import TestCase
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from core.models import Ticket, UserProfile

class TicketAPITestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create admin user
        self.admin = User.objects.create_user(
            username='admin',
            password='admin123',
            email='admin@test.com'
        )
        UserProfile.objects.create(user=self.admin, role='ADMIN')
        
        # Create client user
        self.client_user = User.objects.create_user(
            username='client',
            password='client123',
            email='client@test.com'
        )
        UserProfile.objects.create(user=self.client_user, role='CLIENT')
    
    def test_create_ticket(self):
        # Login as client
        response = self.client.post('/api/auth/login/', {
            'username': 'client',
            'password': 'client123'
        })
        token = response.json()['access']
        
        # Create ticket
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.post('/api/tickets/', {
            'title': 'Test Ticket',
            'description': 'Test Description',
            'priority': 'HIGH',
            'category': 'BUG',
            'project_name': 'Test Project'
        })
        
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Ticket.objects.count(), 1)
```

**Run tests:**
```bash
python manage.py test core
```

---

## Troubleshooting

### Common Issues

**1. Database Connection Errors:**
```bash
# Check database is running
# PostgreSQL
sudo systemctl status postgresql

# Check connection
psql -U incident_user -d incident_management -h localhost
```

**2. Email Not Sending:**
- Verify EMAIL_BACKEND setting
- Check EMAIL_HOST_USER and EMAIL_HOST_PASSWORD
- Ensure 2-Step Verification and App Password (Gmail)
- Check firewall allows port 587

**3. Static Files Not Loading:**
```bash
python manage.py collectstatic --clear
python manage.py collectstatic --noinput
```

**4. JWT Token Expired:**
- Tokens expire after 2 hours
- Use refresh token to get new access token
- Adjust `ACCESS_TOKEN_LIFETIME` in settings if needed

**5. SLA Times Not Calculating:**
- Ensure signals are enabled
- Check ticket priority is set correctly
- Verify timezone settings: `USE_TZ = True`

**6. CORS Errors (Microservice Setup):**
```bash
pip install django-cors-headers
```
Add to `INSTALLED_APPS` and `MIDDLEWARE`, configure `CORS_ALLOWED_ORIGINS`

### Debug Mode

**Enable detailed error messages:**
```python
# settings.py (ONLY FOR DEVELOPMENT)
DEBUG = True
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'DEBUG',
    },
}
```

---

## Security Checklist

Before going to production:

- [ ] Set `DEBUG = False`
- [ ] Change `SECRET_KEY` to a strong, unique value
- [ ] Configure `ALLOWED_HOSTS` properly
- [ ] Use environment variables for sensitive data
- [ ] Enable HTTPS (`SECURE_SSL_REDIRECT = True`)
- [ ] Use strong database passwords
- [ ] Configure CSRF and CORS properly
- [ ] Regular backups of database
- [ ] Keep Django and dependencies updated
- [ ] Use secure cookies (`SESSION_COOKIE_SECURE = True`)
- [ ] Enable security headers
- [ ] Review user permissions regularly

---

## Support

For issues or questions:
- Check Django documentation: https://docs.djangoproject.com/
- Check DRF documentation: https://www.django-rest-framework.org/
- Review application logs
- Check email notification logs in admin panel

---

## License

[Your License Here]

---

## Version History

- **v1.0** (December 2025)
  - Initial release
  - SLA management
  - Email notifications
  - Role-based access control
  - Complete ticket workflow
