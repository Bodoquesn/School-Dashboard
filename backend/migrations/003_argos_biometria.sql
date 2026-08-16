-- Integración ARGOS con el esquema existente del Portal Escolar.
-- Conserva c_alumnos como catálogo maestro y no duplica estudiantes.

CREATE TABLE IF NOT EXISTS rostros_alumnos (
    id_rostro       INT AUTO_INCREMENT PRIMARY KEY,
    id_alumno       INT NOT NULL UNIQUE,
    motor           VARCHAR(50) NOT NULL,
    descriptor      JSON NOT NULL,
    actualizado_en  DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_rostro_motor (motor),
    FOREIGN KEY (id_alumno) REFERENCES c_alumnos(id_alumno) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS eventos_biometricos (
    id_evento       INT AUTO_INCREMENT PRIMARY KEY,
    id_alumno       INT NOT NULL,
    id_profesor     INT NULL,
    reconocido_en   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    confianza       FLOAT NOT NULL,
    camara          VARCHAR(150) DEFAULT 'Cámara principal',
    tipo_evento     VARCHAR(30) DEFAULT 'entrada',
    INDEX idx_evento_alumno (id_alumno),
    INDEX idx_evento_profesor (id_profesor),
    INDEX idx_evento_fecha (reconocido_en),
    FOREIGN KEY (id_alumno) REFERENCES c_alumnos(id_alumno) ON DELETE CASCADE,
    FOREIGN KEY (id_profesor) REFERENCES c_profesor(id_profesor) ON DELETE SET NULL
);
