@echo off
rem Cripta de Hoare: crea el entorno virtual (solo la primera vez), instala pygame y abre el juego.
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" goto instalar

set "PY="
where py >nul 2>nul && set "PY=py -3"
if not defined PY (
    where python >nul 2>nul && set "PY=python"
)
if not defined PY (
    echo No se encontro Python 3. Instalalo desde https://www.python.org/downloads/
    echo y marca la casilla "Add python.exe to PATH". Luego vuelve a abrir este archivo.
    pause
    exit /b 1
)

echo Creando el entorno virtual .venv ...
%PY% -m venv .venv
if errorlevel 1 (
    echo No se pudo crear el entorno virtual.
    pause
    exit /b 1
)

:instalar
echo Instalando dependencias ...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r requirements.txt
if errorlevel 1 (
    echo No se pudieron instalar las dependencias. Revisa tu conexion a internet.
    pause
    exit /b 1
)

".venv\Scripts\python.exe" main.py
if errorlevel 1 pause
endlocal
