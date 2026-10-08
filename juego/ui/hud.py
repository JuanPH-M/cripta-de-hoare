"""HUD en alta resolución: vida, consumibles, progreso de la run, oro y jefe."""

import math

import pygame

from juego.core import config
from juego.sistemas.partida import Partida
from juego.ui import iconos, paleta, textos
from juego.ui.tween import acercar

ALTO = config.ALTO_HUD * config.ESCALA  # 80 px


class Hud:
    def __init__(self) -> None:
        self.vida_mostrada = 0.0     # barra fantasma que persigue a la vida real
        self.oro_mostrado = 0.0
        self.pulso_oro = 0.0
        self._oro_anterior = 0
        self.jefe_mostrado = 1.0

    def reiniciar(self, partida: Partida) -> None:
        self.vida_mostrada = partida.jugador.vida
        self.oro_mostrado = partida.run.oro
        self._oro_anterior = partida.run.oro

    def actualizar(self, dt: float, partida: Partida) -> None:
        j = partida.jugador
        if j.vida > self.vida_mostrada:
            self.vida_mostrada = j.vida
        else:
            self.vida_mostrada = acercar(self.vida_mostrada, j.vida, 3.5, dt)
        oro = partida.run.oro
        if oro != self._oro_anterior:
            self.pulso_oro = 1.0
            self._oro_anterior = oro
        self.oro_mostrado = acercar(self.oro_mostrado, oro, 10, dt)
        self.pulso_oro = max(0.0, self.pulso_oro - dt * 4)
        if partida.jefe is not None:
            self.jefe_mostrado = acercar(self.jefe_mostrado, partida.jefe.vida / partida.jefe.vida_max, 4, dt)

    def dibujar(self, s: pygame.Surface, partida: Partida, t: float) -> None:
        run = partida.run
        j = partida.jugador
        pygame.draw.rect(s, paleta.PANEL, (0, 0, config.ANCHO_VENTANA, ALTO))
        pygame.draw.line(s, paleta.PANEL_BORDE, (0, ALTO - 2), (config.ANCHO_VENTANA, ALTO - 2), 2)

        # --- Vida
        x, y, w, h = 24, 18, 300, 22
        frac = j.vida / j.vida_max
        fantasma = max(0.0, min(1.0, self.vida_mostrada / j.vida_max))
        critico = frac <= 0.25
        pygame.draw.rect(s, paleta.NOCHE, (x - 3, y - 3, w + 6, h + 6), border_radius=6)
        pygame.draw.rect(s, paleta.ROJO_OSCURO, (x, y, w, h), border_radius=4)
        pygame.draw.rect(s, paleta.TEXTO, (x, y, int(w * fantasma), h), border_radius=4)
        color = paleta.ROJO if critico else paleta.VERDE
        if critico:
            color = paleta.mezclar(paleta.ROJO, paleta.BLANCO, 0.25 + 0.25 * math.sin(t * 10))
        pygame.draw.rect(s, color, (x, y, int(w * frac), h), border_radius=4)
        pygame.draw.rect(s, paleta.mezclar(color, paleta.BLANCO, 0.4), (x + 3, y + 3, max(0, int(w * frac) - 6), 4),
                         border_radius=2)
        textos.dibujar(s, f"{j.vida} / {j.vida_max}", x + w / 2, y + h / 2, 17, paleta.TEXTO, True, "center")
        # Dash
        listo = 1 - j.t_dash / max(0.01, j.enfriamiento_dash)
        pygame.draw.rect(s, paleta.NOCHE, (x - 1, y + h + 9, w + 2, 8), border_radius=3)
        pygame.draw.rect(s, paleta.CIAN if listo >= 1 else paleta.CIAN_OSCURO,
                         (x, y + h + 10, int(w * min(1.0, listo)), 6), border_radius=3)
        textos.dibujar(s, "DASH", x + w + 10, y + h + 13, 13, paleta.CIAN if listo >= 1 else paleta.TEXTO_APAGADO,
                       True, "midleft")

        # --- Consumibles
        x0 = 400
        for i, objeto in enumerate(j.inventario):
            r = pygame.Rect(x0 + i * 50, 16, 44, 44)
            pygame.draw.rect(s, paleta.PANEL_CLARO, r, border_radius=8)
            pygame.draw.rect(s, paleta.PANEL_BORDE, r, 2, border_radius=8)
            if objeto == config.POCION:
                iconos.icono(s, "pocion", r.centerx, r.centery, 26)
            elif objeto == config.BOMBA:
                iconos.icono(s, "bomba", r.centerx, r.centery, 26)
        textos.dibujar(s, "Q poción · E bomba", x0 + 97, 68, 12, paleta.TEXTO_SUAVE, False, "center", 1)

        # --- Progreso de la run
        cx = 820
        textos.dibujar(s, f"NIVEL {run.nivel}/{config.NIVELES_MAX}", cx, 22, 22, paleta.ORO, True, "center")
        for n in range(1, config.NIVELES_MAX + 1):
            px = cx - 117 + (n - 1) * 26
            py = 52
            if n == config.NIVEL_JEFE:
                iconos.icono(s, "calavera", px, py, 18 if n != run.nivel else 20 + 2 * math.sin(t * 6))
            elif n < run.nivel:
                pygame.draw.circle(s, paleta.ORO, (px, py), 6)
            elif n == run.nivel:
                pygame.draw.circle(s, paleta.ORO, (px, py), int(7 + 1.5 * math.sin(t * 6)), 2)
            else:
                pygame.draw.circle(s, paleta.TEXTO_APAGADO, (px, py), 4)

        # --- Oro, puntaje y enemigos
        escala = 1 + 0.25 * self.pulso_oro
        iconos.icono(s, "moneda", 1032, 26, 22 * escala)
        textos.dibujar(s, f"{round(self.oro_mostrado)}", 1050, 26, 22, paleta.ORO, True, "midleft")
        textos.dibujar(s, f"{run.puntaje_total():,}".replace(",", "."), 1256, 26, 20, paleta.TEXTO, True, "midright")
        textos.dibujar(s, "PUNTOS", 1256, 50, 12, paleta.TEXTO_SUAVE, False, "midright", 1)
        if partida.jefe is None:
            texto = "Portal abierto" if partida.portal.abierto else f"Enemigos: {partida.vivos}"
            color = paleta.CIAN if partida.portal.abierto else paleta.TEXTO_SUAVE
            textos.dibujar(s, texto, 1032, 56, 14, color, True, "midleft", 1)

    def dibujar_jefe(self, s: pygame.Surface, partida: Partida, t: float, aparicion: float) -> None:
        jefe = partida.jefe
        if jefe is None or not jefe.vivo or aparicion <= 0:
            return
        w = int(640 * aparicion)
        x = config.ANCHO_VENTANA // 2 - w // 2
        y = config.ALTO_VENTANA - 46
        pygame.draw.rect(s, paleta.NOCHE, (x - 4, y - 4, w + 8, 22), border_radius=6)
        pygame.draw.rect(s, paleta.MAGENTA_OSCURO, (x, y, w, 14), border_radius=4)
        pygame.draw.rect(s, paleta.TEXTO, (x, y, int(w * self.jefe_mostrado), 14), border_radius=4)
        pygame.draw.rect(s, paleta.MAGENTA, (x, y, int(w * jefe.vida / jefe.vida_max), 14), border_radius=4)
        for k in (1 / 3, 2 / 3):
            pygame.draw.line(s, paleta.NOCHE, (x + int(w * k), y), (x + int(w * k), y + 13), 2)
        textos.dibujar(s, f"{jefe.nombre.upper()}  ·  FASE {jefe.fase}", config.ANCHO_VENTANA // 2, y - 16,
                       16, paleta.MAGENTA, True, "center", alfa=int(255 * aparicion))
