from flask import Flask
from config import DevelopConfig
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)
app.config.from_object(DevelopConfig)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
timer_clients = list()


from app import routes, models, backend
