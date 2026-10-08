"""Entidades menores del nivel: proyectiles, monedas y el portal de salida."""

from dataclasses import dataclass


@dataclass
class Proyectil:
    x: float
    y: float
    vx: float
    vy: float
    dano: int
    radio: float = 2.5
    vida: float = 3.0            # segundos antes de desaparecer
    tipo: str = "flecha"         # "flecha" | "orbe"
    activo: bool = True


@dataclass
class Moneda:
    x: float
    y: float
    valor: int = 1
    vx: float = 0.0
    vy: float = 0.0
    t: float = 0.0               # edad, para animación y retardo de recogida
    atraida: bool = False


@dataclass
class Portal:
    x: float
    y: float
    abierto: bool = False
    t_abierto: float = 0.0
