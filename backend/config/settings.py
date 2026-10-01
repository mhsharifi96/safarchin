from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="insecure-dev-key-change-me")
DEBUG = env.bool("DJANGO_DEBUG", default=False)
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

FRONTEND_BASE_URL = env("FRONTEND_BASE_URL", default="http://localhost:3000")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "corsheaders",
    "django_celery_results",
    "apps.accounts",
    "apps.trips",
    "apps.planner",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "apps.accounts.middleware.GuestSessionMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": env("POSTGRES_DB", default="safarchin"),
        "USER": env("POSTGRES_USER", default="safarchin"),
        "PASSWORD": env("POSTGRES_PASSWORD", default="safarchin"),
        "HOST": env("POSTGRES_HOST", default="localhost"),
        "PORT": env("POSTGRES_PORT", default="5432"),
    }
}

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "fa-ir"
# All instants are stored in UTC; trip-local wall-clock times use TripPreferences.timezone (default Asia/Tehran).
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

DEFAULT_TRIP_TIMEZONE = env("DEFAULT_TRIP_TIMEZONE", default="Asia/Tehran")

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Redis cache (also backs DRF throttling / rate limiting) ---
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env("REDIS_URL", default="redis://localhost:6379/0"),
        "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
    }
}
SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"
SESSION_CACHE_ALIAS = "default"
SESSION_COOKIE_AGE = 60 * 60 * 24 * 30  # 30 days
SESSION_SAVE_EVERY_REQUEST = True

# --- Single-origin-style cookie auth for the Next.js frontend ---
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=["http://localhost:3000"])
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=["http://localhost:3000"])
CSRF_COOKIE_HTTPONLY = False  # Next.js reads this to echo back as X-CSRFToken
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
CSRF_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework.authentication.SessionAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer",),
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.ScopedRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "auth-write": "10/minute",
        "auth-sensitive": "5/hour",
        "planner": "20/hour",
    },
    "EXCEPTION_HANDLER": "apps.accounts.exceptions.safarchin_exception_handler",
}

# --- Email ---
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="Safarchin <no-reply@safarchin.local>")
EMAIL_HOST = env("SMTP_HOST", default="")
EMAIL_PORT = env.int("SMTP_PORT", default=587)
EMAIL_USE_TLS = env.bool("SMTP_USE_TLS", default=True)
EMAIL_HOST_USER = env("SMTP_USER", default="")
EMAIL_HOST_PASSWORD = env("SMTP_PASSWORD", default="")

EMAIL_VERIFICATION_TOKEN_MAX_AGE = 60 * 60 * 24  # 24h
PASSWORD_RESET_TOKEN_MAX_AGE = 60 * 60  # 1h

# --- Celery ---
CELERY_BROKER_URL = env("CELERY_BROKER_REDIS_URL", default="redis://localhost:6379/1")
CELERY_RESULT_BACKEND = "django-db"
CELERY_CACHE_BACKEND = "django-cache"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TASK_TIME_LIMIT = 60 * 10
CELERY_TASK_SOFT_TIME_LIMIT = 60 * 8

# --- LLM / agent configuration (langchain-openai) ---
OPENAI_API_KEY = env("OPENAI_API_KEY", default="")
OPENAI_MODEL_NAME = env("OPENAI_MODEL_NAME", default="gpt-5.6-luna")
OPENAI_BASE_URL = env("OPENAI_BASE_URL", default="") or None

LANGCHAIN_TRACING_V2 = env.bool("LANGCHAIN_TRACING_V2", default=False)
LANGCHAIN_API_KEY = env("LANGCHAIN_API_KEY", default="")
LANGCHAIN_PROJECT = env("LANGCHAIN_PROJECT", default="safarchin")

TAVILY_API_KEY = env("TAVILY_API_KEY", default="")

NESHAN_API_KEY = env("NESHAN_API_KEY", default="")
NESHAN_WEB_SDK_KEY = env("NESHAN_WEB_SDK_KEY", default="")

import os as _os  # noqa: E402

if LANGCHAIN_TRACING_V2:
    _os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
    _os.environ.setdefault("LANGCHAIN_API_KEY", LANGCHAIN_API_KEY)
    _os.environ.setdefault("LANGCHAIN_PROJECT", LANGCHAIN_PROJECT)
