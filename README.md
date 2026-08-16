# Portal Escolar · Universidad SABES

Dashboard escolar con backend en **Python (Flask + SQLAlchemy)** y frontend en
**React (Vite)**, conectado a tu base de datos existente.

---

## 1. Cambios necesarios en tu base de datos

Tu esquema actual (visto en el diagrama) **no tiene tabla de usuarios/login**,
así que no hay forma de autenticar a alguien todavía. Ejecuta el script:

```
backend/migrations/001_new_tables.sql
backend/migrations/002_matricula_clave.sql
backend/migrations/003_argos_biometria.sql
```

Este script **no borra ni modifica tus datos actuales**. Agrega:

| Tabla nueva          | Para qué sirve |
|-----------------------|----------------|
| `usuarios`             | Login (usuario/contraseña) ligado a un `id_alumno` o `id_profesor` existente |
| `tareas`                | Tareas/actividades que un profesor asigna a un grupo |
| `entregas_tareas`       | Lo que cada alumno sube para una tarea, y su calificación |
| `asistencia`            | Pase de lista por alumno/horario/fecha |
| `rostros_alumnos`       | Descriptor facial ARGOS ligado a un alumno existente |
| `eventos_biometricos`   | Entradas y salidas reconocidas por ARGOS |

También agrega 4 columnas a `d_calificaciones` (`id_materia`, `id_profesor`,
`periodo`, `fecha_captura`) porque, tal como está, esa tabla solo guarda
`(id_alumnos, calificacion)` — sin eso no se puede saber a qué materia o
periodo pertenece cada calificación. Si prefieres no tocar esa tabla, el
sistema puede seguir funcionando con **una sola calificación global** por
alumno (dímelo y ajusto el backend).

---

## 2. Backend (Flask)

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edita .env con los datos reales de tu base de datos (DATABASE_URL, etc.)

# Ejecuta migrations/001, 002 y 003, en ese orden, en tu base de datos

# Crea un usuario de prueba ligado a un alumno/profesor que YA exista:
python seed.py alumno   12  ana.garcia   miPassword123
python seed.py profesor  3  juan.perez   otraPassword456

python app.py     # levanta en http://localhost:5000
```

## 3. Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev        # levanta en http://localhost:5173
```

El frontend usa un proxy (`vite.config.js`) para mandar `/api/*` al backend en
`localhost:5000`, así que no necesitas configurar CORS en desarrollo.

---

## 4. Qué incluye el dashboard

**Login**
- Logo de la universidad, selector de idioma (ES/EN), autenticación JWT.

**Alumno**
- Calificaciones por materia/periodo
- Tareas: ver pendientes, subir entregas (archivo + comentario)
- Descargar boleta de calificaciones en PDF
- Materias, profesores y compañeros de su grupo

**Profesor**
- Captura y edición de calificaciones por grupo/periodo
- Crear tareas, revisar entregas y calificarlas con retroalimentación
- Pase de lista (asistencia) por grupo/horario/fecha
- ARGOS: enrolamiento y reconocimiento facial para alumnos de sus grupos
- Historial biométrico de entradas y salidas

**General**
- Sidebar izquierdo con pestañas según el rol del usuario
- Configuración y cerrar sesión abajo a la izquierda
- Selector de idioma arriba a la derecha (persiste por usuario)
- Refresh automático de sesión (JWT access + refresh token)

---

## 5. Estructura del proyecto

```
school-dashboard/
├── backend/
│   ├── app.py                 # App factory + registro de blueprints
│   ├── config.py               # Config vía variables de entorno
│   ├── extensions.py           # db, jwt, bcrypt, cors
│   ├── models.py               # Modelos SQLAlchemy (existentes + nuevos)
│   ├── utils.py                 # Decorador de permisos por rol
│   ├── seed.py                  # Script para crear usuarios de prueba
│   ├── import_excel.py          # Importa alumnos/calificaciones desde Excel (vía Python)
│   ├── generar_sql_import.py    # Genera un .sql para importar el Excel directo en DBeaver
│   ├── migrations/
│   │   ├── 001_new_tables.sql
│   │   ├── 002_matricula_clave.sql
│   │   └── 003_argos_biometria.sql
│   ├── services/
│   │   └── face_engine.py      # Motor demo de OpenCV importado de ARGOS
│   └── routes/
│       ├── auth.py             # /api/auth/*
│       ├── alumno.py           # /api/alumno/*
│       ├── profesor.py         # /api/profesor/*
│       ├── common.py           # /api/archivos/*, /api/salud
│       └── biometria.py        # /api/biometria/* (ARGOS)
└── frontend/
    └── src/
        ├── App.jsx              # Rutas (cambian según el rol)
        ├── api.js                # Cliente axios + refresh de token
        ├── context/AuthContext.jsx
        ├── i18n/                 # Traducciones ES/EN
        ├── components/           # Sidebar, Topbar, layout protegido
        └── pages/
            ├── Login.jsx, Dashboard.jsx, Settings.jsx
            ├── alumno/           # Calificaciones, Tareas, Boleta, Materias...
            └── profesor/         # Calificaciones, Tareas, Asistencia
```

---

## 6. Integración ARGOS

ARGOS quedó incorporado en el mismo backend Flask, frontend React y sistema
JWT del Portal Escolar. No mantiene un catálogo duplicado de instituciones o
estudiantes: utiliza `c_alumnos`, `d_grupo` y `d_campus` como fuente oficial.

Ejecuta la migración:

```text
backend/migrations/003_argos_biometria.sql
```

Configuración opcional en `backend/.env`:

```env
FACE_ENGINE=demo
FACE_MATCH_THRESHOLD=0.90
ATTENDANCE_COOLDOWN_MINUTES=5
FACE_MAX_UPLOAD_MB=5
TIMEZONE=America/Mexico_City
```

El motor `demo` de OpenCV se instala con `requirements.txt`. InsightFace se
conserva como alternativa opcional:

```bash
pip install -r requirements-face.txt
```

Los docentes solo pueden enrolar y reconocer alumnos pertenecientes a sus
grupos. El rol `admin` puede operar sobre todo el catálogo. El historial de
ARGOS registra entrada/salida y no sustituye la tabla de pase de lista por
horario.

Los datos de una instalación ARGOS anterior pueden migrarse por matrícula,
sin copiar usuarios ni contraseñas:

```bash
python migrate_argos.py "D:\ruta\argos-app\backend\.env" --dry-run
python migrate_argos.py "D:\ruta\argos-app\backend\.env"
```

---

## 7. Importar alumnos desde un Excel (concentrado de calificaciones)

Tienes DOS formas de importar el mismo Excel. Usa la que prefieras.

### 7a. Con Python (conecta directo a tu base de datos)

Si tienes un reporte tipo "concentrado de calificaciones" (hoja `concentrado`,
con columnas Centro, Matrícula, Nombre Alumno, Especialidad, Subsistema,
Estatus, clave/nombre Materia, clave/nombre Tutor, Parcial1-3, Final, etc.),
usa `backend/import_excel.py` para cargarlo automáticamente:

```bash
cd backend
# 1) corre también esta migración (agrega matrícula/clave_tutor):
#    migrations/002_matricula_clave.sql  (ejecútala en DBeaver)

# 2) primero en modo prueba, no toca la base de datos:
python import_excel.py "C:\ruta\a\concentrado.xlsx" --dry-run

# 3) si se ve bien, corre la importación real:
python import_excel.py "C:\ruta\a\concentrado.xlsx" --periodo "SEPT-DIC 2025"
```

Qué hace automáticamente:
- **Excluye por completo** a los alumnos con estatus `BAJA DEFINITIVA` (no se
  crean ni sus calificaciones ni su usuario).
- Crea/actualiza campus, carreras, grados/grupos, materias y profesores
  (tutores) según lo que encuentre en el Excel.
- Crea el alumno (o lo actualiza si ya existía, usando la matrícula como
  llave) y le asigna sus calificaciones finales por materia.
- Crea un **usuario y contraseña** para cada alumno nuevo (username = su
  matrícula en minúsculas). Las contraseñas en texto plano se guardan **una
  sola vez** en `backend/credenciales_generadas.csv` para que se las
  entregues — la base de datos solo guarda el hash. Ese archivo ya está en
  `.gitignore`, pero bórralo de tu computadora en cuanto termines de
  repartir las contraseñas.

### 7b. Directo en SQL (sin correr el backend, todo en DBeaver)

Si prefieres no tocar tu conexión de Python y hacerlo 100% desde DBeaver:

```bash
cd backend
pip install pandas openpyxl --break-system-packages   # solo si no los tienes

python generar_sql_import.py "C:\ruta\a\concentrado.xlsx" "SEPT-DIC 2025"
```

Esto genera dos archivos en `backend/`:

- **`import_alumnos.sql`** — ábrelo en DBeaver (Archivo → Abrir archivo SQL)
  conectado a tu base de datos, y ejecútalo completo de una sola vez
  (botón "Execute SQL Script", no "Execute Statement"). El script usa
  variables de sesión `@algo`, así que **debe correr como un solo script**,
  no línea por línea en distintas pestañas.
- **`credenciales_generadas.csv`** — usuario/contraseña en texto plano para
  repartir a los alumnos. Bórralo de tu computadora después.

Qué hace el script SQL generado:
- Excluye a los alumnos con `BAJA DEFINITIVA`
- Crea (o reutiliza si ya existen) campus, carreras, grados/grupos, materias
  y profesores usando el nombre como llave — es seguro volver a correrlo
- Inserta cada alumno (con su matrícula) y su usuario de acceso
- Inserta las calificaciones finales por materia
- Las contraseñas se guardan con un hash `sha256$salt$hash` (no bcrypt,
  porque MySQL no lo tiene nativo) — el backend ya sabe leer ese formato y
  lo convierte a bcrypt automáticamente la primera vez que cada alumno
  inicia sesión, de forma transparente

## 8. Mejoras implementadas

- Los endpoints validan que grupos, alumnos, materias, horarios, tareas y
  entregas pertenezcan al profesor autenticado. También se validan rangos de
  calificación, fechas y estados de asistencia.
- Cada alumno o profesor puede actualizar su foto desde Configuración. Las
  imágenes se validan, se limitan a 5 MB y se guardan con nombres únicos en
  `backend/uploads/perfiles/`. El frontend las descarga usando el JWT.
- La sección **Reportes** muestra promedios por materia, tareas y resumen de
  asistencia. Para docentes también presenta totales de grupos, estudiantes
  y asistencia por grupo.
- La captura de asistencia y creación de tareas utiliza horarios y materias
  autorizados obtenidos desde la API, sin pedir IDs internos manualmente.

Pruebas de regresión:

```bash
cd backend
venv\Scripts\python.exe -m unittest discover -s tests -v
```
