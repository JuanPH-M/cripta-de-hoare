"""
Dibujo procedural en pixel art (lienzo de baja resolución, sin archivos de imagen).
"""

import math
import random

import pygame

from juego.core import config
from juego.entidades.enemigo import Enemigo
from juego.entidades.jugador import Jugador
from juego.entidades.objetos import Moneda, Portal, Proyectil
from juego.ui import paleta
from juego.ui.paleta import mezclar

T = config.TAM


# =============================================================================
# MAPA
# =============================================================================

def prerender_mapa(tiles: list[list[int]], semilla: int) -> tuple[pygame.Surface, list[tuple[float, float]]]:
    """Devuelve la superficie del mapa y la lista de antorchas (x, y)."""
    rng = random.Random(semilla)
    surf = pygame.Surface((config.ANCHO_MAPA, config.ALTO_MAPA))
    surf.fill(paleta.MURO_RELLENO)
    antorchas = []

    def muro(x, y):
        return not (0 <= x < config.COLUMNAS and 0 <= y < config.FILAS) or tiles[y][x] == config.MURO

    for y in range(config.FILAS):
        for x in range(config.COLUMNAS):
            px, py = x * T, y * T
            if not muro(x, y):
                base = paleta.PISO_A if (x + y) % 2 == 0 else paleta.PISO_B
                pygame.draw.rect(surf, base, (px, py, T, T))
                # Baldosas: juntas y detalles aleatorios
                pygame.draw.line(surf, paleta.PISO_SOMBRA, (px, py + T - 1), (px + T - 1, py + T - 1))
                pygame.draw.line(surf, paleta.PISO_SOMBRA, (px + T - 1, py), (px + T - 1, py + T - 1))
                for _ in range(rng.randint(0, 2)):
                    dx, dy = rng.randint(2, T - 4), rng.randint(2, T - 4)
                    pygame.draw.rect(surf, paleta.PISO_DETALLE, (px + dx, py + dy, 1 + rng.randint(0, 1), 1))
                if rng.random() < 0.06:  # grieta
                    cx, cy = px + rng.randint(3, 12), py + rng.randint(3, 12)
                    pygame.draw.lines(surf, paleta.PISO_SOMBRA, False,
                                      [(cx, cy), (cx + 2, cy + 1), (cx + 3, cy + 3), (cx + 5, cy + 3)])
                # Oclusión ambiental bajo los muros
                if muro(x, y - 1):
                    pygame.draw.rect(surf, paleta.PISO_SOMBRA, (px, py, T, 4))
                    pygame.draw.rect(surf, mezclar(paleta.PISO_SOMBRA, base, 0.5), (px, py + 4, T, 2))
                if muro(x - 1, y):
                    pygame.draw.rect(surf, mezclar(paleta.PISO_SOMBRA, base, 0.4), (px, py, 2, T))

    for y in range(config.FILAS):
        for x in range(config.COLUMNAS):
            if not muro(x, y):
                continue
            px, py = x * T, y * T
            if not muro(x, y + 1):
                # Muro con cara frontal visible (ladrillos)
                pygame.draw.rect(surf, paleta.MURO_FRENTE, (px, py, T, T))
                for fila in range(3):
                    yy = py + 3 + fila * 5
                    pygame.draw.line(surf, paleta.MURO_FRENTE_OSCURO, (px, yy), (px + T - 1, yy))
                    desfase = 0 if fila % 2 == 0 else 5
                    for xx in range(px + desfase, px + T, 10):
                        pygame.draw.line(surf, paleta.MURO_FRENTE_OSCURO, (xx, yy), (xx, yy + 5))
                pygame.draw.rect(surf, paleta.MURO_TOPE, (px, py, T, 3))
                pygame.draw.line(surf, paleta.MURO_TOPE_LUZ, (px, py), (px + T - 1, py))
                pygame.draw.line(surf, paleta.NOCHE, (px, py + T - 1), (px + T - 1, py + T - 1))
                if rng.random() < 0.09 and 2 < x < config.COLUMNAS - 3:
                    antorchas.append((px + T / 2, py + 7))
            else:
                # Parte superior del muro: oscura, con arista clara donde toca el piso
                vecino_piso = any(not muro(x + vx, y + vy) for vx in (-1, 0, 1) for vy in (-1, 0, 1, 2))
                pygame.draw.rect(surf, paleta.MURO_ARISTA if vecino_piso else paleta.MURO_RELLENO, (px, py, T, T))
                if vecino_piso:
                    if not muro(x, y - 1):
                        pygame.draw.line(surf, paleta.MURO_TOPE_LUZ, (px, py), (px + T - 1, py), 2)
                    if not muro(x - 1, y):
                        pygame.draw.line(surf, paleta.MURO_TOPE, (px, py), (px, py + T - 1), 2)
                    if not muro(x + 1, y):
                        pygame.draw.line(surf, paleta.MURO_TOPE, (px + T - 2, py), (px + T - 2, py + T - 1), 2)
                    if rng.random() < 0.25:
                        mancha = (px + rng.randint(3, 11), py + rng.randint(3, 11), 2, 2)
                        pygame.draw.rect(surf, paleta.MURO_FRENTE, mancha)
    return surf, antorchas


def dibujar_antorcha(mundo: pygame.Surface, x: float, y: float, t: float) -> None:
    pygame.draw.rect(mundo, (90, 60, 40), (int(x) - 1, int(y), 3, 5))
    parpadeo = math.sin(t * 13 + x) * 0.8 + math.sin(t * 7.3 + y) * 0.6
    alto = 4 + parpadeo
    pygame.draw.ellipse(mundo, paleta.NARANJA, (int(x) - 2, int(y - alto), 5, int(alto) + 2))
    pygame.draw.ellipse(mundo, paleta.ORO, (int(x) - 1, int(y - alto + 2), 3, max(1, int(alto) - 1)))


# =============================================================================
# ENTIDADES
# =============================================================================

def sombra(mundo: pygame.Surface, x: float, y: float, ancho: float) -> None:
    w = max(4, int(ancho))
    pygame.draw.ellipse(mundo, paleta.PISO_SOMBRA, (int(x - w / 2), int(y - 2), w, 4))


def dibujar_alcance(mundo: pygame.Surface, x: float, y: float, alcance: float, t: float, objetivo) -> None:
    """
    Indicador del alcance del tajo: anillo punteado de radio `alcance` (el mismo
    valor que usan el apuntado y el impacto). Se ilumina si hay un objetivo válido
    y marca a ese enemigo con un pequeño chevrón.
    """
    activo = objetivo is not None
    color = paleta.CIAN if activo else paleta.CIAN_OSCURO
    puntos = max(16, int(alcance * 1.1))
    giro = t * (1.6 if activo else 0.5)
    for i in range(puntos):
        if i % 2:
            continue
        a = giro + math.tau * i / puntos
        mundo.set_at((int(x + math.cos(a) * alcance), int(y + math.sin(a) * alcance)), color)
    if activo:
        ox, oy = int(objetivo.x), int(objetivo.y - objetivo.radio - 4 - abs(math.sin(t * 8)) * 2)
        pygame.draw.lines(mundo, paleta.CIAN, False, [(ox - 2, oy - 2), (ox, oy), (ox + 2, oy - 2)], 1)


def dibujar_jugador(mundo: pygame.Surface, j: Jugador, t: float, t_tajo: float) -> None:
    if j.t_invulnerable > 0 and not j.en_dash and int(t * 20) % 2 == 0:
        return  # parpadeo de invulnerabilidad
    x, y = j.x, j.y
    paso = math.sin(t * 16) if j.moviendose else 0.0
    rebote = abs(paso) * 1.5
    lado = 1 if j.mira_x >= 0 else -1
    estirar = 1.25 if j.en_dash else 1.0

    sombra(mundo, x, y + 6, 10)
    cuerpo_y = y - rebote
    # Capa
    capa = [(x - 5 * estirar, cuerpo_y + 5), (x + 5 * estirar, cuerpo_y + 5),
            (x + 4, cuerpo_y - 3), (x - 4, cuerpo_y - 3)]
    pygame.draw.polygon(mundo, paleta.CIAN_OSCURO, capa)
    pygame.draw.polygon(mundo, paleta.CIAN, [(x - 3, cuerpo_y + 4), (x + 3, cuerpo_y + 4),
                                             (x + 3, cuerpo_y - 2), (x - 3, cuerpo_y - 2)])
    # Pies
    pygame.draw.rect(mundo, paleta.NOCHE, (int(x - 3 + paso), int(y + 4), 2, 2))
    pygame.draw.rect(mundo, paleta.NOCHE, (int(x + 1 - paso), int(y + 4), 2, 2))
    # Cabeza y capucha
    cabeza_y = cuerpo_y - 6
    pygame.draw.circle(mundo, paleta.CIAN_OSCURO, (int(x), int(cabeza_y)), 5)
    pygame.draw.circle(mundo, paleta.PIEL, (int(x + lado), int(cabeza_y + 1)), 3)
    pygame.draw.rect(mundo, paleta.NOCHE, (int(x + lado * 2), int(cabeza_y), 1, 2))
    # Espada en reposo (si no está atacando)
    if t_tajo <= 0:
        ex = x + lado * 6
        pygame.draw.line(mundo, paleta.HUESO, (ex, cuerpo_y + 2), (ex + lado * 2, cuerpo_y - 7), 1)
        pygame.draw.line(mundo, paleta.ORO, (ex - 2, cuerpo_y), (ex + 2, cuerpo_y), 1)


def dibujar_enemigo(mundo: pygame.Surface, e: Enemigo, t: float, px: float, py: float) -> None:
    cuerpo, detalle = paleta.COLOR_ENEMIGO[e.tipo]
    if e.t_flash > 0:
        cuerpo = detalle = paleta.BLANCO
    x, y = e.x, e.y
    fn = {"slime": _slime, "murcielago": _murcielago, "arquero": _arquero, "bruto": _bruto, "jefe": _jefe}[e.tipo]
    fn(mundo, e, x, y, t, cuerpo, detalle, px, py)
    if e.tipo != "jefe" and e.vida < e.vida_max:
        w = int(e.radio * 2 + 4)
        bx, by = int(x - w / 2), int(y - e.radio - 8)
        pygame.draw.rect(mundo, paleta.NOCHE, (bx - 1, by - 1, w + 2, 4))
        pygame.draw.rect(mundo, paleta.ROJO, (bx, by, max(1, int(w * e.vida / e.vida_max)), 2))
    if e.estado == "alerta" and e.tipo != "jefe":
        pygame.draw.rect(mundo, paleta.ORO, (int(x) - 1, int(y - e.radio - 13), 2, 5))
        pygame.draw.rect(mundo, paleta.ORO, (int(x) - 1, int(y - e.radio - 7), 2, 2))


def _slime(m, e, x, y, t, c, d, px, py):
    if e.estado == "salto":
        ancho, alto, elev = 9, 12, 4
    else:
        fase = math.sin(t * 6 + e.semilla_anim)
        ancho, alto, elev = 12 + fase, 9 - fase, 0
    sombra(m, x, y + 5, 11)
    rect = pygame.Rect(0, 0, int(ancho), int(alto))
    rect.midbottom = (int(x), int(y + 5 - elev))
    pygame.draw.ellipse(m, d, rect)
    pygame.draw.ellipse(m, c, rect.inflate(-2, -2))
    pygame.draw.rect(m, paleta.BLANCO, (rect.x + 2, rect.y + 2, 2, 1))
    mira = 1 if px > x else -1
    pygame.draw.rect(m, paleta.NOCHE, (int(x - 2 + mira), rect.centery - 1, 1, 2))
    pygame.draw.rect(m, paleta.NOCHE, (int(x + 2 + mira), rect.centery - 1, 1, 2))


def _murcielago(m, e, x, y, t, c, d, px, py):
    aleteo = math.sin(t * 22 + e.semilla_anim)
    flota = math.sin(t * 4 + e.semilla_anim) * 2
    y = y - 4 + flota
    sombra(m, x, e.y + 6, 7)
    ala = 4 * aleteo
    pygame.draw.polygon(m, d, [(x - 2, y), (x - 8, y - 2 - ala), (x - 6, y + 2)])
    pygame.draw.polygon(m, d, [(x + 2, y), (x + 8, y - 2 - ala), (x + 6, y + 2)])
    pygame.draw.circle(m, c, (int(x), int(y)), 3)
    pygame.draw.rect(m, paleta.ROJO, (int(x) - 2, int(y) - 1, 1, 1))
    pygame.draw.rect(m, paleta.ROJO, (int(x) + 1, int(y) - 1, 1, 1))


def _arquero(m, e, x, y, t, c, d, px, py):
    sombra(m, x, y + 6, 9)
    paso = math.sin(t * 9 + e.semilla_anim) if abs(e.vx) + abs(e.vy) > 1 else 0
    pygame.draw.line(m, d, (x - 2, y + 2), (x - 2 + paso, y + 6))
    pygame.draw.line(m, d, (x + 2, y + 2), (x + 2 - paso, y + 6))
    pygame.draw.rect(m, c, (int(x) - 3, int(y) - 3, 6, 6))
    pygame.draw.line(m, d, (x - 2, y - 1), (x + 2, y - 1))
    pygame.draw.line(m, d, (x - 2, y + 1), (x + 2, y + 1))
    pygame.draw.circle(m, c, (int(x), int(y) - 7), 4)
    pygame.draw.rect(m, paleta.NOCHE, (int(x) - 2, int(y) - 8, 1, 2))
    pygame.draw.rect(m, paleta.NOCHE, (int(x) + 1, int(y) - 8, 1, 2))
    # Arco
    ang = math.atan2(e.dir_y, e.dir_x) if e.estado == "apuntar" else math.atan2(py - y, px - x)
    bx, by = x + math.cos(ang) * 6, y + math.sin(ang) * 6
    perp = ang + math.pi / 2
    p1 = (bx + math.cos(perp) * 5, by + math.sin(perp) * 5)
    p2 = (bx - math.cos(perp) * 5, by - math.sin(perp) * 5)
    pygame.draw.line(m, (150, 100, 60), p1, (bx + math.cos(ang) * 2, by + math.sin(ang) * 2))
    pygame.draw.line(m, (150, 100, 60), p2, (bx + math.cos(ang) * 2, by + math.sin(ang) * 2))
    pygame.draw.line(m, paleta.TEXTO_SUAVE, p1, p2)
    if e.estado == "apuntar":
        # Aviso: línea de mira que se intensifica antes del disparo
        k = 1 - max(0.0, e.t_estado) / 0.6
        largo = 40 + 80 * k
        color = mezclar(paleta.ROJO_OSCURO, paleta.ROJO, k)
        for i in range(0, int(largo), 6):
            a0 = (x + e.dir_x * (8 + i), y + e.dir_y * (8 + i))
            a1 = (x + e.dir_x * (11 + i), y + e.dir_y * (11 + i))
            pygame.draw.line(m, color, a0, a1)


def _bruto(m, e, x, y, t, c, d, px, py):
    temblor = math.sin(t * 60) * 1.2 if e.estado == "preparar" else 0
    x += temblor
    sombra(m, x, y + 8, 16)
    if e.estado == "preparar":
        k = 1 - max(0.0, e.t_estado) / 0.65
        c = mezclar(c, paleta.ROJO, k)
        # flecha de aviso de la embestida
        for i in range(3):
            dist = 12 + i * 6 + k * 4
            cx, cy = x + e.dir_x * dist, y + e.dir_y * dist
            pygame.draw.circle(m, mezclar(paleta.ROJO_OSCURO, paleta.ROJO, k), (int(cx), int(cy)), 2)
    pygame.draw.ellipse(m, d, (int(x) - 8, int(y) - 7, 16, 15))
    pygame.draw.ellipse(m, c, (int(x) - 7, int(y) - 6, 14, 12))
    pygame.draw.rect(m, d, (int(x) - 6, int(y) - 1, 12, 3))
    pygame.draw.polygon(m, paleta.HUESO, [(x - 6, y - 5), (x - 9, y - 10), (x - 4, y - 6)])
    pygame.draw.polygon(m, paleta.HUESO, [(x + 6, y - 5), (x + 9, y - 10), (x + 4, y - 6)])
    mira = 1 if px > x else -1
    ojo = paleta.ORO if e.estado in ("preparar", "carga") else paleta.NOCHE
    pygame.draw.rect(m, ojo, (int(x - 3 + mira), int(y - 4), 2, 2))
    pygame.draw.rect(m, ojo, (int(x + 2 + mira), int(y - 4), 2, 2))
    if e.estado == "aturdido":
        for i in range(3):
            a = t * 6 + i * math.tau / 3
            pygame.draw.rect(m, paleta.ORO, (int(x + math.cos(a) * 7), int(y - 12 + math.sin(a) * 2), 2, 2))


def _jefe(m, e, x, y, t, c, d, px, py):
    flota = math.sin(t * 2) * 2
    sombra(m, x, y + 14, 28)
    y = y + flota - 2
    aura = 15 + math.sin(t * 5) * 1.5
    if e.estado == "telegrafia":
        aura += 3 + math.sin(t * 40) * 1.5
        pygame.draw.circle(m, paleta.MAGENTA, (int(x), int(y)), int(aura + 4), 1)
    pygame.draw.circle(m, d, (int(x), int(y)), int(aura))
    pygame.draw.circle(m, c, (int(x), int(y)), 12)
    # Corona de púas
    for i in range(7):
        a = -math.pi / 2 + (i - 3) * 0.35
        base = (x + math.cos(a) * 11, y + math.sin(a) * 11)
        punta = (x + math.cos(a) * 18, y + math.sin(a) * 18)
        pygame.draw.line(m, paleta.ORO if i % 2 == 0 else paleta.ORO_OSCURO, base, punta, 2)
    # Ojo que sigue al jugador
    ang = math.atan2(py - y, px - x)
    pygame.draw.circle(m, paleta.HUESO, (int(x), int(y + 1)), 6)
    pupila = paleta.ROJO if e.fase >= 2 else paleta.NOCHE
    pygame.draw.circle(m, pupila, (int(x + math.cos(ang) * 3), int(y + 1 + math.sin(ang) * 3)), 3)
    if e.fase >= 3:
        pygame.draw.circle(m, paleta.ORO, (int(x + math.cos(ang) * 3), int(y + 1 + math.sin(ang) * 3)), 1)


def dibujar_moneda(m: pygame.Surface, mo: Moneda, t: float) -> None:
    giro = abs(math.cos(t * 6 + mo.x * 0.3))
    w = max(2, int(6 * giro))
    flota = math.sin(t * 4 + mo.y) * 1 if not mo.atraida else 0
    rect = pygame.Rect(0, 0, w, 6)
    rect.center = (int(mo.x), int(mo.y + flota))
    pygame.draw.ellipse(m, paleta.ORO_OSCURO, rect.move(0, 1))
    pygame.draw.ellipse(m, paleta.ORO, rect)
    if giro > 0.8:
        pygame.draw.rect(m, paleta.BLANCO, (rect.x + 1, rect.y + 1, 1, 1))


def dibujar_proyectil(m: pygame.Surface, pr: Proyectil) -> None:
    if pr.tipo == "flecha":
        ang = math.atan2(pr.vy, pr.vx)
        cola = (pr.x - math.cos(ang) * 7, pr.y - math.sin(ang) * 7)
        pygame.draw.line(m, (150, 100, 60), cola, (pr.x, pr.y), 1)
        pygame.draw.rect(m, paleta.HUESO, (int(pr.x) - 1, int(pr.y) - 1, 2, 2))
    else:
        pygame.draw.circle(m, paleta.MAGENTA, (int(pr.x), int(pr.y)), 3)
        pygame.draw.circle(m, paleta.BLANCO, (int(pr.x), int(pr.y)), 1)


def dibujar_portal(m: pygame.Surface, p: Portal, t: float) -> None:
    x, y = int(p.x), int(p.y)
    if not p.abierto:
        # Círculo rúnico apagado: marca dónde aparecerá la salida
        pygame.draw.ellipse(m, paleta.PISO_SOMBRA, (x - 10, y - 5, 20, 10))
        pygame.draw.ellipse(m, paleta.CIAN_OSCURO, (x - 10, y - 5, 20, 10), 1)
        for i in range(6):
            a = t * 0.6 + i * math.tau / 6
            pygame.draw.rect(m, paleta.CIAN_OSCURO, (int(x + math.cos(a) * 7), int(y + math.sin(a) * 3), 2, 1))
        return
    k = min(1.0, p.t_abierto / 0.6)
    r = 10 * k
    pygame.draw.ellipse(m, paleta.CIAN_OSCURO, (x - r, y - r * 1.3, r * 2, r * 2.6))
    pygame.draw.ellipse(m, paleta.CIAN, (x - r, y - r * 1.3, r * 2, r * 2.6), 1)
    for i in range(8):
        a = t * 3 + i * math.tau / 8
        rr = r * (0.4 + 0.5 * ((t * 0.8 + i * 0.13) % 1))
        pygame.draw.rect(m, paleta.BLANCO if i % 2 else paleta.CIAN,
                         (int(x + math.cos(a) * rr), int(y + math.sin(a) * rr * 1.3), 1, 1))
