from flask import Blueprint, render_template, session, redirect, url_for

app_routes = Blueprint('app_routes', __name__)

# Verifica sesión antes de mostrar los paneles
def validar_sesion_y_rol(rol_requerido):
    def wrapper(func):
        def decorated_function(*args, **kwargs):
            if 'rol' not in session or session['rol'] != rol_requerido:
                return redirect(url_for('general_bp.login'))
            return func(*args, **kwargs)
        return decorated_function
    return wrapper

# RUTAS PARA EL SUPERUSUARIO
@app_routes.route('/dashboard/superuser/principal')
def dashboard_superuser():
    return render_template('superuser/dashboard.html')

@app_routes.route('/dashboard/superuser/gestionuser') 
def dashboard_superuser_gestionuser():
    return render_template('superuser/gestionuser.html')

@app_routes.route('/dashboard/superuser/register')
def dashboard_superuser_register():
    return render_template('superuser/registraruser.html')

@app_routes.route('/dashboard/superuser/company')
def dashboard_superuser_company():
    return render_template('superuser/company.html')





# RUTAS PARA EL DUEÑO




#RUTAS PARA CAPTURISTA
