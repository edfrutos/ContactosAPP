from setuptools import setup

APP = ['contactos_mejorado.py']
DATA_FILES = ['contactos.json']  # Opcional
OPTIONS = {
    'iconfile': 'contactos.icns',
    'packages': ['tkinter'],
    'includes': ['re', 'json', 'csv', 'os']
}


setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
