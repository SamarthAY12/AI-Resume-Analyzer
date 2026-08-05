import os
from dotenv import load_dotenv

load_dotenv()

from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user

from config import Config
from extensions import db, bcrypt, login_manager
from models.user import User
from models.report import Report
from resume_utils import extract_text_from_resume, analyze_resume_with_gemini

from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
bcrypt.init_app(app)
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


ALLOWED_EXTENSIONS = {"pdf", "docx"}


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash("Email already registered!")
            return redirect(url_for("register"))

        hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")

        user = User(name=name, email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()

        flash("Registered successfully! Please log in.")
        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("dashboard"))

        flash("Invalid email or password")
        return redirect(url_for("login"))

    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/dashboard")
@login_required
def dashboard():
    reports = (
        Report.query.filter_by(user_id=current_user.id)
        .order_by(Report.created_at.desc())
        .all()
    )
    return render_template("dashboard.html", reports=reports)


@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        file = request.files.get("resume")
        job_description = request.form.get("job_description", "")

        if not file or file.filename == "":
            flash("Please choose a resume file.")
            return redirect(url_for("upload"))

        if not allowed_file(file.filename):
            flash("Only PDF or DOCX files are supported.")
            return redirect(url_for("upload"))

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        file.save(filepath)

        try:
            resume_text = extract_text_from_resume(filepath)
            result = analyze_resume_with_gemini(resume_text, job_description)
        except Exception as e:
            flash(f"Analysis failed: {e}")
            return redirect(url_for("upload"))

        report = Report(
            user_id=current_user.id,
            filename=filename,
            ats_score=result.get("ats_score", 0),
            missing_skills=", ".join(result.get("missing_skills", [])),
            suggestions="\n".join(result.get("suggestions", [])),
            job_description=job_description,
        )
        db.session.add(report)
        db.session.commit()

        return redirect(url_for("report", report_id=report.id))

    return render_template("upload.html")


@app.route("/report/<int:report_id>")
@login_required
def report(report_id):
    report_obj = Report.query.get_or_404(report_id)

    if report_obj.user_id != current_user.id:
        flash("You don't have access to that report.")
        return redirect(url_for("dashboard"))

    missing_skills = [s.strip() for s in report_obj.missing_skills.split(",") if s.strip()]
    suggestions = [s for s in report_obj.suggestions.split("\n") if s.strip()]

    return render_template(
        "report.html",
        report=report_obj,
        missing_skills=missing_skills,
        suggestions=suggestions,
    )


with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(debug=True)