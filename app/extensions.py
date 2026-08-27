from dotenv import load_dotenv
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from google import genai

# db nesnesini hiçbir parametre vermeden başlatıyoruz.
db = SQLAlchemy()
jwt = JWTManager()

load_dotenv()

genai_client = genai.Client()
