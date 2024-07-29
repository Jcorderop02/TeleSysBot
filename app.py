from flask import Flask, render_template, request, redirect, url_for, flash
import json
import os

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Ruta a tu archivo de configuración
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

if __name__ == '__main__':
    app.run(debug=True)

