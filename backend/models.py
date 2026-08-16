"""
Modelos SQLAlchemy.

IMPORTANTE:
Los modelos marcados con "# --- TABLA EXISTENTE ---" representan tu base de
datos TAL COMO ESTÁ (según el diagrama que compartiste). No se modifican
nombres de columnas para no romper tu esquema actual.

Los modelos marcados con "# --- TABLA NUEVA ---" son tablas que se necesitan
crear para que el dashboard funcione (login, tareas, asistencia, etc). El
script SQL equivalente está en migrations/001_new_tables.sql
"""
from datetime import datetime
from extensions import db


# =====================================================================
#  TABLAS EXISTENTES (mapeadas 1:1 a tu diagrama)
# =====================================================================

class CCampus(db.Model):
    __tablename__ = "d_campus"
    id_campus = db.Column(db.Integer, primary_key=True)
    nombrecampus = db.Column(db.String(120))
    ubicacion_campus = db.Column(db.String(255))


class CCarrera(db.Model):
    __tablename__ = "d_carrera"
    id_carrera = db.Column(db.Integer, primary_key=True)
    nombrecarrera = db.Column(db.String(120))
    id_campus = db.Column(db.Integer, db.ForeignKey("d_campus.id_campus"))


class CGrado(db.Model):
    __tablename__ = "d_grado"
    id_grado = db.Column(db.Integer, primary_key=True)
    id_carrera = db.Column(db.Integer, db.ForeignKey("d_carrera.id_carrera"))
    id_grupo = db.Column(db.Integer)
    Grado = db.Column(db.String(50))


class CGrupo(db.Model):
    __tablename__ = "d_grupo"
    id_grupo = db.Column(db.Integer, primary_key=True)
    id_carrera = db.Column(db.Integer, db.ForeignKey("d_carrera.id_carrera"))
    id_campus = db.Column(db.Integer, db.ForeignKey("d_campus.id_campus"))
    id_grado = db.Column(db.Integer, db.ForeignKey("d_grado.id_grado"))
    id_alumno = db.Column(db.Integer)
    id_profesor = db.Column(db.Integer, db.ForeignKey("c_profesor.id_profesor"))
    grupo = db.Column(db.String(50))


class CTurno(db.Model):
    __tablename__ = "d_turno"
    id_turno = db.Column(db.Integer, primary_key=True)
    id_grupo = db.Column(db.Integer, db.ForeignKey("d_grupo.id_grupo"))
    turno = db.Column(db.String(50))
    id_campus = db.Column(db.Integer, db.ForeignKey("d_campus.id_campus"))


class CEstatus(db.Model):
    __tablename__ = "c_estatus"
    id_estatus = db.Column(db.Integer, primary_key=True)
    estatus = db.Column(db.String(50))


class CSalones(db.Model):
    __tablename__ = "d_salones"
    id_salones = db.Column(db.Integer, primary_key=True)
    id_campus = db.Column(db.Integer, db.ForeignKey("d_campus.id_campus"))
    id_turno = db.Column(db.Integer, db.ForeignKey("d_turno.id_turno"))
    id_grupo = db.Column(db.Integer, db.ForeignKey("d_grupo.id_grupo"))


class CMateria(db.Model):
    __tablename__ = "c_materias"
    id_materias = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120))
    foto = db.Column(db.String(255))
    id_carrera = db.Column(db.Integer, db.ForeignKey("d_carrera.id_carrera"))
    id_grado = db.Column(db.Integer, db.ForeignKey("d_grado.id_grado"))


class CAlumno(db.Model):
    __tablename__ = "c_alumnos"
    id_alumno = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80))
    apellido_paterno = db.Column(db.String(80))
    apellido_materno = db.Column(db.String(80))
    edad = db.Column(db.Integer)
    movil = db.Column(db.String(20))
    sexo = db.Column(db.String(20))
    email = db.Column(db.String(120))
    foto = db.Column(db.String(255))
    cp = db.Column(db.String(10))
    calle = db.Column(db.String(120))
    colonia = db.Column(db.String(120))
    pais = db.Column(db.String(80))
    estado = db.Column(db.String(80))
    municipio = db.Column(db.String(80))
    noint = db.Column(db.String(20))
    noext = db.Column(db.String(20))
    id_grupo = db.Column(db.Integer, db.ForeignKey("d_grupo.id_grupo"))
    id_carrera = db.Column(db.Integer, db.ForeignKey("d_carrera.id_carrera"))
    id_grado = db.Column(db.Integer, db.ForeignKey("d_grado.id_grado"))
    id_campus = db.Column(db.Integer, db.ForeignKey("d_campus.id_campus"))
    id_horario = db.Column(db.Integer)
    id_turno = db.Column(db.Integer, db.ForeignKey("d_turno.id_turno"))
    id_estatus = db.Column(db.Integer, db.ForeignKey("c_estatus.id_estatus"))
    fecha_nacimiento = db.Column(db.Date)
    matricula = db.Column(db.String(30), unique=True)  # ver migración 002

    def nombre_completo(self):
        return f"{self.nombre} {self.apellido_paterno} {self.apellido_materno}".strip()

    def to_dict(self):
        return {
            "id_alumno": self.id_alumno,
            "matricula": self.matricula,
            "nombre": self.nombre_completo(),
            "email": self.email,
            "foto": self.foto,
            "id_grupo": self.id_grupo,
            "id_carrera": self.id_carrera,
            "id_grado": self.id_grado,
            "id_campus": self.id_campus,
        }


class CProfesor(db.Model):
    __tablename__ = "c_profesor"
    id_profesor = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80))
    apellido_paterno = db.Column(db.String(80))
    apellido_materno = db.Column(db.String(80))
    edad = db.Column(db.Integer)
    movil = db.Column(db.String(20))
    sexo = db.Column(db.String(20))
    email = db.Column(db.String(120))
    foto = db.Column(db.String(255))
    cp = db.Column(db.String(10))
    calle = db.Column(db.String(120))
    colonia = db.Column(db.String(120))
    pais = db.Column(db.String(80))
    estado = db.Column(db.String(80))
    municipio = db.Column(db.String(80))
    noint = db.Column(db.String(20))
    noext = db.Column(db.String(20))
    id_grupo = db.Column(db.Integer)
    id_carrera = db.Column(db.Integer, db.ForeignKey("d_carrera.id_carrera"))
    id_grado = db.Column(db.Integer, db.ForeignKey("d_grado.id_grado"))
    id_campus = db.Column(db.Integer, db.ForeignKey("d_campus.id_campus"))
    id_horario = db.Column(db.Integer)
    id_turno = db.Column(db.Integer, db.ForeignKey("d_turno.id_turno"))
    id_estatus = db.Column(db.Integer, db.ForeignKey("c_estatus.id_estatus"))
    fecha_nacimiento = db.Column(db.Date)
    clave_tutor = db.Column(db.String(30), unique=True)  # ver migración 002

    def nombre_completo(self):
        return f"{self.nombre} {self.apellido_paterno} {self.apellido_materno}".strip()

    def to_dict(self):
        return {
            "id_profesor": self.id_profesor,
            "clave_tutor": self.clave_tutor,
            "nombre": self.nombre_completo(),
            "email": self.email,
            "foto": self.foto,
        }


class CPersonal(db.Model):
    __tablename__ = "c_personal"
    id_personal = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80))
    apellido_paterno = db.Column(db.String(80))
    apellido_materno = db.Column(db.String(80))
    movil = db.Column(db.String(20))
    sexo = db.Column(db.String(20))
    edad = db.Column(db.Integer)
    email = db.Column(db.String(120))
    foto = db.Column(db.String(255))
    cp = db.Column(db.String(10))
    calle = db.Column(db.String(120))
    colonia = db.Column(db.String(120))
    pais = db.Column(db.String(80))
    estado = db.Column(db.String(80))
    municipio = db.Column(db.String(80))
    noint = db.Column(db.String(20))
    noext = db.Column(db.String(20))
    id_estatus = db.Column(db.Integer, db.ForeignKey("c_estatus.id_estatus"))
    fecha_nacimiento = db.Column(db.Date)


class DHorario(db.Model):
    __tablename__ = "d_horarios"
    id_horario = db.Column(db.Integer, primary_key=True)
    id_alumnos = db.Column(db.Integer, db.ForeignKey("c_alumnos.id_alumno"))
    id_profesor = db.Column(db.Integer, db.ForeignKey("c_profesor.id_profesor"))
    id_grado = db.Column(db.Integer, db.ForeignKey("d_grado.id_grado"))
    id_grupo = db.Column(db.Integer, db.ForeignKey("d_grupo.id_grupo"))
    id_carrera = db.Column(db.Integer, db.ForeignKey("d_carrera.id_carrera"))
    id_campus = db.Column(db.Integer, db.ForeignKey("d_campus.id_campus"))
    id_materias = db.Column(db.Integer, db.ForeignKey("c_materias.id_materias"))


class DCalificacion(db.Model):
    """
    NOTA: en tu diagrama esta tabla solo tiene (id_alumnos, calificacion),
    lo cual no permite saber a qué MATERIA, PERIODO o PROFESOR pertenece
    cada calificación. Se agregaron 4 columnas nuevas (ver migración SQL)
    para que el dashboard pueda mostrar calificaciones por materia/periodo:
    id_materia, id_profesor, periodo, fecha_captura.
    Si prefieres no modificar la tabla original, el sistema puede seguir
    funcionando con una sola calificación global por alumno.
    """
    __tablename__ = "d_calificaciones"
    id_calificacion = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_alumnos = db.Column(db.Integer, db.ForeignKey("c_alumnos.id_alumno"), nullable=False)
    calificacion = db.Column(db.Numeric(4, 1))
    # --- columnas nuevas recomendadas ---
    id_materia = db.Column(db.Integer, db.ForeignKey("c_materias.id_materias"))
    id_profesor = db.Column(db.Integer, db.ForeignKey("c_profesor.id_profesor"))
    periodo = db.Column(db.String(30))          # ej. "Parcial 1", "2026-A"
    fecha_captura = db.Column(db.DateTime, default=datetime.utcnow)


# =====================================================================
#  TABLAS NUEVAS (necesarias para que el dashboard funcione)
# =====================================================================

class Usuario(db.Model):
    """
    Tabla de autenticación. Un usuario se liga a UN alumno o UN profesor
    (o admin) mediante tipo_usuario + id_referencia.
    """
    __tablename__ = "usuarios"
    id_usuario = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    tipo_usuario = db.Column(db.String(20), nullable=False)  # 'alumno' | 'profesor' | 'admin'
    id_referencia = db.Column(db.Integer, nullable=False)    # id_alumno o id_profesor
    idioma_preferido = db.Column(db.String(5), default="es")  # 'es' | 'en'
    activo = db.Column(db.Boolean, default=True)
    creado_en = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id_usuario": self.id_usuario,
            "username": self.username,
            "tipo_usuario": self.tipo_usuario,
            "id_referencia": self.id_referencia,
            "idioma_preferido": self.idioma_preferido,
        }


class Tarea(db.Model):
    __tablename__ = "tareas"
    id_tarea = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_materia = db.Column(db.Integer, db.ForeignKey("c_materias.id_materias"), nullable=False)
    id_profesor = db.Column(db.Integer, db.ForeignKey("c_profesor.id_profesor"), nullable=False)
    id_grupo = db.Column(db.Integer, db.ForeignKey("d_grupo.id_grupo"), nullable=False)
    titulo = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text)
    archivo_adjunto = db.Column(db.String(255))
    fecha_asignacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_entrega = db.Column(db.DateTime, nullable=False)

    def to_dict(self):
        return {
            "id_tarea": self.id_tarea,
            "id_materia": self.id_materia,
            "id_profesor": self.id_profesor,
            "id_grupo": self.id_grupo,
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "archivo_adjunto": self.archivo_adjunto,
            "fecha_asignacion": self.fecha_asignacion.isoformat() if self.fecha_asignacion else None,
            "fecha_entrega": self.fecha_entrega.isoformat() if self.fecha_entrega else None,
        }


class EntregaTarea(db.Model):
    __tablename__ = "entregas_tareas"
    id_entrega = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_tarea = db.Column(db.Integer, db.ForeignKey("tareas.id_tarea"), nullable=False)
    id_alumno = db.Column(db.Integer, db.ForeignKey("c_alumnos.id_alumno"), nullable=False)
    archivo = db.Column(db.String(255))
    comentario = db.Column(db.Text)
    fecha_entrega = db.Column(db.DateTime, default=datetime.utcnow)
    calificacion = db.Column(db.Numeric(4, 1))
    retroalimentacion = db.Column(db.Text)
    estatus = db.Column(db.String(20), default="entregada")  # entregada | calificada | atrasada

    def to_dict(self):
        return {
            "id_entrega": self.id_entrega,
            "id_tarea": self.id_tarea,
            "id_alumno": self.id_alumno,
            "archivo": self.archivo,
            "comentario": self.comentario,
            "fecha_entrega": self.fecha_entrega.isoformat() if self.fecha_entrega else None,
            "calificacion": float(self.calificacion) if self.calificacion is not None else None,
            "retroalimentacion": self.retroalimentacion,
            "estatus": self.estatus,
        }


class Asistencia(db.Model):
    __tablename__ = "asistencia"
    id_asistencia = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_alumno = db.Column(db.Integer, db.ForeignKey("c_alumnos.id_alumno"), nullable=False)
    id_horario = db.Column(db.Integer, db.ForeignKey("d_horarios.id_horario"), nullable=False)
    id_profesor = db.Column(db.Integer, db.ForeignKey("c_profesor.id_profesor"), nullable=False)
    fecha = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    estatus = db.Column(db.String(20), default="presente")  # presente | ausente | retardo | justificado

    def to_dict(self):
        return {
            "id_asistencia": self.id_asistencia,
            "id_alumno": self.id_alumno,
            "id_horario": self.id_horario,
            "id_profesor": self.id_profesor,
            "fecha": self.fecha.isoformat() if self.fecha else None,
            "estatus": self.estatus,
        }


class RostroAlumno(db.Model):
    """Descriptor biométrico de ARGOS ligado al alumno existente del portal."""
    __tablename__ = "rostros_alumnos"
    id_rostro = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_alumno = db.Column(
        db.Integer, db.ForeignKey("c_alumnos.id_alumno"), nullable=False, unique=True, index=True
    )
    motor = db.Column(db.String(50), nullable=False, index=True)
    descriptor = db.Column(db.JSON, nullable=False)
    actualizado_en = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EventoBiometrico(db.Model):
    """Entrada o salida reconocida por ARGOS; no sustituye el pase de lista."""
    __tablename__ = "eventos_biometricos"
    id_evento = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_alumno = db.Column(
        db.Integer, db.ForeignKey("c_alumnos.id_alumno"), nullable=False, index=True
    )
    id_profesor = db.Column(
        db.Integer, db.ForeignKey("c_profesor.id_profesor"), nullable=True, index=True
    )
    reconocido_en = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, index=True)
    confianza = db.Column(db.Float, nullable=False)
    camara = db.Column(db.String(150), default="Cámara principal")
    tipo_evento = db.Column(db.String(30), default="entrada")

    def to_dict(self, alumno=None, campus=None):
        return {
            "id_evento": self.id_evento,
            "id_alumno": self.id_alumno,
            "alumno": alumno.nombre_completo() if alumno else None,
            "campus": campus.nombrecampus if campus else None,
            "reconocido_en": self.reconocido_en.isoformat() if self.reconocido_en else None,
            "confianza": self.confianza,
            "camara": self.camara,
            "tipo_evento": self.tipo_evento,
        }
