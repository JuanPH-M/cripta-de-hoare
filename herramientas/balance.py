"""
Simulación de balance: tabla de oro vs. precios por nivel y desempeño del bot.

Uso:  python -m herramientas.balance [semillas]
"""

import statistics
import sys

from herramientas.bot import jugar_nivel
from juego.core import config
from juego.sistemas import economia
from juego.sistemas.mazmorra import generar_mazmorra
from juego.sistemas.run import Run


def tabla_economia(semillas: int) -> None:
    print("Nivel | Oro garantizado (mín / prom / máx) | Poción | Bomba | Permanente más barato / más caro")
    print("------|-----------------------------------|--------|-------|--------------------------------")
    for nivel in range(1, config.NIVELES_MAX):
        oros = [economia.oro_garantizado(generar_mazmorra(s, nivel)) for s in range(semillas)]
        permanentes = [economia.precio(o, nivel) for o in ("espada", "armadura", "amuleto", "botas", "talisman")]
        print(f"{nivel:5d} | {min(oros):9d} / {statistics.mean(oros):6.1f} / {max(oros):4d}      "
              f"| {economia.precio('pocion', nivel):6d} | {economia.precio('bomba', nivel):5d} | "
              f"{min(permanentes)} / {max(permanentes)}")


def desempeno_bot(semillas: int) -> None:
    """El bot compra lo más barato que sirva y elige siempre la primera mejora."""
    alcanzados = []
    for s in range(semillas):
        run = Run(s)
        while True:
            resultado = jugar_nivel(run.crear_partida(), 300)
            if resultado in ("muerte", "tiempo", "victoria"):
                break
            run.completar_nivel()
            run.elegir_mejora(run.opciones_mejora()[0])
            oferta = economia.generar_oferta(run.semilla, run.nivel)
            for objeto in sorted(oferta, key=lambda o: economia.precio(o, run.nivel)):
                run.comprar_objeto(objeto, economia.nivel_de_tienda(run.nivel))
            run.avanzar_nivel()
        alcanzados.append(run.nivel if resultado != "victoria" else 11)
    print(f"\nBot sin ayudas en {semillas} runs: nivel promedio alcanzado {statistics.mean(alcanzados):.1f}, "
          f"máximo {max(alcanzados)} (11 = victoria)")
    for n in range(1, 12):
        c = alcanzados.count(n)
        if c:
            print(f"  muere/termina en nivel {n:2d}: {c}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    tabla_economia(n)
    desempeno_bot(max(5, n // 10))
