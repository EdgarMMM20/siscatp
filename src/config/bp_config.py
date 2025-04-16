from routes.generalRoute import general_bp
from routes.AppRoutes import app_routes
from routes.SuperUserRoutes import BP_SuperUserRoutes


def register_blueprints(app):
    app.register_blueprint(general_bp)
    app.register_blueprint(app_routes)
    app.register_blueprint(BP_SuperUserRoutes)
    
