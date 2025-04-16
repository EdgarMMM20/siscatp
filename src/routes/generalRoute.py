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
from db.db import connect_to_database, get_db
import os
from mysql.connector import Error

# Cargar variables desde el archivo .env
# load_dotenv()

general_bp = Blueprint("general_bp", __name__)


@general_bp.route("/")
def index():
    return redirect(url_for("general_bp.login"))


@general_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        required_fields = ["usuario", "password"]
        missing_fields = [
            field for field in required_fields if not request.form.get(field)
        ]

        if missing_fields:
            return (
                jsonify(
                    {
                        "error": f"Faltan los siguientes campos: {', '.join(missing_fields)}"
                    }
                ),
                400,
            )

        usuario = request.form.get("usuario").strip()
        password = request.form.get("password").strip()

        try:
            conn = connect_to_database()
            cursor = conn.cursor()

            query = """
                SELECT persona.rfc, persona.rol, usuario.rfccomp,
                       puesto.idpuesto, puesto.nombre, puesto.hentrada, puesto.hsalida
                FROM persona 
                JOIN usuario ON usuario.rfc = persona.rfc
                LEFT JOIN puesto ON persona.rol = puesto.idpuesto
                WHERE usuario.usuario = %s AND usuario.password = %s;
            """
            cursor.execute(query, (usuario, password))
            res1 = cursor.fetchone()
            conn.close()

            if res1 is None:
                return jsonify({"message": "Credenciales inválidas"}), 400

            # Desempaquetar datos
            rfc, rol_usuario, rfc_comp, puesto_id, puesto_nombre, h_ent, h_sal = res1

            # Guardar sesión
            session["rfc"] = rfc
            session["rol"] = rol_usuario
            session["rfccomp"] = rfc_comp
            session["idpuesto"] = puesto_id
            session["nombre"] = puesto_nombre
            session["hentrada"] = str(h_ent)
            session["hsalida"] = str(h_sal)

            print("Sesión guardada:", dict(session))

            # Redirección por rol
            if rol_usuario == "0":
                return redirect(url_for("app_routes.dashboard_superuser"))
            elif rol_usuario == "1":
                return redirect(url_for("app_routes.dashboard_owner"))
            elif rol_usuario in ["2", "3", "4"]:
                return redirect(url_for("app_routes.dashboard_employees"))
            else:
                return jsonify({"message": "Rol no reconocido"}), 403

        except Exception as e:
            return jsonify({"error": f"Error en servidor: {str(e)}"}), 500

    # Si GET, renderiza login
    return render_template("login.html")


@general_bp.route("/logout")
def logout():
    session.clear()
    flash("Sesión cerrada", "info")
    return redirect(url_for("general_bp.login"))


@general_bp.route("/no-autorizado")
def no_autorizado():
    return "No tienes permisos para acceder a esta página", 403


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
