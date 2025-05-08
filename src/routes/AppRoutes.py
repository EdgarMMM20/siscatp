from flask import Blueprint, render_template, session, redirect, url_for
from functools import wraps
from db.db import *

app_routes = Blueprint('app_routes', __name__)

# Verifica sesión antes de mostrar los paneles
def validar_sesion_y_rol(*roles_o_puestos_permitidos):
    def wrapper(func):
        @wraps(func)
        def decorated_function(*args, **kwargs):
            rol = session.get("rol")
            puesto = session.get("nombre_puesto", "").lower()

            # Acceso por rol directo
            if rol in roles_o_puestos_permitidos:
                return func(*args, **kwargs)

            # Si es empleado (rol 2), validar por puesto
            if rol == "2":
                for item in roles_o_puestos_permitidos:
                    if item.lower() == puesto:
                        return func(*args, **kwargs)

            return redirect(url_for("general_bp.no_autorizado"))
        return decorated_function
    return wrapper

# ---------------------------- RUTAS DEL SISTEMA GENERAL ---------------------------------------


# ---------------------------- RUTAS PARA EL SUPERUSUARIO ---------------------------------------
@app_routes.route('/dashboard/superuser/principal')
@validar_sesion_y_rol("0")
def dashboard_superuser():
    return render_template('superuser/dashboard.html')

@app_routes.route('/dashboard/superuser/gestionuser')
@validar_sesion_y_rol("0")
def dashboard_superuser_gestionuser():
    return redirect(url_for('BP_SuperUserRoutes.mostrar_dueños'))

@app_routes.route('/dashboard/superuser/registerowner')
@validar_sesion_y_rol("0")
def dashboard_superuser_register():
    return render_template('superuser/registrarDueno.html')

@app_routes.route('/dashboard/superuser/company')
@validar_sesion_y_rol("0")
def dashboard_superuser_company():
    return redirect(url_for('BP_SuperUserRoutes.view_companys'))
    
# Esta ruta solo redirige a la vista de compañías para gestión de sucursales.
# No muestra sucursales directamente, solo sirve para mantener compatibilidad con enlaces antiguos o navegación.
@app_routes.route('/dashboard/superuser/sucursales')
@validar_sesion_y_rol("0")
def dashboard_superuser_sucursales():
    return redirect(url_for('BP_SuperUserRoutes.view_companys'))

#VER SUCURSALES
@app_routes.route('/dashboard/superuser/viewsucursales')
@validar_sesion_y_rol("0")
def dashboard_superuser_viewsucursales():
    return render_template('superuser/viewsucursales.html')

#REGISTRAR PUESTO
@app_routes.route('/dashboard/superuser/registerpuesto')
@validar_sesion_y_rol("0")
def dashboard_superuser_registerpuesto():
    return render_template('superuser/registrarpuesto.html')

#REGISTRAR USUARIO
@app_routes.route('/dashboard/superuser/registeruser')
@validar_sesion_y_rol("0")
def dashboard_superuser_registeruser():
    return render_template('superuser/registerUser.html')
    
@app_routes.route('/dashboard/superuser/metricas')
@validar_sesion_y_rol("0")
def dashboard_superuser_metricas():
    return render_template('superuser/metricas.html')

@app_routes.route('/dashboard/superuser/subirpost')
@validar_sesion_y_rol("0")
def dashboard_superuser_subirpost():
    return render_template('superuser/subirpost.html')

@app_routes.route('/dashboard/superuser/ajuste')
@validar_sesion_y_rol("0")
def dashboard_superuser_ajuste():
    return render_template('superuser/ajuste.html')

#---------------------------- RUTAS PARA EL DUEÑO ---------------------------------------
@app_routes.route('/dashboard/owner/principal')
@validar_sesion_y_rol("1")
def dashboard_owner():
    return render_template('dueno/dashboard.html')

@app_routes.route('/dashboard/owner/registeruser')
@validar_sesion_y_rol("1")
def dashboard_owner_registeruser():
    return render_template('dueno/registraruser.html')


#---------------------------- RUTAS PARA CAPTURISTA ---------------------------------------
@app_routes.route('/dashboard/capturista/principal')
@validar_sesion_y_rol("capturista")
def dashboard_capturista():
    mostrar_alerta = session.pop("mostrar_alerta", False)
    return render_template('capturista/dashboard.html', mostrar_alerta=mostrar_alerta)

@app_routes.route('/dashboard/capturista/registrarcaja')
@validar_sesion_y_rol("capturista")
def dashboard_capturista_registrarcaja():
    return render_template('capturista/registrarcaja.html')

@app_routes.route('/dashboard/capturista/registrarpro')
@validar_sesion_y_rol("0", "capturista")
def dashboard_capturista_registrarpro():
    return render_template('capturista/registrarpro.html')

@app_routes.route('/dashboard/capturista/registrartpro')
@validar_sesion_y_rol("capturista")
def dashboard_capturista_registrartpro():
    return render_template('capturista/registrartpro.html')

@app_routes.route('/dashboard/capturista/registrarzona')
@validar_sesion_y_rol("capturista")
def dashboard_capturista_registrarzona():
    return render_template('capturista/registrarzona.html')
