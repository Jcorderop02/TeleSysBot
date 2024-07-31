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
    <img alt="Version" src="https://img.shields.io/badge/version-1.0.1-orange?style=for-the-badge" />
  </a>
</p>

## Tabla de Contenidos

- [Introducción](#introducción)
- [Características](#características)
- [Requisitos del Sistema](#requisitos-del-sistema)
- [Instalación](#instalación)
- [Uso](#uso)
  - [Comandos Disponibles](#comandos-disponibles)
  - [Configuración](#configuración)
  - [Interfaz Web](#interfaz-web)
- [Notificaciones](#notificaciones)
- [Arquitectura del Proyecto](#arquitectura-del-proyecto)
- [Changelog](#changelog)
- [Contribuciones](#contribuciones)
- [Licencia](#licencia)

## Introducción

**TeleSysBot** es un versátil bot de Telegram diseñado para gestionar operaciones del sistema mediante comandos de Telegram. Además, cuenta con una interfaz web basada en Flask para monitorear y configurar el bot. Este proyecto tiene como objetivo proporcionar una interfaz fácil de usar para que los administradores de sistemas puedan gestionar y monitorear sus sistemas de manera eficiente.

## Características

- **Actualizaciones del Sistema**: Actualiza el sistema y Pi-hole.
- **Estadísticas del Sistema**: Consulta el uso de CPU, memoria, disco y carga del sistema.
- **Gestión de Contenedores**: Inicia, detén, reinicia y verifica el estado de los contenedores Docker.
- **Gestión de Usuarios**: Autentica usuarios, gestiona usuarios bloqueados.
- **Monitoreo del Sistema**: Monitorea el uso de recursos del sistema.
- **Dashboard en Tiempo Real**: Muestra estadísticas del sistema con actualización automática.
- **Modo Oscuro/Claro**: Alterna entre tema oscuro y claro en la interfaz web.

## Requisitos del Sistema

- Python 3.8 o superior
- Docker (para la gestión de contenedores) (opcional)
- Dependencias adicionales listadas en `requirements.txt`

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

## Arquitectura del Proyecto

- **telegram_bot.py**: Contiene la lógica principal del bot de Telegram.
- **shared.py**: Módulo compartido para gestionar usuarios autenticados y bloqueados.
- **app.py**: Configuración de la aplicación Flask.
- **templates/**: Directorio que contiene las plantillas HTML para la interfaz web.

## Changelog

### Versión 1.0.1

#### Nuevas Características

- **Dashboard en Tiempo Real**: Añadido soporte para mostrar estadísticas del sistema en tiempo real en la interfaz web.
- **Modo Oscuro/Claro**: Implementación de la funcionalidad para alternar entre modo oscuro y claro en la interfaz web.

#### Mejoras

- **Refactorización del Código**:
  - Modularización del código: Creación de `shared.py` para gestionar usuarios autenticados y bloqueados de forma centralizada.
  - Eliminación de dependencias de HTML y Flask desde `telegram_bot.py`.

- **Interfaz Web**:
  - Actualización de la plantilla `base.html` para incluir el soporte de modo oscuro/claro.
  - Creación de `templates/dashboard.html` para mostrar el dashboard en tiempo real.
  - Actualización de `templates/users.html` para mejorar la gestión de usuarios autenticados y bloqueados.
  - Actualización de `templates/index.html` para reflejar los cambios en la configuración del bot y añadir nuevas opciones.

- **Telegram Bot**:
  - Optimización de la carga y guardado de usuarios autenticados y bloqueados mediante el uso del módulo `shared.py`.
  - Mejora en el manejo de comandos y modularización de funcionalidades.


## Contribuciones

¡Las contribuciones son bienvenidas! Si deseas contribuir a este proyecto, por favor sigue estos pasos:

1. Haz un fork del repositorio.
2. Crea una nueva rama (`git checkout -b feature/nueva-funcionalidad`).
3. Realiza tus cambios y commitea (`git commit -am 'Añadir nueva funcionalidad'`).
4. Haz push a la rama (`git push origin feature/nueva-funcionalidad`).
5. Abre un Pull Request.

## Licencia

Este proyecto está licenciado bajo la Licencia MIT. Consulta el archivo [LICENSE](LICENSE) para obtener más información.

