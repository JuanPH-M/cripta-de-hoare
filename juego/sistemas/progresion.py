"""Curva de dificultad, creación de enemigos escalados y mejoras del jugador."""

import random

from juego.core import config
from juego.datos import tablas
from juego.entidades.enemigo import Enemigo
from juego.entidades.jugador import Jugador


def vida_enemigo(tipo: str, nivel: int) -> int:
    base = tablas.ENEMIGOS[tipo]["vida"]
    if tipo == "jefe":
        return base
    return round(base * (1 + tablas.CRECIMIENTO_VIDA * (nivel - 1)))


def ataque_enemigo(tipo: str, nivel: int) -> int:
    base = tablas.ENEMIGOS[tipo]["ataque"]
    if tipo == "jefe":
        return base
    return base + (nivel - 1) // tablas.NIVELES_POR_ATAQUE


def oro_enemigo(tipo: str, nivel: int) -> int:
    base = tablas.ENEMIGOS[tipo]["oro"]
    if base == 0:
        return 0
    return base + (nivel - 1) // tablas.NIVELES_POR_ORO


def crear_enemigo(tipo: str, nivel: int, x: float, y: float, rng: random.Random) -> Enemigo:
    d = tablas.ENEMIGOS[tipo]
    vida = vida_enemigo(tipo, nivel)
    return Enemigo(
        tipo=tipo, nombre=d["nombre"], x=x, y=y,
        vida=vida, vida_max=vida,
        ataque=ataque_enemigo(tipo, nivel), defensa=d["defensa"],
        rapidez=d["rapidez"] * (1 + 0.04 * (nivel - 1)),
        radio=d["radio"], oro=oro_enemigo(tipo, nivel),
        puntos=d["puntos"] * (1 + (nivel - 1) // 2), esquiva=d["esquiva"],
        t_estado=rng.uniform(0.2, 1.0), t_disparo=rng.uniform(1.0, 2.2),
        semilla_anim=rng.uniform(0, 6.28),
    )


# -----------------------------------------------------------------------------
# Mejoras gratuitas entre niveles
# -----------------------------------------------------------------------------

def opciones_mejora(rng: random.Random, cantidad: int = 3) -> list[str]:
    return rng.sample(sorted(tablas.MEJORAS), cantidad)


def aplicar_mejora(j: Jugador, mejora: str) -> None:
    if mejora == "filo":
        j.ataque += 2
    elif mejora == "corazon":
        j.vida_max += 8
        j.vida = min(j.vida_max, j.vida + 8)
    elif mejora == "viento":
        j.rapidez *= 1.12
    elif mejora == "halcon":
        j.critico = min(0.75, j.critico + 0.10)
    elif mejora == "sombra":
        j.enfriamiento_dash *= 0.70
    elif mejora == "sangre":
        j.robo_vida += 1
    elif mejora == "piedra":
        j.defensa += 1
    elif mejora == "furia":
        j.enfriamiento_ataque = max(0.12, j.enfriamiento_ataque * 0.82)
    elif mejora == "amplia":
        j.alcance *= 1.20
    elif mejora == "reflejos":
        j.esquiva = min(0.5, j.esquiva + 0.08)
    else:
        raise ValueError(f"mejora desconocida: {mejora}")


def aplicar_objeto_permanente(j: Jugador, objeto: str) -> None:
    if objeto == "espada":
        j.ataque += 1
    elif objeto == "armadura":
        j.defensa += 1
    elif objeto == "amuleto":
        j.vida_max += 6
        j.vida = min(j.vida_max, j.vida + 6)
    elif objeto == "botas":
        j.rapidez *= 1.08
    elif objeto == "talisman":
        j.critico = min(0.75, j.critico + 0.07)
    else:
        raise ValueError(f"objeto desconocido: {objeto}")


def nombre_nivel(nivel: int) -> str:
    if nivel == config.NIVEL_JEFE:
        return "El trono del Guardián"
    nombres = ["Criptas húmedas", "Galerías del eco", "Osario olvidado", "Pozos de ceniza",
               "Forja hundida", "Catacumbas rojas", "Biblioteca muda", "Abismo de sal",
               "Umbral del vacío"]
    return nombres[nivel - 1]
