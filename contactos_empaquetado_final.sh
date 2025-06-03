#!/bin/bash

echo "🚀 Iniciando proceso completo de empaquetado..."

# Ruta a Python instalado desde python.org
PYTHON311="/Library/Frameworks/Python.framework/Versions/3.11/bin/python3.11"

# Paso 1: Limpiar entorno
echo "🧹 Limpiando directorios antiguos..."
rm -rf build dist contactos_mejorado.spec

# Paso 2: Crear entorno virtual limpio
echo "🐍 Creando entorno virtual..."
$PYTHON311 -m venv .venv
source .venv/bin/activate

# Paso 3: Instalar dependencias
echo "📦 Instalando dependencias..."
pip install --upgrade pip setuptools wheel
pip install py2app Pillow

# Paso 4: Ejecutar py2app
echo "🛠️ Generando .app con py2app..."
python setup.py py2app

# Paso 5: Crear DMG elegante
echo "📦 Creando archivo .dmg..."
APP_NAME="contactos_mejorado"
DMG_NAME="ContactosApp.dmg"
create-dmg \
  --volname "Contactos App" \
  --volicon "contactos_icon.icns" \
  --window-pos 200 120 \
  --window-size 500 300 \
  --icon "$APP_NAME.app" 125 150 \
  --hide-extension "$APP_NAME.app" \
  --app-drop-link 375 150 \
  "$DMG_NAME" \
  "dist/"

# Paso final
echo "✅ Proceso finalizado. Revisa el archivo generado: dist/$DMG_NAME"
