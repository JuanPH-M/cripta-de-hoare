# Cripta de Hoare

[![Tests](https://github.com/JuanPH-M/cripta-de-hoare/actions/workflows/tests.yml/badge.svg)](https://github.com/JuanPH-M/cripta-de-hoare/actions/workflows/tests.yml)
[![Descargar el juego (.exe)](https://img.shields.io/badge/Descargar%20el%20juego-.exe%20Windows-2ea44f?logo=windows)](https://github.com/JuanPH-M/cripta-de-hoare/releases/latest/download/CriptaDeHoare.exe)
[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/JuanPH-M/cripta-de-hoare?quickstart=1)

Roguelike de acción en 2D hecho en Python con pygame: diez niveles generados al azar, un jefe final y una lógica de juego cuyas funciones clave están **verificadas formalmente** con precondiciones {P}, postcondiciones {Q}, invariantes y funciones variantes que además se comprueban mientras se juega.

El juego es el medio: lo importante es comprender, verificar y justificar la corrección del código.

## Contenido

1. [Descripción del juego](#1-descripción-del-juego)
2. [Cómo jugar (3 opciones)](#2-cómo-jugar-3-opciones)
3. [Controles](#3-controles)
4. [Estructura del código y requisitos de verificación](#4-estructura-del-código-y-requisitos-de-verificación)
5. [A. Precondiciones y postcondiciones](#5-a-precondiciones-y-postcondiciones)
6. [B. Verificación de código sin ciclos](#6-b-verificación-de-código-sin-ciclos)
7. [C. Verificación de ciclos](#7-c-verificación-de-ciclos)
8. [D. Arreglos](#8-d-arreglos)
9. [Apartado del código: la tienda paso a paso](#9-apartado-del-código-la-tienda-paso-a-paso)
10. [Bitácora de uso de IA](#10-bitácora-de-uso-de-ia)
11. [Preguntas frecuentes sobre la verificación](#11-preguntas-frecuentes-sobre-la-verificación)

---

## 1. Descripción del juego

- **Runs de 10 niveles.** Cada nivel es una mazmorra de salas y pasillos generada por semilla. Para abrir el portal de salida hay que derrotar a todos los enemigos. En el **nivel 10** espera el **Guardián del Abismo**, un jefe con tres fases.
- **Entre niveles** se elige 1 de 3 **bendiciones** gratis (ataque, vida, velocidad, crítico, dash, robo de vida, alcance…) y se visita al **mercader**, que vende 2 consumibles y 2 mejoras permanentes elegidas al azar.
- **Muerte = reinicio.** La pantalla de derrota indica quién te mató, en qué nivel, tus estadísticas y tu puesto en el ranking. Con `R` empiezas otra run.
- **Enemigos:** slime (salta hacia ti), murciélago (vuelo ondulante), esqueleto arquero (muestra una línea roja antes de disparar), bruto acorazado (brilla y embiste; si choca contra un muro queda aturdido) y el jefe (ráfagas radiales, disparos dirigidos, embestidas, espirales e invocaciones).
- **Sensación de juego:** partículas, sacudida de cámara, hitstop, números de daño flotantes, transiciones en iris, cámara lenta al morir o al vencer al jefe, iluminación con antorchas, y sonido y música sintetizados en memoria (el juego no usa archivos de sonido ni de imagen).
- **Panel de verificación en vivo (F1):** muestra cuántas veces se ha comprobado cada contrato mientras juegas.

**Tienda equitativa.** El oro de cada nivel está garantizado (monedas del suelo + botín de todos los enemigos, que vuelan hacia el jugador al abrirse el portal). Los precios suben por nivel (`precio = base + incremento × (nivel − 1)`) de modo que **el oro de un nivel siempre alcanza para 1 objeto y nunca para 3**:

| Nivel | Oro garantizado (mín / prom / máx, 400 semillas) | Poción | Bomba | Permanente más barato / más caro |
|---|---|---|---|---|
| 1 | 18 / 18,0 / 18 | 8 | 10 | 12 / 16 |
| 3 | 24 / 26,4 / 31 | 14 | 16 | 18 / 24 |
| 5 | 36 / 42,7 / 55 | 20 | 22 | 24 / 32 |
| 7 | 52 / 59,0 / 69 | 26 | 28 | 30 / 40 |
| 9 | 65 / 77,3 / 91 | 32 | 34 | 36 / 48 |

(Tabla completa con `python -m herramientas.balance 400`. En esa misma simulación un bot con reflejos casi perfectos gana 25 de 40 runs; sus derrotas se reparten entre los niveles 7 y 10.)

---

## 2. Cómo jugar (3 opciones)

### Opción 1: descargar el `.exe` (Windows, sin instalar nada)

1. Pulsa **[Descargar el juego (.exe)](https://github.com/JuanPH-M/cripta-de-hoare/releases/latest/download/CriptaDeHoare.exe)** (o entra a la sección *Releases* del repositorio).
2. Abre `CriptaDeHoare.exe` con doble clic. Si Windows SmartScreen avisa, pulsa **Más información → Ejecutar de todas formas** (el ejecutable no está firmado).

**Seguridad:** el juego no usa internet, no lee archivos personales y solo escribe `ranking.json` junto al `.exe`. Junto al ejecutable se publica `CriptaDeHoare.exe.sha256`; puedes comprobar que el archivo no fue alterado con `Get-FileHash CriptaDeHoare.exe` en PowerShell. Descárgalo solo desde la página de Releases de este repositorio.

El `.exe` lo genera automáticamente GitHub Actions (`.github/workflows/release.yml`) con PyInstaller cada vez que se crea un tag `v*`.

### Opción 2: doble clic en el script (Windows, Linux o Mac)

Requisito: Python 3.10 o superior instalado. Descarga el repositorio (botón verde **Code → Download ZIP**, o `git clone`) y:

- **Windows:** doble clic en `ejecutar.bat`.
- **Linux / Mac:** en una terminal, dentro de la carpeta, `./ejecutar.sh` (la primera vez puede hacer falta `chmod +x ejecutar.sh`).

El script crea el entorno virtual `.venv` si no existe, instala `requirements.txt` (pygame) y lanza `python main.py`. Las siguientes veces abre el juego directamente.

### Opción 3: jugar en el navegador con GitHub Codespaces

1. Pulsa el botón **Open in GitHub Codespaces** de arriba y espera a que termine de crearse (instala pygame solo).
2. Abre la pestaña **PORTS** (Puertos), busca el puerto **6080** ("Escritorio del juego") y pulsa el ícono del globo para abrirlo en el navegador. Pulsa **Connect**; si pide contraseña escribe `noPassword`.
3. En la terminal del Codespace ejecuta `python main.py`. El juego aparece en el escritorio del puerto 6080.

El puerto queda **privado** por defecto (solo tú, con tu sesión de GitHub, puedes abrirlo); no lo cambies a público.

### Comandos útiles (desde la carpeta del proyecto)

| Comando | Qué hace |
|---|---|
| `python main.py` | Abre el juego |
| `python -m unittest discover -s tests -t .` | 61 pruebas: verificación, economía, mazmorras, ranking, simulación, combate/navegación y app sin ventana |
| `python -m herramientas.trazas` | Tablas de traza reales de los ciclos (sección C y D) |
| `python -m herramientas.balance 400` | Oro contra precios y desempeño de un bot en runs completas |

---

## 3. Controles

| Acción | Teclado / ratón |
|---|---|
| Mover | WASD / flechas |
| Atacar (tajo) | Espacio / J / clic izquierdo (apunta al cursor). Con teclado apunta al enemigo válido más cercano (vivo, al alcance y sin pared de por medio); si no hay ninguno, ataca hacia donde mira |
| Dash (invulnerable) | Shift / K / clic derecho |
| Beber poción / lanzar bomba | Q / E |
| Pausa | Esc / P (también se pausa sola si la ventana pierde el foco) |
| Panel de verificación en vivo | F1 |
| Silenciar / pantalla completa | M / F11 |
| Bendiciones y tienda | 1-4, flechas + Enter, o ratón |

---

## 4. Estructura del código y requisitos de verificación

```text
main.py                     punto de entrada
juego/
  core/config.py            resolución, cuadrícula, constantes
  verificacion/
    contratos.py            requiere {P} / asegura {Q} / invariante {I} + registro para el panel F1
    funciones.py            las 9 funciones verificadas (lógica pura)
  entidades/                Jugador, Enemigo, Proyectil, Moneda, Portal
  sistemas/                 lógica pura del juego, sin pygame (combate, partida, run, economía, IA, mazmorra…)
  datos/tablas.py           tablas de balance (enemigos, curva, tienda, mejoras)
  datos/persistencia.py     ranking.json (usa ordenar_desc y buscar_lineal)
  ui/                       todo lo que usa pygame: app, escena, sprites, HUD, pantallas, efectos, audio
tests/                      pruebas unitarias y de integración
herramientas/               bot de pruebas, simulación de balance, trazas
```

La lógica (`core`, `verificacion`, `entidades`, `sistemas`, `datos`) **no importa pygame**; `tests/test_pureza.py` lo comprueba leyendo el código. Por eso el juego entero se puede simular sin ventana.

**Cómo se comprueban los contratos.** `requiere(P)` se evalúa al entrar a la función, `asegura(Q)` al salir e `invariante(I)` dentro de los ciclos. Si alguno es falso se lanza `ContratoError`, así que ningún estado inválido pasa en silencio. Los invariantes de ciclo se comprueban **de forma incremental** (O(1) por vuelta) para que los contratos no conviertan un ciclo O(n) en O(n²); las comprobaciones completas (sumas, conteos, copia "fantasma" para la permutación) se hacen una sola vez al final y solo si `contratos.CONTRATOS_ACTIVOS` es verdadero.

| Requisito | Mínimo | En el proyecto |
|---|---|---|
| Funciones sin ciclos con lógica relevante | 3 | `aplicar_dano`, `puede_comprar`, `comprar`, `mover_jugador`, `clasificar_combate` |
| Función con condicional anidado | 1 | `clasificar_combate` (4 ramas: esquiva, gana, empate, pierde) |
| Funciones con ciclos `while`/`for` | 2 | `sumar_puntajes`, `contar_vivos`, `buscar_lineal`, `ordenar_desc` (2 ciclos anidados) |
| Arreglos usados mediante funciones | 2 | puntajes de la run, vidas de los enemigos, inventario, ranking |
| Búsqueda u ordenamiento sobre un arreglo | 1 | `buscar_lineal` (inventario y ranking) y `ordenar_desc` (ranking, inserción) |
| Código comentado con {P} y {Q} | — | docstring de cada función de `juego/verificacion/funciones.py` |

---

## 5. A. Precondiciones y postcondiciones

Una **tripleta de Hoare** `{P} S {Q}` dice: *si el programa S empieza en un estado que cumple P y termina, entonces termina en un estado que cumple Q*. P es lo que la función exige a quien la llama; Q es lo que la función garantiza a cambio.

| Función | Tripleta de Hoare {P} S {Q} | Uso en el juego |
|---|---|---|
| `aplicar_dano(vida, dano)` | {vida ≥ 0 ∧ dano ≥ 0} S {res = max(0, vida − dano) ∧ 0 ≤ res ≤ vida} | Todo daño (`combate.py`, bomba en `partida.py`) |
| `puede_comprar(oro, precio)` | {oro ≥ 0 ∧ precio > 0} res := oro ≥ precio {res ⇔ oro ≥ precio} | Tienda (`run.py`) |
| `comprar(oro, precio, gastado, compras)` | {precio > 0 ∧ oro ≥ precio ∧ gastado ≥ 0 ∧ compras ≥ 0} S1;S2;S3 {oro2 ≥ 0 ∧ oro2 + gastado2 = oro + gastado ∧ compras2 = compras + 1} | Tienda (`run.py`) |
| `mover_jugador(x, y, dx, dy, rapidez, dt, ancho, alto)` | {0 ≤ x ≤ ancho ∧ 0 ≤ y ≤ alto ∧ dx² + dy² ≤ 1 + ε ∧ rapidez ≥ 0 ∧ 0 ≤ dt ≤ 0,1} S1;S2;S3 {0 ≤ nx ≤ ancho ∧ 0 ≤ ny ≤ alto ∧ \|nx − x\| ≤ paso·(1 + ε) ∧ \|ny − y\| ≤ paso·(1 + ε)}, con ε = 10⁻⁹ y paso = rapidez·dt | Movimiento de cada frame (`partida.py`) |
| `clasificar_combate(ataque, defensa, esquiva)` | {ataque ≥ 0 ∧ defensa ≥ 0} S {res = esquiva si esquiva; gana si atq > def; empate si atq = def; pierde si atq < def} | Cada golpe (`combate.py`) |
| `sumar_puntajes(p, n)` | {0 ≤ n ≤ len(p)} S {s = Σ_{k=0}^{n−1} p[k]} | Puntaje total (`run.py`) |
| `contar_vivos(vidas, n)` | {0 ≤ n ≤ len(vidas)} S {c = #{k ∈ [0,n) : vidas[k] > 0}} | Abrir el portal (`partida.py`) |
| `buscar_lineal(a, n, x)` | {0 ≤ n ≤ len(a)} S {(res = −1 ∧ ∀k∈[0,n): a[k] ≠ x) ∨ (0 ≤ res < n ∧ a[res] = x ∧ ∀k∈[0,res): a[k] ≠ x)} | Inventario (`run.py`) y puesto en el ranking |
| `ordenar_desc(a, n)` | {0 ≤ n ≤ len(a)} S {∀k∈[0,n−1): a[k] ≥ a[k+1] ∧ a[0..n) es permutación del original} | Ranking (`persistencia.py`) |

### Fortalecimiento de la precondición (regla de consecuencia)

Regla: si `P' ⇒ P` y `{P} S {Q}`, entonces `{P'} S {Q}`.

En la sección B se demuestra `{vida ≥ 0 ∧ dano ≥ 0} aplicar_dano {Q}`. En el juego, `combate.resolver_golpe` solo calcula `dano = ataque − defensa` en la rama `gana` de `clasificar_combate`, donde `ataque > defensa`, así que en esa llamada siempre `dano ≥ 1`:

```
P' ≡ vida ≥ 0 ∧ dano ≥ 1      y      P' ⇒ (vida ≥ 0 ∧ dano ≥ 0) ≡ P      (porque dano ≥ 1 ⇒ dano ≥ 0)
```

Por la regla de consecuencia, `{P'} aplicar_dano {Q}` es válida sin repetir la demostración: un contrato general sirve para cualquier llamada más restringida.

### Debilitamiento de la postcondición

Regla: si `{P} S {Q}` y `Q ⇒ Q'`, entonces `{P} S {Q'}`.

La barra de vida del HUD solo necesita saber que un golpe **nunca cura**, para animar la "vida fantasma" que baja despacio:

```
Q  ≡ res = max(0, vida − dano) ∧ 0 ≤ res ≤ vida
Q' ≡ res ≤ vida                                   Q ⇒ Q'  (se descarta información)
```

Entonces `{vida ≥ 0 ∧ dano ≥ 0} aplicar_dano {res ≤ vida}`: una garantía más débil, pero suficiente para quien la usa.

### Bug real causado por una precondición incorrecta: la ε de `mover_jugador`

La precondición "matemática" natural de `mover_jugador` era `dx² + dy² ≤ 1` (dirección unitaria o nula). **En punto flotante esa precondición es incorrecta:** `normalizar(-40, -36)` devuelve un vector cuya norma al cuadrado es `1.0000000000000002`.

1. El jugador lanza un tajo apuntando con el ratón en diagonal; el tajo guarda esa dirección normalizada en `mira_x, mira_y`.
2. Sin tocar las teclas de movimiento pulsa dash, que usa `mira` como dirección.
3. `mover_jugador` recibe `dx² + dy² = 1.0000000000000002 > 1` → `ContratoError: {P} violada en mover_jugador` y el juego se cierra.

La precondición exigía algo que quien llama **no puede garantizar**. **Primera corrección:** debilitar P a `dx² + dy² ≤ 1 + ε` (ε = 10⁻⁹).

**Segunda corrección (encontrada al revisar la entrega).** Al debilitar P, la Q antigua `|nx − x| ≤ paso + ε` dejó de ser consecuencia de P: con `dx = √(1 + 9·10⁻¹⁰)` (que sí cumple P), `rapidez = 270` y `dt = 0,1` el desplazamiento es `27·1,00000000045 ≈ 27 + 1,2·10⁻⁸ > 27 + 10⁻⁹` y el contrato fallaba. Es decir, **P no implicaba wp(S, Q)**. Se corrigió Q a `|nx − x| ≤ paso·(1 + ε)`, que sí se demuestra (sección B.1-b). Tests: `test_precondicion_exacta_rompe_el_dash_diagonal`, `test_mover_jugador_con_direccion_en_el_borde_de_epsilon` y `test_mover_jugador_cumple_q_en_todo_el_dominio_de_p` (20 000 entradas aleatorias que cumplen P).

### Explicación del equipo (A)

Entendemos la tripleta de Hoare como un contrato: quien llama a la función se compromete a cumplir P y la función se compromete a dejar el estado en Q. El bug de la ε nos enseñó que una precondición no solo debe ser "correcta en matemáticas", sino también algo que el código que llama pueda cumplir de verdad.


---

## 6. B. Verificación de código sin ciclos

Regla de asignación: **wp(x := E, Q) = Q[x := E]**, es decir, Q con cada aparición de x reemplazada por E. Las demostraciones van **de abajo hacia arriba**: se parte de Q y se sube instrucción por instrucción hasta obtener la precondición más débil; al final se comprueba que `P ⇒ wp`.

### B.1 Regla de asignación (wp de 2 funciones)

**(a) `puede_comprar`**: `res := (oro ≥ precio)` con `Q ≡ res ⇔ oro ≥ precio`.

```
wp(res := oro ≥ precio,  res ⇔ oro ≥ precio)
  = (oro ≥ precio) ⇔ (oro ≥ precio)        sustitución de res
  ≡ true
```

Como la wp es `true`, cualquier precondición la implica. La P `oro ≥ 0 ∧ precio > 0` no hace falta para Q; es una exigencia del dominio (no hay oro negativo ni objetos gratis).

**(b) `mover_jugador` con ε**: `S1: paso := rapidez·dt`, `S2: nx := min(max(x + dx·paso, 0), ancho)`, con `Qx ≡ 0 ≤ nx ≤ ancho ∧ |nx − x| ≤ paso·(1 + ε)`.

Paso 1, wp de S2 (sustituir nx). Sea `c(v) = min(max(v, 0), ancho)`:
```
wp(S2, Qx) = 0 ≤ c(x + dx·paso) ≤ ancho  ∧  |c(x + dx·paso) − x| ≤ paso·(1 + ε)
```
- `c(v) ≤ ancho` siempre; `c(v) ≥ 0` si `ancho ≥ 0`.
- Si `0 ≤ x ≤ ancho`, entonces `c(x) = x`, y como `c` no aumenta distancias: `|c(v) − x| = |c(v) − c(x)| ≤ |v − x| = |dx|·paso`.
- Además `dx² ≤ dx² + dy² ≤ 1 + ε ⇒ |dx| ≤ √(1 + ε) ≤ 1 + ε` (porque `1 + ε ≥ 1`). Si `paso ≥ 0`, `|dx|·paso ≤ paso·(1 + ε)`.

Por lo tanto `wp(S2, Qx) ⇐ 0 ≤ x ≤ ancho ∧ dx² + dy² ≤ 1 + ε ∧ paso ≥ 0`.

Paso 2, wp de S1 (sustituir paso por rapidez·dt):
```
wp(S1, ·) = 0 ≤ x ≤ ancho ∧ dx² + dy² ≤ 1 + ε ∧ rapidez·dt ≥ 0
```
P incluye `0 ≤ x ≤ ancho`, `dx² + dy² ≤ 1 + ε`, `rapidez ≥ 0` y `dt ≥ 0` (de donde `rapidez·dt ≥ 0`). Entonces **P ⇒ wp**: el jugador nunca sale del mapa ni avanza más de un paso. Para `ny` (S3) es igual. Al comprobar Q en ejecución se suma además el redondeo de una resta en punto flotante (un ulp del tamaño del mapa, ~10⁻¹³ px); la demostración es sobre números reales.

**(c) Rama `else` de `aplicar_dano`:** `wp(res := vida − dano, 0 ≤ res ≤ vida) = 0 ≤ vida − dano ≤ vida ≡ dano ≤ vida ∧ dano ≥ 0`. Se usa en B.3.

### B.2 Composición secuencial: `comprar` (3 instrucciones)

Regla: `wp(S1; S2; S3, Q) = wp(S1, wp(S2, wp(S3, Q)))`.

```
S1: oro2     := oro − precio
S2: gastado2 := gastado + precio
S3: compras2 := compras + 1
Q : oro2 ≥ 0 ∧ oro2 + gastado2 = oro + gastado ∧ compras2 = compras + 1
```

De abajo hacia arriba:

```
R2 = wp(S3, Q)  = oro2 ≥ 0 ∧ oro2 + gastado2 = oro + gastado ∧ compras + 1 = compras + 1
               ≡ oro2 ≥ 0 ∧ oro2 + gastado2 = oro + gastado

R1 = wp(S2, R2) = oro2 ≥ 0 ∧ oro2 + (gastado + precio) = oro + gastado

R0 = wp(S1, R1) = (oro − precio) ≥ 0 ∧ (oro − precio) + gastado + precio = oro + gastado
               ≡ oro ≥ precio ∧ (oro + gastado = oro + gastado)
               ≡ oro ≥ precio
```

`P ≡ precio > 0 ∧ oro ≥ precio ∧ gastado ≥ 0 ∧ compras ≥ 0` implica `R0 ≡ oro ≥ precio`. ∎ La conservación del oro se cumple por construcción; la única condición real es tener oro suficiente, y la tienda la comprueba antes con `puede_comprar`.

### B.3 Regla del condicional: `aplicar_dano` (ambas ramas)

```
S : if dano ≥ vida then res := 0 else res := vida − dano
P : vida ≥ 0 ∧ dano ≥ 0
Q : res = max(0, vida − dano) ∧ 0 ≤ res ≤ vida
```

Regla: `{P} if B then S1 else S2 {Q}` vale si `{P ∧ B} S1 {Q}` y `{P ∧ ¬B} S2 {Q}`.

**Rama then** (B ≡ dano ≥ vida):
```
wp(res := 0, Q) = 0 = max(0, vida − dano) ∧ 0 ≤ 0 ≤ vida
                ≡ vida − dano ≤ 0 ∧ vida ≥ 0
P ∧ B:  dano ≥ vida ⇒ vida − dano ≤ 0  ✔      vida ≥ 0 (de P) ✔
```

**Rama else** (¬B ≡ dano < vida):
```
wp(res := vida − dano, Q) = vida − dano = max(0, vida − dano) ∧ 0 ≤ vida − dano ≤ vida
                          ≡ vida − dano ≥ 0 ∧ dano ≥ 0
P ∧ ¬B: dano < vida ⇒ vida − dano > 0 ✔       dano ≥ 0 (de P) ✔
```

Las dos ramas cumplen Q, así que la tripleta es válida. ∎

**Condicional anidado: `clasificar_combate`** (4 ramas excluyentes). Aplicando la regla tres veces:
```
wp = (esquiva ⇒ Q[res:=esquiva]) ∧ (¬esquiva ∧ atq > def ⇒ Q[res:=gana])
   ∧ (¬esquiva ∧ atq ≤ def ∧ atq = def ⇒ Q[res:=empate]) ∧ (¬esquiva ∧ atq ≤ def ∧ atq ≠ def ⇒ Q[res:=pierde])
```
Cada implicación es cierta porque la guarda de cada rama es exactamente la condición que Q asocia a ese resultado (en la última, `atq ≤ def ∧ atq ≠ def ⇒ atq < def`). Las guardas cubren todos los casos sin solaparse. `test_clasificar_combate_cuatro_ramas` ejecuta cada rama.

### Explicación del equipo (B)

Para nosotros la wp es "lo mínimo que tiene que ser cierto antes" para que Q salga cierta después. La calculamos de abajo hacia arriba porque cada asignación solo cambia una variable, y así basta con sustituir.


---

## 7. C. Verificación de ciclos

Para cada ciclo: P y Q, invariante I con su justificación, **inicialización** (`P ⇒ I` tras las asignaciones iniciales), **conservación** (`{I ∧ B} cuerpo {I}`), **salida** (`I ∧ ¬B ⇒ Q`) y **variante** V (entera, acotada por abajo y que decrece en cada vuelta).

### C.1 `sumar_puntajes(p, n)`

```python
i = 0; s = 0
while i < n:            # B
    s = s + p[i]
    i = i + 1
```

- **P:** `0 ≤ n ≤ len(p)` **Q:** `s = Σ_{k=0}^{n−1} p[k]`
- **I:** `0 ≤ i ≤ n ∧ s = Σ_{k=0}^{i−1} p[k]` **V:** `n − i`

**Por qué este invariante.** Sale de generalizar Q cambiando la constante `n` por la variable `i`: "s es la suma de lo que ya recorrí". La parte `0 ≤ i ≤ n` sirve para dos cosas: con `B` da `i < n ≤ len(p)` (el índice `p[i]` es válido) y al salir permite concluir `i = n`.

**Inicialización:** `wp(i:=0; s:=0, I) = 0 ≤ 0 ≤ n ∧ 0 = Σ_{k=0}^{−1} p[k]`. La suma vacía vale 0 y `n ≥ 0` sale de P. ✔

**Conservación**, de abajo hacia arriba:
```
wp(i := i+1, I)    = 0 ≤ i+1 ≤ n ∧ s = Σ_{k=0}^{i} p[k]
wp(s := s+p[i], ·) = 0 ≤ i+1 ≤ n ∧ s + p[i] = Σ_{k=0}^{i} p[k]
                   ≡ 0 ≤ i+1 ≤ n ∧ s = Σ_{k=0}^{i−1} p[k]
```
Con `I ∧ B`: `i ≥ 0 ⇒ i+1 ≥ 0`; `i < n ⇒ i+1 ≤ n`; la suma parcial viene de I. ✔

**Salida:** `i ≤ n ∧ i ≥ n ⇒ i = n`, por lo tanto `s = Σ_{k=0}^{n−1} p[k]`. ✔

**Variante y terminación:** `V = n − i` es entera; por I, `V ≥ 0` (acotada); cada vuelta hace `i := i+1`, así que V baja exactamente 1. Un entero no negativo no puede bajar para siempre: hay como máximo `n` vueltas.

**En el código** el invariante se comprueba de forma incremental: al iniciar `s = 0`, y en cada vuelta `s − s_antes = p[i−1]`; por inducción eso equivale a `s = Σ p[0..i)`. También se comprueba `0 ≤ n − i < V_antes`. La suma completa se compara una sola vez en Q.

**Traza real** (`python -m herramientas.trazas`: los 4 primeros eventos de puntaje de una partida del bot, nivel 1, semilla 1):

| Iteración | i | p[i−1] | s | V = n − i | I: s = Σ p[0..i) |
|---|---|---|---|---|---|
| 0 (inicio) | 0 | — | 0 | 4 | 0 = 0 ✔ |
| 1 | 1 | 2 | 2 | 3 | 2 = 2 ✔ |
| 2 | 2 | 10 | 12 | 2 | 12 = 12 ✔ |
| 3 | 3 | 2 | 14 | 1 | 14 = 14 ✔ |
| 4 | 4 | 10 | 24 | 0 | 24 = 24 ✔ |

### C.2 `contar_vivos(vidas, n)`

```python
i = 0; c = 0
while i < n:
    if vidas[i] > 0:
        c = c + 1
    i = i + 1
```

- **P:** `0 ≤ n ≤ len(vidas)` **Q:** `c = #{k ∈ [0,n) : vidas[k] > 0}`
- **I:** `0 ≤ i ≤ n ∧ c = #{k ∈ [0,i) : vidas[k] > 0} ∧ 0 ≤ c ≤ i` **V:** `n − i`

**Justificación:** se generaliza Q de `n` a `i`. La cota `c ≤ i` permite demostrar `0 ≤ c ≤ n` al salir. El portal se abre cuando `c = 0`, así que de este conteo depende poder pasar de nivel.

**Inicialización:** `i = 0, c = 0`; el conjunto `#{k ∈ [0,0) : …}` es vacío y vale 0. ✔

**Conservación** (el cuerpo tiene un condicional: regla del condicional + asignación):
```
wp(i := i+1, I) = 0 ≤ i+1 ≤ n ∧ c = #{k∈[0,i] : vidas[k] > 0} ∧ c ≤ i+1
rama vidas[i] > 0:  wp(c := c+1, ·) ≡ c + 1 = #{k∈[0,i) : …} + 1 ∧ c + 1 ≤ i + 1   ⇐ I ∧ B ∧ vidas[i] > 0
rama vidas[i] ≤ 0:  (c no cambia)     c = #{k∈[0,i) : …} + 0 ∧ c ≤ i + 1           ⇐ I ∧ B ∧ vidas[i] ≤ 0
```
El índice es válido porque `0 ≤ i < n ≤ len(vidas)`. ✔

**Salida:** `I ∧ i ≥ n ⇒ i = n ⇒ c = #{k ∈ [0,n) : vidas[k] > 0}`. ✔ **Terminación:** `V = n − i ≥ 0` baja 1 por vuelta.

**En el código:** comprobación incremental `c − c_antes = (1 si vidas[i−1] > 0, si no 0)` y `0 ≤ n − i < V_antes`. En el juego, `Partida._contar_vivos` recorre el arreglo de enemigos en una sola pasada mediante una vista que lee `enemigos[k].vida` sin construir una lista intermedia.

**Traza real.** Vidas de los enemigos de la misma partida en el frame en que ya habían muerto dos (los muertos siguen en el arreglo con vida 0):

| Iteración | i | vidas[i−1] | c | V = n − i | I: c = #{k<i : vidas[k] > 0} |
|---|---|---|---|---|---|
| 0 (inicio) | 0 | — | 0 | 5 | 0 = 0 ✔ |
| 1 | 1 | 8 | 1 | 4 | 1 = 1 ✔ |
| 2 | 2 | 0 | 1 | 3 | 1 = 1 ✔ |
| 3 | 3 | 0 | 1 | 2 | 1 = 1 ✔ |
| 4 | 4 | 8 | 2 | 1 | 2 = 2 ✔ |
| 5 | 5 | 8 | 3 | 0 | 3 = 3 ✔ |

### C.3 `ordenar_desc(a, n)`: dos ciclos anidados (ordenamiento por inserción)

```python
i = 1
while i < n:                              # ciclo externo
    clave = a[i]
    j = i
    while j > 0 and a[j-1] < clave:       # ciclo interno
        a[j] = a[j-1]
        j = j - 1
    a[j] = clave
    i = i + 1
```

- **P:** `0 ≤ n ≤ len(a)`
- **Q:** `∀k ∈ [0, n−1): a[k] ≥ a[k+1] ∧ a[0..n) es permutación del arreglo original`
- **I externo:** `(n = 0 ∨ 1 ≤ i ≤ n) ∧ a[0..i) está ordenado descendente ∧ a[0..n) es permutación del original` **V externo:** `n − i`
- **I interno:** `0 ≤ j ≤ i ∧ a[0..j) no cambió ∧ a[j+1..i] = (antiguo a[j..i−1]) ∧ ∀k ∈ (j, i]: a[k] < clave` **V interno:** `j`

**Por qué estos invariantes.** El externo divide el arreglo en zona ordenada `a[0..i)` y zona pendiente `a[i..n)`, como en todo recorrido. El interno describe el "hueco" que se abre al desplazar: todo lo que ya se corrió a la derecha (posiciones `(j, i]`) es **estrictamente menor** que la clave, así que cuando la clave se escriba en `j` quedará delante de ellos.

**Ciclo interno, paso a paso.**

1. *Inicialización* (`clave := a[i]; j := i`): `(i, i]` es vacío, así que `∀k ∈ (i,i]: a[k] < clave` es verdadero por vacuidad; `0 ≤ i ≤ i`. ✔
2. *Conservación* (`{I_int ∧ j > 0 ∧ a[j−1] < clave} a[j] := a[j−1]; j := j−1 {I_int}`), de abajo hacia arriba:
   ```
   wp(j := j−1, I_int)   = 0 ≤ j−1 ≤ i ∧ ∀k ∈ (j−1, i]: a[k] < clave
                         ≡ 0 ≤ j−1 ≤ i ∧ a[j] < clave ∧ ∀k ∈ (j, i]: a[k] < clave
   wp(a[j] := a[j−1], ·) = 0 ≤ j−1 ≤ i ∧ a[j−1] < clave ∧ ∀k ∈ (j, i]: a[k] < clave
   ```
   `j > 0 ⇒ j−1 ≥ 0`; `a[j−1] < clave` es la guarda; el ∀ sobre `(j, i]` viene de I_int (esas posiciones no se tocan). ✔
3. *Salida:* `¬B ≡ j = 0 ∨ a[j−1] ≥ clave`.
4. *Variante* `j`: es entera, la guarda exige `j > 0` (acotada) y cada vuelta hace `j := j − 1`. Termina en a lo sumo `i` vueltas.

**Ciclo externo, paso a paso.**

1. *Inicialización* (`i := 1`): si `n = 0` el ciclo no se ejecuta y Q es trivial; si `n ≥ 1`, `a[0..1)` tiene un solo elemento y está ordenado. Nada se ha movido: es permutación del original. ✔
2. *Conservación:* tras el ciclo interno se escribe `a[j] := clave`. Entonces:
   - `a[0..j)` no cambió y ya estaba ordenado;
   - `a[j−1] ≥ clave` (por la salida del interno; si `j = 0` no hay vecino izquierdo);
   - `clave > a[j+1]` (por I_int con `k = j+1`, si `j < i`);
   - `a[j+1..i]` es el antiguo `a[j..i−1]`, que ya estaba ordenado.
   Por lo tanto `a[0..i]` queda ordenado. La clave se guardó antes de que el desplazamiento sobrescribiera `a[i]` y se vuelve a escribir en `a[j]`: los elementos son los mismos (permutación). Con `i := i + 1`, I_ext vuelve a valer. ✔
3. *Salida:* `I_ext ∧ i ≥ n ⇒ i = n ⇒ a[0..n)` ordenado y permutación = Q. ✔
4. *Variante* `n − i`: entera, `≥ 0` por I_ext, baja 1 por vuelta.

**Índices válidos:** en la guarda `j > 0 and a[j-1] < clave` el `and` es de cortocircuito: `a[j−1]` solo se lee si `j ≥ 1`. Además `j ≤ i < n ≤ len(a)`, así que `a[j]` también es válido.

**En el código:** el interno comprueba `a[j+1] < clave` (el único elemento que entra a `(j, i]` en esa vuelta) y `0 ≤ j < V_antes`; el externo comprueba solo los vecinos del punto de inserción (`a[j−1] ≥ a[j] ≥ a[j+1]`) y `0 ≤ n − i < V_antes`. La permutación se verifica en Q comparando con una copia "fantasma" ordenada, que solo se crea si los contratos están activos.

**Traza real** (`python -m herramientas.trazas`): puntajes finales de 4 runs completas jugadas por el bot (semillas 1 a 4), en el orden en que se jugaron, ordenados como lo hace el ranking:

| Paso | Ciclo | i | j | clave | a | Invariante comprobado | V |
|---|---|---|---|---|---|---|---|
| 0 | inicio | 1 | — | — | [5262, 1801, 3428, 2843] | a[0..1) ordenado (un elemento) | n − i = 3 |
| 1 | externo | 2 | 1 | 1801 | [5262, 1801, 3428, 2843] | a[0..2) = [5262, 1801] descendente ✔ | n − i = 2 |
| 2 | interno | 2 | 1 | 3428 | [5262, 1801, 1801, 2843] | a[2] = 1801 < 3428 ✔ | j = 1 |
| 3 | externo | 3 | 1 | 3428 | [5262, 3428, 1801, 2843] | a[0..3) = [5262, 3428, 1801] descendente ✔ | n − i = 1 |
| 4 | interno | 3 | 2 | 2843 | [5262, 3428, 1801, 1801] | a[3] = 1801 < 2843 ✔ | j = 2 |
| 5 | externo | 4 | 2 | 2843 | [5262, 3428, 2843, 1801] | a[0..4) = [5262, 3428, 2843, 1801] descendente ✔ | n − i = 0 |

En la fila 1 la clave 1801 no se mueve (5262 ≥ 1801: el interno da 0 vueltas). En las filas 2 y 4 se ve el "hueco": el valor desplazado aparece repetido hasta que la clave se escribe en `j`.

### Explicación del equipo (C)

Para nosotros el invariante es "la frase que sigue siendo cierta en cada vuelta" y la variante es "un contador que siempre baja y no puede bajar de cero"; con lo primero demostramos que el resultado es correcto y con lo segundo que el ciclo termina.


---

## 8. D. Arreglos

### Rangos y cuantificadores

| Notación | Significado | Dónde aparece |
|---|---|---|
| `a[0..n)` | los elementos `a[0], …, a[n−1]` | todos los contratos de arreglos |
| `∀k ∈ [0,i): a[k] ≠ x` | ninguno de los primeros `i` es `x` | invariante de `buscar_lineal` |
| `∃k ∈ [0,n): a[k] = x` | `x` está en el prefijo | caso `res ≠ −1` de `buscar_lineal` |
| `Σ_{k=0}^{i−1} p[k]` | suma del prefijo (vacía = 0) | `sumar_puntajes` |
| `#{k ∈ [0,n) : vidas[k] > 0}` | cantidad de índices que cumplen la condición | `contar_vivos` |
| `∀k ∈ [0,n−1): a[k] ≥ a[k+1]` | orden descendente | `ordenar_desc` |
| `∀k ∈ (j,i]: a[k] < clave` | todo lo ya desplazado es menor que la clave | ciclo interno de `ordenar_desc` |

### Precondición de índices válidos: `0 ≤ i < len(a)`

- `sumar_puntajes` y `contar_vivos`: con `I ∧ B` se tiene `0 ≤ i < n ≤ len`.
- `buscar_lineal`: la guarda `i < n and a[i] != x` usa cortocircuito: `a[i]` **solo** se evalúa si `i < n ≤ len(a)`.
- `ordenar_desc`: `a[j−1]` solo se lee si `j ≥ 1`, y `j ≤ i < n ≤ len(a)`.
- Uso encadenado en `Run.comprar_objeto`: `motivo_no_compra` comprueba que haya espacio (`buscar_lineal(…, VACIO) ≠ −1`). Por la Q de `buscar_lineal`, el índice `libre` cumple `0 ≤ libre < TAM_INVENTARIO`, y `inventario[libre] = …` es seguro. **La postcondición de una función se convierte en la precondición de índice de la instrucción siguiente.**

### Verificación formal de un algoritmo clásico: búsqueda lineal

```python
i = 0
while i < n and a[i] != x:
    i = i + 1
res = i if i < n else -1
```

- **P:** `0 ≤ n ≤ len(a)` **I:** `0 ≤ i ≤ n ∧ ∀k ∈ [0,i): a[k] ≠ x` **B:** `i < n ∧ a[i] ≠ x` **V:** `n − i`

1. **Inicialización:** `i = 0`. El rango `[0,0)` es vacío y el ∀ es verdadero por vacuidad; `0 ≤ 0 ≤ n` por P. ✔
2. **Conservación:** `wp(i := i+1, I) = 0 ≤ i+1 ≤ n ∧ ∀k ∈ [0,i]: a[k] ≠ x`. De `I ∧ B`: `i+1 ≤ n` (porque `i < n`), `∀k ∈ [0,i): a[k] ≠ x` (de I) y `a[i] ≠ x` (de B). Juntando: `∀k ∈ [0,i]`. ✔
3. **Salida:** `¬B ≡ i ≥ n ∨ a[i] = x`.
   - Si `i < n`, entonces `a[i] = x`, y con I (`∀k < i: a[k] ≠ x`) `i` es el **primer** índice de `x` → `res = i`. ✔
   - Si `i ≥ n`, entonces `i = n` (por I) y `∀k ∈ [0,n): a[k] ≠ x` → `res = −1`. ✔
4. **Terminación:** `V = n − i ≥ 0` y baja 1 por vuelta.

**Invariante del recorrido.** En todo recorrido el arreglo queda partido en una zona **procesada** `[0,i)`, de la que el invariante afirma algo ("x no está", "s es su suma", "c cuenta los vivos", "está ordenada"), y una zona **pendiente** `[i,n)`. Cada vuelta pasa un elemento de pendiente a procesado sin romper la afirmación. Por eso en el código basta comprobar el elemento que acaba de entrar (`a[i−1] ≠ x`): la comprobación es incremental. Al terminar, la zona pendiente está vacía (o se encontró x) y la afirmación sobre `[0,n)` es la postcondición.

**Traza real** (inventario `[1, 0, 0, 0]` del jugador al terminar el nivel; 1 = poción, 0 = vacío):

| Llamada | i inicial → final | V | Resultado |
|---|---|---|---|
| `buscar_lineal(a, 4, 0)` (casilla libre) | 0 → 1 | 4 → 3 | 1 (primer vacío) |
| `buscar_lineal(a, 4, 2)` (bomba) | 0 → 1 → 2 → 3 → 4 | 4 → 3 → 2 → 1 → 0 | −1 (recorrió todo sin salirse) |

**Otros algoritmos clásicos del proyecto:** suma (`sumar_puntajes`), conteo (`contar_vivos`) y ordenamiento simple con intercambio por desplazamiento (`ordenar_desc`), verificados en la sección C.

### Explicación del equipo (D)

Entendemos que en los arreglos lo más importante es no salirse de los índices: por eso cada acceso `a[i]` lo justificamos con la precondición o con el invariante, y usamos los cuantificadores para decir con precisión qué parte del arreglo ya revisamos.


---

## 9. Apartado del código: la tienda paso a paso

Este apartado recorre el código más sencillo del proyecto, la compra en la tienda, que une varias funciones verificadas.

**1. `puede_comprar(oro, precio)`** (en `juego/verificacion/funciones.py`): una sola asignación.

```python
requiere(oro >= 0 and precio > 0, "oro >= 0 ∧ precio > 0", "puede_comprar")   # {P}
res = oro >= precio                                                             # S
asegura(res == (oro >= precio), "res ⇔ oro >= precio", "puede_comprar")         # {Q}
return res
```

**2. `comprar(oro, precio, gastado, compras)`**: tres asignaciones seguidas (composición secuencial, B.2).

```python
oro2 = oro - precio          # S1: se descuenta el precio
gastado2 = gastado + precio  # S2: se suma a lo gastado
compras2 = compras + 1       # S3: una compra más
```

Su Q `oro2 + gastado2 = oro + gastado` dice que el oro ni se crea ni se destruye.

**3. `Run.motivo_no_compra` y `Run.comprar_objeto`** (en `juego/sistemas/run.py`): usan las funciones anteriores en orden.

```python
precio = economia.precio(objeto, nivel_tienda)             # base + incremento·(nivel − 1)
motivo = self.motivo_no_compra(objeto, precio)             # usa buscar_lineal y puede_comprar
if motivo:
    return motivo                                          # "Inventario lleno" u "Oro insuficiente"
self.oro, self.oro_gastado, self.compras = comprar(...)    # aquí ya se cumple {P}: oro >= precio
if es consumible:
    libre = buscar_lineal(inventario, TAM_INVENTARIO, VACIO)   # 0 <= libre < 4 por su {Q}
    inventario[libre] = id del objeto
```

**Por qué es correcto.** `comprar` exige `oro ≥ precio`; justo antes, `puede_comprar` devolvió verdadero, y por su Q eso significa exactamente `oro ≥ precio`. Igual con el inventario: `buscar_lineal` devolvió un índice distinto de −1, y su Q garantiza que está en `[0, 4)`. Cada Q prepara la P de lo siguiente. Se prueba en `tests/test_economia.py` (`test_compra_real_desde_una_run` y `test_rechazos`).

---

## 10. Bitácora de uso de IA

**Qué le pedimos.** Convertir nuestro juego por turnos de 3 niveles en un roguelike de 10 niveles con jefe, tienda equitativa y mejor aspecto visual; separar la lógica de pygame; implementar y documentar las funciones verificadas (pre y postcondiciones, wp, invariantes y variantes); y luego corregir los errores que encontramos jugando y revisando.

**Qué usamos.** Casi todo el código, las pruebas, las herramientas (bot, balance, trazas) y la primera versión de este documento. Del juego anterior se conservaron `aplicar_dano`, `clasificar_combate`, `buscar_lineal` y la idea del panel de verificación.

**Qué modificamos y revisamos.** Aportamos la idea y el proyecto base, las decisiones de diseño (tienda equitativa, máximo 10 niveles, mejor aspecto visual), probamos jugando, revisamos cada demostración contra el código y pedimos las correcciones. Errores reales encontrados:

1. **Precio contra oro en el nivel 9:** la IA subió los enemigos sin ajustar precios; el test de la tienda dio el contraejemplo `nivel=9, semilla=358: 87 not less than 86`. Se subió el incremento de los consumibles de 2 a 3.
2. **Ruta por defecto del ranking:** `ruta=RUTA_RANKING` se evaluaba al importar y una prueba escribió en el ranking real. Ahora se resuelve al llamar.
3. **Recorrido sin ceros:** los enemigos muertos se borraban del arreglo y `contar_vivos` nunca veía un 0. Ahora permanecen.
4. **ε de punto flotante** en `mover_jugador` (P y luego Q).
5. **Los 4 errores de jugabilidad:** rango, ataque automático, paredes y atascos.
6. **J / Espacio no atacaban** si no había un enemigo al alcance (el tajo no salía). Ahora sale hacia donde mira el personaje.

---

## 11. Preguntas frecuentes sobre la verificación

**¿Qué ocurre si se viola la precondición de `aplicar_dano`?**
`requiere` lanza `ContratoError: {P} violada en aplicar_dano: vida >= 0 ∧ dano >= 0` antes de ejecutar nada (`test_aplicar_dano_viola_precondicion`). Sin el contrato, `aplicar_dano(10, -4)` entraría en la rama `else` y devolvería `10 − (−4) = 14`: el golpe **curaría** y rompería `res ≤ vida`. Por eso `combate.resolver_golpe` clasifica primero el golpe y solo resta en la rama `gana`, donde el daño es ≥ 1 (precondición fortalecida, sección A).

**¿Cuál es la precondición más débil de esta asignación?**
En `comprar`: `wp(oro2 := oro − precio, oro2 ≥ 0) = oro − precio ≥ 0 ≡ oro ≥ precio`, justo lo que comprueba `puede_comprar` antes. En la rama `else` de `aplicar_dano`: `wp(res := vida − dano, 0 ≤ res ≤ vida) ≡ 0 ≤ dano ≤ vida`. En `puede_comprar`: `wp(res := oro ≥ precio, res ⇔ oro ≥ precio) ≡ true`.

**¿Por qué escogieron ese invariante?**
En `sumar_puntajes`, `I ≡ 0 ≤ i ≤ n ∧ s = Σ_{k<i} p[k]` es la postcondición generalizada (n → i): al salir con `i = n` se convierte en Q. La cota `0 ≤ i ≤ n` garantiza, junto con la guarda, que `p[i]` es un índice válido, y permite deducir `i = n` de `¬(i < n)`. En `ordenar_desc`, el interno `∀k ∈ (j,i]: a[k] < clave` es justo lo que hace falta para que, al escribir la clave en `j`, el prefijo quede ordenado.

**¿Qué ocurriría si el invariante fuera más débil?**
Con solo `0 ≤ i ≤ n` (sin la suma) se demuestran la terminación y los índices, pero al salir solo se sabe `i = n`, nada sobre `s`: Q no se puede demostrar. Sin `i ≤ n`, de `¬B` solo sale `i ≥ n`. En `ordenar_desc`, sin `a[k] < clave` no se podría asegurar `clave > a[j+1]` al insertar. Un invariante demasiado débil sigue siendo verdadero, pero no sirve para demostrar Q.

**¿Cómo demuestran que el ciclo termina?**
Con la función variante: un entero que el invariante mantiene `≥ 0` y que baja al menos 1 en cada vuelta. No puede bajar indefinidamente, así que hay como máximo `V₀` vueltas (`n` en los recorridos). El código lo comprueba en cada vuelta con `invariante(0 <= n - i < variante_antes, …)` (y `0 <= j < variante_int` en el interno del ordenamiento).

**¿Cuál es la función variante?**
`V = n − i` en `sumar_puntajes`, `contar_vivos` y `buscar_lineal`. En `ordenar_desc`, `n − i` para el ciclo externo y `j` para el interno (`j := j − 1`, protegido por la guarda `j > 0`).

**¿Qué ocurre en la verificación si cambiamos `<` por `<=`?**
En `sumar_puntajes` con `while i <= n`, `I ∧ B` ya no implica `i < n`: no se puede demostrar que `p[i]` sea válido (si `n = len(p)` hay `IndexError`; si no, se suma un elemento de más) y se rompe la conservación (`i` llega a `n + 1`). `test_guardia_con_menor_igual_viola_el_invariante` ejecuta ese mutante y el contrato lo detiene. En el ciclo interno de `ordenar_desc`, cambiar `a[j-1] < clave` por `<=` sigue ordenando pero desplaza también los iguales: deja de cumplirse `∀k ∈ (j,i]: a[k] < clave` y el orden deja de ser estable (el ranking usa esa estabilidad para dar el puesto correcto en un empate). `test_insercion_con_menor_igual_viola_el_invariante_interno` lo detecta.

**¿Cómo verificaron el recorrido del arreglo?**
En cuatro niveles. (1) Formalmente: invariante de zona procesada / pendiente con inicialización, conservación y salida (sección D). (2) En ejecución: `invariante(...)` comprueba en cada vuelta el elemento que entra a la zona procesada y `asegura` comprueba Q completa al final. (3) Con pruebas de bordes: arreglo vacío, elemento ausente, último elemento, `n < len(a)`, `n > len(a)` y primera aparición. (4) Con trazas reales capturadas con `sys.settrace` sobre la función real (`herramientas/trazas.py`).

**¿Qué error encontraron en el código generado por IA?**
El principal: al endurecer la curva de dificultad, la IA aumentó los enemigos por nivel sin recalcular los precios, y en los niveles 7 a 9 el oro de un solo nivel alcanzaba para 3 objetos. También la ε de `mover_jugador`, cuya P y luego cuya Q eran incorrectas en punto flotante, y el argumento por defecto `ruta=RUTA_RANKING` evaluado al importar (sección 10).

**¿Cómo utilizaron la verificación formal para detectar ese error?**
Escribimos la regla de la tienda como fórmula: `∀ nivel ∈ [1,9], ∀ semilla ∈ [0,400): min(precios) ≤ oro_garantizado < Σ 3 menores precios`, y la comprobamos exhaustivamente en `tests/test_economia.py`. Falló con un contraejemplo concreto (nivel 9, semilla 358: 87 ≥ 86). Tras subir el incremento de los consumibles, en el nivel 9 el oro máximo es 91 y la suma de los 3 precios más baratos es 32 + 34 + 36 = 102: la fórmula vale. Con la ε fue igual: al escribir `P ⇒ wp(S, Q)` vimos que con P debilitada la Q antigua no se podía demostrar, y el test con `dx = √(1 + 9·10⁻¹⁰)` lo confirmó.
