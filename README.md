<h2 align="center">TeleSysBot - Bot de Gestión de Sistemas para Telegram</h2>

<h2 align="center">TeleSysBot</h2>

<p align="center">
  <a href="https://github.com/Jcorderop02/TeleSysBot/issues">
    <img alt="GitHub Issues" src="https://img.shields.io/github/issues/Jcorderop02/TeleSysBot?style=for-the-badge" />
  </a>
  <a href="https://github.com/Jcorderop02/TeleSysBot/pulls">
    <img alt="GitHub Pull Requests" src="https://img.shields.io/github/issues-pr/Jcorderop02/TeleSysBot?style=for-the-badge" />
  </a>
  <a href="https://github.com/Jcorderop02/TeleSysBot/blob/main/LICENSE">
    <img alt="License" src="https://img.shields.io/github/license/Jcorderop02/TeleSysBot?style=for-the-badge" />
  </a>
  <a href="https://www.python.org/">
    <img alt="Made with Python" src="https://img.shields.io/badge/Made%20with-Python-blue?style=for-the-badge" />
  </a>
  <a href="https://flask.palletsprojects.com/">
    <img alt="Flask" src="https://img.shields.io/badge/Flask-3.0.3-green?style=for-the-badge" />
  </a>
  <a href="https://core.telegram.org/bots">
    <img alt="Telegram" src="https://img.shields.io/badge/Telegram-Bot-blue?style=for-the-badge" />
  </a>
  <a href="#">
    <img alt="Status" src="https://img.shields.io/badge/status-active-success.svg?style=for-the-badge" />
  </a>
  <a href="#">
    <img alt="Version" src="https://img.shields.io/badge/version-1.0.0-orange?style=for-the-badge" />
  </a>
</p>

## Tabla de Contenidos

- [Introducción](#introducción)
- [Características](#características)
- [Instalación](#instalación)
- [Uso](#uso)
  - [Comandos de Telegram](#comandos-de-telegram)
  - [Interfaz Web](#interfaz-web)
- [Configuración](#configuración)
- [Contribuyendo](#contribuyendo)
- [Licencia](#licencia)

## Introducción

**TeleSysBot** es un versátil bot de Telegram diseñado para gestionar operaciones del sistema mediante comandos de Telegram. Además, cuenta con una interfaz web basada en Flask para monitorear y configurar el bot. Este proyecto tiene como objetivo proporcionar una interfaz fácil de usar para que los administradores de sistemas puedan gestionar y monitorear sus sistemas de manera eficiente.

## Características

- **Actualizaciones del Sistema**: Actualiza el sistema y Pi-hole.
- **Estadísticas del Sistema**: Consulta el uso de CPU, memoria, disco y carga del sistema.
- **Gestión de Contenedores**: Inicia, detén, reinicia y verifica el estado de los contenedores Docker.
- **Gestión de Usuarios**: Autentica usuarios, gestiona usuarios bloqueados.
- **Monitoreo del Sistema**: Monitorea el uso de recursos del sistema.

## Instalación

1. Clona el repositorio:
   ```bash
   git clone https://github.com/Jcorderop02/TeleSysBot.git
   cd TeleSysBot
2. Crea un entorno virtual e instala las dependencias:
   ```bash
   python3 -m venv botenv
   source botenv/bin/activate
   pip install -r requirements.txt
3. Configura las variables de entorno creando un archivo .env:
   ```bash
   TELEGRAM_BOT_TOKEN=<tu_token_de_telegram>
   TELEGRAM_BOT_PASSWORD=<tu_contraseña_de_bot>
   ADMIN_ID=<tu_id_de_telegram>
4. Ejecuta el bot:
   ```bash
   python3 telegram_bot.py
   
## Uso

### Comandos Disponibles

- `/start`: Inicia la interacción con el bot.
- `/password <tu contraseña>`: Autentica al usuario con la contraseña proporcionada.
- `/update`: Actualiza el sistema y Pi-hole.
- `/stats`: Muestra las estadísticas del sistema.
- `/unblock <user_id>`: Desbloquea a un usuario.
- `/blocked`: Muestra la lista de usuarios bloqueados.
- `/authenticated`: Muestra la lista de usuarios autenticados (solo admin).
- `/system_status`: Muestra el estado del sistema.
- `/start_container <nombre_contenedor>`: Inicia un contenedor Docker.
- `/stop_container <nombre_contenedor>`: Detiene un contenedor Docker.
- `/restart_container <nombre_contenedor>`: Reinicia un contenedor Docker.
- `/status_container <nombre_contenedor>`: Muestra el estado de un contenedor Docker.
- `/container_list`: Lista todos los contenedores y su estado.
- `/menu`: Muestra un menú interactivo con las opciones disponibles.
- `/dashboard`: Muestra un panel con las estadísticas del sistema.

### Configuración

Para habilitar o deshabilitar comandos, puedes modificar el archivo `config.json` en la raíz del proyecto. El archivo contiene una lista de comandos con valores booleanos que indican si están habilitados (`true`) o deshabilitados (`false`).

### Interfaz Web

El bot incluye una interfaz web que permite actualizar la configuración de los comandos. Para acceder a la interfaz, abre un navegador web y dirígete a `http://<tu_ip>:5000`.

### Notificaciones

El bot enviará notificaciones al administrador cuando ocurran ciertos eventos, como múltiples intentos fallidos de autenticación o alto uso de recursos del sistema.

## Contribuciones

¡Las contribuciones son bienvenidas! Si deseas contribuir a este proyecto, por favor sigue estos pasos:

1. Haz un fork del repositorio.
2. Crea una nueva rama (`git checkout -b feature/nueva-funcionalidad`).
3. Realiza tus cambios y commitea (`git commit -am 'Añadir nueva funcionalidad'`).
4. Haz push a la rama (`git push origin feature/nueva-funcionalidad`).
5. Abre un Pull Request.

## Licencia

Este proyecto está licenciado bajo la Licencia MIT. Consulta el archivo [LICENSE](LICENSE) para obtener más información.
