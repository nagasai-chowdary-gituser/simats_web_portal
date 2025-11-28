from flask import Flask, request, render_template, redirect, url_for, session, send_file
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import re
from functools import wraps
import uuid

# Capstone generator imports
from ai_capstone.ai_engine import generate_ai_content
from ai_capstone.create_ai_docx import create_ai_docx
from ai_capstone.utils.docx_filler import merge_docx


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
# USER MODEL
# -----------------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    reg_number = db.Column(db.String(20), nullable=True)
    password = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    security_bike = db.Column(db.String(120), nullable=True)

# -----------------------------
# CREATE ADMIN IF NOT EXISTS
# -----------------------------
admin_created = False

def extract_reg_no(email: str):
    try:
        return email.split(".")[0]
    except:
        return ""

@app.before_request
def create_admin_once():
    global admin_created

    if not admin_created:
        db.create_all()

        admin = User.query.filter_by(username="admin").first()
        if not admin:
            admin = User(
                username="admin",
                email="admin@system.com",
                reg_number="ADMIN",
                password=generate_password_hash("admin123"),
                is_admin=True,
                security_bike="adminbike"
            )
            db.session.add(admin)
            db.session.commit()
            print("🔥 Admin Created: admin / admin123")

        admin_created = True

# -----------------------------
# HELPERS
# -----------------------------
def login_required(admin_only=False):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if "user_id" not in session:
                return redirect(url_for("login"))
            if admin_only and not session.get("is_admin"):
                return "❌ Access Denied – Admin Only"
            return f(*args, **kwargs)
        return wrapper
    return decorator


# -----------------------------
# ROUTES
# -----------------------------
@app.route("/")
def default_route():
    return redirect(url_for("login"))

@app.route("/home")
@login_required()
def index():
    return render_template("index.html")

# -----------------------------
# USER PROFILE PAGE
# -----------------------------
@app.route("/profile")
@login_required()
def profile():
    user = User.query.get(session["user_id"])
    return render_template("profile.html", user=user)

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
        bike = request.form["reg_bike"].strip()

        if username.lower() == "admin":
            return render_template("register.html", error="❌ 'admin' is reserved")

        pattern = r"^\d+\.simats@saveetha\.com$"
        if not re.match(pattern, email):
            return render_template("register.html", error="⚠ Only SIMATS Email allowed")

        existing = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        if existing:
            return render_template("register.html", error="User already exists")

        reg_no = extract_reg_no(email)

        user = User(
            username=username,
            email=email,
            reg_number=reg_no,
            password=generate_password_hash(password),
            is_admin=False,
            security_bike=bike
        )
        db.session.add(user)
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
            return render_template("login.html", shake=True, message="❌ Username not found")

        if not check_password_hash(user.password, password):
            return render_template("login.html", shake=True, message="❌ Wrong password")

        session["user_id"] = user.id
        session["username"] = user.username
        session["is_admin"] = user.is_admin

        if user.is_admin:
            return redirect(url_for("admin_page"))
        return redirect(url_for("index"))

    return render_template("login.html", message=message, shake=shake)

# -----------------------------
# FORGOT PASSWORD
# -----------------------------
@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    message = ""

    if request.method == "POST":
        username = request.form["username"].strip()
        bike = request.form["bike"].strip()
        new_pass = request.form["new_password"].strip()

        user = User.query.filter_by(username=username).first()

        if not user:
            return render_template("forgot_password.html", message="❌ Username not found")

        if user.security_bike.lower() != bike.lower():
            return render_template("forgot_password.html", message="❌ Wrong bike name")

        user.password = generate_password_hash(new_pass)
        db.session.commit()

        return render_template("forgot_password.html", message="✅ Password Updated Successfully!")

    return render_template("forgot_password.html", message=message)

# -----------------------------
# USER CHANGE PASSWORD
# -----------------------------
@app.route("/change_password", methods=["GET", "POST"])
@login_required()
def change_password():
    message = ""
    if request.method == "POST":

        old = request.form["old_password"]
        new = request.form["new_password"]
        conf = request.form["confirm_password"]

        user = User.query.get(session["user_id"])

        if not check_password_hash(user.password, old):
            return render_template("change_password.html", message="❌ Old password incorrect")

        if new != conf:
            return render_template("change_password.html", message="❌ Passwords do not match")

        user.password = generate_password_hash(new)
        db.session.commit()

        return render_template("change_password.html", message="✅ Password changed!")

    return render_template("change_password.html", message=message)

# -----------------------------
# ADMIN PAGE WITH SEARCH + COUNT
# -----------------------------
@app.route("/admin")
@login_required(admin_only=True)
def admin_page():

    search = request.args.get("search", "").strip()

    if search:
        users = User.query.filter(User.reg_number.like(f"%{search}%")).all()
    else:
        users = User.query.all()

    user_count = len(User.query.all())

    return render_template("admin.html", users=users, search=search, user_count=user_count)


# -----------------------------
# LOGOUT
# -----------------------------
@app.route("/logout")
@login_required()
def logout():
    session.clear()
    return redirect(url_for("login"))
# -----------------------------
# ATTENDANCE PAGE
# -----------------------------
@app.route("/attendance", methods=["GET", "POST"])
@login_required()
def attendance_calc():
    if request.method == "POST":
        try:
            total = float(request.form.get("total_classes", 0))
            attended = float(request.form.get("no_of_classes_attended", 0))
            result = round(attended / total * 100, 2) if total else 0
        except:
            result = 0

        return render_template("attendance.html", results=result)

    return render_template("attendance.html", results="")
# -----------------------------
# CGPA PAGE
# -----------------------------
@app.route("/cgpa", methods=["GET", "POST"])
@login_required()
def cgpa_calc():
    if request.method == "POST":

        # Get values safely
        def safe_int(v):
            try:
                if v.strip() == "":
                    return 0
                return int(v)
            except:
                return 0

        s = safe_int(request.form.get("s_grades", "0"))
        a = safe_int(request.form.get("a_grades", "0"))
        b = safe_int(request.form.get("b_grades", "0"))
        c = safe_int(request.form.get("c_grades", "0"))
        d = safe_int(request.form.get("d_grades", "0"))
        e = safe_int(request.form.get("e_grades", "0"))

        total_points = s*10 + a*9 + b*8 + c*7 + d*6 + e*5
        total_subs = s + a + b + c + d + e

        if total_subs == 0:
            return render_template("cgpa.html", results="0.00", words="Please enter valid values")

        cgpa = round(total_points / total_subs, 2)

        # Words based on CGPA
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
@app.route("/capstone")
def capstone_form():
    return render_template("capstone_form.html")
@app.route("/generate_capstone", methods=["POST"])
def generate_capstone():

    title = request.form.get("title")

    # 1. Generate AI content
    sections = generate_ai_content(title)

    # Paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "ai_capstone", "output")
    os.makedirs(output_dir, exist_ok=True)

    # 2. Create AI chapters as DOCX
    ai_docx_path = os.path.join(output_dir, "ai_chapters.docx")
    create_ai_docx(sections, ai_docx_path)

    # 3. First 5 DOCX pages (unchanged)
    docx_dir = os.path.join(base_dir, "ai_capstone", "templates_docx")
    fixed_pages = [
        os.path.join(docx_dir, "page1_title.docx"),
        os.path.join(docx_dir, "page2_declaration.docx"),
        os.path.join(docx_dir, "page3_bonafide.docx"),
        os.path.join(docx_dir, "page4_acknowledgement.docx"),
    ]

    # 4. Merge (fixed pages + AI chapters)
    final_docx = os.path.join(output_dir, "final_capstone.docx")
    merge_docx(fixed_pages + [ai_docx_path], final_docx)

    # 5. Send Word file to user
    return send_file(
        final_docx,
        as_attachment=True,
        download_name="Capstone_Report.docx"
    )






# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5050)
