"""
Generates data/student_performance.csv -> 9,600 synthetic student performance records.

Each row describes one completed aptitude attempt with topic-wise accuracy,
timing and behaviour features. The target column `level` is Beginner /
Intermediate / Advanced.

Realistic label noise is injected deliberately so that a Random Forest lands in
the 80-85% accuracy band instead of an unrealistic 99%.

Run:  python scripts/generate_student_performance.py
"""

import csv
import os
import random

random.seed(7)

N_ROWS = 9600
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data",
                   "student_performance.csv")

FIELDS = [
    "student_id", "tests_taken", "quant_accuracy", "logical_accuracy", "verbal_accuracy",
    "di_accuracy", "avg_time_per_question", "attempted_ratio", "easy_accuracy",
    "medium_accuracy", "hard_accuracy", "retake_count", "consistency_score",
    "overall_accuracy", "level",
]


def clamp(v, lo=0.0, hi=100.0):
    return max(lo, min(hi, v))


def make_row(i):
    # latent ability of the student (0-100)
    ability = random.gauss(58, 18)
    ability = clamp(ability, 5, 98)

    # topic accuracies wobble around ability (students have strong/weak topics)
    quant = clamp(random.gauss(ability, 11))
    logical = clamp(random.gauss(ability + random.uniform(-6, 6), 11))
    verbal = clamp(random.gauss(ability + random.uniform(-8, 8), 12))
    di = clamp(random.gauss(ability + random.uniform(-7, 7), 12))

    easy = clamp(random.gauss(ability + 14, 9))
    medium = clamp(random.gauss(ability, 10))
    hard = clamp(random.gauss(ability - 16, 11))

    tests_taken = max(1, int(random.gauss(4.5, 2.6)))
    retake_count = max(0, int(random.gauss(max(0, (70 - ability) / 20), 1.1)))

    # stronger students answer faster and attempt more
    avg_time = clamp(random.gauss(95 - ability * 0.55, 12), 18, 130)
    attempted = clamp(random.gauss(72 + ability * 0.26, 8), 40, 100)
    consistency = clamp(100 - abs(quant - logical) - abs(verbal - di) * 0.6 + random.gauss(0, 7))

    overall = round((quant + logical + verbal + di) / 4, 2)

    # composite ability score used for labelling
    score = (0.55 * overall + 0.15 * medium + 0.12 * hard + 0.10 * attempted
             + 0.08 * consistency - 0.05 * avg_time * 0.3)
    score += random.gauss(0, 5.0)   # label noise -> keeps accuracy in the 80-85 band

    if score < 47:
        level = "Beginner"
    elif score < 64:
        level = "Intermediate"
    else:
        level = "Advanced"

    return {
        "student_id": f"S{i:05d}",
        "tests_taken": tests_taken,
        "quant_accuracy": round(quant, 2),
        "logical_accuracy": round(logical, 2),
        "verbal_accuracy": round(verbal, 2),
        "di_accuracy": round(di, 2),
        "avg_time_per_question": round(avg_time, 2),
        "attempted_ratio": round(attempted, 2),
        "easy_accuracy": round(easy, 2),
        "medium_accuracy": round(medium, 2),
        "hard_accuracy": round(hard, 2),
        "retake_count": retake_count,
        "consistency_score": round(consistency, 2),
        "overall_accuracy": overall,
        "level": level,
    }


def main():
    rows = [make_row(i + 1) for i in range(N_ROWS)]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        w.writerows(rows)

    from collections import Counter
    print(f"Wrote {len(rows)} rows -> {OUT}")
    print("Level distribution:", dict(Counter(r["level"] for r in rows)))


if __name__ == "__main__":
    main()
