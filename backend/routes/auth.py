import os
from uuid import uuid4

from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required,
    get_jwt_identity, get_jwt,
)
from extensions import db, bcrypt
from models import Usuario, CAlumno, CProfesor
from utils import verificar_password

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

EXTENSIONES_IMAGEN = {"jpg", "jpeg", "png", "webp"}
MAX_FOTO_BYTES = 5 * 1024 * 1024


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
    if not usuario or not verificar_password(usuario.password_hash, password):
        return jsonify({"msg": "Credenciales inválidas"}), 401

    # Si el hash venía del import masivo (sha256$...), lo "sube" a bcrypt
    # de forma transparente la primera vez que el usuario entra.
    if not usuario.password_hash.startswith("$2"):
        usuario.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
        db.session.commit()

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
    if not verificar_password(usuario.password_hash, actual):
        return jsonify({"msg": "La contraseña actual no es correcta"}), 400
    if len(nueva) < 6:
        return jsonify({"msg": "La nueva contraseña debe tener al menos 6 caracteres"}), 400
    usuario.password_hash = bcrypt.generate_password_hash(nueva).decode("utf-8")
    db.session.commit()
    return jsonify({"msg": "Contraseña actualizada"})


@auth_bp.put("/foto")
@jwt_required()
def cambiar_foto():
    usuario = Usuario.query.get(int(get_jwt_identity()))
    if not usuario or not usuario.activo:
        return jsonify({"msg": "Usuario no encontrado o inactivo"}), 404

    archivo = request.files.get("foto")
    if not archivo or not archivo.filename:
        return jsonify({"msg": "Debes seleccionar una imagen"}), 400

    extension = archivo.filename.rsplit(".", 1)[-1].lower() if "." in archivo.filename else ""
    if extension not in EXTENSIONES_IMAGEN:
        return jsonify({"msg": "La foto debe ser JPG, PNG o WebP"}), 400

    contenido = archivo.read(MAX_FOTO_BYTES + 1)
    if len(contenido) > MAX_FOTO_BYTES:
        return jsonify({"msg": "La foto no puede superar 5 MB"}), 400
    if not _firma_imagen_valida(contenido, extension):
        return jsonify({"msg": "El archivo no contiene una imagen válida"}), 400

    persona = _persona_de(usuario)
    if not persona:
        return jsonify({"msg": "Perfil no encontrado"}), 404

    carpeta = os.path.join(current_app.config["UPLOAD_FOLDER"], "perfiles")
    os.makedirs(carpeta, exist_ok=True)
    nombre = f"perfil_{usuario.id_usuario}_{uuid4().hex}.{extension}"
    ruta = os.path.join(carpeta, nombre)
    with open(ruta, "wb") as destino:
        destino.write(contenido)

    foto_anterior = persona.foto
    persona.foto = f"perfiles/{nombre}"
    db.session.commit()
    _eliminar_foto_generada(foto_anterior)

    return jsonify({"msg": "Foto actualizada", "perfil": _perfil_de(usuario)})


def _persona_de(usuario):
    if usuario.tipo_usuario == "alumno":
        return CAlumno.query.get(usuario.id_referencia)
    if usuario.tipo_usuario == "profesor":
        return CProfesor.query.get(usuario.id_referencia)
    return None


def _firma_imagen_valida(contenido, extension):
    if extension in {"jpg", "jpeg"}:
        return contenido.startswith(b"\xff\xd8\xff")
    if extension == "png":
        return contenido.startswith(b"\x89PNG\r\n\x1a\n")
    if extension == "webp":
        return len(contenido) >= 12 and contenido[:4] == b"RIFF" and contenido[8:12] == b"WEBP"
    return False


def _eliminar_foto_generada(foto):
    if not foto or not foto.replace("\\", "/").startswith("perfiles/perfil_"):
        return
    ruta = os.path.abspath(os.path.join(current_app.config["UPLOAD_FOLDER"], foto))
    raiz = os.path.abspath(current_app.config["UPLOAD_FOLDER"])
    if os.path.commonpath([ruta, raiz]) == raiz and os.path.isfile(ruta):
        os.remove(ruta)
