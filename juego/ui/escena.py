"""Composición del mundo: mapa, entidades ordenadas por profundidad, luz y efectos."""

import math

import pygame

from juego.core import config
from juego.sistemas.objetivo import elegir_objetivo, rango_ataque
from juego.sistemas.partida import Partida
from juego.ui import sprites
from juego.ui.efectos import Efectos


class Escena:
    def __init__(self, efectos: Efectos) -> None:
        self.efectos = efectos
        self.mundo = pygame.Surface((config.ANCHO_MAPA, config.ALTO_MAPA))
        self.oscuridad = pygame.Surface((config.ANCHO_MAPA, config.ALTO_MAPA), pygame.SRCALPHA)
        self._partida_id = None
        self.fondo: pygame.Surface | None = None
        self.antorchas: list[tuple[float, float]] = []
        self._luces: dict[int, pygame.Surface] = {}
        self.t_tajo = 0.0
        self._t_polvo = 0.0

    def _luz(self, radio: int) -> pygame.Surface:
        """Disco con alfa decreciente para "restar" oscuridad."""
        surf = self._luces.get(radio)
        if surf is None:
            surf = pygame.Surface((radio * 2, radio * 2), pygame.SRCALPHA)
            for r in range(radio, 0, -2):
                a = int(255 * (1 - (r / radio) ** 2))
                pygame.draw.circle(surf, (0, 0, 0, a), (radio, radio), r)
            self._luces[radio] = surf
        return surf

    def preparar(self, partida: Partida) -> None:
        if self._partida_id != id(partida):
            self._partida_id = id(partida)
            self.fondo, self.antorchas = sprites.prerender_mapa(partida.tiles, partida.run.semilla + partida.nivel)

    def actualizar(self, dt: float, partida: Partida) -> None:
        self.t_tajo = max(0.0, self.t_tajo - dt)
        j = partida.jugador
        if j.moviendose and j.vivo:
            self._t_polvo -= dt
            if self._t_polvo <= 0:
                self._t_polvo = 0.05 if j.en_dash else 0.16
                self.efectos.polvo(j.x, j.y + 5)

    def dibujar(self, partida: Partida, t: float) -> pygame.Surface:
        self.preparar(partida)
        m = self.mundo
        m.blit(self.fondo, (0, 0))
        j = partida.jugador

        for ax, ay in self.antorchas:
            sprites.dibujar_antorcha(m, ax, ay, t)
        if partida.jefe is None:  # en la arena del jefe se gana al derrotarlo, no hay portal
            sprites.dibujar_portal(m, partida.portal, t)
        for mo in partida.monedas:
            sprites.dibujar_moneda(m, mo, t)
        if j.vivo:
            objetivo = elegir_objetivo(partida.tiles, j, partida.enemigos)
            sprites.dibujar_alcance(m, j.x, j.y, rango_ataque(j), t, objetivo)

        # Entidades ordenadas por su "y" para dar profundidad.
        entidades = [(e.y, 1, e) for e in partida.enemigos if e.vivo]
        if j.vivo:
            entidades.append((j.y, 0, j))
        entidades.sort(key=lambda par: (par[0], par[1]))
        for _, es_enemigo, ent in entidades:
            if es_enemigo:
                sprites.dibujar_enemigo(m, ent, t, j.x, j.y)
            else:
                sprites.dibujar_jugador(m, ent, t, self.t_tajo)
        for pr in partida.proyectiles:
            sprites.dibujar_proyectil(m, pr)

        self.efectos.dibujar_mundo(m)
        self._iluminar(partida, t)
        return m

    def _iluminar(self, partida: Partida, t: float) -> None:
        m = self.mundo
        j = partida.jugador
        base = min(200, 110 + 9 * partida.nivel)
        self.oscuridad.fill((8, 5, 16, base))
        sub = pygame.BLEND_RGBA_SUB

        def luz(x, y, radio):
            self.oscuridad.blit(self._luz(radio), (x - radio, y - radio), special_flags=sub)

        luz(j.x, j.y, 118 + int(math.sin(t * 2.3) * 3))
        luz(j.x, j.y, 70)
        for ax, ay in self.antorchas:
            luz(ax, ay, 46 + int(math.sin(t * 11 + ax) * 2))
        if partida.portal.abierto:
            luz(partida.portal.x, partida.portal.y, 64)
        for pr in partida.proyectiles:
            if pr.tipo == "orbe":
                luz(pr.x, pr.y, 16)
        if partida.jefe is not None and partida.jefe.vivo:
            luz(partida.jefe.x, partida.jefe.y, 60)
        m.blit(self.oscuridad, (0, 0))

        # Brillo aditivo de fuentes de luz
        add = pygame.BLEND_RGB_ADD
        ef = self.efectos
        for ax, ay in self.antorchas:
            g = ef.resplandor(14, (90, 46, 12))
            m.blit(g, (ax - 14, ay - 18), special_flags=add)
        if partida.portal.abierto:
            g = ef.resplandor(26, (20, 70, 90))
            m.blit(g, (partida.portal.x - 26, partida.portal.y - 26), special_flags=add)
        for pr in partida.proyectiles:
            g = ef.resplandor(8, (90, 30, 100) if pr.tipo == "orbe" else (40, 30, 20))
            m.blit(g, (pr.x - 8, pr.y - 8), special_flags=add)
        for mo in partida.monedas:
            g = ef.resplandor(5, (60, 46, 10))
            m.blit(g, (mo.x - 5, mo.y - 5), special_flags=add)
        if j.en_dash:
            g = ef.resplandor(16, (20, 60, 70))
            m.blit(g, (j.x - 16, j.y - 16), special_flags=add)
