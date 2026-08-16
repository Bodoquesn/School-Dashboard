from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import numpy as np
from flask import Blueprint, current_app, jsonify, request
from flask_jwt_extended import get_jwt
from sqlalchemy import distinct, func

from extensions import db
from models import (
    CAlumno, CCampus, CGrupo, EventoBiometrico, RostroAlumno,
)
from services.face_engine import FaceEngineError, cosine_similarity, get_face_engine
from utils import roles_requeridos


biometria_bp = Blueprint("biometria", __name__, url_prefix="/api/biometria")
TIPOS_IMAGEN = {"image/jpeg", "image/png", "image/webp"}
TIPOS_EVENTO = {"entrada", "salida"}


def _claims():
    return get_jwt()


def _alumnos_autorizados_query():
    claims = _claims()
    query = CAlumno.query
    if claims.get("tipo_usuario") == "profesor":
        query = query.join(CGrupo, CAlumno.id_grupo == CGrupo.id_grupo).filter(
            CGrupo.id_profesor == claims.get("id_referencia")
        )
    return query


def _alumno_autorizado(id_alumno):
    return _alumnos_autorizados_query().filter(CAlumno.id_alumno == id_alumno).first()


def _leer_imagen():
    archivo = request.files.get("file")
    if not archivo or not archivo.filename:
        return None, (jsonify({"msg": "Debes enviar una imagen"}), 400)
    if archivo.mimetype not in TIPOS_IMAGEN:
        return None, (jsonify({"msg": "Usa una imagen JPG, PNG o WebP"}), 415)
    maximo = current_app.config["FACE_MAX_UPLOAD_MB"] * 1024 * 1024
    contenido = archivo.read(maximo + 1)
    if len(contenido) > maximo:
        return None, (jsonify({"msg": f"La imagen supera {current_app.config['FACE_MAX_UPLOAD_MB']} MB"}), 413)
    return contenido, None


def _extraer_descriptor(contenido):
    try:
        motor = get_face_engine()
        return motor, motor.extract_embedding(contenido), None
    except FaceEngineError as exc:
        return None, None, (jsonify({"msg": str(exc)}), 422)
    except RuntimeError as exc:
        return None, None, (jsonify({"msg": str(exc)}), 503)


@biometria_bp.get("/alumnos")
@roles_requeridos("profesor", "admin")
def alumnos_biometria():
    alumnos = _alumnos_autorizados_query().order_by(CAlumno.nombre, CAlumno.apellido_paterno).all()
    ids_con_rostro = {
        item.id_alumno for item in RostroAlumno.query.filter(
            RostroAlumno.id_alumno.in_([a.id_alumno for a in alumnos])
        ).all()
    } if alumnos else set()
    return jsonify([
        {
            **alumno.to_dict(),
            "rostro_registrado": alumno.id_alumno in ids_con_rostro,
        }
        for alumno in alumnos
    ])


@biometria_bp.post("/alumnos/<int:id_alumno>/enrolar")
@roles_requeridos("profesor", "admin")
def enrolar_rostro(id_alumno):
    alumno = _alumno_autorizado(id_alumno)
    if not alumno:
        return jsonify({"msg": "Alumno no encontrado o no autorizado"}), 404
    contenido, error = _leer_imagen()
    if error:
        return error
    motor, descriptor, error = _extraer_descriptor(contenido)
    if error:
        return error

    rostro = RostroAlumno.query.filter_by(id_alumno=id_alumno).first()
    if rostro:
        rostro.motor = motor.name
        rostro.descriptor = descriptor.astype(float).tolist()
        rostro.actualizado_en = datetime.utcnow()
    else:
        rostro = RostroAlumno(
            id_alumno=id_alumno,
            motor=motor.name,
            descriptor=descriptor.astype(float).tolist(),
        )
        db.session.add(rostro)
    db.session.commit()
    return jsonify({
        "id_alumno": id_alumno,
        "motor": motor.name,
        "msg": "Rostro enrolado correctamente",
    })


@biometria_bp.post("/reconocer")
@roles_requeridos("profesor", "admin")
def reconocer_rostro():
    tipo_evento = request.form.get("tipo_evento", "entrada")
    camara = (request.form.get("camara") or "Cámara principal").strip()[:150]
    if tipo_evento not in TIPOS_EVENTO:
        return jsonify({"msg": "El evento debe ser entrada o salida"}), 422

    contenido, error = _leer_imagen()
    if error:
        return error
    motor, descriptor, error = _extraer_descriptor(contenido)
    if error:
        return error

    alumnos = _alumnos_autorizados_query().all()
    ids_alumnos = [alumno.id_alumno for alumno in alumnos]
    rostros = RostroAlumno.query.filter(
        RostroAlumno.id_alumno.in_(ids_alumnos), RostroAlumno.motor == motor.name
    ).all() if ids_alumnos else []

    mejor = None
    mejor_puntaje = -1.0
    for rostro in rostros:
        puntaje = cosine_similarity(descriptor, np.asarray(rostro.descriptor, dtype=np.float32))
        if puntaje > mejor_puntaje:
            mejor, mejor_puntaje = rostro, puntaje

    umbral = current_app.config["FACE_MATCH_THRESHOLD"]
    if mejor is None or mejor_puntaje < umbral:
        return jsonify({
            "coincidencia": False,
            "confianza": mejor_puntaje if mejor_puntaje >= 0 else None,
            "evento_creado": False,
            "msg": "No se encontró una coincidencia suficiente",
        })

    alumno = next(a for a in alumnos if a.id_alumno == mejor.id_alumno)
    limite = datetime.utcnow() - timedelta(minutes=current_app.config["ATTENDANCE_COOLDOWN_MINUTES"])
    reciente = EventoBiometrico.query.filter(
        EventoBiometrico.id_alumno == alumno.id_alumno,
        EventoBiometrico.tipo_evento == tipo_evento,
        EventoBiometrico.reconocido_en >= limite,
    ).first()

    creado = reciente is None
    if creado:
        claims = _claims()
        db.session.add(EventoBiometrico(
            id_alumno=alumno.id_alumno,
            id_profesor=claims.get("id_referencia") if claims.get("tipo_usuario") == "profesor" else None,
            confianza=mejor_puntaje,
            camara=camara,
            tipo_evento=tipo_evento,
        ))
        db.session.commit()

    campus = CCampus.query.get(alumno.id_campus) if alumno.id_campus else None
    return jsonify({
        "coincidencia": True,
        "confianza": mejor_puntaje,
        "id_alumno": alumno.id_alumno,
        "alumno": alumno.nombre_completo(),
        "campus": campus.nombrecampus if campus else None,
        "evento_creado": creado,
        "msg": "Asistencia registrada correctamente" if creado else "Identidad reconocida; no se duplicó el registro",
    })


@biometria_bp.get("/eventos")
@roles_requeridos("profesor", "admin")
def eventos_biometria():
    limite = min(max(request.args.get("limite", 200, type=int), 1), 500)
    ids_alumnos = [a.id_alumno for a in _alumnos_autorizados_query().all()]
    eventos = EventoBiometrico.query.filter(
        EventoBiometrico.id_alumno.in_(ids_alumnos)
    ).order_by(EventoBiometrico.reconocido_en.desc()).limit(limite).all() if ids_alumnos else []
    resultado = []
    for evento in eventos:
        alumno = CAlumno.query.get(evento.id_alumno)
        campus = CCampus.query.get(alumno.id_campus) if alumno and alumno.id_campus else None
        resultado.append(evento.to_dict(alumno, campus))
    return jsonify(resultado)


@biometria_bp.get("/resumen")
@roles_requeridos("profesor", "admin")
def resumen_biometria():
    ids_alumnos = [a.id_alumno for a in _alumnos_autorizados_query().all()]
    if not ids_alumnos:
        return jsonify({"alumnos_activos": 0, "presentes_hoy": 0, "ausentes_estimados": 0, "eventos_hoy": 0})

    zona = ZoneInfo(current_app.config["TIMEZONE"])
    hoy = datetime.now(zona).date()
    inicio = datetime.combine(hoy, time.min, tzinfo=zona).astimezone(timezone.utc).replace(tzinfo=None)
    fin = datetime.combine(hoy, time.max, tzinfo=zona).astimezone(timezone.utc).replace(tzinfo=None)
    presentes = db.session.query(func.count(distinct(EventoBiometrico.id_alumno))).filter(
        EventoBiometrico.id_alumno.in_(ids_alumnos),
        EventoBiometrico.reconocido_en.between(inicio, fin),
        EventoBiometrico.tipo_evento == "entrada",
    ).scalar() or 0
    eventos = EventoBiometrico.query.filter(
        EventoBiometrico.id_alumno.in_(ids_alumnos),
        EventoBiometrico.reconocido_en.between(inicio, fin),
    ).count()
    return jsonify({
        "alumnos_activos": len(ids_alumnos),
        "presentes_hoy": presentes,
        "ausentes_estimados": max(len(ids_alumnos) - presentes, 0),
        "eventos_hoy": eventos,
    })
