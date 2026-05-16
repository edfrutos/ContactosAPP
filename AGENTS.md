# Repository Guidelines

## Project Structure & Module Organization

This repository contains a small macOS desktop contacts app written in Python with Tkinter.

- `contactos_mejorado.py`: active application entry point and main development target.
- `contactos.json`: local JSON data file used by the app.
- `setup.py`: `py2app` configuration for building a macOS `.app`.
- `requirements.txt`: packaging dependency list; currently only `py2app`.
- `contactos_instalacion_y_paquetizado.sh`, `contactos_empaquetado_final.sh`, `crear_dmg_contactos.sh`: macOS packaging and DMG scripts.
- `contactos_icon.icns`, `contactos.iconset/`, `background.png`: app and DMG assets.
- `build/` and `dist/`: generated packaging output; do not edit manually.

## Build, Test, and Development Commands

Run the app locally:

```bash
python contactos_mejorado.py
```

Install packaging dependencies:

```bash
pip install -r requirements.txt
```

Build a macOS app bundle:

```bash
python setup.py py2app
```

Run the full packaging flow, including DMG generation:

```bash
bash contactos_instalacion_y_paquetizado.sh
```

Use the packaging scripts only on macOS with Tkinter support available.

## Coding Style & Naming Conventions

Use Python 3.6+ compatible code. Keep the current single-file Tkinter structure unless a refactor is explicitly needed. Follow existing conventions:

- Four-space indentation.
- `snake_case` for functions, methods, and variables.
- `PascalCase` for classes, such as `ContactosApp`.
- Uppercase constants, such as `CONTACTOS_FILE` and `COLORS`.
- Private UI/helper methods prefixed with `_`.

Prefer standard-library modules already used in the project (`tkinter`, `json`, `csv`, `os`, `re`). Keep UI text consistent with the existing Spanish interface.

## Testing Guidelines

There is no automated test suite configured. Before submitting changes, manually verify:

- Adding, editing, deleting, and searching contacts.
- JSON persistence in `contactos.json`.
- Email and phone validation.
- CSV export.
- Closing behavior with unsaved form data.

If tests are added later, place them under `tests/` and use descriptive names like `test_contact_validation.py`.

## Commit & Pull Request Guidelines

Recent commit history uses short Spanish imperative messages, for example `Corregir formato en README.md`. Keep commits focused and descriptive.

Pull requests should include:

- A concise summary of the change.
- Manual verification steps performed.
- Screenshots or short recordings for visible UI changes.
- Notes about packaging impact when touching `setup.py`, icons, or shell scripts.

## Security & Configuration Tips

Do not commit personal contact data. Treat `contactos.json` as sample/local data unless intentionally updating fixtures. Avoid destructive packaging script changes without documenting their effect on `build/`, `dist/`, or generated DMG files.
