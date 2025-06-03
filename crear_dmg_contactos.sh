#!/bin/bash

# Configuración
APP_NAME="contactos_mejorado"
APP_PATH="dist/${APP_NAME}.app"
DMG_NAME="Contactos_Mejorado.dmg"
VOL_NAME="Contactos Mejorado"
ICON_FILE="contactos.icns"
BACKGROUND_FILE="background.png"

echo "📦 Verificando archivos requeridos..."

# Verificar existencia de la app
if [ ! -d "$APP_PATH" ]; then
    echo "❌ No se encontró la aplicación en: $APP_PATH"
    exit 1
fi

# Verificar existencia del icono
if [ ! -f "$ICON_FILE" ]; then
    echo "⚠️ Icono personalizado '$ICON_FILE' no encontrado. Se usará el icono por defecto del sistema."
    USE_ICON=false
else
    USE_ICON=true
fi

# Verificar existencia del fondo (opcional)
if [ ! -f "$BACKGROUND_FILE" ]; then
    echo "⚠️ Imagen de fondo '$BACKGROUND_FILE' no encontrada. El dmg tendrá fondo blanco."
    USE_BG=false
else
    USE_BG=true
fi

echo "🧹 Eliminando dmg anterior si existe..."
rm -f "$DMG_NAME"

# Construcción del comando
CMD=(create-dmg --volname "$VOL_NAME")

$USE_ICON && CMD+=(--volicon "$ICON_FILE")
$USE_BG && CMD+=(--background "$BACKGROUND_FILE")

CMD+=(--window-pos 200 120)
CMD+=(--window-size 500 300)
CMD+=(--icon-size 100)
CMD+=(--icon "${APP_NAME}.app" 125 150)
CMD+=(--hide-extension "${APP_NAME}.app")
CMD+=(--app-drop-link 375 150)
CMD+=("$DMG_NAME")
CMD+=("dist/")

echo "🚀 Ejecutando creación del .dmg..."
"${CMD[@]}"

echo "✅ Proceso completado. Revisa el archivo '$DMG_NAME'"
