import os
from datetime import datetime
from flask import Blueprint, request, jsonify, send_file, current_app
from flask_jwt_extended import get_jwt, get_jwt_identity
from werkzeug.utils import secure_filename

from extensions import db
from models import (
    CAlumno, CProfesor, CMateria, DCalificacion, DHorario,
    Tarea, EntregaTarea, CGrupo,
)
from utils import roles_requeridos

alumno_bp = Blueprint("alumno", __name__, url_prefix="/api/alumno")


def _id_alumno_actual():
    return get_jwt().get("id_referencia")


@alumno_bp.get("/calificaciones")
@roles_requeridos("alumno")
def calificaciones():
    id_alumno = _id_alumno_actual()
    registros = DCalificacion.query.filter_by(id_alumnos=id_alumno).all()
    resultado = []
    for r in registros:
        materia = CMateria.query.get(r.id_materia) if r.id_materia else None
        resultado.append({
            "id_calificacion": r.id_calificacion,
            "materia": materia.nombre if materia else "General",
            "periodo": r.periodo,
            "calificacion": float(r.calificacion) if r.calificacion is not None else None,
            "fecha_captura": r.fecha_captura.isoformat() if r.fecha_captura else None,
        })
    return jsonify(resultado)


@alumno_bp.get("/boleta")
@roles_requeridos("alumno")
def boleta_pdf():
    """Genera y descarga la boleta de calificaciones en PDF."""
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    id_alumno = _id_alumno_actual()
    alumno = CAlumno.query.get(id_alumno)
    if not alumno:
        return jsonify({"msg": "Alumno no encontrado"}), 404

    registros = DCalificacion.query.filter_by(id_alumnos=id_alumno).all()

    filename = f"boleta_{id_alumno}_{int(datetime.utcnow().timestamp())}.pdf"
    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], filename)

    c = canvas.Canvas(filepath, pagesize=letter)
    width, height = letter
    y = height - 60

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, y, "Boleta de Calificaciones")
    y -= 30
    c.setFont("Helvetica", 11)
    c.drawString(50, y, f"Alumno: {alumno.nombre_completo()}")
    y -= 16
    c.drawString(50, y, f"Fecha de emisión: {datetime.utcnow().strftime('%d/%m/%Y')}")
    y -= 30

    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "Materia")
    c.drawString(300, y, "Periodo")
    c.drawString(450, y, "Calificación")
    y -= 16
    c.line(50, y, 550, y)
    y -= 14

    c.setFont("Helvetica", 10)
    for r in registros:
        materia = CMateria.query.get(r.id_materia) if r.id_materia else None
        c.drawString(50, y, materia.nombre if materia else "General")
        c.drawString(300, y, r.periodo or "-")
        c.drawString(450, y, str(r.calificacion) if r.calificacion is not None else "-")
        y -= 16
        if y < 60:
            c.showPage()
            y = height - 60

    c.save()
    return send_file(filepath, as_attachment=True, download_name=f"boleta_{alumno.nombre}.pdf")


@alumno_bp.get("/materias")
@roles_requeridos("alumno")
def materias():
    id_alumno = _id_alumno_actual()
    alumno = CAlumno.query.get(id_alumno)
    if not alumno:
        return jsonify([])
    lista = CMateria.query.filter_by(id_carrera=alumno.id_carrera, id_grado=alumno.id_grado).all()
    return jsonify([{"id_materias": m.id_materias, "nombre": m.nombre, "foto": m.foto} for m in lista])


@alumno_bp.get("/profesores")
@roles_requeridos("alumno")
def profesores():
    id_alumno = _id_alumno_actual()
    alumno = CAlumno.query.get(id_alumno)
    if not alumno:
        return jsonify([])
    lista = CProfesor.query.filter_by(id_grupo=alumno.id_grupo).all()
    return jsonify([p.to_dict() for p in lista])


@alumno_bp.get("/companeros")
@roles_requeridos("alumno")
def companeros():
    id_alumno = _id_alumno_actual()
    alumno = CAlumno.query.get(id_alumno)
    if not alumno:
        return jsonify([])
    lista = CAlumno.query.filter_by(id_grupo=alumno.id_grupo).filter(CAlumno.id_alumno != id_alumno).all()
    return jsonify([a.to_dict() for a in lista])


@alumno_bp.get("/tareas")
@roles_requeridos("alumno")
def tareas():
    id_alumno = _id_alumno_actual()
    alumno = CAlumno.query.get(id_alumno)
    if not alumno:
        return jsonify([])
    lista = Tarea.query.filter_by(id_grupo=alumno.id_grupo).order_by(Tarea.fecha_entrega.asc()).all()
    resultado = []
    for t in lista:
        entrega = EntregaTarea.query.filter_by(id_tarea=t.id_tarea, id_alumno=id_alumno).first()
        item = t.to_dict()
        item["mi_entrega"] = entrega.to_dict() if entrega else None
        resultado.append(item)
    return jsonify(resultado)


@alumno_bp.post("/tareas/<int:id_tarea>/entregar")
@roles_requeridos("alumno")
def entregar_tarea(id_tarea):
    id_alumno = _id_alumno_actual()
    tarea = Tarea.query.get_or_404(id_tarea)

    comentario = request.form.get("comentario", "")
    archivo = request.files.get("archivo")
    ruta_guardada = None

    if archivo:
        nombre_seguro = secure_filename(archivo.filename)
        nombre_final = f"entrega_{id_tarea}_{id_alumno}_{nombre_seguro}"
        ruta_guardada = os.path.join(current_app.config["UPLOAD_FOLDER"], nombre_final)
        archivo.save(ruta_guardada)
        ruta_guardada = nombre_final

    estatus = "atrasada" if datetime.utcnow() > tarea.fecha_entrega else "entregada"

    entrega = EntregaTarea.query.filter_by(id_tarea=id_tarea, id_alumno=id_alumno).first()
    if entrega:
        entrega.archivo = ruta_guardada or entrega.archivo
        entrega.comentario = comentario
        entrega.fecha_entrega = datetime.utcnow()
        entrega.estatus = estatus
    else:
        entrega = EntregaTarea(
            id_tarea=id_tarea, id_alumno=id_alumno, archivo=ruta_guardada,
            comentario=comentario, estatus=estatus,
        )
        db.session.add(entrega)

    db.session.commit()
    return jsonify(entrega.to_dict()), 201
