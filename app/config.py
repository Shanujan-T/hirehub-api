from datetime import timedelta
import os
from urllib.parse import quote_plus

from dotenv import load_dotenv

load_dotenv()


def _normalize_mysql_url(url: str) -> str:
    if url.startswith("mysql://"):
        return url.replace("mysql://", "mysql+pymysql://", 1)
    return url


def _build_database_uri() -> str:
    url = os.getenv("DATABASE_URL") or os.getenv("MYSQL_URL")
    if url:
        return _normalize_mysql_url(url)

    host = os.getenv("MYSQLHOST") or os.getenv("DB_HOST", "localhost")
    port = os.getenv("MYSQLPORT") or os.getenv("DB_PORT", "3306")
    user = os.getenv("MYSQLUSER") or os.getenv("DB_USER", "root")
    password = os.getenv("MYSQLPASSWORD") or os.getenv("DB_PASSWORD", "root123")
    name = os.getenv("MYSQLDATABASE") or os.getenv("DB_NAME", "hirehub_db")

    return (
        f"mysql+pymysql://{quote_plus(user)}:{quote_plus(password)}"
        f"@{host}:{port}/{name}"
    )


class Config:
    DB_USER = os.getenv("MYSQLUSER") or os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("MYSQLPASSWORD") or os.getenv("DB_PASSWORD", "root123")
    DB_HOST = os.getenv("MYSQLHOST") or os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("MYSQLPORT") or os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("MYSQLDATABASE") or os.getenv("DB_NAME", "hirehub_db")

    SQLALCHEMY_DATABASE_URI = _build_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 280,
        "connect_args": {"connect_timeout": 10},
    }
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "super-secret-key-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(
        minutes=int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES_MINUTES", "1440"))
    )
    PASSWORD_RESET_TOKEN_EXPIRES = timedelta(
        minutes=int(os.getenv("PASSWORD_RESET_TOKEN_EXPIRES_MINUTES", "60"))
    )
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_ENABLED = os.getenv("RATELIMIT_ENABLED", "true").lower() in ("1", "true", "yes")
    RESUME_UPLOAD_FOLDER = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "uploads",
        "resumes",
    )
    POST_IMAGE_UPLOAD_FOLDER = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "uploads",
        "posts",
    )
    JOB_IMAGE_UPLOAD_FOLDER = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "uploads",
        "jobs",
    )
    COMPANY_LOGO_UPLOAD_FOLDER = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "uploads",
        "companies",
    )


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {}
    JWT_SECRET_KEY = "test-secret-key"
    RATELIMIT_ENABLED = False
