from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt


def roles_requeridos(*roles_permitidos):
    """Uso: @roles_requeridos('alumno')  o  @roles_requeridos('profesor', 'admin')"""
    def decorador(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            if claims.get("tipo_usuario") not in roles_permitidos:
                return jsonify({"msg": "No tienes permiso para acceder a este recurso"}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorador
