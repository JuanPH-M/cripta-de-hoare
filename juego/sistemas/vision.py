"""
Línea de visión exacta sobre la cuadrícula (recorrido DDA de Amanatides-Woo).

Se usa para todo lo que no debe atravesar paredes: el tajo y la bomba del
jugador, los proyectiles, el despertar y la puntería de los enemigos y la
navegación. A diferencia de un muestreo cada N píxeles, el DDA visita *todas*
las casillas que cruza el segmento, así que no se "cuela" por las esquinas.
"""

import math

from juego.core import config
from juego.sistemas.colisiones import es_muro as _muro


def linea_de_vision(tiles: list[list[int]], x0: float, y0: float, x1: float, y1: float) -> bool:
    """
    True si el segmento (x0, y0) -> (x1, y1) no cruza ninguna casilla de muro.
    La casilla de origen no se comprueba (es donde está quien mira); la de destino sí.
    Si el segmento pasa justo por la esquina de dos casillas, basta con que una sea
    muro para bloquearlo (no se ve a través de rendijas diagonales).
    """
    t = config.TAM
    tx, ty = int(x0 // t), int(y0 // t)
    tx1, ty1 = int(x1 // t), int(y1 // t)
    dx, dy = x1 - x0, y1 - y0
    paso_x = 1 if dx > 0 else -1
    paso_y = 1 if dy > 0 else -1
    if dx != 0:
        borde_x = (tx + 1) * t if dx > 0 else tx * t
        t_max_x, t_delta_x = (borde_x - x0) / dx, t / abs(dx)
    else:
        t_max_x = t_delta_x = math.inf
    if dy != 0:
        borde_y = (ty + 1) * t if dy > 0 else ty * t
        t_max_y, t_delta_y = (borde_y - y0) / dy, t / abs(dy)
    else:
        t_max_y = t_delta_y = math.inf

    # Cada vuelta acerca (tx, ty) al destino en al menos un eje: como mucho |Δtx| + |Δty| pasos.
    for _ in range(abs(tx1 - tx) + abs(ty1 - ty)):
        if (tx, ty) == (tx1, ty1):
            break
        if t_max_x < t_max_y:
            tx += paso_x
            t_max_x += t_delta_x
        elif t_max_y < t_max_x:
            ty += paso_y
            t_max_y += t_delta_y
        else:  # cruza exactamente una esquina
            if _muro(tiles, tx + paso_x, ty) or _muro(tiles, tx, ty + paso_y):
                return False
            tx += paso_x
            ty += paso_y
            t_max_x += t_delta_x
            t_max_y += t_delta_y
        if _muro(tiles, tx, ty):
            return False
    return True


def camino_libre(tiles: list[list[int]], x0: float, y0: float, x1: float, y1: float, radio: float) -> bool:
    """
    True si un círculo de `radio` puede ir en línea recta de (x0, y0) a (x1, y1):
    se comprueban el eje central y las dos líneas paralelas desplazadas ±radio.
    """
    if not linea_de_vision(tiles, x0, y0, x1, y1):
        return False
    d = math.hypot(x1 - x0, y1 - y0)
    if d < 1e-9 or radio <= 0:
        return True
    px, py = -(y1 - y0) / d * radio, (x1 - x0) / d * radio
    return (linea_de_vision(tiles, x0 + px, y0 + py, x1 + px, y1 + py)
            and linea_de_vision(tiles, x0 - px, y0 - py, x1 - px, y1 - py))
