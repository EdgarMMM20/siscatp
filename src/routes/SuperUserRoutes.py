from flask import Blueprint, request, jsonify, session

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
            "rfc", "nombre", "app", "apm", "sexo", "tel", "mail", "rol",
            "idcolonia", "calle", "numero", "usuario", "password"
        ]
        missing_fields = [field for field in required_fields if not request.form.get(field)]
        if missing_fields:
            return jsonify({"error": f"Faltan campos: {', '.join(missing_fields)}"}), 400

        # Verificar RFC
        cursor.execute("SELECT rfc FROM persona WHERE rfc= %s", (request.form.get("rfc"),))
        if cursor.fetchone():
            return jsonify({"error": "El rfc ya existe en la tabla persona"}), 400
        cursor.execute("SELECT rfc from usuario WHERE rfc= %s", (request.form.get("rfc"),))
        if cursor.fetchone():
            return jsonify({"error": "El rfc ya existe en la tabla usuario"}), 400

        # Insertar persona
        querypersona = """
            INSERT INTO persona (rfc, nombre, app, apm, sexo, tel, mail, rol, idcolonia, calle, numero) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(querypersona, (
            request.form.get("rfc"), request.form.get("nombre"), request.form.get("app"),
            request.form.get("apm"), request.form.get("sexo"), request.form.get("tel"),
            request.form.get("mail"), request.form.get("rol"), request.form.get("idcolonia"),
            request.form.get("calle"), request.form.get("numero"),
        ))

        # Insertar usuario
        queryusuario = """
            INSERT INTO usuario (rfc,usuario,password)
            VALUES (%s,%s,%s)
        """
        cursor.execute(queryusuario, (
            request.form.get("rfc"), request.form.get("usuario"), request.form.get("password")
        ))
        conn.commit()

        # Guardar RFC en sesión para el siguiente registro
        session["rfcdueno"] = request.form.get("rfc")
        return jsonify({"success": True, "msg": "Registro completado correctamente"}), 200

    except Exception as e:
        conn.rollback()
        # --- RETORNAR ERROR AQUÍ ---
        return jsonify({"error": f"Error en el registro: {str(e)}"}), 500

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
        # Verifica que el RFC del dueño esté en sesión
        if not session.get("rfcdueno"):
            return (
                jsonify({"error": "No hay RFC de dueño en la sesión. Registre primero al dueño."}),
                400,
            )

        if missing_fields:
            return (
                jsonify({"error": f"Faltan campos: {', '.join(missing_fields)}"}),
                400,
            )

        # Obtén la ruta absoluta del directorio actual (donde está este archivo)
        BASE_DIR = os.path.dirname(os.path.abspath(__file__))
        LOGOS_DIR = os.path.join(BASE_DIR, '..', 'static', 'logos')

        logo_file = request.files.get("logo")
        logo_path = None
        if logo_file and logo_file.filename != "":
            if not os.path.exists(LOGOS_DIR):
                os.makedirs(LOGOS_DIR)
            logo_path = os.path.join(LOGOS_DIR, logo_file.filename)
            logo_file.save(logo_path)
            # Guarda la ruta relativa para la base de datos
            logo_db_path = f"static/logos/{logo_file.filename}"
        else:
            logo_db_path = None

        # Insertar compañía
        query = """
            INSERT INTO compania (rfccomp, nombre,logo, tel, idcolonia, calle, numero, rfcdueno) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(
            query,
            (
                request.form.get("rfccomp"),
                request.form.get("nombre"),
                logo_path,
                request.form.get("telefono"),
                request.form.get("idcolonia"),
                request.form.get("calle"),
                request.form.get("numero"),
                session.get("rfcdueno"),
            ),
        )

        #ACTUALIZAR USUARIO CON EL RFC DE LA COMPAÑIA
        update_user= """ UPDATE usuario SET rfccomp = %s WHERE rfc =%s """
        cursor.execute(update_user, (request.form.get("rfccomp"), session.get("rfcdueno")))
        
        conn.commit()
        # Limpiar la sesión
        session.pop("rfcdueno", None)
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
                
