from functools import lru_cache
from ultralytics import YOLO
from .config import settings

@lru_cache(maxsize=1)
def get_model() -> YOLO:
    return YOLO(settings.model)
