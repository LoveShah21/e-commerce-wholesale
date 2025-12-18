from pathlib import Path
from decouple import config, Csv
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-unsafe-secret-key')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='127.0.0.1,localhost', cast=Csv())

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    'django_filters',
    'cloudinary',
    'cloudinary_storage',

    # Local apps
    'apps.users',
    'apps.products',
    'apps.orders',
    'apps.manufacturing',
    'apps.finance',
    'apps.support',
    'apps.dashboard',
]


MIDDLEWARE = [
    'utils.middleware.HTTPSRedirectMiddleware',  # Redirect HTTP to HTTPS
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.users.middleware.RequestLoggingMiddleware',  # Request/response logging
    'utils.logging_middleware.SlowQueryLoggingMiddleware',  # Slow query logging
    'utils.logging_middleware.SecurityEventLoggingMiddleware',  # Security event logging
    'utils.middleware.SecurityHeadersMiddleware',  # Add security headers
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        default=config('DATABASE_URL'),
        conn_max_age=600,
        ssl_require=False 
    )
}

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Custom User Model
AUTH_USER_MODEL = 'users.User'

# Login URLs
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/login/'

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_TZ = True



# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Cloudinary Configuration
import cloudinary
import cloudinary.uploader
import cloudinary.api

CLOUDINARY_STORAGE = {
    'CLOUD_NAME': config('CLOUDINARY_CLOUD_NAME', default=''),
    'API_KEY': config('CLOUDINARY_API_KEY', default=''),
    'API_SECRET': config('CLOUDINARY_API_SECRET', default=''),
}

# Configure Cloudinary
cloudinary.config(
    cloud_name=CLOUDINARY_STORAGE['CLOUD_NAME'],
    api_key=CLOUDINARY_STORAGE['API_KEY'],
    api_secret=CLOUDINARY_STORAGE['API_SECRET'],
    secure=True
)

# Use Cloudinary for media storage if configured
if CLOUDINARY_STORAGE.get('CLOUD_NAME'):
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    'DEFAULT_PAGINATION_CLASS': 'utils.pagination.StandardResultsSetPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ),
}

# JWT Settings
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# CORS
CORS_ALLOW_ALL_ORIGINS = True # For development

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {asctime} {message}',
            'style': '{',
        },
        'detailed': {
            'format': '{levelname} {asctime} {name} {module} {funcName} {lineno} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'application.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'errors.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'detailed',
        },
        'payment_file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'payments.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 10,  # Keep more payment logs
            'formatter': 'detailed',
        },
        'security_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'security.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 10,
            'formatter': 'detailed',
        },
        'slow_query_file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'slow_queries.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'detailed',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.request': {
            'handlers': ['error_file', 'console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['security_file', 'console'],
            'level': 'WARNING',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['slow_query_file'],
            'level': 'DEBUG' if DEBUG else 'WARNING',
            'propagate': False,
        },
        'services': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'services.payment_service': {
            'handlers': ['payment_file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apps': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG' if DEBUG else 'INFO',
            'propagate': False,
        },
        'apps.users': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}

# Database Query Logging Configuration
# Log queries that take longer than this threshold (in seconds)
SLOW_QUERY_THRESHOLD = config('SLOW_QUERY_THRESHOLD', default=1.0, cast=float)

# Enable query logging in DEBUG mode or when explicitly enabled
ENABLE_QUERY_LOGGING = config('ENABLE_QUERY_LOGGING', default=DEBUG, cast=bool)

# Security Settings
# =================

# HTTPS Enforcement
ENFORCE_HTTPS = config('ENFORCE_HTTPS', default=not DEBUG, cast=bool)

# CSRF Protection
CSRF_COOKIE_SECURE = not DEBUG  # Only send CSRF cookie over HTTPS in production
CSRF_COOKIE_HTTPONLY = True  # Prevent JavaScript access to CSRF cookie
CSRF_COOKIE_SAMESITE = 'Strict'  # Prevent CSRF cookie from being sent in cross-site requests
CSRF_USE_SESSIONS = False  # Use cookie-based CSRF tokens
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='', cast=Csv())

# Session Security
SESSION_COOKIE_SECURE = not DEBUG  # Only send session cookie over HTTPS in production
SESSION_COOKIE_HTTPONLY = True  # Prevent JavaScript access to session cookie
SESSION_COOKIE_SAMESITE = 'Lax'  # Prevent session cookie from being sent in cross-site requests
SESSION_COOKIE_AGE = 86400  # 24 hours

# Security Headers
SECURE_BROWSER_XSS_FILTER = True  # Enable browser XSS filtering
SECURE_CONTENT_TYPE_NOSNIFF = True  # Prevent MIME type sniffing
X_FRAME_OPTIONS = 'DENY'  # Prevent clickjacking

# HTTPS/SSL Settings (only in production)
if not DEBUG:
    SECURE_SSL_REDIRECT = ENFORCE_HTTPS  # Redirect all HTTP to HTTPS
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Caching Configuration
# ======================
# Django supports multiple cache backends. By default, we use local memory cache.
# For production, Redis is recommended for better performance and scalability.

# Check if Redis is configured
REDIS_URL = config('REDIS_URL', default=None)

if REDIS_URL:
    # Use Redis cache backend if configured
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.redis.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 50,
                    'retry_on_timeout': True,
                },
                'SOCKET_CONNECT_TIMEOUT': 5,
                'SOCKET_TIMEOUT': 5,
            },
            'KEY_PREFIX': 'vaitikan',
            'TIMEOUT': 300,  # Default timeout: 5 minutes
        }
    }
else:
    # Fallback to local memory cache for development
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'vaitikan-cache',
            'OPTIONS': {
                'MAX_ENTRIES': 1000,
            },
            'TIMEOUT': 300,  # Default timeout: 5 minutes
        }
    }

# Cache key prefix to avoid collisions
CACHE_MIDDLEWARE_KEY_PREFIX = 'vaitikan'
CACHE_MIDDLEWARE_SECONDS = 300

# Rate Limiting
RATELIMIT_ENABLE = config('RATELIMIT_ENABLE', default=True, cast=bool)
RATELIMIT_USE_CACHE = 'default'  # Use default cache for rate limiting

# File Upload Security
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5 MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5 MB
FILE_UPLOAD_PERMISSIONS = 0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS = 0o755

# Content Security Policy
CSP_DEFAULT_SRC = ("'self'",)
CSP_SCRIPT_SRC = ("'self'", "'unsafe-inline'", "'unsafe-eval'", "https://cdn.jsdelivr.net", "https://checkout.razorpay.com")
CSP_STYLE_SRC = ("'self'", "'unsafe-inline'", "https://cdn.jsdelivr.net")
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = ("'self'", "https://cdn.jsdelivr.net")
CSP_CONNECT_SRC = ("'self'", "https://api.razorpay.com")
CSP_FRAME_SRC = ("https://api.razorpay.com",)

# Additional Security Settings
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# Email Configuration
# ===================
# Gmail SMTP Configuration for sending emails

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default=EMAIL_HOST_USER)
SERVER_EMAIL = DEFAULT_FROM_EMAIL

# Email settings for development
if DEBUG:
    # In development, you can use console backend to see emails in console
    # EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
    pass
