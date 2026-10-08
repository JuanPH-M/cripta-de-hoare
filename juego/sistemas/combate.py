"""Resolución de golpes usando las funciones verificadas."""

import random
from dataclasses import dataclass

from juego.verificacion.funciones import (
    EMPATE, GANA, aplicar_dano, clasificar_combate,
)


@dataclass
class Golpe:
    resultado: str      # "esquiva" | "gana" | "empate" | "pierde"
    dano: int
    critico: bool


def resolver_golpe(rng: random.Random, ataque: int, defensa: int,
                   prob_esquiva: float, prob_critico: float = 0.0) -> Golpe:
    """
    Tira los dados (crítico y esquiva) y clasifica el golpe.
      gana   -> daño = ataque - defensa
      empate -> daño = 1 (roce)
      pierde -> daño = 0 (bloqueado por la armadura)
      esquiva-> daño = 0
    """
    critico = rng.random() < prob_critico
    ataque_real = ataque * 2 if critico else ataque
    esquiva = rng.random() < prob_esquiva
    resultado = clasificar_combate(ataque_real, defensa, esquiva)
    if resultado == GANA:
        dano = ataque_real - defensa
    elif resultado == EMPATE:
        dano = 1
    else:
        dano = 0
    return Golpe(resultado, dano, critico and resultado == GANA)


def recibir_dano(vida: int, golpe: Golpe) -> int:
    """Nueva vida tras el golpe (nunca negativa)."""
    return aplicar_dano(vida, golpe.dano)
