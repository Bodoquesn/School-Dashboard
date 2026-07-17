from flask import Blueprint, send_from_directory, current_app
from flask_jwt_extended import jwt_required

common_bp = Blueprint("common", __name__, url_prefix="/api")


@common_bp.get("/archivos/<path:nombre_archivo>")
@jwt_required()
def descargar_archivo(nombre_archivo):
    """Sirve fotos, tareas y entregas subidas (requiere estar logueado)."""
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], nombre_archivo)


@common_bp.get("/salud")
def salud():
    return {"status": "ok"}
