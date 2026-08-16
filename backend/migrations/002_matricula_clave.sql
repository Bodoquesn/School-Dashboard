-- =====================================================================
-- Migración 002: agrega "matricula" y "clave_tutor" como llave natural
-- Necesario para poder importar el Excel de calificaciones de forma
-- repetible (evita duplicar alumnos/profesores si vuelves a importar) y
-- para generar el username de cada alumno.
-- =====================================================================

ALTER TABLE c_alumnos
    ADD COLUMN IF NOT EXISTS matricula VARCHAR(30) NULL UNIQUE;

ALTER TABLE c_profesor
    ADD COLUMN IF NOT EXISTS clave_tutor VARCHAR(30) NULL UNIQUE;
