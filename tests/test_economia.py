"""
Simulación de la tienda: con el oro que da UN solo nivel siempre se puede
comprar al menos un objeto útil, y nunca más de dos (obliga a elegir).
"""

import unittest

from juego.core import config
from juego.datos import tablas
from juego.sistemas import economia
from juego.sistemas.mazmorra import generar_mazmorra
from juego.sistemas.run import Run

SEMILLAS = 400


class TestEconomia(unittest.TestCase):
    def test_oro_de_un_nivel_alcanza_para_1_o_2_objetos(self):
        for nivel in range(1, config.NIVELES_MAX):          # hay tienda tras los niveles 1..9
            for semilla in range(SEMILLAS):
                oro = economia.oro_garantizado(generar_mazmorra(semilla, nivel))
                oferta = economia.generar_oferta(semilla, nivel)
                precios = sorted(economia.precios_oferta(oferta, nivel))
                with self.subTest(nivel=nivel, semilla=semilla):
                    self.assertLessEqual(precios[0], oro, "no alcanza para nada")
                    self.assertLess(oro, sum(precios[:3]), "alcanza para 3 o más objetos")

    def test_siempre_hay_una_mejora_permanente_al_alcance(self):
        for nivel in range(1, config.NIVELES_MAX):
            for semilla in range(SEMILLAS):
                oro = economia.oro_garantizado(generar_mazmorra(semilla, nivel))
                oferta = economia.generar_oferta(semilla, nivel)
                permanentes = [economia.precio(o, nivel) for o in oferta if o in tablas.PERMANENTES]
                with self.subTest(nivel=nivel, semilla=semilla):
                    self.assertLessEqual(min(permanentes), oro)

    def test_compra_real_desde_una_run(self):
        """Partiendo con 0 de oro y recibiendo el oro garantizado, la compra se concreta."""
        for nivel in range(1, config.NIVELES_MAX):
            run = Run(semilla=nivel)
            run.nivel = nivel
            run.oro = economia.oro_garantizado(generar_mazmorra(run.semilla, nivel))
            oferta = economia.generar_oferta(run.semilla, nivel)
            mas_barato = min(oferta, key=lambda o: economia.precio(o, nivel))
            antes = run.oro
            self.assertEqual(run.comprar_objeto(mas_barato, nivel), "")
            self.assertEqual(run.oro, antes - economia.precio(mas_barato, nivel))
            self.assertEqual(run.oro + run.oro_gastado, antes)

    def test_rechazos(self):
        run = Run(semilla=1)
        self.assertEqual(run.comprar_objeto("espada", 1), "Oro insuficiente")
        run.oro = 500
        run.jugador.inventario = [config.POCION] * config.TAM_INVENTARIO
        self.assertEqual(run.comprar_objeto("bomba", 1), "Inventario lleno")
        self.assertEqual(run.comprar_objeto("espada", 1), "")     # los permanentes no ocupan casilla


if __name__ == "__main__":
    unittest.main()
