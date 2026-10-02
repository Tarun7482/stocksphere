import os
import logging

from flask import Flask
from db import db, Base
from flask_login import LoginManager


app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# configure the database, using external PostgreSQL from Render
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://hackindia_652w_user:dx8XzlXYo01FhlVy5pBqg4ZJcgT1EWIA@dpg-cvmcpq15pdvs73f1vn1g-a.singapore-postgres.render.com/hackindia_652w"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
# initialize the app with the extension, flask-sqlalchemy >= 3.0.x
db.init_app(app)

# Configure login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from models import User  # moved import here to avoid circular import
    return db.session.get(User, int(user_id))

with app.app_context():
    # Make sure to import the models here or their tables won't be created
    import models  # noqa: F401

    db.create_all()

# Import routes at the end to avoid circular imports
from routes import *
