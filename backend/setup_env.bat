@echo off
echo Creando entorno virtual...

REM Eliminar el entorno virtual existente si existe
if exist venv (
    echo Eliminando entorno virtual existente...
    rmdir /s /q venv
)

REM Crear un nuevo entorno virtual
echo Creando nuevo entorno virtual...
python -m venv venv

REM Activar el entorno virtual e instalar dependencias
echo Activando entorno virtual e instalando dependencias...
call venv\Scripts\activate.bat

REM Instalar paquetes desde requirements.txt
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Entorno virtual creado exitosamente!
echo Para activarlo en el futuro, ejecuta: venv\Scripts\activate
echo.
pause