"""
Infraestructura de contratos: precondiciones {P}, postcondiciones {Q} e invariantes {I}.

Cada verificación se registra para poder mostrarla en el panel de verificación
del juego (tecla F1). No depende de pygame.
"""

from collections import deque

# Si es False, las comprobaciones se omiten (útil para medir rendimiento).
CONTRATOS_ACTIVOS: bool = True


class ContratoError(AssertionError):
    """Se lanza cuando se viola {P}, {Q} o un invariante {I}."""


# Últimas verificaciones (función, tipo, texto) para el panel en vivo.
REGISTRO: deque = deque(maxlen=12)
# Contador de verificaciones superadas por función.
CONTADORES: dict[str, int] = {}


def _anotar(funcion: str, tipo: str, texto: str) -> None:
    CONTADORES[funcion] = CONTADORES.get(funcion, 0) + 1
    if not REGISTRO or REGISTRO[-1][:2] != (funcion, tipo):
        REGISTRO.append((funcion, tipo, texto))


def requiere(condicion: bool, texto: str, funcion: str) -> None:
    """Comprueba la precondición {P}. Lanza ContratoError si es falsa."""
    if not CONTRATOS_ACTIVOS:
        return
    if not condicion:
        raise ContratoError(f"{{P}} violada en {funcion}: {texto}")
    _anotar(funcion, "P", texto)


def asegura(condicion: bool, texto: str, funcion: str) -> None:
    """Comprueba la postcondición {Q}. Lanza ContratoError si es falsa."""
    if not CONTRATOS_ACTIVOS:
        return
    if not condicion:
        raise ContratoError(f"{{Q}} violada en {funcion}: {texto}")
    _anotar(funcion, "Q", texto)


def invariante(condicion: bool, texto: str, funcion: str) -> None:
    """Comprueba un invariante de ciclo {I}. Lanza ContratoError si es falso."""
    if CONTRATOS_ACTIVOS and not condicion:
        raise ContratoError(f"{{I}} violado en {funcion}: {texto}")
