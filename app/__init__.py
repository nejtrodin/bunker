from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_sockets import Sockets
from redis import Redis
import rq
from config import Config


db = SQLAlchemy()
migrate = Migrate()
# timer_clients = list()
sockets = Sockets()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app, db)
    sockets.init_app(app)
    app.redis = Redis.from_url(app.config['REDIS_URL'])
    app.task_queue = rq.Queue('game_tasks', connection=app.redis)

    from app.game import bp as game_bp
    app.register_blueprint(game_bp)

    return app


from app import models
