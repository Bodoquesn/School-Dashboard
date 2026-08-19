-- Materializa las relaciones profesor-grupo-materia a partir de las
-- calificaciones importadas. El grupo aporta carrera, campus y cuatrimestre.
INSERT INTO d_horarios (
    id_profesor, id_grado, id_grupo, id_carrera, id_campus, id_materias
)
SELECT DISTINCT
    cal.id_profesor,
    alumno.id_grado,
    alumno.id_grupo,
    alumno.id_carrera,
    alumno.id_campus,
    cal.id_materia
FROM d_calificaciones AS cal
JOIN c_alumnos AS alumno ON alumno.id_alumno = cal.id_alumnos
LEFT JOIN d_horarios AS horario
    ON horario.id_profesor = cal.id_profesor
   AND horario.id_grupo = alumno.id_grupo
   AND horario.id_materias = cal.id_materia
WHERE cal.id_profesor IS NOT NULL
  AND cal.id_materia IS NOT NULL
  AND alumno.id_grupo IS NOT NULL
  AND horario.id_horario IS NULL;

-- No se fuerza una llave única porque algunas bases históricas contienen
-- horarios repetidos que todavía están referenciados por alumnos/asistencia.
-- El LEFT JOIN anterior y los importadores evitan crear duplicados nuevos.
