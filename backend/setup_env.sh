#!/bin/bash

echo "Creando entorno virtual..."

# Eliminar el entorno virtual existente si existe
if [ -d "venv" ]; then
    echo "Eliminando entorno virtual existente..."
    rm -rf venv
fi

# Crear un nuevo entorno virtual
echo "Creando nuevo entorno virtual..."
python3 -m venv venv

# Activar el entorno virtual e instalar dependencias
echo "Activando entorno virtual e instalando dependencias..."
source venv/bin/activate

# Instalar paquetes desde requirements.txt
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "Entorno virtual creado exitosamente!"
echo "Para activarlo en el futuro, ejecuta: source venv/bin/activate"
echo ""