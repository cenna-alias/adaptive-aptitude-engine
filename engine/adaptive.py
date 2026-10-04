"""
Adaptive question-selection engine.

1. TOPIC BLUEPRINT - every full test covers all four placement areas in a fixed
   ratio, so the report always has topic-wise data.
2. DIFFICULTY LADDER - two correct in a row promotes the learner to a harder
   question, two wrong in a row demotes. Ability is estimated with fewer items.
3. NO REPEATS - a question is never served twice in one attempt, and questions
   seen in earlier attempts are avoided while unseen ones remain.
"""

import random

from models import Answer, Question, TestAttempt, db

LEVELS = ["easy", "medium", "hard"]

FULL_BLUEPRINT = {
    "Quantitative Aptitude": 7,
    "Logical Reasoning": 6,
    "Verbal Ability": 4,
    "Data Interpretation": 3,
}


def build_topic_plan(length, focus_topics=None):
    """Return a list of topics, one per question slot."""
    if focus_topics:
        return [focus_topics[i % len(focus_topics)] for i in range(length)]

    plan = []
    for topic, count in FULL_BLUEPRINT.items():
        plan += [topic] * count
    while len(plan) < length:
        plan.append(random.choice(list(FULL_BLUEPRINT)))
    plan = plan[:length]
    random.shuffle(plan)
    return plan


def next_difficulty(current, results):
    """results: list of bools, most recent last."""
    idx = LEVELS.index(current)
    tail = results[-2:]
    if len(tail) == 1:
        idx = min(idx + 1, 2) if tail[0] else max(idx - 1, 0)
    elif all(tail):
        idx = min(idx + 1, 2)
    elif not any(tail):
        idx = max(idx - 1, 0)
    return LEVELS[idx]


def seen_question_ids(user_id):
    rows = (db.session.query(Answer.question_id)
            .join(TestAttempt, Answer.attempt_id == TestAttempt.id)
            .filter(TestAttempt.user_id == user_id).distinct().all())
    return {r[0] for r in rows}


def _pool(topic, diff, exclude):
    q = Question.query.filter(Question.active.is_(True))
    if topic:
        q = q.filter(Question.topic == topic)
    if diff:
        q = q.filter(Question.difficulty == diff)
    if exclude:
        q = q.filter(~Question.id.in_(exclude))
    return q.all()


def pick_question(topic, difficulty, exclude_ids, user_id=None):
    """Pick one active question, relaxing constraints only when forced to."""
    exclude = set(exclude_ids or [])
    seen = seen_question_ids(user_id) if user_id else set()
    ladder = [difficulty] + [d for d in LEVELS if d != difficulty]

    for diff in ladder:                       # fresh questions first
        pool = _pool(topic, diff, exclude | seen)
        if pool:
            return random.choice(pool)
    for diff in ladder:                       # bank exhausted for this user
        pool = _pool(topic, diff, exclude)
        if pool:
            return random.choice(pool)
    pool = _pool(None, None, exclude)         # any topic as last resort
    return random.choice(pool) if pool else None
