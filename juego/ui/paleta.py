"""Paleta única del juego: todo color de la interfaz sale de aquí."""

FONDO = (14, 10, 22)
NOCHE = (8, 6, 14)

PISO_A = (40, 33, 54)
PISO_B = (44, 37, 60)
PISO_DETALLE = (55, 47, 74)
PISO_SOMBRA = (26, 21, 37)

MURO_TOPE = (86, 72, 112)
MURO_TOPE_LUZ = (112, 96, 140)
MURO_FRENTE = (58, 47, 80)
MURO_FRENTE_OSCURO = (44, 35, 62)
MURO_RELLENO = (20, 15, 29)
MURO_ARISTA = (40, 32, 56)

TEXTO = (242, 234, 228)
TEXTO_SUAVE = (160, 148, 182)
TEXTO_APAGADO = (98, 88, 120)

ORO = (255, 205, 75)
ORO_OSCURO = (196, 132, 38)
ROJO = (236, 70, 92)
ROJO_OSCURO = (130, 30, 52)
VERDE = (98, 226, 140)
VERDE_OSCURO = (38, 120, 82)
CIAN = (90, 210, 232)
CIAN_OSCURO = (36, 104, 140)
MAGENTA = (206, 92, 222)
MAGENTA_OSCURO = (104, 40, 128)
NARANJA = (255, 142, 70)
HUESO = (226, 218, 196)
PIEL = (240, 196, 160)
BLANCO = (255, 255, 255)
NEGRO = (0, 0, 0)

PANEL = (24, 19, 36)
PANEL_CLARO = (36, 29, 52)
PANEL_BORDE = (78, 64, 108)

# Colores de cada enemigo (cuerpo, detalle)
COLOR_ENEMIGO = {
    "slime": ((98, 214, 120), (42, 110, 70)),
    "murcielago": ((150, 96, 210), (70, 40, 110)),
    "arquero": (HUESO, (120, 108, 96)),
    "bruto": ((222, 108, 70), (120, 50, 40)),
    "jefe": ((170, 60, 200), (70, 22, 90)),
}


def mezclar(a: tuple, b: tuple, t: float) -> tuple[int, int, int]:
    t = max(0.0, min(1.0, t))
    return (int(a[0] + (b[0] - a[0]) * t), int(a[1] + (b[1] - a[1]) * t), int(a[2] + (b[2] - a[2]) * t))
