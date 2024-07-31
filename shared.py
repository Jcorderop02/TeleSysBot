import json
import logging

# Set para rastrear usuarios autenticados
authenticated_users = set()

# Diccionario para rastrear usuarios bloqueados (ID y nombre de usuario)
blocked_users = {}

# Función para cargar los usuarios autenticados desde un archivo
def load_authenticated_users():
    try:
        with open("authenticated_users.txt", "r") as file:
            users = file.read().splitlines()
            logging.info("Usuarios autenticados cargados correctamente.")
            return set(int(user) for user in users)
    except FileNotFoundError:
        logging.warning("El archivo authenticated_users.txt no existe. Se creará uno nuevo.")
        return set()

# Función para guardar los usuarios autenticados en un archivo
def save_authenticated_users():
    try:
        with open("authenticated_users.txt", "w") as file:
            for user in authenticated_users:
                file.write(f"{user}\n")
            logging.info("Usuarios autenticados guardados correctamente.")
    except Exception as e:
        logging.error(f"Error al guardar authenticated_users.txt: {e}")

# Función para cargar los usuarios bloqueados desde un archivo
def load_blocked_users():
    try:
        with open("blocked_users.txt", "r") as file:
            users = {}
            for line in file:
                name, user_id = line.strip().split(' - ')
                users[int(user_id)] = name
            logging.info("Usuarios bloqueados cargados correctamente.")
            return users
    except FileNotFoundError:
        logging.warning("El archivo blocked_users.txt no existe. Se creará uno nuevo.")
        return {}
    except Exception as e:
        logging.error(f"Error al cargar blocked_users.txt: {e}")
        return {}

# Función para guardar los usuarios bloqueados en un archivo
def save_blocked_users():
    try:
        with open("blocked_users.txt", "w") as file:
            for user_id, name in blocked_users.items():
                file.write(f"{name} - {user_id}\n")
            logging.info("Usuarios bloqueados guardados correctamente.")
    except Exception as e:
        logging.error(f"Error al guardar blocked_users.txt: {e}")
