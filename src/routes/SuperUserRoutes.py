from flask import Blueprint, request, jsonify

# from flask_jwt_extended import jwt_required
from db.db import *

BP_SuperUserRoutes = Blueprint("BP_SuperUserRoutes", __name__)


@BP_SuperUserRoutes.route("/registerperson", methods=["POST"])
def register_person():
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Validar campos requeridos
        required_fields = [
            "rfc",
            "nombre",
            "app",
            "apm",
            "sexo",
            "tel",
            "mail",
            "rol",
            "idcolonia",
            "calle",
            "numero",
            "usuario",
            "password"
        ]
        missing_fields = [
            field for field in required_fields if not request.form.get(field)
        ]

        if missing_fields:
            return (
                jsonify({"error": f"Faltan campos: {', '.join(missing_fields)}"}),
                400,
            )
        #VERIFICAR QUE EL RFC NO EXISTA
        cursor.execute ("SELECT rfc FROM persona WHERE rfc= %s", (request.form.get("rfc"),))
        if cursor.fetchone():
            return jsonify({"error": "El rfc ya existe en la tabla persona"}), 400

        cursor.execute ("SELECT rfc from usuario WHERE rfc= %s", (request.form.get ("rfc"),))
        if cursor.fetchone():
            return jsonify({"error": "El rfc ya existe en la tabla usuario"}), 400

        # Insertar persona
        querypersona = """
            INSERT INTO persona (rfc, nombre, app, apm, sexo, tel, mail, rol, idcolonia, calle, numero) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            querypersona,
            (
                request.form.get("rfc"),
                request.form.get("nombre"),
                request.form.get("app"),
                request.form.get("apm"),
                request.form.get("sexo"),
                request.form.get("tel"),
                request.form.get("mail"),
                request.form.get("rol"),
                request.form.get("idcolonia"),
                request.form.get("calle"),
                request.form.get("numero"),
            ),
        )

        #Insertar usuario
        queryusuario= """
            INSERT INTO usuario (rfc,usuario,password)
            VALUES (%s,%s,%s)
        """
        cursor.execute(queryusuario, (request.form.get("rfc"),request.form.get("usuario"), request.form.get("password")))
        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"success": True, "msg": f"Registro completado correctamente"}), 200   
        
    finally:
        if "cursor" in locals() and cursor:
            cursor.close()
        if "conn" in locals() and conn:
            conn.close()


@BP_SuperUserRoutes.route("/registrarcompany", methods=["POST"])
def register_company():
    try:
        conn = get_db()
        cursor = conn.cursor()

        # Validar campos requeridos
        required_fields = [
            "rfccomp",
            "nombre",
            "telefono",
            "idcolonia",
            "calle",
            "numero",
        ]
        missing_fields = [
            field for field in required_fields if not request.form.get(field)
        ]

        if missing_fields:
            return (
                jsonify({"error": f"Faltan campos: {', '.join(missing_fields)}"}),
                400,
            )

        # Insertar compañía
        query = """
            INSERT INTO compania (rfccomp, nombre, tel, idcolonia, calle, numero) 
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            query,
            (
                request.form.get("rfccomp"),
                request.form.get("nombre"),
                request.form.get("telefono"),
                request.form.get("idcolonia"),
                request.form.get("calle"),
                request.form.get("numero"),
            ),
        )

        conn.commit()
        return (
            jsonify({"success": True, "msg": "Compañía registrada correctamente"}),
            200,
        )

    except Exception as e:
        conn.rollback()
        return jsonify({"error": f"Error al registrar compañía: {str(e)}"}), 500

    finally:
        if "cursor" in locals() and cursor:
            cursor.close()
        if "conn" in locals() and conn:
            conn.close()
