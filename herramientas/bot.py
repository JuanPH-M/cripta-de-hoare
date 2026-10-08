"""
Bot jugador para pruebas automáticas: navega con BFS sobre la cuadrícula,
ataca al enemigo más cercano, esquiva proyectiles con dash y bebe pociones.
Juega a través de la misma `Entrada` que usa un humano.
"""

import math

from juego.core import config
from juego.sistemas.colisiones import centro_casilla, normalizar
from juego.sistemas.mazmorra import distancias_bfs
from juego.sistemas.objetivo import elegir_objetivo, es_objetivo_valido
from juego.sistemas.partida import Entrada, Partida


_CACHE_BFS: dict = {}


def _mapa_hacia(tiles: list[list[int]], destino: tuple[int, int]) -> dict:
    # Se guarda también la referencia a `tiles`: así su id no se puede reutilizar para el
    # mapa de otro nivel mientras siga en el caché (antes devolvía rutas de un mapa viejo).
    clave = (id(tiles), destino)
    guardado = _CACHE_BFS.get(clave)
    if guardado is None or guardado[0] is not tiles:
        if len(_CACHE_BFS) > 4000:
            _CACHE_BFS.clear()
        guardado = _CACHE_BFS[clave] = (tiles, distancias_bfs(tiles, destino))
    return guardado[1]


def _casilla(x: float, y: float) -> tuple[int, int]:
    return int(x // config.TAM), int(y // config.TAM)


def decidir(p: Partida) -> Entrada:
    j = p.jugador
    vivos = [e for e in p.enemigos if e.vivo]
    if vivos:
        objetivo = min(vivos, key=lambda e: math.hypot(e.x - j.x, e.y - j.y))
        ox, oy = objetivo.x, objetivo.y
    elif p.portal.abierto:
        objetivo = None
        ox, oy = p.portal.x, p.portal.y
    else:
        return Entrada()

    entrada = Entrada()

    # Movimiento: siguiente casilla del camino más corto hacia el objetivo.
    destino = _casilla(ox, oy)
    if p.tiles[destino[1]][destino[0]] == config.MURO:
        destino = _casilla(j.x, j.y)
    mapa = _mapa_hacia(p.tiles, destino)
    cx, cy = _casilla(j.x, j.y)
    mejor = (cx, cy)
    for nx, ny in ((cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)):
        if (nx, ny) in mapa and mapa[(nx, ny)] < mapa.get(mejor, 10**9):
            mejor = (nx, ny)
    if objetivo is not None and es_objetivo_valido(p.tiles, j, objetivo):
        entrada.mover_x, entrada.mover_y = 0.0, 0.0
    elif mejor == (cx, cy):
        entrada.mover_x, entrada.mover_y = normalizar(ox - j.x, oy - j.y)
    else:
        tx, ty = centro_casilla(*mejor)
        entrada.mover_x, entrada.mover_y = normalizar(tx - j.x, ty - j.y)

    # Mismo apuntado automático que un humano con teclado (mismo rango, sin atravesar muros).
    if elegir_objetivo(p.tiles, j, vivos) is not None:
        entrada.atacar = True

    # Dash si un proyectil está por impactar (reacciona solo a la mitad, como un humano).
    for pr in p.proyectiles:
        if math.hypot(pr.x - j.x, pr.y - j.y) < 22 and int(pr.x * 7 + pr.vy * 13) % 2 == 0:
            entrada.dash = True
            break
    if j.vida < j.vida_max * 0.4:
        entrada.pocion = True
    return entrada


def jugar_nivel(p: Partida, segundos: float = 240.0, invencible: bool = False, dt: float = 1 / 60) -> str:
    """Juega un nivel. Devuelve "completado", "victoria", "muerte" o "tiempo"."""
    t = 0.0
    while t < segundos:
        if invencible:
            p.jugador.t_invulnerable = 1.0
        p.actualizar(dt, decidir(p))
        p.tomar_eventos()
        t += dt
        if p.victoria:
            return "victoria"
        if p.completada:
            return "completado"
        if not p.jugador.vivo:
            return "muerte"
    return "tiempo"
