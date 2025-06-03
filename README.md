# ContactosAPP

Una aplicación de gestión de contactos desarrollada en Python con interfaz gráfica.

## Descripción

ContactosAPP es una aplicación de escritorio que permite gestionar contactos de manera sencilla y eficiente. Diseñada con Python y `tkinter` (la biblioteca estándar de GUI incluida con Python) para la interfaz gráfica.

## Características

- Gestión completa de contactos (crear, editar, eliminar)
- Interfaz gráfica intuitiva
- Almacenamiento de datos en formato JSON
- Exportación de contactos a CSV

## Requisitos

- Python 3.6 o superior (incluye `tkinter` por defecto)
- `py2app` (para empaquetado en macOS)

## Instalación

1. Clona este repositorio

   ```bash
   git clone https://github.com/edfrutos/ContactosAPP.git
   cd ContactosAPP
   ```

2. Instala las dependencias

   ```bash
   pip install -r requirements.txt
   ```

3. Ejecuta la aplicación

   ```bash
   python contactos_mejorado.py
   ```

## Empaquetado

Para crear una aplicación ejecutable en macOS:

```bash
python setup.py py2app
```

## Licencia

MIT

## Autor

E. de Frutos
