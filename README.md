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
backend/
├── app.py
├── config.py
├── extensions.py
├── models.py
├── utils.py
├── seed.py
├── migrations/
└── routes/
    ├── auth.py
    ├── alumno.py
    ├── profesor.py
    └── common.py

frontend/
└── src/
    ├── components/
    ├── context/
    ├── pages/
    ├── App.jsx
    ├── api.js
    └── i18n/
```

### Backend

| Archivo | Descripción |
|---------|-------------|
| `app.py` | App Factory y registro de Blueprints |
| `config.py` | Configuración mediante variables de entorno |
| `extensions.py` | SQLAlchemy, JWT, Bcrypt y CORS |
| `models.py` | Modelos de la base de datos |
| `utils.py` | Decoradores y funciones auxiliares |
| `seed.py` | Crea usuarios de prueba |

### Frontend

| Carpeta | Descripción |
|---------|-------------|
| `components/` | Componentes reutilizables |
| `pages/` | Pantallas de la aplicación |
| `context/` | Context API (autenticación) |
| `i18n/` | Internacionalización |
