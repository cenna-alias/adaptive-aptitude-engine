"""
Turns one attempt (plus the learner's history) into the 13 features the Random
Forest was trained on and predicts Beginner / Intermediate / Advanced.
Falls back to simple banding if the model file is missing.
"""

import json
import os

TOPIC_KEY = {
    "Quantitative Aptitude": "quant_accuracy",
    "Logical Reasoning": "logical_accuracy",
    "Verbal Ability": "verbal_accuracy",
    "Data Interpretation": "di_accuracy",
}

_bundle = None
_metrics = None


def load_model(path):
    global _bundle
    if _bundle is None and os.path.exists(path):
        import joblib
        _bundle = joblib.load(path)
    return _bundle


def load_metrics(path):
    global _metrics
    if _metrics is None and os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            _metrics = json.load(f)
    return _metrics or {}


def build_features(attempt, user):
    topics = attempt.topic_breakdown()
    diffs = attempt.difficulty_breakdown()
    total = len(attempt.answers) or 1
    answered = sum(1 for a in attempt.answers if a.selected_option)

    feats = {
        "tests_taken": max(1, len(user.completed_attempts)),
        "avg_time_per_question": round(attempt.time_taken / total, 2) if attempt.time_taken else 45.0,
        "attempted_ratio": round(answered * 100 / total, 2),
        "easy_accuracy": diffs.get("easy", {}).get("accuracy", 0.0),
        "medium_accuracy": diffs.get("medium", {}).get("accuracy", 0.0),
        "hard_accuracy": diffs.get("hard", {}).get("accuracy", 0.0),
        "retake_count": sum(1 for a in user.completed_attempts if a.mode == "retake"),
        "overall_accuracy": round(attempt.percentage, 2),
    }
    for topic, key in TOPIC_KEY.items():
        # topics not covered (e.g. in a retake) fall back to overall accuracy
        feats[key] = topics.get(topic, {}).get("accuracy", feats["overall_accuracy"])

    vals = [feats[k] for k in TOPIC_KEY.values()]
    feats["consistency_score"] = round(max(0.0, 100.0 - (max(vals) - min(vals))), 2)
    return feats


def predict_level(attempt, user, model_path):
    feats = build_features(attempt, user)
    bundle = load_model(model_path)

    if bundle:
        import pandas as pd
        order = bundle["features"]
        X = pd.DataFrame([[feats[f] for f in order]], columns=order)
        model = bundle["model"]
        label = str(model.predict(X)[0])
        proba = model.predict_proba(X)[0]
        probs = {str(c): round(float(p) * 100, 2) for c, p in zip(model.classes_, proba)}
        return label, round(float(max(proba)) * 100, 2), feats, probs, "Random Forest"

    pct = feats["overall_accuracy"]
    label = "Advanced" if pct >= 75 else "Intermediate" if pct >= 50 else "Beginner"
    return label, 100.0, feats, {label: 100.0}, "rule-based fallback"


def recommendation(level, weak_topics):
    if not weak_topics:
        base = "No weak area detected. Move to a harder mixed paper to push your ceiling."
    else:
        base = "Focus your next practice on: " + ", ".join(weak_topics) + "."
    tips = {
        "Beginner": " Start with easy sets, learn the standard formulas, and target accuracy before speed.",
        "Intermediate": " Drill medium questions under a timer and revise shortcuts for weak topics.",
        "Advanced": " Attempt hard mixed papers with sectional time limits to hold accuracy under pressure.",
    }
    return base + tips.get(level, "")
