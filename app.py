from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import json, os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")

if not app.config["SECRET_KEY"]:
    raise RuntimeError("SECRET_KEY environment variable is required.")
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///careerpilot.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    skills_json = db.Column(db.Text, default="[]")
    role = db.Column(db.String(20), default="user", nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    @property
    def skills(self):
        try:
            return json.loads(self.skills_json or "[]")
        except (TypeError, json.JSONDecodeError):
            return []

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    company = db.Column(db.String(120), nullable=False)
    location = db.Column(db.String(120), nullable=False)
    job_type = db.Column(db.String(60), default="Full-time")
    salary = db.Column(db.String(80), default="Not specified")
    description = db.Column(db.Text, default="")
    skills_json = db.Column(db.Text, default="[]")

    @property
    def skills(self):
        try:
            return json.loads(self.skills_json or "[]")
        except (TypeError, json.JSONDecodeError):
            return []

class SavedJob(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    job_id = db.Column(db.Integer, db.ForeignKey("job.id"), nullable=False)
    status = db.Column(db.String(30), default="Saved")
    __table_args__ = (db.UniqueConstraint("user_id", "job_id", name="unique_user_job"),)


def match_data(
    user_skills,
    job_skills,
    job_title="",
    job_description="",
    company=""
):
    """Recommend jobs using TF-IDF and cosine similarity."""

    mine = {
        skill.strip().lower()
        for skill in user_skills if skill.strip()
    }

    required = {
        skill.strip().lower()
        for skill in job_skills if skill.strip()
    }

    matched = sorted(mine & required)
    missing = sorted(required - mine)

    profile_text = " ".join(user_skills).strip()

    job_text = " ".join([
        job_title,
        company,
        " ".join(job_skills),
        job_description
    ]).strip()

    if not profile_text or not job_text:
        return 0, matched, missing, 0

    vectorizer = TfidfVectorizer(
        stop_words="english",
        ngram_range=(1, 2)
    )

    matrix = vectorizer.fit_transform([
        profile_text,
        job_text
    ])

    similarity = cosine_similarity(
        matrix[0:1],
        matrix[1:2]
    )[0][0]

    ml_score = round(float(similarity) * 100)

    skill_score = (
        round(len(matched) / len(required) * 100)
        if required else 0
    )

    return skill_score, matched, missing, ml_score


def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access your dashboard.", "info")
            return redirect(url_for("login"))

        user = db.session.get(User, session["user_id"])

        if user is None or not user.is_active:
            session.clear()
            flash(
                "Your session is no longer active. Please contact support if needed.",
                "danger"
            )
            return redirect(url_for("login"))

        return fn(*args, **kwargs)

    return wrapper

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in first.", "info")
            return redirect(url_for("login"))

        user = db.session.get(User, session["user_id"])

        if user is None or not user.is_active:
            session.clear()
            flash(
                "Your account is inactive. Please contact support.",
                "danger"
            )
            return redirect(url_for("login"))

        if user.role != "admin":
            flash(
                "Administrator access is required.",
                "danger"
            )
            return redirect(url_for("dashboard"))

        return fn(*args, **kwargs)

    return wrapper


@app.context_processor
def inject_user():
    user = db.session.get(User, session.get("user_id")) if session.get("user_id") else None
    return {"current_user": user}

def seed_jobs():
    if Job.query.count():
        return
    rows = [
        ("Python Developer Intern", "CodeCraft Labs", "Noida, India", "Internship", "₹10,000–₹18,000/month",
         "Build Python applications, write clean code, and work with APIs.",
         ["Python", "SQL", "Git", "Flask"]),
        ("Machine Learning Intern", "AIML Works", "Remote", "Internship", "₹12,000–₹20,000/month",
         "Prepare datasets, train baseline models, and evaluate model performance.",
         ["Python", "Machine Learning", "Pandas", "NumPy", "SQL"]),
        ("Frontend Developer Intern", "PixelBridge", "Delhi NCR", "Internship", "₹8,000–₹15,000/month",
         "Create responsive web interfaces and collaborate with backend developers.",
         ["HTML", "CSS", "JavaScript", "Bootstrap", "Git"]),
        ("Data Analyst Intern", "InsightSpring", "Gurugram, India", "Internship", "₹10,000–₹16,000/month",
         "Clean datasets, analyse trends, and create clear reports and visualisations.",
         ["Python", "SQL", "Excel", "Pandas", "Power BI"]),
        ("Flask Backend Trainee", "LaunchStack", "Hybrid — Noida", "Full-time", "₹3–5 LPA",
         "Develop REST endpoints, connect databases, and test backend workflows.",
         ["Python", "Flask", "SQLite", "SQL", "Git"]),
        ("Junior Data Scientist", "Northstar Analytics", "Remote", "Full-time", "₹5–8 LPA",
         "Support experiments, feature engineering, and model evaluation.",
         ["Python", "Machine Learning", "Statistics", "Pandas", "NumPy"]),
        ("Web Developer Trainee", "WebNest Studio", "Ghaziabad, India", "Full-time", "₹2.5–4 LPA",
         "Maintain web pages and implement responsive components.",
         ["HTML", "CSS", "JavaScript", "Bootstrap", "SQL"]),
        ("AI Research Assistant", "FutureMind Lab", "Delhi, India", "Internship", "₹12,000–₹22,000/month",
         "Assist with experiments and document model results.",
         ["Python", "Machine Learning", "NumPy", "Statistics", "Git"]),
    ]
    for title, company, location, job_type, salary, description, skills in rows:
        db.session.add(Job(title=title, company=company, location=location, job_type=job_type,
                           salary=salary, description=description, skills_json=json.dumps(skills)))
    db.session.commit()

@app.route("/")
def home():
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    return render_template("home.html", job_count=Job.query.count())

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or not email or len(password) < 6:
            flash("Enter your name, a valid email, and a password of at least 6 characters.", "danger")
        elif User.query.filter_by(email=email).first():
            flash("An account with that email already exists. Please log in.", "warning")
        else:
            user = User(name=name, email=email, password_hash=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            session["user_id"] = user.id
            flash("Account created. Add your skills to improve your matches!", "success")
            return redirect(url_for("profile"))
    return render_template("auth.html", mode="register")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password_hash, password):
            if not user.is_active:
                flash(
                    "Your account has been suspended. Please contact support.",
                    "danger"
                )
                return render_template("auth.html", mode="login")

            session.clear()
            session["user_id"] = user.id
            flash("Welcome back!", "success")
            return redirect(url_for("dashboard"))

        flash("Incorrect email or password.", "danger")

    return render_template("auth.html", mode="login")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("home"))

@app.route("/dashboard")
@login_required
def dashboard():
    user = db.session.get(User, session["user_id"])
    jobs = Job.query.order_by(Job.title).all()
    ranked = []
    for job in jobs:
        skill_score, matched, missing, ml_score = match_data(
            user.skills,
            job.skills,
            job.title,
            job.description,
            job.company
        )
        ranked.append({
            "job": job,
            "percent": skill_score,
            "ml_score": ml_score,
            "matched": matched,
            "missing": missing
        })
    ranked.sort(
        key=lambda item: item["ml_score"],
        reverse=True
    )
    print("TOTAL RECOMMENDATIONS:", len(ranked))
    print("TOP RECOMMENDATIONS:", [
        (item["job"].title, item["percent"], item["ml_score"])
        for item in ranked[:5]
    ])
    return render_template(
    "dashboard.html",
    user=user,
    recommendations=ranked,
    total_jobs=Job.query.count(),
    skill_count=len(user.skills),
    saved_count=SavedJob.query.filter_by(user_id=user.id).count()
)


@app.route("/admin")
@admin_required
def admin_dashboard():
    users = User.query.order_by(User.id.desc()).all()

    print("ADMIN SESSION USER ID:", session.get("user_id"))
    for u in users:
        print("USER:", u.id, u.email, u.role, u.is_active)

    return render_template(
        "admin.html",
        users=users
    )
 
@app.route("/admin/users/<int:user_id>/toggle-status", methods=["POST"])
@admin_required
def toggle_user_status(user_id):
    target_user = db.session.get(User, user_id)

    if target_user is None:
        flash("User not found.", "danger")
        return redirect(url_for("admin_dashboard"))

    if target_user.id == session.get("user_id"):
        flash("You cannot suspend your own account.", "danger")
        return redirect(url_for("admin_dashboard"))

    if target_user.role == "admin":
        flash("Administrator accounts cannot be suspended here.", "danger")
        return redirect(url_for("admin_dashboard"))

    target_user.is_active = not target_user.is_active
    db.session.commit()

    if target_user.is_active:
        flash("User account reactivated successfully.", "success")
    else:
        flash("User account suspended successfully.", "success")

    return redirect(url_for("admin_dashboard"))


    ranked.sort(
        key=lambda item: (item["ml_score"], item["job"].title),
        reverse=True
    )
    saved_count = SavedJob.query.filter_by(user_id=user.id).count()
    return render_template("dashboard.html", ranked=ranked[:4], total_jobs=len(jobs),
                           saved_count=saved_count, skill_count=len(user.skills))

@app.route("/jobs")
@login_required
def jobs():
    user = db.session.get(User, session["user_id"])
    query = request.args.get("q", "").strip()
    location = request.args.get("location", "").strip()
    job_type = request.args.get("type", "").strip()
    all_jobs = Job.query.order_by(Job.title).all()
    results = []
    for job in all_jobs:
        if query and query.lower() not in (job.title + " " + job.company + " " + job.description + " " + " ".join(job.skills)).lower():
            continue
        if location and location.lower() not in job.location.lower():
            continue
        if job_type and job_type != job.job_type:
            continue
        skill_score, matched, missing, ml_score = match_data(
            user.skills,
            job.skills,
            job.title,
            job.description,
            job.company
        )
        results.append({
            "job": job,
            "percent": skill_score,
            "skill_score": skill_score,
            "matched": matched,
            "missing": missing,
            "ml_score": ml_score
        })
    results.sort(key=lambda item: item["ml_score"], reverse=True)
    print("JOBS DEBUG:", len(results))
    print("FIRST RESULT:", results[0] if results else "No results")
    return render_template("jobs.html", results=results, q=query, location=location, selected_type=job_type)

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = db.session.get(User, session["user_id"])
    if request.method == "POST":
        user.name = request.form.get("name", "").strip() or user.name
        raw = request.form.get("skills", "")
        skills = list(dict.fromkeys(s.strip().title() for s in raw.replace("\n", ",").split(",") if s.strip()))
        user.skills_json = json.dumps(skills)
        db.session.commit()
        flash("Your profile and skills have been updated.", "success")
        return redirect(url_for("profile"))
    return render_template("profile.html", user=user)




# ------------------------- Career DNA -------------------------
CAREER_SKILL_GROUPS = {
    "Programming": {"python", "java", "c", "c++", "javascript", "typescript", "php", "ruby"},
    "Web Development": {"html", "css", "javascript", "typescript", "bootstrap", "react", "flask", "django", "node.js"},
    "Data & Analytics": {"sql", "excel", "pandas", "numpy", "power bi", "tableau", "statistics", "data analysis"},
    "AI & Machine Learning": {"machine learning", "deep learning", "tensorflow", "pytorch", "scikit-learn", "numpy", "pandas", "statistics"},
    "Databases": {"sql", "sqlite", "mysql", "postgresql", "mongodb", "database"},
    "Tools & Collaboration": {"git", "github", "docker", "linux", "agile", "communication", "teamwork"},
}

@app.route("/career-dna")
@login_required
def career_dna():
    user = db.session.get(User, session["user_id"])
    skills = user.skills
    normalized = {skill.strip().casefold() for skill in skills if skill.strip()}

    # A skill can support more than one career area. Counts are transparent
    # rule-based indicators, not AI-generated assessments.
    categories = []
    for category, keywords in CAREER_SKILL_GROUPS.items():
        matched_skills = sorted(
            [skill for skill in skills if skill.strip().casefold() in keywords],
            key=str.casefold
        )
        if matched_skills:
            categories.append({
                "name": category,
                "skills": matched_skills,
                "count": len(matched_skills),
                "percent": min(100, round(len(matched_skills) / max(4, len(keywords & normalized)) * 100))
            })
    categories.sort(key=lambda item: (item["count"], item["name"]), reverse=True)

    # Recommend directions from the existing job catalogue by skill overlap.
    directions = []
    for job in Job.query.order_by(Job.title).all():
        score, matched, missing, ml_score = match_data(
            skills, job.skills, job.title, job.description, job.company
        )
        directions.append({
            "job": job,
            "percent": score,
            "matched": matched,
            "missing": missing,
            "ml_score": ml_score
        })
    directions.sort(key=lambda item: (item["percent"], item["ml_score"]), reverse=True)

    top_skills = skills[:8]
    profile_strength = min(100, round(len(skills) / 8 * 100))
    return render_template(
        "career_dna.html",
        user=user,
        skills=skills,
        categories=categories,
        directions=directions[:3],
        top_skills=top_skills,
        profile_strength=profile_strength,
        saved_count=SavedJob.query.filter_by(user_id=user.id).count(),
    )


@app.route("/job/<int:job_id>")
@login_required
def job_detail(job_id):
    user = db.session.get(User, session["user_id"])
    job = db.get_or_404(Job, job_id)

    percent, matched, missing, ml_score = match_data(
        user.skills,
        job.skills,
        job.title,
        job.description,
        job.company
    )

    saved = SavedJob.query.filter_by(
        user_id=user.id,
        job_id=job.id
    ).first() is not None

    return render_template(
        "job_detail.html",
        job=job,
        percent=percent,
        matched=matched,
        missing=missing,
        ml_score=ml_score,
        saved=saved
    )

@app.route("/job/<int:job_id>/save", methods=["POST"])
@login_required
def save_job(job_id):
    user = db.session.get(User, session["user_id"])
    job = db.get_or_404(Job, job_id)
    saved = SavedJob.query.filter_by(user_id=user.id, job_id=job.id).first()
    if saved:
        db.session.delete(saved)
        flash("Job removed from your saved list.", "info")
    else:
        db.session.add(SavedJob(user_id=user.id, job_id=job.id, status="Saved"))
        flash("Job saved successfully.", "success")
    db.session.commit()
    return redirect(request.referrer or url_for("jobs"))

@app.route("/saved")
@login_required
def saved_jobs():
    user = db.session.get(User, session["user_id"])
    saved = SavedJob.query.filter_by(user_id=user.id).all()
    items = []
    for entry in saved:
        job = db.get_or_404(Job, entry.job_id)
        if job:
            skill_score, matched, missing, ml_score = match_data(
    user.skills,
    job.skills,
    job.title,
    job.description,
    job.company
)
            items.append({
    "job": job,
    "percent": skill_score,
    "skill_score": skill_score,
    "matched": matched,
    "missing": missing,
    "ml_score": ml_score,
    "status": entry.status
})
    items.sort(key=lambda item: item["skill_score"], reverse=True)
    return render_template("saved.html", items=items)

with app.app_context():
    db.create_all()

    from sqlalchemy import inspect, text

    inspector = inspect(db.engine)
    user_columns = {
        column["name"]
        for column in inspector.get_columns("user")
    }

    with db.engine.begin() as connection:
        if "role" not in user_columns:
            connection.execute(
                text(
                    "ALTER TABLE user "
                    "ADD COLUMN role VARCHAR(20) "
                    "NOT NULL DEFAULT 'user'"
                )
            )

        if "is_active" not in user_columns:
            connection.execute(
                text(
                    "ALTER TABLE user "
                    "ADD COLUMN is_active BOOLEAN "
                    "NOT NULL DEFAULT 1"
                )
            )

    seed_jobs()

if __name__ == "__main__":
    app.run(debug=False)
