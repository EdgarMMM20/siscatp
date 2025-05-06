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
    return redirect(url_for("general_bp.principal"))

@general_bp.route("/principal")
def principal():
    return render_template("general/principal.html")

@general_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        password = request.form.get("password", "").strip()

        if not usuario or not password:
            return jsonify({"error": "Faltan campos obligatorios"}), 400

        try:
            conn = connect_to_database()
            if not conn:
                cerrar_sesion("Error de conexión a la base de datos", "danger")
                return redirect(url_for("general_bp.login"))

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

            if resultado is None:
                cerrar_sesion("Usuario o contraseña incorrectos", "danger")
                return redirect(url_for("general_bp.login"))

            # Desempaquetar los datos
            rfc, rol_id, rfc_comp, nombre, app, apm, rol_nombre = resultado

            # Guardar datos básicos en sesión
            session["rfc"] = rfc
            session["rol"] = rol_id
            session["rol_nombre"] = rol_nombre
            session["rfccomp"] = rfc_comp
            session["usuario_nombre"] = f"{nombre} {app} {apm}"
            print("Sesión:", dict(session))

            # Si es empleado, obtener su puesto y sucursal
            if rol_id == "2":
                query_emp = """
                    SELECT p.nombre AS nombre_puesto, s.nombre AS nombre_sucursal, e.idpuesto, e.idsucursal
                    FROM empleado e
                    LEFT JOIN puesto p ON e.idpuesto = p.idpuesto
                    LEFT JOIN sucursal s ON e.idsucursal = s.id
                    WHERE e.rfc = %s;
                """
                cursor.execute(query_emp, (rfc,))
                emp_data = cursor.fetchone()
                conn.close()

                if emp_data is None:
                    cerrar_sesion("El empleado no tiene puesto o sucursal asignada", "danger")
                    return redirect(url_for("general_bp.login"))

                nombre_puesto, nombre_sucursal, idpuesto, idsucursal = emp_data

                session["nombre_puesto"] = nombre_puesto
                session["nombre_sucursal"] = nombre_sucursal
                session["idpuesto"] = idpuesto
                session["idsucursal"] = idsucursal

                # Redirigir según el puesto
                if nombre_puesto.lower() == "capturista":
                    return redirect(url_for("app_routes.dashboard_capturista"))
                #elif nombre_puesto.lower() == "almacenista":
                    #return redirect(url_for("app_routes.dashboard_almacenista"))
                else:
                    cerrar_sesion("Puesto no reconocido", "danger")
                    return redirect(url_for("general_bp.login"))

            # Si no es empleado, redirigir por rol
            if rol_id == "0":
                return redirect(url_for("app_routes.dashboard_superuser"))
            elif rol_id == "1":
                return redirect(url_for("app_routes.dashboard_owner"))

            cerrar_sesion("Rol no reconocido", "danger")
            return redirect(url_for("general_bp.login"))

        except Exception as e:
            cerrar_sesion("Error del servidor", "danger")
            return redirect(url_for("general_bp.login"))

    return render_template("login.html")

def cerrar_sesion(mensaje="Sesión cerrada", categoria="info"):
    session.clear()
    flash(mensaje, categoria)

@general_bp.route("/logout")
def logout():
    cerrar_sesion()
    return redirect(url_for("general_bp.login"))

@general_bp.route("/no-autorizado")
def no_autorizado():
    cerrar_sesion()
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
            
@general_bp.route("/get-companias", methods=["GET"])
def get_companias():
    try:
        conn = get_db()
        cursor = conn.cursor()

        rol_actual = int(session.get("rol", 0))
        puesto = session.get("puesto", "").lower() if session.get("puesto") else ""
        rfc_usuario = session.get("rfc")

        if rol_actual == 0:
            # Superusuario: ve todas las compañías activas
            cursor.execute("SELECT rfccomp, nombre FROM compania WHERE estatus = 1")

        elif rol_actual == 1:
            # Dueño: ve solo su propia compañía
            cursor.execute("SELECT rfccomp, nombre FROM compania WHERE rfcdueno = %s AND estatus = 1", (rfc_usuario,))

        elif rol_actual == 2 and puesto == "administrador":
            # Administrador: ve la compañía donde trabaja
            cursor.execute("""
                SELECT c.rfccomp, c.nombre 
                FROM compania c
                JOIN sucursal s ON s.rfccomp = c.rfccomp
                JOIN empleado e ON e.idsucursal = s.id
                WHERE e.rfc = %s AND c.estatus = 1
                LIMIT 1
            """, (rfc_usuario,))

        else:
            return jsonify([])

        companias = [{"rfccomp": r[0], "nombre": r[1]} for r in cursor.fetchall()]
        return jsonify(companias)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        cursor.close()
        conn.close()

@general_bp.route("/get-sucursales-by-compania/<rfccomp>", methods=["GET"])
def get_sucursales_by_compania(rfccomp):
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT id, nombre FROM sucursal WHERE rfccomp = %s", (rfccomp,))
        sucursales = [{"id": r[0], "nombre": r[1]} for r in cursor.fetchall()]
        return jsonify(sucursales)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# Obtener turnos
@general_bp.route("/get-turnos", methods=["GET"])
def get_turnos():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT idturno, nombre FROM turno")
        turnos = [{"id": row[0], "nombre": row[1]} for row in cursor.fetchall()]
        return jsonify(turnos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@general_bp.route("/get-roles", methods=["GET"])
def get_roles():
    try:
        conn = get_db()
        cursor = conn.cursor()

        rol_actual = int(session.get("rol", 0))  # convertir a entero
        puesto = session.get("puesto", "").lower() if session.get("puesto") else ""

        if rol_actual == 0:  # Superusuario
            cursor.execute("SELECT idrol, nombre FROM rol")
        elif rol_actual == 1:  # Dueño
            cursor.execute("SELECT idrol, nombre FROM rol WHERE idrol = 2")
        elif rol_actual == 2 and puesto == "administrador":
            cursor.execute("SELECT idrol, nombre FROM rol WHERE idrol = 2")
        else:
            return jsonify([])

        roles = [{"id": row[0], "nombre": row[1]} for row in cursor.fetchall()]
        return jsonify(roles)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@general_bp.route("/get-puestos-by-sucursal/<idsucursal>", methods=["GET"])
def get_puestos_by_sucursal(idsucursal):
    try:
        conn = get_db()
        cursor = conn.cursor()
        query = """
            SELECT idpuesto, nombre
            FROM puesto
            WHERE idsucursal = %s
        """
        cursor.execute(query, (idsucursal,))
        puestos = [{"id": row[0], "nombre": row[1]} for row in cursor.fetchall()]
        return jsonify(puestos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@general_bp.route("/get-turnos-by-puesto-sucursal/<idpuesto>/<idsucursal>", methods=["GET"])
def get_turnos_by_puesto_sucursal(idpuesto, idsucursal):
    try:
        conn = get_db()
        cursor = conn.cursor()
        query = """
            SELECT t.idturno, t.nombre
            FROM hopuestosu h
            JOIN turno t ON h.idturno = t.idturno
            WHERE h.idpuesto = %s AND h.idsucursal = %s
        """
        cursor.execute(query, (idpuesto, idsucursal))
        turnos = [{"id": row[0], "nombre": row[1]} for row in cursor.fetchall()]
        return jsonify(turnos)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()
