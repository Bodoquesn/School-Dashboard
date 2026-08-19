import os
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import get_jwt
from werkzeug.utils import secure_filename

from extensions import db
from models import (
    CAlumno, CGrupo, CMateria, DCalificacion, DHorario,
    Tarea, EntregaTarea, Asistencia,
)
from utils import roles_requeridos

profesor_bp = Blueprint("profesor", __name__, url_prefix="/api/profesor")

ESTATUS_ASISTENCIA = {"presente", "ausente", "retardo", "justificado"}
EXTENSIONES_PERMITIDAS = {"pdf", "doc", "docx", "xls", "xlsx", "ppt", "pptx", "txt", "zip", "png", "jpg", "jpeg", "webp"}


def _id_profesor_actual():
    return get_jwt().get("id_referencia")


def _es_admin():
    return get_jwt().get("tipo_usuario") == "admin"


def _grupo_autorizado(id_grupo):
    grupo = CGrupo.query.get(id_grupo)
    if not grupo or _es_admin():
        return grupo
    asignado = DHorario.query.filter_by(
        id_grupo=id_grupo, id_profesor=_id_profesor_actual()
    ).first()
    return grupo if asignado or grupo.id_profesor == _id_profesor_actual() else None


def _horario_autorizado(id_horario, id_grupo=None):
    query = DHorario.query.filter_by(id_horario=id_horario)
    if not _es_admin():
        query = query.filter_by(id_profesor=_id_profesor_actual())
    if id_grupo is not None:
        query = query.filter_by(id_grupo=id_grupo)
    return query.first()


def _archivo_permitido(nombre):
    return "." in nombre and nombre.rsplit(".", 1)[1].lower() in EXTENSIONES_PERMITIDAS


def _calificacion_valida(valor):
    try:
        numero = Decimal(str(valor))
    except (InvalidOperation, TypeError, ValueError):
        return False
    return Decimal("0") <= numero <= Decimal("10")


@profesor_bp.get("/grupos")
@roles_requeridos("profesor", "admin")
def grupos():
    query = CGrupo.query
    if not _es_admin():
        query = query.outerjoin(DHorario, DHorario.id_grupo == CGrupo.id_grupo).filter(
            (DHorario.id_profesor == _id_profesor_actual())
            | (CGrupo.id_profesor == _id_profesor_actual())
        )
    lista = query.distinct().order_by(CGrupo.grupo).all()
    return jsonify([{
        "id_grupo": g.id_grupo, "grupo": g.grupo,
        "id_carrera": g.id_carrera, "id_grado": g.id_grado,
    } for g in lista])


@profesor_bp.get("/grupos/<int:id_grupo>/alumnos")
@roles_requeridos("profesor", "admin")
def alumnos_de_grupo(id_grupo):
    if not _grupo_autorizado(id_grupo):
        return jsonify({"msg": "El grupo no pertenece al profesor autenticado"}), 403
    lista = CAlumno.query.filter_by(id_grupo=id_grupo).all()
    return jsonify([a.to_dict() for a in lista])


@profesor_bp.get("/grupos/<int:id_grupo>/horarios")
@roles_requeridos("profesor", "admin")
def horarios_de_grupo(id_grupo):
    if not _grupo_autorizado(id_grupo):
        return jsonify({"msg": "El grupo no pertenece al profesor autenticado"}), 403
    query = DHorario.query.filter_by(id_grupo=id_grupo)
    if not _es_admin():
        query = query.filter_by(id_profesor=_id_profesor_actual())
    horarios = query.all()
    resultado = []
    for horario in horarios:
        materia = CMateria.query.get(horario.id_materias) if horario.id_materias else None
        resultado.append({
            "id_horario": horario.id_horario,
            "id_materia": horario.id_materias,
            "materia": materia.nombre if materia else f"Horario {horario.id_horario}",
        })
    return jsonify(resultado)


@profesor_bp.get("/grupos/<int:id_grupo>/materias")
@roles_requeridos("profesor", "admin")
def materias_de_grupo(id_grupo):
    grupo = _grupo_autorizado(id_grupo)
    if not grupo:
        return jsonify({"msg": "El grupo no pertenece al profesor autenticado"}), 403
    horarios_query = DHorario.query.filter_by(id_grupo=id_grupo)
    if not _es_admin():
        horarios_query = horarios_query.filter_by(id_profesor=_id_profesor_actual())
    ids_materia = {h.id_materias for h in horarios_query.all() if h.id_materias}
    if ids_materia:
        materias = CMateria.query.filter(CMateria.id_materias.in_(ids_materia)).order_by(CMateria.nombre).all()
    else:
        materias = CMateria.query.filter_by(
            id_carrera=grupo.id_carrera, id_grado=grupo.id_grado
        ).order_by(CMateria.nombre).all()
    return jsonify([{"id_materia": m.id_materias, "materia": m.nombre} for m in materias])


# ---------------------------------------------------------------- Calificaciones
@profesor_bp.get("/calificaciones")
@roles_requeridos("profesor", "admin")
def ver_calificaciones():
    id_grupo = request.args.get("id_grupo", type=int)
    id_materia = request.args.get("id_materia", type=int)
    id_profesor = _id_profesor_actual()

    query = DCalificacion.query
    if not _es_admin():
        query = query.filter_by(id_profesor=id_profesor)
    if id_materia:
        query = query.filter_by(id_materia=id_materia)

    registros = query.all()
    if id_grupo:
        if not _grupo_autorizado(id_grupo):
            return jsonify({"msg": "El grupo no pertenece al profesor autenticado"}), 403
        ids_alumnos_grupo = {a.id_alumno for a in CAlumno.query.filter_by(id_grupo=id_grupo).all()}
        registros = [r for r in registros if r.id_alumnos in ids_alumnos_grupo]

    resultado = []
    for r in registros:
        alumno = CAlumno.query.get(r.id_alumnos)
        resultado.append({
            "id_calificacion": r.id_calificacion,
            "id_alumno": r.id_alumnos,
            "alumno": alumno.nombre_completo() if alumno else "?",
            "periodo": r.periodo,
            "calificacion": float(r.calificacion) if r.calificacion is not None else None,
        })
    return jsonify(resultado)


@profesor_bp.post("/calificaciones")
@roles_requeridos("profesor")
def capturar_calificacion():
    """Crea o actualiza la calificación de un alumno en una materia/periodo."""
    data = request.get_json(silent=True) or {}
    id_alumno = data.get("id_alumno")
    id_materia = data.get("id_materia")
    periodo = data.get("periodo", "General")
    calificacion = data.get("calificacion")
    id_profesor = _id_profesor_actual()

    alumno = CAlumno.query.get(id_alumno) if id_alumno is not None else None
    if not alumno or calificacion is None:
        return jsonify({"msg": "id_alumno y calificacion son requeridos"}), 400
    if not _grupo_autorizado(alumno.id_grupo):
        return jsonify({"msg": "El alumno no pertenece a un grupo del profesor"}), 403
    if not _calificacion_valida(calificacion):
        return jsonify({"msg": "La calificación debe estar entre 0 y 10"}), 400
    if id_materia is not None:
        if not CMateria.query.get(id_materia):
            return jsonify({"msg": "Materia no encontrada"}), 404
        horarios_grupo = DHorario.query.filter_by(
            id_profesor=id_profesor, id_grupo=alumno.id_grupo
        )
        if horarios_grupo.first() and not horarios_grupo.filter_by(id_materias=id_materia).first():
            return jsonify({"msg": "La materia no está asignada al profesor en este grupo"}), 403

    registro = DCalificacion.query.filter_by(
        id_alumnos=id_alumno, id_materia=id_materia, periodo=periodo, id_profesor=id_profesor
    ).first()

    if registro:
        registro.calificacion = calificacion
        registro.fecha_captura = datetime.utcnow()
    else:
        registro = DCalificacion(
            id_alumnos=id_alumno, id_materia=id_materia, periodo=periodo,
            calificacion=calificacion, id_profesor=id_profesor,
        )
        db.session.add(registro)

    db.session.commit()
    return jsonify({"msg": "Calificación guardada", "id_calificacion": registro.id_calificacion}), 201


# ---------------------------------------------------------------- Tareas
@profesor_bp.get("/tareas")
@roles_requeridos("profesor", "admin")
def listar_tareas():
    id_profesor = _id_profesor_actual()
    query = Tarea.query
    if not _es_admin():
        query = query.filter_by(id_profesor=id_profesor)
    lista = query.order_by(Tarea.fecha_entrega.desc()).all()
    return jsonify([t.to_dict() for t in lista])


@profesor_bp.post("/tareas")
@roles_requeridos("profesor")
def crear_tarea():
    id_profesor = _id_profesor_actual()
    titulo = request.form.get("titulo")
    descripcion = request.form.get("descripcion", "")
    id_materia = request.form.get("id_materia", type=int)
    id_grupo = request.form.get("id_grupo", type=int)
    fecha_entrega = request.form.get("fecha_entrega")  # ISO string
    archivo = request.files.get("archivo")

    if not (titulo and id_materia and id_grupo and fecha_entrega):
        return jsonify({"msg": "titulo, id_materia, id_grupo y fecha_entrega son requeridos"}), 400
    if not _grupo_autorizado(id_grupo):
        return jsonify({"msg": "El grupo no pertenece al profesor autenticado"}), 403
    if not CMateria.query.get(id_materia):
        return jsonify({"msg": "Materia no encontrada"}), 404
    horarios_grupo = DHorario.query.filter_by(id_profesor=id_profesor, id_grupo=id_grupo)
    if horarios_grupo.first() and not horarios_grupo.filter_by(id_materias=id_materia).first():
        return jsonify({"msg": "La materia no está asignada al profesor en este grupo"}), 403
    fecha_entrega_valida = _fecha_hora_valida(fecha_entrega)
    if fecha_entrega_valida is None:
        return jsonify({"msg": "fecha_entrega debe tener formato ISO válido"}), 400

    ruta_guardada = None
    if archivo:
        if not archivo.filename or not _archivo_permitido(archivo.filename):
            return jsonify({"msg": "Tipo de archivo no permitido"}), 400
        nombre_seguro = secure_filename(archivo.filename)
        nombre_final = f"tarea_{id_profesor}_{int(datetime.utcnow().timestamp())}_{nombre_seguro}"
        archivo.save(os.path.join(current_app.config["UPLOAD_FOLDER"], nombre_final))
        ruta_guardada = nombre_final

    tarea = Tarea(
        id_materia=id_materia, id_profesor=id_profesor, id_grupo=id_grupo,
        titulo=titulo, descripcion=descripcion, archivo_adjunto=ruta_guardada,
        fecha_entrega=fecha_entrega_valida,
    )
    db.session.add(tarea)
    db.session.commit()
    return jsonify(tarea.to_dict()), 201


@profesor_bp.get("/tareas/<int:id_tarea>/entregas")
@roles_requeridos("profesor")
def ver_entregas(id_tarea):
    tarea = Tarea.query.filter_by(
        id_tarea=id_tarea, id_profesor=_id_profesor_actual()
    ).first()
    if not tarea:
        return jsonify({"msg": "Tarea no encontrada o no autorizada"}), 404
    entregas = EntregaTarea.query.filter_by(id_tarea=id_tarea).all()
    resultado = []
    for e in entregas:
        alumno = CAlumno.query.get(e.id_alumno)
        item = e.to_dict()
        item["alumno"] = alumno.nombre_completo() if alumno else "?"
        resultado.append(item)
    return jsonify(resultado)


@profesor_bp.put("/entregas/<int:id_entrega>/calificar")
@roles_requeridos("profesor")
def calificar_entrega(id_entrega):
    data = request.get_json(silent=True) or {}
    entrega = EntregaTarea.query.join(Tarea).filter(
        EntregaTarea.id_entrega == id_entrega,
        Tarea.id_profesor == _id_profesor_actual(),
    ).first()
    if not entrega:
        return jsonify({"msg": "Entrega no encontrada o no autorizada"}), 404
    calificacion = data.get("calificacion")
    if not _calificacion_valida(calificacion):
        return jsonify({"msg": "La calificación debe estar entre 0 y 10"}), 400
    entrega.calificacion = calificacion
    entrega.retroalimentacion = data.get("retroalimentacion", "")
    entrega.estatus = "calificada"
    db.session.commit()
    return jsonify(entrega.to_dict())


# ---------------------------------------------------------------- Asistencia
@profesor_bp.get("/asistencia")
@roles_requeridos("profesor", "admin")
def ver_asistencia():
    id_horario = request.args.get("id_horario", type=int)
    fecha = request.args.get("fecha")  # YYYY-MM-DD
    query = Asistencia.query
    if not _es_admin():
        query = query.filter_by(id_profesor=_id_profesor_actual())
    if id_horario:
        if not _horario_autorizado(id_horario):
            return jsonify({"msg": "Horario no autorizado"}), 403
        query = query.filter_by(id_horario=id_horario)
    if fecha:
        fecha_valida = _fecha_valida(fecha)
        if fecha_valida is None:
            return jsonify({"msg": "La fecha debe usar el formato YYYY-MM-DD"}), 400
        query = query.filter_by(fecha=fecha_valida)
    return jsonify([a.to_dict() for a in query.all()])


@profesor_bp.post("/asistencia")
@roles_requeridos("profesor")
def tomar_asistencia():
    """
    Recibe una lista para pasar lista de un grupo completo en una fecha:
    { "id_horario": 3, "fecha": "2026-07-14",
      "registros": [{"id_alumno": 1, "estatus": "presente"}, ...] }
    """
    data = request.get_json(silent=True) or {}
    id_horario = data.get("id_horario")
    fecha = data.get("fecha")
    registros = data.get("registros", [])
    id_profesor = _id_profesor_actual()

    if not (id_horario and fecha and registros):
        return jsonify({"msg": "id_horario, fecha y registros son requeridos"}), 400

    horario = _horario_autorizado(id_horario)
    if not horario or not _grupo_autorizado(horario.id_grupo):
        return jsonify({"msg": "Horario no autorizado"}), 403
    fecha_valida = _fecha_valida(fecha)
    if fecha_valida is None:
        return jsonify({"msg": "La fecha debe usar el formato YYYY-MM-DD"}), 400

    ids_alumnos = {a.id_alumno for a in CAlumno.query.filter_by(id_grupo=horario.id_grupo).all()}
    if not registros or any(r.get("id_alumno") not in ids_alumnos for r in registros):
        return jsonify({"msg": "La lista contiene alumnos ajenos al grupo del horario"}), 403
    if any(r.get("estatus", "presente") not in ESTATUS_ASISTENCIA for r in registros):
        return jsonify({"msg": "Estatus de asistencia no válido"}), 400

    guardados = []
    for r in registros:
        existente = Asistencia.query.filter_by(
            id_alumno=r["id_alumno"], id_horario=id_horario,
            id_profesor=id_profesor, fecha=fecha_valida
        ).first()
        if existente:
            existente.estatus = r.get("estatus", "presente")
        else:
            existente = Asistencia(
                id_alumno=r["id_alumno"], id_horario=id_horario, id_profesor=id_profesor,
                fecha=fecha_valida, estatus=r.get("estatus", "presente"),
            )
            db.session.add(existente)
        guardados.append(existente)

    db.session.commit()
    return jsonify([a.to_dict() for a in guardados]), 201


def _fecha_valida(valor):
    try:
        return date.fromisoformat(valor)
    except (TypeError, ValueError):
        return None


def _fecha_hora_valida(valor):
    try:
        return datetime.fromisoformat(valor)
    except (TypeError, ValueError):
        return None
