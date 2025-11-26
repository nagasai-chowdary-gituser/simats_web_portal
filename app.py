from flask import Flask, request, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import re
from functools import wraps

app = Flask(__name__)

# -----------------------------
# DB CONFIG
# -----------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "database.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "super_secret_key"

db = SQLAlchemy(app)

# -----------------------------
# USER MODEL (WITH is_admin)
# -----------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)


# -----------------------------
# CREATE TABLES + DEFAULT ADMIN (Flask 3 safe)
# -----------------------------
admin_created = False

@app.before_request
def create_admin_once():
    """
    Runs before every request, but only creates admin once using a flag.
    Flask 3 removed before_first_request, so this is the safe workaround.
    """
    global admin_created

    if not admin_created:
        db.create_all()

        admin = User.query.filter_by(username="admin").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@system.com",
                password=generate_password_hash("admin123"),
                is_admin=True
            )
            db.session.add(admin)
            db.session.commit()
            print("🔥 Admin Created: admin / admin123")

        admin_created = True


# -----------------------------
# HELPERS
# -----------------------------
def safe(v):
    try:
        if not v:
            return 0
        v = v.strip()
        return int(v) if v.isdigit() else 0
    except:
        return 0


def login_required(admin_only=False):
    """
    Decorator to protect routes.
    - If user not logged in -> redirect to /login
    - If admin_only=True and user is not admin -> block
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))

            if admin_only and not session.get("is_admin"):
                return "❌ Access denied – Admin only"

            return f(*args, **kwargs)
        return wrapper
    return decorator


# -----------------------------
# DEFAULT ROUTE
# -----------------------------
@app.route("/")
def default_route():
    return redirect(url_for("login"))


# -----------------------------
# HOME (PROTECTED)
# -----------------------------
@app.route("/home")
@login_required()
def index():
    return render_template("index.html")


# -----------------------------
# ATTENDANCE (PROTECTED)
# -----------------------------
@app.route("/attendance", methods=["GET", "POST"])
@login_required()
def attendance_calc():
    if request.method == "POST":
        total = float(request.form.get("total_classes", 0))
        attended = float(request.form.get("no_of_classes_attended", 0))
        result = round(attended / total * 100, 2) if total else 0
        return render_template("attendance.html", results=result)
    return render_template("attendance.html")


# -----------------------------
# CGPA (PROTECTED)
# -----------------------------
@app.route("/cgpa", methods=["GET", "POST"])
@login_required()
def cgpa_calc():
    if request.method == "POST":
        s = safe(request.form.get("s_grades"))
        a = safe(request.form.get("a_grades"))
        b = safe(request.form.get("b_grades"))
        c = safe(request.form.get("c_grades"))
        d = safe(request.form.get("d_grades"))
        e = safe(request.form.get("e_grades"))

        total_points = s*10 + a*9 + b*8 + c*7 + d*6 + e*5
        total_subs = s + a + b + c + d + e

        if not total_subs:
            return render_template("cgpa.html", results="0.00", words="Enter at least one subject")

        cgpa = round(total_points / total_subs, 2)

        if cgpa > 9:
            words = "Excellent ⭐"
        elif cgpa >= 8:
            words = "Very Good 👍"
        elif cgpa >= 7:
            words = "Good 🙂"
        elif cgpa >= 6:
            words = "Average 😐"
        else:
            words = "Needs Improvement ⚠️"

        return render_template("cgpa.html", results=cgpa, words=words)

    return render_template("cgpa.html", results="", words="")


# -----------------------------
# REGISTER
# -----------------------------
@app.route("/register", methods=["GET", "POST"])
def register():
    error = ""

    if request.method == "POST":
        username = request.form["reg_username"].strip()
        email = request.form["reg_email"].strip()
        password = request.form["reg_password"].strip()

        # Block "admin" username for normal users
        if username.lower() == "admin":
            error = "❌ Username 'admin' is reserved."
            return render_template("register.html", error=error)

        # SIMATS email validation
        pattern = r"^\d+\.simats@saveetha\.com$"
        if not re.match(pattern, email):
            error = "⚠ Only SIMATS Email allowed (Ex: 192424292.simats@saveetha.com)"
            return render_template("register.html", error=error)

        if not username or not email or not password:
            error = "All fields required"
            return render_template("register.html", error=error)

        existing = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing:
            error = "User already exists"
            return render_template("register.html", error=error)

        hashed = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed, is_admin=False)

        db.session.add(new_user)
        db.session.commit()

        return render_template("register_success.html")

    return render_template("register.html", error=error)


# -----------------------------
# LOGIN
# -----------------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    message = ""
    shake = False

    if request.method == "POST":
        username = request.form["l_user"].strip()
        password = request.form["l_pass"].strip()

        user = User.query.filter_by(username=username).first()

        if not user:
            message = "❌ No username found"
            shake = True
            return render_template("login.html", message=message, shake=shake)

        if not check_password_hash(user.password, password):
            message = "❌ Incorrect password"
            shake = True
            return render_template("login.html", message=message, shake=shake)

        # Success login -> Save session
        session["user_id"] = user.id
        session["username"] = user.username
        session["is_admin"] = user.is_admin

        if user.is_admin:
            return redirect(url_for("admin_page"))
        else:
            return redirect(url_for("index"))

    return render_template("login.html", message=message, shake=shake)


# -----------------------------
# LOGOUT
# -----------------------------
@app.route("/logout")
@login_required()
def logout():
    session.clear()
    return redirect(url_for("login"))


# -----------------------------
# ADMIN PAGE (ADMIN ONLY)
# -----------------------------
@app.route("/admin")
@login_required(admin_only=True)
def admin_page():
    users = User.query.all()
    return render_template("admin.html", users=users)
# -----------------------------
# CHANGE PASSWORD (PROTECTED)
# -----------------------------
@app.route("/change_password", methods=["GET", "POST"])
@login_required()
def change_password():
    message = ""
    success = False

    if request.method == "POST":
        old_pass = request.form["old_password"]
        new_pass = request.form["new_password"]
        confirm_pass = request.form["confirm_password"]

        user = User.query.get(session["user_id"])

        # Check old password
        if not check_password_hash(user.password, old_pass):
            message = "❌ Old password is incorrect"
            return render_template("change_password.html", message=message, success=success)

        # Check match
        if new_pass != confirm_pass:
            message = "❌ New passwords do not match"
            return render_template("change_password.html", message=message, success=success)

        # Update new password
        user.password = generate_password_hash(new_pass)
        db.session.commit()

        success = True
        message = "✅ Password changed successfully!"
        return render_template("change_password.html", message=message, success=success)

    return render_template("change_password.html", message=message, success=success)



# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5050)