from extensions import db
from datetime import datetime


class Report(db.Model):
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    filename = db.Column(db.String(200), nullable=False)
    ats_score = db.Column(db.Integer, nullable=True)
    missing_skills = db.Column(db.Text, nullable=True)     # stored as comma-separated text
    suggestions = db.Column(db.Text, nullable=True)         # stored as plain text
    job_description = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
