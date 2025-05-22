import os
from dotenv import load_dotenv
from flask import Flask
from flask_cors import CORS
from config.bp_config import register_blueprints
from datetime import timedelta
from routes.operadorRoute import iniciar_verificacion


def create_app():
    # Cargar variables de entorno desde .env
    load_dotenv()

    # Crear la app de Flask
    app = Flask(__name__, template_folder="../templates", static_folder="../static")

    # Clave secreta para sesiones
    app.secret_key = os.getenv("SECRET_KEY_JWT", "clave_por_defecto_segura")
    
    app.permanent_session_lifetime = timedelta(hours=5)

    # Habilitar CORS
    CORS(app)

    # Registrar blueprints desde bp_config
    register_blueprints(app)
    
    iniciar_verificacion()

    return app
