import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

# Cargar variables del entorno desde .env
load_dotenv()

# Leer variables del entorno
DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_NAME = os.getenv("DATABASE_NAME")


# Conexión a la base de datos
def connect_to_database():
    try:
        connection = mysql.connector.connect(
            host=DATABASE_HOST,
            user=DATABASE_USER,
            password=DATABASE_PASSWORD,
            database=DATABASE_NAME,
        )
        if connection.is_connected():
            print("✅ Conexión establecida con la base de datos.")
            return connection
    except Error as e:
        print("❌ Error al conectar a la base de datos:", e)
    return None


def get_db():
    connection = connect_to_database()
    if connection:
        connection.autocommit = True
    return connection
