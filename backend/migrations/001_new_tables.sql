-- =====================================================================
-- Migración 001: tablas y columnas nuevas necesarias para el dashboard
-- Ejecuta este script sobre tu base de datos existente (NO borra nada).
-- Ajusta ENGINE/CHARSET si no usas MySQL.
-- =====================================================================

-- 1) Tabla de autenticación (login). Es indispensable: hoy c_alumnos y
--    c_profesor no tienen usuario/contraseña.
CREATE TABLE IF NOT EXISTS usuarios (
    id_usuario        INT AUTO_INCREMENT PRIMARY KEY,
    username          VARCHAR(80)  NOT NULL UNIQUE,
    password_hash     VARCHAR(255) NOT NULL,
    tipo_usuario      VARCHAR(20)  NOT NULL,      -- 'alumno' | 'profesor' | 'admin'
    id_referencia     INT          NOT NULL,      -- id_alumno o id_profesor correspondiente
    idioma_preferido  VARCHAR(5)   DEFAULT 'es',
    activo            BOOLEAN      DEFAULT TRUE,
    creado_en         DATETIME     DEFAULT CURRENT_TIMESTAMP
);

-- 2) Tareas / actividades que un profesor asigna a un grupo/materia
CREATE TABLE IF NOT EXISTS tareas (
    id_tarea          INT AUTO_INCREMENT PRIMARY KEY,
    id_materia        INT NOT NULL,
    id_profesor       INT NOT NULL,
    id_grupo          INT NOT NULL,
    titulo            VARCHAR(150) NOT NULL,
    descripcion       TEXT,
    archivo_adjunto   VARCHAR(255),
    fecha_asignacion  DATETIME DEFAULT CURRENT_TIMESTAMP,
    fecha_entrega     DATETIME NOT NULL,
    FOREIGN KEY (id_materia)  REFERENCES c_materias(id_materias),
    FOREIGN KEY (id_profesor) REFERENCES c_profesor(id_profesor),
    FOREIGN KEY (id_grupo)    REFERENCES d_grupo(id_grupo)
);

-- 3) Entregas de los alumnos para cada tarea
CREATE TABLE IF NOT EXISTS entregas_tareas (
    id_entrega        INT AUTO_INCREMENT PRIMARY KEY,
    id_tarea          INT NOT NULL,
    id_alumno         INT NOT NULL,
    archivo           VARCHAR(255),
    comentario        TEXT,
    fecha_entrega     DATETIME DEFAULT CURRENT_TIMESTAMP,
    calificacion      DECIMAL(4,1),
    retroalimentacion TEXT,
    estatus           VARCHAR(20) DEFAULT 'entregada', -- entregada | calificada | atrasada
    FOREIGN KEY (id_tarea)  REFERENCES tareas(id_tarea),
    FOREIGN KEY (id_alumno) REFERENCES c_alumnos(id_alumno),
    UNIQUE KEY unico_alumno_tarea (id_tarea, id_alumno)
);

-- 4) Pase de lista / asistencia
CREATE TABLE IF NOT EXISTS asistencia (
    id_asistencia     INT AUTO_INCREMENT PRIMARY KEY,
    id_alumno         INT NOT NULL,
    id_horario        INT NOT NULL,
    id_profesor       INT NOT NULL,
    fecha             DATE NOT NULL,
    estatus           VARCHAR(20) DEFAULT 'presente', -- presente | ausente | retardo | justificado
    FOREIGN KEY (id_alumno)   REFERENCES c_alumnos(id_alumno),
    FOREIGN KEY (id_horario)  REFERENCES d_horarios(id_horario),
    FOREIGN KEY (id_profesor) REFERENCES c_profesor(id_profesor),
    UNIQUE KEY unico_alumno_horario_fecha (id_alumno, id_horario, fecha)
);

-- 5) Columnas recomendadas en d_calificaciones para poder mostrar
--    calificaciones POR MATERIA y POR PERIODO (hoy solo hay una
--    calificación global por alumno, sin relación a materia/profesor).
--    Si tu tabla ya tiene una PK propia, cambia el ALTER según corresponda.
ALTER TABLE d_calificaciones
    ADD COLUMN IF NOT EXISTS id_calificacion INT AUTO_INCREMENT PRIMARY KEY FIRST,
    ADD COLUMN IF NOT EXISTS id_materia   INT NULL,
    ADD COLUMN IF NOT EXISTS id_profesor  INT NULL,
    ADD COLUMN IF NOT EXISTS periodo      VARCHAR(30) NULL,
    ADD COLUMN IF NOT EXISTS fecha_captura DATETIME DEFAULT CURRENT_TIMESTAMP;

-- (Opcional) crea llaves foráneas si tu motor lo permite sin conflictos:
-- ALTER TABLE d_calificaciones ADD FOREIGN KEY (id_materia) REFERENCES c_materias(id_materias);
-- ALTER TABLE d_calificaciones ADD FOREIGN KEY (id_profesor) REFERENCES c_profesor(id_profesor);

-- 6) (Opcional) crea un usuario admin/profesor de prueba una vez que tengas
--    contraseñas hasheadas -- hazlo desde el endpoint /api/auth/seed-demo
--    en modo desarrollo, o con el script backend/seed.py
