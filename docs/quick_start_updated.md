# Vaitikan E-Commerce Platform - Quick Start Guide

---

## 1. Prerequisites

### 1.1 Required Software

| Software | Version | Purpose | Download Link |
|----------|---------|---------|---------------|
| **Python** | 3.11+ | Backend runtime | [python.org](https://www.python.org/downloads/) |
| **pip** | Latest | Python package manager | Included with Python |
| **MySQL** | 8.4+ | Database server | [mysql.com](https://dev.mysql.com/downloads/installer/) |
| **Git** | Latest | Version control | [git-scm.com](https://git-scm.com/downloads/) |

### 1.2 Optional Software

| Software | Version | Purpose | Download Link |
|----------|---------|---------|---------------|
| **Redis** | 7.0+ | Cache backend (production) | [redis.io](https://redis.io/download/) |
| **VS Code** | Latest | IDE (recommended) | [code.visualstudio.com](https://code.visualstudio.com/) |
| **Postman** | Latest | API testing | [postman.com](https://www.postman.com/downloads/) |

### 1.3 Verify Installations

```bash
# Check Python version
python --version
# Expected: Python 3.11.x or higher

# Check pip
pip --version
# Expected: pip 23.x or higher

# Check MySQL
mysql --version
# Expected: mysql Ver 8.4.x

# Check Git
git --version
# Expected: git version 2.x
```

---

## 2. Installation

### 2.1 Clone the Repository

```bash
# Clone the project
git clone https://github.com/vaitikan/ecommerce-platform.git

# Navigate to project directory
cd ecommerce-platform
```

### 2.2 Create Virtual Environment

**Windows:**
```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.venv\Scripts\activate
```

**macOS/Linux:**
```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate
```

### 2.3 Install Dependencies

```bash
# Navigate to backend directory
cd backend

# Install Python packages
pip install -r requirements.txt
```

**Dependencies installed:**
- Django 5.2
- Django REST Framework
- djangorestframework-simplejwt
- mysqlclient
- django-cors-headers
- django-filter
- python-decouple
- dj-database-url
- reportlab (PDF generation)
- razorpay (Payment gateway)
- pillow (Image processing)
- bleach (XSS sanitization)
- cloudinary (Image storage)
- django-cloudinary-storage
- django-redis
- redis

---

## 3. Configuration

### 3.1 Database Setup

**Step 1: Create MySQL Database**

```sql
-- Login to MySQL
mysql -u root -p

-- Create database
CREATE DATABASE vaitikan_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create user (optional, for production)
CREATE USER 'vaitikan_user'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON vaitikan_db.* TO 'vaitikan_user'@'localhost';
FLUSH PRIVILEGES;

-- Exit MySQL
EXIT;
```

### 3.2 Environment Variables

**Step 1: Copy example environment file**

```bash
# From backend directory
cp .env.example .env
```

**Step 2: Edit `.env` file with your settings**

```env
# ============================
# CORE SETTINGS
# ============================
DEBUG=True
SECRET_KEY=your-super-secret-key-change-in-production

# Comma-separated list of allowed hosts
ALLOWED_HOSTS=localhost,127.0.0.1

# ============================
# DATABASE
# ============================
# Format: mysql://username:password@host:port/database_name
DATABASE_URL=mysql://root:your_password@localhost:3306/vaitikan_db

# ============================
# RAZORPAY PAYMENT GATEWAY
# ============================
# Get test credentials from: https://dashboard.razorpay.com/app/keys
RAZORPAY_KEY_ID=rzp_test_XXXXXXXXXXXXXXX
RAZORPAY_KEY_SECRET=XXXXXXXXXXXXXXXXXXXXXXXX

# ============================
# CLOUDINARY (Optional - for image storage)
# ============================
# Get credentials from: https://cloudinary.com/console
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# ============================
# EMAIL CONFIGURATION (Optional)
# ============================
# For Gmail SMTP, get app password from: https://myaccount.google.com/apppasswords
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=Vaitikan <your-email@gmail.com>

# ============================
# CACHING (Optional)
# ============================
# Leave empty for local memory cache (development)
# For production: redis://localhost:6379/0
REDIS_URL=
```

### 3.3 Database Migration

```bash
# From backend directory, with venv activated

# Create database tables
python manage.py migrate

# Verify migration
python manage.py showmigrations
```

### 3.4 Load Sample Data (Optional)

```bash
# Load fixture data for testing
python manage.py loaddata database/fixtures/countries.json
python manage.py loaddata database/fixtures/sizes.json
python manage.py loaddata database/fixtures/fabrics.json
python manage.py loaddata database/fixtures/colors.json
python manage.py loaddata database/fixtures/patterns.json
python manage.py loaddata database/fixtures/sleeves.json
python manage.py loaddata database/fixtures/pockets.json
python manage.py loaddata database/fixtures/products.json

# Or load all at once
python manage.py loaddata database/fixtures/*.json
```

### 3.5 Create Superuser

```bash
# Create admin account
python manage.py createsuperuser

# Follow prompts:
# Email: admin@example.com
# Username: admin
# Full Name: Admin User
# Password: (secure password)
```

---

## 4. Run Commands

### 4.1 Development Server

```bash
# Start development server (from backend directory)
python manage.py runserver

# Server runs at: http://localhost:8000/
```

**Available URLs:**
- Web Interface: `http://localhost:8000/`
- API Base: `http://localhost:8000/api/`
- Admin Panel: `http://localhost:8000/admin/`

### 4.2 Run with Custom Port

```bash
# Run on different port
python manage.py runserver 8080

# Run accessible from network
python manage.py runserver 0.0.0.0:8000
```

### 4.3 Production Server (WSGI)

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn (Linux/macOS)
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4

# For Windows, use waitress
pip install waitress
waitress-serve --port=8000 config.wsgi:application
```

---

## 5. Verification

### 5.1 Health Check

**Access the home page:**
```
http://localhost:8000/
```

**Expected:** Login page or dashboard (if logged in)

### 5.2 API Test

```bash
# Test public API endpoint
curl http://localhost:8000/api/products/

# Expected: JSON response with product list or empty array
```

### 5.3 Admin Login

1. Navigate to: `http://localhost:8000/admin/`
2. Login with superuser credentials
3. Expected: Django Admin panel

### 5.4 Database Check

```bash
# Run Django shell
python manage.py shell

# Test database connection
>>> from apps.users.models import User
>>> User.objects.count()
# Expected: Number (0 or more)
>>> exit()
```

---

## 6. Test Credentials

| Role | Email | Password |
|------|-------|----------|
| Customer | customer@example.com | customer123 |
| Admin | admin@example.com | admin123 |
| Operator | operator@example.com | operator123 |

> **Note:** Create these users via admin panel or use the `createsuperuser` command.

---

## 7. Razorpay Test Mode

### Test Card Details
| Field | Value |
|-------|-------|
| Card Number | 4111 1111 1111 1111 |
| Expiry | Any future date (e.g., 12/25) |
| CVV | Any 3 digits (e.g., 123) |
| OTP | 1234 |

### Test UPI
| Field | Value |
|-------|-------|
| UPI ID | success@razorpay |

---

## 8. Common Commands Reference

### Database
```bash
# Create new migration after model changes
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Reset database (development only!)
python manage.py flush

# Load fixtures
python manage.py loaddata <fixture_file>

# Dump data to fixture
python manage.py dumpdata app_name.ModelName --indent 2 > fixture.json
```

### User Management
```bash
# Create superuser
python manage.py createsuperuser

# Change user password
python manage.py changepassword <username>
```

### Shell & Debugging
```bash
# Django shell
python manage.py shell

# Shell with auto-import models
python manage.py shell_plus  # requires django-extensions
```

### Static Files
```bash
# Collect static files (for production)
python manage.py collectstatic
```

### Testing
```bash
# Run all tests
python manage.py test

# Run tests for specific app
python manage.py test apps.users

# Run with verbosity
python manage.py test --verbosity=2
```

---

## 9. Troubleshooting

### Issue: MySQLdb ImportError
```
ImportError: No module named 'MySQLdb'
```

**Solution:**
```bash
# Windows: Install mysqlclient wheel
pip install mysqlclient

# If that fails, install via conda
conda install mysqlclient

# Or install mysql-connector-python alternative
pip install mysql-connector-python
```

### Issue: Database Connection Refused
```
django.db.utils.OperationalError: (2003, "Can't connect to MySQL server")
```

**Solution:**
1. Verify MySQL service is running
2. Check DATABASE_URL in `.env`
3. Confirm username/password are correct

### Issue: Permission Denied on Static Files
**Solution:**
```bash
# Create directories if missing
mkdir -p static staticfiles media logs

# Fix permissions (Linux/macOS)
chmod -R 755 static staticfiles media logs
```

### Issue: Redis Connection Failed
**Solution:**
- Leave `REDIS_URL` empty in `.env` for development
- The app will use local memory cache

---

## 10. Next Steps

1. **Explore the API**: Review [API Documentation](./API_DOCUMENTATION.md)
2. **Set up Razorpay**: Get test credentials from [Razorpay Dashboard](https://dashboard.razorpay.com/)
3. **Configure Cloudinary**: Set up image storage at [cloudinary.com](https://cloudinary.com/)
4. **Review Database Design**: Check [Database Design](./database_design_updated.md)
5. **Understand Workflows**: Read [Workflow Documentation](./workflow.md)

---

**Document Version**: 1.0  
**Last Updated**: December 2024  
**Author**: Final Year Project Team
