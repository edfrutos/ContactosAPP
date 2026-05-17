import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import csv
import re
import sys
import unicodedata


def _ruta_contactos():
    if getattr(sys, "frozen", False):
        app_dir = os.path.join(os.path.expanduser("~/Library/Application Support"), "ContactosAPP")
        os.makedirs(app_dir, exist_ok=True)
        return os.path.join(app_dir, "contactos.json")
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "contactos.json")


CONTACTOS_FILE = _ruta_contactos()
BASE_FIELDS = ("nombre", "teléfono", "email")
MAX_EXTRA_PHONES = 4
MAX_EXTRA_EMAILS = 2

COLORS = {
    "bg":           "#F5F7FA",
    "panel":        "#FFFFFF",
    "primary":      "#3B82F6",
    "primary_dark": "#2563EB",
    "danger":       "#EF4444",
    "danger_dark":  "#DC2626",
    "success":      "#10B981",
    "warning":      "#F59E0B",
    "text":         "#1F2937",
    "text_muted":   "#6B7280",
    "border":       "#E5E7EB",
    "header_bg":    "#1E293B",
    "header_fg":    "#F8FAFC",
    "row_even":     "#FFFFFF",
    "row_odd":      "#F9FAFB",
    "selected":     "#DBEAFE",
    "selected_fg":  "#1D4ED8",
}


class ContactosApp:
    def __init__(self, root):
        self.root = root
        self.contactos = self._cargar()
        self.campos = self._asegurar_campos(self.contactos)
        self.extra_entries = {}
        self._extra_fields_actuales = ()
        self._orden_columna = "nombre"
        self._orden_desc = False
        self._modo_edicion = False
        self._idx_edicion = None  # índice real en self.contactos

        self._configurar_ventana()
        self._configurar_estilos()
        self._construir_ui()
        self._actualizar_lista()

    # ── Persistencia ─────────────────────────────────────────────────────────────

    def _cargar(self):
        if not os.path.exists(CONTACTOS_FILE):
            return []
        with open(CONTACTOS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    def _guardar(self):
        self.campos = self._asegurar_campos(self.contactos)
        self.contactos.sort(key=lambda c: c.get("nombre", "").lower())
        with open(CONTACTOS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.contactos, f, indent=4, ensure_ascii=False)

    @classmethod
    def _campos_desde_contactos(cls, contactos):
        campos = list(BASE_FIELDS)
        for contacto in contactos:
            for campo in contacto:
                if campo not in campos and not cls._campo_importado_ignorado(campo):
                    campos.append(campo)
        return campos

    def _asegurar_campos(self, contactos):
        campos = self._campos_desde_contactos(contactos)
        for contacto in contactos:
            for campo in campos:
                contacto.setdefault(campo, "")
        return campos

    def _ampliar_esquema(self, nuevos):
        campos = self._campos_desde_contactos(self.contactos + nuevos)
        for contacto in self.contactos + nuevos:
            for campo in campos:
                contacto.setdefault(campo, "")
        self.campos = campos
        if hasattr(self, "extra_fields_frame"):
            self._reconstruir_campos_extra()

    # ── Importación de contactos ────────────────────────────────────────────────

    @staticmethod
    def _normalizar_texto(valor):
        return (valor or "").strip()

    @staticmethod
    def _normalizar_email(valor):
        return (valor or "").strip().lower()

    @staticmethod
    def _normalizar_telefono(valor):
        return re.sub(r"\D", "", valor or "")

    @staticmethod
    def _telefonos_equivalentes(a, b):
        if not a or not b:
            return False
        return a == b or (len(a) >= 7 and len(b) >= 7 and (a.endswith(b) or b.endswith(a)))

    @staticmethod
    def _desplegar_lineas_vcard(texto):
        lineas = []
        for linea in texto.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
            if linea.startswith((" ", "\t")) and lineas:
                lineas[-1] += linea[1:]
            else:
                lineas.append(linea)
        return lineas

    @staticmethod
    def _desescapar_vcard(valor):
        return (
            valor.replace("\\n", "\n")
            .replace("\\N", "\n")
            .replace("\\,", ",")
            .replace("\\;", ";")
            .replace("\\\\", "\\")
            .strip()
        )

    @staticmethod
    def _primer_valor(row, claves):
        for clave in claves:
            valor = (row.get(clave) or "").strip()
            if valor:
                return valor
        return ""

    @staticmethod
    def _normalizar_nombre_campo(valor):
        valor = (valor or "").strip()
        valor = re.sub(r"\s+", " ", valor)
        return valor[:1].lower() + valor[1:] if valor else ""

    @staticmethod
    def _normalizar_cabecera_csv(clave):
        texto = unicodedata.normalize("NFKD", str(clave or "").replace("\ufeff", ""))
        texto = "".join(c for c in texto if not unicodedata.combining(c))
        texto = texto.casefold().strip()
        return re.sub(r"[\s_]+", " ", texto)

    @staticmethod
    def _numero_campo_repetido(campo_norm, prefijos):
        for prefijo in prefijos:
            match = re.search(rf"\b{re.escape(prefijo)}\s*(\d+)\b", campo_norm)
            if match:
                return int(match.group(1))
        return None

    @classmethod
    def _campo_importado_ignorado(cls, campo, para_busqueda=False):
        campo_norm = cls._normalizar_cabecera_csv(campo).replace("-", " ")
        if campo_norm.startswith("x "):
            return True

        if re.search(r"\b(label|etiqueta|lat|latitude|long|longitude)\b", campo_norm):
            return True

        if re.match(r"^(address|direccion|dirección|event|evento|relation|relacion|relación)\s+\d+\b", campo_norm):
            return True

        if re.match(r"^website\s+[2-9]\d*\b", campo_norm):
            return True

        if campo_norm == "organization":
            return True

        telefono_num = cls._numero_campo_repetido(campo_norm, ("telefono", "phone"))
        if (
            not para_busqueda
            and telefono_num is not None
            and re.search(r"\b(value|valor|formatted|formateado)\b", campo_norm)
        ):
            return True
        if telefono_num is not None and (
            telefono_num > MAX_EXTRA_PHONES or (
                telefono_num > 2 and re.search(r"\b(value|valor|formatted|formateado)\b", campo_norm)
            )
        ):
            return True
        email_num = cls._numero_campo_repetido(campo_norm, ("email", "e mail", "correo electronico"))
        if email_num is not None and email_num > MAX_EXTRA_EMAILS:
            return True
        return (
            not para_busqueda
            and email_num is not None
            and re.search(r"\b(value|valor)\b", campo_norm)
        )

    def _primer_valor_csv(self, row, exactos=(), contiene=()):
        valores = [
            (self._normalizar_cabecera_csv(clave), (valor or "").strip())
            for clave, valor in row.items()
            if not self._campo_importado_ignorado(clave, para_busqueda=True)
        ]
        for buscado in exactos:
            buscado_norm = self._normalizar_cabecera_csv(buscado)
            for clave, valor in valores:
                if valor and clave == buscado_norm:
                    return valor
        for tokens in contiene:
            tokens_norm = [self._normalizar_cabecera_csv(token) for token in tokens]
            for clave, valor in valores:
                if valor and all(token in clave for token in tokens_norm):
                    return valor
        return ""

    def _contactos_desde_google_csv(self, ruta):
        contactos = []
        with open(ruta, "r", encoding="utf-8-sig", newline="") as f:
            muestra = f.read(4096)
            f.seek(0)
            try:
                dialecto = csv.Sniffer().sniff(muestra, delimiters=",;\t")
            except csv.Error:
                dialecto = csv.excel
            reader = csv.DictReader(f, dialect=dialecto)
            for row in reader:
                nombre = self._primer_valor_csv(row, exactos=(
                    "Name", "Full Name", "Nombre", "Nombre completo",
                    "Display Name", "Nombre para mostrar",
                ))
                if not nombre:
                    partes = [
                        self._primer_valor_csv(row, exactos=("Given Name", "First Name", "Nombre de pila")),
                        self._primer_valor_csv(row, exactos=("Additional Name", "Middle Name", "Segundo nombre")),
                        self._primer_valor_csv(row, exactos=("Family Name", "Last Name", "Apellidos")),
                    ]
                    nombre = " ".join(p for p in partes if p).strip()

                telefono = self._primer_valor_csv(row, exactos=(
                    "Phone 1 - Value", "Phone 2 - Value", "Phone 3 - Value",
                    "Teléfono 1 - Valor", "Teléfono 2 - Valor", "Teléfono 3 - Valor",
                    "Telefono 1 - Valor", "Telefono 2 - Valor", "Telefono 3 - Valor",
                    "Phone 1 - Formatted", "Teléfono", "Telefono", "Phone", "Mobile Phone",
                    "Móvil", "Movil", "Teléfono móvil", "Telefono movil",
                ), contiene=(
                    ("phone", "value"), ("telefono", "value"), ("telefono", "valor"), ("movil",),
                ))
                email = self._primer_valor_csv(row, exactos=(
                    "E-mail 1 - Value", "E-mail 2 - Value", "E-mail 3 - Value",
                    "E-mail 1 - Valor", "E-mail 2 - Valor", "E-mail 3 - Valor",
                    "Correo electrónico 1 - Valor", "Correo electrónico 2 - Valor",
                    "Correo electronico 1 - Valor", "Correo electronico 2 - Valor",
                    "Email", "E-mail Address", "Correo electrónico", "Correo electronico",
                ), contiene=(
                    ("e-mail", "value"), ("email", "value"), ("e-mail", "valor"),
                    ("email", "valor"), ("correo", "valor"), ("correo",),
                ))
                contacto = self._preparar_contacto(nombre, telefono, email)
                if contacto:
                    self._añadir_campos_extra_csv(contacto, row)
                    contactos.append(contacto)
        return contactos

    def _añadir_campos_extra_csv(self, contacto, row):
        for clave, valor in row.items():
            valor = self._normalizar_texto(valor)
            campo = self._normalizar_nombre_campo(clave)
            if not valor or not campo:
                continue
            campo_norm = self._normalizar_cabecera_csv(campo)
            if campo_norm in {
                "name", "full name", "nombre", "nombre completo",
                "display name", "nombre para mostrar", "given name",
                "first name", "nombre de pila", "additional name",
                "middle name", "segundo nombre", "family name",
                "last name", "apellidos",
            }:
                continue
            if self._campo_importado_ignorado(campo):
                continue
            if valor in (contacto.get("teléfono"), contacto.get("email")):
                continue
            if campo not in contacto:
                contacto[campo] = valor

    def _contactos_desde_vcard(self, ruta):
        with open(ruta, "r", encoding="utf-8-sig", errors="replace") as f:
            lineas = self._desplegar_lineas_vcard(f.read())

        contactos = []
        actual = {}
        en_vcard = False
        for linea in lineas:
            if linea.upper() == "BEGIN:VCARD":
                actual = {"tel": [], "email": []}
                en_vcard = True
                continue
            if linea.upper() == "END:VCARD":
                nombre = actual.get("fn") or actual.get("n", "")
                telefonos = actual.get("tel") or []
                emails = actual.get("email") or []
                contacto = self._preparar_contacto(
                    nombre,
                    telefonos[0] if telefonos else "",
                    emails[0] if emails else "",
                )
                if contacto:
                    for i, telefono in enumerate(telefonos[1:], start=2):
                        campo = f"teléfono {i}"
                        if not self._campo_importado_ignorado(campo):
                            contacto[campo] = telefono
                    for i, email in enumerate(emails[1:], start=2):
                        campo = f"email {i}"
                        if not self._campo_importado_ignorado(campo):
                            contacto[campo] = email
                    for campo, valor in actual.get("extras", {}).items():
                        contacto[campo] = valor
                    contactos.append(contacto)
                actual = {}
                en_vcard = False
                continue
            if not en_vcard or ":" not in linea:
                continue

            clave, valor = linea.split(":", 1)
            clave = clave.split(";", 1)[0].upper()
            clave_base = clave.rsplit(".", 1)[-1]
            valor = self._desescapar_vcard(valor)

            if clave_base == "FN" and not actual.get("fn"):
                actual["fn"] = valor
            elif clave_base == "N" and not actual.get("n"):
                partes = valor.split(";")
                familia = partes[0] if len(partes) > 0 else ""
                nombre = partes[1] if len(partes) > 1 else ""
                adicional = partes[2] if len(partes) > 2 else ""
                prefijo = partes[3] if len(partes) > 3 else ""
                sufijo = partes[4] if len(partes) > 4 else ""
                actual["n"] = " ".join(p for p in (prefijo, nombre, adicional, familia, sufijo) if p).strip()
            elif clave_base == "TEL":
                actual.setdefault("tel", []).append(valor)
            elif clave_base == "EMAIL":
                actual.setdefault("email", []).append(valor)
            elif clave_base not in {"BEGIN", "END", "VERSION", "PRODID"}:
                campo = self._campo_extra_vcard(clave_base)
                if campo and valor and not self._campo_importado_ignorado(campo):
                    actual.setdefault("extras", {}).setdefault(campo, valor)
        return contactos

    @staticmethod
    def _campo_extra_vcard(clave):
        return {
            "ORG": "empresa",
            "TITLE": "cargo",
            "ADR": "dirección",
            "NOTE": "notas",
            "URL": "web",
            "BDAY": "cumpleaños",
            "NICKNAME": "alias",
        }.get(clave, clave.lower())

    def _preparar_contacto(self, nombre, telefono, email):
        nombre = self._normalizar_texto(nombre)
        telefono = self._normalizar_texto(telefono)
        email = self._normalizar_texto(email)
        if not nombre:
            return None
        return {"nombre": nombre, "teléfono": telefono, "email": email}

    def _indice_duplicado(self, nuevo):
        nuevo_email = self._normalizar_email(nuevo.get("email"))
        nuevo_tel = self._normalizar_telefono(nuevo.get("teléfono"))
        nuevo_nombre = nuevo.get("nombre", "").casefold()

        for idx, existente in enumerate(self.contactos):
            email = self._normalizar_email(existente.get("email"))
            tel = self._normalizar_telefono(existente.get("teléfono"))
            nombre = existente.get("nombre", "").casefold()
            if nuevo_email and email and nuevo_email == email:
                return idx
            if self._telefonos_equivalentes(nuevo_tel, tel):
                return idx
            if not nuevo_email and not nuevo_tel and nuevo_nombre and nuevo_nombre == nombre:
                return idx
        return None

    @staticmethod
    def _campos_conflictivos(existente, nuevo):
        conflictos = []
        for campo in set(existente) | set(nuevo):
            local = (existente.get(campo) or "").strip()
            importado = (nuevo.get(campo) or "").strip()
            if local and importado and not ContactosApp._valores_equivalentes(campo, local, importado):
                conflictos.append(campo)
        return conflictos

    @staticmethod
    def _valores_equivalentes(campo, local, importado):
        campo_norm = ContactosApp._normalizar_cabecera_csv(campo)
        if "email" in campo_norm or "e-mail" in campo_norm or "correo" in campo_norm:
            return ContactosApp._normalizar_email(local) == ContactosApp._normalizar_email(importado)
        if "telefono" in campo_norm or "phone" in campo_norm or "movil" in campo_norm:
            return ContactosApp._telefonos_equivalentes(
                ContactosApp._normalizar_telefono(local),
                ContactosApp._normalizar_telefono(importado),
            )
        return local == importado

    @staticmethod
    def _fusionar_contactos(existente, nuevo, preferencia="local"):
        fusionado = existente.copy()
        for campo in set(existente) | set(nuevo):
            local = (fusionado.get(campo) or "").strip()
            importado = (nuevo.get(campo) or "").strip()
            if not local and importado:
                fusionado[campo] = nuevo[campo]
            elif local and importado and not ContactosApp._valores_equivalentes(campo, local, importado) and preferencia == "importado":
                fusionado[campo] = nuevo[campo]
        return fusionado

    def _dialogo_opciones(self, titulo, mensaje, opciones):
        ventana = tk.Toplevel(self.root)
        ventana.title(titulo)
        ventana.transient(self.root)
        ventana.grab_set()
        ventana.resizable(False, False)

        resultado = {"valor": None}
        marco = ttk.Frame(ventana, padding=16)
        marco.grid(row=0, column=0, sticky="nsew")
        ttk.Label(marco, text=mensaje, justify="left", wraplength=560).grid(row=0, column=0, columnspan=len(opciones), sticky="w")

        def elegir(valor):
            resultado["valor"] = valor
            ventana.destroy()

        for col, (texto, valor) in enumerate(opciones):
            ttk.Button(marco, text=texto, command=lambda v=valor: elegir(v)).grid(row=1, column=col, padx=(0, 8), pady=(14, 0))

        ventana.protocol("WM_DELETE_WINDOW", lambda: elegir(None))
        ventana.update_idletasks()
        x = self.root.winfo_rootx() + (self.root.winfo_width() - ventana.winfo_width()) // 2
        y = self.root.winfo_rooty() + (self.root.winfo_height() - ventana.winfo_height()) // 2
        ventana.geometry(f"+{max(x, 0)}+{max(y, 0)}")
        self.root.wait_window(ventana)
        return resultado["valor"]

    def _preguntar_duplicado(self, existente, nuevo, conflictos):
        campos = ", ".join(conflictos[:6])
        if len(conflictos) > 6:
            campos += f" y {len(conflictos) - 6} más"
        return self._dialogo_opciones(
            "Duplicado detectado",
            "Ya existe un contacto parecido:\n\n"
            f"Existente: {existente.get('nombre', '')} | {existente.get('teléfono', '')} | {existente.get('email', '')}\n"
            f"Importado: {nuevo.get('nombre', '')} | {nuevo.get('teléfono', '')} | {nuevo.get('email', '')}\n\n"
            f"Campos con conflicto: {campos}",
            (
                ("Fusionar este", "fusionar"),
                ("Guardar ambos", "guardar_ambos"),
                ("Omitir", "omitir"),
                ("Fusionar todo", "fusionar_todo"),
                ("Cancelar", "cancelar"),
            ),
        )

    def _preguntar_preferencia_fusion(self):
        return self._dialogo_opciones(
            "Criterio de fusión",
            "Para los campos que tengan valores distintos en local e importado, elige qué dato debe conservarse.\n\n"
            "Los campos vacíos en local se rellenarán siempre con el dato importado sin preguntar.",
            (
                ("Mantener local", "local"),
                ("Usar importado", "importado"),
                ("Cancelar", None),
            ),
        )

    def _importar_contactos(self):
        ruta = filedialog.askopenfilename(
            title="Importar contactos",
            filetypes=[
                ("Contactos Google CSV o Apple vCard", "*.csv *.vcf *.vcard"),
                ("Google Contacts CSV", "*.csv"),
                ("Apple Contacts vCard", "*.vcf *.vcard"),
                ("Todos los archivos", "*.*"),
            ],
            parent=self.root,
        )
        if not ruta:
            return

        try:
            extension = os.path.splitext(ruta)[1].lower()
            if extension == ".csv":
                nuevos = self._contactos_desde_google_csv(ruta)
            elif extension in (".vcf", ".vcard"):
                nuevos = self._contactos_desde_vcard(ruta)
            else:
                messagebox.showwarning("Formato no soportado", "Selecciona un archivo .csv, .vcf o .vcard.", parent=self.root)
                return
        except (OSError, csv.Error, UnicodeError) as exc:
            messagebox.showerror("Error al importar", f"No se pudo leer el archivo:\n{exc}", parent=self.root)
            return

        if not nuevos:
            messagebox.showwarning("Sin contactos", "No se encontraron contactos válidos en el archivo.", parent=self.root)
            return

        self._ampliar_esquema(nuevos)
        añadidos = guardados_ambos = fusionados = fusionados_auto = omitidos = 0
        preferencia_global = None
        for nuevo in nuevos:
            idx = self._indice_duplicado(nuevo)
            if idx is None:
                self.contactos.append(nuevo)
                añadidos += 1
                continue

            existente = self.contactos[idx]
            conflictos = self._campos_conflictivos(existente, nuevo)
            if not conflictos:
                self.contactos[idx] = self._fusionar_contactos(existente, nuevo, "local")
                fusionados_auto += 1
                continue

            preferencia = preferencia_global
            if not preferencia:
                decision = self._preguntar_duplicado(existente, nuevo, conflictos)
                if decision in (None, "cancelar"):
                    break
                if decision == "guardar_ambos":
                    self.contactos.append(nuevo)
                    guardados_ambos += 1
                    continue
                if decision == "omitir":
                    omitidos += 1
                    continue
                if decision == "fusionar_todo":
                    preferencia_global = self._preguntar_preferencia_fusion()
                    if not preferencia_global:
                        break
                    preferencia = preferencia_global
                else:
                    preferencia = self._preguntar_preferencia_fusion()

            if not preferencia:
                break

            self.contactos[idx] = self._fusionar_contactos(existente, nuevo, preferencia)
            fusionados += 1

        self._guardar()
        self._limpiar_formulario()
        self._actualizar_lista(self.entry_busqueda.get())
        self._flash_status(
            f"✓  {añadidos} añadidos, {guardados_ambos} guardados como nuevos, "
            f"{fusionados + fusionados_auto} fusionados, {omitidos} omitidos."
        )

    # ── Validación ───────────────────────────────────────────────────────────────

    @staticmethod
    def _email_valido(email):
        return bool(re.match(r"[^@\s]+@[^@\s]+\.[^@\s]+", email))

    @staticmethod
    def _telefono_valido(tel):
        # Acepta dígitos, espacios, guiones, paréntesis y prefijo +
        return bool(re.match(r"^\+?[\d\s\-().]{6,20}$", tel))

    # ── CRUD ──────────────────────────────────────────────────────────────────────

    def _guardar_contacto(self):
        nombre   = self.entry_nombre.get().strip()
        telefono = self.entry_telefono.get().strip()
        email    = self.entry_email.get().strip()

        if not nombre:
            messagebox.showwarning("Campo obligatorio", "El nombre es obligatorio.", parent=self.root)
            return
        if email and not self._email_valido(email):
            messagebox.showwarning("Email inválido", "Formato esperado: usuario@dominio.ext", parent=self.root)
            return
        if telefono and not self._telefono_valido(telefono):
            messagebox.showwarning("Teléfono inválido", "Mínimo 6 dígitos. Se permiten: + espacios - ( )", parent=self.root)
            return

        if self._modo_edicion and self._idx_edicion is not None:
            contacto = self.contactos[self._idx_edicion].copy()
            contacto.update({"nombre": nombre, "teléfono": telefono, "email": email})
            for campo, entry in self.extra_entries.items():
                contacto[campo] = entry.get().strip()
            self.contactos[self._idx_edicion] = contacto
            self._flash_status(f"✓  '{nombre}' actualizado correctamente.")
        else:
            contacto = {campo: "" for campo in self.campos}
            contacto.update({"nombre": nombre, "teléfono": telefono, "email": email})
            for campo, entry in self.extra_entries.items():
                contacto[campo] = entry.get().strip()
            self.contactos.append(contacto)
            self._flash_status(f"✓  '{nombre}' añadido correctamente.")

        self._guardar()
        self._limpiar_formulario()
        self._actualizar_lista(self.entry_busqueda.get())

    def _eliminar_contacto(self):
        item = self.lista.focus()
        if not item:
            messagebox.showwarning("Sin selección", "Selecciona un contacto para eliminarlo.", parent=self.root)
            return
        idx = int(self.lista.item(item)["values"][-1])
        nombre = self.contactos[idx].get("nombre", "")
        if messagebox.askyesno(
            "Confirmar eliminación",
            f"¿Eliminar el contacto '{nombre}'?\nEsta acción no se puede deshacer.",
            parent=self.root,
        ):
            del self.contactos[idx]
            self._guardar()
            self._limpiar_formulario()
            self._actualizar_lista(self.entry_busqueda.get())
            self._flash_status(f"✓  '{nombre}' eliminado.")

    def _exportar_csv(self):
        ruta = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV", "*.csv"), ("Todos los archivos", "*.*")],
            parent=self.root,
        )
        if not ruta:
            return
        with open(ruta, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            self.campos = self._asegurar_campos(self.contactos)
            writer.writerow(self.campos)
            for c in self.contactos:
                writer.writerow([c.get(campo, "") for campo in self.campos])
        self._flash_status(f"✓  {len(self.contactos)} contactos exportados a CSV.")

    # ── Helpers UI ───────────────────────────────────────────────────────────────

    def _actualizar_lista(self, filtro=""):
        self.campos = self._asegurar_campos(self.contactos)
        self._reconstruir_campos_extra()
        self._configurar_columnas_lista()
        self.lista.delete(*self.lista.get_children())
        filtro_l = filtro.lower()
        visible = 0
        for idx, c in enumerate(self.contactos):
            valores = [c.get(campo, "") for campo in self.campos]
            if any(filtro_l in str(valor).lower() for valor in valores):
                tag = "par" if visible % 2 == 0 else "impar"
                # El índice real se guarda en la columna oculta _idx
                self.lista.insert("", "end", values=(*valores, idx), tags=(tag,))
                visible += 1
        self.lbl_total.config(text=f"{visible} contacto{'s' if visible != 1 else ''}")

    def _configurar_columnas_lista(self):
        columnas = (*self.campos, "_idx")
        if tuple(self.lista["columns"]) != columnas:
            self.lista.configure(columns=columnas, displaycolumns=self.campos)
        for campo in self.campos:
            titulo = campo[:1].upper() + campo[1:]
            if campo == self._orden_columna:
                titulo += " ↓" if self._orden_desc else " ↑"
            self.lista.heading(
                campo,
                text=titulo,
                anchor="w",
                command=lambda c=campo: self._ordenar_por_columna(c),
            )
            ancho = 170 if campo == "nombre" else 145
            self.lista.column(campo, width=ancho, stretch=True, minwidth=90, anchor="w")
        self.lista.column("_idx", width=0, stretch=False, minwidth=0)

    def _ordenar_por_columna(self, campo):
        if self._orden_columna == campo:
            self._orden_desc = not self._orden_desc
        else:
            self._orden_columna = campo
            self._orden_desc = False

        def clave(contacto):
            valor = str(contacto.get(campo, "")).strip()
            campo_norm = self._normalizar_cabecera_csv(campo)
            if "telefono" in campo_norm or "phone" in campo_norm or "movil" in campo_norm:
                return self._normalizar_telefono(valor) or valor.casefold()
            return valor.casefold()

        self.contactos.sort(key=clave, reverse=self._orden_desc)
        self._actualizar_lista(self.entry_busqueda.get())

    def _seleccionar_contacto(self, _event=None):
        item = self.lista.focus()
        if not item:
            return
        idx = int(self.lista.item(item)["values"][-1])
        c = self.contactos[idx]
        for entry, valor in zip(
            (self.entry_nombre, self.entry_telefono, self.entry_email),
            (c.get("nombre", ""), c.get("teléfono", ""), c.get("email", "")),
        ):
            entry.delete(0, tk.END)
            entry.insert(0, valor)
        for campo, entry in self.extra_entries.items():
            entry.delete(0, tk.END)
            entry.insert(0, c.get(campo, ""))
        self._modo_edicion = True
        self._idx_edicion = idx
        self._refrescar_modo()

    def _limpiar_formulario(self):
        for e in (self.entry_nombre, self.entry_telefono, self.entry_email):
            e.delete(0, tk.END)
        for entry in self.extra_entries.values():
            entry.delete(0, tk.END)
        self._modo_edicion = False
        self._idx_edicion = None
        self.lista.selection_remove(*self.lista.selection())
        self._refrescar_modo()

    def _refrescar_modo(self):
        if self._modo_edicion:
            self.btn_guardar.config(text="💾  Guardar cambios")
            self.lbl_modo.config(text="  EDITANDO  ", bg=COLORS["warning"])
            self.btn_cancelar.pack(fill="x", pady=(0, 6), after=self.btn_guardar)
        else:
            self.btn_guardar.config(text="➕  Añadir contacto")
            self.lbl_modo.config(text="  NUEVO  ", bg=COLORS["success"])
            self.btn_cancelar.pack_forget()

    def _buscar(self, _event=None):
        self._actualizar_lista(self.entry_busqueda.get())

    def _flash_status(self, msg):
        self.lbl_status.config(text=f"  {msg}", fg=COLORS["success"])
        self.root.after(4000, lambda: self.lbl_status.config(text="", fg=COLORS["text_muted"]))

    def _on_close(self):
        entradas = (self.entry_nombre, self.entry_telefono, self.entry_email, *self.extra_entries.values())
        tiene_datos = any(e.get().strip() for e in entradas)
        if tiene_datos:
            if not messagebox.askyesno(
                "Cerrar aplicación",
                "Hay datos en el formulario sin guardar.\n¿Cerrar de todos modos?",
                parent=self.root,
            ):
                return
        self.root.destroy()

    # ── Configuración ventana ────────────────────────────────────────────────────

    def _configurar_ventana(self):
        self.root.title("Agenda de Contactos")
        self.root.configure(bg=COLORS["bg"])
        self.root.minsize(640, 520)
        self.root.update_idletasks()
        w, h = 760, 600
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.resizable(True, True)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _configurar_estilos(self):
        s = ttk.Style()
        s.theme_use("clam")

        s.configure(".", background=COLORS["bg"], foreground=COLORS["text"], font=("Helvetica Neue", 11))

        s.configure("Card.TFrame",   background=COLORS["panel"])
        s.configure("Header.TFrame", background=COLORS["header_bg"])

        s.configure("TLabel",          background=COLORS["bg"],      foreground=COLORS["text"])
        s.configure("Card.TLabel",     background=COLORS["panel"],   foreground=COLORS["text"])
        s.configure("Muted.TLabel",    background=COLORS["panel"],   foreground=COLORS["text_muted"],
                    font=("Helvetica Neue", 10))
        s.configure("Header.TLabel",   background=COLORS["header_bg"], foreground=COLORS["header_fg"],
                    font=("Helvetica Neue", 16, "bold"))
        s.configure("Subtitle.TLabel", background=COLORS["header_bg"], foreground="#94A3B8",
                    font=("Helvetica Neue", 10))

        s.configure("TEntry",
                    fieldbackground=COLORS["panel"], foreground=COLORS["text"],
                    bordercolor=COLORS["border"], padding=8)
        s.map("TEntry", bordercolor=[("focus", COLORS["primary"])])

        s.configure("Primary.TButton",
                    background=COLORS["primary"], foreground="white",
                    font=("Helvetica Neue", 11, "bold"), padding=(12, 9), relief="flat", borderwidth=0)
        s.map("Primary.TButton",
              background=[("active", COLORS["primary_dark"]), ("pressed", COLORS["primary_dark"])],
              foreground=[("active", "white")])

        s.configure("Danger.TButton",
                    background=COLORS["danger"], foreground="white",
                    font=("Helvetica Neue", 11), padding=(12, 9), relief="flat", borderwidth=0)
        s.map("Danger.TButton",
              background=[("active", COLORS["danger_dark"]), ("pressed", COLORS["danger_dark"])],
              foreground=[("active", "white")])

        s.configure("Secondary.TButton",
                    background=COLORS["border"], foreground=COLORS["text"],
                    font=("Helvetica Neue", 11), padding=(12, 9), relief="flat", borderwidth=0)
        s.map("Secondary.TButton", background=[("active", "#D1D5DB"), ("pressed", "#D1D5DB")])

        s.configure("Ghost.TButton",
                    background=COLORS["panel"], foreground=COLORS["text_muted"],
                    font=("Helvetica Neue", 10), padding=(8, 7), relief="flat", borderwidth=0)
        s.map("Ghost.TButton", background=[("active", COLORS["bg"])])

        s.configure("Treeview",
                    background=COLORS["panel"], foreground=COLORS["text"],
                    fieldbackground=COLORS["panel"], rowheight=34, font=("Helvetica Neue", 11))
        s.configure("Treeview.Heading",
                    background=COLORS["bg"], foreground=COLORS["text_muted"],
                    font=("Helvetica Neue", 10, "bold"), relief="flat", padding=(10, 8))
        s.map("Treeview",
              background=[("selected", COLORS["selected"])],
              foreground=[("selected", COLORS["selected_fg"])])
        s.map("Treeview.Heading", background=[("active", COLORS["border"])])

    # ── Construcción UI ──────────────────────────────────────────────────────────

    def _construir_ui(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)
        self._build_header()
        self._build_content()
        self._build_statusbar()

    def _build_header(self):
        hdr = ttk.Frame(self.root, style="Header.TFrame")
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.columnconfigure(1, weight=1)

        ttk.Label(hdr, text="  📋", style="Header.TLabel",
                  font=("Helvetica Neue", 22)).grid(row=0, column=0, rowspan=2, padx=(16, 8), pady=16)
        ttk.Label(hdr, text="Agenda de Contactos", style="Header.TLabel").grid(
            row=0, column=1, sticky="w", pady=(16, 2))
        ttk.Label(hdr, text="Gestiona tus contactos de forma sencilla",
                  style="Subtitle.TLabel").grid(row=1, column=1, sticky="w", pady=(0, 16))

    def _build_content(self):
        content = ttk.Frame(self.root, style="Card.TFrame", padding=16)
        content.grid(row=1, column=0, sticky="nsew", padx=16, pady=16)
        content.columnconfigure(0, weight=0, minsize=240)
        content.columnconfigure(1, weight=1)
        content.rowconfigure(0, weight=1)
        self._build_form(content)
        self._build_table(content)

    def _build_form(self, parent):
        form = ttk.Frame(parent, style="Card.TFrame", padding=(0, 0, 20, 0))
        form.grid(row=0, column=0, sticky="nsew")
        form.columnconfigure(0, weight=1)
        form.rowconfigure(0, weight=1)

        self.form_canvas = tk.Canvas(
            form,
            bg=COLORS["panel"],
            bd=0,
            highlightthickness=0,
        )
        self.form_scroll = ttk.Scrollbar(form, orient="vertical", command=self.form_canvas.yview)
        self.form_fields = tk.Frame(self.form_canvas, bg=COLORS["panel"])
        self.form_window = self.form_canvas.create_window((0, 0), window=self.form_fields, anchor="nw")
        self.form_canvas.configure(yscrollcommand=self.form_scroll.set)
        self.form_canvas.grid(row=0, column=0, sticky="nsew")
        self.form_scroll.grid(row=0, column=1, sticky="ns", padx=(4, 0))
        self.form_fields.bind("<Configure>", self._actualizar_scroll_formulario)
        self.form_canvas.bind("<Configure>", self._ajustar_ancho_formulario)
        self.form_canvas.bind("<Enter>", self._activar_scroll_formulario)
        self.form_canvas.bind("<Leave>", self._desactivar_scroll_formulario)

        # Indicador de modo (NUEVO / EDITANDO)
        top = tk.Frame(self.form_fields, bg=COLORS["panel"])
        top.pack(fill="x", pady=(0, 16))
        self.lbl_modo = tk.Label(
            top, text="  NUEVO  ",
            font=("Helvetica Neue", 9, "bold"),
            bg=COLORS["success"], fg="white", padx=8, pady=4,
        )
        self.lbl_modo.pack(side="left")

        # Campos del formulario
        campos = [
            ("Nombre",   "Ej: Ana García"),
            ("Teléfono (opcional)", "Ej: +34 612 345 678"),
            ("Email (opcional)",    "Ej: ana@ejemplo.com"),
        ]
        entries = []
        for label, hint in campos:
            fila = tk.Frame(self.form_fields, bg=COLORS["panel"])
            fila.pack(fill="x", pady=(4, 2))
            tk.Label(fila, text=label, bg=COLORS["panel"], fg=COLORS["text"],
                     font=("Helvetica Neue", 11, "bold")).pack(side="left")
            tk.Label(fila, text=hint, bg=COLORS["panel"], fg="#CBD5E1",
                     font=("Helvetica Neue", 9)).pack(side="left", padx=(8, 0))
            entry = ttk.Entry(self.form_fields, width=30)
            entry.pack(fill="x", pady=(0, 8))
            entries.append(entry)
        self.entry_nombre, self.entry_telefono, self.entry_email = entries

        self.extra_fields_title = tk.Label(
            self.form_fields, text="Campos importados", bg=COLORS["panel"], fg=COLORS["text_muted"],
            font=("Helvetica Neue", 10, "bold"),
        )
        self.extra_fields_frame = tk.Frame(self.form_fields, bg=COLORS["panel"])
        self._reconstruir_campos_extra()

        actions = tk.Frame(form, bg=COLORS["panel"])
        actions.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(14, 0))

        ttk.Separator(actions, orient="horizontal").pack(fill="x", pady=(0, 14))

        self.btn_guardar = ttk.Button(
            actions, text="➕  Añadir contacto", style="Primary.TButton",
            command=self._guardar_contacto,
        )
        self.btn_guardar.pack(fill="x", pady=(0, 6))

        self.btn_cancelar = ttk.Button(
            actions, text="Cancelar edición", style="Secondary.TButton",
            command=self._limpiar_formulario,
        )
        # Se muestra/oculta dinámicamente con pack/pack_forget

        ttk.Separator(actions, orient="horizontal").pack(fill="x", pady=14)

        ttk.Button(
            actions, text="🗑  Eliminar seleccionado", style="Danger.TButton",
            command=self._eliminar_contacto,
        ).pack(fill="x", pady=(0, 6))

        ttk.Button(
            actions, text="Exportar a CSV →", style="Ghost.TButton",
            command=self._exportar_csv,
        ).pack(fill="x")

        self.btn_importar = ttk.Button(
            actions, text="Importar contactos...", style="Ghost.TButton",
            command=self._importar_contactos,
        )
        self.btn_importar.pack(fill="x", pady=(6, 0))

    def _reconstruir_campos_extra(self):
        if not hasattr(self, "extra_fields_frame"):
            return
        extras = tuple(campo for campo in self.campos if campo not in BASE_FIELDS)
        if extras == self._extra_fields_actuales:
            return
        self._extra_fields_actuales = extras
        for widget in self.extra_fields_frame.winfo_children():
            widget.destroy()
        self.extra_entries = {}

        if not extras:
            self.extra_fields_title.pack_forget()
            self.extra_fields_frame.pack_forget()
            return

        self.extra_fields_title.pack(anchor="w", pady=(8, 4))
        self.extra_fields_frame.pack(fill="x", pady=(0, 8))
        for campo in extras:
            fila = tk.Frame(self.extra_fields_frame, bg=COLORS["panel"])
            fila.pack(fill="x", pady=(4, 2))
            tk.Label(
                fila,
                text=campo[:1].upper() + campo[1:],
                bg=COLORS["panel"],
                fg=COLORS["text"],
                font=("Helvetica Neue", 10, "bold"),
            ).pack(anchor="w")
            entry = ttk.Entry(self.extra_fields_frame, width=30)
            entry.pack(fill="x", pady=(0, 4))
            self.extra_entries[campo] = entry
        self._actualizar_scroll_formulario()

    def _actualizar_scroll_formulario(self, _event=None):
        if hasattr(self, "form_canvas"):
            self.form_canvas.configure(scrollregion=self.form_canvas.bbox("all"))

    def _ajustar_ancho_formulario(self, event):
        if hasattr(self, "form_window"):
            self.form_canvas.itemconfigure(self.form_window, width=event.width)

    def _activar_scroll_formulario(self, _event=None):
        self.root.bind_all("<MouseWheel>", self._scroll_formulario)

    def _desactivar_scroll_formulario(self, _event=None):
        self.root.unbind_all("<MouseWheel>")

    def _scroll_formulario(self, event):
        if not hasattr(self, "form_canvas"):
            return
        pasos = -1 if event.delta > 0 else 1
        self.form_canvas.yview_scroll(pasos, "units")

    def _build_table(self, parent):
        right = ttk.Frame(parent, style="Card.TFrame")
        right.grid(row=0, column=1, sticky="nsew", padx=(20, 0))
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        # Búsqueda
        search_row = tk.Frame(right, bg=COLORS["panel"])
        search_row.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        search_row.columnconfigure(1, weight=1)

        tk.Label(search_row, text="🔍 ", bg=COLORS["panel"], fg=COLORS["text_muted"],
                 font=("Helvetica Neue", 13)).grid(row=0, column=0)
        self.entry_busqueda = ttk.Entry(search_row, font=("Helvetica Neue", 11))
        self.entry_busqueda.grid(row=0, column=1, sticky="ew", ipady=4)
        self.entry_busqueda.bind("<KeyRelease>", self._buscar)

        self.btn_limpiar_busqueda = ttk.Button(
            search_row,
            text="X",
            style="Ghost.TButton",
            width=3,
            command=self._limpiar_busqueda,
        )
        self.btn_limpiar_busqueda.grid(row=0, column=2, padx=(6, 0))

        self.lbl_total = tk.Label(search_row, text="", bg=COLORS["panel"], fg=COLORS["text_muted"],
                                   font=("Helvetica Neue", 10))
        self.lbl_total.grid(row=0, column=3, padx=(10, 0))

        # Tabla
        tree_frame = ttk.Frame(right, style="Card.TFrame")
        tree_frame.grid(row=1, column=0, sticky="nsew")
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)

        self.lista = ttk.Treeview(
            tree_frame,
            columns=("nombre", "teléfono", "email", "_idx"),
            show="headings",
            displaycolumns=("nombre", "teléfono", "email"),
            selectmode="browse",
        )
        self.lista.heading("nombre",   text="Nombre",   anchor="w")
        self.lista.heading("teléfono", text="Teléfono", anchor="w")
        self.lista.heading("email",    text="Email",    anchor="w")
        self.lista.column("nombre",   width=175, stretch=True,  minwidth=100, anchor="w")
        self.lista.column("teléfono", width=145, stretch=False, minwidth=100, anchor="w")
        self.lista.column("email",    width=210, stretch=True,  minwidth=120, anchor="w")
        self.lista.grid(row=0, column=0, sticky="nsew")
        self.lista.bind("<<TreeviewSelect>>", self._seleccionar_contacto)

        self.lista.tag_configure("par",   background=COLORS["row_even"])
        self.lista.tag_configure("impar", background=COLORS["row_odd"])

        sb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.lista.yview)
        sb.grid(row=0, column=1, sticky="ns")
        sb_horizontal = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.lista.xview)
        sb_horizontal.grid(row=1, column=0, sticky="ew")
        self.lista.configure(yscrollcommand=sb.set, xscrollcommand=sb_horizontal.set)

    def _limpiar_busqueda(self):
        self.entry_busqueda.delete(0, tk.END)
        self._actualizar_lista()
        self.entry_busqueda.focus_set()

    def _build_statusbar(self):
        tk.Frame(self.root, bg=COLORS["border"], height=1).grid(row=2, column=0, sticky="ew")
        self.lbl_status = tk.Label(
            self.root, text="", bg=COLORS["bg"], fg=COLORS["text_muted"],
            font=("Helvetica Neue", 10), anchor="w", padx=16, pady=5,
        )
        self.lbl_status.grid(row=3, column=0, sticky="ew")


if __name__ == "__main__":
    root = tk.Tk()
    ContactosApp(root)
    root.mainloop()
