"""Íconos vectoriales en alta resolución para HUD, tienda y cartas de mejora."""

import math

import pygame

from juego.ui import paleta


def icono(s: pygame.Surface, nombre: str, cx: float, cy: float, tam: float = 32) -> None:
    k = tam / 32.0
    cx, cy = int(cx), int(cy)

    def p(x, y):
        return (cx + x * k, cy + y * k)

    def r(v):
        return max(1, int(v * k))

    if nombre in ("pocion",):
        pygame.draw.circle(s, paleta.ROJO_OSCURO, p(0, 5), r(11))
        pygame.draw.circle(s, paleta.ROJO, p(0, 5), r(9))
        pygame.draw.rect(s, paleta.HUESO, (*p(-4, -12), r(8), r(8)))
        pygame.draw.rect(s, (150, 100, 60), (*p(-5, -15), r(10), r(4)))
        pygame.draw.circle(s, paleta.BLANCO, p(-4, 1), r(3))
    elif nombre == "bomba":
        pygame.draw.circle(s, paleta.NOCHE, p(0, 4), r(12))
        pygame.draw.circle(s, (60, 54, 80), p(0, 4), r(10))
        pygame.draw.circle(s, (120, 110, 150), p(-4, 0), r(3))
        pygame.draw.line(s, (150, 100, 60), p(6, -6), p(10, -13), r(3))
        pygame.draw.circle(s, paleta.NARANJA, p(11, -14), r(4))
        pygame.draw.circle(s, paleta.ORO, p(11, -14), r(2))
    elif nombre == "espada":
        pygame.draw.line(s, paleta.HUESO, p(-10, 10), p(12, -12), r(5))
        pygame.draw.line(s, paleta.BLANCO, p(-8, 8), p(12, -12), r(2))
        pygame.draw.line(s, paleta.ORO, p(-13, 3), p(-3, 13), r(4))
        pygame.draw.line(s, (120, 80, 50), p(-10, 10), p(-15, 15), r(4))
    elif nombre in ("armadura", "escudo"):
        pts = [p(-12, -12), p(12, -12), p(12, 0), p(0, 14), p(-12, 0)]
        pygame.draw.polygon(s, paleta.CIAN_OSCURO, pts)
        pygame.draw.polygon(s, paleta.CIAN, pts, r(3))
        pygame.draw.line(s, paleta.ORO, p(0, -10), p(0, 10), r(3))
    elif nombre in ("amuleto", "corazon"):
        pygame.draw.circle(s, paleta.ROJO, p(-6, -3), r(8))
        pygame.draw.circle(s, paleta.ROJO, p(6, -3), r(8))
        pygame.draw.polygon(s, paleta.ROJO, [p(-13, 0), p(13, 0), p(0, 14)])
        pygame.draw.circle(s, paleta.BLANCO, p(-7, -5), r(3))
        if nombre == "amuleto":
            pygame.draw.line(s, paleta.ORO, p(-10, -14), p(0, -8), r(2))
            pygame.draw.line(s, paleta.ORO, p(10, -14), p(0, -8), r(2))
    elif nombre == "botas":
        pygame.draw.polygon(s, (150, 100, 60), [p(-8, -12), p(2, -12), p(2, 6), p(12, 6), p(12, 12), p(-8, 12)])
        pygame.draw.line(s, paleta.ORO, p(-8, -6), p(2, -6), r(2))
        pygame.draw.line(s, paleta.CIAN, p(-14, 0), p(-20, 0), r(2))
        pygame.draw.line(s, paleta.CIAN, p(-14, 6), p(-22, 6), r(2))
    elif nombre in ("talisman", "ojo"):
        pygame.draw.ellipse(s, paleta.HUESO, (*p(-14, -8), r(28), r(16)))
        pygame.draw.circle(s, paleta.ORO, p(0, 0), r(7))
        pygame.draw.circle(s, paleta.NOCHE, p(0, 0), r(3))
        for i in range(4):
            a = i * math.pi / 2 + math.pi / 4
            pygame.draw.line(s, paleta.ORO, p(math.cos(a) * 14, math.sin(a) * 14),
                             p(math.cos(a) * 17, math.sin(a) * 17), r(2))
    elif nombre == "dash":
        for i in range(3):
            pygame.draw.polygon(s, paleta.mezclar(paleta.CIAN, paleta.PANEL, i * 0.35),
                                [p(-10 + i * 7, -10), p(-2 + i * 7, 0), p(-10 + i * 7, 10)], r(3))
    elif nombre == "gota":
        pygame.draw.polygon(s, paleta.ROJO, [p(0, -15), p(-9, 2), p(9, 2)])
        pygame.draw.circle(s, paleta.ROJO, p(0, 4), r(9))
        pygame.draw.circle(s, paleta.BLANCO, p(-3, 3), r(2))
    elif nombre == "rayo":
        pygame.draw.polygon(s, paleta.ORO, [p(3, -15), p(-8, 2), p(0, 2), p(-4, 15), p(9, -3), p(1, -3)])
    elif nombre == "arco":
        pygame.draw.arc(s, paleta.CIAN, (*p(-14, -14), r(28), r(28)), 0.3, 2.8, r(4))
        pygame.draw.arc(s, paleta.BLANCO, (*p(-10, -10), r(20), r(20)), 0.5, 2.6, r(2))
    elif nombre == "pluma":
        pygame.draw.ellipse(s, paleta.VERDE, (*p(-5, -14), r(10), r(26)))
        pygame.draw.line(s, paleta.VERDE_OSCURO, p(0, -12), p(0, 15), r(2))
    elif nombre == "moneda":
        pygame.draw.circle(s, paleta.ORO_OSCURO, p(0, 2), r(10))
        pygame.draw.circle(s, paleta.ORO, p(0, 0), r(10))
        pygame.draw.circle(s, paleta.ORO_OSCURO, p(0, 0), r(6), r(2))
    elif nombre == "calavera":
        pygame.draw.circle(s, paleta.HUESO, p(0, -2), r(10))
        pygame.draw.rect(s, paleta.HUESO, (*p(-6, 4), r(12), r(7)))
        pygame.draw.circle(s, paleta.NOCHE, p(-4, -2), r(3))
        pygame.draw.circle(s, paleta.NOCHE, p(4, -2), r(3))
