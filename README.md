# ContactosAPP

Aplicación de escritorio para gestionar contactos, desarrollada en Python con interfaz gráfica `tkinter`.

## Características

- Añadir, editar y eliminar contactos (nombre, teléfono, email)
- Búsqueda en tiempo real por nombre, teléfono o email
- Indicador visual de modo **Nuevo / Editando**
- Validación de email y teléfono (admite formatos internacionales: `+34 612 345 678`)
- Exportación a CSV
- Datos persistidos en `contactos.json` junto al ejecutable
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
