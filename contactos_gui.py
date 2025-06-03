import tkinter as tk
from tkinter import messagebox, simpledialog
import json
import os

CONTACTOS_FILE = "contactos.json"

# === Funciones de lógica ===
def cargar_contactos():
    if not os.path.exists(CONTACTOS_FILE):
        return []
    with open(CONTACTOS_FILE, "r") as f:
        return json.load(f)

def guardar_contactos():
    with open(CONTACTOS_FILE, "w") as f:
        json.dump(contactos, f, indent=4)

def añadir_contacto():
    nombre = entrada_nombre.get().strip()
    teléfono = entrada_telefono.get().strip()
    email = entrada_email.get().strip()

    if not nombre:
        messagebox.showwarning("Campo obligatorio", "El nombre es obligatorio.")
        return

    contactos.append({"nombre": nombre, "teléfono": teléfono, "email": email})
    guardar_contactos()
    actualizar_lista()
    entrada_nombre.delete(0, tk.END)
    entrada_telefono.delete(0, tk.END)
    entrada_email.delete(0, tk.END)

def buscar_contacto():
    término = simpledialog.askstring("Buscar", "Introduce el nombre:")
    if término:
        resultados = [f"{c['nombre']} - {c['teléfono']} - {c['email']}" for c in contactos if término.lower() in c["nombre"].lower()]
        if resultados:
            messagebox.showinfo("Resultados", "\n".join(resultados))
        else:
            messagebox.showinfo("Sin resultados", "No se encontró ningún contacto.")

def eliminar_contacto():
    seleccionado = lista.curselection()
    if not seleccionado:
        messagebox.showwarning("Selecciona un contacto", "Selecciona un contacto de la lista.")
        return
    índice = seleccionado[0]
    contacto = contactos[índice]
    if messagebox.askyesno("Confirmar", f"¿Eliminar a {contacto['nombre']}?"):
        del contactos[índice]
        guardar_contactos()
        actualizar_lista()

def actualizar_lista():
    lista.delete(0, tk.END)
    for c in contactos:
        lista.insert(tk.END, f"{c['nombre']} - {c['teléfono']} - {c['email']}")

# === Interfaz gráfica ===
root = tk.Tk()
root.title("Agenda de Contactos")

frame_formulario = tk.Frame(root)
frame_formulario.pack(pady=10)

tk.Label(frame_formulario, text="Nombre:").grid(row=0, column=0)
entrada_nombre = tk.Entry(frame_formulario, width=30)
entrada_nombre.grid(row=0, column=1)

tk.Label(frame_formulario, text="Teléfono:").grid(row=1, column=0)
entrada_telefono = tk.Entry(frame_formulario, width=30)
entrada_telefono.grid(row=1, column=1)

tk.Label(frame_formulario, text="Email:").grid(row=2, column=0)
entrada_email = tk.Entry(frame_formulario, width=30)
entrada_email.grid(row=2, column=1)

botón_añadir = tk.Button(root, text="Añadir contacto", command=añadir_contacto)
botón_añadir.pack(pady=5)

frame_botones = tk.Frame(root)
frame_botones.pack(pady=5)

tk.Button(frame_botones, text="Buscar", command=buscar_contacto).grid(row=0, column=0, padx=5)
tk.Button(frame_botones, text="Eliminar", command=eliminar_contacto).grid(row=0, column=1, padx=5)

lista = tk.Listbox(root, width=60)
lista.pack(pady=10)

# === Cargar y mostrar contactos ===
contactos = cargar_contactos()
actualizar_lista()

root.mainloop()
