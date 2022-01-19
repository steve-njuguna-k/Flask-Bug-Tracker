from flask import Flask
from flask_bcrypt import Bcrypt

app = Flask(__name__)

app.config.from_object(DevConfig)
bcrypt = Bcrypt(app)

from app import views