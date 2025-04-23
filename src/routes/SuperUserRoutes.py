from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash
# from flask_jwt_extended import jwt_required
from db.db import *
import os
from datetime import datetime

BP_SuperUserRoutes = Blueprint("BP_SuperUserRoutes", __name__)


@BP_SuperUserRoutes.route("/registerperson", methods=["POST"])
def register_person():
    fech = datetime.now().date()
    rdef= 1

    try:
        conn = get_db()
        cursor = conn.cursor()

        # Validar campos requeridos
        required_fields = [
            "rfc", "nombre", "app", "apm", "sexo", "tel", "mail",
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
            INSERT INTO persona (rfc, nombre, app, apm, sexo, tel, mail, rol, idcolonia, calle, numero, fechregis) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(querypersona, (
            request.form.get("rfc"), request.form.get("nombre"), request.form.get("app"),
            request.form.get("apm"), request.form.get("sexo"), request.form.get("tel"),
            request.form.get("mail"), rdef, request.form.get("idcolonia"),
            request.form.get("calle"), request.form.get("numero"), fech,
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
                logo_db_path,
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
                
@BP_SuperUserRoutes.route("/gestionuser", methods=["GET"])
def mostrar_dueños():
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        # CONSULTA PARA OBTENER LA LISTA DE DUEÑOS
        query= """SELECT p.rfc, p.nombre, p.app, p.apm, p.tel, p.mail, p.rol, p.fechregis, u.activo
        FROM persona p 
        JOIN usuario u ON p.rfc = u.rfc WHERE p.rol = "1" """

        filters = []  # Lista para almacenar condiciones WHERE
        params = []   # Lista para los parámetros de la consulta

        # FILTRO SI EL USUARIO ESCRIBIO EN EL BUSCADOR
        rfc= request.args.get('obrfc')
        if rfc:
            filters.append("p.rfc LIKE%s")
            params.append(f"%{rfc}%")

        # Filtro por estado según el select
        filtro = request.args.get('filtro')

        # Si no hay filtro seleccionado, por defecto muestra solo activos
        if  filtro ==  "activos" or (filtro is None):
            filters.append("u.activo=1")
        elif filtro == "inactivos":
            filters.append("u.activo=0")
        elif filtro == "recientes":
            filters.append("p.fechregis >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)")
    
        
        # Si hay filtros, agrégalos a la consulta base
        if filters:
            query += " AND " + " AND ".join(filters)
        # Ordena por fecha de registro descendente (más recientes arriba)
        query += " ORDER BY p.fechregis DESC"
        
        # Ejecutar la consulta con los parametros
        cursor.execute(query, tuple(params))
        dueños = cursor.fetchall()
        return render_template('superuser/gestionuser.html', dueños=dueños), 200
    except Exception as e:
        return f"{str(e)}", 500
    finally:
        if "cursor" in locals() and cursor:
            cursor.close()
        if "conn" in locals() and conn:
            conn.close()

@BP_SuperUserRoutes.route('/toggle_estado_dueño/<rfc>', methods=["POST"])
def toggle_estado_dueño(rfc):
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT activo FROM usuario WHERE rfc=%s", (rfc,))
        usuario = cursor.fetchone()
        if usuario:
            new_state = 0 if usuario["activo"] == 1 else 1
            cursor.execute("UPDATE usuario SET activo = %s WHERE rfc = %s", (new_state, rfc))
            conn.commit()
            if new_state == 1:
                flash("Dueño reactivado exitosamente.", "success")
            else:
                flash("Dueño dado de baja exitosamente.", "warning")
        else:
            flash("No se encontró el usuario especificado.", "danger")
    except Exception as e:
        flash(f"Error al actualizar el estado: {str(e)}", "danger")
    finally:
        if "cursor" in locals() and cursor:
            cursor.close()
        if "conn" in locals() and conn:
            conn.close()
    return redirect(url_for('BP_SuperUserRoutes.mostrar_dueños'))

