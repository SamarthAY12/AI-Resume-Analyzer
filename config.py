import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# On Render's free tier, the project source folder isn't reliably writable.
# /tmp is always writable in these container environments, so we default there
# unless a DATABASE_URL is explicitly provided (e.g. a real Postgres URL later).
DB_PATH = os.environ.get("SQLITE_DB_PATH", "/tmp/resume_analyzer.db")


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key-change-this")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + DB_PATH
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", "/tmp/uploads")
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB