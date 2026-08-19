"""
Importa un "concentrado de calificaciones" (como el que exporta UNIDEG) a la
base de datos del dashboard, y genera un usuario + contraseña por cada
alumno.

QUÉ HACE:
  1. Lee el Excel (hoja "concentrado", encabezados en la fila 9).
  2. Ignora alumnos con Estatus = "BAJA DEFINITIVA" (no se importan, no se
     les crea calificación ni usuario).
  3. Crea/actualiza: campus, carreras, grados/grupos, materias, profesores
     (tutores) y alumnos — usando "matricula" / "clave_tutor" como llave
     natural para que puedas volver a correr el script sin duplicar nada.
  4. Inserta/actualiza la calificación FINAL de cada alumno por materia.
  5. Crea un usuario de acceso (tabla `usuarios`) para cada alumno que
     todavía no tenga uno, con username = matrícula en minúsculas y una
     contraseña aleatoria.
  6. Guarda esas contraseñas EN TEXTO PLANO solo una vez, en un CSV local
     (para que se las repartas a los alumnos) — la base de datos solo
     guarda el hash, nunca la contraseña real.

ANTES DE CORRERLO:
  - Ejecuta migrations/001_new_tables.sql y migrations/002_matricula_clave.sql
    en tu base de datos (desde DBeaver).
  - Ten tu backend/.env configurado y apuntando a tu base de datos real.

USO:
    cd backend
    venv\\Scripts\\activate
    python import_excel.py "C:\\ruta\\a\\concentrado_anonimizado.xlsx"

    Parámetros opcionales:
    python import_excel.py archivo.xlsx --periodo "SEPT-DIC 2025" --dry-run

    --dry-run   : NO escribe nada en la base de datos, solo muestra un
                  resumen de lo que haría (alumnos nuevos, materias nuevas,
                  calificaciones a insertar, etc). Úsalo primero.
"""
import argparse
import csv
import re
import secrets
import string
import sys
from datetime import datetime

import pandas as pd

from app import create_app
from extensions import db, bcrypt
from models import (
    CAlumno, CProfesor, CMateria, CEstatus, CCampus, CCarrera, CGrado, CGrupo,
    DCalificacion, DHorario, Usuario,
)

COLUMNAS_ESPERADAS = [
    "Centro", "Matricula", "Nombre Alumno", "Especialidad", "Subsistema",
    "Estatus", "clave Materia", "Materia", "clave Tutor", "nombre Tutor",
    " Parcial1", " Parcial2", " Parcial3", " Final", "tipo Curso", "Plan",
]


def generar_password(longitud=10):
    alfabeto = string.ascii_letters + string.digits
    return "".join(secrets.choice(alfabeto) for _ in range(longitud))


def dividir_nombre(nombre_completo):
    """
    Los reportes de UNIDEG vienen como
    'APELLIDO_PATERNO APELLIDO_MATERNO NOMBRE(S)'.
    Se asume: primeras 2 palabras = apellidos, el resto = nombre(s).
    """
    partes = str(nombre_completo).strip().split()
    if len(partes) >= 3:
        return partes[0].title(), partes[1].title(), " ".join(partes[2:]).title()
    if len(partes) == 2:
        return partes[0].title(), "", partes[1].title()
    return "", "", (partes[0].title() if partes else "")


def parsear_subsistema(subsistema):
    """'5A' -> (grado='5', grupo='A'). Si no matchea el patrón, regresa (subsistema, '')."""
    m = re.match(r"^(\d+)([A-Za-z]*)$", str(subsistema).strip())
    if m:
        return m.group(1), (m.group(2) or "GRAL")
    return str(subsistema), "GRAL"


def cargar_excel(ruta):
    df = pd.read_excel(ruta, sheet_name="concentrado", header=8)
    df = df.dropna(axis=1, how="all")

    faltantes = [c for c in COLUMNAS_ESPERADAS if c not in df.columns]
    if faltantes:
        print(f"AVISO: no se encontraron estas columnas esperadas: {faltantes}")

    # Quita filas basura (pies de página del reporte) sin matrícula
    df = df[df["Matricula"].notna()].copy()

    # Excluye POR COMPLETO a los alumnos dados de baja (todas sus materias)
    matriculas_baja = set(df.loc[df["Estatus"] == "BAJA DEFINITIVA", "Matricula"].unique())
    if matriculas_baja:
        print(f"Excluyendo {len(matriculas_baja)} alumno(s) dado(s) de baja: {sorted(matriculas_baja)}")
    df = df[~df["Matricula"].isin(matriculas_baja)].copy()

    return df


def obtener_o_crear_campus(nombre_centro):
    # "058M - UNIDEG (PLANTEL SAN JOSE ITURBIDE)" -> nombre limpio
    nombre = re.sub(r"^\d+\w*\s*-\s*", "", str(nombre_centro)).strip()
    campus = CCampus.query.filter_by(nombrecampus=nombre).first()
    if not campus:
        campus = CCampus(nombrecampus=nombre, ubicacion_campus="")
        db.session.add(campus)
        db.session.flush()
    return campus


def obtener_o_crear_carrera(nombre_carrera, id_campus):
    carrera = CCarrera.query.filter_by(nombrecarrera=nombre_carrera).first()
    if not carrera:
        carrera = CCarrera(nombrecarrera=nombre_carrera, id_campus=id_campus)
        db.session.add(carrera)
        db.session.flush()
    return carrera


def obtener_o_crear_grado(grado_txt, id_carrera):
    grado = CGrado.query.filter_by(Grado=grado_txt, id_carrera=id_carrera).first()
    if not grado:
        grado = CGrado(Grado=grado_txt, id_carrera=id_carrera)
        db.session.add(grado)
        db.session.flush()
    return grado


def obtener_o_crear_grupo(letra_grupo, id_carrera, id_campus, id_grado):
    grupo = CGrupo.query.filter_by(grupo=letra_grupo, id_carrera=id_carrera, id_grado=id_grado).first()
    if not grupo:
        grupo = CGrupo(grupo=letra_grupo, id_carrera=id_carrera, id_campus=id_campus, id_grado=id_grado)
        db.session.add(grupo)
        db.session.flush()
    return grupo


def obtener_o_crear_estatus(nombre_estatus):
    estatus = CEstatus.query.filter_by(estatus=nombre_estatus).first()
    if not estatus:
        estatus = CEstatus(estatus=nombre_estatus)
        db.session.add(estatus)
        db.session.flush()
    return estatus


def obtener_o_crear_materia(clave, nombre):
    materia = CMateria.query.filter_by(nombre=nombre).first()
    if not materia:
        materia = CMateria(nombre=nombre)
        db.session.add(materia)
        db.session.flush()
    return materia


def obtener_o_crear_profesor(clave_tutor, nombre_tutor):
    clave_tutor = str(clave_tutor) if pd.notna(clave_tutor) else None
    profesor = None
    if clave_tutor:
        profesor = CProfesor.query.filter_by(clave_tutor=clave_tutor).first()
    if not profesor:
        ap, am, nom = dividir_nombre(nombre_tutor)
        profesor = CProfesor(nombre=nom, apellido_paterno=ap, apellido_materno=am, clave_tutor=clave_tutor)
        db.session.add(profesor)
        db.session.flush()
    return profesor


def main():
    parser = argparse.ArgumentParser(description="Importa el concentrado de calificaciones a la base de datos")
    parser.add_argument("excel_path", help="Ruta al archivo .xlsx")
    parser.add_argument("--periodo", default=None, help="Etiqueta del periodo, ej. 'SEPT-DIC 2025'")
    parser.add_argument("--dry-run", action="store_true", help="Solo muestra un resumen, no escribe en la BD")
    parser.add_argument("--credenciales-out", default="credenciales_generadas.csv",
                         help="Archivo CSV donde se guardan usuario/password en texto plano")
    args = parser.parse_args()

    df = cargar_excel(args.excel_path)
    if df.empty:
        print("No hay filas para importar después de filtrar.")
        return

    periodo = args.periodo
    if not periodo:
        # Usa el "Plan" que viene en el Excel como respaldo si no se especifica periodo
        plan = df["Plan"].dropna().mode()
        periodo = f"Plan {int(plan.iloc[0])}" if not plan.empty else "General"

    alumnos_unicos = df.drop_duplicates(subset="Matricula")
    print(f"Alumnos a importar: {len(alumnos_unicos)}")
    print(f"Filas de calificación a procesar: {len(df)}")
    print(f"Periodo asignado a las calificaciones: {periodo}")

    if args.dry_run:
        print("\n--dry-run activo: no se escribió nada en la base de datos.")
        print("Ejemplo de los primeros 5 alumnos que se crearían/actualizarían:")
        for _, row in alumnos_unicos.head(5).iterrows():
            ap, am, nom = dividir_nombre(row["Nombre Alumno"])
            print(f"  - {row['Matricula']}: {nom} {ap} {am}  |  {row['Especialidad']}  |  grupo {row['Subsistema']}")
        return

    app = create_app()
    with app.app_context():
        estatus_inscrito = obtener_o_crear_estatus("INSCRITO")

        credenciales_nuevas = []  # (matricula, nombre, username, password_plano)
        alumnos_creados, alumnos_actualizados = 0, 0
        calificaciones_guardadas = 0

        for _, row in alumnos_unicos.iterrows():
            campus = obtener_o_crear_campus(row["Centro"])
            carrera = obtener_o_crear_carrera(str(row["Especialidad"]).strip(), campus.id_campus)
            grado_txt, letra_grupo = parsear_subsistema(row["Subsistema"])
            grado = obtener_o_crear_grado(grado_txt, carrera.id_carrera)
            grupo = obtener_o_crear_grupo(letra_grupo, carrera.id_carrera, campus.id_campus, grado.id_grado)

            ap, am, nom = dividir_nombre(row["Nombre Alumno"])
            matricula = str(row["Matricula"]).strip()

            alumno = CAlumno.query.filter_by(matricula=matricula).first()
            if not alumno:
                alumno = CAlumno(matricula=matricula)
                db.session.add(alumno)
                alumnos_creados += 1
            else:
                alumnos_actualizados += 1

            alumno.nombre = nom
            alumno.apellido_paterno = ap
            alumno.apellido_materno = am
            alumno.id_campus = campus.id_campus
            alumno.id_carrera = carrera.id_carrera
            alumno.id_grado = grado.id_grado
            alumno.id_grupo = grupo.id_grupo
            alumno.id_estatus = estatus_inscrito.id_estatus
            db.session.flush()

            # --- usuario de acceso (solo si no existe ya) ---
            usuario_existente = Usuario.query.filter_by(tipo_usuario="alumno", id_referencia=alumno.id_alumno).first()
            if not usuario_existente:
                username = matricula.lower()
                # evita choques de username si ya existiera por algún motivo
                sufijo = 1
                username_final = username
                while Usuario.query.filter_by(username=username_final).first():
                    sufijo += 1
                    username_final = f"{username}{sufijo}"

                password_plano = generar_password()
                nuevo_usuario = Usuario(
                    username=username_final,
                    password_hash=bcrypt.generate_password_hash(password_plano).decode("utf-8"),
                    tipo_usuario="alumno",
                    id_referencia=alumno.id_alumno,
                )
                db.session.add(nuevo_usuario)
                credenciales_nuevas.append((matricula, f"{nom} {ap} {am}", username_final, password_plano))

        db.session.flush()

        # --- materias, profesores y calificaciones (una fila del excel = una materia de un alumno) ---
        for _, row in df.iterrows():
            if pd.isna(row.get(" Final")):
                continue  # sin calificación final capturada aún, se omite

            matricula = str(row["Matricula"]).strip()
            alumno = CAlumno.query.filter_by(matricula=matricula).first()
            if not alumno:
                continue

            materia = obtener_o_crear_materia(row.get("clave Materia"), str(row["Materia"]).strip())
            profesor = obtener_o_crear_profesor(row.get("clave Tutor"), row.get("nombre Tutor"))

            registro = DCalificacion.query.filter_by(
                id_alumnos=alumno.id_alumno, id_materia=materia.id_materias, periodo=periodo
            ).first()
            if not registro:
                registro = DCalificacion(
                    id_alumnos=alumno.id_alumno, id_materia=materia.id_materias, periodo=periodo,
                )
                db.session.add(registro)

            registro.calificacion = row[" Final"]
            registro.id_profesor = profesor.id_profesor
            registro.fecha_captura = datetime.utcnow()

            asignacion = DHorario.query.filter_by(
                id_profesor=profesor.id_profesor,
                id_grupo=alumno.id_grupo,
                id_materias=materia.id_materias,
            ).first()
            if not asignacion:
                db.session.add(DHorario(
                    id_profesor=profesor.id_profesor,
                    id_grado=alumno.id_grado,
                    id_grupo=alumno.id_grupo,
                    id_carrera=alumno.id_carrera,
                    id_campus=alumno.id_campus,
                    id_materias=materia.id_materias,
                ))
            calificaciones_guardadas += 1

        db.session.commit()

        print(f"\nListo.")
        print(f"  Alumnos nuevos: {alumnos_creados}")
        print(f"  Alumnos actualizados: {alumnos_actualizados}")
        print(f"  Calificaciones guardadas: {calificaciones_guardadas}")
        print(f"  Usuarios nuevos creados: {len(credenciales_nuevas)}")

        if credenciales_nuevas:
            with open(args.credenciales_out, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["matricula", "nombre", "username", "password"])
                writer.writerows(credenciales_nuevas)
            print(f"  Credenciales en texto plano guardadas en: {args.credenciales_out}")
            print("  ⚠️  Este archivo NO debe subirse a git. Repártelo a los alumnos y bórralo.")


if __name__ == "__main__":
    main()
