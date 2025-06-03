#!/bin/bash

# Script completo para instalación limpia, creación de entorno virtual,
# compilación con py2app y empaquetado DMG (Apple Silicon - ARM64)

set -e

echo "🔄 Paso 1: Verificando Homebrew..."
if ! command -v brew &> /dev/null; then
  echo "❌ Homebrew no está instalado. Cancela el script e instálalo primero desde https://brew.sh"
  exit 1
fi
echo "✅ Homebrew disponible."

echo "🔧 Paso 2: Instalando dependencias del sistema..."
brew install tcl-tk pyenv pyenv-virtualenv create-dmg gettext

echo "🧠 Paso 3: Configurando compilación para ARM64..."
export PATH="$HOME/.pyenv/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

echo "🐍 Paso 4: Instalando Python 3.11.9 con soporte Tkinter y gettext..."
pyenv uninstall -f 3.11.9 || true
env \
  PYTHON_CONFIGURE_OPTS="--enable-framework --with-gettext=$(brew --prefix gettext)" \
  LDFLAGS="-L$(brew --prefix gettext)/lib -L$(brew --prefix tcl-tk)/lib" \
  CPPFLAGS="-I$(brew --prefix gettext)/include -I$(brew --prefix tcl-tk)/include" \
  PKG_CONFIG_PATH="$(brew --prefix gettext)/lib/pkgconfig:$(brew --prefix tcl-tk)/lib/pkgconfig" \
  pyenv install 3.11.9

echo "📦 Paso 5: Creando entorno virtual 'contactos311env'..."
pyenv virtualenv 3.11.9 contactos311env
pyenv activate contactos311env

echo "📚 Paso 6: Instalando dependencias del proyecto..."
pip install --upgrade pip setuptools wheel
pip install py2app jaraco.text

echo "🧹 Paso 7: Limpiando el directorio de trabajo..."
rm -rf build dist
find . -name "__pycache__" -type d -exec rm -r {} + 2>/dev/null
find . -name "*.pyc" -type f -delete 2>/dev/null
find . -name "*.pyo" -type f -delete 2>/dev/null
find . -name ".DS_Store" -type f -delete 2>/dev/null
find . -name "*.log" -type f -delete 2>/dev/null
find . -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null
find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null

echo "⚙️ Paso 8: Compilando app con py2app..."
python3 setup.py py2app

echo "💿 Paso 9: Creando .dmg elegante..."
create-dmg \
  --volname "ContactosApp" \
  --window-pos 200 120 \
  --window-size 500 300 \
  --icon-size 100 \
  --icon "contactos_mejorado.app" 100 100 \
  --hide-extension "contactos_mejorado.app" \
  --app-drop-link 380 100 \
  "ContactosApp.dmg" \
  "dist/"

echo "🎉 Listo. La aplicación se encuentra empaquetada en dist/ y el DMG creado como ContactosApp.dmg"
