"""
app/utils/logger.py
-------------------
Enterprise logging configuration for CyberShield AI.
Structured logging with different levels for development and production.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime
import json


class JSONFormatter(logging.Formatter):
    """Format logs as JSON for easy parsing and analysis."""
    
    def format(self, record):
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add custom fields
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "ip_address"):
            log_data["ip_address"] = record.ip_address
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id
        
        return json.dumps(log_data)


def setup_logging(app):
    """
    Configure application-wide logging.
    
    Creates separate log files for:
    - app.log: General application logs
    - security.log: Security-related events (auth, failed attempts, etc.)
    - ml.log: ML model predictions and performance
    """
    
    # Determine log level
    log_level = logging.DEBUG if app.config.get("DEBUG") else logging.INFO
    
    # Remove default Flask handlers
    app.logger.handlers = []
    
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if app.config.get("DEBUG") else logging.INFO)
    console_formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    app.logger.addHandler(console_handler)

    # Vercel's deployed filesystem is read-only; platform logs replace files.
    if os.environ.get("VERCEL"):
        app.logger.setLevel(log_level)
        app.logger.info("Logging system initialized (serverless console mode)")
        return

    # Create logs directory for local development.
    log_dir = os.path.join(app.root_path, "..", "logs")
    os.makedirs(log_dir, exist_ok=True)
    
    # Application log file
    app_handler = RotatingFileHandler(
        os.path.join(log_dir, "app.log"),
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=10
    )
    app_handler.setLevel(log_level)
    
    if app.config.get("DEBUG"):
        app_formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
        )
    else:
        app_formatter = JSONFormatter()
    
    app_handler.setFormatter(app_formatter)
    app.logger.addHandler(app_handler)
    app.logger.setLevel(log_level)
    
    # Security log file
    security_logger = logging.getLogger("cybershield.security")
    security_handler = RotatingFileHandler(
        os.path.join(log_dir, "security.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=10
    )
    security_handler.setLevel(logging.INFO)
    security_handler.setFormatter(JSONFormatter() if not app.config.get("DEBUG") else app_formatter)
    security_logger.addHandler(security_handler)
    security_logger.setLevel(logging.INFO)
    
    # ML log file
    ml_logger = logging.getLogger("cybershield.ml")
    ml_handler = RotatingFileHandler(
        os.path.join(log_dir, "ml.log"),
        maxBytes=10 * 1024 * 1024,
        backupCount=10
    )
    ml_handler.setLevel(logging.INFO)
    ml_handler.setFormatter(JSONFormatter() if not app.config.get("DEBUG") else app_formatter)
    ml_logger.addHandler(ml_handler)
    ml_logger.setLevel(logging.INFO)
    
    app.logger.info("Logging system initialized")


def log_security_event(action: str, user_id=None, ip_address=None, detail=None, success=True):
    """
    Log security-related events (auth, access control, etc.)
    
    Args:
        action: Type of security event (e.g., "login", "logout", "failed_login")
        user_id: ID of the user involved
        ip_address: IP address of the request
        detail: Additional details about the event
        success: Whether the action was successful
    """
    logger = logging.getLogger("cybershield.security")
    
    log_record = logger.makeRecord(
        name=logger.name,
        level=logging.INFO if success else logging.WARNING,
        fn="",
        lno=0,
        msg=f"Security event: {action}",
        args=(),
        exc_info=None
    )
    
    log_record.user_id = user_id
    log_record.ip_address = ip_address
    log_record.action = action
    log_record.detail = detail
    log_record.success = success
    
    logger.handle(log_record)


def log_ml_prediction(module: str, is_threat: bool, confidence: float, processing_time: float, user_id=None):
    """
    Log ML model predictions for monitoring and analysis.
    
    Args:
        module: Detection module name (e.g., "job_scam", "phishing")
        is_threat: Whether a threat was detected
        confidence: Prediction confidence (0-100)
        processing_time: Time taken to process (seconds)
        user_id: ID of the user who made the request
    """
    logger = logging.getLogger("cybershield.ml")
    
    log_record = logger.makeRecord(
        name=logger.name,
        level=logging.INFO,
        fn="",
        lno=0,
        msg=f"ML prediction: {module}",
        args=(),
        exc_info=None
    )
    
    log_record.module = module
    log_record.is_threat = is_threat
    log_record.confidence = confidence
    log_record.processing_time = processing_time
    log_record.user_id = user_id
    
    logger.handle(log_record)
