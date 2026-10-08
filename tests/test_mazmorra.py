"""Generación procedural: conectividad, bordes, determinismo y arena del jefe."""

import unittest

from juego.core import config
from juego.sistemas.mazmorra import distancias_bfs, es_conexa, generar_mazmorra


class TestMazmorra(unittest.TestCase):
    def test_todas_las_mazmorras_son_validas(self):
        for nivel in range(1, config.NIVELES_MAX + 1):
            for semilla in range(150):
                m = generar_mazmorra(semilla, nivel)
                with self.subTest(nivel=nivel, semilla=semilla):
                    self.assertTrue(es_conexa(m))
                    for x in range(config.COLUMNAS):
                        self.assertEqual(m.tiles[0][x], config.MURO)
                        self.assertEqual(m.tiles[config.FILAS - 1][x], config.MURO)
                    for y in range(config.FILAS):
                        self.assertEqual(m.tiles[y][0], config.MURO)
                        self.assertEqual(m.tiles[y][config.COLUMNAS - 1], config.MURO)
                    alcanzables = distancias_bfs(m.tiles, m.inicio)
                    self.assertIn(m.salida, alcanzables)
                    for _, x, y in m.spawns:
                        self.assertIn((x, y), alcanzables)
                    for p in m.monedas:
                        self.assertIn(p, alcanzables)

    def test_determinismo(self):
        a = generar_mazmorra(1234, 4)
        b = generar_mazmorra(1234, 4)
        self.assertEqual(a.tiles, b.tiles)
        self.assertEqual(a.spawns, b.spawns)
        self.assertNotEqual(a.tiles, generar_mazmorra(1235, 4).tiles)

    def test_jefe_solo_en_el_nivel_10(self):
        for nivel in range(1, config.NIVELES_MAX + 1):
            tipos = [t for t, _, _ in generar_mazmorra(7, nivel).spawns]
            self.assertEqual("jefe" in tipos, nivel == config.NIVEL_JEFE)

    def test_dificultad_creciente(self):
        cantidades = [len(generar_mazmorra(3, n).spawns) for n in range(1, config.NIVELES_MAX)]
        self.assertEqual(cantidades, sorted(cantidades))

    def test_nivel_invalido(self):
        with self.assertRaises(AssertionError):
            generar_mazmorra(1, 0)


if __name__ == "__main__":
    unittest.main()
