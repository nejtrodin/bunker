from flask import Flask
from flask_apscheduler import APScheduler
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_sockets import Sockets
from redis import Redis
from config import Config
from apscheduler.schedulers import SchedulerAlreadyRunningError
from flask_talisman import Talisman


db = SQLAlchemy()
migrate = Migrate()
sockets = Sockets()
scheduler = APScheduler()

csp = {
    'default-src': [
        '\'self\'',
        'meet.jit.si',
        '*.jitsi.net',
        'web-cdn.jitsi.net',
    ],
    'script-src': [
        '\'self\'',
        '\'unsafe-inline\'',
        '*',
        'meet.jit.si',
        '*.jitsi.net',
        'web-cdn.jitsi.net',
    ],
    'style-src': [
        '\'self\'',
        '\'unsafe-inline\'',
    ],
    'connect-src': [
        '*'
    ]
}


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    Talisman(app, content_security_policy=csp)

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
