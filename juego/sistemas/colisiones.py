"""Colisiones círculo-vs-muros y utilidades geométricas (píxeles de lienzo).
La línea de visión está en sistemas/vision.py."""

import math

from juego.core import config


def es_muro(tiles: list[list[int]], tx: int, ty: int) -> bool:
    """Fuera del mapa se considera muro."""
    if 0 <= tx < config.COLUMNAS and 0 <= ty < config.FILAS:
        return tiles[ty][tx] == config.MURO
    return True


def circulo_choca(tiles: list[list[int]], x: float, y: float, r: float) -> bool:
    """True si el círculo (x, y, r) se superpone con alguna casilla de muro."""
    t = config.TAM
    for ty in range(int((y - r) // t), int((y + r) // t) + 1):
        for tx in range(int((x - r) // t), int((x + r) // t) + 1):
            if es_muro(tiles, tx, ty):
                # Punto del rectángulo de la casilla más cercano al centro.
                cx = min(max(x, tx * t), tx * t + t)
                cy = min(max(y, ty * t), ty * t + t)
                if (x - cx) ** 2 + (y - cy) ** 2 < r * r:
                    return True
    return False


def mover_con_colisiones(tiles: list[list[int]], x: float, y: float, dx: float, dy: float,
                         r: float) -> tuple[float, float, bool]:
    """
    Desplaza el círculo (dx, dy) por subpasos de <= 2 px, eje por eje, para
    deslizarse por las paredes. Devuelve (x, y, choco).
    """
    pasos = max(1, int(math.ceil(max(abs(dx), abs(dy)) / 2.0)))
    sx, sy = dx / pasos, dy / pasos
    choco = False
    for _ in range(pasos):
        if sx and not circulo_choca(tiles, x + sx, y, r):
            x += sx
        elif sx:
            choco = True
        if sy and not circulo_choca(tiles, x, y + sy, r):
            y += sy
        elif sy:
            choco = True
    return x, y, choco


def circulos_se_tocan(x1: float, y1: float, r1: float, x2: float, y2: float, r2: float) -> bool:
    return (x1 - x2) ** 2 + (y1 - y2) ** 2 < (r1 + r2) ** 2


def normalizar(dx: float, dy: float) -> tuple[float, float]:
    d = math.hypot(dx, dy)
    if d < 1e-9:
        return 0.0, 0.0
    return dx / d, dy / d


def centro_casilla(tx: int, ty: int) -> tuple[float, float]:
    return tx * config.TAM + config.TAM / 2, ty * config.TAM + config.TAM / 2
