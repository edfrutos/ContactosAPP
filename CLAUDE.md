# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Qué es este proyecto

Aplicación de escritorio para gestión de contactos, escrita en Python con `tkinter`. Los contactos se persisten en `contactos.json` (formato JSON plano). No hay servidor ni base de datos.

## Ejecutar la aplicación

```bash
python contactos_mejorado.py   # versión principal (ttk + validación + CSV)
```

Requiere Python 3.6+ con `tkinter` disponible (incluido en instalaciones estándar de Python.org). No hay dependencias de terceros para ejecutar la app; `py2app` solo se necesita para empaquetar.

## Instalar dependencias de empaquetado

```bash
pip install -r requirements.txt   # instala py2app
```

## Empaquetar como .app para macOS

```bash
# Opción simple (requiere entorno virtual activo con py2app)
python setup.py py2app

# Opción completa con DMG (instala todo desde cero vía Homebrew/pyenv)
bash contactos_instalacion_y_paquetizado.sh

# Opción rápida (asume dependencias ya instaladas)
bash contactos_empaquetado_final.sh
```

El script `contactos_instalacion_y_paquetizado.sh` es el más robusto: instala pyenv, compila Python 3.11.9 con soporte `--enable-framework` (necesario para `py2app` en Apple Silicon), crea el `.app` y genera el `.dmg` con `create-dmg`.

## Arquitectura

El proyecto mantiene una única variante activa:

| Archivo | Tipo | Estado |
|---|---|---|
| `contactos_mejorado.py` | GUI completa (`ttk`) | **Versión activa** |

**`contactos_mejorado.py`** es el único archivo relevante para desarrollo. Contiene la clase `ContactosApp`, con persistencia, validación, lógica CRUD y construcción de UI en el mismo módulo. El estado de la aplicación vive en `self.contactos` y en los widgets de Tkinter asociados a la instancia.

Flujo de datos: `contactos.json` → `ContactosApp._cargar()` → `self.contactos` → `ContactosApp._guardar()` → `contactos.json`.

La importación de contactos soporta Google Contacts en CSV y Apple Contacts en vCard (`.vcf` / `.vcard`). Los duplicados se detectan por email o teléfono normalizados. Los campos vacíos locales se completan automáticamente y, si hay conflictos, la UI permite fusionar un contacto, fusionar todos, guardar ambos o elegir si prevalece el dato local o el importado. Si el archivo importado trae campos nuevos, se añaden al esquema JSON de todos los contactos, se muestran como columnas ordenables y se pueden editar desde el formulario. El listado tiene desplazamiento horizontal para columnas adicionales y el buscador incluye una acción para limpiar el filtro.

## Datos

En desarrollo, `contactos.json` se lee y escribe junto al script mediante una ruta absoluta basada en `__file__`, independiente del directorio de trabajo. En la app empaquetada con `py2app`, se guarda en `~/Library/Application Support/ContactosAPP/contactos.json` para no escribir dentro del `.app`. Cada contacto tiene tres campos: `nombre`, `teléfono`, `email`; solo `nombre` es obligatorio. Este archivo contiene datos personales y debe permanecer ignorado por Git.

## Sin tests

El proyecto no tiene suite de tests. No hay `pytest` ni ningún framework de testing configurado.
