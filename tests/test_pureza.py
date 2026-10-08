"""La lógica (core, datos, entidades, sistemas, verificacion) no depende del motor gráfico."""

import ast
import unittest
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1] / "juego"
PAQUETES_PUROS = ["core", "datos", "entidades", "sistemas", "verificacion"]


class TestPureza(unittest.TestCase):
    def test_sin_pygame_fuera_de_ui(self):
        for paquete in PAQUETES_PUROS:
            for archivo in (RAIZ / paquete).glob("*.py"):
                arbol = ast.parse(archivo.read_text(encoding="utf-8"))
                for nodo in ast.walk(arbol):
                    nombres = []
                    if isinstance(nodo, ast.Import):
                        nombres = [a.name for a in nodo.names]
                    elif isinstance(nodo, ast.ImportFrom):
                        nombres = [nodo.module or ""]
                    for n in nombres:
                        with self.subTest(archivo=archivo.name, modulo=n):
                            self.assertFalse(n.startswith("pygame"))
                            self.assertFalse(n.startswith("juego.ui"))

    def test_funciones_verificadas_documentan_contratos(self):
        from juego.verificacion import funciones
        for nombre in ("aplicar_dano", "puede_comprar", "comprar", "mover_jugador", "clasificar_combate",
                       "sumar_puntajes", "contar_vivos", "buscar_lineal", "ordenar_desc"):
            doc = getattr(funciones, nombre).__doc__
            with self.subTest(funcion=nombre):
                self.assertIn("{P}", doc)
                self.assertIn("{Q}", doc)


if __name__ == "__main__":
    unittest.main()
