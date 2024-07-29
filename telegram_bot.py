# -*- coding: utf-8 -*-
import logging
import subprocess
import telegram
import psutil
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler
from dotenv import load_dotenv
import json
import os
import threading
from flask import Flask, render_template, request, redirect, url_for, flash

# Cargar variables de entorno desde el archivo .env
load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
PASSWORD = os.getenv('TELEGRAM_BOT_PASSWORD')
ADMIN_ID = int(os.getenv('ADMIN_ID'))

# Configuración del logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Set para rastrear usuarios autenticados
authenticated_users = set()

# Diccionario para rastrear intentos fallidos de contraseña
failed_attempts = {}

# Diccionario para rastrear usuarios bloqueados (ID y nombre de usuario)
blocked_users = {}

# Función para cargar la configuración de comandos habilitados desde config.json
def load_config():
    try:
        with open("config.json", "r") as file:
            config = json.load(file)
            logger.info("Configuración de comandos cargada correctamente.")
            return config
    except FileNotFoundError:
        logger.warning("El archivo config.json no existe. Se creará uno nuevo con todos los comandos habilitados.")
        default_config = {
            "update": True,
            "stats": True,
            "unblock": True,
            "blocked": True,
            "authenticated": True,
            "system_status": True,
            "start_container": True,
            "stop_container": True,
            "restart_container": True,
            "status_container": True,
            "container_list": True
        }
        save_command_config(default_config)
        return default_config
    except Exception as e:
        logger.error(f"Error al cargar config.json: {e}")
        return {}

def save_command_config(config):
    try:
        with open("config.json", "w") as file:
            json.dump(config, file, indent=4)
            logger.info("Configuración de comandos guardada correctamente.")
    except Exception as e:
        logger.error(f"Error al guardar config.json: {e}")

# Ruta para cargar la configuración
@app.route('/')
def index():
    config = load_config()
    return render_template('index.html', config=config)

# Ruta para actualizar la configuración
@app.route('/update_config', methods=['POST'])
def update_config():
    config = load_config()
    for command in config.keys():
        config[command] = request.form.get(command) == 'on'
    save_command_config(config)
    flash('Configuración actualizada correctamente.')
    return redirect(url_for('index'))

def is_command_enabled(command):
    config = load_config()
    return config.get(command, False)

# Función para cargar los usuarios autenticados desde un archivo
def load_authenticated_users():
    try:
        with open("authenticated_users.txt", "r") as file:
            users = file.read().splitlines()
            logger.info("Usuarios autenticados cargados correctamente.")
            return set(int(user) for user in users)
    except FileNotFoundError:
        logger.warning("El archivo authenticated_users.txt no existe. Se creará uno nuevo.")
        return set()

# Función para guardar los usuarios autenticados en un archivo
def save_authenticated_users():
    try:
        with open("authenticated_users.txt", "w") as file:
            for user in authenticated_users:
                file.write(f"{user}\n")
            logger.info("Usuarios autenticados guardados correctamente.")
    except Exception as e:
        logger.error(f"Error al guardar authenticated_users.txt: {e}")

# Función para cargar los usuarios bloqueados desde un archivo
def load_blocked_users():
    try:
        with open("blocked_users.txt", "r") as file:
            users = {}
            for line in file:
                name, user_id = line.strip().split(' - ')
                users[int(user_id)] = name
            logger.info("Usuarios bloqueados cargados correctamente.")
            return users
    except FileNotFoundError:
        logger.warning("El archivo blocked_users.txt no existe. Se creará uno nuevo.")
        return {}
    except Exception as e:
        logger.error(f"Error al cargar blocked_users.txt: {e}")
        return {}

# Función para guardar los usuarios bloqueados en un archivo
def save_blocked_users():
    try:
        with open("blocked_users.txt", "w") as file:
            for user_id, name in blocked_users.items():
                file.write(f"{name} - {user_id}\n")
            logger.info("Usuarios bloqueados guardados correctamente.")
    except Exception as e:
        logger.error(f"Error al guardar blocked_users.txt: {e}")

# Función para enviar notificaciones al administrador
async def notify_admin(message: str):
    bot = telegram.Bot(token=TOKEN)
    await bot.send_message(chat_id=ADMIN_ID, text=message, parse_mode='HTML')

# Cargar el estado de autenticación y bloqueos al iniciar el bot
authenticated_users = load_authenticated_users()
blocked_users = load_blocked_users()

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id in blocked_users:
        await update.message.reply_text('Estás bloqueado y no puedes usar este bot.')
        return

    if user_id not in authenticated_users:
        await update.message.reply_text('Por favor, ingresa la contraseña usando el comando /password <tu contraseña>.')
    else:
        await update.message.reply_text('🔐 ¡Bienvenido de vuelta! Usa /update para actualizar y /stats para ver las estadísticas.')

# Comando /password
async def password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    username = update.effective_user.username

    if user_id in blocked_users:
        await update.message.reply_text('Estás bloqueado y no puedes usar este bot.')
        return

    if len(context.args) == 0:
        await update.message.reply_text('Por favor, proporciona una contraseña. Usa: /password <tu contraseña>.')
        return

    input_password = context.args[0]

    if input_password == PASSWORD:
        authenticated_users.add(user_id)
        save_authenticated_users()
        if user_id in failed_attempts:
            del failed_attempts[user_id]
        await update.message.reply_text('👍 ¡Contraseña correcta! Ahora puedes usar los comandos habilitados en el bot.')
    else:
        failed_attempts[user_id] = failed_attempts.get(user_id, 0) + 1
        if failed_attempts[user_id] >= 3:
            blocked_users[user_id] = username
            save_blocked_users()
            await notify_admin(f'🚫 Usuario @{username} ({user_id}) ha sido bloqueado por múltiples intentos fallidos de contraseña.')
            await update.message.reply_text('🔒 Has sido bloqueado por ingresar la contraseña incorrecta tres veces.')
        else:
            await update.message.reply_text(f'😕 Contraseña incorrecta. Intentos fallidos: {failed_attempts[user_id]} de 3.')

# Comando /unblock para desbloquear usuarios
async def unblock(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_command_enabled("unblock"):
        await update.message.reply_text('⚠️ Este comando está desactivado.')
        return

    user_id = update.effective_user.id
    if user_id not in authenticated_users:
        await update.message.reply_text('Acceso denegado. Este comando es solo para usuarios autorizados.')
        return

    if len(context.args) == 0:
        await update.message.reply_text('Por favor, proporciona el ID del usuario a desbloquear. Usa: /unblock <user_id>.')
        return

    try:
        user_id_to_unblock = int(context.args[0])
        if user_id_to_unblock in blocked_users:
            del blocked_users[user_id_to_unblock]
            save_blocked_users()
            await update.message.reply_text(f'🔓 Usuario {user_id_to_unblock} desbloqueado.')
        else:
            await update.message.reply_text(f'❌ Usuario {user_id_to_unblock} no está bloqueado.')
    except ValueError:
        await update.message.reply_text('❌ ID de usuario inválido. Usa: /unblock <user_id>.')

# Comando /blocked para ver usuarios bloqueados
async def blocked(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback=False) -> None:
    if not is_command_enabled("blocked"):
        await update.message.reply_text('⚠️ Este comando está desactivado.')
        return

    user_id = update.effective_user.id if not from_callback else update.callback_query.from_user.id
    if user_id not in authenticated_users:
        await update.message.reply_text('Acceso denegado. Este comando es solo para usuarios autorizados.') if not from_callback else await update.callback_query.message.reply_text('Acceso denegado. Este comando es solo para usuarios autorizados.')
        return

    if not blocked_users:
        await update.message.reply_text('No hay usuarios bloqueados.') if not from_callback else await update.callback_query.message.reply_text('No hay usuarios bloqueados.')
    else:
        blocked_list = "\n".join(f"Usuario: @{username} - ID: {user_id}" for user_id, username in blocked_users.items())
        await update.message.reply_text(f'Usuarios bloqueados:\n{blocked_list}') if not from_callback else await update.callback_query.message.reply_text(f'Usuarios bloqueados:\n{blocked_list}')

# Comando /authenticated para ver usuarios autenticados
async def authenticated(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback=False) -> None:
    if not is_command_enabled("authenticated"):
        await update.message.reply_text('⚠️ Este comando está desactivado.')
        return

    user_id = update.effective_user.id if not from_callback else update.callback_query.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text('Acceso denegado. Este comando es solo para el administrador.') if not from_callback else await update.callback_query.message.reply_text('Acceso denegado. Este comando es solo para el administrador.')
        return

    if not authenticated_users:
        await update.message.reply_text('No hay usuarios autenticados.') if not from_callback else await update.callback_query.message.reply_text('No hay usuarios autenticados.')
    else:
        authenticated_list = "\n".join(f"ID: {user_id}" for user_id in authenticated_users)
        await update.message.reply_text(f'Usuarios autenticados:\n{authenticated_list}') if not from_callback else await update.callback_query.message.reply_text(f'Usuarios autenticados:\n{authenticated_list}')

# Comando /system_status para ver el estado del sistema
async def system_status(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback=False) -> None:
    if not is_command_enabled("system_status"):
        await update.message.reply_text('⚠️ Este comando está desactivado.')
        return

    user_id = update.effective_user.id if not from_callback else update.callback_query.from_user.id

    if user_id not in authenticated_users:
        await update.message.reply_text('Acceso denegado. Por favor, ingresa la contraseña usando /password <tu contraseña>.') if not from_callback else await update.callback_query.message.reply_text('Acceso denegado. Por favor, ingresa la contraseña usando /password <tu contraseña>.')
        return

    try:
        result = subprocess.run(['systemctl', 'status', '--no-pager', '--full'], capture_output=True, text=True, check=True)
        important_lines = []
        for line in result.stdout.split('\n'):
            if any(keyword in line for keyword in ['State:', 'Units:', 'Jobs:', 'Failed:', 'Since:', 'systemd:', 'CGroup:']):
                important_lines.append(line)
        filtered_output = '\n'.join(important_lines)
        if not filtered_output:
            filtered_output = "No se encontraron líneas relevantes en la salida de 'systemctl status'."
        await update.message.reply_text(f'<pre>{filtered_output}</pre>', parse_mode='HTML') if not from_callback else await update.callback_query.message.reply_text(f'<pre>{filtered_output}</pre>', parse_mode='HTML')
    except subprocess.CalledProcessError as e:
        logger.error(f"Error al obtener el estado del sistema: {e.stderr}")
        await update.message.reply_text('⚠️ Ocurrió un error al obtener el estado del sistema. Por favor, intenta de nuevo más tarde.') if not from_callback else await update.callback_query.message.reply_text('⚠️ Ocurrió un error al obtener el estado del sistema. Por favor, intenta de nuevo más tarde.')
    except Exception as e:
        logger.error(f"Error inesperado al obtener el estado del sistema: {str(e)}")
        await update.message.reply_text('⚠️ Ocurrió un error inesperado al obtener el estado del sistema. Por favor, intenta de nuevo más tarde.') if not from_callback else await update.callback_query.message.reply_text('⚠️ Ocurrió un error inesperado al obtener el estado del sistema. Por favor, intenta de nuevo más tarde.')

# Método que gestiona el comando /update
async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback=False) -> None:
    if not is_command_enabled("update"):
        await update.message.reply_text('⚠️ Este comando está desactivado.')
        return

    user_id = update.effective_user.id if not from_callback else update.callback_query.from_user.id

    if user_id in blocked_users:
        await update.message.reply_text('Estás bloqueado y no puedes usar este bot.') if not from_callback else await update.callback_query.message.reply_text('Estás bloqueado y no puedes usar este bot.')
        return

    if user_id not in authenticated_users:
        await update.message.reply_text('Acceso denegado. Por favor, ingresa la contraseña usando /password <tu contraseña>.') if not from_callback else await update.callback_query.message.reply_text('Acceso denegado. Por favor, ingresa la contraseña usando /password <tu contraseña>.')
        return

    try:
        await context.bot.send_message(chat_id=user_id, text='🔄 Actualizando el sistema en segundo plano...')
        await update_system(user_id)
    except subprocess.CalledProcessError as e:
        logger.error(f"Error en la actualización: {e.stderr.decode()}")
        await context.bot.send_message(chat_id=user_id, text='⚠️ Ocurrió un error durante la actualización. Por favor, intenta de nuevo más tarde.')
    except Exception as e:
        logger.error(f"Error inesperado en la actualización: {str(e)}")
        await context.bot.send_message(chat_id=user_id, text='⚠️ Ocurrió un error inesperado durante la actualización. Por favor, intenta de nuevo más tarde.')

# Comando /stats para ver las estadisticas de la Pi
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback=False) -> None:
    if not is_command_enabled("stats"):
        await update.message.reply_text('⚠️ Este comando está desactivado.')
        return

    user_id = update.effective_user.id if not from_callback else update.callback_query.from_user.id

    if user_id in blocked_users:
        await update.message.reply_text('Estás bloqueado y no puedes usar este bot.') if not from_callback else await update.callback_query.message.reply_text('Estás bloqueado y no puedes usar este bot.')
        return

    if user_id not in authenticated_users:
        await update.message.reply_text('Acceso denegado. Por favor, ingresa la contraseña usando /password <tu contraseña>.') if not from_callback else await update.callback_query.message.reply_text('Acceso denegado. Por favor, ingresa la contraseña usando /password <tu contraseña>.')
        return

    cpu_usage = psutil.cpu_percent(interval=1)
    mem_info = psutil.virtual_memory()
    disk_info = psutil.disk_usage('/')
    load_avg = psutil.getloadavg()

    # Obtener información de las particiones de disco
    partitions = psutil.disk_partitions()
    disk_usage_info = "\n".join(f"• {p.device}: {psutil.disk_usage(p.mountpoint).percent}%" for p in partitions)

    stats_message = (
        f"📊 <b>Estadísticas del Sistema</b>:\n"
        f"• Uso de CPU: {cpu_usage}%\n"
        f"• Uso de Memoria: {mem_info.percent}% (Total: {mem_info.total / (1024 ** 2):.2f} MB, Disponible: {mem_info.available / (1024 ** 2):.2f} MB)\n"
        f"• Uso de Disco: {disk_info.percent}% (Total: {disk_info.total / (1024 ** 2):.2f} MB)\n"
        f"• Carga del Sistema: {load_avg[0]} (1 min), {load_avg[1]} (5 min), {load_avg[2]} (15 min)\n"
        f"• Uso de Disco por Partición:\n{disk_usage_info}\n"
    )

    await update.message.reply_text(stats_message, parse_mode='HTML') if not from_callback else await update.callback_query.message.reply_text(stats_message, parse_mode='HTML')

# Comando /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_message = "Aquí tienes los comandos disponibles:\n"
    commands = {
        "update": "/update - Actualizar el sistema y Pi-hole\n",
        "stats": "/stats - Ver estadísticas del sistema\n",
        "unblock": "/unblock <user_id> - Desbloquear a un usuario\n",
        "blocked": "/blocked - Ver la lista de usuarios bloqueados\n",
        "authenticated": "/authenticated - Ver la lista de usuarios autenticados (solo admin)\n",
        "system_status": "/system_status - Ver el estado del sistema\n",
        "start_container": "/start_container <nombre_contenedor> - Iniciar un contenedor Docker\n",
        "stop_container": "/stop_container <nombre_contenedor> - Detener un contenedor Docker\n",
        "restart_container": "/restart_container <nombre_contenedor> - Reiniciar un contenedor Docker\n",
        "status_container": "/status_container <nombre_contenedor> - Ver el estado de un contenedor Docker\n",
        "container_list": "/container_list - Listar todos los contenedores y su estado\n",
        "help": "/help - Mostrar esta ayuda\n"
    }
    for command, description in commands.items():
        if is_command_enabled(command):
            help_message += description
    await update.message.reply_text(help_message)

# Metodo que se ejecuta dentro del /update 
def check_updates():
    subprocess.run(['sudo', 'apt-get', 'update'], capture_output=True, text=True)

    upgrade_output = subprocess.run(['sudo', 'apt-get', 'upgrade', '-s'], capture_output=True, text=True)

    upgrade_lines = upgrade_output.stdout.splitlines()
    packages_to_upgrade = []

    for line in upgrade_lines:
        if line.startswith("Inst") or line.startswith("Conf"):
            packages_to_upgrade.append(line)

    return packages_to_upgrade

# Metodo que se ejecuta dentro del /update 
def check_pihole_update():
    pihole_output = subprocess.run(['pihole', '-up'], capture_output=True, text=True)
    return pihole_output.stdout

async def send_message(user_id, message):
    bot = telegram.Bot(token=TOKEN)
    await bot.send_message(chat_id=user_id, text=message, parse_mode='HTML')

# Metodo /update para actualizar el sistema
async def update_system(user_id):
    packages_to_upgrade = check_updates()

    if packages_to_upgrade:
        packages_message = "\n".join(f"• {pkg}" for pkg in packages_to_upgrade)
    else:
        packages_message = "• No hay actualizaciones de paquetes"

    # Ejecutar la actualización de Pi-hole
    pihole_output_text = check_pihole_update()

    # Verificar si Pi-hole se actualizó
    if "Everything is up to date!" in pihole_output_text:
        pihole_message = "• Pi-hole está actualizado."
    else:
        pihole_message = "• Pi-hole se ha actualizado."

    # Enviar el mensaje inicial
    final_message = (
        f"<b>Actualización del Sistema</b>:\n"
        f"{packages_message}\n\n"
        f"<b>Actualización de Pi-hole</b>:\n"
        f"{pihole_message}"
    )
    await send_message(user_id, final_message)

    # Aplicar las actualizaciones solo si hay actualizaciones de paquetes
    if packages_to_upgrade or "Everything is up to date!" not in pihole_output_text:
        try:
            subprocess.run(['sudo', 'apt-get', 'upgrade', '-y'], check=True)
            await send_message(user_id, '✅ Las actualizaciones del sistema se han aplicado correctamente.')
        except subprocess.CalledProcessError as e:
            logger.error(f"Error al aplicar actualizaciones del sistema: {str(e)}")
            await send_message(user_id, '⚠️ Ocurrió un error al aplicar actualizaciones del sistema.')
    else:
        logger.info("No hay actualizaciones de paquetes ni de Pi-hole.")

# Función para monitorear el uso de recursos
async def monitor_resources():
    while True:
        cpu_usage = psutil.cpu_percent(interval=1)
        mem_info = psutil.virtual_memory()
        disk_info = psutil.disk_usage('/')
        
        if cpu_usage > 80:
            await notify_admin(f'⚠️ Uso de CPU alto: {cpu_usage}%')
        if mem_info.percent > 80:
            await notify_admin(f'⚠️ Uso de Memoria alto: {mem_info.percent}%')
        if disk_info.percent > 80:
            await notify_admin(f'⚠️ Uso de Disco alto: {disk_info.percent}%')
        
        await asyncio.sleep(60)  # Monitorea cada minuto

# Comando /start_container para iniciar un contenedor específico
async def start_container(update: Update, context: ContextTypes.DEFAULT_TYPE, container_name=None, from_callback=False) -> None:
    if not is_command_enabled("start_container"):
        await update.message.reply_text('⚠️ Este comando está desactivado.')
        return

    user_id = update.effective_user.id if not from_callback else update.callback_query.from_user.id
    if user_id not in authenticated_users:
        if from_callback:
            await update.callback_query.message.reply_text('Acceso denegado. Solo los usuarios autenticados pueden usar este comando.')
        else:
            await update.message.reply_text('Acceso denegado. Solo los usuarios autenticados pueden usar este comando.')
        return

    if container_name is None:
        if len(context.args) == 0:
            if from_callback:
                await update.callback_query.message.reply_text('Por favor, proporciona el nombre del contenedor.')
            else:
                await update.message.reply_text('Por favor, proporciona el nombre del contenedor. Usa: /start_container <nombre_contenedor>.')
            return
        container_name = context.args[0]

    try:
        subprocess.run(['sudo', 'docker', 'start', container_name], check=True)
        if from_callback:
            await update.callback_query.message.reply_text(f'🔄 El contenedor {container_name} se está iniciando...')
        else:
            await update.message.reply_text(f'🔄 El contenedor {container_name} se está iniciando...')

        # Verificar si el contenedor se ha iniciado
        while True:
            result = subprocess.run(['sudo', 'docker', 'ps', '--filter', f'name={container_name}', '--filter', 'status=running', '--format', '{{.Names}}: {{.Status}}'], capture_output=True, text=True)
            if container_name in result.stdout:
                if from_callback:
                    await update.callback_query.message.reply_text(f'✅ El contenedor {container_name} se ha iniciado por completo.')
                else:
                    await update.message.reply_text(f'✅ El contenedor {container_name} se ha iniciado por completo.')
                break
            await asyncio.sleep(1)  # Espera un segundo antes de verificar nuevamente

    except subprocess.CalledProcessError as e:
        logger.error(f"Error al iniciar el contenedor {container_name}: {str(e)}")
        if from_callback:
            await update.callback_query.message.reply_text(f'⚠️ Ocurrió un error al intentar iniciar el contenedor {container_name}.')
        else:
            await update.message.reply_text(f'⚠️ Ocurrió un error al intentar iniciar el contenedor {container_name}.')
    except Exception as e:
        logger.error(f"Error inesperado al iniciar el contenedor {container_name}: {str(e)}")
        if from_callback:
            await update.callback_query.message.reply_text(f'⚠️ Ocurrió un error inesperado al intentar iniciar el contenedor {container_name}.')
        else:
            await update.message.reply_text(f'⚠️ Ocurrió un error inesperado al intentar iniciar el contenedor {container_name}.')

# Comando /stop_container para detener un contenedor específico
async def stop_container(update: Update, context: ContextTypes.DEFAULT_TYPE, container_name=None, from_callback=False) -> None:
    if not is_command_enabled("stop_container"):
        await update.message.reply_text('⚠️ Este comando está desactivado.')
        return

    user_id = update.effective_user.id if not from_callback else update.callback_query.from_user.id
    if user_id not in authenticated_users:
        if from_callback:
            await update.callback_query.message.reply_text('Acceso denegado. Solo los usuarios autenticados pueden usar este comando.')
        else:
            await update.message.reply_text('Acceso denegado. Solo los usuarios autenticados pueden usar este comando.')
        return

    if container_name is None:
        if len(context.args) == 0:
            if from_callback:
                await update.callback_query.message.reply_text('Por favor, proporciona el nombre del contenedor.')
            else:
                await update.message.reply_text('Por favor, proporciona el nombre del contenedor. Usa: /stop_container <nombre_contenedor>.')
            return
        container_name = context.args[0]

    try:
        subprocess.run(['sudo', 'docker', 'stop', container_name], check=True)
        if from_callback:
            await update.callback_query.message.reply_text(f'🔄 El contenedor {container_name} se está deteniendo...')
        else:
            await update.message.reply_text(f'🔄 El contenedor {container_name} se está deteniendo...')

        # Verificar si el contenedor se ha detenido
        while True:
            result = subprocess.run(['sudo', 'docker', 'ps', '-a', '--filter', f'name={container_name}', '--filter', 'status=exited', '--format', '{{.Names}}: {{.Status}}'], capture_output=True, text=True)
            if container_name in result.stdout:
                if from_callback:
                    await update.callback_query.message.reply_text(f'✅ El contenedor {container_name} se ha detenido por completo.')
                else:
                    await update.message.reply_text(f'✅ El contenedor {container_name} se ha detenido por completo.')
                break
            await asyncio.sleep(1)

    except subprocess.CalledProcessError as e:
        logger.error(f"Error al detener el contenedor {container_name}: {str(e)}")
        if from_callback:
            await update.callback_query.message.reply_text(f'⚠️ Ocurrió un error al intentar detener el contenedor {container_name}.')
        else:
            await update.message.reply_text(f'⚠️ Ocurrió un error al intentar detener el contenedor {container_name}.')
    except Exception as e:
        logger.error(f"Error inesperado al detener el contenedor {container_name}: {str(e)}")
        if from_callback:
            await update.callback_query.message.reply_text(f'⚠️ Ocurrió un error inesperado al intentar detener el contenedor {container_name}.')
        else:
            await update.message.reply_text(f'⚠️ Ocurrió un error inesperado al intentar detener el contenedor {container_name}.')

# Comando /restart_container para reiniciar un contenedor específico
async def restart_container(update: Update, context: ContextTypes.DEFAULT_TYPE, container_name=None, from_callback=False) -> None:
    if not is_command_enabled("restart_container"):
        await update.message.reply_text('⚠️ Este comando está desactivado.')
        return

    user_id = update.effective_user.id if not from_callback else update.callback_query.from_user.id
    if user_id not in authenticated_users:
        if from_callback:
            await update.callback_query.message.reply_text('Acceso denegado. Solo los usuarios autenticados pueden usar este comando.')
        else:
            await update.message.reply_text('Acceso denegado. Solo los usuarios autenticados pueden usar este comando.')
        return

    if container_name is None:
        if len(context.args) == 0:
            if from_callback:
                await update.callback_query.message.reply_text('Por favor, proporciona el nombre del contenedor.')
            else:
                await update.message.reply_text('Por favor, proporciona el nombre del contenedor. Usa: /restart_container <nombre_contenedor>.')
            return
        container_name = context.args[0]

    try:
        subprocess.run(['sudo', 'docker', 'restart', container_name], check=True)
        if from_callback:
            await update.callback_query.message.reply_text(f'🔄 El contenedor {container_name} se está reiniciando...')
        else:
            await update.message.reply_text(f'🔄 El contenedor {container_name} se está reiniciando...')

        # Verificar si el contenedor se ha reiniciado
        while True:
            result = subprocess.run(['sudo', 'docker', 'ps', '--filter', f'name={container_name}', '--filter', 'status=running', '--format', '{{.Names}}: {{.Status}}'], capture_output=True, text=True)
            if container_name in result.stdout:
                if from_callback:
                    await update.callback_query.message.reply_text(f'✅ El contenedor {container_name} se ha reiniciado por completo.')
                else:
                    await update.message.reply_text(f'✅ El contenedor {container_name} se ha reiniciado por completo.')
                break
            await asyncio.sleep(1) 

    except subprocess.CalledProcessError as e:
        logger.error(f"Error al reiniciar el contenedor {container_name}: {str(e)}")
        if from_callback:
            await update.callback_query.message.reply_text(f'⚠️ Ocurrió un error al intentar reiniciar el contenedor {container_name}.')
        else:
            await update.message.reply_text(f'⚠️ Ocurrió un error al intentar reiniciar el contenedor {container_name}.')
    except Exception as e:
        logger.error(f"Error inesperado al reiniciar el contenedor {container_name}: {str(e)}")
        if from_callback:
            await update.callback_query.message.reply_text(f'⚠️ Ocurrió un error inesperado al intentar reiniciar el contenedor {container_name}.')
        else:
            await update.message.reply_text(f'⚠️ Ocurrió un error inesperado al intentar reiniciar el contenedor {container_name}.')

# Comando /status_container para consultar el estado de un contenedor específico
async def status_container(update: Update, context: ContextTypes.DEFAULT_TYPE, container_name=None, from_callback=False) -> None:
    if not is_command_enabled("status_container"):
        await update.message.reply_text('⚠️ Este comando está desactivado.')
        return

    user_id = update.effective_user.id if not from_callback else update.callback_query.from_user.id
    if user_id not in authenticated_users:
        if from_callback:
            await update.callback_query.message.reply_text('Acceso denegado. Solo los usuarios autenticados pueden usar este comando.')
        else:
            await update.message.reply_text('Acceso denegado. Solo los usuarios autenticados pueden usar este comando.')
        return

    if container_name is None:
        if len(context.args) == 0:
            if from_callback:
                await update.callback_query.message.reply_text('Por favor, proporciona el nombre del contenedor.')
            else:
                await update.message.reply_text('Por favor, proporciona el nombre del contenedor. Usa: /status_container <nombre_contenedor>.')
            return
        container_name = context.args[0]

    try:
        result = subprocess.run(['sudo', 'docker', 'ps', '--filter', f'name={container_name}', '--format', '{{.Names}}: {{.Status}}'], capture_output=True, text=True, check=True)
        status = result.stdout.strip()
        if status:
            formatted_status = '\n'.join([f'• {line}' for line in status.split('\n')])
            if from_callback:
                await update.callback_query.message.reply_text(f'🔍 <b>Estado del contenedor {container_name}:</b>\n{formatted_status}', parse_mode='HTML')
            else:
                await update.message.reply_text(f'🔍 <b>Estado del contenedor {container_name}:</b>\n{formatted_status}', parse_mode='HTML')
        else:
            if from_callback:
                await update.callback_query.message.reply_text(f'⚠️ No se encontró ningún contenedor con el nombre {container_name}.')
            else:
                await update.message.reply_text(f'⚠️ No se encontró ningún contenedor con el nombre {container_name}.')
    except subprocess.CalledProcessError as e:
        logger.error(f"Error al consultar el estado del contenedor {container_name}: {e.stderr}")
        if from_callback:
            await update.callback_query.message.reply_text(f'⚠️ Ocurrió un error al intentar consultar el estado del contenedor {container_name}.')
        else:
            await update.message.reply_text(f'⚠️ Ocurrió un error al intentar consultar el estado del contenedor {container_name}.')
    except Exception as e:
        logger.error(f"Error inesperado al consultar el estado del contenedor {container_name}: {str(e)}")
        if from_callback:
            await update.callback_query.message.reply_text(f'⚠️ Ocurrió un error inesperado al consultar el estado del contenedor {container_name}.')
        else:
            await update.message.reply_text(f'⚠️ Ocurrió un error inesperado al consultar el estado del contenedor {container_name}.')

# Comando /container_list para listar todos los contenedores y su estado
async def container_list(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback=False) -> None:
    if not is_command_enabled("container_list"):
        await update.message.reply_text('⚠️ Este comando está desactivado.')
        return

    user_id = update.effective_user.id if not from_callback else update.callback_query.from_user.id
    if user_id not in authenticated_users:
        await update.message.reply_text('Acceso denegado. Solo los usuarios autenticados pueden usar este comando.') if not from_callback else await update.callback_query.message.reply_text('Acceso denegado. Solo los usuarios autenticados pueden usar este comando.')
        return

    try:
        result = subprocess.run(['sudo', 'docker', 'ps', '-a', '--format', '{{.Names}}: {{.Status}}'], capture_output=True, text=True, check=True)
        containers = result.stdout.strip().split('\n')
        if containers:
            formatted_containers = '\n'.join([f'• {container}' for container in containers])
            await update.message.reply_text(f'🔍 <b>Lista de contenedores:</b>\n{formatted_containers}', parse_mode='HTML') if not from_callback else await update.callback_query.message.reply_text(f'🔍 <b>Lista de contenedores:</b>\n{formatted_containers}', parse_mode='HTML')
        else:
            await update.message.reply_text('⚠️ No se encontraron contenedores.') if not from_callback else await update.callback_query.message.reply_text('⚠️ No se encontraron contenedores.')
    except subprocess.CalledProcessError as e:
        logger.error(f"Error al listar los contenedores: {e.stderr}")
        await update.message.reply_text('⚠️ Ocurrió un error al intentar listar los contenedores.') if not from_callback else await update.callback_query.message.reply_text('⚠️ Ocurrió un error al intentar listar los contenedores.')
    except Exception as e:
        logger.error(f"Error inesperado al listar los contenedores: {str(e)}")
        await update.message.reply_text('⚠️ Ocurrió un error inesperado al listar los contenedores.') if not from_callback else await update.callback_query.message.reply_text('⚠️ Ocurrió un error inesperado al listar los contenedores.')

# Comando /menu para mostrar un menú interactivo
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = []
    if is_command_enabled("update"):
        keyboard.append([InlineKeyboardButton("Actualizar Sistema", callback_data='update')])
    if is_command_enabled("stats"):
        keyboard.append([InlineKeyboardButton("Ver Estadísticas", callback_data='stats')])
    if is_command_enabled("system_status"):
        keyboard.append([InlineKeyboardButton("Verificar Estado del Sistema", callback_data='system_status')])
    keyboard.append([InlineKeyboardButton("Ver Dashboards", callback_data='dashboard')])
    if is_command_enabled("start_container"):
        keyboard.append([InlineKeyboardButton("Iniciar Contenedor", callback_data='start_container_menu')])
    if is_command_enabled("stop_container"):
        keyboard.append([InlineKeyboardButton("Detener Contenedor", callback_data='stop_container_menu')])
    if is_command_enabled("restart_container"):
        keyboard.append([InlineKeyboardButton("Reiniciar Contenedor", callback_data='restart_container_menu')])
    if is_command_enabled("status_container"):
        keyboard.append([InlineKeyboardButton("Estado del Contenedor", callback_data='status_container_menu')])
    if is_command_enabled("container_list"):
        keyboard.append([InlineKeyboardButton("Lista de Contenedores", callback_data='container_list')])
    if is_command_enabled("blocked"):
        keyboard.append([InlineKeyboardButton("Usuarios Bloqueados", callback_data='blocked')])
    if is_command_enabled("authenticated"):
        keyboard.append([InlineKeyboardButton("Usuarios Autenticados", callback_data='authenticated')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Por favor, selecciona una opción:', reply_markup=reply_markup)

# Comando /start_container_menu para mostrar un menú de contenedores disponibles
async def start_container_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback=False) -> None:
    if not is_command_enabled("start_container"):
        await update.message.reply_text('⚠️ Este comando está desactivado.')
        return

    user_id = update.effective_user.id if not from_callback else update.callback_query.from_user.id
    if user_id not in authenticated_users:
        if from_callback:
            await update.callback_query.message.reply_text('Acceso denegado. Solo los usuarios autenticados pueden usar este comando.')
        else:
            await update.message.reply_text('Acceso denegado. Solo los usuarios autenticados pueden usar este comando.')
        return

    try:
        result = subprocess.run(['sudo', 'docker', 'ps', '-a', '--format', '{{.Names}}'], capture_output=True, text=True, check=True)
        containers = result.stdout.strip().split('\n')
        if containers:
            keyboard = [[InlineKeyboardButton(container, callback_data=f'start_{container}')] for container in containers]
            reply_markup = InlineKeyboardMarkup(keyboard)
            if from_callback:
                await update.callback_query.message.reply_text('Selecciona el contenedor que deseas iniciar:', reply_markup=reply_markup)
            else:
                await update.message.reply_text('Selecciona el contenedor que deseas iniciar:', reply_markup=reply_markup)
        else:
            if from_callback:
                await update.callback_query.message.reply_text('⚠️ No se encontraron contenedores.')
            else:
                await update.message.reply_text('⚠️ No se encontraron contenedores.')
    except subprocess.CalledProcessError as e:
        logger.error(f"Error al listar los contenedores: {e.stderr}")
        if from_callback:
            await update.callback_query.message.reply_text('⚠️ Ocurrió un error al intentar listar los contenedores.')
        else:
            await update.message.reply_text('⚠️ Ocurrió un error al intentar listar los contenedores.')
    except Exception as e:
        logger.error(f"Error inesperado al listar los contenedores: {str(e)}")
        if from_callback:
            await update.callback_query.message.reply_text('⚠️ Ocurrió un error inesperado al listar los contenedores.')
        else:
            await update.message.reply_text('⚠️ Ocurrió un error inesperado al listar los contenedores.')

# Comando /stop_container_menu para mostrar un menú de contenedores disponibles para detener
async def stop_container_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback=False) -> None:
    if not is_command_enabled("stop_container"):
        await update.message.reply_text('⚠️ Este comando está desactivado.')
        return

    user_id = update.effective_user.id if not from_callback else update.callback_query.from_user.id
    if user_id not in authenticated_users:
        if from_callback:
            await update.callback_query.message.reply_text('Acceso denegado. Solo los usuarios autenticados pueden usar este comando.')
        else:
            await update.message.reply_text('Acceso denegado. Solo los usuarios autenticados pueden usar este comando.')
        return

    try:
        result = subprocess.run(['sudo', 'docker', 'ps', '--format', '{{.Names}}'], capture_output=True, text=True, check=True)
        containers = result.stdout.strip().split('\n')
        if containers:
            keyboard = [[InlineKeyboardButton(container, callback_data=f'stop_{container}')] for container in containers]
            reply_markup = InlineKeyboardMarkup(keyboard)
            if from_callback:
                await update.callback_query.message.reply_text('Selecciona el contenedor que deseas detener:', reply_markup=reply_markup)
            else:
                await update.message.reply_text('Selecciona el contenedor que deseas detener:', reply_markup=reply_markup)
        else:
            if from_callback:
                await update.callback_query.message.reply_text('⚠️ No se encontraron contenedores.')
            else:
                await update.message.reply_text('⚠️ No se encontraron contenedores.')
    except subprocess.CalledProcessError as e:
        logger.error(f"Error al listar los contenedores: {e.stderr}")
        if from_callback:
            await update.callback_query.message.reply_text('⚠️ Ocurrió un error al intentar listar los contenedores.')
        else:
            await update.message.reply_text('⚠️ Ocurrió un error al intentar listar los contenedores.')
    except Exception as e:
        logger.error(f"Error inesperado al listar los contenedores: {str(e)}")
        if from_callback:
            await update.callback_query.message.reply_text('⚠️ Ocurrió un error inesperado al listar los contenedores.')
        else:
            await update.message.reply_text('⚠️ Ocurrió un error inesperado al listar los contenedores.')

# Comando /restart_container_menu para mostrar un menú de contenedores disponibles para reiniciar
async def restart_container_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback=False) -> None:
    if not is_command_enabled("restart_container"):
        await update.message.reply_text('⚠️ Este comando está desactivado.')
        return

    user_id = update.effective_user.id if not from_callback else update.callback_query.from_user.id
    if user_id not in authenticated_users:
        if from_callback:
            await update.callback_query.message.reply_text('Acceso denegado. Solo los usuarios autenticados pueden usar este comando.')
        else:
            await update.message.reply_text('Acceso denegado. Solo los usuarios autenticados pueden usar este comando.')
        return

    try:
        result = subprocess.run(['sudo', 'docker', 'ps', '--format', '{{.Names}}'], capture_output=True, text=True, check=True)
        containers = result.stdout.strip().split('\n')
        if containers:
            keyboard = [[InlineKeyboardButton(container, callback_data=f'restart_{container}')] for container in containers]
            reply_markup = InlineKeyboardMarkup(keyboard)
            if from_callback:
                await update.callback_query.message.reply_text('Selecciona el contenedor que deseas reiniciar:', reply_markup=reply_markup)
            else:
                await update.message.reply_text('Selecciona el contenedor que deseas reiniciar:', reply_markup=reply_markup)
        else:
            if from_callback:
                await update.callback_query.message.reply_text('⚠️ No se encontraron contenedores.')
            else:
                await update.message.reply_text('⚠️ No se encontraron contenedores.')
    except subprocess.CalledProcessError as e:
        logger.error(f"Error al listar los contenedores: {e.stderr}")
        if from_callback:
            await update.callback_query.message.reply_text('⚠️ Ocurrió un error al intentar listar los contenedores.')
        else:
            await update.message.reply_text('⚠️ Ocurrió un error al intentar listar los contenedores.')
    except Exception as e:
        logger.error(f"Error inesperado al listar los contenedores: {str(e)}")
        if from_callback:
            await update.callback_query.message.reply_text('⚠️ Ocurrió un error inesperado al listar los contenedores.')
        else:
            await update.message.reply_text('⚠️ Ocurrió un error inesperado al listar los contenedores.')

# Comando /status_container_menu para mostrar un menú de contenedores disponibles para consultar estado
async def status_container_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback=False) -> None:
    if not is_command_enabled("status_container"):
        await update.message.reply_text('⚠️ Este comando está desactivado.')
        return

    user_id = update.effective_user.id if not from_callback else update.callback_query.from_user.id
    if user_id not in authenticated_users:
        if from_callback:
            await update.callback_query.message.reply_text('Acceso denegado. Solo los usuarios autenticados pueden usar este comando.')
        else:
            await update.message.reply_text('Acceso denegado. Solo los usuarios autenticados pueden usar este comando.')
        return

    try:
        result = subprocess.run(['sudo', 'docker', 'ps', '-a', '--format', '{{.Names}}'], capture_output=True, text=True, check=True)
        containers = result.stdout.strip().split('\n')
        if containers:
            keyboard = [[InlineKeyboardButton(container, callback_data=f'status_{container}')] for container in containers]
            reply_markup = InlineKeyboardMarkup(keyboard)
            if from_callback:
                await update.callback_query.message.reply_text('Selecciona el contenedor que deseas consultar:', reply_markup=reply_markup)
            else:
                await update.message.reply_text('Selecciona el contenedor que deseas consultar:', reply_markup=reply_markup)
        else:
            if from_callback:
                await update.callback_query.message.reply_text('⚠️ No se encontraron contenedores.')
            else:
                await update.message.reply_text('⚠️ No se encontraron contenedores.')
    except subprocess.CalledProcessError as e:
        logger.error(f"Error al listar los contenedores: {e.stderr}")
        if from_callback:
            await update.callback_query.message.reply_text('⚠️ Ocurrió un error al intentar listar los contenedores.')
        else:
            await update.message.reply_text('⚠️ Ocurrió un error al intentar listar los contenedores.')
    except Exception as e:
        logger.error(f"Error inesperado al listar los contenedores: {str(e)}")
        if from_callback:
            await update.callback_query.message.reply_text('⚠️ Ocurrió un error inesperado al listar los contenedores.')
        else:
            await update.message.reply_text('⚠️ Ocurrió un error inesperado al listar los contenedores.')

# Función para manejar los botones del menú
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    command = query.data

    if command == 'update':
        await update_command(update, context, from_callback=True)
    elif command == 'stats':
        await stats(update, context, from_callback=True)
    elif command == 'system_status':
        await system_status(update, context, from_callback=True)
    elif command == 'dashboard':
        await dashboard(update, context, from_callback=True)
    elif command == 'container_list':
        await container_list(update, context, from_callback=True)
    elif command == 'blocked':
        await blocked(update, context, from_callback=True)
    elif command == 'authenticated':
        await authenticated(update, context, from_callback=True)
    elif command == 'start_container_menu':
        await start_container_menu(update, context, from_callback=True)
    elif command == 'stop_container_menu':
        await stop_container_menu(update, context, from_callback=True)
    elif command == 'restart_container_menu':
        await restart_container_menu(update, context, from_callback=True)
    elif command == 'status_container_menu':
        await status_container_menu(update, context, from_callback=True)
    elif command.startswith('start_'):
        container_name = command.split('_', 1)[1]
        await start_container(update, context, container_name=container_name, from_callback=True)
    elif command.startswith('stop_'):
        container_name = command.split('_', 1)[1]
        await stop_container(update, context, container_name=container_name, from_callback=True)
    elif command.startswith('restart_'):
        container_name = command.split('_', 1)[1]
        await restart_container(update, context, container_name=container_name, from_callback=True)
    elif command.startswith('status_'):
        container_name = command.split('_', 1)[1]
        await status_container(update, context, container_name=container_name, from_callback=True)

# Funcion para enseñar el dashboard
async def dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback=False) -> None:
    if from_callback:
        user_id = update.callback_query.from_user.id
    else:
        user_id = update.effective_user.id

    if user_id not in authenticated_users:
        await update.message.reply_text('Acceso denegado. Solo los usuarios autenticados pueden usar este comando.') if not from_callback else await update.callback_query.message.reply_text('Acceso denegado. Solo los usuarios autenticados pueden usar este comando.')
        return

    # Obtener estadísticas del sistema
    cpu_usage = psutil.cpu_percent(interval=1)
    mem_info = psutil.virtual_memory()
    disk_info = psutil.disk_usage('/')

    # Obtener estado de los contenedores Docker
    result = subprocess.run(['sudo', 'docker', 'ps', '-a', '--format', '{{.Names}}: {{.Status}}'], capture_output=True, text=True)
    containers = result.stdout.strip().split('\n')
    formatted_containers = '\n'.join([f'• {container}' for container in containers])

    # Crear el mensaje del dashboard
    dashboard_message = (
        f"<b>📊 Dashboard del Sistema</b>\n\n"
        f"<b>Uso de CPU:</b> {cpu_usage}%\n"
        f"<b>Uso de Memoria:</b> {mem_info.percent}%\n"
        f"<b>Uso de Disco:</b> {disk_info.percent}%\n\n"
        f"<b>Contenedores Docker:</b>\n{formatted_containers}"
    )

    await update.message.reply_text(dashboard_message, parse_mode='HTML') if not from_callback else await update.callback_query.message.reply_text(dashboard_message, parse_mode='HTML')

# Ejecutar la monitorización en el fondo
async def post_init(application):
    asyncio.create_task(monitor_resources())

def main() -> None:
    # Iniciar el bot
    application = ApplicationBuilder().token(TOKEN).post_init(post_init).build()

    # Registrar los comandos
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("password", password))
    application.add_handler(CommandHandler("update", update_command))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("unblock", unblock))
    application.add_handler(CommandHandler("blocked", blocked))
    application.add_handler(CommandHandler("authenticated", authenticated))
    application.add_handler(CommandHandler("system_status", system_status))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("start_container", start_container))
    application.add_handler(CommandHandler("stop_container", stop_container))
    application.add_handler(CommandHandler("restart_container", restart_container))
    application.add_handler(CommandHandler("status_container", status_container))
    application.add_handler(CommandHandler("container_list", container_list))
    application.add_handler(CommandHandler("menu", menu))  # Comando para mostrar el menú interactivo
    application.add_handler(CommandHandler("dashboard", dashboard))  # Comando para mostrar el dashboard
    application.add_handler(CallbackQueryHandler(button))  # Manejador de botones del menú

    # Iniciar Flask en un hilo separado
    threading.Thread(target=run_flask).start()

    # Iniciar el bot
    application.run_polling()

def run_flask():
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5000)

if __name__ == '__main__':
    main()