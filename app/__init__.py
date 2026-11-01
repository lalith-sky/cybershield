"""
app/__init__.py
------------------
Application factory. Assembles the Flask app from:
  - config.py            (environment-specific settings)
  - extensions.py         (db, login_manager)
  - app/database/models   (ORM schema)
  - app/routes/*          (blueprints: main, auth, predict)
  - app/middleware/*      (security, rate limiting, error handlers)

Enhanced for enterprise deployment with comprehensive middleware stack.
"""

import os

from flask import Flask

from config import get_config
from extensions import db, login_manager

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def create_app(config_class=None):
    app = Flask(
        __name__,
        template_folder=os.path.join(PROJECT_ROOT, "templates"),
        static_folder=os.path.join(PROJECT_ROOT, "static"),
        instance_path=os.path.join(PROJECT_ROOT, "instance"),
        instance_relative_config=True,
    )
    app.config.from_object(config_class or get_config())

    # Create necessary directories
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(app.config.get("UPLOAD_FOLDER"), exist_ok=True)

    # Initialize logging
    from app.utils.logger import setup_logging
    setup_logging(app)
    
    app.logger.info(f"Starting {app.config['APP_NAME']} v{app.config['APP_VERSION']}")
    app.logger.info(f"Environment: {app.config.get('ENV', 'development')}")

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Initialize middleware
    if app.config.get("SECURITY_HEADERS_ENABLED"):
        from app.middleware.security import SecurityMiddleware
        SecurityMiddleware(app)
        app.logger.info("Security middleware enabled")
    
    if app.config.get("RATELIMIT_ENABLED"):
        from app.middleware.rate_limiter import RateLimiter
        rate_limiter = RateLimiter(app)
        app.rate_limiter = rate_limiter
        app.logger.info("Rate limiting enabled")
    
    # Register error handlers
    from app.middleware.error_handlers import register_error_handlers
    register_error_handlers(app)

    from app.database.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register blueprints
    from app.routes.main_routes import main_bp
    from app.routes.auth_routes import auth_bp
    from app.routes.predict_routes import predict_bp
    from app.routes.api_routes import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(predict_bp)
    app.register_blueprint(api_bp)
    
    app.logger.info("Blueprints registered: main, auth, predict")

    # Initialize database and seed data
    with app.app_context():
        db.create_all()
        _seed_threats()
        app.logger.info("Database initialized")

    return app


def _seed_threats():
    """Populate the Threat lookup table on first run so /api/modules has
    real data immediately. Idempotent -- only inserts rows that don't exist."""
    from app.database.models import Threat

    seed_data = [
        dict(key="job_scam", name="Fake Job Offer Detection", category="Employment Fraud",
             description="Detects fraudulent job postings and recruitment scams using NLP.",
             icon="briefcase", status="active"),
        dict(key="phishing", name="Phishing Email Detection", category="Email Security",
             description="Flags phishing attempts in email content using a trained classifier.",
             icon="mail-warning", status="active"),
    ]

    existing_keys = {t.key for t in Threat.query.all()}
    for row in seed_data:
        if row["key"] not in existing_keys:
            db.session.add(Threat(**row))
    db.session.commit()
