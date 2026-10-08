"""Entidad Jugador: estadísticas persistentes de la run y estado físico del nivel."""

from dataclasses import dataclass, field

from juego.core import config
from juego.datos import tablas


@dataclass
class Jugador:
    # Estadísticas (persisten entre niveles)
    vida_max: int = tablas.JUGADOR_BASE["vida_max"]
    vida: int = tablas.JUGADOR_BASE["vida_max"]
    ataque: int = tablas.JUGADOR_BASE["ataque"]
    defensa: int = tablas.JUGADOR_BASE["defensa"]
    rapidez: float = tablas.JUGADOR_BASE["rapidez"]
    critico: float = tablas.JUGADOR_BASE["critico"]
    esquiva: float = tablas.JUGADOR_BASE["esquiva"]
    enfriamiento_ataque: float = tablas.JUGADOR_BASE["enfriamiento_ataque"]
    alcance: float = tablas.JUGADOR_BASE["alcance"]
    enfriamiento_dash: float = tablas.JUGADOR_BASE["enfriamiento_dash"]
    robo_vida: int = tablas.JUGADOR_BASE["robo_vida"]
    inventario: list[int] = field(
        default_factory=lambda: [config.POCION] + [config.VACIO] * (config.TAM_INVENTARIO - 1))

    # Estado físico (se reinicia en cada nivel)
    x: float = 0.0
    y: float = 0.0
    radio: float = tablas.RADIO_JUGADOR
    mira_x: float = 1.0          # dirección a la que mira (unitaria)
    mira_y: float = 0.0
    t_ataque: float = 0.0        # enfriamiento restante del tajo
    t_dash: float = 0.0          # enfriamiento restante del dash
    t_en_dash: float = 0.0       # tiempo restante del dash en curso
    dash_dx: float = 0.0
    dash_dy: float = 0.0
    t_invulnerable: float = 0.0
    empuje_x: float = 0.0        # retroceso al recibir un golpe
    empuje_y: float = 0.0
    moviendose: bool = False

    @property
    def vivo(self) -> bool:
        return self.vida > 0

    @property
    def en_dash(self) -> bool:
        return self.t_en_dash > 0
