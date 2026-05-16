# ContactosAPP

Aplicación de escritorio para gestionar contactos, desarrollada en Python con interfaz gráfica `tkinter`.

## Características

- Añadir, editar y eliminar contactos (solo el nombre es obligatorio)
- Búsqueda en tiempo real por nombre, teléfono o email
- Indicador visual de modo **Nuevo / Editando**
- Validación de email y teléfono cuando se informan (admite formatos internacionales: `+34 612 345 678`)
- Exportación a CSV
- Importación de contactos desde Google Contacts (`.csv`) y Apple Contacts (`.vcf` / `.vcard`)
- Gestión de duplicados al importar con opción de fusionar, fusionar todo, guardar ambos u omitir
- Ampliación automática del esquema cuando el archivo importado trae campos nuevos
- Datos persistidos localmente en `contactos.json`; en la app empaquetada se guardan en `~/Library/Application Support/ContactosAPP/`
- Confirmación al cerrar si hay datos sin guardar

## Requisitos

- Python 3.6 o superior con `tkinter` incluido (instalación estándar de [python.org](https://www.python.org))
- `py2app` solo si se desea empaquetar la app para macOS

## Instalación y ejecución

```bash
git clone https://github.com/edfrutos/ContactosAPP.git
cd ContactosAPP
python contactos_mejorado.py
```

## Importar contactos

Exporta tus contactos desde Google Contacts en formato CSV o desde Apple Contacts en formato vCard. En la app, usa **Importar contactos...** y selecciona el archivo `.csv`, `.vcf` o `.vcard`.

En duplicados, los campos vacíos locales se completan siempre con el dato importado. Si hay conflicto entre valores locales e importados, puedes fusionar un contacto, fusionar todos, guardar ambos como contactos separados y elegir si prevalece el dato local o el importado.

`contactos.json` y los archivos exportados (`.csv`, `.vcf`, `.vcard`) están ignorados por Git para evitar publicar datos personales. El empaquetado no incluye datos reales dentro del `.app`.

El repositorio incluye `contactos_example.json` como referencia de estructura sin datos reales.

## Empaquetar como `.app` para macOS

```bash
# Instala la dependencia de empaquetado
pip install -r requirements.txt

# Genera la app en dist/
python setup.py py2app
```

Para un proceso completo desde cero (instala pyenv, compila Python con soporte Tkinter y genera el DMG):

```bash
bash contactos_instalacion_y_paquetizado.sh
```

## Licencia

MIT

## Autor

E. de Frutos
