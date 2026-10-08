"""Ranking: inserción con empates, lectura robusta de ranking.json y ruta del ejecutable."""

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from juego.datos import persistencia


class TestRanking(unittest.TestCase):
    def test_posicion_del_nuevo_puntaje(self):
        r = [500, 300, 100]
        self.assertEqual(persistencia.insertar_puntaje(r, 400), 1)
        self.assertEqual(r, [500, 400, 300, 100])

    def test_empate_en_el_ultimo_puesto_no_entra(self):
        """Antes devolvía la posición del 50 que ya estaba aunque el nuevo 50 se recortaba."""
        r = [100] * 9 + [50]
        self.assertEqual(persistencia.insertar_puntaje(r, 50), -1)
        self.assertEqual(r, [100] * 9 + [50])

    def test_empate_queda_despues_de_los_iguales(self):
        r = [90, 70, 70, 10]
        self.assertEqual(persistencia.insertar_puntaje(r, 70), 3)
        self.assertEqual(r, [90, 70, 70, 70, 10])

    def test_cargar_ranking_ignora_valores_invalidos(self):
        with tempfile.TemporaryDirectory() as tmp:
            ruta = Path(tmp) / "ranking.json"
            ruta.write_text('[30, -5, "x", true, 1e999, 120.0, 75]', encoding="utf-8")
            self.assertEqual(persistencia.cargar_ranking(ruta), [120, 75, 30])
            ruta.write_text("{roto", encoding="utf-8")
            self.assertEqual(persistencia.cargar_ranking(ruta), [])

    def test_en_el_exe_el_ranking_va_junto_al_ejecutable(self):
        with mock.patch.object(sys, "frozen", True, create=True), \
                mock.patch.object(sys, "executable", str(Path("C:/Juegos/CriptaDeHoare.exe"))):
            self.assertEqual(persistencia._carpeta_del_juego(), Path("C:/Juegos").resolve())


if __name__ == "__main__":
    unittest.main()
