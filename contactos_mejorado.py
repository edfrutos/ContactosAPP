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
        self.contactos.sort(key=lambda c: c["nombre"].lower())
        with open(CONTACTOS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.contactos, f, indent=4, ensure_ascii=False)

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
    def _normalizar_cabecera_csv(clave):
        texto = unicodedata.normalize("NFKD", str(clave or "").replace("\ufeff", ""))
        texto = "".join(c for c in texto if not unicodedata.combining(c))
        texto = texto.casefold().strip()
        return re.sub(r"[\s_]+", " ", texto)

    def _primer_valor_csv(self, row, exactos=(), contiene=()):
        valores = [
            (self._normalizar_cabecera_csv(clave), (valor or "").strip())
            for clave, valor in row.items()
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
                    contactos.append(contacto)
        return contactos

    def _contactos_desde_vcard(self, ruta):
        with open(ruta, "r", encoding="utf-8-sig", errors="replace") as f:
            lineas = self._desplegar_lineas_vcard(f.read())

        contactos = []
        actual = {}
        en_vcard = False
        for linea in lineas:
            if linea.upper() == "BEGIN:VCARD":
                actual = {}
                en_vcard = True
                continue
            if linea.upper() == "END:VCARD":
                nombre = actual.get("fn") or actual.get("n", "")
                contacto = self._preparar_contacto(nombre, actual.get("tel", ""), actual.get("email", ""))
                if contacto:
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
            elif clave_base == "TEL" and not actual.get("tel"):
                actual["tel"] = valor
            elif clave_base == "EMAIL" and not actual.get("email"):
                actual["email"] = valor
        return contactos

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
    def _fusionar_contactos(existente, nuevo):
        fusionado = existente.copy()
        for campo in ("nombre", "teléfono", "email"):
            if not fusionado.get(campo) and nuevo.get(campo):
                fusionado[campo] = nuevo[campo]
        if len(nuevo.get("nombre", "")) > len(fusionado.get("nombre", "")):
            fusionado["nombre"] = nuevo["nombre"]
        return fusionado

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

        añadidos = fusionados = omitidos = 0
        for nuevo in nuevos:
            idx = self._indice_duplicado(nuevo)
            if idx is None:
                self.contactos.append(nuevo)
                añadidos += 1
                continue

            existente = self.contactos[idx]
            decision = messagebox.askyesnocancel(
                "Duplicado detectado",
                "Ya existe un contacto parecido:\n\n"
                f"Existente: {existente.get('nombre')} | {existente.get('teléfono')} | {existente.get('email')}\n"
                f"Importado: {nuevo.get('nombre')} | {nuevo.get('teléfono')} | {nuevo.get('email')}\n\n"
                "Sí: fusionar completando campos vacíos.\n"
                "No: omitir el contacto importado.\n"
                "Cancelar: detener la importación.",
                parent=self.root,
            )
            if decision is None:
                break
            if decision:
                self.contactos[idx] = self._fusionar_contactos(existente, nuevo)
                fusionados += 1
            else:
                omitidos += 1

        self._guardar()
        self._limpiar_formulario()
        self._actualizar_lista(self.entry_busqueda.get())
        self._flash_status(f"✓  {añadidos} añadidos, {fusionados} fusionados, {omitidos} omitidos.")

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
            self.contactos[self._idx_edicion] = {"nombre": nombre, "teléfono": telefono, "email": email}
            self._flash_status(f"✓  '{nombre}' actualizado correctamente.")
        else:
            self.contactos.append({"nombre": nombre, "teléfono": telefono, "email": email})
            self._flash_status(f"✓  '{nombre}' añadido correctamente.")

        self._guardar()
        self._limpiar_formulario()
        self._actualizar_lista(self.entry_busqueda.get())

    def _eliminar_contacto(self):
        item = self.lista.focus()
        if not item:
            messagebox.showwarning("Sin selección", "Selecciona un contacto para eliminarlo.", parent=self.root)
            return
        idx = int(self.lista.item(item)["values"][3])
        nombre = self.contactos[idx]["nombre"]
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
            writer.writerow(["Nombre", "Teléfono", "Email"])
            for c in self.contactos:
                writer.writerow([c["nombre"], c["teléfono"], c["email"]])
        self._flash_status(f"✓  {len(self.contactos)} contactos exportados a CSV.")

    # ── Helpers UI ───────────────────────────────────────────────────────────────

    def _actualizar_lista(self, filtro=""):
        self.lista.delete(*self.lista.get_children())
        filtro_l = filtro.lower()
        visible = 0
        for idx, c in enumerate(self.contactos):
            if (
                filtro_l in c["nombre"].lower()
                or filtro_l in c["teléfono"].lower()
                or filtro_l in c["email"].lower()
            ):
                tag = "par" if visible % 2 == 0 else "impar"
                # El índice real se guarda en la columna oculta _idx
                self.lista.insert("", "end", values=(c["nombre"], c["teléfono"], c["email"], idx), tags=(tag,))
                visible += 1
        self.lbl_total.config(text=f"{visible} contacto{'s' if visible != 1 else ''}")

    def _seleccionar_contacto(self, _event=None):
        item = self.lista.focus()
        if not item:
            return
        idx = int(self.lista.item(item)["values"][3])
        c = self.contactos[idx]
        for entry, valor in zip(
            (self.entry_nombre, self.entry_telefono, self.entry_email),
            (c["nombre"], c["teléfono"], c["email"]),
        ):
            entry.delete(0, tk.END)
            entry.insert(0, valor)
        self._modo_edicion = True
        self._idx_edicion = idx
        self._refrescar_modo()

    def _limpiar_formulario(self):
        for e in (self.entry_nombre, self.entry_telefono, self.entry_email):
            e.delete(0, tk.END)
        self._modo_edicion = False
        self._idx_edicion = None
        self.lista.selection_remove(*self.lista.selection())
        self._refrescar_modo()

    def _refrescar_modo(self):
        if self._modo_edicion:
            self.btn_guardar.config(text="💾  Guardar cambios")
            self.lbl_modo.config(text="  EDITANDO  ", bg=COLORS["warning"])
            self.btn_cancelar.pack(fill="x", pady=(0, 6))
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
        tiene_datos = any(e.get().strip() for e in (self.entry_nombre, self.entry_telefono, self.entry_email))
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

        # Indicador de modo (NUEVO / EDITANDO)
        top = tk.Frame(form, bg=COLORS["panel"])
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
            fila = tk.Frame(form, bg=COLORS["panel"])
            fila.pack(fill="x", pady=(4, 2))
            tk.Label(fila, text=label, bg=COLORS["panel"], fg=COLORS["text"],
                     font=("Helvetica Neue", 11, "bold")).pack(side="left")
            tk.Label(fila, text=hint, bg=COLORS["panel"], fg="#CBD5E1",
                     font=("Helvetica Neue", 9)).pack(side="left", padx=(8, 0))
            entry = ttk.Entry(form, width=30)
            entry.pack(fill="x", pady=(0, 8))
            entries.append(entry)
        self.entry_nombre, self.entry_telefono, self.entry_email = entries

        ttk.Separator(form, orient="horizontal").pack(fill="x", pady=14)

        self.btn_guardar = ttk.Button(
            form, text="➕  Añadir contacto", style="Primary.TButton",
            command=self._guardar_contacto,
        )
        self.btn_guardar.pack(fill="x", pady=(0, 6))

        self.btn_cancelar = ttk.Button(
            form, text="Cancelar edición", style="Secondary.TButton",
            command=self._limpiar_formulario,
        )
        # Se muestra/oculta dinámicamente con pack/pack_forget

        ttk.Separator(form, orient="horizontal").pack(fill="x", pady=14)

        ttk.Button(
            form, text="🗑  Eliminar seleccionado", style="Danger.TButton",
            command=self._eliminar_contacto,
        ).pack(fill="x", pady=(0, 6))

        ttk.Button(
            form, text="Exportar a CSV →", style="Ghost.TButton",
            command=self._exportar_csv,
        ).pack(fill="x")

        self.btn_importar = ttk.Button(
            form, text="Importar contactos...", style="Ghost.TButton",
            command=self._importar_contactos,
        )
        self.btn_importar.pack(fill="x", pady=(6, 0))

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

        self.lbl_total = tk.Label(search_row, text="", bg=COLORS["panel"], fg=COLORS["text_muted"],
                                   font=("Helvetica Neue", 10))
        self.lbl_total.grid(row=0, column=2, padx=(10, 0))

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
        self.lista.configure(yscrollcommand=sb.set)

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
