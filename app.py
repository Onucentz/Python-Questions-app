from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import database
import questions
import os



app = Flask(__name__)
app.secret_key = "supersecretkey123"

# =========================

# INITIALIZE DATABASE

# =========================

database.init_db()

# =========================

# FLASK LOGIN SETUP

# =========================

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "admin_login"

# =========================

# ADMIN USER CLASS

# =========================

class Admin(UserMixin):
    def __init__(self, id):
        self.id = id

# =========================

# DEFAULT ADMIN DETAILS

# =========================

ADMIN_USERNAME = "admin"
DEFAULT_PASSWORD = "admin123"
NEW_PASSWORD = "securequiz2026"

@login_manager.user_loader
def load_user(user_id):
    return Admin(user_id)

# =========================

# HOME / LOGIN PAGE

# =========================

@app.route("/", methods=["GET", "POST"])
def home():

    if request.method == "POST":

        fname = request.form.get("fname")
        sname = request.form.get("sname")
        sclass = request.form.get("sclass")

        if not fname or not sname or not sclass:
            flash("Please fill all fields")
            return redirect(url_for("home"))

    # TWO ATTEMPT RESTRICTION
        attempts = database.get_attempts(fname, sname)

        if attempts >= 2:
            return "You have exceeded the maximum number of attempts."

    # SAVE TO SESSION
        session["fname"] = fname
        session["sname"] = sname
        session["sclass"] = sclass
        session["score"] = 0
        session["current_q"] = 0

        return redirect(url_for("ready"))

    return render_template("index.html")

# =========================

# READY PAGE

# =========================
@app.route("/ready", methods=["POST"])
def ready():

    # CLEAR OLD SESSION
    session.clear()

    # SAVE STUDENT DETAILS
    session["fname"] = request.form["fname"]
    session["sname"] = request.form["sname"]
    session["sclass"] = request.form["sclass"]

    # RESET QUIZ VALUES
    session["current_q"] = 0
    session["score"] = 0

    # START TIMER
    session["start_time"] = datetime.now().timestamp()

    return render_template(
        "ready.html",
        fname=session["fname"]
    )
# =========================

# QUIZ PAGE

# =========================

@app.route("/quiz", methods=["GET", "POST"])
def quiz():

    QUIZ_DURATION = 1500

    # ENSURE QUIZ STARTED
    if "start_time" not in session:
        return redirect("/")

    elapsed = datetime.now().timestamp() - session["start_time"]

    remaining = int(QUIZ_DURATION - elapsed)

    # TIME FINISHED
    if remaining <= 0:
        return redirect("/result")

    index = session.get("current_q", 0)

    total = len(questions.quiz_data)

    # PROCESS ANSWER
    if request.method == "POST":

        selected = request.form.get("answer")

        correct = questions.quiz_data[index]["answer"]

        if selected == correct:
            session["score"] += 1

        session["current_q"] += 1

        return redirect("/quiz")

    # QUIZ FINISHED
    if index >= total:
        return redirect("/result")

    q = questions.quiz_data[index]

    return render_template(
        "quiz.html",
        q=q,
        index=index,
        total=total,
        remaining=remaining
    )
# END QUIZ
    if index >= len(questions.quiz_data):
        return redirect(url_for("result"))

    q = questions.quiz_data[index]

    return render_template(
        "quiz.html",
        question=q,
        q_number=index + 1,
        total=len(questions.quiz_data)
        )

# =========================

# RESULT PAGE

# =========================

@app.route("/result")
def result():

    score = session.get("score", 0)

    total = len(questions.quiz_data)

    percentage = (score / total) * 100
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    database.save_result(
        session.get("fname"),
        session.get("sname"),
        session.get("sclass"),
        score,
        percentage,
        timestamp
    )

    return render_template(
        "result.html",
        score=score,
        total=total,
        percentage=percentage
    )

# UPDATE ATTEMPTS
    database.update_attempt(fname, sname)

# CLEAR QUIZ SESSION
    session.pop("current_q", None)

    return render_template(
        "result.html",
        fname=fname,
        score=score,
        total=total,
        percent=percent
    )

# =========================

# ADMIN LOGIN

# =========================

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == ADMIN_USERNAME and (
            password == DEFAULT_PASSWORD or
            password == NEW_PASSWORD
        ):

            admin = Admin(1)

            login_user(admin)

            return redirect(url_for("admin_dashboard"))

        else:
            flash("Invalid login details")

    return render_template("admin_login.html")

# =========================

# ADMIN DASHBOARD

# =========================

@app.route("/admin")
@login_required
def admin_dashboard():
    results = database.get_results()

    return render_template(
    "admin.html",
    results=results
    )

# =========================

# ADMIN LOGOUT

# =========================

@app.route("/logout")
@login_required
def logout():
    logout_user()

    return redirect(url_for("admin_login"))

# =========================

# EXPORT PDF

# =========================

@app.route("/export/pdf")
@login_required
def export_pdf():
    data = database.get_results()

    pdf_file = "results.pdf"

    doc = SimpleDocTemplate(pdf_file)

    styles = getSampleStyleSheet()

    elements = []

    title = Paragraph(
        "Student Quiz Results",
        styles['Title']
    )

    elements.append(title)

    elements.append(Spacer(1, 20))

    for row in data:

        text = (
            f"Name: {row[0]} {row[1]} | "
            f"Class: {row[2]} | "
            f"Score: {row[3]} | "
            f"Percentage: {row[4]:.1f}% | "
            f"Date: {row[5]}"
        )

        p = Paragraph(text, styles['BodyText'])

        elements.append(p)

        elements.append(Spacer(1, 12))

    doc.build(elements)

    return send_file(
        pdf_file,
        as_attachment=True
    )

# =========================

# PREVENT BACK BUTTON CACHE

# =========================

@app.after_request
def add_header(response):
    response.headers[
        "Cache-Control"
    ] = "no-store, no-cache, must-revalidate, max-age=0"

    response.headers["Pragma"] = "no-cache"

    response.headers["Expires"] = "0"

    return response
# =========================

# MAIN APP

# =========================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
