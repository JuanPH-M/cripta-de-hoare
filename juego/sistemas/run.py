"""
Una "run" del roguelike: 10 niveles con un mismo personaje.
Guarda lo que persiste entre niveles: estadísticas, oro, inventario y puntaje.
"""

import math
import random

from juego.core import config
from juego.datos import tablas
from juego.entidades.enemigo import Enemigo
from juego.entidades.jugador import Jugador
from juego.sistemas import economia, progresion
from juego.sistemas.mazmorra import generar_mazmorra
from juego.sistemas.partida import Partida
from juego.verificacion.funciones import buscar_lineal, comprar, puede_comprar, sumar_puntajes


class Run:
    def __init__(self, semilla: int | None = None):
        self.semilla = semilla if semilla is not None else random.randrange(1, 10**9)
        self.nivel = 1
        self.jugador = Jugador()
        self.oro = 0
        self.oro_total = 0
        self.oro_gastado = 0
        self.compras = 0
        self.puntajes: list[int] = []        # cada evento que da puntos
        self.enemigos_derrotados = 0
        self.tiempo = 0.0
        self.causa_muerte = ""
        self.victoria = False
        self.mejoras_elegidas: list[str] = []
        self._puntaje_cache = (0, 0)         # (cantidad de eventos, total)

    # ------------------------------------------------------------ niveles
    def crear_partida(self) -> Partida:
        return Partida(self, generar_mazmorra(self.semilla, self.nivel))

    def completar_nivel(self) -> int:
        """Bono de nivel y pequeña curación. Devuelve la vida recuperada."""
        self.registrar_puntos(tablas.PUNTOS_POR_NIVEL * self.nivel)
        j = self.jugador
        antes = j.vida
        j.vida = min(j.vida_max, j.vida + math.ceil(j.vida_max * tablas.CURA_ENTRE_NIVELES))
        return j.vida - antes

    def avanzar_nivel(self) -> None:
        self.nivel = min(config.NIVELES_MAX, self.nivel + 1)

    def ganar(self) -> None:
        self.victoria = True
        self.registrar_puntos(tablas.PUNTOS_VICTORIA)

    # ------------------------------------------------------------ puntaje
    def registrar_puntos(self, puntos: int) -> None:
        self.puntajes.append(puntos)

    def puntaje_total(self) -> int:
        n = len(self.puntajes)
        if self._puntaje_cache[0] != n:
            self._puntaje_cache = (n, sumar_puntajes(self.puntajes, n))
        return self._puntaje_cache[1]

    def registrar_derrota(self, e: Enemigo) -> None:
        if e.puntos > 0:
            self.enemigos_derrotados += 1
            self.registrar_puntos(e.puntos)

    def ganar_oro(self, valor: int) -> None:
        self.oro += valor
        self.oro_total += valor
        self.registrar_puntos(valor * tablas.PUNTOS_POR_ORO)

    # ------------------------------------------------------------ inventario
    def contar(self, objeto: int) -> int:
        return self.jugador.inventario.count(objeto)

    def hay_espacio(self) -> bool:
        return buscar_lineal(self.jugador.inventario, config.TAM_INVENTARIO, config.VACIO) != -1

    def usar_pocion(self) -> int | None:
        """None si no hay pociones; 0 si la vida está llena; si no, la vida curada."""
        j = self.jugador
        i = buscar_lineal(j.inventario, config.TAM_INVENTARIO, config.POCION)
        if i == -1:
            return None
        if j.vida >= j.vida_max:
            return 0
        j.inventario[i] = config.VACIO
        antes = j.vida
        j.vida = min(j.vida_max, j.vida + math.ceil(j.vida_max * tablas.CURA_POCION))
        return j.vida - antes

    def usar_bomba(self) -> bool:
        j = self.jugador
        i = buscar_lineal(j.inventario, config.TAM_INVENTARIO, config.BOMBA)
        if i == -1:
            return False
        j.inventario[i] = config.VACIO
        return True

    # ------------------------------------------------------------ tienda
    def motivo_no_compra(self, objeto: str, precio: int) -> str:
        """Cadena vacía si se puede comprar; si no, el motivo para mostrarlo en la tienda."""
        if tablas.OBJETOS_TIENDA[objeto]["consumible"] and not self.hay_espacio():
            return "Inventario lleno"
        if not puede_comprar(self.oro, precio):
            return "Oro insuficiente"
        return ""

    def comprar_objeto(self, objeto: str, nivel_tienda: int) -> str:
        """Intenta comprar; devuelve "" si tuvo éxito o el motivo del rechazo."""
        precio = economia.precio(objeto, nivel_tienda)
        motivo = self.motivo_no_compra(objeto, precio)
        if motivo:
            return motivo
        self.oro, self.oro_gastado, self.compras = comprar(self.oro, precio, self.oro_gastado, self.compras)
        if tablas.OBJETOS_TIENDA[objeto]["consumible"]:
            libre = buscar_lineal(self.jugador.inventario, config.TAM_INVENTARIO, config.VACIO)
            self.jugador.inventario[libre] = tablas.CONSUMIBLE_A_ID[objeto]
        else:
            progresion.aplicar_objeto_permanente(self.jugador, objeto)
        return ""

    def opciones_mejora(self) -> list[str]:
        return progresion.opciones_mejora(random.Random(self.semilla * 17 + self.nivel))

    def elegir_mejora(self, mejora: str) -> None:
        progresion.aplicar_mejora(self.jugador, mejora)
        self.mejoras_elegidas.append(mejora)
