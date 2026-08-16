from functools import wraps
import hashlib
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


def verificar_password(password_hash, password_plano):
    """
    Verifica una contraseña contra dos formatos posibles de hash:
      - bcrypt (los que crea la app: seed.py, cambio de contraseña) -> empiezan con $2
      - sha256$<salt>$<hash> (los que genera import_excel.py / el script SQL
        de importación masiva, sin depender de la librería bcrypt)
    """
    if password_hash.startswith("$2"):
        from extensions import bcrypt
        return bcrypt.check_password_hash(password_hash, password_plano)

    if password_hash.startswith("sha256$"):
        try:
            _, salt, hash_esperado = password_hash.split("$", 2)
        except ValueError:
            return False
        data = (salt + password_plano).encode("utf-8")
        for _ in range(20000):
            data = hashlib.sha256(data).digest()
        return data.hex() == hash_esperado

    return False
