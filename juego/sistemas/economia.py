"""
Economía: precios por nivel, oro garantizado por nivel y oferta de la tienda.

Regla de diseño (verificada en tests/test_economia.py):
    precio_más_barato(oferta)  <=  oro_garantizado(nivel)  <  suma_3_más_baratos(oferta)
es decir, el oro de un solo nivel siempre alcanza para 1 objeto útil y nunca
para más de 2, así cada visita a la tienda obliga a elegir.
"""

import random

from juego.core import config
from juego.datos import tablas
from juego.sistemas.mazmorra import Mazmorra
from juego.sistemas.progresion import oro_enemigo


def precio(objeto: str, nivel: int) -> int:
    d = tablas.OBJETOS_TIENDA[objeto]
    return d["base"] + d["inc"] * (nivel - 1)


def oro_garantizado(m: Mazmorra) -> int:
    """
    Oro que el jugador obtiene sí o sí al completar el nivel: las monedas del
    suelo más el botín de todos los enemigos (el portal solo se abre tras
    derrotarlos y entonces todas las monedas vuelan hacia el jugador).
    """
    total = len(m.monedas) * tablas.VALOR_MONEDA
    for tipo, _, _ in m.spawns:
        total += oro_enemigo(tipo, m.nivel)
    return total


def generar_oferta(semilla: int, nivel: int) -> list[str]:
    """Poción y bomba siempre; más dos objetos permanentes al azar."""
    rng = random.Random(semilla * 31 + nivel * 977)
    return ["pocion", "bomba"] + rng.sample(tablas.PERMANENTES, 2)


def precios_oferta(oferta: list[str], nivel: int) -> list[int]:
    return [precio(o, nivel) for o in oferta]


def nivel_de_tienda(nivel_completado: int) -> int:
    """La tienda que aparece tras completar el nivel L cobra precios del nivel L."""
    return max(1, min(nivel_completado, config.NIVELES_MAX - 1))
