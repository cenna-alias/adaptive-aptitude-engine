import csv
import io
import os
from datetime import datetime
from functools import wraps

from flask import (Flask, Response, abort, flash, redirect, render_template,
                   request, session, url_for)

from config import Config
from engine import adaptive, predictor
from models import Answer, Question, TestAttempt, User, db

app = Flask(__name__)
app.config.from_object(Config)
os.makedirs(os.path.join(os.path.dirname(os.path.abspath(__file__)), "instance"), exist_ok=True)
db.init_app(app)


# ---------------------------------------------------------------- helpers
def current_user():
    uid = session.get("user_id")
    return db.session.get(User, uid) if uid else None


def login_required(view):
    @wraps(view)
    def wrapper(*a, **kw):
        if not current_user():
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return view(*a, **kw)
    return wrapper


def admin_required(view):
    @wraps(view)
    def wrapper(*a, **kw):
        u = current_user()
        if not u or not u.is_admin:
            flash("Superuser access required.", "danger")
            return redirect(url_for("admin_login"))
        return view(*a, **kw)
    return wrapper


def aggregate_topics(attempts):
    totals = {}
    for a in attempts:
        for t, s in a.topic_breakdown().items():
            d = totals.setdefault(t, {"total": 0, "correct": 0})
            d["total"] += s["total"]
            d["correct"] += s["correct"]
    for d in totals.values():
        d["accuracy"] = round(d["correct"] * 100 / d["total"], 2) if d["total"] else 0.0
    return totals


@app.context_processor
def inject_globals():
    return {"user": current_user(), "year": datetime.utcnow().year}


# ---------------------------------------------------------------- public
@app.route("/")
def home():
    stats = {
        "questions": Question.query.filter_by(active=True).count(),
        "students": User.query.filter_by(is_admin=False).count(),
        "attempts": TestAttempt.query.filter_by(completed=True).count(),
    }
    return render_template("home.html", stats=stats)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        f = request.form
        username = f.get("username", "").strip()
        email = f.get("email", "").strip().lower()
        password = f.get("password", "")

        if not username or not email or len(password) < 6:
            flash("Username, email and a password of at least 6 characters are required.", "danger")
        elif User.query.filter_by(username=username).first():
            flash("That username is already taken.", "danger")
        elif User.query.filter_by(email=email).first():
            flash("That email is already registered.", "danger")
        else:
            u = User(username=username, email=email,
                     full_name=f.get("full_name", "").strip(),
                     college=f.get("college", "").strip())
            u.set_password(password)
            db.session.add(u)
            db.session.commit()
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        ident = request.form.get("identifier", "").strip()
        pwd = request.form.get("password", "")
        u = (User.query.filter_by(username=ident).first()
             or User.query.filter_by(email=ident.lower()).first())
        if u and u.check_password(pwd):
            session.clear()
            session["user_id"] = u.id
            flash(f"Welcome back, {u.full_name or u.username}.", "success")
            return redirect(url_for("admin_dashboard" if u.is_admin else "dashboard"))
        flash("Invalid credentials.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for("home"))


# ---------------------------------------------------------------- dashboard
@app.route("/dashboard")
@login_required
def dashboard():
    u = current_user()
    if u.is_admin:
        return redirect(url_for("admin_dashboard"))

    attempts = sorted(u.completed_attempts, key=lambda a: a.finished_at or a.started_at, reverse=True)
    topic_totals = aggregate_topics(attempts)
    weak = sorted([t for t, d in topic_totals.items()
                   if d["accuracy"] < app.config["WEAK_TOPIC_THRESHOLD"]],
                  key=lambda t: topic_totals[t]["accuracy"])
    trend = [{"label": f"#{i + 1}", "value": a.percentage}
             for i, a in enumerate(reversed(attempts))][-10:]

    return render_template("dashboard.html", attempts=attempts, topic_totals=topic_totals,
                           weak=weak, trend=trend, latest=attempts[0] if attempts else None)


# ---------------------------------------------------------------- test flow
def _start_attempt(mode, focus_topics=None):
    u = current_user()
    length = app.config["RETAKE_LENGTH"] if mode == "retake" else app.config["TEST_LENGTH"]
    plan = adaptive.build_topic_plan(length, focus_topics)

    attempt = TestAttempt(user_id=u.id, mode=mode, total_questions=length,
                          focus_topics=",".join(focus_topics) if focus_topics else None)
    db.session.add(attempt)
    db.session.commit()

    session["test"] = {
        "attempt_id": attempt.id, "plan": plan, "index": 0, "difficulty": "medium",
        "results": [], "served": [], "current_qid": None, "elapsed": 0,
    }
    return redirect(url_for("test_question"))


@app.route("/test/start", methods=["GET", "POST"])
@login_required
def test_start():
    return _start_attempt("full")


@app.route("/test/retake/<int:attempt_id>", methods=["GET", "POST"])
@login_required
def test_retake(attempt_id):
    attempt = db.session.get(TestAttempt, attempt_id)
    if not attempt or attempt.user_id != current_user().id:
        abort(404)
    weak = attempt.weak_topics(app.config["WEAK_TOPIC_THRESHOLD"])
    if not weak:
        flash("No weak topic in that attempt - starting a full adaptive test instead.", "warning")
        return _start_attempt("full")
    return _start_attempt("retake", weak)


@app.route("/test/question")
@login_required
def test_question():
    st = session.get("test")
    if not st:
        flash("No test in progress.", "warning")
        return redirect(url_for("dashboard"))
    if st["index"] >= len(st["plan"]):
        return redirect(url_for("test_finish"))

    # reuse the same question on refresh so a user can't reroll
    q = db.session.get(Question, st["current_qid"]) if st.get("current_qid") else None
    if q is None:
        topic = st["plan"][st["index"]]
        q = adaptive.pick_question(topic, st["difficulty"], st["served"], current_user().id)
        if q is None:
            flash("Question bank is empty - ask the administrator to load questions.", "danger")
            return redirect(url_for("dashboard"))
        st["current_qid"] = q.id
        session["test"] = st

    mode = db.session.get(TestAttempt, st["attempt_id"]).mode
    return render_template("test.html", q=q, number=st["index"] + 1,
                           total=len(st["plan"]), difficulty=st["difficulty"], mode=mode)


@app.route("/test/answer", methods=["POST"])
@login_required
def test_answer():
    st = session.get("test")
    if not st:
        return redirect(url_for("dashboard"))

    qid = int(request.form.get("question_id", 0))
    if qid != st.get("current_qid"):
        return redirect(url_for("test_question"))

    q = db.session.get(Question, qid)
    selected = (request.form.get("option") or "").upper()[:1]
    try:
        seconds = max(0, min(600, int(float(request.form.get("seconds", 0)))))
    except ValueError:
        seconds = 0
    is_correct = selected == q.correct_option

    db.session.add(Answer(attempt_id=st["attempt_id"], question_id=q.id,
                          sequence=st["index"] + 1, topic=q.topic, difficulty=q.difficulty,
                          selected_option=selected or None, is_correct=is_correct,
                          seconds=seconds))
    db.session.commit()

    st["served"].append(q.id)
    st["results"].append(bool(is_correct))
    st["elapsed"] += seconds
    st["difficulty"] = adaptive.next_difficulty(st["difficulty"], st["results"])
    st["index"] += 1
    st["current_qid"] = None
    session["test"] = st

    if st["index"] >= len(st["plan"]):
        return redirect(url_for("test_finish"))
    return redirect(url_for("test_question"))


@app.route("/test/finish")
@login_required
def test_finish():
    st = session.pop("test", None)
    if not st:
        return redirect(url_for("dashboard"))

    attempt = db.session.get(TestAttempt, st["attempt_id"])
    u = current_user()
    total = len(attempt.answers) or 1
    correct = sum(1 for a in attempt.answers if a.is_correct)

    attempt.total_questions = len(attempt.answers)
    attempt.correct_answers = correct
    attempt.percentage = round(correct * 100 / total, 2)
    attempt.time_taken = st.get("elapsed", 0)
    attempt.completed = True
    attempt.finished_at = datetime.utcnow()
    db.session.commit()

    level, conf, *_ = predictor.predict_level(attempt, u, app.config["MODEL_PATH"])
    attempt.predicted_level = level
    attempt.level_confidence = conf
    db.session.commit()
    return redirect(url_for("report", attempt_id=attempt.id))


@app.route("/report/<int:attempt_id>")
@login_required
def report(attempt_id):
    attempt = db.session.get(TestAttempt, attempt_id)
    u = current_user()
    if not attempt or not attempt.completed or (attempt.user_id != u.id and not u.is_admin):
        abort(404)

    owner = db.session.get(User, attempt.user_id)
    level, conf, feats, probs, src = predictor.predict_level(attempt, owner, app.config["MODEL_PATH"])
    weak = attempt.weak_topics(app.config["WEAK_TOPIC_THRESHOLD"])
    return render_template("report.html", attempt=attempt, topics=attempt.topic_breakdown(),
                           diffs=attempt.difficulty_breakdown(), weak=weak, level=level,
                           confidence=conf, probs=probs, features=feats, source=src,
                           advice=predictor.recommendation(level, weak),
                           metrics=predictor.load_metrics(app.config["METRICS_PATH"]))


# ---------------------------------------------------------------- admin
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        ident = request.form.get("identifier", "").strip()
        pwd = request.form.get("password", "")
        u = (User.query.filter_by(username=ident).first()
             or User.query.filter_by(email=ident.lower()).first())
        if u and u.is_admin and u.check_password(pwd):
            session.clear()
            session["user_id"] = u.id
            flash("Superuser signed in.", "success")
            return redirect(url_for("admin_dashboard"))
        flash("Invalid superuser credentials.", "danger")
    return render_template("admin_login.html")


@app.route("/admin")
@admin_required
def admin_dashboard():
    users = User.query.filter_by(is_admin=False).order_by(User.created_at.desc()).all()
    attempts = (TestAttempt.query.filter_by(completed=True)
                .order_by(TestAttempt.finished_at.desc()).limit(25).all())
    done = TestAttempt.query.filter_by(completed=True).all()

    level_counts = {}
    for a in done:
        if a.predicted_level:
            level_counts[a.predicted_level] = level_counts.get(a.predicted_level, 0) + 1

    stats = {
        "users": len(users),
        "attempts": len(done),
        "questions": Question.query.count(),
        "active_questions": Question.query.filter_by(active=True).count(),
    }
    return render_template("admin_dashboard.html", users=users, attempts=attempts, stats=stats,
                           level_counts=level_counts, topic_totals=aggregate_topics(done))


@app.route("/admin/user/<int:user_id>")
@admin_required
def admin_user(user_id):
    u = db.session.get(User, user_id)
    if not u:
        abort(404)
    attempts = sorted(u.completed_attempts, key=lambda a: a.finished_at or a.started_at, reverse=True)
    return render_template("admin_user.html", student=u, attempts=attempts,
                           topic_totals=aggregate_topics(attempts))


@app.route("/admin/user/<int:user_id>/delete", methods=["POST"])
@admin_required
def admin_user_delete(user_id):
    u = db.session.get(User, user_id)
    if not u or u.is_admin:
        abort(404)
    db.session.delete(u)
    db.session.commit()
    flash("Student and all related scores deleted.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/questions")
@admin_required
def admin_questions():
    try:
        page = max(1, int(request.args.get("page", 1)))
    except ValueError:
        page = 1
    per_page = 20
    topic = request.args.get("topic", "")
    search = request.args.get("q", "").strip()

    query = Question.query
    if topic:
        query = query.filter(Question.topic == topic)
    if search:
        query = query.filter(Question.question.ilike(f"%{search}%"))

    total = query.count()
    items = query.order_by(Question.id).offset((page - 1) * per_page).limit(per_page).all()
    topics = [r[0] for r in db.session.query(Question.topic).distinct().order_by(Question.topic)]
    return render_template("admin_questions.html", items=items, page=page,
                           pages=max(1, (total + per_page - 1) // per_page),
                           total=total, topics=topics, topic=topic, search=search)


@app.route("/admin/questions/new", methods=["GET", "POST"])
@app.route("/admin/questions/<int:qid>/edit", methods=["GET", "POST"])
@admin_required
def admin_question_form(qid=None):
    q = db.session.get(Question, qid) if qid else None
    if qid and not q:
        abort(404)

    if request.method == "POST":
        f = request.form
        fields = ["topic", "subtopic", "difficulty", "question", "option_a", "option_b",
                  "option_c", "option_d", "correct_option", "explanation"]
        data = {k: (f.get(k) or "").strip() for k in fields}
        opts = [data["option_a"], data["option_b"], data["option_c"], data["option_d"]]

        if not data["topic"] or not data["question"] or any(not o for o in opts):
            flash("Topic, question text and all four options are required.", "danger")
        elif len(set(opts)) != 4:
            flash("The four options must be different from each other.", "danger")
        elif data["correct_option"].upper() not in {"A", "B", "C", "D"}:
            flash("Correct option must be A, B, C or D.", "danger")
        else:
            data["correct_option"] = data["correct_option"].upper()
            data["difficulty"] = (data["difficulty"] or "medium").lower()
            dup = Question.query.filter(Question.question == data["question"])
            if q:
                dup = dup.filter(Question.id != q.id)
            if dup.first():
                flash("An identical question already exists.", "danger")
                return render_template("admin_question_form.html", q=q)
            if q is None:
                q = Question(**data, active=True)
                db.session.add(q)
                msg = "Question added."
            else:
                for k, v in data.items():
                    setattr(q, k, v)
                q.active = bool(f.get("active"))
                msg = "Question updated."
            db.session.commit()
            flash(msg, "success")
            return redirect(url_for("admin_questions"))

    return render_template("admin_question_form.html", q=q)


@app.route("/admin/questions/<int:qid>/delete", methods=["POST"])
@admin_required
def admin_question_delete(qid):
    q = db.session.get(Question, qid)
    if not q:
        abort(404)
    Answer.query.filter_by(question_id=q.id).delete()
    db.session.delete(q)
    db.session.commit()
    flash(f"Question #{qid} deleted.", "success")
    return redirect(url_for("admin_questions", **request.args.to_dict()))


@app.route("/admin/questions/<int:qid>/toggle", methods=["POST"])
@admin_required
def admin_question_toggle(qid):
    q = db.session.get(Question, qid)
    if not q:
        abort(404)
    q.active = not q.active
    db.session.commit()
    flash(f"Question #{qid} is now {'active' if q.active else 'disabled'}.", "success")
    return redirect(url_for("admin_questions", **request.args.to_dict()))


@app.route("/admin/export/scores.csv")
@admin_required
def admin_export_scores():
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["attempt_id", "username", "email", "mode", "total", "correct", "percentage",
                "predicted_level", "confidence", "time_seconds", "finished_at"])
    for a in TestAttempt.query.filter_by(completed=True).order_by(TestAttempt.id):
        u = db.session.get(User, a.user_id)
        w.writerow([a.id, u.username, u.email, a.mode, a.total_questions, a.correct_answers,
                    a.percentage, a.predicted_level, a.level_confidence, a.time_taken,
                    a.finished_at])
    return Response(buf.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=scores.csv"})


@app.errorhandler(404)
def not_found(_e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)


    