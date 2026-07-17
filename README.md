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
