import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import csv
import re

# Ruta absoluta al lado del script, independiente del CWD
CONTACTOS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "contactos.json")

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

        if not nombre or not telefono or not email:
            messagebox.showwarning("Campos incompletos", "Todos los campos son obligatorios.", parent=self.root)
            return
        if not self._email_valido(email):
            messagebox.showwarning("Email inválido", "Formato esperado: usuario@dominio.ext", parent=self.root)
            return
        if not self._telefono_valido(telefono):
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
            ("Teléfono", "Ej: +34 612 345 678"),
            ("Email",    "Ej: ana@ejemplo.com"),
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
