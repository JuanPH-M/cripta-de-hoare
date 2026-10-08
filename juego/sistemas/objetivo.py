"""
Selección de objetivo del tajo del jugador.

Hay UN solo rango de ataque: `Jugador.alcance` (lo modifica la bendición
"Hoja amplia", +20 % acumulable). Lo leen igual el apuntado automático, la
comprobación de impacto del tajo, el indicador visual y el bot de pruebas.
Un enemigo es objetivo válido si está vivo, su borde está dentro del alcance
y no hay pared entre él y el jugador.
"""

import math

from juego.entidades.enemigo import Enemigo
from juego.entidades.jugador import Jugador
from juego.sistemas.vision import linea_de_vision


def rango_ataque(j: Jugador) -> float:
    return j.alcance


def en_alcance(j: Jugador, x: float, y: float, radio: float) -> bool:
    """El borde del círculo (x, y, radio) está a distancia <= alcance del centro del jugador."""
    return math.hypot(x - j.x, y - j.y) - radio <= rango_ataque(j)


def es_objetivo_valido(tiles: list[list[int]], j: Jugador, e: Enemigo) -> bool:
    return e.vivo and en_alcance(j, e.x, e.y, e.radio) and linea_de_vision(tiles, j.x, j.y, e.x, e.y)


def elegir_objetivo(tiles: list[list[int]], j: Jugador, enemigos: list[Enemigo]) -> Enemigo | None:
    """
    El enemigo válido más cercano (por distancia al borde), o None.
    Se llama en cada tajo, así que si el objetivo anterior murió o salió del
    alcance se elige de inmediato el siguiente válido. Recorrido O(n) único;
    la línea de visión solo se calcula para quien ya está vivo y al alcance.
    """
    mejor, mejor_d = None, math.inf
    for e in enemigos:
        if not e.vivo:
            continue
        d = math.hypot(e.x - j.x, e.y - j.y) - e.radio
        if d <= rango_ataque(j) and d < mejor_d and linea_de_vision(tiles, j.x, j.y, e.x, e.y):
            mejor, mejor_d = e, d
    return mejor
