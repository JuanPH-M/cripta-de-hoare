"""Ranking de puntajes guardado en ranking.json (junto a main.py, sin importar el directorio de trabajo)."""

import json
import math
import sys
from pathlib import Path

from juego.verificacion.funciones import buscar_lineal, ordenar_desc


def _carpeta_del_juego() -> Path:
    # En el .exe de PyInstaller __file__ apunta a una carpeta temporal que se borra al cerrar:
    # el ranking se guarda junto al ejecutable para que no se pierda entre partidas.
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[2]


RUTA_RANKING = _carpeta_del_juego() / "ranking.json"
MAX_RANKING = 10


def cargar_ranking(ruta: Path | None = None) -> list[int]:
    ruta = ruta or RUTA_RANKING  # se resuelve al llamar (permite redirigirla en pruebas)
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    if not isinstance(datos, list):
        return []
    # isfinite descarta valores como 1e999 (inf), que int() no puede convertir.
    ranking = [int(x) for x in datos
               if isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x) and x >= 0]
    ordenar_desc(ranking, len(ranking))
    return ranking[:MAX_RANKING]


def guardar_ranking(ranking: list[int], ruta: Path | None = None) -> None:
    ruta = ruta or RUTA_RANKING
    try:
        ruta.write_text(json.dumps(ranking[:MAX_RANKING]), encoding="utf-8")
    except OSError:
        pass  # sin permisos de escritura: el juego sigue funcionando


def insertar_puntaje(ranking: list[int], puntaje: int) -> int:
    """
    Inserta `puntaje`, reordena (ordenar_desc) y recorta al top 10.
    Devuelve la posición (0..9) del nuevo puntaje o -1 si no entró al ranking.

    ordenar_desc es estable (solo desplaza elementos estrictamente menores), así
    que el puntaje nuevo queda después de los iguales que ya estaban: su posición
    es la primera aparición (buscar_lineal) más la cantidad de iguales previos.
    """
    iguales_previos = sum(1 for x in ranking if x == puntaje)
    ranking.append(puntaje)
    ordenar_desc(ranking, len(ranking))
    posicion = buscar_lineal(ranking, len(ranking), puntaje) + iguales_previos
    del ranking[MAX_RANKING:]
    return posicion if posicion < MAX_RANKING else -1
