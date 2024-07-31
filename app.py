from flask import Flask, render_template, request, redirect, url_for, flash
import json
import os
import psutil 

app = Flask(__name__)
app.secret_key = 'supersecretkey'

CONFIG_FILE = "config.json"

# Cargar configuración
def load_command_config():
    try:
        with open(CONFIG_FILE, "r") as file:
            config = json.load(file)
            return config
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"Error al cargar config.json: {e}")
        return {}

# Guardar configuración
def save_command_config(config):
    try:
        with open(CONFIG_FILE, "w") as file:
            json.dump(config, file, indent=4)
    except Exception as e:
        print(f"Error al guardar config.json: {e}")

@app.route('/')
def index():
    config = load_command_config()
    return render_template('index.html', config=config)

@app.route('/update_config', methods=['POST'])
def update_config():
    config = load_command_config()
    for command in config.keys():
        config[command] = request.form.get(command) == 'on'
    save_command_config(config)
    flash('Configuración actualizada correctamente.')
    return redirect(url_for('index'))

@app.route('/dashboard')
def dashboard():
    cpu_usage = psutil.cpu_percent(interval=1)
    mem_info = psutil.virtual_memory()
    disk_info = psutil.disk_usage('/')
    load_avg = psutil.getloadavg()

    partitions = psutil.disk_partitions()
    disk_usage_info = "\n".join(f"{p.device}: {psutil.disk_usage(p.mountpoint).percent}%" for p in partitions)
    
    return render_template('dashboard.html', 
                           cpu_usage=cpu_usage,
                           mem_total=mem_info.total / (1024 ** 2),
                           mem_available=mem_info.available / (1024 ** 2),
                           mem_usage=mem_info.percent,
                           disk_total=disk_info.total / (1024 ** 2),
                           disk_usage=disk_info.percent,
                           load_avg=load_avg,
                           disk_usage_info=disk_usage_info)

@app.route('/users')
def manage_users():
    from shared import load_authenticated_users, load_blocked_users
    authenticated_users = load_authenticated_users()
    blocked_users = load_blocked_users()
    return render_template('users.html', authenticated_users=authenticated_users, blocked_users=blocked_users)

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0')
