from functools import lru_cache

import cv2
import numpy as np
from flask import current_app


class FaceEngineError(ValueError):
    pass


def _decode_image(image_bytes):
    if not image_bytes:
        raise FaceEngineError("El archivo de imagen está vacío.")
    image = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise FaceEngineError("No fue posible leer la imagen.")
    return image


def cosine_similarity(a, b):
    if a.shape != b.shape:
        return -1.0
    denominator = float(np.linalg.norm(a) * np.linalg.norm(b))
    return float(np.dot(a, b) / denominator) if denominator else -1.0


class DemoFaceEngine:
    """Descriptor visual básico de ARGOS para demostración académica."""

    name = "demo"

    def __init__(self):
        path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.detector = cv2.CascadeClassifier(path)
        if self.detector.empty():
            raise RuntimeError("No se pudo cargar el detector facial de OpenCV.")

    def extract_embedding(self, image_bytes):
        image = _decode_image(image_bytes)
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = self.detector.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80)
        )
        if len(faces) == 0:
            raise FaceEngineError("No se detectó un rostro. Acércate y mejora la iluminación.")
        if len(faces) > 1:
            raise FaceEngineError("La imagen debe contener un solo rostro.")
        x, y, width, height = faces[0]
        face = cv2.equalizeHist(gray[y:y + height, x:x + width])
        face = cv2.resize(face, (32, 32), interpolation=cv2.INTER_AREA)
        vector = face.astype(np.float32).reshape(-1)
        vector -= float(vector.mean())
        norm = float(np.linalg.norm(vector))
        if norm == 0:
            raise FaceEngineError("La imagen no contiene suficiente información.")
        return vector / norm


class InsightFaceEngine:
    name = "insightface"

    def __init__(self, model_name):
        try:
            from insightface.app import FaceAnalysis
        except ImportError as exc:
            raise RuntimeError(
                "Para InsightFace instala backend/requirements-face.txt."
            ) from exc
        self.app = FaceAnalysis(name=model_name, providers=["CPUExecutionProvider"])
        self.app.prepare(ctx_id=-1, det_size=(640, 640))

    def extract_embedding(self, image_bytes):
        faces = self.app.get(_decode_image(image_bytes))
        if len(faces) == 0:
            raise FaceEngineError("No se detectó ningún rostro.")
        if len(faces) > 1:
            raise FaceEngineError("La imagen debe contener un solo rostro.")
        vector = np.asarray(faces[0].normed_embedding, dtype=np.float32)
        norm = float(np.linalg.norm(vector))
        if norm == 0:
            raise FaceEngineError("No fue posible generar el descriptor facial.")
        return vector / norm


@lru_cache(maxsize=4)
def _crear_motor(nombre, modelo):
    if nombre == "demo":
        return DemoFaceEngine()
    if nombre == "insightface":
        return InsightFaceEngine(modelo)
    raise RuntimeError("FACE_ENGINE debe ser 'demo' o 'insightface'.")


def get_face_engine():
    nombre = current_app.config["FACE_ENGINE"].strip().lower()
    return _crear_motor(nombre, current_app.config["FACE_MODEL_NAME"])
