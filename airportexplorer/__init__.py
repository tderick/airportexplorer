from decouple import config
from flask import Flask
from flask_login import LoginManager
from .models import User

def create_app():
    # create and configure the app
    app = Flask(__name__,static_folder="../static", template_folder="../templates",  instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY=config('APP_SECRET_KEY'),
    )

    # Login Manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login_page"
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_email(user_id)
        
    # Register Blieprints
    from . import auth
    from . import home
    from . import panel
    app.register_blueprint(auth.bp)
    app.register_blueprint(home.bp)
    app.register_blueprint(panel.bp)

    return app