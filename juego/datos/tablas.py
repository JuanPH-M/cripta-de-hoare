"""
Tablas de diseño del juego: enemigos, curva de dificultad, tienda y mejoras.
Son datos puros: cualquier ajuste de balance se hace aquí.
"""

from juego.core import config

# -----------------------------------------------------------------------------
# JUGADOR
# -----------------------------------------------------------------------------
JUGADOR_BASE = {
    "vida_max": 30,
    "ataque": 4,
    "defensa": 0,
    "rapidez": 84.0,        # px de lienzo por segundo
    "critico": 0.05,        # probabilidad de golpe crítico (x2)
    "esquiva": 0.0,         # probabilidad de esquivar un golpe recibido
    "enfriamiento_ataque": 0.34,
    "alcance": 21.0,        # radio del tajo
    "enfriamiento_dash": 0.9,
    "robo_vida": 0,         # vida recuperada por enemigo derrotado
}
RADIO_JUGADOR = 4.5         # hurtbox más pequeña que el sprite: golpes justos
INVULNERABLE_TRAS_GOLPE = 0.85
DURACION_DASH = 0.17
RAPIDEZ_DASH = 270.0
ARCO_TAJO_GRADOS = 120.0
CURA_ENTRE_NIVELES = 0.15   # fracción de la vida máxima recuperada al cruzar el portal

# -----------------------------------------------------------------------------
# ENEMIGOS (valores del nivel 1; ver escalar_enemigo en sistemas/progresion.py)
# -----------------------------------------------------------------------------
ENEMIGOS = {
    "slime": {"nombre": "Slime", "vida": 8, "ataque": 3, "defensa": 0, "rapidez": 34.0,
              "radio": 5.0, "oro": 2, "puntos": 10, "esquiva": 0.0},
    "murcielago": {"nombre": "Murciélago", "vida": 5, "ataque": 3, "defensa": 0, "rapidez": 60.0,
                   "radio": 4.0, "oro": 2, "puntos": 15, "esquiva": 0.15},
    "arquero": {"nombre": "Esqueleto arquero", "vida": 9, "ataque": 4, "defensa": 0, "rapidez": 30.0,
                "radio": 5.0, "oro": 3, "puntos": 20, "esquiva": 0.0},
    "bruto": {"nombre": "Bruto acorazado", "vida": 24, "ataque": 6, "defensa": 1, "rapidez": 24.0,
              "radio": 7.0, "oro": 5, "puntos": 40, "esquiva": 0.0},
    "jefe": {"nombre": "Guardián del Abismo", "vida": 420, "ataque": 7, "defensa": 1, "rapidez": 30.0,
             "radio": 13.0, "oro": 0, "puntos": 600, "esquiva": 0.0},
}

# -----------------------------------------------------------------------------
# CURVA DE DIFICULTAD (índice = nivel - 1)
#   enemigos: cantidad de enemigos del nivel
#   mezcla:   pesos de aparición por tipo
#   monedas:  monedas sueltas en el suelo (1 de oro cada una)
# -----------------------------------------------------------------------------
CURVA = [
    {"enemigos": 5,  "monedas": 8,  "mezcla": {"slime": 1.0}},
    {"enemigos": 6,  "monedas": 8,  "mezcla": {"slime": 0.6, "murcielago": 0.4}},
    {"enemigos": 8,  "monedas": 8,  "mezcla": {"slime": 0.4, "murcielago": 0.3, "arquero": 0.3}},
    {"enemigos": 9,  "monedas": 8,  "mezcla": {"slime": 0.3, "murcielago": 0.3, "arquero": 0.4}},
    {"enemigos": 9,  "monedas": 9,  "mezcla": {"slime": 0.3, "murcielago": 0.25, "arquero": 0.3, "bruto": 0.15}},
    {"enemigos": 10, "monedas": 9,  "mezcla": {"slime": 0.25, "murcielago": 0.25, "arquero": 0.3, "bruto": 0.2}},
    {"enemigos": 10, "monedas": 10, "mezcla": {"slime": 0.2, "murcielago": 0.3, "arquero": 0.3, "bruto": 0.2}},
    {"enemigos": 12, "monedas": 10, "mezcla": {"slime": 0.2, "murcielago": 0.25, "arquero": 0.3, "bruto": 0.25}},
    {"enemigos": 13, "monedas": 10, "mezcla": {"slime": 0.15, "murcielago": 0.25, "arquero": 0.3, "bruto": 0.3}},
    {"enemigos": 0,  "monedas": 0,  "mezcla": {}},  # nivel 10: arena del jefe
]
assert len(CURVA) == config.NIVELES_MAX

CRECIMIENTO_VIDA = 0.20     # +20 % de vida enemiga por nivel
NIVELES_POR_ATAQUE = 2      # +1 de ataque enemigo cada 2 niveles
NIVELES_POR_ORO = 3         # +1 de oro por enemigo cada 3 niveles
VALOR_MONEDA = 1

# -----------------------------------------------------------------------------
# TIENDA: precio(nivel) = base + incremento * (nivel - 1)
# -----------------------------------------------------------------------------
OBJETOS_TIENDA = {
    "pocion":   {"nombre": "Poción", "desc": "Cura 40% de la vida", "base": 8, "inc": 3,
                 "consumible": True},
    "bomba":    {"nombre": "Bomba", "desc": "Daña a todo lo cercano", "base": 10, "inc": 3,
                 "consumible": True},
    "espada":   {"nombre": "Filo templado", "desc": "+1 ataque", "base": 14, "inc": 4,
                 "consumible": False},
    "armadura": {"nombre": "Cota de malla", "desc": "+1 defensa", "base": 16, "inc": 4,
                 "consumible": False},
    "amuleto":  {"nombre": "Amuleto vital", "desc": "+6 vida máxima", "base": 12, "inc": 4,
                 "consumible": False},
    "botas":    {"nombre": "Botas ligeras", "desc": "+8% velocidad", "base": 12, "inc": 3,
                 "consumible": False},
    "talisman": {"nombre": "Talismán", "desc": "+7% crítico", "base": 14, "inc": 4,
                 "consumible": False},
}
CONSUMIBLE_A_ID = {"pocion": config.POCION, "bomba": config.BOMBA}
PERMANENTES = ["espada", "armadura", "amuleto", "botas", "talisman"]
CURA_POCION = 0.40
DANO_BOMBA = 14
RADIO_BOMBA = 46.0

# -----------------------------------------------------------------------------
# MEJORAS GRATUITAS ENTRE NIVELES (se elige 1 de 3)
# -----------------------------------------------------------------------------
MEJORAS = {
    "filo":      {"nombre": "Filo rúnico", "desc": "+2 de ataque", "icono": "espada"},
    "corazon":   {"nombre": "Corazón de roble", "desc": "+8 vida máx. y cura 8", "icono": "corazon"},
    "viento":    {"nombre": "Botas de viento", "desc": "+12% velocidad", "icono": "botas"},
    "halcon":    {"nombre": "Ojo de halcón", "desc": "+10% crítico", "icono": "ojo"},
    "sombra":    {"nombre": "Paso sombrío", "desc": "Dash 30% más frecuente", "icono": "dash"},
    "sangre":    {"nombre": "Sed de sangre", "desc": "+1 vida por enemigo derrotado", "icono": "gota"},
    "piedra":    {"nombre": "Piel de piedra", "desc": "+1 defensa", "icono": "escudo"},
    "furia":     {"nombre": "Furia", "desc": "Ataques 18% más rápidos", "icono": "rayo"},
    "amplia":    {"nombre": "Hoja amplia", "desc": "+20% alcance del tajo", "icono": "arco"},
    "reflejos":  {"nombre": "Reflejos", "desc": "+8% esquiva", "icono": "pluma"},
}

# -----------------------------------------------------------------------------
# PUNTUACIÓN
# -----------------------------------------------------------------------------
PUNTOS_POR_ORO = 2
PUNTOS_POR_NIVEL = 60       # x número de nivel superado
PUNTOS_VICTORIA = 1000
