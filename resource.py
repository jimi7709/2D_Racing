# resource.py
from pathlib import Path
import pygame
import sys

def resource_path(relative: str) -> str:
    """
    PyInstaller onefile/onefolder 모두에서 안전하게 리소스 경로를 얻는다.
    relative 예: "assets/images/car.png"
    """
    if hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)  # PyInstaller가 푼 임시 폴더
    else:
        base = Path(__file__).resolve().parent  # 개발 중(소스 실행) 기준: resource.py 위치

    return str(base / relative)

def load_image(relative: str, *, alpha=False, size=None) -> pygame.Surface:
    """
    이미지 로드 헬퍼
    - alpha=True  → PNG 투명도 유지
    - size=(w,h)  → 로드 후 리사이즈
    """
    path = resource_path(relative)
    img = pygame.image.load(path)

    if alpha:
        img = img.convert_alpha()
    else:
        img = img.convert()

    if size is not None:
        img = pygame.transform.smoothscale(img, size)

    return img