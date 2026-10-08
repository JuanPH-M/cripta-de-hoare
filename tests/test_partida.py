"""Simulación sin ventana: reglas del nivel, combate, consumibles y run completa."""

import math
import unittest

from herramientas.bot import jugar_nivel
from juego.core import config
from juego.datos import tablas
from juego.entidades.objetos import Proyectil
from juego.sistemas.partida import Entrada
from juego.sistemas.run import Run


class TestPartida(unittest.TestCase):
    def test_run_completa_hasta_derrotar_al_jefe(self):
        """Con invencibilidad, el bot recorre los 10 niveles: el flujo completo funciona."""
        run = Run(semilla=1)
        while True:
            resultado = jugar_nivel(run.crear_partida(), 400, invencible=True, dt=1 / 30)
            if resultado != "completado":
                break
            run.completar_nivel()
            run.elegir_mejora(run.opciones_mejora()[0])
            run.avanzar_nivel()
        self.assertEqual(resultado, "victoria")
        self.assertEqual(run.nivel, config.NIVEL_JEFE)
        self.assertGreater(run.puntaje_total(), 0)

    def test_portal_solo_se_abre_sin_enemigos(self):
        run = Run(semilla=2)
        p = run.crear_partida()
        self.assertFalse(p.portal.abierto)
        for e in p.enemigos[:-1]:
            e.vida = 0
        ultimo = p.enemigos[-1]
        p.jugador.ataque = 99
        p._golpear_enemigo(ultimo, 1.0, 0.0)
        self.assertFalse(ultimo.vivo)
        self.assertEqual(p.vivos, 0)
        self.assertTrue(p.portal.abierto)

    def test_el_oro_garantizado_nunca_se_pierde(self):
        run = Run(semilla=3)
        p = run.crear_partida()
        oro_esperado = len(p.monedas) + sum(e.oro for e in p.enemigos)
        self.assertEqual(jugar_nivel(p, 300, invencible=True), "completado")
        self.assertEqual(run.oro, oro_esperado)

    def test_muerte_registra_la_causa(self):
        run = Run(semilla=4)
        p = run.crear_partida()
        j = p.jugador
        j.vida = 1
        j.t_invulnerable = 0
        j.esquiva = 0
        p._herir_jugador(50, "Slime", j.x + 5, j.y)
        self.assertFalse(j.vivo)
        self.assertEqual(run.causa_muerte, "Slime")
        self.assertIn("jugador_muere", [ev.tipo for ev in p.tomar_eventos()])

    def test_pocion_no_se_gasta_con_vida_llena(self):
        run = Run(semilla=5)
        p = run.crear_partida()
        p.actualizar(1 / 60, Entrada(pocion=True))
        self.assertEqual(run.contar(config.POCION), 1)
        p.jugador.vida = 5
        p.actualizar(1 / 60, Entrada(pocion=True))
        self.assertEqual(run.contar(config.POCION), 0)
        self.assertEqual(p.jugador.vida, 5 + math.ceil(p.jugador.vida_max * tablas.CURA_POCION))

    def test_tajo_destruye_proyectiles(self):
        run = Run(semilla=6)
        p = run.crear_partida()
        j = p.jugador
        p.proyectiles.append(Proyectil(j.x + 12, j.y, -50, 0, 3))
        p.actualizar(1 / 60, Entrada(atacar=True, apuntar=(1.0, 0.0)))
        self.assertEqual(p.proyectiles, [])
        self.assertIn("parada", [ev.tipo for ev in p.tomar_eventos()])

    def test_dash_da_invulnerabilidad(self):
        run = Run(semilla=7)
        p = run.crear_partida()
        p.jugador.t_invulnerable = 0
        p.actualizar(1 / 60, Entrada(mover_x=1, dash=True))
        self.assertTrue(p.jugador.en_dash)
        self.assertGreater(p.jugador.t_invulnerable, 0)

    def test_simulacion_larga_sin_errores(self):
        """Muchos frames con entradas variadas en todos los niveles: ninguna excepción ni contrato roto."""
        for nivel in range(1, config.NIVELES_MAX + 1):
            run = Run(semilla=100 + nivel)
            run.nivel = nivel
            p = run.crear_partida()
            for k in range(900):
                a = k * 0.13
                p.actualizar(1 / 60, Entrada(math.cos(a), math.sin(a), k % 9 == 0, None, k % 50 == 0,
                                             k % 300 == 0, k % 400 == 0))
                p.tomar_eventos()
                j = p.jugador
                self.assertTrue(0 <= j.x <= config.ANCHO_MAPA and 0 <= j.y <= config.ALTO_MAPA)
                self.assertTrue(0 <= j.vida <= j.vida_max)
                if not j.vivo:
                    break


if __name__ == "__main__":
    unittest.main()
