import redis
from decouple import config
from flask import Flask
from flask_caching import Cache
from flask_login import LoginManager
from flask_session import Session
from flask_wtf.csrf import CSRFProtect
from celery import Celery, Task

from .models import User

cache = Cache(config={"CACHE_TYPE": "redis", "CACHE_REDIS_URL": config("REDIS_URL")})

csrf = CSRFProtect()

def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery_app = Celery(app.name, task_cls=FlaskTask)
    celery_app.config_from_object(app.config["CELERY"], namespace="CELERY")
    celery_app.set_default()
    app.extensions["celery"] = celery_app
    return celery_app


def create_app():
    # create and configure the app
    app = Flask(
        __name__,
        static_folder="../static",
        template_folder="../templates",
        instance_relative_config=True,
    )
    app.config.from_mapping(
        SECRET_KEY=config("APP_SECRET_KEY"),
        CELERY=dict(
            broker_url=config("REDIS_URL"),
            result_backend=config("REDIS_URL"),
            task_ignore_result=False,
        ),
    )

    # SESSION CONFIG
    # Configure Redis for storing the session data on the server-side
    app.config["SESSION_TYPE"] = "redis"
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_USE_SIGNER"] = True
    app.config["SESSION_REDIS"] = redis.from_url(config("REDIS_URL"))

    # Create and initialize the Flask-Session object AFTER `app` has been configured
    Session(app)
    cache.init_app(app)
    csrf.init_app(app)
    
    # Configure Celery
    app.config.from_prefixed_env()
    celery_init_app(app)
    
    # Login Manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login_page"

    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_email(user_id)

    # Register Blieprints
    from . import airport, auth, country, errors, home, panel, region

    app.register_blueprint(auth.bp)
    app.register_blueprint(home.bp)
    app.register_blueprint(panel.bp)
    app.register_blueprint(errors.bp)
    app.register_blueprint(country.bp)
    app.register_blueprint(region.bp)
    app.register_blueprint(airport.bp)

    return app
