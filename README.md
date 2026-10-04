# Adaptive Aptitude Test Engine (Flask + Random Forest)

## Run (Python 3.10+)
```
pip install -r requirements.txt
python seed_db.py        # creates instance/aptitude.db, loads 400 questions, creates superuser
python app.py            # open http://127.0.0.1:5000
```
Superuser: **admin / Admin@123** (change in config.py).

## Regenerate everything (optional)
```
python scripts/generate_questions.py            # data/questions.csv (400, validated)
python scripts/generate_student_performance.py  # data/student_performance.csv (9,600 rows)
python ml/train_model.py                        # ml/rf_level_model.pkl (~83.5% accuracy)
python seed_db.py --reset
```
Notebook: `notebooks/model_training.ipynb` (run `jupyter notebook` from the notebooks folder).

## Flow
Home -> Register -> Login -> Dashboard -> 20-question adaptive test (all 4 topics, no repeats)
-> Score card (topic-wise accuracy, difficulty, ML level + confidence, solutions) -> Retake weak areas.
Admin: all students, scores, predictions, CSV export, add/edit/disable/delete questions.

Database: SQLite at `instance/aptitude.db` (open with DB Browser for SQLite).
