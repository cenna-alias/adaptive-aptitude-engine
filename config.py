import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "adaptive-aptitude-engine-dev-key-change-me")
    SQLALCHEMY_DATABASE_URI = "sqlite:///" + os.path.join(BASE_DIR, "instance", "aptitude.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    QUESTIONS_CSV = os.path.join(BASE_DIR, "data", "questions.csv")
    MODEL_PATH = os.path.join(BASE_DIR, "ml", "rf_level_model.pkl")
    METRICS_PATH = os.path.join(BASE_DIR, "ml", "metrics.json")

    TEST_LENGTH = 20              # questions in a full adaptive test
    RETAKE_LENGTH = 10            # questions in a weak-area retake
    WEAK_TOPIC_THRESHOLD = 60.0   # topic accuracy (%) below this is "weak"

    # Default superuser created by seed_db.py (change after first login)
    SUPERUSER_USERNAME = os.environ.get("SUPERUSER_USERNAME", "admin")
    SUPERUSER_EMAIL = os.environ.get("SUPERUSER_EMAIL", "admin@aptitude.local")
    SUPERUSER_PASSWORD = os.environ.get("SUPERUSER_PASSWORD", "Admin@123")
