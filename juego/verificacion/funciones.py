"""
Funciones puras verificadas formalmente (sin pygame, sin estado global del juego).

Cada función documenta su precondición {P}, su postcondición {Q} y, si tiene
ciclos, su invariante {I} y su función variante {V}. Las condiciones se
comprueban en tiempo de ejecución con `requiere`, `asegura` e `invariante`.

Uso en el juego:
    aplicar_dano       -> sistemas/combate.py (todo daño a jugador y enemigos)
    puede_comprar      -> sistemas/economia.py y ui/pantallas.py (tienda)
    comprar            -> sistemas/economia.py (composición secuencial)
    mover_jugador      -> sistemas/partida.py (movimiento de cada frame)
    clasificar_combate -> sistemas/combate.py (condicional anidado)
    sumar_puntajes     -> sistemas/run.py (puntaje total, ciclo + arreglo)
    contar_vivos       -> sistemas/partida.py (abre el portal, ciclo + arreglo)
    buscar_lineal      -> sistemas/run.py (inventario de consumibles, búsqueda)
    ordenar_desc       -> datos/persistencia.py (ranking, ordenamiento)
"""

import math

from juego.verificacion import contratos
from juego.verificacion.contratos import requiere, asegura, invariante

# Resultados posibles de un intercambio de golpes.
ESQUIVA = "esquiva"
GANA = "gana"
EMPATE = "empate"
PIERDE = "pierde"

# Paso de tiempo máximo admitido por frame (evita "teletransportes" tras un tirón).
DT_MAXIMO = 0.1
# Tolerancia ε de punto flotante: normalizar() puede dar dx² + dy² = 1.0000000000000002.
_EPS = 1e-9


# =============================================================================
# 1) FUNCIONES SIN CICLOS
# =============================================================================

def aplicar_dano(vida: int, dano: int) -> int:
    """
    Resta `dano` a `vida` sin bajar de 0.

    {P}: vida >= 0  ∧  dano >= 0
    S  : if dano >= vida: res := 0  else: res := vida - dano
    {Q}: res = max(0, vida - dano)  ∧  0 <= res <= vida
    """
    requiere(vida >= 0 and dano >= 0, "vida >= 0 ∧ dano >= 0", "aplicar_dano")

    if dano >= vida:
        res = 0
    else:
        res = vida - dano

    asegura(res == max(0, vida - dano) and 0 <= res <= vida,
            "res = max(0, vida - dano) ∧ 0 <= res <= vida", "aplicar_dano")
    return res


def puede_comprar(oro: int, precio: int) -> bool:
    """
    Indica si alcanza el oro para pagar `precio`.

    {P}: oro >= 0  ∧  precio > 0
    S  : res := (oro >= precio)
    {Q}: res ⇔ oro >= precio
    """
    requiere(oro >= 0 and precio > 0, "oro >= 0 ∧ precio > 0", "puede_comprar")

    res = oro >= precio

    asegura(res == (oro >= precio), "res ⇔ oro >= precio", "puede_comprar")
    return res


def comprar(oro: int, precio: int, gastado: int, compras: int) -> tuple[int, int, int]:
    """
    Paga un artículo: composición secuencial de tres asignaciones.

    {P}: precio > 0  ∧  oro >= precio  ∧  gastado >= 0  ∧  compras >= 0
    S1 : oro2     := oro - precio
    S2 : gastado2 := gastado + precio
    S3 : compras2 := compras + 1
    {Q}: oro2 >= 0  ∧  oro2 + gastado2 = oro + gastado  ∧  compras2 = compras + 1
         (el oro ni se crea ni se destruye: solo pasa de "en bolsa" a "gastado")
    """
    requiere(precio > 0 and oro >= precio and gastado >= 0 and compras >= 0,
             "precio > 0 ∧ oro >= precio ∧ gastado >= 0 ∧ compras >= 0", "comprar")

    oro2 = oro - precio          # S1
    gastado2 = gastado + precio  # S2
    compras2 = compras + 1       # S3

    asegura(oro2 >= 0 and oro2 + gastado2 == oro + gastado and compras2 == compras + 1,
            "oro2 >= 0 ∧ oro2 + gastado2 = oro + gastado ∧ compras2 = compras + 1", "comprar")
    return oro2, gastado2, compras2


def mover_jugador(x: float, y: float, dx: float, dy: float, rapidez: float, dt: float,
                  ancho: float, alto: float) -> tuple[float, float]:
    """
    Avanza la posición (x, y) en la dirección (dx, dy) y la mantiene dentro del mapa.
    Los muros interiores se resuelven después en sistemas/colisiones.py.

    {P}: 0 <= x <= ancho  ∧  0 <= y <= alto  ∧  dx² + dy² <= 1 + ε
         ∧  rapidez >= 0  ∧  0 <= dt <= DT_MAXIMO
    S1 : paso := rapidez * dt
    S2 : nx := min(max(x + dx * paso, 0), ancho)
    S3 : ny := min(max(y + dy * paso, 0), alto)
    {Q}: 0 <= nx <= ancho  ∧  0 <= ny <= alto
         ∧  |nx - x| <= paso·(1 + ε)  ∧  |ny - y| <= paso·(1 + ε)

    P ⇒ wp(S1;S2;S3, Q): dx² <= 1 + ε  ⇒  |dx| <= √(1 + ε) <= 1 + ε, así que
    |nx - x| <= |dx|·paso <= paso·(1 + ε). Al comprobarlo en ejecución se suma
    además el redondeo de una resta en punto flotante (un ulp del mapa, ~1e-13 px).
    """
    requiere(0 <= x <= ancho and 0 <= y <= alto and dx * dx + dy * dy <= 1 + _EPS
             and rapidez >= 0 and 0 <= dt <= DT_MAXIMO,
             "0<=x<=ancho ∧ 0<=y<=alto ∧ dx²+dy²<=1+ε ∧ rapidez>=0 ∧ 0<=dt<=DT_MAXIMO",
             "mover_jugador")

    paso = rapidez * dt                          # S1
    nx = min(max(x + dx * paso, 0.0), ancho)     # S2
    ny = min(max(y + dy * paso, 0.0), alto)      # S3

    cota = paso * (1 + _EPS) + math.ulp(max(ancho, alto))
    asegura(0 <= nx <= ancho and 0 <= ny <= alto and abs(nx - x) <= cota and abs(ny - y) <= cota,
            "0<=nx<=ancho ∧ 0<=ny<=alto ∧ |nx-x|<=paso·(1+ε) ∧ |ny-y|<=paso·(1+ε)", "mover_jugador")
    return nx, ny


def clasificar_combate(ataque: int, defensa: int, esquiva: bool) -> str:
    """
    Clasifica un golpe con un condicional anidado de 4 ramas excluyentes.

    {P}: ataque >= 0  ∧  defensa >= 0
    {Q}: ( esquiva                      ⇒ res = "esquiva")
       ∧ (¬esquiva ∧ ataque >  defensa  ⇒ res = "gana")
       ∧ (¬esquiva ∧ ataque == defensa  ⇒ res = "empate")
       ∧ (¬esquiva ∧ ataque <  defensa  ⇒ res = "pierde")
    """
    requiere(ataque >= 0 and defensa >= 0, "ataque >= 0 ∧ defensa >= 0", "clasificar_combate")

    if esquiva:
        res = ESQUIVA
    else:
        if ataque > defensa:
            res = GANA
        else:
            if ataque == defensa:
                res = EMPATE
            else:
                res = PIERDE

    asegura((esquiva and res == ESQUIVA)
            or (not esquiva and ataque > defensa and res == GANA)
            or (not esquiva and ataque == defensa and res == EMPATE)
            or (not esquiva and ataque < defensa and res == PIERDE),
            "rama elegida coherente con (ataque, defensa, esquiva)", "clasificar_combate")
    return res


# =============================================================================
# 2) FUNCIONES CON CICLOS SOBRE ARREGLOS
# =============================================================================

def sumar_puntajes(p: list[int], n: int) -> int:
    """
    Suma los primeros n puntajes del arreglo p.

    {P}: 0 <= n <= len(p)
    {Q}: s = Σ_{k=0}^{n-1} p[k]
    {I}: 0 <= i <= n  ∧  s = Σ_{k=0}^{i-1} p[k]
    {V}: n - i

    El invariante se comprueba de forma incremental (O(1) por vuelta): al iniciar
    s = 0 = Σ vacía, y en cada vuelta s crece exactamente en p[i-1]. Por inducción
    eso equivale a s = Σ p[0..i). La suma completa se compara una sola vez en {Q}.
    """
    requiere(0 <= n <= len(p), "0 <= n <= len(p)", "sumar_puntajes")

    i = 0
    s = 0
    invariante(0 <= i <= n and s == 0, "I al iniciar", "sumar_puntajes")
    while i < n:
        variante_antes = n - i
        s_antes = s
        s = s + p[i]
        i = i + 1
        invariante(0 <= i <= n and s - s_antes == p[i - 1], "I tras iterar", "sumar_puntajes")
        invariante(0 <= n - i < variante_antes, "V decrece y es >= 0", "sumar_puntajes")

    if contratos.CONTRATOS_ACTIVOS:
        asegura(i == n and s == sum(p[:n]), "s = Σ p[0..n)", "sumar_puntajes")
    return s


def contar_vivos(vidas: list[int], n: int) -> int:
    """
    Cuenta cuántos enemigos de vidas[0..n) siguen con vida (> 0).

    {P}: 0 <= n <= len(vidas)
    {Q}: c = #{k ∈ [0, n) : vidas[k] > 0}  ∧  0 <= c <= n
    {I}: 0 <= i <= n  ∧  c = #{k ∈ [0, i) : vidas[k] > 0}  ∧  0 <= c <= i
    {V}: n - i

    Comprobación incremental (O(1) por vuelta): al iniciar c = 0 = #∅, y en cada
    vuelta c sube 1 si vidas[i-1] > 0 y se queda igual si no. El conteo completo
    se compara una sola vez en {Q}.
    """
    requiere(0 <= n <= len(vidas), "0 <= n <= len(vidas)", "contar_vivos")

    i = 0
    c = 0
    invariante(0 <= i <= n and c == 0, "I al iniciar", "contar_vivos")
    while i < n:
        variante_antes = n - i
        c_antes = c
        if vidas[i] > 0:
            c = c + 1
        i = i + 1
        invariante(0 <= i <= n and 0 <= c <= i and c - c_antes == (1 if vidas[i - 1] > 0 else 0),
                   "c cuenta vivos de [0,i)", "contar_vivos")
        invariante(0 <= n - i < variante_antes, "V decrece y es >= 0", "contar_vivos")

    if contratos.CONTRATOS_ACTIVOS:
        asegura(i == n and 0 <= c <= n and c == sum(1 for k in range(n) if vidas[k] > 0),
                "c = #{k∈[0,n): vidas[k] > 0}", "contar_vivos")
    return c


def buscar_lineal(a: list[int], n: int, x: int) -> int:
    """
    Búsqueda lineal: primer índice de x en a[0..n), o -1 si no está.

    {P}: 0 <= n <= len(a)
    {Q}: (res = -1 ∧ ∀k ∈ [0, n): a[k] ≠ x)
         ∨ (0 <= res < n ∧ a[res] = x ∧ ∀k ∈ [0, res): a[k] ≠ x)
    {I}: 0 <= i <= n  ∧  ∀k ∈ [0, i): a[k] ≠ x
    {V}: n - i

    Comprobación incremental: al iniciar [0, 0) es vacío; en cada vuelta solo
    entra a la zona procesada el elemento a[i-1], así que basta con ver que a[i-1] ≠ x.
    """
    requiere(0 <= n <= len(a), "0 <= n <= len(a)", "buscar_lineal")

    i = 0
    invariante(0 <= i <= n, "I al iniciar: [0,0) vacío", "buscar_lineal")
    # Cortocircuito: a[i] solo se evalúa cuando i < n, así 0 <= i < len(a).
    while i < n and a[i] != x:
        variante_antes = n - i
        i = i + 1
        invariante(0 <= i <= n and a[i - 1] != x, "∀k∈[0,i): a[k] ≠ x", "buscar_lineal")
        invariante(0 <= n - i < variante_antes, "V decrece y es >= 0", "buscar_lineal")

    if i < n:
        res = i
    else:
        res = -1

    if contratos.CONTRATOS_ACTIVOS:
        asegura((res == -1 and all(a[k] != x for k in range(n)))
                or (0 <= res < n and a[res] == x and all(a[k] != x for k in range(res))),
                "primer índice de x o -1", "buscar_lineal")
    return res


def ordenar_desc(a: list[int], n: int) -> None:
    """
    Ordena a[0..n) de mayor a menor in situ (inserción). Se usa para el ranking.

    {P}: 0 <= n <= len(a)
    {Q}: ∀k ∈ [0, n-1): a[k] >= a[k+1]  ∧  a[0..n) es permutación del original
    {I externo}: (n = 0 ∨ 1 <= i <= n)  ∧  ∀k ∈ [0, i-1): a[k] >= a[k+1]
    {I interno}: 0 <= j <= i  ∧  ∀k ∈ (j, i]: a[k] < clave
    {V externo}: n - i      {V interno}: j

    Los invariantes se comprueban de forma incremental: en el ciclo interno solo
    entra a (j, i] el elemento recién desplazado a[j+1]; en el externo, como
    a[0..j) y a[j+1..i] ya estaban ordenados, basta mirar los vecinos de la
    posición donde se insertó la clave. La copia "fantasma" para la permutación
    solo se crea si los contratos están activos.
    """
    requiere(0 <= n <= len(a), "0 <= n <= len(a)", "ordenar_desc")
    original = sorted(a[:n]) if contratos.CONTRATOS_ACTIVOS else None

    i = 1
    invariante(n == 0 or 1 <= i <= n, "I externo al iniciar: a[0..1) ordenado", "ordenar_desc")
    while i < n:
        variante_ext = n - i
        clave = a[i]
        j = i
        invariante(0 <= j <= i, "I interno al iniciar: (i, i] vacío", "ordenar_desc")
        # j > 0 se evalúa primero, por eso a[j-1] siempre usa un índice en [0, len(a)).
        while j > 0 and a[j - 1] < clave:
            variante_int = j
            a[j] = a[j - 1]
            j = j - 1
            invariante(0 <= j <= i and a[j + 1] < clave, "∀k∈(j,i]: a[k] < clave", "ordenar_desc")
            invariante(0 <= j < variante_int, "V interno (j) decrece y es >= 0", "ordenar_desc")
        a[j] = clave
        i = i + 1
        invariante((j == 0 or a[j - 1] >= a[j]) and (j + 1 >= i or a[j] >= a[j + 1]),
                   "a[0..i) ordenado descendente", "ordenar_desc")
        invariante(0 <= n - i < variante_ext, "V externo (n - i) decrece y es >= 0", "ordenar_desc")

    if contratos.CONTRATOS_ACTIVOS:
        asegura(all(a[k] >= a[k + 1] for k in range(n - 1)) and sorted(a[:n]) == original,
                "a[0..n) descendente y permutación del original", "ordenar_desc")
