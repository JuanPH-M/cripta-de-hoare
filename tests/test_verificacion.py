"""Pruebas de las funciones verificadas: casos normales, bordes y violaciones de {P}."""

import math
import random
import time
import unittest

from juego.verificacion import contratos
from juego.verificacion.contratos import ContratoError, invariante, requiere
from juego.verificacion.funciones import (
    EMPATE, ESQUIVA, GANA, PIERDE, aplicar_dano, buscar_lineal, clasificar_combate, comprar,
    contar_vivos, mover_jugador, ordenar_desc, puede_comprar, sumar_puntajes,
)


class TestSinCiclos(unittest.TestCase):
    def test_aplicar_dano_ramas(self):
        self.assertEqual(aplicar_dano(10, 3), 7)      # rama else
        self.assertEqual(aplicar_dano(3, 10), 0)      # rama then (dano >= vida)
        self.assertEqual(aplicar_dano(5, 5), 0)       # frontera dano == vida
        self.assertEqual(aplicar_dano(0, 0), 0)

    def test_aplicar_dano_viola_precondicion(self):
        with self.assertRaises(ContratoError):
            aplicar_dano(10, -4)                      # "daño negativo" curaría
        with self.assertRaises(ContratoError):
            aplicar_dano(-1, 2)

    def test_puede_comprar(self):
        self.assertTrue(puede_comprar(10, 10))
        self.assertFalse(puede_comprar(9, 10))
        with self.assertRaises(ContratoError):
            puede_comprar(10, 0)

    def test_comprar_conserva_el_oro(self):
        oro, gastado, compras = comprar(25, 8, 4, 1)
        self.assertEqual((oro, gastado, compras), (17, 12, 2))
        self.assertEqual(oro + gastado, 25 + 4)
        with self.assertRaises(ContratoError):
            comprar(7, 8, 0, 0)                       # oro < precio

    def test_mover_jugador_limita_al_mapa(self):
        self.assertEqual(mover_jugador(5.0, 5.0, 1.0, 0.0, 100.0, 0.05, 640, 320), (10.0, 5.0))
        self.assertEqual(mover_jugador(1.0, 5.0, -1.0, 0.0, 100.0, 0.05, 640, 320), (0.0, 5.0))
        x, y = mover_jugador(639.0, 319.0, 0.7071, 0.7071, 300.0, 0.1, 640, 320)
        self.assertEqual((x, y), (640, 320))
        with self.assertRaises(ContratoError):
            mover_jugador(5.0, 5.0, 1.0, 1.0, 100.0, 0.05, 640, 320)   # dirección sin normalizar
        with self.assertRaises(ContratoError):
            mover_jugador(5.0, 5.0, 1.0, 0.0, 100.0, 0.5, 640, 320)    # dt mayor que DT_MAXIMO

    def test_clasificar_combate_cuatro_ramas(self):
        self.assertEqual(clasificar_combate(5, 2, True), ESQUIVA)
        self.assertEqual(clasificar_combate(5, 2, False), GANA)
        self.assertEqual(clasificar_combate(3, 3, False), EMPATE)
        self.assertEqual(clasificar_combate(1, 3, False), PIERDE)
        with self.assertRaises(ContratoError):
            clasificar_combate(-1, 0, False)


class TestCiclosYArreglos(unittest.TestCase):
    def test_sumar_puntajes(self):
        self.assertEqual(sumar_puntajes([10, 20, 30, 40], 4), 100)
        self.assertEqual(sumar_puntajes([10, 20, 30, 40], 2), 30)
        self.assertEqual(sumar_puntajes([], 0), 0)
        with self.assertRaises(ContratoError):
            sumar_puntajes([1, 2], 3)

    def test_contar_vivos(self):
        self.assertEqual(contar_vivos([0, 5, 0, 3], 4), 2)
        self.assertEqual(contar_vivos([0, 0], 2), 0)
        self.assertEqual(contar_vivos([9, 9, 9], 2), 2)
        with self.assertRaises(ContratoError):
            contar_vivos([1], -1)

    def test_buscar_lineal(self):
        inv = [1, 0, 2, 1]
        self.assertEqual(buscar_lineal(inv, 4, 1), 0)    # primera aparición
        self.assertEqual(buscar_lineal(inv, 4, 2), 2)
        self.assertEqual(buscar_lineal(inv, 4, 7), -1)   # ausente: recorre todo sin salirse
        self.assertEqual(buscar_lineal(inv, 2, 2), -1)   # solo mira a[0..n)
        self.assertEqual(buscar_lineal([], 0, 1), -1)

    def test_ordenar_desc(self):
        a = [5, 90, 12, 90, 0, 33]
        ordenar_desc(a, len(a))
        self.assertEqual(a, [90, 90, 33, 12, 5, 0])
        b = [3, 1, 2, 99]
        ordenar_desc(b, 3)                               # a[n..] no se toca
        self.assertEqual(b, [3, 2, 1, 99])
        with self.assertRaises(ContratoError):
            ordenar_desc(b, 5)

    def test_ordenar_desc_bordes_y_aleatorios(self):
        for a in ([], [7], [1, 2], [2, 1], [3, 3, 3], [1, 2, 3, 4, 5]):
            b = list(a)
            ordenar_desc(b, len(b))
            self.assertEqual(b, sorted(a, reverse=True))
        rng = random.Random(3)
        for _ in range(300):
            a = [rng.randint(0, 20) for _ in range(rng.randint(0, 15))]
            b = list(a)
            ordenar_desc(b, len(b))
            self.assertEqual(b, sorted(a, reverse=True))

    def test_contar_vivos_y_buscar_con_ceros_y_bordes(self):
        self.assertEqual(contar_vivos([], 0), 0)
        self.assertEqual(contar_vivos([0, 0, 0], 3), 0)
        self.assertEqual(contar_vivos([4, 0, 4, 0, 4], 5), 3)
        self.assertEqual(buscar_lineal([5, 5, 5], 3, 5), 0)
        self.assertEqual(buscar_lineal([1, 2, 3], 3, 3), 2)          # último elemento
        with self.assertRaises(ContratoError):
            buscar_lineal([1, 2], 3, 1)                             # n > len(a)

    def test_contratos_no_vuelven_cuadraticos_los_ciclos(self):
        """
        Con invariantes incrementales cada vuelta cuesta O(1). Con la versión anterior
        (sum(p[:i]) en cada vuelta) 60 000 elementos eran ~1,8·10⁹ operaciones.
        """
        n = 60000
        datos = [k % 7 for k in range(n)]
        inicio = time.perf_counter()
        self.assertEqual(sumar_puntajes(datos, n), sum(datos))
        self.assertEqual(contar_vivos(datos, n), sum(1 for v in datos if v > 0))
        self.assertEqual(buscar_lineal(datos, n, 99), -1)
        self.assertLess(time.perf_counter() - inicio, 5.0)

    def test_contratos_desactivados_dan_el_mismo_resultado(self):
        a = [5, 90, 12, 90, 0, 33]
        contratos.CONTRATOS_ACTIVOS = False
        try:
            b = list(a)
            ordenar_desc(b, len(b))
            self.assertEqual(b, [90, 90, 33, 12, 5, 0])
            self.assertEqual(sumar_puntajes(a, 6), 230)
            self.assertEqual(contar_vivos(a, 6), 5)
            self.assertEqual(buscar_lineal(a, 6, 12), 2)
        finally:
            contratos.CONTRATOS_ACTIVOS = True


class TestInvarianteDetectaErrores(unittest.TestCase):
    def test_guardia_con_menor_igual_viola_el_invariante(self):
        """Mutante de sumar_puntajes con `i <= n`: el invariante 0 <= i <= n lo detecta."""
        def sumar_mutante(p, n):
            requiere(0 <= n <= len(p), "0 <= n <= len(p)", "mutante")
            i, s = 0, 0
            while i <= n:                                # ERROR: <= en lugar de <
                s += p[i] if i < len(p) else 0
                i += 1
                invariante(0 <= i <= n, "0 <= i <= n", "mutante")
            return s

        with self.assertRaises(ContratoError):
            sumar_mutante([4, 5, 6], 2)

    def test_insercion_con_menor_igual_viola_el_invariante_interno(self):
        """
        Mutante de ordenar_desc con `a[j-1] <= clave`: también desplaza los iguales, así que
        (j, i] deja de cumplir ∀k: a[k] < clave (el orden sigue bien, pero ya no es estable).
        """
        def ordenar_mutante(a, n):
            i = 1
            while i < n:
                clave, j = a[i], i
                while j > 0 and a[j - 1] <= clave:              # ERROR: <= en lugar de <
                    a[j] = a[j - 1]
                    j -= 1
                    invariante(a[j + 1] < clave, "∀k∈(j,i]: a[k] < clave", "mutante")
                a[j] = clave
                i += 1

        with self.assertRaises(ContratoError):
            ordenar_mutante([5, 3, 5], 3)

    def test_precondicion_exacta_rompe_el_dash_diagonal(self):
        """
        Bug real de precondición: con {P} dx²+dy² <= 1 exacta (sin tolerancia), apuntar un tajo
        hacia (-40, -36) y luego hacer dash pasa una dirección de norma² 1.0000000000000002
        y el contrato tumba el juego. Se corrigió admitiendo dx²+dy² <= 1 + ε.
        """
        from juego.sistemas.partida import Entrada
        from juego.sistemas.run import Run
        from juego.verificacion import funciones

        def jugar():
            p = Run(semilla=1).crear_partida()
            p.actualizar(1 / 60, Entrada(atacar=True, apuntar=(-40.0, -36.0)))
            p.actualizar(1 / 60, Entrada(dash=True))

        original = funciones._EPS
        try:
            funciones._EPS = 0.0
            with self.assertRaises(ContratoError):
                jugar()
        finally:
            funciones._EPS = original
        jugar()  # con la precondición corregida no falla

    def test_mover_jugador_con_direccion_en_el_borde_de_epsilon(self):
        """
        {P} admite dx² + dy² <= 1 + ε. Con dx = √(1 + 9e-10) (dentro de P), rapidez 270 y dt 0,1
        el desplazamiento es 27·1,00000000045 > 27 + 1e-9: la Q antigua (|nx - x| <= paso + ε)
        lanzaba ContratoError. Con Q: |nx - x| <= paso·(1 + ε) se cumple P ⇒ wp.
        """
        dx = math.sqrt(1 + 9e-10)
        self.assertLessEqual(dx * dx, 1 + 1e-9)                 # la entrada sí cumple P
        nx, ny = mover_jugador(100.0, 100.0, dx, 0.0, 270.0, 0.1, 640, 320)
        self.assertAlmostEqual(nx, 127.0, places=6)
        self.assertEqual(ny, 100.0)
        nx, ny = mover_jugador(100.0, 100.0, 0.0, -dx, 270.0, 0.1, 640, 320)
        self.assertAlmostEqual(ny, 73.0, places=6)

    def test_mover_jugador_cumple_q_en_todo_el_dominio_de_p(self):
        """Muestreo aleatorio de entradas que cumplen P (incluye dt diminutos y bordes del mapa)."""
        rng = random.Random(7)
        for _ in range(20000):
            ang = rng.uniform(0, math.tau)
            r = math.sqrt(rng.uniform(0, 1 + 1e-9))
            x = rng.choice([0.0, 640.0, rng.uniform(0, 640)])
            y = rng.choice([0.0, 320.0, rng.uniform(0, 320)])
            dt = rng.choice([0.0, 0.1, 1 / 60, rng.uniform(0, 0.1), 10 ** rng.uniform(-12, -1)])
            mover_jugador(x, y, math.cos(ang) * r, math.sin(ang) * r, rng.uniform(0, 400), dt, 640, 320)

    def test_registro_de_contratos(self):
        antes = contratos.CONTADORES.get("aplicar_dano", 0)
        aplicar_dano(3, 1)
        self.assertEqual(contratos.CONTADORES["aplicar_dano"], antes + 2)  # {P} y {Q}


if __name__ == "__main__":
    unittest.main()
