"""Texto nítido en alta resolución con contorno y caché de superficies."""

import pygame

from juego.ui import paleta

_FAMILIA = "bahnschrift,segoeui,trebuchetms,arial"
_fuentes: dict[tuple[int, bool], pygame.font.Font] = {}
_cache: dict[tuple, pygame.Surface] = {}


def fuente(tam: int, negrita: bool = False) -> pygame.font.Font:
    clave = (tam, negrita)
    if clave not in _fuentes:
        _fuentes[clave] = pygame.font.SysFont(_FAMILIA, tam, bold=negrita)
    return _fuentes[clave]


def render(texto: str, tam: int, color=paleta.TEXTO, negrita: bool = False,
           contorno: int = 2, color_contorno=paleta.NOCHE) -> pygame.Surface:
    clave = (texto, tam, color, negrita, contorno, color_contorno)
    surf = _cache.get(clave)
    if surf is not None:
        return surf
    f = fuente(tam, negrita)
    base = f.render(texto, True, color)
    if contorno <= 0:
        surf = base
    else:
        borde = f.render(texto, True, color_contorno)
        w, h = base.get_width() + contorno * 2, base.get_height() + contorno * 2
        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        for ox in range(-contorno, contorno + 1):
            for oy in range(-contorno, contorno + 1):
                if ox * ox + oy * oy <= contorno * contorno + 1:
                    surf.blit(borde, (ox + contorno, oy + contorno))
        surf.blit(base, (contorno, contorno))
    if len(_cache) > 600:
        _cache.clear()
    _cache[clave] = surf
    return surf


def dibujar(destino: pygame.Surface, texto: str, x: float, y: float, tam: int = 20,
            color=paleta.TEXTO, negrita: bool = False, ancla: str = "topleft",
            contorno: int = 2, alfa: int = 255, escala: float = 1.0) -> pygame.Rect:
    surf = render(texto, tam, color, negrita, contorno)
    if escala != 1.0:
        surf = pygame.transform.smoothscale(
            surf, (max(1, int(surf.get_width() * escala)), max(1, int(surf.get_height() * escala))))
    if alfa < 255:
        surf = surf.copy()
        surf.set_alpha(max(0, alfa))
    rect = surf.get_rect(**{ancla: (int(x), int(y))})
    destino.blit(surf, rect)
    return rect
