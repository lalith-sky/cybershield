"""
app/middleware/rate_limiter.py
-------------------------------
In-memory rate limiting for API endpoints.
Protects against abuse and ensures fair usage across all users.
"""

from flask import request, jsonify
from functools import wraps
from collections import defaultdict
from datetime import datetime, timedelta
import threading


class RateLimiter:
    """
    Simple in-memory rate limiter using sliding window algorithm.
    For production, consider Redis-based implementation.
    """

    def __init__(self, app=None):
        self.requests = defaultdict(list)
        self.lock = threading.Lock()
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize rate limiter with Flask app."""
        # Cleanup old entries every 5 minutes
        self.cleanup_interval = 300
        self._schedule_cleanup()

    def _schedule_cleanup(self):
        """Background cleanup of expired rate limit entries."""
        def cleanup():
            with self.lock:
                now = datetime.now()
                for key in list(self.requests.keys()):
                    # Remove entries older than 1 hour
                    self.requests[key] = [
                        ts for ts in self.requests[key]
                        if now - ts < timedelta(hours=1)
                    ]
                    if not self.requests[key]:
                        del self.requests[key]
            
            # Schedule next cleanup
            threading.Timer(self.cleanup_interval, cleanup).start()
        
        threading.Timer(self.cleanup_interval, cleanup).start()

    def _get_identifier(self):
        """Get unique identifier for the request (IP address)."""
        # Try to get real IP from proxy headers
        if request.headers.get("X-Forwarded-For"):
            return request.headers.get("X-Forwarded-For").split(",")[0].strip()
        if request.headers.get("X-Real-IP"):
            return request.headers.get("X-Real-IP")
        return request.remote_addr or "unknown"

    def _is_rate_limited(self, identifier: str, limit: int, window: int) -> tuple:
        """
        Check if request should be rate limited.
        
        Args:
            identifier: Unique identifier (IP address)
            limit: Maximum requests allowed
            window: Time window in seconds
        
        Returns:
            tuple: (is_limited: bool, retry_after: int)
        """
        with self.lock:
            now = datetime.now()
            window_start = now - timedelta(seconds=window)
            
            # Get requests in current window
            key = f"{identifier}:{request.endpoint}"
            requests_in_window = [
                ts for ts in self.requests[key]
                if ts > window_start
            ]
            
            if len(requests_in_window) >= limit:
                # Calculate retry after
                oldest_request = min(requests_in_window)
                retry_after = int((oldest_request + timedelta(seconds=window) - now).total_seconds())
                return True, max(retry_after, 1)
            
            # Add current request
            self.requests[key].append(now)
            return False, 0

    def limit(self, limit: int = 100, window: int = 60):
        """
        Decorator to apply rate limiting to a route.
        
        Args:
            limit: Maximum requests allowed (default: 100)
            window: Time window in seconds (default: 60)
        
        Example:
            @app.route("/api/predict")
            @rate_limiter.limit(limit=10, window=60)
            def predict():
                return {"result": "success"}
        """
        def decorator(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                identifier = self._get_identifier()
                is_limited, retry_after = self._is_rate_limited(identifier, limit, window)
                
                if is_limited:
                    response = jsonify({
                        "error": "Rate limit exceeded",
                        "message": f"Too many requests. Please try again in {retry_after} seconds.",
                        "retry_after": retry_after
                    })
                    response.status_code = 429
                    response.headers["Retry-After"] = str(retry_after)
                    response.headers["X-RateLimit-Limit"] = str(limit)
                    response.headers["X-RateLimit-Window"] = str(window)
                    return response
                
                return f(*args, **kwargs)
            
            return decorated_function
        return decorator


# Preset rate limit decorators for common use cases
def rate_limit_strict(f):
    """Strict rate limit: 10 requests per minute"""
    limiter = RateLimiter()
    return limiter.limit(limit=10, window=60)(f)


def rate_limit_moderate(f):
    """Moderate rate limit: 30 requests per minute"""
    limiter = RateLimiter()
    return limiter.limit(limit=30, window=60)(f)


def rate_limit_generous(f):
    """Generous rate limit: 100 requests per minute"""
    limiter = RateLimiter()
    return limiter.limit(limit=100, window=60)(f)
