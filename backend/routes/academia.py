from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt
from sqlalchemy import distinct, func

from extensions import db
from models import (
    CAlumno, CCampus, CCarrera, CGrado, CGrupo, CMateria, CProfesor,
    DHorario,
)
from utils import roles_requeridos


academia_bp = Blueprint("academia", __name__, url_prefix="/api/academia")


def _asignaciones_query():
    return (
        db.session.query(
            CProfesor.id_profesor,
            CProfesor.nombre,
            CProfesor.apellido_paterno,
            CProfesor.apellido_materno,
            CGrupo.id_grupo,
            CGrupo.grupo,
            CCarrera.id_carrera,
            CCarrera.nombrecarrera,
            CGrado.Grado,
            CMateria.id_materias,
            CMateria.nombre.label("materia"),
            CCampus.nombrecampus,
            func.count(distinct(CAlumno.id_alumno)).label("alumnos"),
        )
        .join(DHorario, DHorario.id_profesor == CProfesor.id_profesor)
        .join(CGrupo, CGrupo.id_grupo == DHorario.id_grupo)
        .join(CCarrera, CCarrera.id_carrera == CGrupo.id_carrera)
        .join(CGrado, CGrado.id_grado == CGrupo.id_grado)
        .join(CMateria, CMateria.id_materias == DHorario.id_materias)
        .outerjoin(CCampus, CCampus.id_campus == CGrupo.id_campus)
        .outerjoin(CAlumno, CAlumno.id_grupo == CGrupo.id_grupo)
        .group_by(
            CProfesor.id_profesor,
            CProfesor.nombre,
            CProfesor.apellido_paterno,
            CProfesor.apellido_materno,
            CGrupo.id_grupo,
            CGrupo.grupo,
            CCarrera.id_carrera,
            CCarrera.nombrecarrera,
            CGrado.Grado,
            CMateria.id_materias,
            CMateria.nombre,
            CCampus.nombrecampus,
        )
    )


def _nombre_profesor(fila):
    return " ".join(filter(None, [fila.nombre, fila.apellido_paterno, fila.apellido_materno]))


def _cuatrimestre(valor):
    if valor is None:
        return None
    numero = float(valor)
    return int(numero) if numero.is_integer() else numero


def _serializar_asignacion(fila):
    return {
        "id_profesor": fila.id_profesor,
        "profesor": _nombre_profesor(fila),
        "id_grupo": fila.id_grupo,
        "grupo": fila.grupo or str(fila.id_grupo),
        "id_carrera": fila.id_carrera,
        "carrera": fila.nombrecarrera,
        "cuatrimestre": _cuatrimestre(fila.Grado),
        "id_materia": fila.id_materias,
        "materia": fila.materia,
        "campus": fila.nombrecampus,
        "alumnos": fila.alumnos,
    }


@academia_bp.get("/resumen")
@roles_requeridos("profesor", "admin")
def resumen_academico():
    claims = get_jwt()
    tipo = claims.get("tipo_usuario")
    id_profesor = claims.get("id_referencia")

    query = _asignaciones_query()
    if tipo == "profesor":
        query = query.filter(CProfesor.id_profesor == id_profesor)

    filas = query.order_by(
        CCarrera.nombrecarrera, CGrado.Grado, CGrupo.grupo, CMateria.nombre
    ).all()
    asignaciones = [_serializar_asignacion(fila) for fila in filas]

    carreras = sorted({a["id_carrera"] for a in asignaciones})
    grupos = {a["id_grupo"] for a in asignaciones}
    materias = {a["id_materia"] for a in asignaciones}
    profesores = {a["id_profesor"] for a in asignaciones}

    companeros = []
    if tipo == "profesor" and carreras:
        colegas = (
            db.session.query(CProfesor)
            .join(DHorario, DHorario.id_profesor == CProfesor.id_profesor)
            .join(CGrupo, CGrupo.id_grupo == DHorario.id_grupo)
            .filter(
                CGrupo.id_carrera.in_(carreras),
                CProfesor.id_profesor != id_profesor,
            )
            .distinct()
            .order_by(CProfesor.nombre, CProfesor.apellido_paterno)
            .all()
        )
        companeros = [profesor.to_dict() for profesor in colegas]

    total_alumnos = (
        CAlumno.query.filter(CAlumno.id_grupo.in_(grupos)).count() if grupos else 0
    )
    return jsonify({
        "alcance": tipo,
        "totales": {
            "profesores": len(profesores),
            "grupos": len(grupos),
            "carreras": len(carreras),
            "materias": len(materias),
            "alumnos": total_alumnos,
        },
        "asignaciones": asignaciones,
        "companeros_area": companeros,
    })
