from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required,
    get_jwt_identity, get_jwt,
)
from extensions import db, bcrypt
from models import Usuario, CAlumno, CProfesor

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def _perfil_de(usuario: Usuario):
    """Regresa el perfil (nombre, foto, etc.) ligado a este usuario."""
    if usuario.tipo_usuario == "alumno":
        persona = CAlumno.query.get(usuario.id_referencia)
        return persona.to_dict() if persona else {}
    if usuario.tipo_usuario == "profesor":
        persona = CProfesor.query.get(usuario.id_referencia)
        return persona.to_dict() if persona else {}
    return {"nombre": "Administrador"}


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""

    if not username or not password:
        return jsonify({"msg": "username y password son requeridos"}), 400

    usuario = Usuario.query.filter_by(username=username, activo=True).first()
    if not usuario or not bcrypt.check_password_hash(usuario.password_hash, password):
        return jsonify({"msg": "Credenciales inválidas"}), 401

    claims = {"tipo_usuario": usuario.tipo_usuario, "id_referencia": usuario.id_referencia}
    access_token = create_access_token(identity=str(usuario.id_usuario), additional_claims=claims)
    refresh_token = create_refresh_token(identity=str(usuario.id_usuario), additional_claims=claims)

    return jsonify({
        "access_token": access_token,
        "refresh_token": refresh_token,
        "usuario": usuario.to_dict(),
        "perfil": _perfil_de(usuario),
    })


@auth_bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    identity = get_jwt_identity()
    claims = get_jwt()
    new_token = create_access_token(
        identity=identity,
        additional_claims={
            "tipo_usuario": claims.get("tipo_usuario"),
            "id_referencia": claims.get("id_referencia"),
        },
    )
    return jsonify({"access_token": new_token})


@auth_bp.get("/me")
@jwt_required()
def me():
    usuario = Usuario.query.get(int(get_jwt_identity()))
    if not usuario:
        return jsonify({"msg": "Usuario no encontrado"}), 404
    return jsonify({"usuario": usuario.to_dict(), "perfil": _perfil_de(usuario)})


@auth_bp.put("/idioma")
@jwt_required()
def set_idioma():
    data = request.get_json(silent=True) or {}
    idioma = data.get("idioma")
    if idioma not in ("es", "en"):
        return jsonify({"msg": "idioma debe ser 'es' o 'en'"}), 400
    usuario = Usuario.query.get(int(get_jwt_identity()))
    usuario.idioma_preferido = idioma
    db.session.commit()
    return jsonify({"idioma_preferido": usuario.idioma_preferido})


@auth_bp.put("/password")
@jwt_required()
def cambiar_password():
    data = request.get_json(silent=True) or {}
    actual = data.get("password_actual", "")
    nueva = data.get("password_nueva", "")
    usuario = Usuario.query.get(int(get_jwt_identity()))
    if not bcrypt.check_password_hash(usuario.password_hash, actual):
        return jsonify({"msg": "La contraseña actual no es correcta"}), 400
    if len(nueva) < 6:
        return jsonify({"msg": "La nueva contraseña debe tener al menos 6 caracteres"}), 400
    usuario.password_hash = bcrypt.generate_password_hash(nueva).decode("utf-8")
    db.session.commit()
    return jsonify({"msg": "Contraseña actualizada"})
