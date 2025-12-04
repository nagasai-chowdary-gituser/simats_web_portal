from flask import Flask, request, render_template, redirect, url_for, session, send_file, send_from_directory, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
import re
from functools import wraps
import uuid
import json

# Capstone generator imports
#from ai_capstone.ai_engine import generate_ai_content
#from ai_capstone.create_ai_docx import create_ai_docx
#from ai_capstone.utils.docx_filler import merge_docx

# AI-BOT imports
#from src.config.config import Config
#from src.document_ingestion.document_processor import DocumentProcessor
#from src.vectorstore.vectorstore import VectorStore
#from src.graph_builder.graph_builder import GraphBuilder
#from src.memory.persistent_memory import UserMemoryManager


import time
# Payments Gateway
import razorpay


app = Flask(__name__)
app.config["SESSION_PERMANENT"] = False

app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql+psycopg2://postgres.qoyyvcnyijgjtdeodicu:deltaforce@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require"


app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# -----------------------------
# DB CONFIG
# -----------------------------
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
###app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(BASE_DIR, "database.db")
###app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "super_secret_key"

db = SQLAlchemy(app)

# ============================================================
# ⭐⭐⭐ RAZORPAY PAYMENT CONFIG ⭐⭐⭐
# ============================================================
RAZORPAY_KEY_ID = "rzp_test_Rlssl9MYDdeGpC"       # <-- put your Key ID
RAZORPAY_KEY_SECRET = "turKE03kkV1EAU6AQNG2UDEq"     # <-- put your Secret Key

razorpay_client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

"""
# ============================================================
# ⭐⭐⭐ CHATBOT ENGINE SETUP (GLOBAL) ⭐⭐⭐
# ============================================================

# 1) LLM
llm = Config.get_llm()

# 2) Load college documents
processor = DocumentProcessor(
    chunk_size=Config.CHUNK_SIZE,
    chunk_overlap=Config.CHUNK_OVERLAP
)

print("📄 Loading college documents for chatbot...")
docs = processor.process(Config.DOCUMENT_SOURCES)
print(f"✅ Loaded {len(docs)} chunks")

# 3) Create vectorstore + retriever
vs = VectorStore()
vs.create_vectorstore(docs)
retriever = vs.get_retriever()

# 4) Graph cache (agentic / normal)
graph_cache = {}


def get_graph(agentic: bool):
    if agentic in graph_cache:
        return graph_cache[agentic]

    graph = GraphBuilder(
        retriever=retriever,
        llm=llm,
        use_agentic=agentic
    ).build()

    graph_cache[agentic] = graph
    return graph

# ============================================================
# END CHATBOT ENGINE SETUP
# ============================================================"""


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

class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), nullable=False)  # success / failed
    payment_id = db.Column(db.String(100), nullable=True)

class CapstoneHistory(db.Model):
    __tablename__ = "capstone_history"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.String(50), nullable=False)

  # store date-time
    


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

        # Check admin by EMAIL (unique always)
        admin = User.query.filter_by(email="admin@system.com").first()

        if not admin:
            admin = User(
                username="admin",   # <-- NEW USERNAME HERE
                email="admin@system.com",
                reg_number="ADMIN",
                password=generate_password_hash("admin123"),
                is_admin=True,
                security_bike="adminbike"
            )
            db.session.add(admin)
            db.session.commit()
            print("🔥 Admin Created!")

        admin_created = True



# -----------------------------
# AUTH HELPERS (DECORATORS)
# -----------------------------
def login_required(admin_only=False):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):

            # If not logged in
            if "user_id" not in session:
                return redirect(url_for("login"))

            # If admin-only route
            if admin_only and not session.get("is_admin"):
                return "❌ Access Denied – Admin Only"

            return f(*args, **kwargs)

        return wrapper
    return decorator



def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        if not session.get("is_admin"):
            return "❌ Access Denied – Admin Only"
        return f(*args, **kwargs)
    return wrapper


# -----------------------------
# GLOBAL FIREWALL – BLOCK ALL WITHOUT LOGIN
# -----------------------------
@app.before_request
def block_unauthenticated_access():
    """
    This runs BEFORE every request.
    If user is not logged in, only allow:
      - login
      - register
      - forgot_password
      - static files
    Everything else → redirect to /login
    """
    # allow static files & OPTIONS preflight
    if request.endpoint == "static" or request.method == "OPTIONS":
        return

    open_endpoints = {"login", "register", "forgot_password"}

    # If route is open, allow
    if request.endpoint in open_endpoints:
        return

    # For all other endpoints, require login
    if "user_id" not in session:
        return redirect(url_for("login"))


# -----------------------------
# ROUTES
# -----------------------------
@app.route("/")
def default_route():
    session.clear()
    # Even if someone hits "/", firewall will redirect if not logged in
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
    session.clear()   # Ensure no old session stays
    message = ""
    shake = False

    if request.method == "POST":
        reg_no = request.form["reg_no"].strip()
        password = request.form["l_pass"].strip()

        # Find user by register number
        user = User.query.filter_by(reg_number=reg_no).first()

        if not user:
            return render_template(
                "login.html",
                shake=True,
                message="❌ Register Number not found"
            )

        if not check_password_hash(user.password, password):
            return render_template(
                "login.html",
                shake=True,
                message="❌ Wrong password"
            )

        # Set session values
        session["user_id"] = user.id
        session["username"] = user.username
        session["reg_no"] = user.reg_number
        session["is_admin"] = user.is_admin

        # Admin redirect
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

    user_count = len(users)

    # ⭐ TOTAL SUCCESSFUL CAPSTONE PAYMENTS ⭐
    total_capstone_payments = Payment.query.filter_by(status="success").count()

    return render_template(
        "admin.html",
        users=users,
        search=search,
        user_count=user_count,
        total_capstone_payments=total_capstone_payments
    )


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
# CAPSTONE FORM
# -----------------------------
@app.route("/capstone")
@login_required()
def capstone_form():
    return render_template("capstone_form.html")


@app.route("/generate_capstone", methods=["POST"])
@login_required()
def generate_capstone():

    data = request.get_json()
    if not data or "title" not in data:
        return {"error": "Title missing"}, 400

    title = data["title"].strip()

    print("STEP 1: Starting capstone...")

    # 1. AI content
    from ai_capstone.ai_engine import generate_ai_content
    sections = generate_ai_content(title)
    print("STEP 2: AI done")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(base_dir, "ai_capstone", "output")
    os.makedirs(output_dir, exist_ok=True)

    # 2. Create DOCX
    from ai_capstone.create_ai_docx import create_ai_docx
    from ai_capstone.utils.docx_filler import merge_docx

    ai_docx_path = os.path.join(output_dir, "ai_chapters.docx")
    create_ai_docx(sections, ai_docx_path)

    # 3. Merge with front pages
    docx_dir = os.path.join(base_dir, "ai_capstone", "templates_docx")
    fixed_pages = [
        os.path.join(docx_dir, "fixed_front_pages.docx")
    ]
    final_docx = os.path.join(output_dir, "final_capstone.docx")
    merge_docx(fixed_pages + [ai_docx_path], final_docx)

    # ⭐ SAVE HISTORY
    from datetime import datetime
    history = CapstoneHistory(
        user_id=session["user_id"],
        title=title,
        file_path=final_docx,
        created_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )

    try:
        db.session.add(history)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print("🔥 DB ERROR:", e)
        return jsonify({"error": "Database save failed"}), 500

    # ⭐ ONLY RETURN AFTER SUCCESSFUL DB SAVE
    session["capstone_file_path"] = final_docx
    session["project_title"] = title

    return jsonify({"redirect": "/payment"})


@app.route("/history")
@login_required()
def history_page():
    records = CapstoneHistory.query.filter_by(user_id=session["user_id"]).all()
    return render_template("history.html", records=records)





# ============================================================
# ⚡ PDF DOWNLOAD SYSTEM (FINAL BOSS ADDED)
# ============================================================
PDF_FOLDER = os.path.join(BASE_DIR, "static", "pdfs")

CAPSTONE_FOLDER = os.path.join(BASE_DIR, "ai_capstone", "output")

@app.route("/pdfs")
@login_required()
def list_pdfs():
    if not os.path.exists(PDF_FOLDER):
        os.makedirs(PDF_FOLDER)

    pdf_files = [f for f in os.listdir(PDF_FOLDER) if f.lower().endswith(".pdf")]
    return render_template("pdf_list.html", pdfs=pdf_files)

@app.route("/download_history/<int:id>")
@login_required()
def download_history(id):
    record = CapstoneHistory.query.get(id)
    if not record:
        return "Record not found", 404

    filename = os.path.basename(record.file_path)

    return send_from_directory(CAPSTONE_FOLDER, filename, as_attachment=True)



"""
# ============================================================
# ⭐⭐⭐ FLOATING CHATBOT WIDGET API ⭐⭐⭐
# ============================================================
@app.route("/chatbot-ask", methods=["POST"])
@login_required
def chatbot_ask():
    data = request.get_json() or {}
    user_message = data.get("message", "")
    agentic_mode = data.get("agentic", True)
    user_id = str(session.get("user_id") or "anonymous")   # 🔥 FIXED

    graph = get_graph(agentic_mode)

    user_context = UserMemoryManager.fetch_context(user_id)
    state_payload = {
        "question": user_message,
        "user_id": user_id,
        "memory": user_context.get("profile", {}),
        "chat_history": user_context.get("chat_history", [])
    }

    try:
        result = graph.invoke(state_payload)

        if isinstance(result, dict):
            answer = result.get("answer", "Sorry, I couldn't generate an answer.")
        else:
            answer = getattr(result, "answer", "Sorry, I couldn't generate an answer.")

        time.sleep(0.6)

    except Exception as e:
        answer = f"⚠️ Backend error: {str(e)}"
        print("❌ Error:", e)

    return jsonify({"answer": answer})"""

### For Staff Numbers
FACULTY_FILE = os.path.join(BASE_DIR, "static", "data", "full_info_faculty_numbers.json")

@app.route("/faculty")
@login_required()
def faculty_page():
    try:
        with open(FACULTY_FILE, "r", encoding="utf-8") as f:
            faculty_list = json.load(f)
    except Exception as e:
        faculty_list = []
        print("Error loading faculty JSON:", e)

    return render_template("faculty.html", faculty=faculty_list)

### ai tools for students
@app.route("/ai-tools")
@login_required()
def ai_tools():
    import json, os
    tools_file = os.path.join(BASE_DIR, "static", "data", "ai_tools.json")

    with open(tools_file, "r", encoding="utf-8") as f:
        tools = json.load(f)

    return render_template("ai_tools.html", tools=tools)


### Policys
@app.route("/privacy-policy")
@login_required()
def privacy_policy():
    return render_template("policies/privacy_policy.html")

@app.route("/refund-policy")
@login_required()
def refund_policy():
    return render_template("policies/refund_policy.html")

@app.route("/terms")
@login_required()
def terms_conditions():
    return render_template("policies/terms_conditions.html")

@app.route("/shipping-policy")
@login_required()
def shipping_policy():
    return render_template("policies/shipping_policy.html")

@app.route("/contact")
@login_required()
def contact_page():
    return render_template("policies/contact.html")

### payment
# ============================================================
# ⭐⭐⭐ PAYMENT PAGE ⭐⭐⭐
# ============================================================
@app.route("/payment")
@login_required()
def payment_page():
    amount_rupees = 19

    return render_template(
        "payment.html",
        razorpay_key_id=RAZORPAY_KEY_ID,
        amount_rupees=amount_rupees,
        username=session.get("username", "Student"),
        project_title=session.get("project_title", "Capstone Project")
    )


# ============================================================
# ⭐⭐⭐ CREATE RAZORPAY ORDER ⭐⭐⭐
# ============================================================
@app.route("/create_order", methods=["POST"])
@login_required()
def create_order():
    amount_rupees = 19
    amount_paise = amount_rupees * 100

    try:
        order = razorpay_client.order.create(dict(
            amount=amount_paise,
            currency="INR",
            payment_capture="1"
        ))
    except Exception as e:
        print("❌ Razorpay Error:", e)
        return jsonify({"error": "Failed to create order"}), 500

    return jsonify(order)


# ============================================================
# ⭐⭐⭐ PAYMENT SUCCESS HANDLER ⭐⭐⭐
# ============================================================
@app.route("/payment_success", methods=["POST"])
@login_required()
def payment_success():
    data = request.form

    razorpay_payment_id = data.get("razorpay_payment_id")
    razorpay_order_id = data.get("razorpay_order_id")
    razorpay_signature = data.get("razorpay_signature")

    # Verify signature
    try:
        razorpay_client.utility.verify_payment_signature({
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature
        })
    except:
        return "❌ Payment verification failed", 400

    # ⭐ SAVE SUCCESS PAYMENT IN DATABASE ⭐
    payment = Payment(
        user_id=session["user_id"],
        amount=19,
        status="success",
        payment_id=razorpay_payment_id
    )
    db.session.add(payment)
    db.session.commit()

    # Allow download of last generated file
    file_path = session.get("capstone_file_path")
    if not file_path or not os.path.exists(file_path):
        return "❌ File missing. Generate again."

    return send_file(
        file_path,
        as_attachment=True,
        download_name="Capstone_Report.docx"
    )

### admin update the strict/loose in json
@app.route("/update-faculty-behavior", methods=["POST"])
@login_required()
def update_faculty_behavior():
    # Only admins allowed
    if not session.get("is_admin"):
        return jsonify({"error": "Unauthorized"}), 403

    try:
        data = request.get_json()
        name = data.get("name")
        behavior = data.get("behavior")

        with open(FACULTY_FILE, "r", encoding="utf-8") as f:
            faculty = json.load(f)

        updated = False
        for person in faculty:
            if person.get("Name", "").strip().lower() == name.strip().lower():
                person["Strict/Loose"] = behavior
                updated = True
                break

        if not updated:
            return jsonify({"error": "Faculty not found"}), 404

        with open(FACULTY_FILE, "w", encoding="utf-8") as f:
            json.dump(faculty, f, indent=4)

        return jsonify({"message": "Updated successfully!"})

    except Exception as e:
        return jsonify({"error": str(e)}), 500


### faculty suggestions by users
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "static", "data")

SUGGESTION_FILE = os.path.join(DATA_DIR, "faculty_suggestions.json")
MASTER_FILE = os.path.join(DATA_DIR, "full_info_faculty_numbers.json")

def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return default

def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)



@app.route("/faculty-suggestion", methods=["POST"])
@login_required()
def faculty_suggestion():
    data = request.get_json() or {}
    
    suggestion_type = data.get("type", "").strip()
    phone = data.get("phone_number", "").strip()
    behavior = data.get("behavior", "").strip()
    
    # For existing faculty - only need phone and behavior
    if suggestion_type == "existing":
        if not phone or not behavior:
            return jsonify({"message": "Missing fields"}), 400
        
        suggestions = load_json(SUGGESTION_FILE, [])
        new_id = suggestions[-1]["id"] + 1 if suggestions else 1
        
        suggestions.append({
            "id": new_id,
            "type": "existing",
            "phone_number": phone,
            "behavior": behavior,
            "added_by": session.get("username")
        })
        
        save_json(SUGGESTION_FILE, suggestions)
        return jsonify({"message": "Behaviour suggestion submitted!"})
    
    # For new faculty - need name, phone and behavior
    else:
        faculty_name = data.get("name", "").strip()
        dept = data.get("dept", "").strip()
        
        if not faculty_name or not phone or not dept:
            return jsonify({"message": "Missing fields"}), 400
        
        suggestions = load_json(SUGGESTION_FILE, [])
        new_id = suggestions[-1]["id"] + 1 if suggestions else 1
        
        suggestions.append({
            "id": new_id,
            "type": "new",
            "name": faculty_name,
            "phone_number": phone,
            "dept": dept,
            "added_by": session.get("username")
        })
        
        save_json(SUGGESTION_FILE, suggestions)
        return jsonify({"message": "New faculty suggestion submitted!"})


@app.route("/faculty-suggestions")
@login_required(admin_only=True)
def faculty_suggestions_page():
    try:
        with open(SUGGESTION_FILE, "r", encoding="utf-8") as f:
            suggestions = json.load(f)
    except:
        suggestions = []

    return render_template("faculty_suggestions.html", suggestions=suggestions)
    


@app.route("/approve-new/<int:sid>", methods=["POST"])
@login_required(admin_only=True)
def approve_new(sid):

    suggestions = load_json(SUGGESTION_FILE, [])
    suggestion = next((s for s in suggestions if s["id"] == sid), None)

    if not suggestion:
        return jsonify({"message": "Invalid suggestion"}), 400

    name = suggestion["name"]
    phone = int(suggestion["phone_number"])
    behavior = suggestion["dept"]

    master = load_json(MASTER_FILE, [])

    # Prevent duplicates
    if any(str(f["Phone Number"]) == str(phone) for f in master):
        return jsonify({"message": "Faculty already exists!"}), 400

    master.append({
        "Name": name,
        "Phone Number": phone,
        "Strict/Loose": behavior
    })

    save_json(MASTER_FILE, master)

    # Remove from suggestion list
    suggestions = [s for s in suggestions if s["id"] != sid]
    save_json(SUGGESTION_FILE, suggestions)

    return jsonify({"message": "New faculty added successfully!"})


@app.route("/approve-existing/<int:sid>", methods=["POST"])
@login_required(admin_only=True)
def approve_existing(sid):

    suggestions = load_json(SUGGESTION_FILE, [])
    suggestion = next((s for s in suggestions if s["id"] == sid), None)

    if not suggestion:
        return jsonify({"message": "Invalid suggestion"}), 400

    phone = suggestion["phone_number"]
    behavior = suggestion["behavior"]

    master = load_json(MASTER_FILE, [])

    for f in master:
        if str(f["Phone Number"]) == str(phone):
            f["Strict/Loose"] = behavior

    save_json(MASTER_FILE, master)

    # Remove suggestion from list
    suggestions = [s for s in suggestions if s["id"] != sid]
    save_json(SUGGESTION_FILE, suggestions)

    return jsonify({"message": "Behavior updated successfully!"})




@app.route("/reject-suggestion/<int:sid>", methods=["POST"])
@login_required(admin_only=True)
def reject_suggestion(sid):

    suggestions = load_json(SUGGESTION_FILE, [])

    suggestions = [s for s in suggestions if s["id"] != sid]

    save_json(SUGGESTION_FILE, suggestions)

    return jsonify({"message": "Suggestion rejected!"})




@app.route("/suggest-existing-behavior", methods=["POST"])
@login_required()
def suggest_existing_behavior():
    data = request.get_json() or {}
    phone = data.get("phone_number")
    behavior = data.get("behavior")

    if not phone or not behavior:
        return jsonify({"message": "Missing data"}), 400

    master = load_json(MASTER_FILE, [])

    faculty = next((f for f in master if str(f["Phone Number"]) == str(phone)), None)

    if not faculty:
        return jsonify({"message": "Faculty with this phone not found"}), 400

    if faculty.get("Strict/Loose"):
        return jsonify({"message": "This faculty already has a behaviour"}), 400

    suggestions = load_json(SUGGESTION_FILE, [])
    new_id = suggestions[-1]["id"] + 1 if suggestions else 1

    suggestions.append({
        "id": new_id,
        "type": "existing",
        "faculty_name": faculty["Name"],
        "phone_number": phone,
        "behavior": behavior,
        "submitted_by": session.get("username")
    })

    save_json(SUGGESTION_FILE, suggestions)

    return jsonify({"message": "Behaviour update suggestion submitted!"})

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/services")
def services():
    return render_template("services.html")
# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5050)