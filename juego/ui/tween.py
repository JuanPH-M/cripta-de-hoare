"""Funciones de interpolación (easing) para animaciones de interfaz."""

import math


def limitar(t: float) -> float:
    return 0.0 if t < 0 else (1.0 if t > 1 else t)


def ease_out_cubic(t: float) -> float:
    t = limitar(t)
    return 1 - (1 - t) ** 3


def ease_in_out(t: float) -> float:
    t = limitar(t)
    return 4 * t * t * t if t < 0.5 else 1 - (-2 * t + 2) ** 3 / 2


def ease_out_back(t: float) -> float:
    t = limitar(t)
    c1 = 1.70158
    c3 = c1 + 1
    return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2


def acercar(actual: float, objetivo: float, velocidad: float, dt: float) -> float:
    """Suavizado exponencial independiente de los FPS."""
    return objetivo + (actual - objetivo) * math.exp(-velocidad * dt)
