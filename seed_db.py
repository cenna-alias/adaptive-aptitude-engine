import csv
import sys

from app import app
from config import Config
from models import Answer, Question, User, db


def load_questions(reset=False):
    if reset:
        Answer.query.delete()
        Question.query.delete()
        db.session.commit()

    if Question.query.count() > 0:
        print(f"Questions already present: {Question.query.count()} (use --reset to reload)")
        return

    with open(Config.QUESTIONS_CSV, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        db.session.add(Question(
            topic=r["topic"], subtopic=r["subtopic"], difficulty=r["difficulty"],
            question=r["question"], option_a=r["option_a"], option_b=r["option_b"],
            option_c=r["option_c"], option_d=r["option_d"],
            correct_option=r["correct_option"], explanation=r["explanation"], active=True))
    db.session.commit()
    print(f"Loaded {len(rows)} questions into SQLite.")


def create_superuser():
    admin = User.query.filter_by(username=Config.SUPERUSER_USERNAME).first()
    if admin:
        admin.is_admin = True
        db.session.commit()
        print(f"Superuser already exists: {admin.username}")
        return
    admin = User(username=Config.SUPERUSER_USERNAME, email=Config.SUPERUSER_EMAIL,
                 full_name="Super User", is_admin=True)
    admin.set_password(Config.SUPERUSER_PASSWORD)
    db.session.add(admin)
    db.session.commit()
    print(f"Superuser created -> username: {Config.SUPERUSER_USERNAME} / "
          f"password: {Config.SUPERUSER_PASSWORD}")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        load_questions(reset="--reset" in sys.argv)
        create_superuser()
        print("Database ready:", app.config["SQLALCHEMY_DATABASE_URI"])
