"""
Trazas reales de los ciclos verificados.

Ejecuta las funciones del juego tal cual (sin copias) y, con sys.settrace,
captura el valor de las variables al final de cada iteración. Los datos de
entrada salen de partidas reales jugadas por el bot.

Uso:  python -m herramientas.trazas
"""

import inspect
import sys

from herramientas.bot import decidir, jugar_nivel
from juego.sistemas.run import Run
from juego.verificacion import funciones

# Línea que marca "fin de una vuelta" en cada ciclo (la comprobación de la variante).
FIN_VUELTA = '"V decrece y es >= 0"'
FIN_VUELTA_EXTERNA = '"V externo (n - i) decrece y es >= 0"'
FIN_VUELTA_INTERNA = '"V interno (j) decrece y es >= 0"'


def _linea_que_contiene(funcion, texto: str) -> int:
    lineas, inicio = inspect.getsourcelines(funcion)
    for k, linea in enumerate(lineas):
        if texto in linea:
            return inicio + k
    raise ValueError(texto)


def trazar(funcion, marcas: list[str], variables: list[str], *args) -> tuple[list[dict], object]:
    """
    Ejecuta funcion(*args) y registra `variables` cada vez que se ejecuta una de las
    líneas `marcas`. Cada fila lleva "marca" (índice de la marca) y copias de las listas.
    """
    objetivos = {_linea_que_contiene(funcion, m): k for k, m in enumerate(marcas)}
    codigo = funcion.__code__
    filas: list[dict] = []

    def rastreador(frame, evento, _):
        if frame.f_code is codigo and evento == "line" and frame.f_lineno in objetivos:
            fila = {"marca": objetivos[frame.f_lineno]}
            for v in variables:
                valor = frame.f_locals.get(v)
                fila[v] = list(valor) if isinstance(valor, list) else valor
            filas.append(fila)
        return rastreador

    sys.settrace(rastreador)
    try:
        resultado = funcion(*args)
    finally:
        sys.settrace(None)
    return filas, resultado


def datos_reales(semilla: int = 1):
    """Juega el nivel 1 con el bot y toma los puntajes y las vidas enemigas a mitad del combate."""
    run = Run(semilla)
    p = run.crear_partida()
    vidas = None
    for _ in range(60 * 60):
        p.actualizar(1 / 60, decidir(p))
        p.tomar_eventos()
        if vidas is None and sum(1 for e in p.enemigos if not e.vivo) >= 2:
            vidas = [e.vida for e in p.enemigos]   # los valores que lee contar_vivos en ese frame
        if p.completada:
            break
    return run.puntajes[:4], vidas or [e.vida for e in p.enemigos], list(run.jugador.inventario)


def puntajes_de_partidas(semillas=(1, 2, 3, 4)) -> list[int]:
    """
    Puntaje final de runs completas jugadas por el bot (sin invencibilidad, como en
    herramientas/balance.py), en el orden en que se jugaron: el arreglo que recibiría el ranking.
    """
    resultado = []
    for s in semillas:
        run = Run(s)
        while True:
            r = jugar_nivel(run.crear_partida(), 300)
            if r in ("muerte", "tiempo"):
                break
            if r == "victoria":
                run.ganar()
                break
            run.completar_nivel()
            run.elegir_mejora(run.opciones_mejora()[0])
            run.avanzar_nivel()
        resultado.append(run.puntaje_total())
    return resultado


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    puntajes, vidas, inventario = datos_reales()

    filas, total = trazar(funciones.sumar_puntajes, [FIN_VUELTA], ["i", "s"], puntajes, len(puntajes))
    n = len(puntajes)
    print(f"sumar_puntajes(p={puntajes}, n={n}) = {total}")
    print("| Iteración | i | p[i−1] | s | V = n − i | I: s = Σ p[0..i) |")
    print("|---|---|---|---|---|---|")
    print(f"| 0 (inicio) | 0 | — | 0 | {n} | 0 = 0 ✔ |")
    for k, f in enumerate(filas, 1):
        print(f"| {k} | {f['i']} | {puntajes[f['i'] - 1]} | {f['s']} | {n - f['i']} | "
              f"{f['s']} = {sum(puntajes[:f['i']])} ✔ |")

    filas, c = trazar(funciones.contar_vivos, [FIN_VUELTA], ["i", "c"], vidas, len(vidas))
    n = len(vidas)
    print(f"\ncontar_vivos(vidas={vidas}, n={n}) = {c}")
    print("| Iteración | i | vidas[i−1] | c | V = n − i | I: c = #{k<i : vidas[k] > 0} |")
    print("|---|---|---|---|---|---|")
    print(f"| 0 (inicio) | 0 | — | 0 | {n} | 0 = 0 ✔ |")
    for k, f in enumerate(filas, 1):
        esperado = sum(1 for v in vidas[:f["i"]] if v > 0)
        print(f"| {k} | {f['i']} | {vidas[f['i'] - 1]} | {f['c']} | {n - f['i']} | {f['c']} = {esperado} ✔ |")

    for x, nombre in ((0, "casilla libre"), (2, "bomba")):
        filas, res = trazar(funciones.buscar_lineal, [FIN_VUELTA], ["i"], inventario, len(inventario), x)
        print(f"\nbuscar_lineal(a={inventario}, n={len(inventario)}, x={x} [{nombre}]) = {res}")
        print(f"  inicio: i = 0, V = {len(inventario)}")
        for k, f in enumerate(filas, 1):
            print(f"  iteración {k}: i = {f['i']}, V = {len(inventario) - f['i']}")

    ranking = puntajes_de_partidas()
    original = list(ranking)
    filas, _ = trazar(funciones.ordenar_desc, [FIN_VUELTA_INTERNA, FIN_VUELTA_EXTERNA],
                      ["i", "j", "clave", "a"], ranking, len(ranking))
    n = len(original)
    print(f"\nordenar_desc(a={original}, n={n})  ->  {ranking}")
    print("| Paso | Ciclo | i | j | clave | a | Invariante comprobado | V |")
    print("|---|---|---|---|---|---|---|---|")
    print(f"| 0 | inicio | 1 | — | — | {original} | a[0..1) ordenado (un elemento) | n − i = {n - 1} |")
    for k, f in enumerate(filas, 1):
        if f["marca"] == 0:   # fin de una vuelta interna (antes de que se incremente i)
            print(f"| {k} | interno | {f['i']} | {f['j']} | {f['clave']} | {f['a']} | "
                  f"a[{f['j'] + 1}] = {f['a'][f['j'] + 1]} < {f['clave']} ✔ | j = {f['j']} |")
        else:                 # fin de una vuelta externa (clave ya insertada, i ya incrementado)
            prefijo = f["a"][:f["i"]]
            ok = all(prefijo[t] >= prefijo[t + 1] for t in range(len(prefijo) - 1))
            print(f"| {k} | externo | {f['i']} | {f['j']} | {f['clave']} | {f['a']} | "
                  f"a[0..{f['i']}) = {prefijo} descendente {'✔' if ok else '✘'} | n − i = {n - f['i']} |")


if __name__ == "__main__":
    main()
