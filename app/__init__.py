import logging, json, time
from flask import Flask, request, jsonify
from .config import config_by_name
from .extensions import db, migrate, jwt, cache


def create_app(config_name: str = "development"):
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])

    # Extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cache.init_app(app)

    # Logging (stdout)
    handler = logging.StreamHandler()
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)

    # Blueprints
    from .v1 import bp as v1_bp
    from .v2 import bp as v2_bp
    app.register_blueprint(v1_bp, url_prefix="/api/v1")
    app.register_blueprint(v2_bp, url_prefix="/api/v2")

    # Health
    @app.get("/health")
    def health():
        return {"status": "ok"}, 200

    # Request/Response logging hooks
    @app.before_request
    def log_request():
        request.start_time = time.time()
        try:
            body = request.get_json(silent=True)
        except Exception:
            body = None
        app.logger.info(json.dumps({
            "event": "request",
            "method": request.method,
            "path": request.path,
            "args": request.args.to_dict(),
            "json": body
        }))

    @app.after_request
    def log_response(response):
        duration = None
        if hasattr(request, "start_time"):
            duration = round(time.time() - request.start_time, 4)
        app.logger.info(json.dumps({
            "event": "response",
            "status": response.status_code,
            "path": request.path,
            "duration_s": duration
        }))
        return response

    # Custom 404 JSON
    @app.errorhandler(404)
    def not_found(err):
        return jsonify({"error": "Not Found", "message": str(err)}), 404

    return app
