from flask import Blueprint, send_from_directory, current_app
from datetime import datetime

from flask import jsonify
from flask_jwt_extended import jwt_required, get_jwt
from sqlalchemy import func

from extensions import db
from models import (
    Asistencia, CAlumno, CGrupo, CMateria, CProfesor, DCalificacion,
    DHorario, EntregaTarea, Tarea,
)

common_bp = Blueprint("common", __name__, url_prefix="/api")


@common_bp.get("/archivos/<path:nombre_archivo>")
@jwt_required()
def descargar_archivo(nombre_archivo):
    """Sirve fotos, tareas y entregas subidas (requiere estar logueado)."""
    if not _archivo_autorizado(nombre_archivo):
        return jsonify({"msg": "Archivo no encontrado o no autorizado"}), 404
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], nombre_archivo)


@common_bp.get("/salud")
def salud():
    return {"status": "ok"}


def _archivo_autorizado(nombre_archivo):
    claims = get_jwt()
    tipo = claims.get("tipo_usuario")
    referencia = claims.get("id_referencia")
    nombre_normalizado = nombre_archivo.replace("\\", "/")

    if tipo == "admin":
        return True

    # Las fotos de perfil se muestran a miembros autenticados del portal.
    if nombre_normalizado.startswith("perfiles/perfil_"):
        return True

    tarea = Tarea.query.filter_by(archivo_adjunto=nombre_archivo).first()
    if tarea:
        if tipo == "profesor":
            return tarea.id_profesor == referencia
        if tipo == "alumno":
            alumno = CAlumno.query.get(referencia)
            return bool(alumno and alumno.id_grupo == tarea.id_grupo)
        return False

    entrega = EntregaTarea.query.filter_by(archivo=nombre_archivo).first()
    if entrega:
        if tipo == "alumno":
            return entrega.id_alumno == referencia
        if tipo == "profesor":
            tarea_entrega = Tarea.query.get(entrega.id_tarea)
            return bool(tarea_entrega and tarea_entrega.id_profesor == referencia)
        return False

    # Compatibilidad con fotos históricas guardadas antes de usar /perfiles.
    return bool(
        CAlumno.query.filter_by(foto=nombre_archivo).first()
        or CProfesor.query.filter_by(foto=nombre_archivo).first()
    )


@common_bp.get("/reportes/resumen")
@jwt_required()
def resumen_reportes():
    claims = get_jwt()
    tipo = claims.get("tipo_usuario")
    id_referencia = claims.get("id_referencia")
    if tipo == "alumno":
        return jsonify(_reporte_alumno(id_referencia))
    if tipo == "profesor":
        return jsonify(_reporte_profesor(id_referencia))
    if tipo == "admin":
        return jsonify(_reporte_admin())
    return jsonify({"msg": "No hay reportes disponibles para este rol"}), 403


def _reporte_alumno(id_alumno):
    alumno = CAlumno.query.get(id_alumno)
    if not alumno:
        return {"tarjetas": [], "promedios_materia": [], "asistencia": []}

    calificaciones = DCalificacion.query.filter_by(id_alumnos=id_alumno).all()
    entregas = EntregaTarea.query.filter_by(id_alumno=id_alumno).count()
    tareas = Tarea.query.filter_by(id_grupo=alumno.id_grupo).count()
    promedio = (
        sum(float(c.calificacion) for c in calificaciones if c.calificacion is not None)
        / max(1, sum(c.calificacion is not None for c in calificaciones))
    )

    promedios = (
        db.session.query(CMateria.nombre, func.avg(DCalificacion.calificacion))
        .join(DCalificacion, DCalificacion.id_materia == CMateria.id_materias)
        .filter(DCalificacion.id_alumnos == id_alumno)
        .group_by(CMateria.id_materias, CMateria.nombre)
        .order_by(CMateria.nombre)
        .all()
    )
    asistencia = (
        db.session.query(Asistencia.estatus, func.count(Asistencia.id_asistencia))
        .filter(Asistencia.id_alumno == id_alumno)
        .group_by(Asistencia.estatus)
        .all()
    )
    pendientes = (
        Tarea.query.filter(Tarea.id_grupo == alumno.id_grupo, Tarea.fecha_entrega >= datetime.utcnow())
        .outerjoin(
            EntregaTarea,
            (EntregaTarea.id_tarea == Tarea.id_tarea) & (EntregaTarea.id_alumno == id_alumno),
        )
        .filter(EntregaTarea.id_entrega.is_(None))
        .count()
    )
    return {
        "tarjetas": [
            {"clave": "promedio", "valor": round(promedio, 2)},
            {"clave": "tareas_entregadas", "valor": entregas},
            {"clave": "tareas_totales", "valor": tareas},
            {"clave": "tareas_pendientes", "valor": pendientes},
        ],
        "promedios_materia": [
            {"materia": nombre, "promedio": round(float(valor), 2)}
            for nombre, valor in promedios if valor is not None
        ],
        "asistencia": [
            {"estatus": estatus, "total": total} for estatus, total in asistencia
        ],
    }


def _reporte_profesor(id_profesor):
    grupos = (
        CGrupo.query.join(DHorario, DHorario.id_grupo == CGrupo.id_grupo)
        .filter(DHorario.id_profesor == id_profesor)
        .distinct()
        .all()
    )
    ids_grupo = [grupo.id_grupo for grupo in grupos]
    estudiantes = CAlumno.query.filter(CAlumno.id_grupo.in_(ids_grupo)).count() if ids_grupo else 0
    tareas = Tarea.query.filter_by(id_profesor=id_profesor).count()
    eventos = Asistencia.query.filter_by(id_profesor=id_profesor).count()

    promedios = (
        db.session.query(CMateria.nombre, func.avg(DCalificacion.calificacion))
        .join(DCalificacion, DCalificacion.id_materia == CMateria.id_materias)
        .filter(DCalificacion.id_profesor == id_profesor)
        .group_by(CMateria.id_materias, CMateria.nombre)
        .order_by(CMateria.nombre)
        .all()
    )
    asistencia = (
        db.session.query(CGrupo.id_grupo, CGrupo.grupo, Asistencia.estatus, func.count(Asistencia.id_asistencia))
        .join(CAlumno, CAlumno.id_grupo == CGrupo.id_grupo)
        .join(Asistencia, Asistencia.id_alumno == CAlumno.id_alumno)
        .filter(CGrupo.id_grupo.in_(ids_grupo), Asistencia.id_profesor == id_profesor)
        .group_by(CGrupo.id_grupo, CGrupo.grupo, Asistencia.estatus)
        .order_by(CGrupo.grupo, Asistencia.estatus)
        .all()
    )
    return {
        "tarjetas": [
            {"clave": "grupos", "valor": len(grupos)},
            {"clave": "estudiantes", "valor": estudiantes},
            {"clave": "tareas_asignadas", "valor": tareas},
            {"clave": "registros_asistencia", "valor": eventos},
        ],
        "promedios_materia": [
            {"materia": nombre, "promedio": round(float(valor), 2)}
            for nombre, valor in promedios if valor is not None
        ],
        "asistencia_grupo": [
            {"id_grupo": id_grupo, "grupo": grupo or str(id_grupo), "estatus": estatus, "total": total}
            for id_grupo, grupo, estatus, total in asistencia
        ],
    }


def _reporte_admin():
    promedios = (
        db.session.query(CMateria.nombre, func.avg(DCalificacion.calificacion))
        .join(DCalificacion, DCalificacion.id_materia == CMateria.id_materias)
        .group_by(CMateria.id_materias, CMateria.nombre)
        .order_by(CMateria.nombre)
        .all()
    )
    asistencia = (
        db.session.query(CGrupo.id_grupo, CGrupo.grupo, Asistencia.estatus, func.count(Asistencia.id_asistencia))
        .join(CAlumno, CAlumno.id_grupo == CGrupo.id_grupo)
        .join(Asistencia, Asistencia.id_alumno == CAlumno.id_alumno)
        .group_by(CGrupo.id_grupo, CGrupo.grupo, Asistencia.estatus)
        .order_by(CGrupo.grupo, Asistencia.estatus)
        .all()
    )
    return {
        "tarjetas": [
            {"clave": "profesores", "valor": CProfesor.query.count()},
            {"clave": "grupos", "valor": CGrupo.query.count()},
            {"clave": "estudiantes", "valor": CAlumno.query.count()},
            {"clave": "materias", "valor": CMateria.query.count()},
        ],
        "promedios_materia": [
            {"materia": nombre, "promedio": round(float(valor), 2)}
            for nombre, valor in promedios if valor is not None
        ],
        "asistencia_grupo": [
            {"id_grupo": id_grupo, "grupo": grupo or str(id_grupo), "estatus": estatus, "total": total}
            for id_grupo, grupo, estatus, total in asistencia
        ],
    }
