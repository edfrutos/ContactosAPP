import json
import os

CONTACTOS_FILE = "contactos.json"

# Cargar contactos desde archivo
def cargar_contactos():
    if not os.path.exists(CONTACTOS_FILE):
        return []
    with open(CONTACTOS_FILE, "r") as f:
        return json.load(f)

# Guardar contactos en archivo
def guardar_contactos(contactos):
    with open(CONTACTOS_FILE, "w") as f:
        json.dump(contactos, f, indent=4)

# Añadir un nuevo contacto
def añadir_contacto():
    nombre = input("Nombre: ")
    teléfono = input("Teléfono: ")
    email = input("Email: ")
    contactos.append({"nombre": nombre, "teléfono": teléfono, "email": email})
    guardar_contactos(contactos)
    print("✔ Contacto añadido correctamente.")

# Buscar un contacto por nombre
def buscar_contacto():
    nombre = input("Introduce el nombre a buscar: ")
    encontrados = [c for c in contactos if nombre.lower() in c["nombre"].lower()]
    if encontrados:
        print("📋 Resultados:")
        for c in encontrados:
            print(f"{c['nombre']} - {c['teléfono']} - {c['email']}")
    else:
        print("⚠ No se encontraron contactos con ese nombre.")

# Mostrar todos los contactos
def mostrar_contactos():
    if not contactos:
        print("📭 No hay contactos guardados.")
        return
    print("📒 Lista de contactos:")
    for c in contactos:
        print(f"{c['nombre']} - {c['teléfono']} - {c['email']}")

# Eliminar contacto
def eliminar_contacto():
    nombre = input("Introduce el nombre del contacto a eliminar: ")
    global contactos
    contactos_filtrados = [c for c in contactos if nombre.lower() != c["nombre"].lower()]
    if len(contactos_filtrados) < len(contactos):
        contactos = contactos_filtrados
        guardar_contactos(contactos)
        print("🗑 Contacto eliminado.")
    else:
        print("⚠ No se encontró ningún contacto con ese nombre.")

# Menú principal
def menu():
    while True:
        print("\n=== Lista de Contactos ===")
        print("1. Añadir contacto")
        print("2. Buscar contacto")
        print("3. Mostrar todos los contactos")
        print("4. Eliminar contacto")
        print("5. Salir")
        opción = input("Selecciona una opción (1-5): ")
        if opción == "1":
            añadir_contacto()
        elif opción == "2":
            buscar_contacto()
        elif opción == "3":
            mostrar_contactos()
        elif opción == "4":
            eliminar_contacto()
        elif opción == "5":
            print("👋 Saliendo del sistema.")
            break
        else:
            print("❌ Opción no válida.")

# Programa principal
if __name__ == "__main__":
    contactos = cargar_contactos()
    menu()
