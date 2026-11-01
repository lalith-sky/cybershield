"""
config.py
---------
Centralized application configuration.

All environment-specific values (secret key, database location, debug mode)
live here instead of being scattered across the codebase. Values are read
from environment variables where possible so the same code can run in
development, staging, and production without modification.

Enhanced for enterprise deployment with comprehensive security settings.
"""

import os
from datetime import timedelta

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    """Base configuration shared by every environment."""

    # Flask signs session cookies with this key. In production this MUST be
    # overridden via the SECRET_KEY environment variable.
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-insecure-key-change-me")

    # SQLite database lives in the Flask instance folder (not version
    # controlled), so local dev data never gets committed by accident.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'cybershield.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    # Cookie hardening (safe defaults even outside production).
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_REFRESH_EACH_REQUEST = True

    # Max upload size for document analyzer
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024  # 10 MB
    
    # Allowed file extensions for document upload
    ALLOWED_UPLOAD_EXTENSIONS = {
        "pdf", "docx", "txt", "png", "jpg", "jpeg", "gif"
    }
    
    # Upload folder
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "instance", "uploads")
    
    # Rate limiting defaults
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = "memory://"
    
    # CSRF protection
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # No time limit for CSRF token
    
    # Application metadata
    APP_NAME = "CyberShield AI"
    APP_VERSION = "2.0.0"
    APP_DESCRIPTION = "Enterprise AI-Powered Cyber Defense Platform"
    
    # API configuration
    API_TITLE = "CyberShield AI API"
    API_VERSION = "v1"
    
    # Pagination
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    # ML Model paths
    MODELS_DIR = os.path.join(BASE_DIR, "models")
    
    # Cache configuration
    CACHE_TYPE = "simple"
    CACHE_DEFAULT_TIMEOUT = 300
    
    # Logging
    LOG_LEVEL = "INFO"
    LOG_FORMAT = "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    
    # Security headers
    SECURITY_HEADERS_ENABLED = True
    
    # CORS settings
    CORS_ENABLED = False
    CORS_ORIGINS = []


class DevelopmentConfig(Config):
    """Development environment configuration."""
    DEBUG = True
    TESTING = False
    LOG_LEVEL = "DEBUG"
    
    # Disable some security features for easier development
    SESSION_COOKIE_SECURE = False
    WTF_CSRF_ENABLED = False  # Easier API testing
    
    # More lenient rate limits
    RATELIMIT_ENABLED = False


class ProductionConfig(Config):
    """Production environment configuration."""
    DEBUG = False
    TESTING = False
    
    # Strict security in production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Strict"
    
    # Enable all security features
    WTF_CSRF_ENABLED = True
    SECURITY_HEADERS_ENABLED = True
    RATELIMIT_ENABLED = True
    
    # PostgreSQL for production (if DATABASE_URL is set)
    # Falls back to SQLite if not set
    if os.environ.get("DATABASE_URL", "").startswith("postgresql"):
        SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL").replace(
            "postgres://", "postgresql://", 1
        )
    
    # Production logging
    LOG_LEVEL = "WARNING"


class TestingConfig(Config):
    """Testing environment configuration."""
    TESTING = True
    DEBUG = True
    
    # In-memory database for tests
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    
    # Disable security features that interfere with testing
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False
    SESSION_COOKIE_SECURE = False
    
    # Speed up password hashing in tests
    BCRYPT_LOG_ROUNDS = 4


CONFIG_MAP = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config():
    """Resolve the active config class from the FLASK_ENV environment variable."""
    env = os.environ.get("FLASK_ENV", "development")
    return CONFIG_MAP.get(env, DevelopmentConfig)
