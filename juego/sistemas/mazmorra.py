"""
Generación procedural de mazmorras (salas + pasillos de 2 casillas de ancho).

Determinista: la misma (semilla, nivel) produce siempre la misma mazmorra.
"""

import random
from collections import deque
from dataclasses import dataclass, field

from juego.core import config
from juego.datos import tablas

Sala = tuple[int, int, int, int]  # (x, y, ancho, alto) en casillas


@dataclass
class Mazmorra:
    nivel: int
    tiles: list[list[int]]
    inicio: tuple[int, int]
    salida: tuple[int, int]
    salas: list[Sala] = field(default_factory=list)
    spawns: list[tuple[str, int, int]] = field(default_factory=list)
    monedas: list[tuple[int, int]] = field(default_factory=list)


def generar_mazmorra(semilla: int, nivel: int) -> Mazmorra:
    """
    {P}: 1 <= nivel <= NIVELES_MAX
    {Q}: mazmorra con borde de muros, todo el piso conexo desde el inicio,
         enemigos y monedas sobre piso alcanzable.
    """
    assert 1 <= nivel <= config.NIVELES_MAX, "nivel fuera de rango"
    rng = random.Random(semilla * 7919 + nivel * 104729)
    if nivel == config.NIVEL_JEFE:
        return _arena_jefe(nivel)

    for _ in range(50):
        mazmorra = _intentar_generar(rng, nivel)
        if mazmorra is not None:
            return mazmorra
    raise RuntimeError("no se pudo generar la mazmorra")  # no ocurre en la práctica


# -----------------------------------------------------------------------------

def _rejilla_llena() -> list[list[int]]:
    return [[config.MURO] * config.COLUMNAS for _ in range(config.FILAS)]


def _excavar(tiles: list[list[int]], x: int, y: int) -> None:
    if 1 <= x < config.COLUMNAS - 1 and 1 <= y < config.FILAS - 1:
        tiles[y][x] = config.PISO


def _centro(sala: Sala) -> tuple[int, int]:
    x, y, w, h = sala
    return x + w // 2, y + h // 2


def _se_solapan(a: Sala, b: Sala, margen: int = 2) -> bool:
    return not (a[0] + a[2] + margen <= b[0] or b[0] + b[2] + margen <= a[0]
                or a[1] + a[3] + margen <= b[1] or b[1] + b[3] + margen <= a[1])


def _pasillo(tiles: list[list[int]], a: tuple[int, int], b: tuple[int, int], rng: random.Random) -> None:
    """Pasillo en L de 2 casillas de ancho entre dos puntos."""
    (x1, y1), (x2, y2) = a, b
    if rng.random() < 0.5:
        esquina = (x2, y1)
    else:
        esquina = (x1, y2)
    for (ax, ay), (bx, by) in (((x1, y1), esquina), (esquina, (x2, y2))):
        for x in range(min(ax, bx), max(ax, bx) + 2):
            for y in range(min(ay, by), max(ay, by) + 2):
                _excavar(tiles, x, y)


def _intentar_generar(rng: random.Random, nivel: int) -> Mazmorra | None:
    tiles = _rejilla_llena()
    salas: list[Sala] = []
    objetivo = rng.randint(6, 8)
    intentos = 0
    while len(salas) < objetivo and intentos < 400:
        intentos += 1
        w = rng.randint(5, 10)
        h = rng.randint(4, 7)
        x = rng.randint(1, config.COLUMNAS - w - 2)
        y = rng.randint(1, config.FILAS - h - 2)
        nueva = (x, y, w, h)
        if all(not _se_solapan(nueva, s) for s in salas):
            salas.append(nueva)
    if len(salas) < 5:
        return None

    for x, y, w, h in salas:
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                _excavar(tiles, xx, yy)

    # Conectar en orden horizontal y añadir un par de ciclos extra.
    salas.sort(key=lambda s: s[0])
    for i in range(len(salas) - 1):
        _pasillo(tiles, _centro(salas[i]), _centro(salas[i + 1]), rng)
    for _ in range(2):
        a, b = rng.sample(salas, 2)
        _pasillo(tiles, _centro(a), _centro(b), rng)

    inicio = _centro(salas[0])
    distancias = distancias_bfs(tiles, inicio)
    sala_salida = max(salas[1:], key=lambda s: distancias.get(_centro(s), -1))
    salida = _centro(sala_salida)
    if salida not in distancias:
        return None

    mazmorra = Mazmorra(nivel, tiles, inicio, salida, salas)
    _poblar(mazmorra, rng, distancias)
    return mazmorra


def _poblar(m: Mazmorra, rng: random.Random, distancias: dict[tuple[int, int], int]) -> None:
    curva = tablas.CURVA[m.nivel - 1]
    sala_inicio = m.salas[0]
    candidatas = []
    for (x, y), d in distancias.items():
        sx, sy, sw, sh = sala_inicio
        en_sala_inicio = sx - 1 <= x <= sx + sw and sy - 1 <= y <= sy + sh
        if d >= 9 and not en_sala_inicio and (x, y) != m.salida:
            candidatas.append((x, y))
    candidatas.sort()
    rng.shuffle(candidatas)

    tipos = list(curva["mezcla"].keys())
    pesos = list(curva["mezcla"].values())
    for i in range(min(curva["enemigos"], len(candidatas))):
        tipo = rng.choices(tipos, pesos)[0]
        x, y = candidatas[i]
        m.spawns.append((tipo, x, y))

    libres = sorted(p for p in distancias if p != m.inicio and p != m.salida)
    rng.shuffle(libres)
    m.monedas = libres[:curva["monedas"]]


def _arena_jefe(nivel: int) -> Mazmorra:
    tiles = _rejilla_llena()
    for y in range(2, config.FILAS - 2):
        for x in range(3, config.COLUMNAS - 3):
            tiles[y][x] = config.PISO
    # Pilares para cubrirse de las ráfagas.
    for px, py in ((10, 6), (28, 6), (10, 12), (28, 12)):
        for dy in range(2):
            for dx in range(2):
                tiles[py + dy][px + dx] = config.MURO
    inicio = (config.COLUMNAS // 2, config.FILAS - 4)
    salida = (config.COLUMNAS // 2, config.FILAS // 2)
    m = Mazmorra(nivel, tiles, inicio, salida, [(3, 2, config.COLUMNAS - 6, config.FILAS - 4)])
    m.spawns.append(("jefe", config.COLUMNAS // 2, 5))
    return m


# -----------------------------------------------------------------------------
# Consultas sobre el mapa
# -----------------------------------------------------------------------------

def distancias_bfs(tiles: list[list[int]], origen: tuple[int, int]) -> dict[tuple[int, int], int]:
    """Distancia en pasos (4 vecinos) desde origen a cada casilla de piso alcanzable."""
    dist = {origen: 0}
    cola = deque([origen])
    while cola:
        x, y = cola.popleft()
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if (0 <= nx < config.COLUMNAS and 0 <= ny < config.FILAS
                    and tiles[ny][nx] == config.PISO and (nx, ny) not in dist):
                dist[(nx, ny)] = dist[(x, y)] + 1
                cola.append((nx, ny))
    return dist


def es_conexa(m: Mazmorra) -> bool:
    """True si todo el piso es alcanzable desde el inicio."""
    alcanzables = distancias_bfs(m.tiles, m.inicio)
    total_piso = sum(fila.count(config.PISO) for fila in m.tiles)
    return len(alcanzables) == total_piso
