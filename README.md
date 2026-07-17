# Portal Escolar · Universidad SABES

Dashboard escolar con backend en **Python (Flask + SQLAlchemy)** y frontend en
**React (Vite)**, conectado a tu base de datos existente.

---

## 1. Qué incluye el dashboard

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

## 2. Estructura del proyecto
```text
school-dashboard/
├── backend/
│   ├── app.py                    # App Factory + registro de blueprints
│   ├── config.py                 # Configuración mediante variables de entorno
│   ├── extensions.py             # db, jwt, bcrypt, cors
│   ├── models.py                 # Modelos SQLAlchemy
│   ├── utils.py                  # Decoradores y utilidades
│   ├── seed.py                   # Script para crear usuarios de prueba
│   ├── migrations/
│   │   └── 001_new_tables.sql
│   └── routes/
│       ├── auth.py               # /api/auth/*
│       ├── alumno.py             # /api/alumno/*
│       ├── profesor.py           # /api/profesor/*
│       └── common.py             # /api/archivos/*, /api/salud
│
└── frontend/
    └── src/
        ├── App.jsx               # Rutas principales
        ├── api.js                # Cliente Axios
        ├── context/
        │   └── AuthContext.jsx
        ├── i18n/
        ├── components/
        │   ├── Sidebar.jsx
        │   ├── Topbar.jsx
        │   └── ProtectedRoute.jsx
        └── pages/
            ├── Login.jsx
            ├── Dashboard.jsx
            ├── Settings.jsx
            ├── alumno/
            │   ├── Calificaciones.jsx
            │   ├── Tareas.jsx
            │   ├── Boleta.jsx
            │   └── Materias.jsx
            └── profesor/
                ├── Calificaciones.jsx
                ├── Tareas.jsx
                └── Asistencia.jsx
```
