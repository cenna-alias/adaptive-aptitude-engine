from datetime import datetime
from zoneinfo import ZoneInfo

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

def india_time():
    return datetime.now(ZoneInfo("Asia/Kolkata")).replace(tzinfo=None)

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(120))
    college = db.Column(db.String(160))
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    attempts = db.relationship("TestAttempt", backref="user", lazy=True,
                               cascade="all, delete-orphan")

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)

    @property
    def completed_attempts(self):
        return [a for a in self.attempts if a.completed]

    @property
    def best_score(self):
        return max((a.percentage for a in self.completed_attempts), default=0.0)

    @property
    def avg_score(self):
        done = self.completed_attempts
        return round(sum(a.percentage for a in done) / len(done), 2) if done else 0.0


class Question(db.Model):
    __tablename__ = "questions"

    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(60), nullable=False, index=True)
    subtopic = db.Column(db.String(80))
    difficulty = db.Column(db.String(10), nullable=False, index=True)  # easy|medium|hard
    question = db.Column(db.Text, nullable=False)
    option_a = db.Column(db.String(255), nullable=False)
    option_b = db.Column(db.String(255), nullable=False)
    option_c = db.Column(db.String(255), nullable=False)
    option_d = db.Column(db.String(255), nullable=False)
    correct_option = db.Column(db.String(1), nullable=False)  # A|B|C|D
    explanation = db.Column(db.Text)
    active = db.Column(db.Boolean, default=True, nullable=False)

    def options(self):
        return [("A", self.option_a), ("B", self.option_b),
                ("C", self.option_c), ("D", self.option_d)]

    def option_text(self, letter):
        return {"A": self.option_a, "B": self.option_b,
                "C": self.option_c, "D": self.option_d}.get(letter)


class TestAttempt(db.Model):
    __tablename__ = "test_attempts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    mode = db.Column(db.String(20), default="full")        # full | retake
    focus_topics = db.Column(db.String(255))               # comma separated, retake mode
    total_questions = db.Column(db.Integer, default=0)
    correct_answers = db.Column(db.Integer, default=0)
    percentage = db.Column(db.Float, default=0.0)
    predicted_level = db.Column(db.String(20))
    level_confidence = db.Column(db.Float)
    time_taken = db.Column(db.Integer, default=0)          # seconds
    completed = db.Column(db.Boolean, default=False)
    started_at = db.Column(db.DateTime, default=india_time)
    finished_at = db.Column(db.DateTime)

    answers = db.relationship("Answer", backref="attempt", lazy=True,
                              cascade="all, delete-orphan", order_by="Answer.sequence")

    def topic_breakdown(self):
        stats = {}
        for a in self.answers:
            s = stats.setdefault(a.topic, {"total": 0, "correct": 0})
            s["total"] += 1
            s["correct"] += 1 if a.is_correct else 0
        for s in stats.values():
            s["accuracy"] = round(s["correct"] * 100 / s["total"], 2) if s["total"] else 0.0
        return stats

    def difficulty_breakdown(self):
        stats = {}
        for a in self.answers:
            s = stats.setdefault(a.difficulty, {"total": 0, "correct": 0})
            s["total"] += 1
            s["correct"] += 1 if a.is_correct else 0
        for s in stats.values():
            s["accuracy"] = round(s["correct"] * 100 / s["total"], 2) if s["total"] else 0.0
        return stats

    def weak_topics(self, threshold=60.0):
        return [t for t, s in self.topic_breakdown().items() if s["accuracy"] < threshold]


class Answer(db.Model):
    __tablename__ = "answers"

    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey("test_attempts.id"), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False)
    sequence = db.Column(db.Integer, default=0)
    topic = db.Column(db.String(60))
    difficulty = db.Column(db.String(10))
    selected_option = db.Column(db.String(1))
    is_correct = db.Column(db.Boolean, default=False)
    seconds = db.Column(db.Integer, default=0)

    question = db.relationship("Question")
