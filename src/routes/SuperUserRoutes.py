from flask import Blueprint, request, jsonify, session, render_template, redirect, url_for, flash
# from flask_jwt_extended import jwt_required
from db.db import *
import os
from datetime import datetime

BP_SuperUserRoutes = Blueprint("BP_SuperUserRoutes", __name__)
fech = datetime.now().date()
@BP_SuperUserRoutes.route("/registerperson", methods=["POST"])
def register_person():
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

@BP_SuperUserRoutes.route('/update_dueño', methods=['POST'])
def update_dueño():
    try:
        conn = get_db()
        cursor = conn.cursor()
        # Obtener datos del formulario
        rfc = request.form.get('rfc')
        nombre = request.form.get('nombre')
        app = request.form.get('app')
        apm = request.form.get('apm')
        tel = request.form.get('tel')
        mail = request.form.get('mail')
        idcolonia= request.form.get('idcolonia')
        calle= request.form.get('calle')
        numero= request.form.get('numero')
        # Ejecutar UPDATE en persona
        cursor.execute(
            """
            UPDATE persona
            SET nombre = %s,
                app = %s,
                apm = %s,
                tel = %s,
                mail = %s,
                idcolonia=%s,
                calle=%s,
                numero=%s
            WHERE rfc = %s
            """,
            (nombre, app, apm, tel, mail, idcolonia, calle, numero, rfc)
        )
        conn.commit()
        flash("Dueño actualizado exitosamente.", "success")
    except Exception as e:
        conn.rollback()
        flash(f"Error al actualizar el dueño: {str(e)}", "danger")
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()
    return redirect(url_for('BP_SuperUserRoutes.mostrar_dueños'))

# NUEVO ENDPOINT: Obtener datos completos de un dueño (incluyendo dirección)
@BP_SuperUserRoutes.route('/get_dueño/<rfc>', methods=['GET'])
def get_dueño(rfc):
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        query = '''
            SELECT 
                p.rfc, p.nombre, p.app, p.apm, p.tel, p.mail, p.rol, p.idcolonia, p.calle, p.numero,
                c.nombre AS colonia, c.municipio AS idmunicipio,
                m.nombre AS municipio, m.estado AS idestado,
                e.nombre AS estado, e.pais AS idpais,
                pa.nombre AS pais
            FROM persona p
            LEFT JOIN colonias c ON p.idcolonia = c.id
            LEFT JOIN municipios m ON c.municipio = m.id
            LEFT JOIN estados e ON m.estado = e.id
            LEFT JOIN paises pa ON e.pais = pa.id
            WHERE p.rfc = %s
        '''
        cursor.execute(query, (rfc,))
        data = cursor.fetchone()
        if not data:
            return jsonify({'error': 'Dueño no encontrado'}), 404
        return jsonify(data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

@BP_SuperUserRoutes.route("/viewCompanys", methods=["GET"])
def view_companys():
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)

        # Consulta base (sin filtro de estatus)
        query = """
            SELECT c.rfccomp, c.nombre, CONCAT(p.nombre, ' ', p.app, ' ', p.apm) AS dueño, c.tel, c.numero, p.mail, c.estatus
            FROM compania c
            JOIN persona p ON c.rfcdueno = p.rfc
            WHERE p.rol = "1"
        """

        filters = []
        params = []

        busqueda= request.args.get('obrfc')
        # Filtro RFC compañía
        if busqueda:
            filters.append("c.rfccomp LIKE %s OR c.nombre LIKE %s")
            params.append(f"%{busqueda}%")
            params.append(f"%{busqueda}%")

        # Filtro por estado
        filtro = request.args.get('filtro')
        if filtro == "activos" or filtro is None:
            filters.append("c.estatus = 1")
        elif filtro == "inactivos":
            filters.append("c.estatus = 0")

        # Agrega los filtros a la consulta
        if filters:
            query += " AND " + " AND ".join(filters)

        # Ordena por nombre de compañía
        query += " ORDER BY c.nombre ASC"

        cursor.execute(query, tuple(params))
        companias = cursor.fetchall()
        return render_template('superuser/viewCompany.html' and 'superuser/registersucursales.html', companias=companias), 200
    except Exception as e:
        return f"{str(e)}", 500
    finally:
        if "cursor" in locals() and cursor:
            cursor.close()
        if "conn" in locals() and conn:
            conn.close()

@BP_SuperUserRoutes.route('/toggle_estado_compania/<rfccomp>', methods=['POST'])
def toggle_estado_compania(rfccomp):
    try:
        conn = get_db()
        cursor = conn.cursor()
        # Consulta el estado actual
        cursor.execute("SELECT estatus FROM compania WHERE rfccomp = %s", (rfccomp,))
        result = cursor.fetchone()
        if not result:
            flash("Compañía no encontrada.", "danger")
            return redirect(url_for('BP_SuperUserRoutes.view_companys'))
        nuevo_estado = 0 if result[0] == 1 else 1
        cursor.execute("UPDATE compania SET estatus = %s WHERE rfccomp = %s", (nuevo_estado, rfccomp))
        conn.commit()
        flash("Estado de la compañía actualizado.", "success")
    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()
    return redirect(url_for('BP_SuperUserRoutes.view_companys'))

@BP_SuperUserRoutes.route('/registerUser', methods=['POST'])
def register_user():
    from datetime import datetime
    try:
        conn = get_db()
        cursor = conn.cursor()

        required_fields = [
            "rfc", "nombre", "app", "apm", "sexo", "tel", "mail", "rol",
            "idcolonia", "calle", "numero", "usuario", "password"
        ]
        rol = request.form.get("rol")
        if rol == "2":  # Empleado
            required_fields += ["puesto", "empresa", "sucursal", "turno", "sueldo"]

        # Verificar campos faltantes
        missing_fields = [f for f in required_fields if not request.form.get(f)]
        if missing_fields:
            return jsonify({"error": f"Faltan campos: {', '.join(missing_fields)}"}), 400

        rfc = request.form.get("rfc")

        # Validación duplicados
        cursor.execute("SELECT rfc FROM persona WHERE rfc = %s", (rfc,))
        if cursor.fetchone():
            return jsonify({"error": "El RFC ya existe en la tabla persona"}), 400

        cursor.execute("SELECT rfc FROM usuario WHERE rfc = %s", (rfc,))
        if cursor.fetchone():
            return jsonify({"error": "El RFC ya existe en la tabla usuario"}), 400

        # Insert persona
        fecha_actual = datetime.now().strftime("%Y-%m-%d")
        cursor.execute("""
            INSERT INTO persona (rfc, nombre, app, apm, sexo, tel, mail, rol, idcolonia, calle, numero, fechregis)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            rfc,
            request.form.get("nombre"),
            request.form.get("app"),
            request.form.get("apm"),
            request.form.get("sexo"),
            request.form.get("tel"),
            request.form.get("mail"),
            rol,
            request.form.get("idcolonia"),
            request.form.get("calle"),
            request.form.get("numero"),
            fecha_actual
        ))
        conn.commit()

        # Insert usuario
        cursor.execute("""
            INSERT INTO usuario (rfc, usuario, password)
            VALUES (%s, %s, %s)
        """, (
            rfc,
            request.form.get("usuario"),
            request.form.get("password")
        ))
        conn.commit()

        # Insert empleado si aplica
        if rol == "2":
            idpuesto = request.form.get("puesto")
            idsucursal = request.form.get("sucursal")
            idturno = request.form.get("turno")

            # Verificar existencia en hopuestosu
            cursor.execute("""
                SELECT 1 FROM hopuestosu WHERE idpuesto = %s AND idsucursal = %s AND idturno = %s
            """, (idpuesto, idsucursal, idturno))
            if not cursor.fetchone():
                return jsonify({"error": "No existe combinación válida en hopuestosu para el puesto, sucursal y turno seleccionados"}), 400

            # Insert en empleado
            cursor.execute("""
                INSERT INTO empleado (rfc, idpuesto, idsucursal, idturno, fechcon, sueldo, estatus)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                rfc,
                idpuesto,
                idsucursal,
                idturno,
                fecha_actual,
                request.form.get("sueldo"),
                1
            ))
            conn.commit()

        return jsonify({"message": "Usuario registrado exitosamente"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

@BP_SuperUserRoutes.route('/registerPuesto', methods=['POST'])
def register_puesto():
    try:
        conn = get_db()
        cursor = conn.cursor()

        idpuesto = request.form.get("IDPuesto")
        idsucursal = request.form.get("Sucursal")
        nombre = request.form.get("nomp")
        descripcion = request.form.get("descripcionp")
        idturno = request.form.get("Turno")
        hentrada = request.form.get("horaenp")
        hsalida = request.form.get("horasap")

        # Validar campos requeridos
        if not all([idpuesto, idsucursal, nombre, descripcion, idturno, hentrada, hsalida]):
            return jsonify({"error": "Faltan campos requeridos"}), 400

        # Validar que hora entrada < hora salida
        cursor.execute("SELECT TIME(%s) < TIME(%s)", (hentrada, hsalida))
        if cursor.fetchone()[0] is False:
            return jsonify({"error": "La hora de entrada debe ser menor que la de salida."}), 400

        # Insertar puesto si no existe aún
        cursor.execute("""
            SELECT * FROM puesto WHERE idpuesto = %s AND idsucursal = %s
        """, (idpuesto, idsucursal))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO puesto (idpuesto, idsucursal, nombre, descripcion)
                VALUES (%s, %s, %s, %s)
            """, (idpuesto, idsucursal, nombre, descripcion))
            conn.commit()

        # Verificar traslape de horarios existentes
        cursor.execute("""
            SELECT idturno, hentrada, hsalida
            FROM hopuestosu
            WHERE idpuesto = %s AND idsucursal = %s
              AND hentrada IS NOT NULL AND hsalida IS NOT NULL
              AND (hentrada < CAST(%s AS TIME) AND hsalida > CAST(%s AS TIME))
        """, (idpuesto, idsucursal, hsalida, hentrada))
        traslapado = cursor.fetchone()

        # 🔍 Mostrar en consola para debugging
        if traslapado:
            print(f"Traslape detectado con turno existente: "
                  f"Turno={traslapado[0]}, Entrada={traslapado[1]}, Salida={traslapado[2]}")
            return jsonify({
                "error": f"Horario en conflicto con el turno {traslapado[0]}: "
                         f"{traslapado[1]} - {traslapado[2]}"
            }), 400
        else:
            print("No hay traslapes detectados con horarios existentes.")

        # Validar duplicado exacto
        cursor.execute("""
            SELECT * FROM hopuestosu 
            WHERE idpuesto = %s AND idsucursal = %s AND idturno = %s
        """, (idpuesto, idsucursal, idturno))
        if cursor.fetchone():
            return jsonify({"error": "Ya existe este turno registrado para este puesto y sucursal."}), 400

        # Insertar nuevo horario
        cursor.execute("""
            INSERT INTO hopuestosu (idpuesto, idsucursal, idturno, hentrada, hsalida)
            VALUES (%s, %s, %s, %s, %s)
        """, (idpuesto, idsucursal, idturno, hentrada, hsalida))
        conn.commit()

        print("Registro exitoso de nuevo puesto y horario.")
        return jsonify({"message": "Puesto y horario registrados correctamente"}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()


# Rutas de sucursales

@BP_SuperUserRoutes.route('/dashboard/superuser/sucursales/register', methods=['POST'])
def register_sucursal():
    try:
        id=3
        conn = get_db()
        cursor = conn.cursor()
        # Validar campos requeridos
        required_fields = ['nombre', 'rfccomp', 'idcolonia', 'calle', 'numero']
        missing = [f for f in required_fields if not request.form.get(f)]
        if missing:
            return jsonify({"error": f"Faltan campos: {', '.join(missing)}"}), 400
        rfc= request.form.get('rfccomp').strip()
        print("RFC recibido:", rfc, "| Longitud:", len(rfc))
        cursor.execute(
            "INSERT INTO sucursal (id,nombre, idcolonia, calle, numero, rfccomp) VALUES (%s, %s, %s, %s, %s,%s)",
            (
                id,
                request.form.get('nombre'),
                request.form.get('idcolonia'),
                request.form.get('calle'),
                request.form.get('numero'),
                rfc
            )
        )
        
        conn.commit()
        return jsonify({"message": "Sucursal registrada exitosamente"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()

@BP_SuperUserRoutes.route('/dashboard/superuser/api/sucursales', methods=['GET'])
def api_get_all_sucursales():
    try:
        conn = get_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute('''
            SELECT s.id, s.nombre, s.rfccomp, co.nombre AS colonia, s.calle, s.numero
            FROM sucursal s
            JOIN colonias co ON s.idcolonia = co.id
            ORDER BY s.nombre
        ''')
        sucursales = cursor.fetchall()
        return jsonify({'sucursales': sucursales}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        if 'cursor' in locals(): cursor.close()
        if 'conn' in locals(): conn.close()




