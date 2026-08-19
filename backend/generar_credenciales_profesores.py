"""Crea o restablece una cuenta para cada profesor y exporta sus credenciales."""
import argparse
import csv
import os
import re
import secrets
import string
import tempfile

from app import create_app
from extensions import bcrypt, db
from models import CProfesor, Usuario


def generar_password(longitud=12):
    alfabeto = string.ascii_letters + string.digits
    return "".join(secrets.choice(alfabeto) for _ in range(longitud))


def username_base(profesor):
    clave = re.sub(r"[^a-zA-Z0-9._-]", "", (profesor.clave_tutor or "").strip().lower())
    return f"prof.{clave}" if clave else f"prof.{profesor.id_profesor}"


def username_disponible(base, id_profesor, ocupados):
    candidato = base
    consecutivo = 2
    while candidato in ocupados and ocupados[candidato] != ("profesor", id_profesor):
        candidato = f"{base}.{consecutivo}"
        consecutivo += 1
    return candidato


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("salida", help="Ruta del CSV de credenciales")
    args = parser.parse_args()

    app = create_app()
    credenciales = []
    nuevos = 0
    restablecidos = 0

    with app.app_context():
        profesores = CProfesor.query.order_by(CProfesor.id_profesor).all()
        ocupados = {
            usuario.username: (usuario.tipo_usuario, usuario.id_referencia)
            for usuario in Usuario.query.all()
        }

        try:
            for profesor in profesores:
                usuario = Usuario.query.filter_by(
                    tipo_usuario="profesor", id_referencia=profesor.id_profesor
                ).first()
                password = generar_password()

                if usuario:
                    username = usuario.username
                    restablecidos += 1
                else:
                    username = username_disponible(
                        username_base(profesor), profesor.id_profesor, ocupados
                    )
                    usuario = Usuario(
                        username=username,
                        tipo_usuario="profesor",
                        id_referencia=profesor.id_profesor,
                    )
                    db.session.add(usuario)
                    ocupados[username] = ("profesor", profesor.id_profesor)
                    nuevos += 1

                usuario.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
                usuario.activo = True
                credenciales.append((
                    profesor.clave_tutor or "",
                    profesor.nombre_completo(),
                    username,
                    password,
                ))

            db.session.flush()

            directorio = os.path.abspath(os.path.dirname(args.salida) or ".")
            os.makedirs(directorio, exist_ok=True)
            descriptor, temporal = tempfile.mkstemp(prefix="credenciales_profesores_", suffix=".csv", dir=directorio)
            try:
                with os.fdopen(descriptor, "w", newline="", encoding="utf-8-sig") as archivo:
                    writer = csv.writer(archivo)
                    writer.writerow(["clave_tutor", "nombre", "username", "password"])
                    writer.writerows(credenciales)
                db.session.commit()
                os.replace(temporal, os.path.abspath(args.salida))
            except Exception:
                if os.path.exists(temporal):
                    os.remove(temporal)
                raise
        except Exception:
            db.session.rollback()
            raise

        verificadas = 0
        for _, _, username, password in credenciales:
            usuario = Usuario.query.filter_by(username=username, activo=True).first()
            verificadas += bool(
                usuario and bcrypt.check_password_hash(usuario.password_hash, password)
            )

        print(f"Profesores procesados: {len(profesores)}")
        print(f"Cuentas nuevas: {nuevos}")
        print(f"Cuentas restablecidas: {restablecidos}")
        print(f"Credenciales verificadas: {verificadas}")
        print(f"CSV: {os.path.abspath(args.salida)}")


if __name__ == "__main__":
    main()
