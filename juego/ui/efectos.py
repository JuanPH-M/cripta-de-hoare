"""
Efectos de sensación de juego: partículas, sacudida de cámara por "trauma",
congelamiento al golpear (hitstop), destellos, ondas expansivas, tajos y
números de daño flotantes.
"""

import math
import random
from dataclasses import dataclass

import pygame

from juego.core import config
from juego.ui import paleta, textos
from juego.ui.tween import ease_out_back, ease_out_cubic


@dataclass
class Particula:
    x: float
    y: float
    vx: float
    vy: float
    vida: float
    vida_max: float
    color: tuple
    tam: float
    gravedad: float = 0.0
    friccion: float = 3.0
    brillo: bool = False


@dataclass
class TextoFlotante:
    texto: str
    x: float
    y: float
    color: tuple
    vida: float
    vida_max: float
    tam: int
    vx: float


@dataclass
class Onda:
    x: float
    y: float
    radio_max: float
    vida: float
    vida_max: float
    color: tuple
    grosor: int = 2


@dataclass
class Tajo:
    x: float
    y: float
    angulo: float
    alcance: float
    vida: float = 0.13
    vida_max: float = 0.13


class Efectos:
    def __init__(self) -> None:
        self.rng = random.Random()
        self.particulas: list[Particula] = []
        self.textos: list[TextoFlotante] = []
        self.ondas: list[Onda] = []
        self.tajos: list[Tajo] = []
        self.trauma = 0.0
        self.hitstop = 0.0
        self.flash_color = paleta.BLANCO
        self.flash = 0.0
        self.dano_vineta = 0.0
        self.offset = (0, 0)
        self._tiempo = 0.0
        self._resplandor_cache: dict[tuple, pygame.Surface] = {}

    # ---------------------------------------------------------------- disparadores
    def sacudir(self, cantidad: float) -> None:
        self.trauma = min(1.0, self.trauma + cantidad)

    def congelar(self, segundos: float) -> None:
        self.hitstop = max(self.hitstop, segundos)

    def destello(self, color: tuple, intensidad: float = 1.0) -> None:
        self.flash_color = color
        self.flash = max(self.flash, intensidad)

    def estallido(self, x: float, y: float, color: tuple, cantidad: int = 12, velocidad: float = 90,
                  tam: float = 2.0, vida: float = 0.5, gravedad: float = 0.0, brillo: bool = False) -> None:
        for _ in range(cantidad):
            a = self.rng.random() * math.tau
            v = velocidad * self.rng.uniform(0.35, 1.0)
            t = vida * self.rng.uniform(0.6, 1.2)
            self.particulas.append(Particula(x, y, math.cos(a) * v, math.sin(a) * v, t, t, color,
                                             tam * self.rng.uniform(0.7, 1.3), gravedad, 3.5, brillo))

    def chispas(self, x: float, y: float, angulo: float, color: tuple, cantidad: int = 6,
                abertura: float = 0.9) -> None:
        for _ in range(cantidad):
            a = angulo + self.rng.uniform(-abertura, abertura)
            v = self.rng.uniform(60, 160)
            t = self.rng.uniform(0.12, 0.3)
            self.particulas.append(Particula(x, y, math.cos(a) * v, math.sin(a) * v, t, t, color, 1.5,
                                             0, 6, True))

    def polvo(self, x: float, y: float) -> None:
        t = self.rng.uniform(0.25, 0.45)
        self.particulas.append(Particula(x + self.rng.uniform(-2, 2), y, self.rng.uniform(-8, 8),
                                         self.rng.uniform(-14, -4), t, t, paleta.PISO_DETALLE, 2.2, 0, 2))

    def ascenso(self, x: float, y: float, color: tuple, cantidad: int = 10) -> None:
        for _ in range(cantidad):
            t = self.rng.uniform(0.5, 0.9)
            self.particulas.append(Particula(x + self.rng.uniform(-6, 6), y + self.rng.uniform(-4, 6),
                                             self.rng.uniform(-6, 6), self.rng.uniform(-45, -20), t, t,
                                             color, 1.6, 0, 1, True))

    def texto(self, texto: str, x: float, y: float, color: tuple, tam: int = 20, vida: float = 0.75) -> None:
        self.textos.append(TextoFlotante(texto, x, y, color, vida, vida, tam, self.rng.uniform(-12, 12)))

    def onda(self, x: float, y: float, radio: float, color: tuple, vida: float = 0.35, grosor: int = 2) -> None:
        self.ondas.append(Onda(x, y, radio, vida, vida, color, grosor))

    def tajo(self, x: float, y: float, angulo_grados: float, alcance: float) -> None:
        self.tajos.append(Tajo(x, y, math.radians(angulo_grados), alcance))

    # ---------------------------------------------------------------- actualización
    def actualizar(self, dt: float) -> None:
        self._tiempo += dt
        self.hitstop = max(0.0, self.hitstop - dt)
        self.trauma = max(0.0, self.trauma - dt * 1.6)
        self.flash = max(0.0, self.flash - dt * 4.0)
        self.dano_vineta = max(0.0, self.dano_vineta - dt * 1.8)
        amp = 7.0 * self.trauma * self.trauma
        self.offset = (round(amp * math.sin(self._tiempo * 61.0)), round(amp * math.cos(self._tiempo * 47.0)))

        vivas = []
        for p in self.particulas:
            p.vida -= dt
            if p.vida <= 0:
                continue
            amort = math.exp(-p.friccion * dt)
            p.vx *= amort
            p.vy = p.vy * amort + p.gravedad * dt
            p.x += p.vx * dt
            p.y += p.vy * dt
            vivas.append(p)
        self.particulas = vivas[-700:]

        for t in self.textos:
            t.vida -= dt
            t.x += t.vx * dt
        self.textos = [t for t in self.textos if t.vida > 0]
        for o in self.ondas:
            o.vida -= dt
        self.ondas = [o for o in self.ondas if o.vida > 0]
        for t in self.tajos:
            t.vida -= dt
        self.tajos = [t for t in self.tajos if t.vida > 0]

    def limpiar(self) -> None:
        self.particulas.clear()
        self.textos.clear()
        self.ondas.clear()
        self.tajos.clear()

    # ---------------------------------------------------------------- dibujo
    def resplandor(self, radio: int, color: tuple) -> pygame.Surface:
        """Círculo difuso para mezcla aditiva (cacheado)."""
        clave = (radio, color)
        surf = self._resplandor_cache.get(clave)
        if surf is None:
            surf = pygame.Surface((radio * 2, radio * 2))
            for r in range(radio, 0, -1):
                k = (1 - r / radio) ** 1.8
                pygame.draw.circle(surf, (int(color[0] * k), int(color[1] * k), int(color[2] * k)), (radio, radio), r)
            self._resplandor_cache[clave] = surf
        return surf

    def dibujar_mundo(self, mundo: pygame.Surface) -> None:
        """Partículas, ondas y tajos en el lienzo de baja resolución."""
        for t in self.tajos:
            self._dibujar_tajo(mundo, t)
        for o in self.ondas:
            k = 1 - o.vida / o.vida_max
            r = max(1, int(o.radio_max * ease_out_cubic(k)))
            color = paleta.mezclar(o.color, paleta.FONDO, k)
            pygame.draw.circle(mundo, color, (int(o.x), int(o.y)), r, max(1, int(o.grosor * (1 - k)) + 1))
        for p in self.particulas:
            k = p.vida / p.vida_max
            tam = max(1, int(p.tam * (0.4 + 0.6 * k) + 0.5))
            if p.brillo:
                g = self.resplandor(4, paleta.mezclar(paleta.NEGRO, p.color, k * 0.8))
                mundo.blit(g, (p.x - 4, p.y - 4), special_flags=pygame.BLEND_RGB_ADD)
            pygame.draw.rect(mundo, p.color, (int(p.x - tam / 2), int(p.y - tam / 2), tam, tam))

    def _dibujar_tajo(self, mundo: pygame.Surface, t: Tajo) -> None:
        """Arco de luz que barre el ángulo del ataque y se desvanece."""
        k = 1 - t.vida / t.vida_max
        medio = math.radians(62)
        fin = -medio + 2 * medio * ease_out_cubic(min(1.0, k * 1.8))
        inicio = max(-medio, fin - math.radians(95))
        for capa, (radio, grosor, color) in enumerate((
                (t.alcance + 2, 3, paleta.mezclar(paleta.BLANCO, paleta.CIAN, k)),
                (t.alcance - 3, 2, paleta.mezclar(paleta.CIAN, paleta.CIAN_OSCURO, k)),
                (t.alcance - 7, 1, paleta.CIAN_OSCURO))):
            puntos = []
            for i in range(10):
                a = t.angulo + inicio + (fin - inicio) * i / 9
                puntos.append((t.x + math.cos(a) * radio, t.y + math.sin(a) * radio))
            pygame.draw.lines(mundo, color, False, puntos, max(1, grosor - int(k * 2)))

    def dibujar_textos(self, pantalla: pygame.Surface, ox: float, oy: float) -> None:
        """Números flotantes en alta resolución (coordenadas de mundo -> pantalla)."""
        e = config.ESCALA
        for t in self.textos:
            k = 1 - t.vida / t.vida_max
            escala = 0.6 + 0.6 * ease_out_back(min(1.0, k * 4)) - 0.2 * k
            sube = 18 * ease_out_cubic(k)
            alfa = int(255 * min(1.0, (t.vida / t.vida_max) * 3))
            textos.dibujar(pantalla, t.texto, (t.x + ox) * e, (t.y - sube + oy) * e, t.tam, t.color,
                           negrita=True, ancla="center", contorno=2, alfa=alfa, escala=escala)
