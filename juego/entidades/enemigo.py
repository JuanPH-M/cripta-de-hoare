"""Entidad Enemigo: estado de un enemigo vivo en el nivel actual."""

from dataclasses import dataclass


@dataclass
class Enemigo:
    tipo: str
    nombre: str
    x: float
    y: float
    vida: int
    vida_max: int
    ataque: int
    defensa: int
    rapidez: float
    radio: float
    oro: int
    puntos: int
    esquiva: float

    # Máquina de estados de la IA
    estado: str = "idle"
    t_estado: float = 0.0
    dir_x: float = 0.0
    dir_y: float = 0.0
    vx: float = 0.0
    vy: float = 0.0
    empuje_x: float = 0.0
    empuje_y: float = 0.0
    t_contacto: float = 0.0      # enfriamiento del daño por contacto
    t_disparo: float = 1.0       # enfriamiento de ataques a distancia
    fase: int = 1                # fases del jefe
    ataque_actual: str = "radial"  # patrón elegido por el jefe
    t_invocar: float = 6.0
    t_flash: float = 0.0         # destello blanco al recibir daño (solo visual)
    semilla_anim: float = 0.0

    # Navegación (sistemas/navegacion.py): detector de atasco
    t_atasco: float = 0.0        # tiempo intentando moverse desde la última muestra
    ref_x: float = 0.0           # posición en la última muestra
    ref_y: float = 0.0
    t_desvio: float = 0.0        # > 0: sigue la ruta BFS casilla por casilla

    @property
    def vivo(self) -> bool:
        return self.vida > 0
