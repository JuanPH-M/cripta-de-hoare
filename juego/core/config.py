"""Constantes globales: resolución, cuadrícula y parámetros de la partida."""

TITULO = "Cripta de Hoare"

# Ventana real y lienzo de baja resolución (pixel art escalado x2).
ESCALA = 2
ANCHO_LIENZO = 640
ALTO_LIENZO = 360
ANCHO_VENTANA = ANCHO_LIENZO * ESCALA
ALTO_VENTANA = ALTO_LIENZO * ESCALA
FPS = 60

# Cuadrícula del mapa (en píxeles de lienzo).
TAM = 16
COLUMNAS = 40
FILAS = 20
ANCHO_MAPA = COLUMNAS * TAM          # 640
ALTO_MAPA = FILAS * TAM              # 320
ALTO_HUD = ALTO_LIENZO - ALTO_MAPA   # 40: franja superior del HUD
MAPA_Y = ALTO_HUD                    # el mapa se dibuja debajo del HUD

# Códigos de casilla.
PISO = 0
MURO = 1

# Estructura de la run.
NIVELES_MAX = 10
NIVEL_JEFE = 10

# Inventario de consumibles.
TAM_INVENTARIO = 4
VACIO = 0
POCION = 1
BOMBA = 2
