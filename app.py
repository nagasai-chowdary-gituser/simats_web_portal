from flask import Flask, request, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import re

app = Flask(__name__)

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "database.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "super_secret_key_finalboss"

db = SQLAlchemy(app)

# ==============================
# DATABASE MODEL
# ==============================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


def safe(value):
    try:
        if not value:
            return 0
        value = value.strip()
        return int(value) if value.isdigit() else 0
    except:
        return 0


# =======================================================
# DEFAULT ROUTE → LOGIN FIRST
# =======================================================
@app.route("/")
def default_route():
    return redirect(url_for("login"))


@app.route("/home")
def index():
    return render_template("index.html")


# =======================================================
# ATTENDANCE
# =======================================================
@app.route("/attendance", methods=["GET", "POST"])
def attendance_calc():
    if request.method == "POST":
        total_class = float(request.form.get("total_classes", 0))
        attended = float(request.form.get("no_of_classes_attended", 0))
        result = round(attended / total_class * 100, 2) if total_class else 0
        return render_template("attendance.html", results=result)
    return render_template("attendance.html")


# =======================================================
# CGPA
# =======================================================
@app.route("/cgpa", methods=["GET", "POST"])
def cgpa_calc():
    if request.method == "POST":
        s = safe(request.form.get("s_grades"))
        a = safe(request.form.get("a_grades"))
        b = safe(request.form.get("b_grades"))
        c = safe(request.form.get("c_grades"))
        d = safe(request.form.get("d_grades"))
        e = safe(request.form.get("e_grades"))

        total_points = s * 10 + a * 9 + b * 8 + c * 7 + d * 6 + e * 5
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


# =======================================================
# REGISTER USER
# =======================================================
@app.route("/register", methods=["GET", "POST"])
def register():
    error = ""

    if request.method == "POST":
        username = request.form["reg_username"].strip()
        email = request.form["reg_email"].strip()
        password = request.form["reg_password"].strip()

        pattern = r"^\d+\.simats@saveetha\.com$"

        if not re.match(pattern, email):
            error = "⚠️ Only SIMATS Email Allowed (example: 192424292.simats@saveetha.com)"
            return render_template("register.html", error=error, username=username, email=email)

        if not username or not email or not password:
            error = "All fields required"
            return render_template("register.html", error=error, username=username, email=email)

        existing = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing:
            error = "User already exists"
            return render_template("register.html", error=error, username=username, email=email)

        #hashed = generate_password_hash(password)
        new_user = User(username=username, email=email, password=password)
        db.session.add(new_user)
        db.session.commit()

        return render_template("register_success.html")

    return render_template("register.html", error="", username="", email="")


# =======================================================
# LOGIN SYSTEM WITH ADMIN ACCESS
# =======================================================
@app.route("/login", methods=["GET", "POST"])
def login():
    message = ""

    if request.method == "POST":
        username = request.form["l_user"]
        password = request.form["l_pass"]

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):

            session["user"] = username

            # ADMIN LOGIN CHECK
            if username == "admin":
                return redirect(url_for("admin_dashboard"))

            return redirect(url_for("index"))

        else:
            message = "Invalid username or password"

    return render_template("login.html", message=message)


# =======================================================
# ADMIN DASHBOARD — ONLY ADMIN CAN SEE USERS
# =======================================================
@app.route("/admin")
def admin_dashboard():

    # not logged in
    if "user" not in session:
        return redirect(url_for("login"))

    # not admin user
    if session["user"] != "admin":
        return "❌ Access Denied — Admin Only!"

    users = User.query.all()
    return render_template("admin.html", users=users)


# =======================================================
# LOGOUT
# =======================================================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# =======================================================
# START APP
# =======================================================
if __name__ == "__main__":
    app.run(debug=True, port=5050)
