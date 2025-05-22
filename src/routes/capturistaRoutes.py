import secrets
import string
import base64
from flask import Blueprint, request, jsonify, session
#from flask_jwt_extended import jwt_required
from db.db import *
from db.db import connect_to_database, get_db
from mysql.connector import Error

BP_CapturistaRoutes = Blueprint('BP_CapturistaRoutes', __name__)

@BP_CapturistaRoutes.route("/get-zonalma", methods=["GET"])
def get_zonalma():
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT idzonalma, nombre FROM zonalmacen;"
        cursor.execute(query)
        data = cursor.fetchall()
        cursor.close()
        return jsonify(data), 200
    except Exception as e:
        print("Error en get_zonalma:", str(e))
        return jsonify({"error": str(e)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()
            
@BP_CapturistaRoutes.route("/get-productos", methods=["GET"])
def get_productos():
    rfccomp = session.get("rfccomp")
    if not rfccomp:
        return jsonify({"error": "No se encontró la compañía en la sesión"}), 400

    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT cvpro, nombre, requiere_caducidad 
            FROM producto 
            WHERE rfccomp = %s;
        """
        cursor.execute(query, (rfccomp,))
        productos = cursor.fetchall()
        cursor.close()
        return jsonify(productos), 200
    except Exception as e:
        print("Error al obtener productos:", str(e))
        return jsonify({"error": str(e)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()

@BP_CapturistaRoutes.route("/get-producto-info/<cvpro>", methods=["GET"])
def get_producto_info(cvpro):
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT z.idzonalma, p.requiere_caducidad
            FROM producto p
            JOIN tipopro t ON p.idtipo = t.idtipop
            JOIN zonalmacen z ON t.idzonalma = z.idzonalma  -- Realizamos el JOIN con zonalmacen
            WHERE p.cvpro = %s AND p.rfccomp = %s;
        """
        rfccomp = session.get("rfccomp")  # Obtenemos el rfccomp de la sesión
        cursor.execute(query, (cvpro, rfccomp))
        producto = cursor.fetchone()
        cursor.close()
        
        if producto:
            return jsonify({
                "zona": producto["idzonalma"],
                "requiere_caducidad": producto["requiere_caducidad"]
            }), 200
        else:
            return jsonify({"error": "Producto no encontrado"}), 404
    except Exception as e:
        print("Error al obtener información del producto:", str(e))
        return jsonify({"error": str(e)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()

@BP_CapturistaRoutes.route("/get-tipopro", methods=["GET"])
def get_tipopro():
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        query = "SELECT idtipop, nombre FROM tipopro;"
        cursor.execute(query)
        data = cursor.fetchall()
        cursor.close()
        return jsonify(data), 200
    except Exception as e:
        print("Error en get_tipopro:", str(e))
        return jsonify({"error": str(e)}), 500
    finally:
        if conn and conn.is_connected():
            conn.close()

@BP_CapturistaRoutes.route("/registrarproducto", methods=["POST"])
def registrar_producto():
    conn = get_db()
    try:
        cursor = conn.cursor()

        # Obtener datos del formulario
        rfccomp = session.get("rfccomp")
        if not rfccomp:
            return jsonify({"error": "No se encontró la compañía en la sesión"}), 400

        cvpro = request.form.get("cvpro")
        idtipo = request.form.get("idtipo")
        nombre = request.form.get("nombre")
        marca = request.form.get("marca")
        presentacion = request.form.get("presentacion")
        precio_compra = request.form.get("precio_compra")
        precio_venta = request.form.get("precio_venta")
        requiere_caducidad = request.form.get("requiere_caducidad")
        activo = request.form.get("activo")

        imagen_file = request.files.get("imagen")
        imagen = imagen_file.read() if imagen_file and imagen_file.filename != '' else None

        # Query de inserción
        query = """
            INSERT INTO producto (
                cvpro, idtipo, requiere_caducidad, nombre, marca, presentacion,
                precio_compra, precio_venta, imagen, activo, rfccomp
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            cvpro, idtipo, requiere_caducidad, nombre, marca, presentacion,
            precio_compra, precio_venta, imagen, activo, rfccomp
        )
        cursor.execute(query, values)
        conn.commit()
        cursor.close()

        return jsonify({"msg": "Producto registrado correctamente"}), 200

    except Exception as e:
        print("Error al registrar producto:", str(e))
        return jsonify({"error": str(e)}), 500

    finally:
        if conn and conn.is_connected():
            conn.close()

@BP_CapturistaRoutes.route("/registrarcaja", methods=["POST"])
def registrar_caja():
    conn = get_db()
    try:
        cursor = conn.cursor()

        rfccomp = session.get("rfccomp")
        if not rfccomp:
            return jsonify({"error": "No se encontró la compañía en la sesión"}), 400

        # Obtener datos del formulario
        cvcaja = request.form.get("cvcaja")
        cvpro = request.form.get("cvpro")
        idzonalmacen = request.form.get("idzonalmacen")
        cant = request.form.get("cant")
        lote = request.form.get("lote")
        precio = request.form.get("precio")
        fcaducidad = request.form.get("fcaducidad") or None
        fingreso = request.form.get("fingreso")
        estado = request.form.get("estado")

        # Insertar en la base de datos
        query = """
            INSERT INTO cajas (
                cvcaja, cvpro, idzonalmacen, cant, lote, precio,
                fcaducidad, fingreso, estado, rfccomp
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        values = (
            cvcaja, cvpro, idzonalmacen, cant, lote, precio,
            fcaducidad, fingreso, estado, rfccomp
        )

        cursor.execute(query, values)
        conn.commit()
        cursor.close()

        return jsonify({"msg": "Caja registrada correctamente"}), 200

    except Exception as e:
        print("Error al registrar caja:", str(e))
        return jsonify({"error": str(e)}), 500

    finally:
        if conn and conn.is_connected():
            conn.close()