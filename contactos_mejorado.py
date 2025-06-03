import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
import csv
import re

CONTACTOS_FILE = "contactos.json"

# === Funciones de lógica ===

def cargar_contactos():
    if not os.path.exists(CONTACTOS_FILE):
        return []
    with open(CONTACTOS_FILE, "r") as f:
        return json.load(f)

def guardar_contactos():
    with open(CONTACTOS_FILE, "w") as f:
        json.dump(sorted(contactos, key=lambda c: c['nombre'].lower()), f, indent=4)

def actualizar_lista(filtrar=""):
    lista.delete(*lista.get_children())
    for i, c in enumerate(contactos):
        if filtrar.lower() in c['nombre'].lower():
            lista.insert("", "end", iid=i, values=(c["nombre"], c["teléfono"], c["email"]))

def validar_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def validar_telefono(teléfono):
    return teléfono.isdigit()

def añadir_contacto():
    nombre = entrada_nombre.get().strip()
    teléfono = entrada_telefono.get().strip()
    email = entrada_email.get().strip()

    if not nombre or not teléfono or not email:
        messagebox.showwarning("Faltan datos", "Todos los campos son obligatorios.")
        return
    if not validar_email(email):
        messagebox.showwarning("Email inválido", "Introduce un email válido.")
        return
    if not validar_telefono(teléfono):
        messagebox.showwarning("Teléfono inválido", "Introduce un teléfono numérico.")
        return

    contactos.append({"nombre": nombre, "teléfono": teléfono, "email": email})
    guardar_contactos()
    limpiar_campos()
    actualizar_lista(entry_busqueda.get())

def editar_contacto():
    seleccionado = lista.focus()
    if not seleccionado:
        messagebox.showwarning("Selecciona", "Selecciona un contacto para editar.")
        return

    nombre = entrada_nombre.get().strip()
    teléfono = entrada_telefono.get().strip()
    email = entrada_email.get().strip()

    if not nombre or not teléfono or not email:
        messagebox.showwarning("Faltan datos", "Todos los campos son obligatorios.")
        return
    if not validar_email(email):
        messagebox.showwarning("Email inválido", "Introduce un email válido.")
        return
    if not validar_telefono(teléfono):
        messagebox.showwarning("Teléfono inválido", "Introduce un teléfono numérico.")
        return

    contactos[int(seleccionado)] = {"nombre": nombre, "teléfono": teléfono, "email": email}
    guardar_contactos()
    limpiar_campos()
    actualizar_lista(entry_busqueda.get())

def eliminar_contacto():
    seleccionado = lista.focus()
    if not seleccionado:
        messagebox.showwarning("Selecciona", "Selecciona un contacto para eliminar.")
        return

    c = contactos[int(seleccionado)]
    if messagebox.askyesno("Confirmar", f"¿Eliminar a {c['nombre']}?"):
        del contactos[int(seleccionado)]
        guardar_contactos()
        limpiar_campos()
        actualizar_lista(entry_busqueda.get())

def exportar_csv():
    archivo = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
    if archivo:
        with open(archivo, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Nombre", "Teléfono", "Email"])
            for c in contactos:
                writer.writerow([c["nombre"], c["teléfono"], c["email"]])
        messagebox.showinfo("Exportado", f"Contactos exportados a:\n{archivo}")

def limpiar_campos():
    entrada_nombre.delete(0, tk.END)
    entrada_telefono.delete(0, tk.END)
    entrada_email.delete(0, tk.END)

def cargar_contacto_evento(event):
    seleccionado = lista.focus()
    if seleccionado:
        c = contactos[int(seleccionado)]
        entrada_nombre.delete(0, tk.END)
        entrada_nombre.insert(0, c["nombre"])
        entrada_telefono.delete(0, tk.END)
        entrada_telefono.insert(0, c["teléfono"])
        entrada_email.delete(0, tk.END)
        entrada_email.insert(0, c["email"])

def buscar_contactos(event):
    término = entry_busqueda.get()
    actualizar_lista(término)

# === Interfaz gráfica ===
root = tk.Tk()
root.title("Agenda de Contactos")

style = ttk.Style()
style.theme_use("clam")
style.configure("Treeview", font=("Segoe UI", 10))
style.configure("TButton", font=("Segoe UI", 10), padding=6)
style.configure("TEntry", padding=5)

frame_superior = ttk.Frame(root, padding=10)
frame_superior.pack()

ttk.Label(frame_superior, text="Buscar:").grid(row=0, column=0, sticky="w")
entry_busqueda = ttk.Entry(frame_superior, width=40)
entry_busqueda.grid(row=0, column=1, columnspan=2, sticky="w")
entry_busqueda.bind("<KeyRelease>", buscar_contactos)

ttk.Label(frame_superior, text="Nombre:").grid(row=1, column=0, sticky="e")
entrada_nombre = ttk.Entry(frame_superior, width=40)
entrada_nombre.grid(row=1, column=1, columnspan=2, sticky="w")

ttk.Label(frame_superior, text="Teléfono:").grid(row=2, column=0, sticky="e")
entrada_telefono = ttk.Entry(frame_superior, width=40)
entrada_telefono.grid(row=2, column=1, columnspan=2, sticky="w")

ttk.Label(frame_superior, text="Email:").grid(row=3, column=0, sticky="e")
entrada_email = ttk.Entry(frame_superior, width=40)
entrada_email.grid(row=3, column=1, columnspan=2, sticky="w")

frame_botones = ttk.Frame(root, padding=10)
frame_botones.pack()

ttk.Button(frame_botones, text="Añadir", command=añadir_contacto).grid(row=0, column=0, padx=5)
ttk.Button(frame_botones, text="Editar", command=editar_contacto).grid(row=0, column=1, padx=5)
ttk.Button(frame_botones, text="Eliminar", command=eliminar_contacto).grid(row=0, column=2, padx=5)
ttk.Button(frame_botones, text="Exportar CSV", command=exportar_csv).grid(row=0, column=3, padx=5)

frame_lista = ttk.Frame(root, padding=10)
frame_lista.pack()

lista = ttk.Treeview(frame_lista, columns=("nombre", "teléfono", "email"), show="headings", height=10)
lista.heading("nombre", text="Nombre")
lista.heading("teléfono", text="Teléfono")
lista.heading("email", text="Email")
lista.pack()
lista.bind("<<TreeviewSelect>>", cargar_contacto_evento)

contactos = cargar_contactos()
actualizar_lista()

root.mainloop()
