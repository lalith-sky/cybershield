"""
app/middleware/error_handlers.py
---------------------------------
Centralized error handling for consistent API responses.
Provides user-friendly error messages and proper logging.
"""

from flask import jsonify, render_template, request
from werkzeug.exceptions import HTTPException
import logging
import traceback

logger = logging.getLogger(__name__)


def register_error_handlers(app):
    """Register all error handlers with the Flask app."""

    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request errors."""
        if request.path.startswith("/api/"):
            return jsonify({
                "error": "Bad Request",
                "message": "The request could not be understood by the server.",
                "status_code": 400
            }), 400
        return render_template("errors/400.html"), 400

    @app.errorhandler(401)
    def unauthorized(error):
        """Handle 401 Unauthorized errors."""
        if request.path.startswith("/api/"):
            return jsonify({
                "error": "Unauthorized",
                "message": "Authentication required to access this resource.",
                "status_code": 401
            }), 401
        return render_template("errors/401.html"), 401

    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 Forbidden errors."""
        if request.path.startswith("/api/"):
            return jsonify({
                "error": "Forbidden",
                "message": "You don't have permission to access this resource.",
                "status_code": 403
            }), 403
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors."""
        if request.path.startswith("/api/"):
            return jsonify({
                "error": "Not Found",
                "message": "The requested resource does not exist.",
                "status_code": 404
            }), 404
        return render_template("errors/404.html"), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        """Handle 405 Method Not Allowed errors."""
        if request.path.startswith("/api/"):
            return jsonify({
                "error": "Method Not Allowed",
                "message": f"The {request.method} method is not allowed for this endpoint.",
                "status_code": 405
            }), 405
        return render_template("errors/405.html"), 405

    @app.errorhandler(413)
    def request_entity_too_large(error):
        """Handle 413 Payload Too Large errors."""
        if request.path.startswith("/api/"):
            return jsonify({
                "error": "Payload Too Large",
                "message": "The uploaded file or request body exceeds the maximum allowed size.",
                "status_code": 413
            }), 413
        return render_template("errors/413.html"), 413

    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        """Handle 429 Rate Limit Exceeded errors."""
        if request.path.startswith("/api/"):
            return jsonify({
                "error": "Rate Limit Exceeded",
                "message": "Too many requests. Please slow down and try again later.",
                "status_code": 429
            }), 429
        return render_template("errors/429.html"), 429

    @app.errorhandler(500)
    def internal_server_error(error):
        """Handle 500 Internal Server Error."""
        logger.error(f"Internal server error: {error}")
        logger.error(traceback.format_exc())
        
        if request.path.startswith("/api/"):
            return jsonify({
                "error": "Internal Server Error",
                "message": "An unexpected error occurred. Our team has been notified.",
                "status_code": 500
            }), 500
        return render_template("errors/500.html"), 500

    @app.errorhandler(503)
    def service_unavailable(error):
        """Handle 503 Service Unavailable errors."""
        if request.path.startswith("/api/"):
            return jsonify({
                "error": "Service Unavailable",
                "message": "The service is temporarily unavailable. Please try again later.",
                "status_code": 503
            }), 503
        return render_template("errors/503.html"), 503

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        """Catch-all handler for unexpected errors."""
        logger.error(f"Unexpected error: {error}")
        logger.error(traceback.format_exc())
        
        # Don't expose internal error details in production
        if app.config.get("DEBUG"):
            message = str(error)
        else:
            message = "An unexpected error occurred. Our team has been notified."
        
        if request.path.startswith("/api/"):
            return jsonify({
                "error": "Internal Server Error",
                "message": message,
                "status_code": 500
            }), 500
        
        return render_template("errors/500.html", error=message if app.config.get("DEBUG") else None), 500


class APIError(Exception):
    """
    Custom exception for API errors with status codes.
    
    Example:
        raise APIError("Invalid input data", status_code=400)
    """
    def __init__(self, message: str, status_code: int = 400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv["error"] = self.__class__.__name__
        rv["message"] = self.message
        rv["status_code"] = self.status_code
        return rv


class ValidationError(APIError):
    """Validation error for invalid input data."""
    def __init__(self, message: str, payload=None):
        super().__init__(message, status_code=400, payload=payload)


class AuthenticationError(APIError):
    """Authentication error for unauthorized access."""
    def __init__(self, message: str = "Authentication required", payload=None):
        super().__init__(message, status_code=401, payload=payload)


class AuthorizationError(APIError):
    """Authorization error for forbidden access."""
    def __init__(self, message: str = "Insufficient permissions", payload=None):
        super().__init__(message, status_code=403, payload=payload)


class ResourceNotFoundError(APIError):
    """Error for resource not found."""
    def __init__(self, message: str = "Resource not found", payload=None):
        super().__init__(message, status_code=404, payload=payload)
