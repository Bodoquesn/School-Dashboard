import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")

    # --- Existing school database connection ---
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "mysql+pymysql://root:password@localhost:3306/escuela"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Auth (JWT) ---
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "dev-jwt-secret")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=8)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=15)
    JWT_TOKEN_LOCATION = ["headers"]

    # --- Uploads (tareas / entregas / fotos) ---
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join(BASE_DIR, "uploads"))
    MAX_CONTENT_LENGTH = 25 * 1024 * 1024  # 25 MB

    # --- ARGOS: reconocimiento facial académico ---
    FACE_ENGINE = os.environ.get("FACE_ENGINE", "demo")
    FACE_MODEL_NAME = os.environ.get("FACE_MODEL_NAME", "buffalo_l")
    FACE_MATCH_THRESHOLD = float(os.environ.get("FACE_MATCH_THRESHOLD", "0.90"))
    ATTENDANCE_COOLDOWN_MINUTES = int(os.environ.get("ATTENDANCE_COOLDOWN_MINUTES", "5"))
    FACE_MAX_UPLOAD_MB = int(os.environ.get("FACE_MAX_UPLOAD_MB", "5"))
    TIMEZONE = os.environ.get("TIMEZONE", "America/Mexico_City")

    # --- CORS ---
    CORS_ORIGINS = os.environ.get(
        "CORS_ORIGINS", "http://localhost:5173,http://localhost:3000"
    ).split(",")
