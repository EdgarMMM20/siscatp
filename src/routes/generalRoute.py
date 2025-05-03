from flask import (
    Blueprint,
    render_template,
    jsonify,
    request,
    redirect,
    session,
    flash,
    url_for,

)
from db.db import *
import os

general_bp = Blueprint("general_bp", __name__)

@general_bp.route("/")
def index():
    return redirect(url_for("general_bp.login"))

@general_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        password = request.form.get("password", "").strip()

        if not usuario or not password:
            return jsonify({"error": "Faltan campos obligatorios"}), 400

        try:
            conn = connect_to_database()
            cursor = conn.cursor()

            query = """
                SELECT persona.rfc, persona.rol, usuario.rfccomp,
                       persona.nombre, persona.app, persona.apm,
                       rol.nombre AS nombre_rol
                FROM persona
                JOIN usuario ON usuario.rfc = persona.rfc
                LEFT JOIN rol ON persona.rol = rol.idrol
                WHERE usuario.usuario = %s AND usuario.password = %s;
            """
            cursor.execute(query, (usuario, password))
            resultado = cursor.fetchone()
            conn.close()

            if resultado is None:
                flash("Usuario o contraseña incorrectos", "danger")
                return redirect(url_for("general_bp.login"))

            # Desempaquetar los datos
            rfc, rol_id, rfc_comp, nombre, app, apm, rol_nombre = resultado

            # Guardar en sesión
            session["rfc"] = rfc
            session["rol"] = rol_id
            session["rol_nombre"] = rol_nombre
            session["rfccomp"] = rfc_comp
            session["usuario_nombre"] = f"{nombre} {app} {apm}"

            print("Sesión:", dict(session))

            # Redireccionar por rol
            if rol_id == "0":
                return redirect(url_for("app_routes.dashboard_superuser"))
            elif rol_id == "1":
                return redirect(url_for("app_routes.dashboard_owner"))
            elif rol_id == "4":
                return redirect(url_for("app_routes.dashboard_capturista"))
            elif rol_id in ["2", "3"]:
                return redirect(url_for("app_routes.dashboard_employees"))
            else:
                return jsonify({"message": "Rol no reconocido"}), 403

        except Exception as e:
            return jsonify({"error": f"Error del servidor: {str(e)}"}), 500

    # Si GET, mostrar formulario
    return render_template("login.html")

@general_bp.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada", "info")
    return redirect(url_for("general_bp.login"))

@general_bp.route("/no-autorizado")
def no_autorizado():
    return render_template('/general/no_autorizado.html')

def convertToObject(cursor):
    columns = [column[0] for column in cursor.description]
    results = []
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))
    return results


@general_bp.route("/get-paises", methods=["GET"])
def get_paises():
    conn = get_db()
    try:
        cursor = conn.cursor(
            dictionary=True
        )  # Usar dictionary=True para obtener resultados como diccionarios
        insert_query = "SELECT id, nombre FROM paises;"
        cursor.execute(insert_query)
        data = cursor.fetchall()  # Obtener los datos directamente
        cursor.close()
        return jsonify(data), 200
    except Exception as e:
        print("Error en get_paises:", str(e))  # Imprimir el error para debugging
        return jsonify({"error": str(e)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()


@general_bp.route("/get-estados/<pais_id>", methods=["GET"])
def get_estados(pais_id):
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        insert_query = "SELECT id, nombre FROM estados WHERE pais=%s;"
        cursor.execute(insert_query, (pais_id,))
        data = cursor.fetchall()
        cursor.close()
        return jsonify(data), 200
    except Exception as e:
        print("Error en get_estados:", str(e))
        return jsonify({"error": str(e)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()


@general_bp.route("/get-municipios/<id_estado>", methods=["GET"])
def get_municipios(id_estado):
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        insert_query = "SELECT id, nombre FROM municipios WHERE estado=%s;"
        cursor.execute(insert_query, (id_estado,))
        data = cursor.fetchall()
        cursor.close()
        return jsonify(data), 200
    except Exception as e:
        print("Error en get_municipios:", str(e))
        return jsonify({"error": str(e)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()


@general_bp.route("/get-colonias/<id_municipio>", methods=["GET"])
def get_colonias(id_municipio):
    conn = get_db()
    try:
        cursor = conn.cursor()
        insert_query = "SELECT id, nombre FROM colonias WHERE municipio=%s;"
        cursor.execute(insert_query, (id_municipio,))
        data = convertToObject(cursor)
        cursor.close()
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()
