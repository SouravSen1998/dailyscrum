from flask import Flask
from dotenv import load_dotenv
from app.config import Config
from app.extensions import db, migrate, cors
from app.routes.health import health_bp
from app.routes.tickets import tickets_bp
from app.routes.dashboard import dashboard_bp
from app.routes.assignee_matrix import assignee_matrix_bp

load_dotenv()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app)

    app.register_blueprint(health_bp, url_prefix="/api/health")
    app.register_blueprint(tickets_bp, url_prefix="/api/tickets")
    app.register_blueprint(dashboard_bp, url_prefix="/api/dashboard")
    app.register_blueprint(assignee_matrix_bp, url_prefix="/api/assignee-matrix")

    return app
