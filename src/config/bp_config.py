from routes.generalRoute import general_bp
from routes.AppRoutes import app_routes
from routes.SuperUserRoutes import BP_SuperUserRoutes
from routes.OwnerRoutes import BP_owner
from routes.capturistaRoutes import BP_CapturistaRoutes
from routes.facebookRoutes import facebook_bp
from routes.operadorRoute import BP_operador

def register_blueprints(app):
    app.register_blueprint(general_bp)
    app.register_blueprint(app_routes)
    app.register_blueprint(BP_SuperUserRoutes)
    app.register_blueprint(BP_owner)
    app.register_blueprint(BP_CapturistaRoutes)
    app.register_blueprint(facebook_bp)
    app.register_blueprint(BP_operador)