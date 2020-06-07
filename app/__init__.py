from flask import Flask
from flask_apscheduler import APScheduler
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_sockets import Sockets
from redis import Redis
from config import Config
from apscheduler.schedulers import SchedulerAlreadyRunningError


db = SQLAlchemy()
migrate = Migrate()
sockets = Sockets()
scheduler = APScheduler()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    sockets.init_app(app)
    app.redis = Redis.from_url(app.config['REDIS_URL'])

    from app.game import bp as game_bp
    app.register_blueprint(game_bp)

    try:
        scheduler.init_app(app)
        scheduler.start()
    except SchedulerAlreadyRunningError:
        pass

    return app


from app import models
