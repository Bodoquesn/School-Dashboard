import os
from flask import Flask
from config import Config
from extensions import db, jwt, bcrypt, cors


def create_app(config_override=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if config_override:
        app.config.update(config_override)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    jwt.init_app(app)
    bcrypt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}}, supports_credentials=True)

    from routes.auth import auth_bp
    from routes.alumno import alumno_bp
    from routes.profesor import profesor_bp
    from routes.common import common_bp
    from routes.biometria import biometria_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(alumno_bp)
    app.register_blueprint(profesor_bp)
    app.register_blueprint(common_bp)
    app.register_blueprint(biometria_bp)

    @app.errorhandler(404)
    def not_found(e):
        return {"msg": "Recurso no encontrado"}, 404

    @app.errorhandler(500)
    def server_error(e):
        return {"msg": "Error interno del servidor"}, 500

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
