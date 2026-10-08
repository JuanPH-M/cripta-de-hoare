#!/usr/bin/env sh
# Cripta de Hoare: crea el entorno virtual (solo la primera vez), instala pygame y abre el juego.
set -e
cd "$(dirname "$0")"

if [ ! -x ".venv/bin/python" ]; then
    if command -v python3 >/dev/null 2>&1; then
        PY=python3
    elif command -v python >/dev/null 2>&1; then
        PY=python
    else
        echo "No se encontró Python 3. Instálalo (por ejemplo: sudo apt install python3 python3-venv)."
        exit 1
    fi
    echo "Creando el entorno virtual .venv ..."
    "$PY" -m venv .venv
fi

echo "Instalando dependencias ..."
.venv/bin/python -m pip install --disable-pip-version-check -q -r requirements.txt

exec .venv/bin/python main.py
