import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# In production (Render), set DATABASE_URL to a Postgres connection string.
# Locally, with no DATABASE_URL set, we fall back to a SQLite file.
_raw_db_url = os.environ.get("DATABASE_URL")

if _raw_db_url:
    # SQLAlchemy 1.4+/2.x requires "postgresql://", but some providers
    # (including Render) still hand out "postgres://" — normalize it.
    if _raw_db_url.startswith("postgres://"):
        _raw_db_url = _raw_db_url.replace("postgres://", "postgresql://", 1)
    DATABASE_URI = _raw_db_url
else:
    DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "resume_analyzer.db")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-this")

    SQLALCHEMY_DATABASE_URI = DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "/tmp/uploads")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB