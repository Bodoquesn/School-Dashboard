import io
import os
import sys
import tempfile
import unittest
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask_jwt_extended import create_access_token

from app import create_app
from extensions import db
from models import (
    CAlumno, CCampus, CCarrera, CGrado, CGrupo, CMateria, CProfesor, DHorario,
    EntregaTarea, Tarea, Usuario,
)


class AuthorizationTestCase(unittest.TestCase):
    def setUp(self):
        self.uploads = tempfile.TemporaryDirectory()
        self.app = create_app({
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "JWT_SECRET_KEY": "test-secret",
            "UPLOAD_FOLDER": self.uploads.name,
        })
        self.client = self.app.test_client()
        with self.app.app_context():
            db.create_all()
            db.session.add_all([
                CCampus(id_campus=1, nombrecampus="Centro"),
                CCarrera(id_carrera=1, nombrecarrera="Datos", id_campus=1),
                CGrado(id_grado=1, id_carrera=1, Grado="5"),
            ])
            db.session.add_all([
                CProfesor(id_profesor=1, nombre="Ada"),
                CProfesor(id_profesor=2, nombre="Grace"),
                CGrupo(id_grupo=1, grupo="A", id_profesor=1, id_campus=1, id_carrera=1, id_grado=1),
                CGrupo(id_grupo=2, grupo="B", id_profesor=2, id_campus=1, id_carrera=1, id_grado=1),
                CAlumno(id_alumno=1, nombre="Ana", id_grupo=1, id_campus=1, id_carrera=1, id_grado=1),
                CAlumno(id_alumno=2, nombre="Beto", id_grupo=2, id_campus=1, id_carrera=1, id_grado=1),
                CMateria(id_materias=1, nombre="Datos"),
                DHorario(id_horario=1, id_profesor=1, id_grupo=1, id_materias=1, id_campus=1, id_carrera=1, id_grado=1),
                DHorario(id_horario=2, id_profesor=2, id_grupo=2, id_materias=1, id_campus=1, id_carrera=1, id_grado=1),
                Usuario(id_usuario=1, username="ana", password_hash="x", tipo_usuario="alumno", id_referencia=1),
            ])
            db.session.flush()
            db.session.add_all([
                Tarea(id_tarea=1, id_materia=1, id_profesor=1, id_grupo=1, titulo="Propia", fecha_entrega=datetime(2027, 1, 1)),
                Tarea(id_tarea=2, id_materia=1, id_profesor=2, id_grupo=2, titulo="Ajena", fecha_entrega=datetime(2027, 1, 1)),
            ])
            db.session.flush()
            db.session.add(EntregaTarea(id_entrega=1, id_tarea=2, id_alumno=2))
            db.session.commit()
            self.profesor_token = create_access_token(
                identity="10", additional_claims={"tipo_usuario": "profesor", "id_referencia": 1}
            )
            self.alumno_token = create_access_token(
                identity="1", additional_claims={"tipo_usuario": "alumno", "id_referencia": 1}
            )
            self.admin_token = create_access_token(
                identity="99", additional_claims={"tipo_usuario": "admin", "id_referencia": 0}
            )

    def tearDown(self):
        with self.app.app_context():
            db.session.remove()
            db.drop_all()
        self.uploads.cleanup()

    def auth(self, token):
        return {"Authorization": f"Bearer {token}"}

    def test_profesor_no_puede_ver_grupo_ajeno(self):
        response = self.client.get("/api/profesor/grupos/2/alumnos", headers=self.auth(self.profesor_token))
        self.assertEqual(response.status_code, 403)

    def test_profesor_no_puede_calificar_alumno_ajeno(self):
        response = self.client.post(
            "/api/profesor/calificaciones",
            json={"id_alumno": 2, "calificacion": 9, "periodo": "P1"},
            headers=self.auth(self.profesor_token),
        )
        self.assertEqual(response.status_code, 403)

    def test_profesor_no_puede_calificar_entrega_ajena(self):
        response = self.client.put(
            "/api/profesor/entregas/1/calificar",
            json={"calificacion": 9}, headers=self.auth(self.profesor_token),
        )
        self.assertEqual(response.status_code, 404)

    def test_alumno_no_puede_entregar_tarea_de_otro_grupo(self):
        response = self.client.post(
            "/api/alumno/tareas/2/entregar",
            data={"comentario": "intento"}, headers=self.auth(self.alumno_token),
        )
        self.assertEqual(response.status_code, 403)

    def test_profesor_no_puede_usar_horario_ajeno(self):
        response = self.client.post(
            "/api/profesor/asistencia",
            json={"id_horario": 2, "fecha": "2026-08-16", "registros": [{"id_alumno": 2, "estatus": "presente"}]},
            headers=self.auth(self.profesor_token),
        )
        self.assertEqual(response.status_code, 403)

    def test_foto_de_perfil_se_guarda_en_carpeta_controlada(self):
        png = b"\x89PNG\r\n\x1a\n" + b"contenido-de-prueba"
        response = self.client.put(
            "/api/auth/foto",
            data={"foto": (io.BytesIO(png), "foto.png")},
            content_type="multipart/form-data",
            headers=self.auth(self.alumno_token),
        )
        self.assertEqual(response.status_code, 200)
        foto = response.get_json()["perfil"]["foto"]
        self.assertTrue(foto.startswith("perfiles/perfil_1_"))
        self.assertTrue(os.path.isfile(os.path.join(self.uploads.name, foto)))

    def test_reporte_del_alumno_responde(self):
        response = self.client.get("/api/reportes/resumen", headers=self.auth(self.alumno_token))
        self.assertEqual(response.status_code, 200)
        self.assertIn("tarjetas", response.get_json())

    def test_argos_profesor_solo_lista_alumnos_de_sus_grupos(self):
        response = self.client.get("/api/biometria/alumnos", headers=self.auth(self.profesor_token))
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item["id_alumno"] for item in response.get_json()], [1])

    def test_argos_rechaza_rol_alumno(self):
        response = self.client.get("/api/biometria/resumen", headers=self.auth(self.alumno_token))
        self.assertEqual(response.status_code, 403)

    def test_argos_admin_lista_todos_los_alumnos(self):
        response = self.client.get("/api/biometria/alumnos", headers=self.auth(self.admin_token))
        self.assertEqual(response.status_code, 200)
        self.assertEqual({item["id_alumno"] for item in response.get_json()}, {1, 2})

    def test_alumno_ve_materias_y_profesores_por_asignacion(self):
        materias = self.client.get("/api/alumno/materias", headers=self.auth(self.alumno_token))
        profesores = self.client.get("/api/alumno/profesores", headers=self.auth(self.alumno_token))
        self.assertEqual(materias.status_code, 200)
        self.assertEqual([item["nombre"] for item in materias.get_json()], ["Datos"])
        self.assertEqual(profesores.status_code, 200)
        self.assertEqual([item["nombre"] for item in profesores.get_json()], ["Ada"])

    def test_academia_profesor_incluye_asignacion_y_companeros_area(self):
        response = self.client.get("/api/academia/resumen", headers=self.auth(self.profesor_token))
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(len(data["asignaciones"]), 1)
        self.assertEqual(data["asignaciones"][0]["cuatrimestre"], 5)
        self.assertEqual([item["nombre"] for item in data["companeros_area"]], ["Grace"])

    def test_admin_ve_todas_las_asignaciones_y_grupos(self):
        academia = self.client.get("/api/academia/resumen", headers=self.auth(self.admin_token))
        grupos = self.client.get("/api/profesor/grupos", headers=self.auth(self.admin_token))
        self.assertEqual(academia.status_code, 200)
        self.assertEqual(len(academia.get_json()["asignaciones"]), 2)
        self.assertEqual(grupos.status_code, 200)
        self.assertEqual({item["id_grupo"] for item in grupos.get_json()}, {1, 2})


if __name__ == "__main__":
    unittest.main()
