"""
Audio sintetizado en memoria (no hay archivos de sonido): efectos y dos pistas
de música en bucle. Si no hay dispositivo de audio, el juego sigue en silencio.
"""

import array
import math
import random
import threading

import pygame

FRECUENCIA = 22050


def _nota(n: str) -> float:
    """'A3' -> Hz."""
    nombres = {"C": -9, "D": -7, "E": -5, "F": -4, "G": -2, "A": 0, "B": 2}
    semitono = nombres[n[0]]
    resto = n[1:]
    if resto.startswith("#"):
        semitono += 1
        resto = resto[1:]
    elif resto.startswith("b"):
        semitono -= 1
        resto = resto[1:]
    octava = int(resto)
    return 440.0 * 2 ** ((semitono + (octava - 4) * 12) / 12)


def _onda(forma: str, fase: float, rng: random.Random) -> float:
    if forma == "seno":
        return math.sin(fase)
    if forma == "cuadrada":
        return 0.6 if math.sin(fase) >= 0 else -0.6
    if forma == "triangulo":
        x = (fase / math.tau) % 1.0
        return 4 * x - 1 if x < 0.5 else 3 - 4 * x
    if forma == "sierra":
        return ((fase / math.tau) % 1.0) * 2 - 1
    return rng.uniform(-1, 1)  # ruido


def _tono(f0: float, f1: float, dur: float, forma: str = "seno", vol: float = 0.5,
          caida: float = 6.0, ataque: float = 0.004, semilla: int = 1) -> list[float]:
    rng = random.Random(semilla)
    n = int(FRECUENCIA * dur)
    datos = [0.0] * n
    fase = 0.0
    for i in range(n):
        t = i / FRECUENCIA
        p = i / n
        f = f0 + (f1 - f0) * p
        fase += math.tau * f / FRECUENCIA
        env = min(1.0, t / ataque) * math.exp(-caida * p)
        datos[i] = _onda(forma, fase, rng) * vol * env
    return datos


def _mezclar(*pistas: list[float], desfases: tuple[float, ...] | None = None) -> list[float]:
    desfases = desfases or tuple(0.0 for _ in pistas)
    largo = max(int(d * FRECUENCIA) + len(p) for p, d in zip(pistas, desfases))
    salida = [0.0] * largo
    for pista, d in zip(pistas, desfases):
        o = int(d * FRECUENCIA)
        for i, v in enumerate(pista):
            salida[o + i] += v
    return salida


def _secuencia(notas: list[tuple[str, float]], forma: str, vol: float, caida: float = 4.0) -> list[float]:
    salida: list[float] = []
    for nombre, dur in notas:
        f = _nota(nombre)
        salida += _tono(f, f, dur, forma, vol, caida)
    return salida


class Audio:
    def __init__(self) -> None:
        self.activo = False
        self.silencio = False
        self.sonidos: dict[str, pygame.mixer.Sound] = {}
        self.musicas: dict[str, pygame.mixer.Sound] = {}
        self.pista_actual = ""
        self._pendiente = ""
        self.canal_musica = None
        self.canales = 1
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(FRECUENCIA, -16, 1, 512)
            self.canales = pygame.mixer.get_init()[2]
            pygame.mixer.set_num_channels(24)
            self.canal_musica = pygame.mixer.Channel(0)
            pygame.mixer.set_reserved(1)
            self._crear_efectos()
            self.activo = True
            threading.Thread(target=self._crear_musica, daemon=True).start()
        except (pygame.error, OSError):
            self.activo = False

    # ------------------------------------------------------------ síntesis
    def _sonido(self, datos: list[float], volumen: float = 1.0) -> pygame.mixer.Sound:
        buf = array.array("h")
        for v in datos:
            m = int(max(-1.0, min(1.0, v * volumen)) * 32000)
            for _ in range(self.canales):
                buf.append(m)
        return pygame.mixer.Sound(buffer=buf.tobytes())

    def _crear_efectos(self) -> None:
        s = self.sonidos
        s["tajo"] = self._sonido(_mezclar(_tono(1400, 300, 0.09, "ruido", 0.35, 5),
                                          _tono(900, 380, 0.08, "triangulo", 0.18, 5)))
        s["golpe"] = self._sonido(_mezclar(_tono(190, 55, 0.13, "seno", 0.8, 5),
                                           _tono(0, 0, 0.05, "ruido", 0.35, 8)))
        s["critico"] = self._sonido(_mezclar(_tono(210, 50, 0.18, "seno", 0.9, 4),
                                             _tono(0, 0, 0.07, "ruido", 0.4, 6),
                                             _tono(1320, 1760, 0.12, "cuadrada", 0.18, 5)))
        s["bloqueo"] = self._sonido(_tono(1800, 1500, 0.1, "triangulo", 0.3, 7))
        s["herido"] = self._sonido(_mezclar(_tono(320, 110, 0.22, "cuadrada", 0.35, 4),
                                            _tono(0, 0, 0.08, "ruido", 0.3, 6)))
        s["moneda"] = self._sonido(_tono(988, 988, 0.05, "cuadrada", 0.18, 2)
                                   + _tono(1319, 1319, 0.1, "cuadrada", 0.18, 5))
        s["dash"] = self._sonido(_tono(300, 1200, 0.15, "ruido", 0.22, 4))
        s["pocion"] = self._sonido(_secuencia([("C5", .06), ("E5", .06), ("G5", .06), ("C6", .14)], "seno", 0.35))
        s["bomba"] = self._sonido(_mezclar(_tono(0, 0, 0.55, "ruido", 0.6, 5),
                                           _tono(95, 28, 0.5, "seno", 0.9, 3)))
        s["flecha"] = self._sonido(_tono(520, 880, 0.06, "triangulo", 0.2, 5))
        s["parada"] = self._sonido(_tono(2100, 1700, 0.09, "triangulo", 0.25, 6))
        s["muerte"] = self._sonido(_mezclar(_tono(420, 70, 0.22, "cuadrada", 0.3, 3),
                                            _tono(0, 0, 0.12, "ruido", 0.3, 5)))
        s["portal"] = self._sonido(_mezclar(_tono(440, 880, 0.7, "seno", 0.25, 2),
                                            _tono(660, 1320, 0.7, "seno", 0.15, 2),
                                            _tono(990, 1980, 0.5, "triangulo", 0.08, 3),
                                            desfases=(0, 0.05, 0.1)))
        s["alerta"] = self._sonido(_tono(760, 900, 0.07, "cuadrada", 0.12, 4))
        s["ui_mover"] = self._sonido(_tono(660, 660, 0.04, "triangulo", 0.25, 6))
        s["ui_ok"] = self._sonido(_tono(880, 1320, 0.09, "cuadrada", 0.18, 4))
        s["ui_error"] = self._sonido(_tono(150, 120, 0.16, "cuadrada", 0.25, 3))
        s["compra"] = self._sonido(_mezclar(_tono(1319, 1319, 0.06, "cuadrada", 0.15, 3),
                                            _tono(1760, 1760, 0.12, "cuadrada", 0.15, 4),
                                            desfases=(0, 0.06)))
        s["impacto"] = self._sonido(_mezclar(_tono(120, 40, 0.25, "seno", 0.9, 4),
                                             _tono(0, 0, 0.1, "ruido", 0.3, 6)))
        s["rugido"] = self._sonido(_mezclar(_tono(90, 45, 1.0, "sierra", 0.35, 2),
                                            _tono(0, 0, 0.9, "ruido", 0.25, 3),
                                            _tono(60, 40, 1.0, "seno", 0.5, 2)))
        s["latido"] = self._sonido(_mezclar(_tono(70, 50, 0.12, "seno", 0.7, 5),
                                            _tono(65, 45, 0.12, "seno", 0.5, 5), desfases=(0, 0.18)))
        s["victoria"] = self._sonido(_secuencia(
            [("C5", .12), ("E5", .12), ("G5", .12), ("C6", .24), ("G5", .12), ("C6", .5)], "cuadrada", 0.2, 2.5))
        s["derrota"] = self._sonido(_secuencia(
            [("A4", .22), ("F4", .22), ("D4", .22), ("A3", .7)], "triangulo", 0.35, 2.5))
        s["nivel"] = self._sonido(_secuencia([("E5", .08), ("A5", .08), ("C6", .08), ("E6", .3)], "cuadrada", 0.16))

    def _crear_musica(self) -> None:
        self.musicas["exploracion"] = self._sonido(self._pista(
            110, [("A2", ["A3", "C4", "E4", "C4"]), ("F2", ["F3", "A3", "C4", "A3"]),
                  ("C3", ["C4", "E4", "G4", "E4"]), ("G2", ["G3", "B3", "D4", "B3"])]), 0.55)
        self.musicas["jefe"] = self._sonido(self._pista(
            140, [("A2", ["A3", "C4", "E4", "A4"]), ("Bb2", ["Bb3", "D4", "F4", "D4"]),
                  ("A2", ["A3", "C4", "E4", "C4"]), ("E2", ["E3", "G#3", "B3", "E4"])], intenso=True), 0.6)

    def _pista(self, bpm: int, acordes: list[tuple[str, list[str]]], intenso: bool = False) -> list[float]:
        negra = 60.0 / bpm
        corchea = negra / 2
        compas = negra * 4
        total = int(FRECUENCIA * compas * len(acordes))
        salida = [0.0] * total
        rng = random.Random(7)
        for c, (bajo, arpegio) in enumerate(acordes):
            inicio = c * compas
            # Bajo: dos notas largas por compás
            for k in range(2):
                datos = _tono(_nota(bajo), _nota(bajo), negra * 2, "triangulo", 0.32, 1.5, 0.01)
                o = int((inicio + k * negra * 2) * FRECUENCIA)
                for i, v in enumerate(datos):
                    if o + i < total:
                        salida[o + i] += v
            # Arpegio en corcheas
            for k in range(8):
                f = _nota(arpegio[k % len(arpegio)])
                datos = _tono(f, f, corchea * 0.95, "cuadrada" if intenso else "triangulo", 0.075, 3.5, 0.005)
                o = int((inicio + k * corchea) * FRECUENCIA)
                for i, v in enumerate(datos):
                    if o + i < total:
                        salida[o + i] += v
            # Percusión suave
            for k in range(8 if intenso else 4):
                paso = corchea if intenso else negra
                datos = _tono(0, 0, 0.03, "ruido", 0.05 if k % 2 else 0.08, 8, 0.001, rng.randint(1, 999))
                o = int((inicio + k * paso + (0 if intenso else corchea)) * FRECUENCIA)
                for i, v in enumerate(datos):
                    if o + i < total:
                        salida[o + i] += v
        return salida

    # ------------------------------------------------------------ control
    def reproducir(self, nombre: str, volumen: float = 1.0) -> None:
        if not self.activo or self.silencio:
            return
        sonido = self.sonidos.get(nombre)
        if sonido is not None:
            canal = sonido.play()
            if canal is not None:
                canal.set_volume(volumen)

    def musica(self, pista: str) -> None:
        """Cambia de pista; si aún se está sintetizando, empieza en cuanto esté lista."""
        if not self.activo or pista == self.pista_actual:
            return
        self.pista_actual = pista
        self.canal_musica.fadeout(400)
        self._pendiente = pista

    def actualizar(self) -> None:
        pista = self._pendiente
        if not self.activo or not pista or pista not in self.musicas:
            return
        self._pendiente = ""
        if not self.silencio and pista == self.pista_actual:
            self.canal_musica.play(self.musicas[pista], loops=-1, fade_ms=900)
            self.canal_musica.set_volume(0.45)

    def alternar_silencio(self) -> bool:
        self.silencio = not self.silencio
        if self.activo:
            if self.silencio:
                self.canal_musica.stop()
            elif self.pista_actual:
                self._pendiente = self.pista_actual
        return self.silencio
