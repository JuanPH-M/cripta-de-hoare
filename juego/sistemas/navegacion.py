"""
Navegación de los enemigos: campo de distancias BFS, separación y detector de atasco.

- `Navegador.direccion` devuelve hacia dónde caminar para llegar a un punto:
  en línea recta si el cuerpo del enemigo cabe sin tocar muros
  (`vision.camino_libre`); si no, sigue el camino más corto del BFS sobre la
  cuadrícula y apunta a la casilla más lejana de ese camino que ya se ve
  directamente (así rodea las esquinas sin engancharse).
- El campo BFS se calcula una vez por casilla destino y lo comparten todos los
  enemigos (800 casillas, se recalcula solo cuando el jugador cambia de casilla).
- `separacion` empuja suavemente a los enemigos cercanos para que no se
  amontonen en el mismo punto.
- `vigilar_atasco` detecta a un enemigo que quiere moverse pero no avanza y lo
  obliga a seguir la ruta casilla por casilla durante un rato.
"""

import math

from juego.core import config
from juego.entidades.enemigo import Enemigo
from juego.sistemas.colisiones import centro_casilla, mover_con_colisiones, normalizar
from juego.sistemas.mazmorra import distancias_bfs
from juego.sistemas.vision import camino_libre

VENTANA_ATASCO = 0.8      # segundos (de querer moverse) entre dos muestras de posición
AVANCE_MINIMO = 4.0       # px que debe avanzar en esa ventana para no considerarse atascado
DURACION_DESVIO = 1.5     # segundos siguiendo la ruta estricta tras un atasco
PASOS_SUAVIZADO = 5       # casillas del camino que se intentan "ver" para cortar esquinas
MARGEN_SEPARACION = 6.0   # px extra entre bordes antes de empezar a separar
FUERZA_SEPARACION = 0.9

_VECINOS = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))


def _casilla(x: float, y: float) -> tuple[int, int]:
    return int(x // config.TAM), int(y // config.TAM)


class Navegador:
    def __init__(self, tiles: list[list[int]]):
        self.tiles = tiles
        self._destino: tuple[int, int] | None = None
        self._dist: dict[tuple[int, int], int] = {}

    def invalidar(self) -> None:
        """Fuerza a recalcular el campo BFS en la próxima consulta."""
        self._destino = None

    def _campo(self, destino: tuple[int, int]) -> dict[tuple[int, int], int]:
        if destino != self._destino:
            self._destino = destino
            self._dist = distancias_bfs(self.tiles, destino)
        return self._dist

    def _siguiente(self, dist: dict, c: tuple[int, int]) -> tuple[int, int] | None:
        """Vecino (8 direcciones, sin cortar esquinas de muro) con menor distancia que c."""
        mejor, mejor_d = None, dist[c]
        for vx, vy in _VECINOS:
            n = (c[0] + vx, c[1] + vy)
            if n not in dist or dist[n] >= mejor_d:
                continue
            if vx and vy and ((c[0] + vx, c[1]) not in dist or (c[0], c[1] + vy) not in dist):
                continue
            mejor, mejor_d = n, dist[n]
        return mejor

    def direccion(self, e: Enemigo, ox: float, oy: float) -> tuple[float, float]:
        """Dirección unitaria (o nula) para que `e` avance hacia (ox, oy) sin atascarse."""
        estricto = e.t_desvio > 0
        if not estricto and camino_libre(self.tiles, e.x, e.y, ox, oy, e.radio):
            return normalizar(ox - e.x, oy - e.y)
        dist = self._campo(_casilla(ox, oy))
        actual = _casilla(e.x, e.y)
        if actual not in dist:
            return normalizar(ox - e.x, oy - e.y)
        paso = self._siguiente(dist, actual)
        if paso is None:                       # ya está en la casilla destino
            return normalizar(ox - e.x, oy - e.y)
        meta = centro_casilla(*paso)
        if not estricto:
            # Suavizado: la casilla más lejana del camino que ya se alcanza en línea recta.
            c = paso
            for _ in range(PASOS_SUAVIZADO - 1):
                c = self._siguiente(dist, c)
                if c is None:
                    break
                cx, cy = centro_casilla(*c)
                if not camino_libre(self.tiles, e.x, e.y, cx, cy, e.radio):
                    break
                meta = (cx, cy)
        return normalizar(meta[0] - e.x, meta[1] - e.y)


def separacion(e: Enemigo, enemigos: list[Enemigo]) -> tuple[float, float]:
    """Suma de repulsiones de los vecinos vivos cercanos (un recorrido O(n))."""
    sx = sy = 0.0
    for o in enemigos:
        if o is e or not o.vivo:
            continue
        dx, dy = e.x - o.x, e.y - o.y
        rango = e.radio + o.radio + MARGEN_SEPARACION
        d2 = dx * dx + dy * dy
        if d2 >= rango * rango:
            continue
        d = math.sqrt(d2)
        if d < 1e-6:                           # misma posición: separar según el índice de memoria
            dx, dy, d = (1.0, 0.0, 1.0) if id(e) > id(o) else (-1.0, 0.0, 1.0)
        k = 1.0 - d / rango
        sx += dx / d * k
        sy += dy / d * k
    return sx * FUERZA_SEPARACION, sy * FUERZA_SEPARACION


def combinar(direccion: tuple[float, float], empuje: tuple[float, float]) -> tuple[float, float]:
    """Dirección de ruta + separación, renormalizada (módulo <= 1)."""
    dx, dy = direccion[0] + empuje[0], direccion[1] + empuje[1]
    if dx * dx + dy * dy <= 1.0:
        return dx, dy
    return normalizar(dx, dy)


def resolver_solapes(tiles: list[list[int]], enemigos: list[Enemigo]) -> None:
    """
    Corrección dura: si dos enemigos vivos se superponen, los separa a medias
    (el jefe no se mueve). Recorre los pares i < k del mismo arreglo, sin copias.
    """
    n = len(enemigos)
    for i in range(n):
        a = enemigos[i]
        if not a.vivo:
            continue
        for k in range(i + 1, n):
            b = enemigos[k]
            if not b.vivo:
                continue
            dx, dy = b.x - a.x, b.y - a.y
            minimo = a.radio + b.radio
            d2 = dx * dx + dy * dy
            if d2 >= minimo * minimo:
                continue
            d = math.sqrt(d2) or 0.01
            empuje = (minimo - d) / 2
            nx, ny = dx / d, dy / d
            if a.tipo != "jefe":
                a.x, a.y, _ = mover_con_colisiones(tiles, a.x, a.y, -nx * empuje, -ny * empuje, a.radio)
            if b.tipo != "jefe":
                b.x, b.y, _ = mover_con_colisiones(tiles, b.x, b.y, nx * empuje, ny * empuje, b.radio)


def vigilar_atasco(e: Enemigo, dt: float, quiere_moverse: bool) -> bool:
    """
    Acumula el tiempo que el enemigo intenta moverse; cada VENTANA_ATASCO segundos
    compara su posición con la muestra anterior. Si avanzó menos de AVANCE_MINIMO
    activa el desvío (ruta estricta casilla por casilla). Devuelve True al detectarlo.
    """
    e.t_desvio = max(0.0, e.t_desvio - dt)
    if not quiere_moverse:
        return False
    e.t_atasco += dt
    if e.t_atasco < VENTANA_ATASCO:
        return False
    avance = math.hypot(e.x - e.ref_x, e.y - e.ref_y)
    e.t_atasco = 0.0
    e.ref_x, e.ref_y = e.x, e.y
    if avance < AVANCE_MINIMO:
        e.t_desvio = DURACION_DESVIO
        return True
    return False
