"""
Pantallas y menús. Cada función dibuja y devuelve la lista de zonas
clicables [(rect, acción)] para que app.py gestione el ratón.
"""

import math

import pygame

from juego.core import config
from juego.datos import tablas
from juego.sistemas import economia
from juego.sistemas.run import Run
from juego.ui import iconos, paleta, textos
from juego.ui.tween import ease_out_back, ease_out_cubic
from juego.verificacion import contratos

W, H = config.ANCHO_VENTANA, config.ALTO_VENTANA
Zonas = list[tuple[pygame.Rect, object]]

_fondo_cache: pygame.Surface | None = None


# =============================================================================
# Elementos comunes
# =============================================================================

def fondo(s: pygame.Surface, t: float) -> None:
    """Fondo animado de los menús: degradado, arcos de cripta y brasas flotantes."""
    global _fondo_cache
    if _fondo_cache is None:
        _fondo_cache = pygame.Surface((W, H))
        for y in range(H):
            _fondo_cache.fill(paleta.mezclar(paleta.PANEL, paleta.NOCHE, y / H), (0, y, W, 1))
        for i in range(7):
            cx = 90 + i * 183
            pygame.draw.rect(_fondo_cache, paleta.mezclar(paleta.PANEL, paleta.NOCHE, 0.4), (cx - 40, 300, 80, H))
            pygame.draw.circle(_fondo_cache, paleta.mezclar(paleta.PANEL, paleta.NOCHE, 0.4), (cx, 300), 40)
            pygame.draw.rect(_fondo_cache, paleta.NOCHE, (cx - 26, 330, 52, H))
            pygame.draw.circle(_fondo_cache, paleta.NOCHE, (cx, 330), 26)
    s.blit(_fondo_cache, (0, 0))
    for i in range(46):
        semilla = i * 97.31
        x = (semilla * 13.7 + math.sin(t * 0.6 + i) * 30) % W
        y = H - ((t * (18 + i % 7 * 6) + semilla * 7) % (H + 40)) + 20
        brillo = 0.5 + 0.5 * math.sin(t * 3 + i)
        color = paleta.mezclar(paleta.ROJO_OSCURO, paleta.NARANJA if i % 3 else paleta.ORO, brillo)
        tam = 2 + (i % 3)
        pygame.draw.rect(s, color, (int(x), int(y), tam, tam))


def oscurecer(s: pygame.Surface, alfa: int = 170) -> None:
    capa = pygame.Surface((W, H), pygame.SRCALPHA)
    capa.fill((*paleta.NOCHE, alfa))
    s.blit(capa, (0, 0))


def panel(s: pygame.Surface, rect: pygame.Rect, borde=paleta.PANEL_BORDE, relleno=paleta.PANEL) -> None:
    sombra = rect.move(0, 8)
    pygame.draw.rect(s, paleta.NOCHE, sombra, border_radius=14)
    pygame.draw.rect(s, relleno, rect, border_radius=14)
    pygame.draw.rect(s, borde, rect, 3, border_radius=14)
    pygame.draw.line(s, paleta.mezclar(relleno, paleta.BLANCO, 0.08), (rect.x + 14, rect.y + 4),
                     (rect.right - 14, rect.y + 4), 2)


def boton(s: pygame.Surface, rect: pygame.Rect, texto: str, activo: bool, t: float,
          habilitado: bool = True, tam: int = 24) -> None:
    if activo and habilitado:
        r = rect.inflate(10 + 4 * math.sin(t * 6), 4)
        pygame.draw.rect(s, paleta.NOCHE, r.move(0, 5), border_radius=10)
        pygame.draw.rect(s, paleta.ORO_OSCURO, r, border_radius=10)
        pygame.draw.rect(s, paleta.ORO, r, 3, border_radius=10)
        textos.dibujar(s, texto, r.centerx, r.centery, tam, paleta.NOCHE, True, "center", 0)
    else:
        pygame.draw.rect(s, paleta.NOCHE, rect.move(0, 4), border_radius=10)
        pygame.draw.rect(s, paleta.PANEL_CLARO, rect, border_radius=10)
        pygame.draw.rect(s, paleta.PANEL_BORDE, rect, 2, border_radius=10)
        color = paleta.TEXTO if habilitado else paleta.TEXTO_APAGADO
        textos.dibujar(s, texto, rect.centerx, rect.centery, tam, color, True, "center")


def tecla(s: pygame.Surface, texto: str, x: float, y: float, tam: int = 15) -> pygame.Rect:
    surf = textos.render(texto, tam, paleta.TEXTO, True, 0)
    r = surf.get_rect(center=(int(x), int(y))).inflate(14, 8)
    pygame.draw.rect(s, paleta.NOCHE, r.move(0, 3), border_radius=6)
    pygame.draw.rect(s, paleta.PANEL_CLARO, r, border_radius=6)
    pygame.draw.rect(s, paleta.PANEL_BORDE, r, 2, border_radius=6)
    s.blit(surf, surf.get_rect(center=r.center))
    return r


def titulo(s: pygame.Surface, texto: str, y: float, t: float, color=paleta.ORO, tam: int = 64,
           entrada: float = 1.0) -> None:
    escala = 0.6 + 0.4 * ease_out_back(entrada)
    flota = math.sin(t * 2) * 3
    textos.dibujar(s, texto, W / 2 + 4, y + 6 + flota, tam, paleta.NOCHE, True, "center", 0,
                   alfa=int(160 * min(1, entrada * 2)), escala=escala)
    textos.dibujar(s, texto, W / 2, y + flota, tam, color, True, "center", 3,
                   alfa=int(255 * min(1, entrada * 2)), escala=escala)


def _botones_verticales(s, opciones: list[str], seleccion: int, t: float, y0: int, t_estado: float,
                        ancho: int = 360) -> Zonas:
    zonas = []
    for i, texto in enumerate(opciones):
        k = ease_out_cubic((t_estado - 0.08 * i) * 3)
        r = pygame.Rect(0, 0, ancho, 54)
        r.center = (W // 2 + int((1 - k) * 120), y0 + i * 70)
        if k > 0.01:
            boton(s, r, texto, i == seleccion, t)
        zonas.append((r, i))
    return zonas


# =============================================================================
# Menú principal, ayuda y ranking
# =============================================================================

OPCIONES_MENU = ["Nueva partida", "Cómo jugar", "Ranking", "Salir"]


def menu(s: pygame.Surface, t: float, seleccion: int, t_estado: float, mejor: int) -> Zonas:
    fondo(s, t)
    titulo(s, "CRIPTA DE HOARE", 150, t, entrada=min(1.0, t_estado * 1.5))
    textos.dibujar(s, "Diez niveles. Un guardián. Cada golpe, verificado.", W / 2, 222, 22,
                   paleta.TEXTO_SUAVE, False, "center", alfa=int(255 * min(1, t_estado * 2)))
    zonas = _botones_verticales(s, OPCIONES_MENU, seleccion, t, 320, t_estado)
    if mejor > 0:
        textos.dibujar(s, f"Mejor puntaje: {mejor}", W / 2, 620, 18, paleta.ORO, True, "center")
    textos.dibujar(s, "Flechas/WASD + Enter  ·  Ratón  ·  M silencio  ·  F11 pantalla completa",
                   W / 2, H - 28, 15, paleta.TEXTO_APAGADO, False, "center", 1)
    return zonas


AYUDA = [
    ("Mover", "WASD / Flechas"),
    ("Atacar (tajo)", "Espacio / J / Clic izquierdo (apunta al cursor)"),
    ("Dash (invulnerable)", "Shift / K / Clic derecho"),
    ("Beber poción", "Q"),
    ("Lanzar bomba", "E"),
    ("Pausa", "Esc / P"),
    ("Panel de verificación", "F1"),
    ("Silenciar", "M"),
]

REGLAS = [
    "Derrota a todos los enemigos del nivel para abrir el portal.",
    "Tu tajo destruye flechas y orbes enemigos: úsalo para defenderte.",
    "Tras cada nivel eliges una bendición gratuita y visitas al mercader.",
    "Los enemigos avisan antes de atacar: línea roja = disparo, brillo = embestida.",
    "En el nivel 10 espera el Guardián del Abismo. Si caes, la run empieza de cero.",
]


def ayuda(s: pygame.Surface, t: float, t_estado: float) -> Zonas:
    fondo(s, t)
    titulo(s, "CÓMO JUGAR", 80, t, tam=48, entrada=min(1.0, t_estado * 2))
    rect = pygame.Rect(140, 140, W - 280, 500)
    panel(s, rect)
    y = 175
    for accion, teclas in AYUDA:
        textos.dibujar(s, accion, rect.x + 50, y, 20, paleta.TEXTO, True)
        textos.dibujar(s, teclas, rect.x + 340, y, 20, paleta.ORO, False)
        y += 32
    y += 16
    for regla in REGLAS:
        pygame.draw.rect(s, paleta.CIAN, (rect.x + 50, y + 9, 6, 6))
        textos.dibujar(s, regla, rect.x + 68, y, 18, paleta.TEXTO_SUAVE, False)
        y += 30
    r = pygame.Rect(0, 0, 240, 48)
    r.center = (W // 2, 680)
    boton(s, r, "Volver", True, t, tam=20)
    return [(r, "volver")]


def ranking(s: pygame.Surface, t: float, t_estado: float, puntajes: list[int], resaltar: int = -1) -> Zonas:
    fondo(s, t)
    titulo(s, "RANKING", 80, t, tam=52, entrada=min(1.0, t_estado * 2))
    rect = pygame.Rect(W // 2 - 260, 140, 520, 470)
    panel(s, rect)
    if not puntajes:
        textos.dibujar(s, "Aún no hay puntajes. ¡Sé el primero!", W / 2, rect.centery, 22,
                       paleta.TEXTO_SUAVE, False, "center")
    for i, p in enumerate(puntajes):
        k = ease_out_cubic((t_estado - i * 0.05) * 4)
        y = rect.y + 40 + i * 43
        color = paleta.ORO if i == 0 else (paleta.HUESO if i < 3 else paleta.TEXTO)
        if i == resaltar:
            pygame.draw.rect(s, paleta.PANEL_CLARO, (rect.x + 20, y - 18, rect.w - 40, 38), border_radius=8)
            color = paleta.CIAN
        textos.dibujar(s, f"#{i + 1}", rect.x + 60, y, 24, color, True, "center", alfa=int(255 * k))
        textos.dibujar(s, f"{p}", rect.right - 60 + (1 - k) * 60, y, 24, color, True, "midright", alfa=int(255 * k))
    r = pygame.Rect(0, 0, 240, 48)
    r.center = (W // 2, 670)
    boton(s, r, "Volver", True, t, tam=20)
    return [(r, "volver")]


# =============================================================================
# Pausa y panel de verificación
# =============================================================================

OPCIONES_PAUSA = ["Continuar", "Reiniciar run", "Menú principal"]


def pausa(s: pygame.Surface, t: float, seleccion: int, t_estado: float, run: Run) -> Zonas:
    oscurecer(s, 190)
    titulo(s, "PAUSA", 150, t, tam=56, entrada=min(1.0, t_estado * 3))
    zonas = _botones_verticales(s, OPCIONES_PAUSA, seleccion, t, 290, t_estado)
    j = run.jugador
    linea = (f"ATQ {j.ataque}   DEF {j.defensa}   VEL {j.rapidez:.0f}   CRÍT {j.critico * 100:.0f}%   "
             f"ESQ {j.esquiva * 100:.0f}%")
    textos.dibujar(s, linea, W / 2, 520, 18, paleta.TEXTO_SUAVE, True, "center")
    if run.mejoras_elegidas:
        nombres = ", ".join(tablas.MEJORAS[m]["nombre"] for m in run.mejoras_elegidas[-5:])
        textos.dibujar(s, f"Bendiciones: {nombres}", W / 2, 550, 16, paleta.TEXTO_APAGADO, False, "center")
    textos.dibujar(s, f"Semilla de la run: {run.semilla}", W / 2, H - 30, 14, paleta.TEXTO_APAGADO, False, "center")
    return zonas


def panel_verificacion(s: pygame.Surface) -> None:
    rect = pygame.Rect(W - 430, 96, 410, 400)
    capa = pygame.Surface(rect.size, pygame.SRCALPHA)
    capa.fill((*paleta.PANEL, 225))
    s.blit(capa, rect)
    pygame.draw.rect(s, paleta.CIAN, rect, 2, border_radius=8)
    textos.dibujar(s, "VERIFICACIÓN EN VIVO  (F1)", rect.x + 16, rect.y + 12, 18, paleta.CIAN, True)
    textos.dibujar(s, "Contratos comprobados por función", rect.x + 16, rect.y + 38, 14, paleta.TEXTO_SUAVE)
    y = rect.y + 64
    for nombre in ("aplicar_dano", "puede_comprar", "comprar", "mover_jugador", "clasificar_combate",
                   "sumar_puntajes", "contar_vivos", "buscar_lineal", "ordenar_desc"):
        textos.dibujar(s, nombre, rect.x + 16, y, 15, paleta.TEXTO, False, contorno=1)
        textos.dibujar(s, f"{contratos.CONTADORES.get(nombre, 0):,}".replace(",", "."), rect.right - 16, y,
                       15, paleta.VERDE, True, "topright", 1)
        y += 21
    y += 8
    textos.dibujar(s, "Últimas comprobaciones", rect.x + 16, y, 14, paleta.TEXTO_SUAVE)
    y += 22
    for funcion, tipo, texto in list(contratos.REGISTRO)[-5:]:
        linea = f"{{{tipo}}} {funcion}: {texto}"
        if len(linea) > 52:
            linea = linea[:51] + "…"
        textos.dibujar(s, linea, rect.x + 16, y, 13, paleta.ORO if tipo == "P" else paleta.VERDE, False, contorno=1)
        y += 19


# =============================================================================
# Bendiciones (mejora gratuita) y tienda
# =============================================================================

def mejoras(s: pygame.Surface, t: float, seleccion: int, t_estado: float, opciones: list[str],
            nivel: int, curado: int) -> Zonas:
    fondo(s, t)
    titulo(s, f"NIVEL {nivel} SUPERADO", 92, t, paleta.VERDE, 52, min(1.0, t_estado * 2))
    sub = "Elige una bendición"
    if curado > 0:
        sub += f"   ·   recuperaste {curado} de vida al descansar"
    textos.dibujar(s, sub, W / 2, 150, 22, paleta.TEXTO_SUAVE, False, "center")
    zonas = []
    for i, m in enumerate(opciones):
        d = tablas.MEJORAS[m]
        k = ease_out_back((t_estado - 0.12 * i) * 2.2)
        elegida = i == seleccion
        r = pygame.Rect(0, 0, 300, 380)
        r.center = (W // 2 + (i - 1) * 340, 400 + int((1 - k) * 420) - (16 if elegida else 0))
        if k <= 0.01:
            zonas.append((r, i))
            continue
        borde = paleta.ORO if elegida else paleta.PANEL_BORDE
        panel(s, r, borde, paleta.PANEL_CLARO if elegida else paleta.PANEL)
        if elegida:
            for a in range(3):
                pygame.draw.rect(s, paleta.mezclar(paleta.ORO, paleta.PANEL, 0.3 + a * 0.25),
                                 r.inflate(6 + a * 6, 6 + a * 6), 1, border_radius=16)
        pygame.draw.circle(s, paleta.NOCHE, (r.centerx, r.y + 110), 62)
        pygame.draw.circle(s, borde, (r.centerx, r.y + 110), 62, 2)
        iconos.icono(s, d["icono"], r.centerx, r.y + 110, 64 + (6 * math.sin(t * 4) if elegida else 0))
        textos.dibujar(s, d["nombre"], r.centerx, r.y + 210, 26, paleta.ORO if elegida else paleta.TEXTO, True,
                       "center")
        textos.dibujar(s, d["desc"], r.centerx, r.y + 255, 19, paleta.TEXTO_SUAVE, False, "center")
        tecla(s, str(i + 1), r.centerx, r.bottom - 40, 18)
        zonas.append((r, i))
    textos.dibujar(s, "1 · 2 · 3  o  flechas + Enter  o  clic", W / 2, H - 30, 16, paleta.TEXTO_APAGADO,
                   False, "center")
    return zonas


def tienda(s: pygame.Surface, t: float, seleccion: int, t_estado: float, run: Run, oferta: list[str],
           vendidos: set[int], nivel_tienda: int, mensaje: str, t_mensaje: float) -> Zonas:
    fondo(s, t)
    titulo(s, "EL MERCADER ERRANTE", 80, t, paleta.ORO, 48, min(1.0, t_estado * 2))
    iconos.icono(s, "moneda", W / 2 - 40, 140, 30)
    textos.dibujar(s, f"{run.oro}", W / 2 - 18, 140, 30, paleta.ORO, True, "midleft")
    zonas: Zonas = []
    for i, objeto in enumerate(oferta):
        d = tablas.OBJETOS_TIENDA[objeto]
        precio = economia.precio(objeto, nivel_tienda)
        vendido = i in vendidos
        motivo = run.motivo_no_compra(objeto, precio)
        k = ease_out_back((t_estado - 0.08 * i) * 2.4)
        elegida = i == seleccion
        r = pygame.Rect(0, 0, 260, 300)
        r.center = (W // 2 + int((i - 1.5) * 285), 345 + int((1 - k) * 420) - (12 if elegida else 0))
        zonas.append((r, i))
        if k <= 0.01:
            continue
        borde = paleta.ORO if elegida and not vendido else paleta.PANEL_BORDE
        panel(s, r, borde, paleta.PANEL_CLARO if elegida else paleta.PANEL)
        iconos.icono(s, objeto, r.centerx, r.y + 80, 64)
        textos.dibujar(s, d["nombre"], r.centerx, r.y + 150, 23, paleta.TEXTO, True, "center")
        textos.dibujar(s, d["desc"], r.centerx, r.y + 184, 17, paleta.TEXTO_SUAVE, False, "center")
        etiqueta = "Consumible" if d["consumible"] else "Permanente"
        textos.dibujar(s, etiqueta, r.centerx, r.y + 210, 14, paleta.CIAN if d["consumible"] else paleta.MAGENTA,
                       True, "center", 1)
        if vendido:
            textos.dibujar(s, "VENDIDO", r.centerx, r.bottom - 50, 24, paleta.TEXTO_APAGADO, True, "center")
        else:
            color = paleta.ORO if not motivo else paleta.ROJO
            iconos.icono(s, "moneda", r.centerx - 30, r.bottom - 52, 22)
            textos.dibujar(s, str(precio), r.centerx - 14, r.bottom - 52, 26, color, True, "midleft")
            if motivo:
                textos.dibujar(s, motivo, r.centerx, r.bottom - 22, 14, paleta.ROJO, False, "center", 1)
            else:
                tecla(s, str(i + 1), r.centerx, r.bottom - 20, 14)

    # Inventario y estadísticas
    j = run.jugador
    y = 540
    textos.dibujar(s, "Mochila", 230, y, 18, paleta.TEXTO_SUAVE, True, "center")
    for i, objeto in enumerate(j.inventario):
        r = pygame.Rect(130 + i * 52, y + 18, 46, 46)
        pygame.draw.rect(s, paleta.PANEL_CLARO, r, border_radius=8)
        pygame.draw.rect(s, paleta.PANEL_BORDE, r, 2, border_radius=8)
        if objeto == config.POCION:
            iconos.icono(s, "pocion", r.centerx, r.centery, 26)
        elif objeto == config.BOMBA:
            iconos.icono(s, "bomba", r.centerx, r.centery, 26)
    stats = (f"VIDA {j.vida}/{j.vida_max}   ATQ {j.ataque}   DEF {j.defensa}   "
             f"CRÍT {j.critico * 100:.0f}%   VEL {j.rapidez:.0f}   ALC {j.alcance:.1f}")
    textos.dibujar(s, stats, W / 2 + 120, y + 40, 18, paleta.TEXTO, True, "center")

    r = pygame.Rect(0, 0, 330, 54)
    r.center = (W // 2, 660)
    boton(s, r, f"Descender al nivel {run.nivel + 1}", seleccion == len(oferta), t, tam=22)
    zonas.append((r, len(oferta)))
    if t_mensaje > 0 and mensaje:
        textos.dibujar(s, mensaje, W / 2, 500, 22, paleta.ROJO if "suficiente" in mensaje or "lleno" in mensaje
                       else paleta.VERDE, True, "center", alfa=int(255 * min(1.0, t_mensaje * 3)))
    textos.dibujar(s, "1-4 comprar · Enter continuar", W / 2, H - 22, 15, paleta.TEXTO_APAGADO, False, "center")
    return zonas


# =============================================================================
# Fin de la run
# =============================================================================

CONSEJOS = [
    "Consejo: el dash te hace invulnerable; úsalo para atravesar ráfagas.",
    "Consejo: un tajo bien orientado destruye flechas y orbes.",
    "Consejo: los brutos quedan aturdidos si embisten contra un muro.",
    "Consejo: guarda una bomba para cuando te rodeen.",
    "Consejo: la tienda solo alcanza para 1 o 2 objetos; elige según tu estilo.",
    "Consejo: los arqueros avisan con una línea roja antes de disparar.",
]

OPCIONES_FIN = ["Nueva run", "Menú principal"]


def _tabla_estadisticas(s, run: Run, y: int, t_estado: float) -> None:
    minutos = int(run.tiempo // 60)
    segundos = int(run.tiempo % 60)
    filas = [
        ("Nivel alcanzado", f"{run.nivel} / {config.NIVELES_MAX}"),
        ("Enemigos derrotados", str(run.enemigos_derrotados)),
        ("Oro reunido", str(run.oro_total)),
        ("Tiempo", f"{minutos}:{segundos:02d}"),
        ("Puntaje", str(run.puntaje_total())),
    ]
    for i, (k, v) in enumerate(filas):
        a = ease_out_cubic((t_estado - 0.6 - i * 0.12) * 3)
        if a <= 0:
            continue
        yy = y + i * 36
        color = paleta.ORO if k == "Puntaje" else paleta.TEXTO
        textos.dibujar(s, k, W / 2 - 200 - (1 - a) * 40, yy, 22, paleta.TEXTO_SUAVE, False, alfa=int(255 * a))
        textos.dibujar(s, v, W / 2 + 200 + (1 - a) * 40, yy, 22, color, True, "topright", alfa=int(255 * a))


def derrota(s: pygame.Surface, t: float, seleccion: int, t_estado: float, run: Run, puesto: int) -> Zonas:
    fondo(s, t)
    capa = pygame.Surface((W, H), pygame.SRCALPHA)
    capa.fill((*paleta.ROJO_OSCURO, 70))
    s.blit(capa, (0, 0))
    titulo(s, "HAS CAÍDO", 110, t, paleta.ROJO, 72, min(1.0, t_estado * 1.4))
    causa = run.causa_muerte or "la oscuridad"
    textos.dibujar(s, f"Derrotado por {causa} en el nivel {run.nivel}", W / 2, 180, 24, paleta.TEXTO, True,
                   "center", alfa=int(255 * min(1, t_estado * 2)))
    _tabla_estadisticas(s, run, 240, t_estado)
    if puesto >= 0 and t_estado > 1.4:
        textos.dibujar(s, f"¡Puesto #{puesto + 1} del ranking!", W / 2, 440, 22, paleta.ORO, True, "center")
    textos.dibujar(s, CONSEJOS[run.semilla % len(CONSEJOS)], W / 2, 480, 18, paleta.TEXTO_SUAVE, False, "center")
    zonas = _botones_verticales(s, OPCIONES_FIN, seleccion, t, 560, max(0.0, t_estado - 1.0), 300)
    textos.dibujar(s, "R: reintentar al instante", W / 2, H - 22, 15, paleta.TEXTO_APAGADO, False, "center")
    return zonas


def victoria(s: pygame.Surface, t: float, seleccion: int, t_estado: float, run: Run, puesto: int) -> Zonas:
    fondo(s, t)
    for i in range(70):  # confeti
        x = (i * 151.7 + math.sin(t * 1.3 + i) * 40) % W
        y = (t * (60 + i % 5 * 25) + i * 83) % (H + 20) - 10
        colores = (paleta.ORO, paleta.CIAN, paleta.MAGENTA, paleta.VERDE, paleta.ROJO)
        ancho = 3 + 3 * abs(math.sin(t * 5 + i))
        pygame.draw.rect(s, colores[i % 5], (int(x), int(y), int(ancho), 6))
    titulo(s, "¡LA CRIPTA HA CAÍDO!", 110, t, paleta.ORO, 64, min(1.0, t_estado * 1.2))
    textos.dibujar(s, "El Guardián del Abismo ya no custodia la oscuridad.", W / 2, 180, 22, paleta.TEXTO,
                   False, "center", alfa=int(255 * min(1, t_estado * 2)))
    _tabla_estadisticas(s, run, 240, t_estado)
    if puesto >= 0 and t_estado > 1.4:
        textos.dibujar(s, f"¡Puesto #{puesto + 1} del ranking!", W / 2, 450, 24, paleta.ORO, True, "center")
    zonas = _botones_verticales(s, OPCIONES_FIN, seleccion, t, 560, max(0.0, t_estado - 1.0), 300)
    return zonas
