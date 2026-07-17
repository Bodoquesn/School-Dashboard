import os
from datetime import datetime
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


def _id_profesor_actual():
    return get_jwt().get("id_referencia")


@profesor_bp.get("/grupos")
@roles_requeridos("profesor")
def grupos():
    id_profesor = _id_profesor_actual()
    lista = CGrupo.query.filter_by(id_profesor=id_profesor).all()
    return jsonify([{"id_grupo": g.id_grupo, "grupo": g.grupo, "id_carrera": g.id_carrera} for g in lista])


@profesor_bp.get("/grupos/<int:id_grupo>/alumnos")
@roles_requeridos("profesor")
def alumnos_de_grupo(id_grupo):
    lista = CAlumno.query.filter_by(id_grupo=id_grupo).all()
    return jsonify([a.to_dict() for a in lista])


# ---------------------------------------------------------------- Calificaciones
@profesor_bp.get("/calificaciones")
@roles_requeridos("profesor")
def ver_calificaciones():
    id_grupo = request.args.get("id_grupo", type=int)
    id_materia = request.args.get("id_materia", type=int)
    id_profesor = _id_profesor_actual()

    query = DCalificacion.query.filter_by(id_profesor=id_profesor)
    if id_materia:
        query = query.filter_by(id_materia=id_materia)

    registros = query.all()
    if id_grupo:
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

    if id_alumno is None or calificacion is None:
        return jsonify({"msg": "id_alumno y calificacion son requeridos"}), 400

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
@roles_requeridos("profesor")
def listar_tareas():
    id_profesor = _id_profesor_actual()
    lista = Tarea.query.filter_by(id_profesor=id_profesor).order_by(Tarea.fecha_entrega.desc()).all()
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

    ruta_guardada = None
    if archivo:
        nombre_seguro = secure_filename(archivo.filename)
        nombre_final = f"tarea_{id_profesor}_{int(datetime.utcnow().timestamp())}_{nombre_seguro}"
        archivo.save(os.path.join(current_app.config["UPLOAD_FOLDER"], nombre_final))
        ruta_guardada = nombre_final

    tarea = Tarea(
        id_materia=id_materia, id_profesor=id_profesor, id_grupo=id_grupo,
        titulo=titulo, descripcion=descripcion, archivo_adjunto=ruta_guardada,
        fecha_entrega=datetime.fromisoformat(fecha_entrega),
    )
    db.session.add(tarea)
    db.session.commit()
    return jsonify(tarea.to_dict()), 201


@profesor_bp.get("/tareas/<int:id_tarea>/entregas")
@roles_requeridos("profesor")
def ver_entregas(id_tarea):
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
    entrega = EntregaTarea.query.get_or_404(id_entrega)
    entrega.calificacion = data.get("calificacion")
    entrega.retroalimentacion = data.get("retroalimentacion", "")
    entrega.estatus = "calificada"
    db.session.commit()
    return jsonify(entrega.to_dict())


# ---------------------------------------------------------------- Asistencia
@profesor_bp.get("/asistencia")
@roles_requeridos("profesor")
def ver_asistencia():
    id_horario = request.args.get("id_horario", type=int)
    fecha = request.args.get("fecha")  # YYYY-MM-DD
    query = Asistencia.query.filter_by(id_profesor=_id_profesor_actual())
    if id_horario:
        query = query.filter_by(id_horario=id_horario)
    if fecha:
        query = query.filter_by(fecha=fecha)
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

    guardados = []
    for r in registros:
        existente = Asistencia.query.filter_by(
            id_alumno=r["id_alumno"], id_horario=id_horario, fecha=fecha
        ).first()
        if existente:
            existente.estatus = r.get("estatus", "presente")
        else:
            existente = Asistencia(
                id_alumno=r["id_alumno"], id_horario=id_horario, id_profesor=id_profesor,
                fecha=fecha, estatus=r.get("estatus", "presente"),
            )
            db.session.add(existente)
        guardados.append(existente)

    db.session.commit()
    return jsonify([a.to_dict() for a in guardados]), 201
