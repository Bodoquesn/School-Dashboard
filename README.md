# Portal Escolar · Universidad SABES

Dashboard escolar con backend en **Python (Flask + SQLAlchemy)** y frontend en
**React (Vite)**, conectado a tu base de datos existente.

---

## 1. Cambios necesarios en tu base de datos

Tu esquema actual (visto en el diagrama) **no tiene tabla de usuarios/login**,
así que no hay forma de autenticar a alguien todavía. Ejecuta el script:

```
backend/migrations/001_new_tables.sql
```

Este script **no borra ni modifica tus datos actuales**. Agrega:

| Tabla nueva          | Para qué sirve |
|-----------------------|----------------|
| `usuarios`             | Login (usuario/contraseña) ligado a un `id_alumno` o `id_profesor` existente |
| `tareas`                | Tareas/actividades que un profesor asigna a un grupo |
| `entregas_tareas`       | Lo que cada alumno sube para una tarea, y su calificación |
| `asistencia`            | Pase de lista por alumno/horario/fecha |

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

# Ejecuta migrations/001_new_tables.sql en tu base de datos (con tu cliente SQL favorito)

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
│   ├── migrations/001_new_tables.sql
│   └── routes/
│       ├── auth.py             # /api/auth/*
│       ├── alumno.py           # /api/alumno/*
│       ├── profesor.py         # /api/profesor/*
│       └── common.py           # /api/archivos/*, /api/salud
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

## 6. Notas / próximos pasos sugeridos

- Ahora mismo cualquier `profesor` puede capturar calificaciones sin
  validar que ese grupo/materia realmente le pertenezca más allá del
  filtro por `id_profesor` — para producción conviene reforzar esa
  validación en cada endpoint.
- Las fotos de perfil (`foto` en `c_alumnos`/`c_profesor`) se sirven desde
  `/api/archivos/<nombre>` — súbelas a la carpeta `backend/uploads/` con el
  mismo nombre que tienes guardado en la base de datos, o cambia esa lógica
  para apuntar a donde ya las tengas almacenadas (S3, etc.).
- Puedo agregar reportes/estadísticas (asistencia por grupo, promedio por
  materia, etc.) si los necesitas — el modelo de datos ya lo soporta.
