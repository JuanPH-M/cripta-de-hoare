"""
Simulación de un nivel en tiempo real, sin pygame.

La interfaz entrega una `Entrada` por frame y recibe `Evento`s que usa para
sonidos, partículas, sacudidas de cámara, etc. Así toda la lógica del juego se
puede probar sin ventana (ver tests/test_partida.py).
"""

import math
import random
from dataclasses import dataclass
from typing import TYPE_CHECKING

from juego.core import config
from juego.datos import tablas
from juego.entidades.enemigo import Enemigo
from juego.entidades.objetos import Moneda, Portal, Proyectil
from juego.sistemas import ia
from juego.sistemas.colisiones import (
    centro_casilla, circulos_se_tocan, mover_con_colisiones, normalizar,
)
from juego.sistemas.combate import recibir_dano, resolver_golpe
from juego.sistemas.mazmorra import Mazmorra
from juego.sistemas.navegacion import Navegador, resolver_solapes
from juego.sistemas.objetivo import elegir_objetivo, en_alcance
from juego.sistemas.progresion import crear_enemigo
from juego.sistemas.vision import linea_de_vision
from juego.verificacion.funciones import (
    DT_MAXIMO, ESQUIVA, aplicar_dano, contar_vivos, mover_jugador,
)

if TYPE_CHECKING:
    from juego.sistemas.run import Run


class _VidasDe:
    """Vista de solo lectura: vidas[k] = enemigos[k].vida (mismo índice, sin copiar el arreglo)."""

    __slots__ = ("_enemigos",)

    def __init__(self, enemigos: list[Enemigo]):
        self._enemigos = enemigos

    def __len__(self) -> int:
        return len(self._enemigos)

    def __getitem__(self, k: int) -> int:
        return self._enemigos[k].vida


@dataclass
class Entrada:
    mover_x: float = 0.0
    mover_y: float = 0.0
    atacar: bool = False
    apuntar: tuple[float, float] | None = None   # dirección explícita (ratón)
    dash: bool = False
    pocion: bool = False
    bomba: bool = False


@dataclass
class Evento:
    tipo: str
    x: float = 0.0
    y: float = 0.0
    valor: float = 0
    critico: bool = False
    texto: str = ""


class Partida:
    """Estado y reglas de un nivel."""

    def __init__(self, run: "Run", mazmorra: Mazmorra):
        self.run = run
        self.jugador = run.jugador
        self.mazmorra = mazmorra
        self.nivel = mazmorra.nivel
        self.tiles = mazmorra.tiles
        self.navegador = Navegador(self.tiles)
        self.rng = random.Random(run.semilla * 131 + mazmorra.nivel)
        self.tiempo = 0.0
        self.eventos: list[Evento] = []
        self.completada = False
        self.victoria = False

        j = self.jugador
        j.x, j.y = centro_casilla(*mazmorra.inicio)
        j.t_ataque = j.t_dash = j.t_en_dash = 0.0
        j.t_invulnerable = 1.0          # gracia al entrar al nivel
        j.empuje_x = j.empuje_y = 0.0

        self.enemigos: list[Enemigo] = []
        for tipo, tx, ty in mazmorra.spawns:
            x, y = centro_casilla(tx, ty)
            self.enemigos.append(crear_enemigo(tipo, self.nivel, x, y, self.rng))
        self.jefe = next((e for e in self.enemigos if e.tipo == "jefe"), None)
        if self.jefe:
            self.jefe.estado = "alerta"
            self.jefe.t_estado = 2.0    # presentación del jefe

        self.monedas = [Moneda(*centro_casilla(tx, ty), valor=tablas.VALOR_MONEDA, t=1.0)
                        for tx, ty in mazmorra.monedas]
        self.proyectiles: list[Proyectil] = []
        self.portal = Portal(*centro_casilla(*mazmorra.salida))
        self.vivos = self._contar_vivos()

    # ------------------------------------------------------------------ util
    def emitir(self, tipo: str, x: float = 0.0, y: float = 0.0, valor: float = 0,
               critico: bool = False, texto: str = "") -> None:
        self.eventos.append(Evento(tipo, x, y, valor, critico, texto))

    def tomar_eventos(self) -> list[Evento]:
        eventos, self.eventos = self.eventos, []
        return eventos

    def disparar(self, x: float, y: float, vx: float, vy: float, dano: int, tipo: str) -> None:
        radio = 3.0 if tipo == "orbe" else 2.5
        self.proyectiles.append(Proyectil(x, y, vx, vy, dano, radio, 4.0, tipo))
        if tipo == "flecha":
            self.emitir("flecha", x, y)

    def invocar_esbirros(self, jefe: Enemigo, cantidad: int) -> None:
        vivos_no_jefe = sum(1 for e in self.enemigos if e.vivo and e is not jefe)
        for _ in range(min(cantidad, 4 - vivos_no_jefe)):
            a = self.rng.random() * math.tau
            x = jefe.x + math.cos(a) * 26
            y = jefe.y + math.sin(a) * 26
            e = crear_enemigo("slime", 6, jefe.x, jefe.y, self.rng)
            e.oro = 0
            e.puntos = 0
            e.x, e.y, _ = mover_con_colisiones(self.tiles, jefe.x, jefe.y, x - jefe.x, y - jefe.y, e.radio)
            e.estado = "alerta"
            e.t_estado = 0.5
            self.enemigos.append(e)
            self.emitir("invocar", e.x, e.y)
        self.vivos = self._contar_vivos()

    def _contar_vivos(self) -> int:
        # Una sola pasada sobre el arreglo de enemigos: la vista lee e.vida al vuelo, sin lista intermedia.
        return contar_vivos(_VidasDe(self.enemigos), len(self.enemigos))

    # ------------------------------------------------------------- bucle
    def actualizar(self, dt: float, entrada: Entrada) -> None:
        dt = min(max(dt, 0.0), DT_MAXIMO)
        self.tiempo += dt
        j = self.jugador
        if self.portal.abierto:
            self.portal.t_abierto += dt
        if not j.vivo or self.completada:
            self._actualizar_monedas(dt)
            return

        self._actualizar_jugador(dt, entrada)
        for e in self.enemigos:
            if e.vivo:
                ia.actualizar(self, e, dt)
        resolver_solapes(self.tiles, self.enemigos)
        self._contacto_enemigos()
        self._actualizar_proyectiles(dt)
        self._actualizar_monedas(dt)
        self._revisar_portal()

    # ----------------------------------------------------------- jugador
    def _actualizar_jugador(self, dt: float, entrada: Entrada) -> None:
        j = self.jugador
        j.t_ataque = max(0.0, j.t_ataque - dt)
        j.t_dash = max(0.0, j.t_dash - dt)
        j.t_en_dash = max(0.0, j.t_en_dash - dt)
        j.t_invulnerable = max(0.0, j.t_invulnerable - dt)

        dx, dy = normalizar(entrada.mover_x, entrada.mover_y)

        if entrada.dash and j.t_dash <= 0 and not j.en_dash:
            ddx, ddy = (dx, dy) if (dx or dy) else (j.mira_x, j.mira_y)
            j.dash_dx, j.dash_dy = ddx, ddy
            j.t_en_dash = tablas.DURACION_DASH
            j.t_dash = j.enfriamiento_dash
            j.t_invulnerable = max(j.t_invulnerable, tablas.DURACION_DASH + 0.06)
            self.emitir("dash", j.x, j.y)

        if j.en_dash:
            dx, dy, rapidez = j.dash_dx, j.dash_dy, tablas.RAPIDEZ_DASH
        else:
            rapidez = j.rapidez
        j.moviendose = bool(dx or dy)
        if j.moviendose and not j.en_dash:
            j.mira_x, j.mira_y = dx, dy

        # Movimiento verificado (mantiene al jugador dentro del mapa) + muros.
        nx, ny = mover_jugador(j.x, j.y, dx, dy, rapidez, dt, config.ANCHO_MAPA, config.ALTO_MAPA)
        amort = math.exp(-12.0 * dt)
        j.empuje_x *= amort
        j.empuje_y *= amort
        mx = nx - j.x + j.empuje_x * dt
        my = ny - j.y + j.empuje_y * dt
        j.x, j.y, _ = mover_con_colisiones(self.tiles, j.x, j.y, mx, my, j.radio)

        if entrada.atacar and j.t_ataque <= 0 and not j.en_dash:
            self._tajo(entrada.apuntar)
        if entrada.pocion:
            self._beber_pocion()
        if entrada.bomba:
            self._lanzar_bomba()

    def _auto_apuntar(self) -> tuple[float, float] | None:
        """
        Apuntado automático (teclado): hacia el enemigo válido más cercano (vivo, al
        alcance y sin pared de por medio; ver sistemas/objetivo.py). Si no hay
        ninguno, hacia el proyectil alcanzable más cercano (para pararlo). Si
        tampoco, None: el tajo sale hacia donde mira el jugador.
        """
        j = self.jugador
        e = elegir_objetivo(self.tiles, j, self.enemigos)
        if e is not None:
            return normalizar(e.x - j.x, e.y - j.y)
        mejor, mejor_d = None, math.inf
        for pr in self.proyectiles:
            d = math.hypot(pr.x - j.x, pr.y - j.y)
            if (pr.activo and d < mejor_d and en_alcance(j, pr.x, pr.y, pr.radio)
                    and linea_de_vision(self.tiles, j.x, j.y, pr.x, pr.y)):
                mejor, mejor_d = pr, d
        if mejor is not None:
            return normalizar(mejor.x - j.x, mejor.y - j.y)
        return None

    def _tajo(self, apuntar: tuple[float, float] | None) -> None:
        j = self.jugador
        if apuntar is not None and (apuntar[0] or apuntar[1]):
            ax, ay = normalizar(*apuntar)
        else:
            # Teclado: al objetivo válido más cercano; si no hay ninguno, hacia donde mira el jugador
            # (antes no salía nada y parecía que J / Espacio no funcionaban).
            auto = self._auto_apuntar()
            ax, ay = auto if auto is not None else (j.mira_x, j.mira_y)
        j.mira_x, j.mira_y = ax, ay
        j.t_ataque = j.enfriamiento_ataque
        self.emitir("tajo", j.x, j.y, valor=math.degrees(math.atan2(ay, ax)))

        medio_arco = math.radians(tablas.ARCO_TAJO_GRADOS / 2)
        for e in self.enemigos:
            if e.vivo and self._en_arco(e.x, e.y, e.radio, ax, ay, medio_arco):
                self._golpear_enemigo(e, ax, ay)
        for pr in self.proyectiles:
            if pr.activo and self._en_arco(pr.x, pr.y, pr.radio, ax, ay, medio_arco):
                pr.activo = False
                self.emitir("parada", pr.x, pr.y)

    def _en_arco(self, x: float, y: float, r: float, ax: float, ay: float, medio_arco: float) -> bool:
        """Al alcance (el mismo que usa el apuntado), dentro del arco y sin pared de por medio."""
        j = self.jugador
        if not en_alcance(j, x, y, r) or not linea_de_vision(self.tiles, j.x, j.y, x, y):
            return False
        vx, vy = x - j.x, y - j.y
        d = math.hypot(vx, vy)
        if d < r + j.radio + 2:     # pegado al jugador: siempre cuenta
            return True
        coseno = (vx * ax + vy * ay) / d
        return coseno >= math.cos(medio_arco)

    def _golpear_enemigo(self, e: Enemigo, ax: float, ay: float) -> None:
        j = self.jugador
        g = resolver_golpe(self.rng, j.ataque, e.defensa, e.esquiva, j.critico)
        if g.resultado == ESQUIVA:
            self.emitir("esquiva_enemigo", e.x, e.y - e.radio)
            return
        if g.dano == 0:
            self.emitir("bloqueo", e.x, e.y - e.radio)
            return
        e.vida = recibir_dano(e.vida, g)
        e.t_flash = 0.12
        empuje = {"jefe": 25.0, "bruto": 70.0}.get(e.tipo, 170.0)
        if e.estado == "carga":
            empuje *= 0.3
        e.empuje_x += ax * empuje
        e.empuje_y += ay * empuje
        self.emitir("golpe_enemigo", e.x, e.y - e.radio, g.dano, g.critico)
        if not e.vivo:
            self._matar(e)

    def _matar(self, e: Enemigo) -> None:
        j = self.jugador
        self.emitir("muerte_enemigo", e.x, e.y, texto=e.tipo)
        self.run.registrar_derrota(e)
        if j.robo_vida and j.vivo:
            j.vida = min(j.vida_max, j.vida + j.robo_vida)
        for _ in range(e.oro):
            a = self.rng.random() * math.tau
            v = self.rng.uniform(35, 75)
            self.monedas.append(Moneda(e.x, e.y, tablas.VALOR_MONEDA, math.cos(a) * v, math.sin(a) * v))

        if e is self.jefe:
            for otro in self.enemigos:
                if otro.vivo and otro is not e:
                    otro.vida = 0
                    self.emitir("muerte_enemigo", otro.x, otro.y, texto=otro.tipo)
            self.proyectiles.clear()
            self.victoria = True
            self.emitir("jefe_derrotado", e.x, e.y)

        self.vivos = self._contar_vivos()
        if self.vivos == 0 and not self.portal.abierto and self.jefe is None:
            self.portal.abierto = True
            self.emitir("portal_abierto", self.portal.x, self.portal.y)
            for m in self.monedas:
                m.atraida = True

    def _herir_jugador(self, ataque: int, fuente: str, ox: float, oy: float) -> None:
        j = self.jugador
        g = resolver_golpe(self.rng, ataque, j.defensa, j.esquiva)
        if g.resultado == ESQUIVA:
            j.t_invulnerable = 0.35
            self.emitir("jugador_esquiva", j.x, j.y - 8)
            return
        if g.dano == 0:
            j.t_invulnerable = 0.45
            self.emitir("jugador_bloquea", j.x, j.y - 8)
            return
        j.vida = recibir_dano(j.vida, g)
        j.t_invulnerable = tablas.INVULNERABLE_TRAS_GOLPE
        kx, ky = normalizar(j.x - ox, j.y - oy)
        j.empuje_x += kx * 190
        j.empuje_y += ky * 190
        self.emitir("jugador_herido", j.x, j.y - 8, g.dano)
        if not j.vivo:
            self.run.causa_muerte = fuente
            self.emitir("jugador_muere", j.x, j.y)

    def _beber_pocion(self) -> None:
        j = self.jugador
        curado = self.run.usar_pocion()
        if curado is None:
            self.emitir("sin_consumible", j.x, j.y - 10, texto="Sin pociones")
        elif curado == 0:
            self.emitir("sin_consumible", j.x, j.y - 10, texto="Vida llena")
        else:
            self.emitir("pocion", j.x, j.y - 10, curado)

    def _lanzar_bomba(self) -> None:
        j = self.jugador
        if not self.run.usar_bomba():
            self.emitir("sin_consumible", j.x, j.y - 10, texto="Sin bombas")
            return
        self.emitir("bomba", j.x, j.y)
        dano = tablas.DANO_BOMBA + j.ataque // 2
        for e in self.enemigos:
            if (e.vivo and math.hypot(e.x - j.x, e.y - j.y) < tablas.RADIO_BOMBA + e.radio
                    and linea_de_vision(self.tiles, j.x, j.y, e.x, e.y)):
                e.vida = aplicar_dano(e.vida, dano)
                e.t_flash = 0.15
                kx, ky = normalizar(e.x - j.x, e.y - j.y)
                e.empuje_x += kx * 160
                e.empuje_y += ky * 160
                self.emitir("golpe_enemigo", e.x, e.y - e.radio, dano, True)
                if not e.vivo:
                    self._matar(e)
        for pr in self.proyectiles:
            if (math.hypot(pr.x - j.x, pr.y - j.y) < tablas.RADIO_BOMBA
                    and linea_de_vision(self.tiles, j.x, j.y, pr.x, pr.y)):
                pr.activo = False

    # ----------------------------------------------------------- mundo
    def _contacto_enemigos(self) -> None:
        j = self.jugador
        for e in self.enemigos:
            if not e.vivo or e.estado in ("idle", "alerta"):
                continue
            if circulos_se_tocan(j.x, j.y, j.radio, e.x, e.y, e.radio) and e.t_contacto <= 0:
                e.t_contacto = 0.5
                if e.tipo == "murcielago":
                    e.estado = "retirada"
                    e.t_estado = 0.7
                if j.t_invulnerable <= 0:
                    extra = 2 if e.estado in ("carga", "atacando") else 0
                    self._herir_jugador(e.ataque + extra, e.nombre, e.x, e.y)
                    if not j.vivo:
                        return

    def _actualizar_proyectiles(self, dt: float) -> None:
        j = self.jugador
        for pr in self.proyectiles:
            if not pr.activo:
                continue
            pr.vida -= dt
            x0, y0 = pr.x, pr.y
            pr.x += pr.vx * dt
            pr.y += pr.vy * dt
            # Segmento recorrido en este frame contra los muros (no atraviesa esquinas).
            if pr.vida <= 0 or not linea_de_vision(self.tiles, x0, y0, pr.x, pr.y):
                pr.activo = False
                self.emitir("proyectil_muro", pr.x, pr.y)
                continue
            if j.vivo and circulos_se_tocan(pr.x, pr.y, pr.radio, j.x, j.y, j.radio) and j.t_invulnerable <= 0:
                pr.activo = False
                fuente = "una flecha" if pr.tipo == "flecha" else "el Guardián del Abismo"
                self._herir_jugador(pr.dano, fuente, pr.x - pr.vx, pr.y - pr.vy)
        self.proyectiles = [pr for pr in self.proyectiles if pr.activo]

    def _actualizar_monedas(self, dt: float) -> None:
        j = self.jugador
        restantes = []
        for m in self.monedas:
            m.t += dt
            dx, dy = j.x - m.x, j.y - m.y
            d = math.hypot(dx, dy)
            if m.t > 0.3 and d < 30:
                m.atraida = True
            if m.atraida and m.t > 0.25:
                nx, ny = normalizar(dx, dy)
                fuerza = 520 if self.portal.abierto else 380
                m.vx += nx * fuerza * dt
                m.vy += ny * fuerza * dt
                m.vx *= math.exp(-3.0 * dt)
                m.vy *= math.exp(-3.0 * dt)
                m.x += m.vx * dt
                m.y += m.vy * dt
            else:
                m.vx *= math.exp(-5.0 * dt)
                m.vy *= math.exp(-5.0 * dt)
                m.x, m.y, _ = mover_con_colisiones(self.tiles, m.x, m.y, m.vx * dt, m.vy * dt, 2.0)
            if m.t > 0.25 and d < j.radio + 5 and j.vivo:
                self.run.ganar_oro(m.valor)
                self.emitir("moneda", m.x, m.y, m.valor)
            else:
                restantes.append(m)
        self.monedas = restantes

    def _revisar_portal(self) -> None:
        j = self.jugador
        if not self.portal.abierto or self.portal.t_abierto < 0.6:
            return
        if math.hypot(j.x - self.portal.x, j.y - self.portal.y) < 10:
            for m in self.monedas:          # el oro garantizado nunca se pierde
                self.run.ganar_oro(m.valor)
            self.monedas.clear()
            self.completada = True
            self.emitir("nivel_completado", j.x, j.y)
