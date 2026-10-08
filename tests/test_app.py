"""Prueba de humo de la aplicación pygame sin ventana (driver de video "dummy")."""

import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame  # noqa: E402

from juego.datos import persistencia  # noqa: E402


def tecla(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k, mod=0, unicode="", scancode=0)


class TestApp(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory()
        persistencia.RUTA_RANKING = Path(cls._tmp.name) / "ranking.json"
        from juego.ui.app import App
        cls.app = App()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()
        cls._tmp.cleanup()

    def avanzar(self, frames, eventos=None):
        for i in range(frames):
            self.app.frame(1 / 60, eventos if (eventos and i == 0) else [])

    def test_flujo_completo_de_pantallas(self):
        a = self.app
        a.cambiar_estado("menu")
        self.avanzar(5)
        self.avanzar(1, [tecla(pygame.K_RETURN)])        # Nueva partida
        self.avanzar(60)
        self.assertEqual(a.estado, "juego")
        self.avanzar(120, [tecla(pygame.K_SPACE)])
        self.avanzar(1, [tecla(pygame.K_ESCAPE)])
        self.assertEqual(a.estado, "pausa")
        self.avanzar(1, [tecla(pygame.K_ESCAPE)])
        self.assertEqual(a.estado, "juego")

        a.transicionar(a._nivel_completado)
        self.avanzar(60)
        self.assertEqual(a.estado, "mejora")
        self.avanzar(1, [tecla(pygame.K_1)])
        self.assertEqual(a.estado, "tienda")
        a.run.oro = 100
        self.avanzar(1, [tecla(pygame.K_1)])              # poción
        self.assertLess(a.run.oro, 100)
        self.avanzar(1, [tecla(pygame.K_RETURN)])
        a.seleccion = len(a.oferta)
        self.avanzar(1, [tecla(pygame.K_RETURN)])         # descender
        self.avanzar(60)
        self.assertEqual((a.estado, a.run.nivel), ("juego", 2))

        a._terminar_run(False)
        self.avanzar(90)
        self.assertEqual(a.estado, "derrota")
        self.assertTrue(persistencia.RUTA_RANKING.exists())
        self.avanzar(1, [tecla(pygame.K_r)])
        self.avanzar(60)
        self.assertEqual((a.estado, a.run.nivel), ("juego", 1))

    def test_pantallas_estaticas(self):
        a = self.app
        for estado in ("menu", "ayuda", "ranking"):
            a.cambiar_estado(estado)
            self.avanzar(20)
        a.nueva_run(9)
        a.run.nivel = 10
        a._entrar_nivel()
        a.panel_verificacion = True
        self.avanzar(200)
        a._terminar_run(True)
        self.avanzar(30)
        self.assertEqual(a.estado, "victoria")


if __name__ == "__main__":
    unittest.main()
