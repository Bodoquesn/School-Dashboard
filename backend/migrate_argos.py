"""Migra descriptores y eventos de ARGOS al Portal Escolar por matrícula."""
import argparse
import json
import os

from dotenv import dotenv_values
from sqlalchemy import create_engine, text

from app import app
from extensions import db
from models import CAlumno, EventoBiometrico, RostroAlumno


def cargar_fuente(ruta_env):
    url = dotenv_values(ruta_env).get("DATABASE_URL")
    if not url:
        raise RuntimeError("El .env de ARGOS no contiene DATABASE_URL")
    return create_engine(url, pool_pre_ping=True)


def normalizar_descriptor(valor):
    return json.loads(valor) if isinstance(valor, str) else valor


def migrar(ruta_env, dry_run=False):
    engine = cargar_fuente(ruta_env)
    with engine.connect() as conexion:
        estudiantes = conexion.execute(text("SELECT id, enrollment_id FROM students")).mappings().all()
        rostros = conexion.execute(text(
            "SELECT student_id, engine_name, embedding FROM face_embeddings"
        )).mappings().all()
        eventos = conexion.execute(text(
            "SELECT student_id, recognized_at, confidence, camera_name, event_type FROM attendances"
        )).mappings().all()
    engine.dispose()

    matricula_por_id = {fila["id"]: fila["enrollment_id"] for fila in estudiantes}
    resumen = {
        "alumnos_fuente": len(estudiantes),
        "alumnos_coincidentes": 0,
        "rostros_por_migrar": 0,
        "eventos_por_migrar": 0,
        "alumnos_sin_coincidencia": 0,
    }

    with app.app_context():
        destino_por_origen = {}
        for id_origen, matricula in matricula_por_id.items():
            alumno = CAlumno.query.filter_by(matricula=matricula).first()
            if alumno:
                destino_por_origen[id_origen] = alumno
                resumen["alumnos_coincidentes"] += 1
            else:
                resumen["alumnos_sin_coincidencia"] += 1

        for fila in rostros:
            alumno = destino_por_origen.get(fila["student_id"])
            if not alumno:
                continue
            resumen["rostros_por_migrar"] += 1
            if dry_run:
                continue
            rostro = RostroAlumno.query.filter_by(id_alumno=alumno.id_alumno).first()
            if not rostro:
                rostro = RostroAlumno(id_alumno=alumno.id_alumno)
                db.session.add(rostro)
            rostro.motor = fila["engine_name"]
            rostro.descriptor = normalizar_descriptor(fila["embedding"])

        for fila in eventos:
            alumno = destino_por_origen.get(fila["student_id"])
            if not alumno:
                continue
            existe = EventoBiometrico.query.filter_by(
                id_alumno=alumno.id_alumno,
                reconocido_en=fila["recognized_at"],
                tipo_evento=fila["event_type"],
            ).first()
            if existe:
                continue
            resumen["eventos_por_migrar"] += 1
            if not dry_run:
                db.session.add(EventoBiometrico(
                    id_alumno=alumno.id_alumno,
                    reconocido_en=fila["recognized_at"],
                    confianza=fila["confidence"],
                    camara=fila["camera_name"],
                    tipo_evento=fila["event_type"],
                ))

        db.session.rollback() if dry_run else db.session.commit()
    return resumen


def main():
    parser = argparse.ArgumentParser(description="Migra datos biométricos desde ARGOS")
    parser.add_argument("source_env", help="Ruta al backend/.env de ARGOS")
    parser.add_argument("--dry-run", action="store_true", help="Analiza sin guardar cambios")
    args = parser.parse_args()
    if not os.path.isfile(args.source_env):
        parser.error("No se encontró el archivo .env indicado")
    resumen = migrar(args.source_env, args.dry_run)
    print("SIMULACIÓN COMPLETADA" if args.dry_run else "MIGRACIÓN COMPLETADA")
    for clave, valor in resumen.items():
        print(f"{clave}: {valor}")


if __name__ == "__main__":
    main()
