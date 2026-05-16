from setuptools import setup

APP = ['contactos_mejorado.py']
DATA_FILES = []
OPTIONS = {
    'iconfile': 'contactos_icon.icns',
    'packages': ['tkinter'],
    'includes': ['re', 'json', 'csv', 'os', 'sys', 'unicodedata']
}


setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
)
