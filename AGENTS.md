# Repository Guidelines

## Project Structure & Module Organization

- `contactos_mejorado.py`: active app entry point and main development target.
- `contactos.json`: ignored local JSON data file used by the app.
- `contactos_example.json`: tracked sample structure with fake data.
- `setup.py`: `py2app` configuration for building a macOS `.app`.
- `requirements.txt`: packaging dependency list.
- `contactos_instalacion_y_paquetizado.sh`, `contactos_empaquetado_final.sh`, `crear_dmg_contactos.sh`: packaging scripts.
- `contactos_icon.icns`, `contactos.iconset/`, `background.png`: assets.
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

Use packaging scripts only on macOS with Tkinter support.

## Coding Style & Naming Conventions

Use Python 3.6+ compatible code. Keep the single-file Tkinter structure unless a refactor is needed. Follow existing conventions:

- Four-space indentation.
- `snake_case` for functions, methods, and variables.
- `PascalCase` for classes.
- Uppercase constants, such as `CONTACTOS_FILE` and `COLORS`.
- Private UI/helper methods prefixed with `_`.

Prefer standard-library modules already used here (`tkinter`, `json`, `csv`, `os`, `re`, `unicodedata`). Keep UI text consistent with the Spanish interface.

## Testing Guidelines

There is no automated test suite. Before submitting changes, manually verify:

- Adding, editing, deleting, and searching contacts.
- JSON persistence in `contactos.json`.
- Email and phone validation when those fields are present.
- CSV export.
- Google Contacts CSV import.
- Apple Contacts vCard import.
- Duplicate import handling: merge one, merge all, keep both, or skip with user confirmation.
- Dynamic JSON fields when imports include columns outside `nombre`, `teléfono`, and `email`.
- Dynamic imported fields must remain editable and visible as sortable table columns.
- Contact list horizontal scrolling and the search clear action.
- Closing behavior with unsaved form data.

If tests are added later, place them under `tests/` and use descriptive names like `test_contact_validation.py`.

## Commit & Pull Request Guidelines

Recent commits use short Spanish imperative messages, for example `Corregir formato en README.md`.

- A concise summary of the change.
- Manual verification steps performed.
- Screenshots or short recordings for visible UI changes.
- Notes about packaging impact when touching `setup.py`, icons, or shell scripts.

## Security & Configuration Tips

Do not commit personal contact data. Keep `contactos.json`, CSV exports, and vCard exports local. Avoid destructive packaging script changes without documenting their effect on `build/`, `dist/`, or generated DMG files.
