"""
Genera un archivo .sql con TODOS los INSERT necesarios para cargar un
"concentrado de calificaciones" a tu base de datos -- sin depender de que
Flask/SQLAlchemy se conecten a la BD para hacerlo. Tú lo ejecutas
directamente en DBeaver.

Uso:
    pip install pandas openpyxl --break-system-packages   # si no los tienes
    python generar_sql_import.py "C:\\ruta\\a\\concentrado.xlsx" "SEPT-DIC 2025"

Genera dos archivos en la carpeta actual:
    - import_alumnos.sql            -> pégalo y ejecútalo en DBeaver
    - credenciales_generadas.csv    -> usuario/contraseña en texto plano,
                                        repártelo a los alumnos y bórralo
                                        después. NUNCA lo subas a git.

Notas:
    - Es seguro volver a correr el .sql generado: usa la matrícula/nombre
      como llave para no duplicar campus, carreras, materias, profesores
      ni alumnos ya existentes.
    - Excluye automáticamente a los alumnos con Estatus = 'BAJA DEFINITIVA'.
    - Las contraseñas se guardan hasheadas (formato sha256$salt$hash) porque
      MySQL no tiene bcrypt nativo. El backend (utils.py) ya sabe verificar
      este formato, y lo "sube" a bcrypt automáticamente la primera vez que
      cada alumno inicia sesión.
"""
import re
import csv
import hashlib
import secrets
import string
import sys

import pandas as pd

EXCEL_PATH = sys.argv[1] if len(sys.argv) > 1 else "/mnt/user-data/uploads/concentrado_anonimizado.xlsx"
PERIODO = sys.argv[2] if len(sys.argv) > 2 else "SEPT-DIC 2025"
SQL_OUT = "import_alumnos.sql"
CSV_OUT = "credenciales_generadas.csv"


def esc(v):
    """Escapa un valor de texto para SQL. None -> NULL."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "NULL"
    s = str(v).replace("\\", "\\\\").replace("'", "''").strip()
    return f"'{s}'"


def num(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return "NULL"
    return str(v)


def dividir_nombre(nombre_completo):
    partes = str(nombre_completo).strip().split()
    if len(partes) >= 3:
        return partes[0].title(), partes[1].title(), " ".join(partes[2:]).title()
    if len(partes) == 2:
        return partes[0].title(), "", partes[1].title()
    return "", "", (partes[0].title() if partes else "")


def parsear_subsistema(subsistema):
    m = re.match(r"^(\d+)([A-Za-z]*)$", str(subsistema).strip())
    if m:
        return m.group(1), (m.group(2) or "GRAL")
    return str(subsistema), "GRAL"


def generar_password(longitud=10):
    alfabeto = string.ascii_letters + string.digits
    return "".join(secrets.choice(alfabeto) for _ in range(longitud))


def hash_password(password_plano):
    """
    Hash compatible con MySQL puro (sin depender de bcrypt en la app):
    sha256$<salt_hex>$<hash_hex>  usando SHA-256 + salt aleatorio, 20000 vueltas.
    El backend (utils.py) sabe verificar este formato.
    """
    salt = secrets.token_hex(16)
    data = (salt + password_plano).encode("utf-8")
    for _ in range(20000):
        data = hashlib.sha256(data).digest()
    return f"sha256${salt}${data.hex()}"


def slug(txt):
    return re.sub(r"[^a-zA-Z0-9]", "_", str(txt))[:40]


def cargar_excel(ruta):
    df = pd.read_excel(ruta, sheet_name="concentrado", header=8)
    df = df.dropna(axis=1, how="all")
    df = df[df["Matricula"].notna()].copy()
    matriculas_baja = set(df.loc[df["Estatus"] == "BAJA DEFINITIVA", "Matricula"].unique())
    df = df[~df["Matricula"].isin(matriculas_baja)].copy()
    return df, matriculas_baja


def main():
    df, matriculas_baja = cargar_excel(EXCEL_PATH)

    sql = []
    sql.append("-- =====================================================================")
    sql.append("-- Importación generada automáticamente desde el Excel de calificaciones")
    sql.append(f"-- Alumnos excluidos por BAJA DEFINITIVA: {sorted(matriculas_baja)}")
    sql.append("-- Ejecuta este script completo de una sola vez (usa variables de sesión @).")
    sql.append("-- Es seguro volver a correrlo: no duplica campus/carreras/materias/")
    sql.append("-- profesores/alumnos ya existentes (usa la matrícula / nombre como llave).")
    sql.append("-- =====================================================================\n")
    sql.append("START TRANSACTION;\n")

    sql.append("-- Necesaria para poder re-insertar/actualizar calificaciones sin duplicar")
    sql.append("-- si vuelves a correr este script (se ignora el error si ya existe).")
    sql.append("ALTER TABLE d_calificaciones ADD UNIQUE KEY uq_calif_alumno_materia_periodo (id_alumnos, id_materia, periodo);\n")

    # ---------------------------------------------------------------- Estatus
    sql.append("-- --- Estatus 'INSCRITO' ---")
    sql.append("SET @v_estatus_inscrito = (SELECT id_estatus FROM c_estatus WHERE estatus = 'INSCRITO' LIMIT 1);")
    sql.append("INSERT INTO c_estatus (estatus)")
    sql.append("SELECT 'INSCRITO' WHERE @v_estatus_inscrito IS NULL;")
    sql.append("SET @v_estatus_inscrito = COALESCE(@v_estatus_inscrito, LAST_INSERT_ID());\n")

    # ---------------------------------------------------------------- Campus
    centros = df["Centro"].dropna().unique().tolist()
    campus_var = {}
    sql.append("-- --- Campus ---")
    for i, centro in enumerate(centros):
        nombre_campus = re.sub(r"^\d+\w*\s*-\s*", "", str(centro)).strip()
        var = f"@v_campus_{i}"
        campus_var[centro] = var
        sql.append(f"SET {var} = (SELECT id_campus FROM d_campus WHERE nombrecampus = {esc(nombre_campus)} LIMIT 1);")
        sql.append(f"INSERT INTO d_campus (nombrecampus, ubicacion_campus)")
        sql.append(f"SELECT {esc(nombre_campus)}, '' WHERE {var} IS NULL;")
        sql.append(f"SET {var} = COALESCE({var}, LAST_INSERT_ID());\n")

    # ---------------------------------------------------------------- Carreras
    carreras = df["Especialidad"].dropna().unique().tolist()
    carrera_var = {}
    sql.append("-- --- Carreras ---")
    for i, carrera in enumerate(carreras):
        var = f"@v_carrera_{i}"
        carrera_var[carrera] = var
        # todas las filas de esta carrera comparten el mismo Centro (campus)
        centro_de_carrera = df.loc[df["Especialidad"] == carrera, "Centro"].iloc[0]
        campus_ref = campus_var[centro_de_carrera]
        sql.append(f"SET {var} = (SELECT id_carrera FROM d_carrera WHERE nombrecarrera = {esc(carrera)} LIMIT 1);")
        sql.append(f"INSERT INTO d_carrera (nombrecarrera, id_campus)")
        sql.append(f"SELECT {esc(carrera)}, {campus_ref} WHERE {var} IS NULL;")
        sql.append(f"SET {var} = COALESCE({var}, LAST_INSERT_ID());\n")

    # ---------------------------------------------------------------- Grado + Grupo (por carrera + subsistema)
    combos = df[["Especialidad", "Subsistema"]].dropna().drop_duplicates().values.tolist()
    grado_var = {}
    grupo_var = {}
    sql.append("-- --- Grados y Grupos ---")
    for i, (carrera, subsistema) in enumerate(combos):
        grado_txt, letra_grupo = parsear_subsistema(subsistema)
        carrera_ref = carrera_var[carrera]
        gvar = f"@v_grado_{i}"
        grado_var[(carrera, subsistema)] = gvar
        sql.append(f"SET {gvar} = (SELECT id_grado FROM d_grado WHERE Grado = {esc(grado_txt)} AND id_carrera = {carrera_ref} LIMIT 1);")
        sql.append(f"INSERT INTO d_grado (Grado, id_carrera)")
        sql.append(f"SELECT {esc(grado_txt)}, {carrera_ref} WHERE {gvar} IS NULL;")
        sql.append(f"SET {gvar} = COALESCE({gvar}, LAST_INSERT_ID());")

        campus_de_carrera = df.loc[df["Especialidad"] == carrera, "Centro"].iloc[0]
        campus_ref = campus_var[campus_de_carrera]
        grpvar = f"@v_grupo_{i}"
        grupo_var[(carrera, subsistema)] = grpvar
        sql.append(f"SET {grpvar} = (SELECT id_grupo FROM d_grupo WHERE grupo = {esc(letra_grupo)} AND id_carrera = {carrera_ref} AND id_grado = {gvar} LIMIT 1);")
        sql.append(f"INSERT INTO d_grupo (grupo, id_carrera, id_campus, id_grado)")
        sql.append(f"SELECT {esc(letra_grupo)}, {carrera_ref}, {campus_ref}, {gvar} WHERE {grpvar} IS NULL;")
        sql.append(f"SET {grpvar} = COALESCE({grpvar}, LAST_INSERT_ID());\n")

    # ---------------------------------------------------------------- Materias
    materias = df[["clave Materia", "Materia"]].dropna(subset=["Materia"]).drop_duplicates(subset=["Materia"]).values.tolist()
    materia_var = {}
    sql.append("-- --- Materias ---")
    for i, (clave, nombre) in enumerate(materias):
        var = f"@v_materia_{i}"
        materia_var[nombre] = var
        sql.append(f"SET {var} = (SELECT id_materias FROM c_materias WHERE nombre = {esc(nombre)} LIMIT 1);")
        sql.append(f"INSERT INTO c_materias (nombre)")
        sql.append(f"SELECT {esc(nombre)} WHERE {var} IS NULL;")
        sql.append(f"SET {var} = COALESCE({var}, LAST_INSERT_ID());\n")

    # ---------------------------------------------------------------- Profesores (tutores)
    profesores = df[["clave Tutor", "nombre Tutor"]].dropna(subset=["nombre Tutor"]).drop_duplicates(subset=["clave Tutor"]).values.tolist()
    profesor_var = {}
    sql.append("-- --- Profesores (tutores) ---")
    for i, (clave, nombre) in enumerate(profesores):
        clave_str = str(int(clave)) if pd.notna(clave) else None
        ap, am, nom = dividir_nombre(nombre)
        var = f"@v_profesor_{i}"
        profesor_var[clave] = var
        if clave_str:
            sql.append(f"SET {var} = (SELECT id_profesor FROM c_profesor WHERE clave_tutor = {esc(clave_str)} LIMIT 1);")
            sql.append(f"INSERT INTO c_profesor (nombre, apellido_paterno, apellido_materno, clave_tutor)")
            sql.append(f"SELECT {esc(nom)}, {esc(ap)}, {esc(am)}, {esc(clave_str)} WHERE {var} IS NULL;")
        else:
            sql.append(f"SET {var} = (SELECT id_profesor FROM c_profesor WHERE nombre = {esc(nom)} AND apellido_paterno = {esc(ap)} AND apellido_materno = {esc(am)} LIMIT 1);")
            sql.append(f"INSERT INTO c_profesor (nombre, apellido_paterno, apellido_materno)")
            sql.append(f"SELECT {esc(nom)}, {esc(ap)}, {esc(am)} WHERE {var} IS NULL;")
        sql.append(f"SET {var} = COALESCE({var}, LAST_INSERT_ID());\n")

    # ---------------------------------------------------------------- Alumnos + Usuarios
    alumnos = df.drop_duplicates(subset="Matricula")
    sql.append("-- --- Alumnos + usuarios de acceso ---")
    credenciales = []
    for _, row in alumnos.iterrows():
        matricula = str(row["Matricula"]).strip()
        ap, am, nom = dividir_nombre(row["Nombre Alumno"])
        carrera = row["Especialidad"]
        subsistema = row["Subsistema"]
        campus_ref = campus_var[row["Centro"]]
        carrera_ref = carrera_var[carrera]
        grado_ref = grado_var[(carrera, subsistema)]
        grupo_ref = grupo_var[(carrera, subsistema)]
        avar = f"@v_alumno_{slug(matricula)}"

        sql.append(f"SET {avar} = (SELECT id_alumno FROM c_alumnos WHERE matricula = {esc(matricula)} LIMIT 1);")
        sql.append("INSERT INTO c_alumnos (matricula, nombre, apellido_paterno, apellido_materno, id_campus, id_carrera, id_grado, id_grupo, id_estatus)")
        sql.append(
            f"SELECT {esc(matricula)}, {esc(nom)}, {esc(ap)}, {esc(am)}, {campus_ref}, {carrera_ref}, "
            f"{grado_ref}, {grupo_ref}, @v_estatus_inscrito WHERE {avar} IS NULL;"
        )
        sql.append(f"SET {avar} = COALESCE({avar}, LAST_INSERT_ID());")

        username = matricula.lower()
        password_plano = generar_password()
        password_hash = hash_password(password_plano)
        sql.append(f"INSERT INTO usuarios (username, password_hash, tipo_usuario, id_referencia)")
        sql.append(
            f"SELECT {esc(username)}, {esc(password_hash)}, 'alumno', {avar} "
            f"WHERE NOT EXISTS (SELECT 1 FROM usuarios WHERE tipo_usuario='alumno' AND id_referencia = {avar});"
        )
        sql.append("")
        credenciales.append((matricula, f"{nom} {ap} {am}", username, password_plano))

    # ---------------------------------------------------------------- Calificaciones
    sql.append("-- --- Calificaciones finales ---")
    n_calif = 0
    for _, row in df.iterrows():
        if pd.isna(row.get(" Final")):
            continue
        matricula = str(row["Matricula"]).strip()
        avar = f"@v_alumno_{slug(matricula)}"
        materia = row["Materia"]
        mvar = materia_var.get(materia)
        if mvar is None:
            continue
        clave_tutor = row.get("clave Tutor")
        pvar = profesor_var.get(clave_tutor)
        pvar_sql = pvar if pvar else "NULL"

        sql.append("INSERT INTO d_calificaciones (id_alumnos, calificacion, id_materia, id_profesor, periodo)")
        sql.append(
            f"VALUES ({avar}, {num(row[' Final'])}, {mvar}, {pvar_sql}, {esc(PERIODO)})"
        )
        sql.append(
            "ON DUPLICATE KEY UPDATE calificacion = VALUES(calificacion), id_profesor = VALUES(id_profesor);"
        )
        n_calif += 1

    sql.append("\nCOMMIT;\n")
    sql.append(f"-- Alumnos procesados: {len(alumnos)}")
    sql.append(f"-- Calificaciones procesadas: {n_calif}")

    with open(SQL_OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(sql))

    with open(CSV_OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["matricula", "nombre", "username", "password"])
        w.writerows(credenciales)

    print(f"SQL generado: {SQL_OUT} ({len(sql)} líneas)")
    print(f"Credenciales generadas: {CSV_OUT} ({len(credenciales)} alumnos)")


if __name__ == "__main__":
    main()
