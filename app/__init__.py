from flask import Flask
from dotenv import load_dotenv

app = Flask(__name__)

load_dotenv('.env')
app.config.from_pyfile('config.py')

from app import views