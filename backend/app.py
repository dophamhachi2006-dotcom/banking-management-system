"""Banking Management System - Flask main app."""
import os, sys, traceback
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from flask import Flask, jsonify
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from backend.config import Config
from backend.api_response import fail
from backend.routes.auth_routes        import bp as auth_bp
from backend.routes.customer_routes    import bp as customer_bp
from backend.routes.account_routes     import bp as account_bp
from backend.routes.transaction_routes import bp as tx_bp
from backend.routes.employee_routes    import bp as employee_bp
from backend.routes.branch_routes      import bp as branch_bp
from backend.routes.report_routes      import bp as report_bp
from backend.routes.loan_routes        import bp as loan_bp
from backend.routes.card_routes        import bp as card_bp
from backend.routes.audit_routes       import bp as audit_bp
from backend.routes.ml_routes          import bp as ml_bp


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)
    CORS(app, resources={r"/api/*": {"origins": "*"}}, supports_credentials=True)

    Limiter(app=app, key_func=get_remote_address,
            default_limits=["200 per minute"])

    # Register blueprints
    app.register_blueprint(auth_bp,     url_prefix="/api/auth")
    app.register_blueprint(customer_bp, url_prefix="/api/customers")
    app.register_blueprint(account_bp,  url_prefix="/api/accounts")
    app.register_blueprint(tx_bp,       url_prefix="/api/transactions")
    app.register_blueprint(employee_bp, url_prefix="/api/employees")
    app.register_blueprint(branch_bp,   url_prefix="/api/branches")
    app.register_blueprint(report_bp,   url_prefix="/api/reports")
    app.register_blueprint(loan_bp,     url_prefix="/api/loans")
    app.register_blueprint(card_bp,     url_prefix="/api/cards")
    app.register_blueprint(audit_bp,    url_prefix="/api/audit")
    app.register_blueprint(ml_bp,       url_prefix="/api/ml")

    @app.get("/api/health")
    def health():
        return {"success": True, "data": {"status": "ok"}, "message": "alive"}

    @app.errorhandler(404)
    def _404(e): return fail("Not found", 404)

    @app.errorhandler(405)
    def _405(e): return fail("Method not allowed", 405)

    @app.errorhandler(Exception)
    def _err(e):
        traceback.print_exc()
        return fail(str(e) or "Internal error", 500)

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=Config.PORT, debug=Config.DEBUG)
