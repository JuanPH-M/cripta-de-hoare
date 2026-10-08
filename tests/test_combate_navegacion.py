"""Regresiones de los bugs de rango, ataque a través de paredes y enemigos atascados."""

import math
import unittest

from juego.core import config
from juego.entidades.objetos import Proyectil
from juego.sistemas import ia
from juego.sistemas.colisiones import centro_casilla
from juego.sistemas.mazmorra import Mazmorra
from juego.sistemas.navegacion import VENTANA_ATASCO, separacion, vigilar_atasco
from juego.sistemas.objetivo import elegir_objetivo, en_alcance, rango_ataque
from juego.sistemas.partida import Entrada, Partida
from juego.sistemas.progresion import crear_enemigo
from juego.sistemas.run import Run
from juego.sistemas.vision import camino_libre, linea_de_vision

DT = 1 / 60


def sala_abierta(muros: list[tuple[int, int]] = (), inicio=(5, 9), spawns=()) -> Mazmorra:
    """Una sola sala que ocupa todo el mapa (borde de muros) más los muros indicados."""
    tiles = [[config.MURO] * config.COLUMNAS for _ in range(config.FILAS)]
    for y in range(1, config.FILAS - 1):
        for x in range(1, config.COLUMNAS - 1):
            tiles[y][x] = config.PISO
    for x, y in muros:
        tiles[y][x] = config.MURO
    return Mazmorra(1, tiles, inicio, (config.COLUMNAS - 3, config.FILAS - 3), spawns=list(spawns))


def partida_en(m: Mazmorra) -> Partida:
    p = Partida(Run(semilla=1), m)
    p.enemigos.clear()
    p.monedas.clear()
    return p


def poner_enemigo(p: Partida, tipo: str, x: float, y: float):
    e = crear_enemigo(tipo, 1, x, y, p.rng)
    e.esquiva = 0.0
    e.vida = e.vida_max = 500     # que no muera: medimos si el golpe llega
    p.enemigos.append(e)
    return e


class TestRangoMejorado(unittest.TestCase):
    def test_hoja_amplia_sube_20_por_ciento_y_acumula(self):
        run = Run(semilla=1)
        antes = run.jugador.alcance
        self.assertAlmostEqual(antes, 21.0)
        run.elegir_mejora("amplia")
        self.assertAlmostEqual(run.jugador.alcance, antes * 1.20)        # 25.2
        run.elegir_mejora("amplia")
        self.assertAlmostEqual(run.jugador.alcance, antes * 1.20 ** 2)   # 30.24
        # El valor sobrevive al cambio de nivel y es el que lee el combate.
        p = run.crear_partida()
        self.assertAlmostEqual(rango_ataque(p.jugador), antes * 1.44)

    def test_el_rango_mejorado_se_usa_para_apuntar_y_para_golpear(self):
        p = partida_en(sala_abierta())
        j = p.jugador
        e = poner_enemigo(p, "slime", j.x + 23 + 5, j.y)    # borde a 23 px: fuera de 21, dentro de 25.2
        self.assertFalse(en_alcance(j, e.x, e.y, e.radio))
        self.assertIsNone(elegir_objetivo(p.tiles, j, p.enemigos))
        p._tajo(None)
        self.assertEqual(e.vida, 500, "fuera de alcance: el tajo sale pero no lo toca")

        p.run.elegir_mejora("amplia")
        self.assertIs(elegir_objetivo(p.tiles, j, p.enemigos), e)
        p._tajo(None)
        self.assertLess(e.vida, 500)


class TestAtaqueAutomatico(unittest.TestCase):
    def test_reselecciona_el_siguiente_valido_si_el_mas_cercano_muere(self):
        p = partida_en(sala_abierta())
        j = p.jugador
        cerca = poner_enemigo(p, "slime", j.x + 12, j.y)
        lejos = poner_enemigo(p, "slime", j.x, j.y - 18)
        self.assertIs(elegir_objetivo(p.tiles, j, p.enemigos), cerca)
        cerca.vida = 0
        self.assertIs(elegir_objetivo(p.tiles, j, p.enemigos), lejos)
        p._tajo(None)
        self.assertLess(lejos.vida, 500, "el tajo va al siguiente objetivo y no se desperdicia")

    def test_tajo_con_teclado_sin_objetivo_sale_hacia_donde_mira(self):
        """Antes, sin enemigos al alcance J / Espacio no hacían nada y parecía que el ataque no funcionaba."""
        p = partida_en(sala_abierta())
        j = p.jugador
        j.mira_x, j.mira_y = 0.0, -1.0
        p.actualizar(DT, Entrada(atacar=True))
        tajos = [ev for ev in p.tomar_eventos() if ev.tipo == "tajo"]
        self.assertEqual(len(tajos), 1)
        self.assertAlmostEqual(tajos[0].valor, -90.0)            # hacia arriba, donde mira
        self.assertGreater(j.t_ataque, 0.0)

    def test_agrupados_cada_tajo_automatico_impacta(self):
        p = partida_en(sala_abierta())
        j = p.jugador
        grupo = [poner_enemigo(p, "slime", j.x + 14 + 3 * k, j.y + (-1) ** k * 4 * k) for k in range(5)]
        for _ in range(6):
            j.t_ataque = 0.0
            vidas = [e.vida for e in grupo]
            p._tajo(None)
            self.assertTrue(any(e.vida < v for e, v in zip(grupo, vidas)))


class TestParedes(unittest.TestCase):
    def setUp(self):
        # Jugador en el centro de (5, 9); muro en (6, 9); enemigo en el centro de (7, 9).
        self.p = partida_en(sala_abierta(muros=[(6, 9)]))
        self.j = self.p.jugador
        self.j.alcance = 40.0
        x, y = centro_casilla(7, 9)
        self.e = poner_enemigo(self.p, "slime", x, y)

    def test_ataque_bloqueado_por_pared(self):
        p, j, e = self.p, self.j, self.e
        self.assertTrue(en_alcance(j, e.x, e.y, e.radio))
        self.assertFalse(linea_de_vision(p.tiles, j.x, j.y, e.x, e.y))
        self.assertIsNone(elegir_objetivo(p.tiles, j, p.enemigos))
        p._tajo(None)                                   # automático: no hay objetivo válido
        self.assertEqual(e.vida, 500)
        p._tajo((1.0, 0.0))                             # apuntando a mano directo al muro
        self.assertEqual(e.vida, 500)
        self.assertNotIn("golpe_enemigo", [ev.tipo for ev in p.tomar_eventos()])

    def test_sin_pared_si_golpea(self):
        p, j, e = self.p, self.j, self.e
        p.tiles[9][6] = config.PISO
        p._tajo(None)
        self.assertLess(e.vida, 500)

    def test_bomba_no_atraviesa_paredes(self):
        p = self.p
        p.jugador.inventario[0] = config.BOMBA
        p._lanzar_bomba()
        self.assertEqual(self.e.vida, 500)

    def test_proyectil_se_destruye_en_la_pared(self):
        p, j = self.p, self.j
        x, y = centro_casilla(7, 9)
        p.proyectiles.append(Proyectil(x, y, -300, 0, 3))
        j.t_invulnerable = 0
        vida = j.vida
        for _ in range(10):
            p._actualizar_proyectiles(DT)
        self.assertEqual(p.proyectiles, [])
        self.assertEqual(j.vida, vida)

    def test_proyectil_no_se_cuela_por_una_esquina(self):
        # Muros en (10, 9) y (9, 10): de (9, 9) a (10, 10) solo se pasa por la rendija de la
        # esquina (160, 160). El punto final cae en piso, así que mirar solo la casilla final fallaba.
        p = partida_en(sala_abierta(muros=[(10, 9), (9, 10)]))
        p.proyectiles.append(Proyectil(156, 156, 600, 600, 3))     # en 0,02 s llega a (168, 168)
        p._actualizar_proyectiles(0.02)
        self.assertEqual(p.proyectiles, [])

    def test_tajo_no_para_proyectiles_detras_del_muro(self):
        p, j = self.p, self.j
        x, y = centro_casilla(7, 9)
        p.proyectiles.append(Proyectil(x, y, 0, 0, 3))
        p._tajo((1.0, 0.0))
        self.assertTrue(p.proyectiles[0].activo)


class TestNavegacion(unittest.TestCase):
    # Una "U" abierta hacia la izquierda: el enemigo empieza dentro y el jugador está detrás del fondo.
    MUROS_U = ([(20, y) for y in range(4, 15)] + [(x, 4) for x in range(15, 20)]
               + [(x, 14) for x in range(15, 20)])

    def _llega(self, tipo: str, segundos: float = 25.0) -> tuple[bool, float]:
        m = sala_abierta(muros=self.MUROS_U, inicio=(25, 9))
        p = partida_en(m)
        j = p.jugador
        e = poner_enemigo(p, tipo, *centro_casilla(18, 9))
        e.estado, e.t_estado = "persigue", 0.0
        e.t_disparo = 999.0                               # el bruto no embiste: medimos el caminar
        self.assertFalse(linea_de_vision(p.tiles, e.x, e.y, j.x, j.y))
        t = 0.0
        while t < segundos:
            j.t_invulnerable = 99.0
            ia.actualizar(p, e, DT)
            p.tiempo += DT
            t += DT
            if math.hypot(e.x - j.x, e.y - j.y) < e.radio + j.radio + 6:
                return True, t
        return False, t

    def test_enemigo_rodea_el_obstaculo_sin_atascarse(self):
        for tipo in ("slime", "bruto", "murcielago"):
            with self.subTest(tipo=tipo):
                llego, t = self._llega(tipo)
                self.assertTrue(llego, f"{tipo} no llegó en {t:.1f} s")

    def test_camino_libre_considera_el_radio(self):
        m = sala_abierta(muros=[(10, 9)])
        cx, cy = centro_casilla(10, 9)
        # La línea central pasa a 9 px del muro: un punto la cruza, un bruto de radio 10 no.
        self.assertTrue(camino_libre(m.tiles, cx - 40, cy - 17, cx + 40, cy - 17, 0))
        self.assertFalse(camino_libre(m.tiles, cx - 40, cy - 17, cx + 40, cy - 17, 10))

    def test_detector_de_atasco(self):
        p = partida_en(sala_abierta())
        e = poner_enemigo(p, "slime", 100, 100)
        detectado = False
        t = 0.0
        while t < VENTANA_ATASCO * 2 + 0.1:              # quiere moverse pero no avanza
            detectado |= vigilar_atasco(e, DT, True)
            t += DT
        self.assertTrue(detectado)
        self.assertGreater(e.t_desvio, 0)

    def test_separacion_entre_enemigos(self):
        p = partida_en(sala_abierta(inicio=(30, 9)))
        x, y = centro_casilla(10, 9)
        grupo = [poner_enemigo(p, "slime", x + 0.1 * k, y) for k in range(6)]
        self.assertNotEqual(separacion(grupo[0], grupo), (0.0, 0.0))
        for e in grupo:
            e.estado, e.t_estado = "persigue", 0.0
        for _ in range(120):
            p.jugador.t_invulnerable = 99.0
            p.actualizar(DT, Entrada())
        minimo = min(math.hypot(a.x - b.x, a.y - b.y)
                     for i, a in enumerate(grupo) for b in grupo[i + 1:])
        self.assertGreater(minimo, 2 * grupo[0].radio - 1.0, "no deben quedar apilados en el mismo punto")


if __name__ == "__main__":
    unittest.main()
