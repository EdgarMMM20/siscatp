from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash
from db.db import *
import os
from datetime import datetime

BP_owner = Blueprint('BP_owner', __name__)

@BP_owner.route("/register_employee", methods=["POST"])
def register_employee():
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Campos requeridos (ajusta si es diferente)
        required_fields = ["rfc", "nombre", "app", "apm", "sexo", "tel", "mail", "rol", "idcolonia", "calle", "numero", "usuario", "password"]
        missing_fields = [field for field in required_fields if not request.form.get(field)]
        if missing_fields:
            return jsonify({"error": f"Faltan campos: {', '.join(missing_fields)}", "success": False}), 400

        # Verificar si el RFC ya existe
        cursor.execute("SELECT rfc FROM persona WHERE rfc = %s", (request.form.get("rfc"),))
        if cursor.fetchone():
            return jsonify({"error": "El RFC ya existe en la tabla persona", "success": False}), 400
        cursor.execute("SELECT rfc FROM usuario WHERE rfc = %s", (request.form.get("rfc"),))
        if cursor.fetchone():
            return jsonify({"error": "El RFC ya existe en la tabla usuario", "success": False}), 400

        # Insertar en persona
        query_persona = """
            INSERT INTO persona (rfc, nombre, app, apm, sexo, tel, mail, rol, idcolonia, calle, numero) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(query_persona, (
            request.form.get("rfc"), request.form.get("nombre"), request.form.get("app"),
            request.form.get("apm"), request.form.get("sexo"), request.form.get("tel"),
            request.form.get("mail"), request.form.get("rol"), request.form.get("idcolonia"),
            request.form.get("calle"), request.form.get("numero")
        ))

        # Insertar en usuario
        query_usuario = """
            INSERT INTO usuario (rfc, usuario, password)
            VALUES (%s, %s, %s)
        """
        cursor.execute(query_usuario, (
            request.form.get("rfc"), request.form.get("usuario"), request.form.get("password")
        ))

        conn.commit()
        return jsonify({"success": True, "msg": "Registro completado correctamente"}), 200

    except Exception as e:
        conn.rollback()
        return jsonify({"error": f"Error en el registro: {str(e)}", "success": False}), 500

    finally:
        cursor.close()
        conn.close()