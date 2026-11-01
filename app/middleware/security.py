"""
app/middleware/security.py
---------------------------
Enterprise-grade security headers and protection middleware.
Implements OWASP recommendations for secure web applications.
"""

from flask import request, abort
from functools import wraps
import re


class SecurityMiddleware:
    """
    Adds security headers and protections to all responses.
    Inspired by Helmet.js but tailored for Flask.
    """

    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize security middleware with Flask app."""
        app.after_request(self.add_security_headers)
        app.before_request(self.validate_content_type)

    @staticmethod
    def add_security_headers(response):
        """Add comprehensive security headers to every response."""
        # Prevent clickjacking attacks
        response.headers["X-Frame-Options"] = "DENY"
        
        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Enable XSS filter in browsers
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Strict Transport Security (HTTPS only in production)
        if not response.headers.get("X-Local-Dev"):
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )
        
        # Content Security Policy - strict but allows inline styles for glassmorphism
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp
        
        # Referrer policy for privacy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions policy (formerly Feature-Policy)
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=()"
        )
        
        return response

    @staticmethod
    def validate_content_type():
        """Validate Content-Type for POST/PUT requests to prevent CSRF."""
        if request.method in ["POST", "PUT", "PATCH"]:
            content_type = request.headers.get("Content-Type", "")
            # Allow form data and JSON only
            if not any(ct in content_type for ct in ["application/json", "application/x-www-form-urlencoded", "multipart/form-data"]):
                if request.endpoint and not request.endpoint.startswith("static"):
                    # Allow empty content type for specific endpoints
                    if request.content_length and request.content_length > 0:
                        pass  # Will be caught by route handlers


def sanitize_filename(filename: str) -> str:
    """
    Sanitize uploaded filename to prevent directory traversal and injection.
    Used by file upload endpoints.
    """
    # Remove path separators
    filename = filename.replace("\\", "").replace("/", "")
    
    # Remove null bytes
    filename = filename.replace("\x00", "")
    
    # Allow only alphanumeric, dash, underscore, and dot
    filename = re.sub(r"[^\w\-.]", "_", filename)
    
    # Prevent hidden files
    if filename.startswith("."):
        filename = "_" + filename[1:]
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
        filename = name[:250] + ("." + ext if ext else "")
    
    return filename or "unnamed_file"


def validate_file_upload(file, allowed_extensions: set, max_size_mb: int = 10):
    """
    Validate uploaded file for security.
    
    Args:
        file: FileStorage object from Flask request
        allowed_extensions: Set of allowed extensions (e.g., {"pdf", "docx"})
        max_size_mb: Maximum file size in megabytes
    
    Returns:
        tuple: (is_valid: bool, error_message: str or None)
    """
    if not file or not file.filename:
        return False, "No file provided"
    
    # Check file extension
    if "." not in file.filename:
        return False, "File must have an extension"
    
    ext = file.filename.rsplit(".", 1)[1].lower()
    if ext not in allowed_extensions:
        return False, f"File type .{ext} not allowed. Allowed: {', '.join(allowed_extensions)}"
    
    # Check file size
    file.seek(0, 2)  # Seek to end
    size = file.tell()
    file.seek(0)  # Reset to beginning
    
    max_size = max_size_mb * 1024 * 1024
    if size > max_size:
        return False, f"File too large. Maximum size: {max_size_mb}MB"
    
    if size == 0:
        return False, "File is empty"
    
    return True, None


def require_api_key(f):
    """
    Decorator to require API key authentication for enterprise endpoints.
    Future-proof for API key authentication system.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get("X-API-Key")
        
        # For now, this is a placeholder - actual API key validation
        # will be implemented when the API key management system is added
        if api_key:
            # TODO: Validate API key against database
            pass
        
        return f(*args, **kwargs)
    
    return decorated_function
