from flask import Flask
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import flask_jwt_extended 
from flask import jsonify
from flask_jwt_extended import JWTManager
from flask_jwt_extended.exceptions import NoAuthorizationError
from flask_mail import Mail
import os
from dotenv import load_dotenv


load_dotenv()
os.makedirs('uploads', exist_ok=True)

app = Flask(__name__)
app.config.from_object('app.config.Config')
db = SQLAlchemy(app)
migrate = Migrate(app, db)
jwt = flask_jwt_extended.JWTManager(app)
mail = Mail(app)
# CORS(app)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)


@jwt.unauthorized_loader
def unauthorized_response(callback):
    return jsonify({"error": "Missing or invalid authorization header"}), 401

@jwt.invalid_token_loader
def invalid_token_response(reason):
    return jsonify({"error": f"Invalid token: {reason}"}), 422

@jwt.expired_token_loader
def expired_token_response(jwt_header, jwt_payload):
    return jsonify({"error": "Token has expired"}), 401

from app import routes, models