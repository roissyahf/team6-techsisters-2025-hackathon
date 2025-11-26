import os
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "postgresql+psycopg://fouziakhan@localhost:5432/career_compass")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Flask-Security-Too
    SECURITY_PASSWORD_HASH = "argon2"
    SECURITY_PASSWORD_SALT = os.getenv("SECURITY_PASSWORD_SALT", "adasdasdewqeqweqw12321312")
    SECURITY_REGISTERABLE = True
    SECURITY_RECOVERABLE = True
    SECURITY_CHANGEABLE = True
    SECURITY_TRACKABLE = True
    SECURITY_SEND_REGISTER_EMAIL = False
    # SECURITY_API_ENABLED = True  # enable if you want JSON endpoints too

    # Email (for recover/confirm in prod)
    MAIL_SERVER = "localhost"
    MAIL_PORT = 25
    MAIL_DEFAULT_SENDER = ("Career Compass", "no-reply@yourapp.tld")
    WTF_CSRF_ENABLED = True
