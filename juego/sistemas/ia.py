"""
Inteligencia artificial de los enemigos (máquinas de estados simples y legibles).

Todo ataque peligroso tiene un aviso visible (estado "apuntar", "preparar",
"telegrafia") antes de ejecutarse: el jugador siempre puede reaccionar.
"""

import math
from typing import TYPE_CHECKING

from juego.entidades.enemigo import Enemigo
from juego.sistemas.colisiones import mover_con_colisiones, normalizar
from juego.sistemas.navegacion import combinar, separacion, vigilar_atasco
from juego.sistemas.vision import linea_de_vision

if TYPE_CHECKING:
    from juego.sistemas.partida import Partida

RADIO_DESPERTAR = 120.0
RADIO_DESPERTAR_VISION = 210.0


def actualizar(p: "Partida", e: Enemigo, dt: float) -> None:
    e.t_estado -= dt
    e.t_contacto = max(0.0, e.t_contacto - dt)
    e.t_disparo -= dt
    e.t_flash = max(0.0, e.t_flash - dt)

    j = p.jugador
    dx, dy = j.x - e.x, j.y - e.y
    dist = math.hypot(dx, dy)

    if e.estado == "idle":
        ve = dist < RADIO_DESPERTAR or (dist < RADIO_DESPERTAR_VISION
                                        and linea_de_vision(p.tiles, e.x, e.y, j.x, j.y))
        if ve:
            e.estado = "alerta"
            e.t_estado = 0.35
            p.emitir("alerta", e.x, e.y - e.radio - 6)
        _mover(p, e, 0, 0, dt)
        return
    if e.estado == "alerta":
        if e.t_estado <= 0:
            e.estado = "persigue"
            e.t_estado = 0.3
        _mover(p, e, 0, 0, dt)
        return

    comportamiento = {
        "slime": _slime, "murcielago": _murcielago, "arquero": _arquero,
        "bruto": _bruto, "jefe": _jefe,
    }[e.tipo]
    comportamiento(p, e, dt, dx, dy, dist)


def _mover(p: "Partida", e: Enemigo, vx: float, vy: float, dt: float) -> bool:
    """Mueve al enemigo con su velocidad más el retroceso. Devuelve si chocó."""
    amort = math.exp(-9.0 * dt)
    e.empuje_x *= amort
    e.empuje_y *= amort
    e.vx, e.vy = vx, vy
    mx = (vx + e.empuje_x) * dt
    my = (vy + e.empuje_y) * dt
    e.x, e.y, choco = mover_con_colisiones(p.tiles, e.x, e.y, mx, my, e.radio)
    if vigilar_atasco(e, dt, bool(vx or vy)):
        p.navegador.invalidar()          # no avanza: recalcular la ruta y seguirla estrictamente
    return choco


def _rumbo(p: "Partida", e: Enemigo) -> tuple[float, float]:
    """Dirección de persecución: ruta que rodea muros (BFS) + separación de los demás enemigos."""
    j = p.jugador
    return combinar(p.navegador.direccion(e, j.x, j.y), separacion(e, p.enemigos))


# -----------------------------------------------------------------------------

def _slime(p, e, dt, dx, dy, dist):
    """Espera y salta hacia el jugador."""
    if e.estado == "salto":
        _mover(p, e, e.dir_x * e.rapidez * 2.6, e.dir_y * e.rapidez * 2.6, dt)
        if e.t_estado <= 0:
            e.estado = "persigue"
            e.t_estado = p.rng.uniform(0.45, 0.9)
    else:
        _mover(p, e, 0, 0, dt)
        if e.t_estado <= 0:
            e.dir_x, e.dir_y = _rumbo(p, e)
            e.estado = "salto"
            e.t_estado = 0.34


def _murcielago(p, e, dt, dx, dy, dist):
    """Vuelo ondulante hacia el jugador; tras golpear se retira un momento."""
    if e.estado == "retirada":
        _mover(p, e, -e.dir_x * e.rapidez, -e.dir_y * e.rapidez, dt)
        if e.t_estado <= 0:
            e.estado = "persigue"
        return
    nx, ny = _rumbo(p, e)
    # La onda se apaga mientras sigue la ruta estricta tras un atasco (si no, lo empuja contra la esquina).
    onda = 0.0 if e.t_desvio > 0 else math.sin(p.tiempo * 7.0 + e.semilla_anim) * 0.75
    vx = (nx - ny * onda) * e.rapidez
    vy = (ny + nx * onda) * e.rapidez
    _mover(p, e, vx, vy, dt)
    e.dir_x, e.dir_y = nx, ny


def _arquero(p, e, dt, dx, dy, dist):
    """Mantiene la distancia, apunta (aviso) y dispara."""
    j = p.jugador
    if e.estado == "apuntar":
        _mover(p, e, 0, 0, dt)
        if e.t_estado > 0.15:  # deja de seguir al jugador justo antes de disparar
            e.dir_x, e.dir_y = normalizar(dx, dy)
        if e.t_estado <= 0:
            p.disparar(e.x, e.y, e.dir_x * 125, e.dir_y * 125, e.ataque, "flecha")
            e.estado = "persigue"
            e.t_disparo = p.rng.uniform(1.7, 2.4)
        return

    nx, ny = normalizar(dx, dy)
    vision = linea_de_vision(p.tiles, e.x, e.y, j.x, j.y)
    if dist < 64 and e.t_desvio <= 0:
        vx, vy = -nx, -ny
    elif dist > 135 or not vision:
        vx, vy = _rumbo(p, e)
    else:   # mantiene la distancia rodeando al jugador (también si quedó arrinconado al retroceder)
        lado = 1 if math.sin(p.tiempo * 0.9 + e.semilla_anim) > 0 else -1
        vx, vy = -ny * lado * 0.6, nx * lado * 0.6
    _mover(p, e, vx * e.rapidez, vy * e.rapidez, dt)

    if e.t_disparo <= 0 and vision and dist < 180:
        e.estado = "apuntar"
        e.t_estado = 0.6
        e.dir_x, e.dir_y = nx, ny


def _bruto(p, e, dt, dx, dy, dist):
    """Camina, se prepara (aviso) y embiste; si choca contra un muro queda aturdido."""
    if e.estado == "preparar":
        _mover(p, e, 0, 0, dt)
        if e.t_estado <= 0:
            e.estado = "carga"
            e.t_estado = 0.7
        return
    if e.estado == "carga":
        choco = _mover(p, e, e.dir_x * 180, e.dir_y * 180, dt)
        if choco:
            e.estado = "aturdido"
            e.t_estado = 0.9
            p.emitir("impacto_muro", e.x, e.y)
        elif e.t_estado <= 0:
            e.estado = "persigue"
            e.t_disparo = 2.0
        return
    if e.estado == "aturdido":
        _mover(p, e, 0, 0, dt)
        if e.t_estado <= 0:
            e.estado = "persigue"
            e.t_disparo = 1.6
        return

    nx, ny = normalizar(dx, dy)
    rx, ry = _rumbo(p, e)
    _mover(p, e, rx * e.rapidez, ry * e.rapidez, dt)
    if e.t_disparo <= 0 and dist < 105 and linea_de_vision(p.tiles, e.x, e.y, p.jugador.x, p.jugador.y):
        e.estado = "preparar"
        e.t_estado = 0.65
        e.dir_x, e.dir_y = nx, ny


def _jefe(p, e, dt, dx, dy, dist):
    """Tres fases según su vida: ráfagas radiales, disparos dirigidos, embestidas y espirales."""
    fraccion = e.vida / e.vida_max
    fase = 1 if fraccion > 0.66 else (2 if fraccion > 0.33 else 3)
    if fase != e.fase:
        e.fase = fase
        e.estado = "pausa"
        e.t_estado = 1.0
        p.emitir("jefe_fase", e.x, e.y, valor=fase)

    nx, ny = normalizar(dx, dy)

    if e.fase >= 2:
        e.t_invocar -= dt
        if e.t_invocar <= 0:
            e.t_invocar = 7.5 if e.fase == 2 else 6.0
            p.invocar_esbirros(e, 2)

    if e.estado in ("persigue", "pausa"):
        rx, ry = _rumbo(p, e)
        _mover(p, e, rx * e.rapidez * 0.6, ry * e.rapidez * 0.6, dt)
        if e.t_estado <= 0:
            opciones = ["radial", "dirigido"]
            if e.fase >= 2:
                opciones.append("carga")
            if e.fase >= 3:
                opciones.append("espiral")
            e.estado = "telegrafia"
            e.dir_x, e.dir_y = nx, ny
            e.semilla_anim = p.rng.random() * math.tau
            e.t_estado = 0.7 if e.fase == 1 else 0.55
            e.t_disparo = 0.0
            e.ataque_actual = p.rng.choice(opciones)
            p.emitir("jefe_telegrafia", e.x, e.y)
        return

    ataque = e.ataque_actual
    vel_orbe = 68 + 14 * e.fase

    if e.estado == "telegrafia":
        _mover(p, e, 0, 0, dt)
        if ataque in ("dirigido", "carga") and e.t_estado > 0.2:
            e.dir_x, e.dir_y = nx, ny
        if e.t_estado <= 0:
            e.estado = "atacando"
            e.t_estado = {"radial": 0.1, "dirigido": 0.1, "carga": 0.75, "espiral": 1.7}[ataque]
            if ataque == "radial":
                n = 10 + 4 * e.fase
                for k in range(n):
                    a = e.semilla_anim + math.tau * k / n
                    p.disparar(e.x, e.y, math.cos(a) * vel_orbe, math.sin(a) * vel_orbe, e.ataque, "orbe")
            elif ataque == "dirigido":
                n = 3 if e.fase == 1 else 5
                base = math.atan2(e.dir_y, e.dir_x)
                for k in range(n):
                    a = base + (k - (n - 1) / 2) * 0.22
                    p.disparar(e.x, e.y, math.cos(a) * (vel_orbe + 30), math.sin(a) * (vel_orbe + 30),
                               e.ataque, "orbe")
        return

    if e.estado == "atacando":
        if ataque == "carga":
            choco = _mover(p, e, e.dir_x * 200, e.dir_y * 200, dt)
            if choco:
                p.emitir("impacto_muro", e.x, e.y)
                e.t_estado = 0
        elif ataque == "espiral":
            _mover(p, e, 0, 0, dt)
            if e.t_disparo <= 0:
                e.t_disparo = 0.07
                e.semilla_anim += 0.45
                for brazo in (0.0, math.pi):
                    a = e.semilla_anim + brazo
                    p.disparar(e.x, e.y, math.cos(a) * vel_orbe, math.sin(a) * vel_orbe, e.ataque, "orbe")
        else:
            _mover(p, e, 0, 0, dt)
        if e.t_estado <= 0:
            e.estado = "pausa"
            e.t_estado = {1: 1.25, 2: 1.0, 3: 0.8}[e.fase]
