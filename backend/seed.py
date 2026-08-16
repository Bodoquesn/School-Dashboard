"""
Script de ayuda para crear usuarios de acceso (login) ligados a registros
YA EXISTENTES en c_alumnos / c_profesor.

Uso:
    python seed.py alumno   12   ana.garcia   miPassword123
    python seed.py profesor  3   juan.perez   otraPassword456
    python seed.py admin     0   admin        adminPassword789

Donde el segundo argumento es el id_alumno / id_profesor ya existente en tu
base de datos (usa 0 para admin, que no está ligado a ninguna tabla).
"""
import sys
from app import create_app
from extensions import db, bcrypt
from models import Usuario, CAlumno, CProfesor


def main():
    if len(sys.argv) != 5:
        print(__doc__)
        sys.exit(1)

    tipo, ref_id, username, password = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]

    if tipo not in ("alumno", "profesor", "admin"):
        print("tipo debe ser 'alumno', 'profesor' o 'admin'")
        sys.exit(1)

    app = create_app()
    with app.app_context():
        if tipo == "alumno" and not CAlumno.query.get(ref_id):
            print(f"No existe ningún alumno con id_alumno={ref_id}")
            sys.exit(1)
        if tipo == "profesor" and not CProfesor.query.get(ref_id):
            print(f"No existe ningún profesor con id_profesor={ref_id}")
            sys.exit(1)

        if Usuario.query.filter_by(username=username).first():
            print(f"El username '{username}' ya existe")
            sys.exit(1)

        usuario = Usuario(
            username=username,
            password_hash=bcrypt.generate_password_hash(password).decode("utf-8"),
            tipo_usuario=tipo,
            id_referencia=ref_id,
        )
        db.session.add(usuario)
        db.session.commit()
        print(f"Usuario creado: {username} ({tipo}, id_referencia={ref_id})")


if __name__ == "__main__":
    main()
