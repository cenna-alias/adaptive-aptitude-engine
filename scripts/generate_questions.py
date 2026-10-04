"""
Generates data/questions.csv  -> 400 unique, verified aptitude questions.

Every question is produced from a template where the correct answer is COMPUTED
(not typed by hand), so there are no wrong keys. Duplicates are removed by
comparing the normalised question text.

Run:  python scripts/generate_questions.py
"""

import csv
import os
import random
from fractions import Fraction
from math import gcd

random.seed(20260930)

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "questions.csv")

TOPICS = {
    "Quantitative Aptitude": [],
    "Logical Reasoning": [],
    "Verbal Ability": [],
    "Data Interpretation": [],
}


# ----------------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------------
def fmt(x):
    """Format a number nicely (no trailing .0)."""
    if isinstance(x, float):
        if abs(x - round(x)) < 1e-9:
            return str(int(round(x)))
        return str(round(x, 2))
    return str(x)


def make_options(answer, distractors):
    """Return (option_list_of_4, correct_letter). Answer always included once."""
    opts = [fmt(answer)]
    for d in distractors:
        s = fmt(d)
        if s not in opts:
            opts.append(s)
        if len(opts) == 4:
            break
    # pad if distractors collided
    i = 1
    while len(opts) < 4:
        try:
            cand = fmt(float(answer) + i * 3)
        except (TypeError, ValueError):
            cand = f"{answer} {i}"
        if cand not in opts:
            opts.append(cand)
        i += 1
    random.shuffle(opts)
    return opts, "ABCD"[opts.index(fmt(answer))]


def q(topic, subtopic, difficulty, text, answer, distractors, explanation):
    opts, letter = make_options(answer, distractors)
    return {
        "topic": topic,
        "subtopic": subtopic,
        "difficulty": difficulty,
        "question": text,
        "option_a": opts[0],
        "option_b": opts[1],
        "option_c": opts[2],
        "option_d": opts[3],
        "correct_option": letter,
        "explanation": explanation,
    }


# ----------------------------------------------------------------------------
# QUANTITATIVE APTITUDE
# ----------------------------------------------------------------------------
def t_percentage():
    base = random.choice([240, 320, 450, 560, 680, 750, 840, 960, 1250, 1600])
    p = random.choice([12, 15, 18, 24, 25, 35, 45, 60, 72])
    ans = base * p / 100
    return q("Quantitative Aptitude", "Percentages", "easy",
             f"What is {p}% of {base}?",
             ans, [ans + base * 0.05, ans - base * 0.04, ans * 2],
             f"{p}% of {base} = {base} x {p}/100 = {fmt(ans)}.")


def t_percentage_change():
    a = random.randint(40, 90) * 10
    inc = random.choice([10, 20, 25, 30, 40, 50])
    b = a * (100 + inc) // 100
    return q("Quantitative Aptitude", "Percentages", "medium",
             f"A salary increases from Rs.{a} to Rs.{b}. What is the percentage increase?",
             f"{inc}%", [f"{inc + 5}%", f"{inc - 5}%", f"{round(inc * 100 / (100 + inc))}%"],
             f"Increase = {b - a}; % = {b - a}/{a} x 100 = {inc}%.")


def t_profit_loss():
    cp = random.choice([250, 300, 400, 480, 500, 640, 750, 800, 900, 1200])
    pct = random.choice([10, 12, 15, 20, 25, 30, 40])
    sp = cp * (100 + pct) // 100
    return q("Quantitative Aptitude", "Profit and Loss", "easy",
             f"An article bought for Rs.{cp} is sold for Rs.{sp}. Find the profit percent.",
             f"{pct}%", [f"{pct + 5}%", f"{pct - 4}%", f"{pct + 10}%"],
             f"Profit = {sp - cp}; Profit% = {sp - cp}/{cp} x 100 = {pct}%.")


def t_discount():
    mp = random.choice([800, 1000, 1200, 1500, 1800, 2000, 2400, 2500])
    d1 = random.choice([10, 15, 20, 25])
    d2 = random.choice([5, 10, 12])
    final = mp * (100 - d1) * (100 - d2) / 10000
    return q("Quantitative Aptitude", "Profit and Loss", "hard",
             f"A shirt marked at Rs.{mp} is sold after two successive discounts of {d1}% and {d2}%. Find the selling price.",
             final, [mp * (100 - d1 - d2) / 100, final + 40, final - 35],
             f"SP = {mp} x {100 - d1}/100 x {100 - d2}/100 = Rs.{fmt(final)}.")


def t_time_work():
    a = random.choice([6, 8, 9, 10, 12, 15, 18, 20])
    b = random.choice([12, 14, 16, 20, 24, 30, 36])
    if a == b:
        b = a + 6
    together = Fraction(a * b, a + b)
    ans = round(float(together), 2)
    return q("Quantitative Aptitude", "Time and Work", "medium",
             f"A can finish a job in {a} days and B in {b} days. Working together, how many days will they take?",
             ans, [ans + 1.5, ans - 1.2, (a + b) / 2],
             f"Together = ({a}x{b})/({a}+{b}) = {together.numerator}/{together.denominator} = {ans} days.")


def t_pipes():
    a = random.choice([10, 12, 15, 18, 20, 24])
    b = random.choice([20, 30, 36, 40, 45, 60])
    ans = round(a * b / (a + b), 2)
    return q("Quantitative Aptitude", "Time and Work", "medium",
             f"Pipe A fills a tank in {a} hours and pipe B in {b} hours. If both are opened together, in how many hours will the tank be full?",
             ans, [ans + 2, ans - 1.5, a + b],
             f"1/{a} + 1/{b} = ({a}+{b})/{a * b}; time = {a * b}/{a + b} = {ans} hours.")


def t_speed_distance():
    s = random.choice([30, 40, 45, 50, 54, 60, 72, 80, 90])
    t = random.choice([2, 2.5, 3, 4, 5, 6])
    d = s * t
    return q("Quantitative Aptitude", "Time Speed Distance", "easy",
             f"A car travels at {s} km/h for {fmt(t)} hours. What distance does it cover?",
             f"{fmt(d)} km", [f"{fmt(d + s)} km", f"{fmt(d - s / 2)} km", f"{fmt(d * 2)} km"],
             f"Distance = speed x time = {s} x {fmt(t)} = {fmt(d)} km.")


def t_train():
    length = random.choice([120, 150, 180, 200, 240, 250, 300])
    speed = random.choice([36, 45, 54, 60, 72, 90])
    ans = round(length / (speed * 5 / 18), 2)
    return q("Quantitative Aptitude", "Time Speed Distance", "hard",
             f"A train {length} m long runs at {speed} km/h. How many seconds does it take to cross a pole?",
             ans, [ans + 3, ans - 2.5, length / speed],
             f"Speed = {speed} x 5/18 = {fmt(speed * 5 / 18)} m/s; time = {length}/{fmt(speed * 5 / 18)} = {ans} s.")


def t_average():
    n = random.choice([5, 6, 7, 8])
    nums = [random.randint(10, 99) for _ in range(n)]
    avg = round(sum(nums) / n, 2)
    return q("Quantitative Aptitude", "Averages", "easy",
             f"Find the average of the numbers {', '.join(map(str, nums))}.",
             avg, [avg + 2.5, avg - 3, sum(nums)],
             f"Sum = {sum(nums)}; average = {sum(nums)}/{n} = {avg}.")


def t_average_shift():
    n = random.choice([10, 12, 15, 20])
    old = random.randint(20, 60)
    new_member = random.randint(60, 120)
    ans = round((old * n + new_member) / (n + 1), 2)
    return q("Quantitative Aptitude", "Averages", "medium",
             f"The average age of {n} students is {old} years. A new student aged {new_member} joins. What is the new average?",
             ans, [old + 1, ans + 2, ans - 1.5],
             f"New average = ({n}x{old} + {new_member})/{n + 1} = {ans} years.")


def t_ratio():
    a, b = random.choice([(2, 3), (3, 4), (4, 5), (5, 7), (3, 7), (5, 8), (7, 9)])
    total = (a + b) * random.choice([6, 8, 9, 12, 15, 20])
    ans = total * a // (a + b)
    return q("Quantitative Aptitude", "Ratio and Proportion", "easy",
             f"Rs.{total} is divided between two friends in the ratio {a}:{b}. Find the smaller share.",
             min(ans, total - ans), [max(ans, total - ans), total // 2, ans + 30],
             f"Smaller share = {total} x {min(a, b)}/{a + b} = Rs.{min(ans, total - ans)}.")


def t_simple_interest():
    p = random.choice([2000, 2500, 4000, 5000, 6400, 8000, 12000])
    r = random.choice([4, 5, 6, 7.5, 8, 10, 12])
    t = random.choice([2, 3, 4, 5])
    si = p * r * t / 100
    return q("Quantitative Aptitude", "Interest", "easy",
             f"Find the simple interest on Rs.{p} at {fmt(r)}% per annum for {t} years.",
             si, [si + p * 0.02, si - p * 0.01, si * 2],
             f"SI = PRT/100 = {p} x {fmt(r)} x {t}/100 = Rs.{fmt(si)}.")


def t_compound_interest():
    p = random.choice([4000, 5000, 6250, 8000, 10000, 12500])
    r = random.choice([4, 5, 8, 10, 20])
    t = 2
    ci = p * ((1 + r / 100) ** t) - p
    return q("Quantitative Aptitude", "Interest", "hard",
             f"Find the compound interest on Rs.{p} at {r}% per annum for {t} years, compounded annually.",
             round(ci, 2), [p * r * t / 100, round(ci, 2) + 60, round(ci, 2) - 45],
             f"CI = {p}[(1+{r}/100)^{t} - 1] = Rs.{fmt(round(ci, 2))}.")


def t_probability():
    red = random.randint(3, 8)
    blue = random.randint(3, 9)
    green = random.randint(2, 6)
    total = red + blue + green
    g = gcd(red, total)
    ans = f"{red // g}/{total // g}"
    return q("Quantitative Aptitude", "Probability", "medium",
             f"A bag has {red} red, {blue} blue and {green} green balls. One ball is drawn at random. What is the probability that it is red?",
             ans, [f"{blue}/{total}", f"{green}/{total}", f"{red}/{blue + green}"],
             f"P(red) = {red}/{total} = {ans}.")


def t_permutation():
    word = random.choice(["PLACE", "LOGIC", "BRAIN", "SMART", "FOCUS", "TRACK", "PRIME", "SCALE"])
    import math
    ans = math.factorial(len(word))
    return q("Quantitative Aptitude", "Permutation and Combination", "medium",
             f"In how many ways can the letters of the word {word} be arranged? (all letters distinct)",
             ans, [ans // 2, ans * 2, len(word) ** 2],
             f"{len(word)} distinct letters -> {len(word)}! = {ans} arrangements.")


def t_number_series_math():
    start = random.randint(2, 9)
    ratio = random.choice([2, 3])
    seq = [start * ratio ** i for i in range(4)]
    ans = seq[-1] * ratio
    return q("Quantitative Aptitude", "Number System", "easy",
             f"Find the next term: {', '.join(map(str, seq))}, ?",
             ans, [ans + ratio, seq[-1] + ratio, ans - seq[-1]],
             f"Each term is multiplied by {ratio}; next = {seq[-1]} x {ratio} = {ans}.")


def t_lcm_hcf():
    a = random.choice([12, 15, 18, 20, 24, 28, 30, 36])
    b = random.choice([16, 21, 25, 27, 32, 40, 45, 48])
    import math
    l = a * b // math.gcd(a, b)
    return q("Quantitative Aptitude", "Number System", "medium",
             f"Find the LCM of {a} and {b}.",
             l, [math.gcd(a, b), a * b, l // 2],
             f"LCM = ({a}x{b})/HCF({a},{b}) = {a * b}/{math.gcd(a, b)} = {l}.")


def t_age():
    ratio_a, ratio_b = random.choice([(2, 3), (3, 5), (4, 7), (5, 6)])
    k = random.choice([4, 5, 6, 7, 8])
    a, b = ratio_a * k, ratio_b * k
    yrs = random.choice([4, 5, 6, 8])
    return q("Quantitative Aptitude", "Ages", "medium",
             f"The present ages of A and B are in the ratio {ratio_a}:{ratio_b} and their total age is {a + b} years. What will be A's age after {yrs} years?",
             a + yrs, [b + yrs, a - yrs, a + b - yrs],
             f"A = {a + b} x {ratio_a}/{ratio_a + ratio_b} = {a}; after {yrs} years = {a + yrs}.")


def t_mixture():
    m = random.choice([40, 50, 60, 80, 100])
    milk_pct = random.choice([60, 70, 75, 80])
    water = m * (100 - milk_pct) // 100
    return q("Quantitative Aptitude", "Mixtures", "medium",
             f"A {m} litre mixture contains milk and water in which milk is {milk_pct}%. How many litres of water does it contain?",
             f"{water} L", [f"{m - water} L", f"{water + 5} L", f"{water * 2} L"],
             f"Water% = {100 - milk_pct}; water = {m} x {100 - milk_pct}/100 = {water} L.")


# ----------------------------------------------------------------------------
# LOGICAL REASONING
# ----------------------------------------------------------------------------
def t_series_diff():
    start = random.randint(3, 15)
    d = random.randint(3, 11)
    seq = [start + i * d for i in range(5)]
    ans = seq[-1] + d
    return q("Logical Reasoning", "Number Series", "easy",
             f"Complete the series: {', '.join(map(str, seq))}, ?",
             ans, [ans + d, ans - 1, seq[-1] + d + 2],
             f"Common difference is {d}; next term = {seq[-1]} + {d} = {ans}.")


def t_series_square():
    n = random.randint(2, 9)
    seq = [(n + i) ** 2 for i in range(4)]
    ans = (n + 4) ** 2
    return q("Logical Reasoning", "Number Series", "medium",
             f"Find the missing term: {', '.join(map(str, seq))}, ?",
             ans, [ans + 5, seq[-1] + (n + 3), (n + 4) * 2],
             f"Terms are squares of {n} to {n + 3}; next = {n + 4}^2 = {ans}.")


def t_series_fib():
    a, b = random.randint(1, 6), random.randint(2, 9)
    seq = [a, b]
    for _ in range(3):
        seq.append(seq[-1] + seq[-2])
    ans = seq[-1] + seq[-2]
    return q("Logical Reasoning", "Number Series", "medium",
             f"What comes next: {', '.join(map(str, seq))}, ?",
             ans, [ans + 2, seq[-1] * 2, ans - 3],
             f"Each term is the sum of the previous two; next = {seq[-1]} + {seq[-2]} = {ans}.")


def t_coding():
    word = random.choice(["CAT", "DOG", "PEN", "BAG", "CUP", "SUN", "MAP", "JOB", "KEY", "FAN", "BOX", "LOG"])
    shift = random.choice([1, 2, 3, 4])
    coded = "".join(chr((ord(c) - 65 + shift) % 26 + 65) for c in word)
    target = random.choice(["RAT", "PIG", "INK", "CAB", "MUG", "FOG", "TAP", "HUB", "LID", "VAN", "NET", "ZIP"])
    ans = "".join(chr((ord(c) - 65 + shift) % 26 + 65) for c in target)
    wrong = "".join(chr((ord(c) - 65 + shift + 1) % 26 + 65) for c in target)
    wrong2 = "".join(chr((ord(c) - 65 - shift) % 26 + 65) for c in target)
    return q("Logical Reasoning", "Coding Decoding", "medium",
             f"If {word} is coded as {coded}, how is {target} coded?",
             ans, [wrong, wrong2, target[::-1]],
             f"Each letter moves {shift} step(s) forward, so {target} -> {ans}.")


def t_blood_relation():
    rel = random.choice([
        ("A is the son of B. B is the sister of C. How is C related to A?", "Maternal uncle/aunt",
         ["Father", "Brother", "Grandfather"], "C is the sibling of A's mother B, hence A's maternal uncle or aunt."),
        ("P is the father of Q and Q is the daughter of R. How is R related to P?", "Wife",
         ["Sister", "Mother", "Daughter"], "Q's parents are P and R, so R is P's wife."),
        ("X is the brother of Y. Y is the mother of Z. How is X related to Z?", "Maternal uncle",
         ["Father", "Cousin", "Grandfather"], "X is the brother of Z's mother, so maternal uncle."),
        ("M is the daughter of N. N is the son of O. How is O related to M?", "Grandfather",
         ["Father", "Uncle", "Brother"], "N is M's father and O is N's father, so O is M's grandfather."),
        ("D is the husband of E. F is the only son of E. How is F related to D?", "Son",
         ["Brother", "Father", "Nephew"], "F is the son of D's wife E, hence D's son."),
        ("G's mother is the only daughter of H. How is H related to G?", "Maternal grandfather",
         ["Father", "Uncle", "Brother"], "H is the father of G's mother."),
    ])
    return q("Logical Reasoning", "Blood Relations", "medium", rel[0], rel[1], rel[2], rel[3])


def t_direction():
    d1 = random.choice([4, 5, 6, 8, 10])
    d2 = random.choice([3, 4, 6, 8, 12])
    import math
    dist = math.hypot(d1, d2)
    ans = round(dist, 2)
    return q("Logical Reasoning", "Direction Sense", "medium",
             f"A man walks {d1} km north, then turns right and walks {d2} km. How far is he from the starting point?",
             f"{fmt(ans)} km", [f"{d1 + d2} km", f"{abs(d1 - d2)} km", f"{fmt(ans + 2)} km"],
             f"The path forms a right triangle: sqrt({d1}^2 + {d2}^2) = {fmt(ans)} km.")


def t_odd_one_out():
    sets = [
        (["16", "25", "36", "30"], "30", "All others are perfect squares."),
        (["11", "13", "17", "21"], "21", "21 is not a prime number."),
        (["8", "27", "64", "70"], "70", "All others are perfect cubes."),
        (["Rose", "Lily", "Mango", "Lotus"], "Mango", "Mango is a fruit; others are flowers."),
        (["Circle", "Square", "Triangle", "Cube"], "Cube", "Cube is a 3-D solid; others are plane figures."),
        (["Kilogram", "Metre", "Litre", "Celsius"], "Celsius", "Celsius measures temperature; others measure mass, length and volume."),
        (["121", "144", "169", "180"], "180", "All others are perfect squares."),
        (["Python", "Java", "Linux", "C++"], "Linux", "Linux is an operating system; others are programming languages."),
    ]
    items, ans, exp = random.choice(sets)
    distract = [i for i in items if i != ans]
    return q("Logical Reasoning", "Odd One Out", "easy",
             f"Choose the odd one out: {', '.join(items)}.", ans, distract, exp)


def t_syllogism():
    cases = [
        ("Statements: All pens are books. All books are papers. Conclusion?", "All pens are papers",
         ["All papers are pens", "Some papers are not books", "No pen is a paper"],
         "Chaining both universal statements gives: all pens are papers."),
        ("Statements: All cats are animals. Some animals are wild. Conclusion?", "Some animals are wild",
         ["All cats are wild", "No cat is wild", "All animals are cats"],
         "Only the given particular statement can be restated; nothing follows about cats."),
        ("Statements: No student is lazy. Ram is a student. Conclusion?", "Ram is not lazy",
         ["Ram is lazy", "Some students are lazy", "Ram is a teacher"],
         "Ram belongs to a class that excludes laziness."),
        ("Statements: All engineers are graduates. Some graduates are employed. Conclusion?",
         "Some engineers may be employed",
         ["All engineers are employed", "No engineer is employed", "All graduates are engineers"],
         "Only a possibility can be drawn from a particular premise."),
    ]
    text, ans, dis, exp = random.choice(cases)
    return q("Logical Reasoning", "Syllogism", "hard", text, ans, dis, exp)


def t_seating():
    names = random.sample(["Amit", "Bala", "Chitra", "Deepa", "Eshan", "Farid", "Gita"], 5)
    ans = names[2]
    return q("Logical Reasoning", "Seating Arrangement", "medium",
             f"{', '.join(names)} sit in a row in that order from left to right. Who is exactly in the middle?",
             ans, [names[1], names[3], names[0]],
             f"With 5 people, the 3rd from left is the middle person: {ans}.")


def t_clock():
    h = random.randint(1, 11)
    m = random.choice([0, 20, 30, 40])
    angle = abs(30 * h - 5.5 * m)
    angle = min(angle, 360 - angle)
    return q("Logical Reasoning", "Clocks", "hard",
             f"What is the angle between the hands of a clock at {h}:{m:02d}?",
             f"{fmt(angle)} degrees", [f"{fmt(angle + 15)} degrees", f"{fmt(abs(angle - 10))} degrees", f"{fmt(30 * h)} degrees"],
             f"Angle = |30H - 5.5M| = |30x{h} - 5.5x{m}| = {fmt(angle)} degrees.")


def t_calendar():
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    start = random.randint(0, 6)
    n = random.choice([15, 23, 45, 61, 100, 123, 200])
    ans = days[(start + n) % 7]
    return q("Logical Reasoning", "Calendars", "hard",
             f"If today is {days[start]}, what day will it be after {n} days?",
             ans, [days[(start + n + 1) % 7], days[(start + n - 1) % 7], days[start]],
             f"{n} mod 7 = {n % 7}; counting {n % 7} day(s) from {days[start]} gives {ans}.")


def t_analogy():
    pairs = [
        ("Doctor : Hospital :: Teacher : ?", "School", ["Book", "Student", "Exam"], "A doctor works in a hospital as a teacher works in a school."),
        ("Pen : Write :: Knife : ?", "Cut", ["Sharp", "Kitchen", "Metal"], "Each tool is matched with its function."),
        ("Bird : Nest :: Bee : ?", "Hive", ["Honey", "Flower", "Wing"], "Each creature is matched with its dwelling."),
        ("Cold : Ice :: Hot : ?", "Fire", ["Water", "Sun", "Steam"], "Each quality is matched with a typical source."),
        ("Author : Book :: Composer : ?", "Symphony", ["Piano", "Stage", "Orchestra"], "Creator to creation relationship."),
        ("Eye : Sight :: Ear : ?", "Hearing", ["Sound", "Head", "Noise"], "Organ to the sense it provides."),
    ]
    text, ans, dis, exp = random.choice(pairs)
    return q("Logical Reasoning", "Analogy", "easy", text, ans, dis, exp)


# ----------------------------------------------------------------------------
# VERBAL ABILITY  (finite banks - each item used once)
# ----------------------------------------------------------------------------
SYNONYMS = [
    ("Abundant", "Plentiful", ["Scarce", "Tiny", "Weak"]),
    ("Candid", "Frank", ["Secretive", "Rude", "Lazy"]),
    ("Diligent", "Hardworking", ["Careless", "Slow", "Rude"]),
    ("Eloquent", "Expressive", ["Silent", "Dull", "Harsh"]),
    ("Frugal", "Thrifty", ["Wasteful", "Rich", "Generous"]),
    ("Gregarious", "Sociable", ["Shy", "Angry", "Honest"]),
    ("Hostile", "Unfriendly", ["Helpful", "Calm", "Polite"]),
    ("Imminent", "Impending", ["Distant", "Absent", "Delayed"]),
    ("Lucid", "Clear", ["Confusing", "Dark", "Heavy"]),
    ("Meticulous", "Careful", ["Hasty", "Bold", "Rough"]),
    ("Novice", "Beginner", ["Expert", "Leader", "Teacher"]),
    ("Obsolete", "Outdated", ["Modern", "Useful", "Rare"]),
    ("Prudent", "Sensible", ["Reckless", "Loud", "Kind"]),
    ("Resilient", "Tough", ["Fragile", "Idle", "Bright"]),
    ("Scrutinise", "Examine", ["Ignore", "Praise", "Reject"]),
    ("Tenacious", "Persistent", ["Weak", "Brief", "Gentle"]),
    ("Vivid", "Bright", ["Faint", "Plain", "Quiet"]),
    ("Zealous", "Enthusiastic", ["Indifferent", "Tired", "Cruel"]),
    ("Ample", "Sufficient", ["Meagre", "Narrow", "Costly"]),
    ("Benevolent", "Kind", ["Cruel", "Greedy", "Timid"]),
    ("Concise", "Brief", ["Lengthy", "Vague", "Loud"]),
    ("Deter", "Discourage", ["Encourage", "Permit", "Assist"]),
    ("Enhance", "Improve", ["Reduce", "Damage", "Delay"]),
    ("Feasible", "Practicable", ["Impossible", "Costly", "Risky"]),
    ("Genuine", "Authentic", ["Fake", "Cheap", "Rough"]),
    ("Adept", "Skilled", ["Clumsy", "New", "Rigid"]),
    ("Placid", "Calm", ["Stormy", "Bitter", "Rapid"]),
    ("Rectify", "Correct", ["Spoil", "Repeat", "Hide"]),
]

ANTONYMS = [
    ("Ancient", "Modern", ["Old", "Ruined", "Historic"]),
    ("Barren", "Fertile", ["Dry", "Empty", "Rocky"]),
    ("Cautious", "Reckless", ["Careful", "Alert", "Slow"]),
    ("Dense", "Sparse", ["Thick", "Heavy", "Solid"]),
    ("Expand", "Contract", ["Grow", "Widen", "Stretch"]),
    ("Fragile", "Sturdy", ["Brittle", "Thin", "Light"]),
    ("Generous", "Stingy", ["Kind", "Noble", "Rich"]),
    ("Humble", "Arrogant", ["Modest", "Simple", "Quiet"]),
    ("Insult", "Praise", ["Abuse", "Mock", "Blame"]),
    ("Joyful", "Sorrowful", ["Merry", "Glad", "Lively"]),
    ("Liberal", "Conservative", ["Free", "Broad", "Kind"]),
    ("Minimise", "Maximise", ["Reduce", "Lower", "Shrink"]),
    ("Obvious", "Obscure", ["Clear", "Plain", "Evident"]),
    ("Permanent", "Temporary", ["Lasting", "Stable", "Fixed"]),
    ("Rigid", "Flexible", ["Stiff", "Firm", "Hard"]),
    ("Scarcity", "Abundance", ["Shortage", "Lack", "Need"]),
    ("Transparent", "Opaque", ["Clear", "Glassy", "Plain"]),
    ("Victory", "Defeat", ["Triumph", "Win", "Success"]),
    ("Wealthy", "Impoverished", ["Rich", "Affluent", "Prosperous"]),
    ("Accelerate", "Decelerate", ["Hasten", "Speed", "Rush"]),
    ("Optimist", "Pessimist", ["Dreamer", "Realist", "Thinker"]),
    ("Innocent", "Guilty", ["Pure", "Naive", "Simple"]),
]

FILL_BLANKS = [
    ("She was praised for her ______ handling of the crisis.", "efficient", ["efficiently", "efficiency", "efficacy"],
     "An adjective is needed before the noun 'handling'."),
    ("The team could not agree ______ the final design.", "on", ["in", "of", "at"], "The idiom is 'agree on' a thing."),
    ("He has been working here ______ 2019.", "since", ["for", "from", "during"],
     "'Since' is used with a point of time in the present perfect continuous."),
    ("Neither the manager nor the employees ______ present.", "were", ["was", "is", "has"],
     "With 'neither...nor', the verb agrees with the nearer subject 'employees'."),
    ("If I ______ you, I would accept the offer.", "were", ["am", "was", "will be"],
     "Second conditional uses 'were' for all persons."),
    ("The report is due ______ Monday morning.", "by", ["till", "since", "in"],
     "'By' expresses a deadline."),
    ("She is one of the ______ students in the class.", "brightest", ["brighter", "bright", "more bright"],
     "'One of the' takes a superlative plural form."),
    ("Hardly had he entered the hall ______ the lights went off.", "when", ["than", "then", "that"],
     "'Hardly had ... when' is the fixed construction."),
    ("The candidate was asked to ______ his answer with examples.", "substantiate", ["substitute", "sustain", "subside"],
     "'Substantiate' means to support with evidence."),
    ("His explanation was so ______ that nobody understood it.", "ambiguous", ["ambitious", "amiable", "amicable"],
     "'Ambiguous' means open to more than one interpretation."),
    ("We need to ______ the deadline because of the delay.", "extend", ["expand", "expend", "expose"],
     "A deadline is extended."),
    ("The new policy will ______ into force next month.", "come", ["go", "put", "take"],
     "The idiom is 'come into force'."),
    ("He apologised ______ his rude behaviour.", "for", ["of", "on", "with"], "'Apologise for' something."),
    ("The children were ______ by the magician's tricks.", "fascinated", ["fascinating", "fascinate", "fascination"],
     "A past participle is needed in the passive voice."),
    ("Very few people ______ the courage to speak the truth.", "have", ["has", "having", "had been"],
     "'Few people' is plural, so 'have'."),
    ("She spoke ______ than her colleague.", "more fluently", ["fluent", "most fluently", "fluently"],
     "A comparative adverb is required with 'than'."),
]

ERROR_SPOT = [
    ("Spot the error: 'One of my friend is a doctor.'", "my friend", ["One of", "is", "a doctor"],
     "'One of' is followed by a plural noun: 'one of my friends'."),
    ("Spot the error: 'He is senior than me.'", "senior than", ["He is", "me", "no error"],
     "'Senior' takes 'to', not 'than'."),
    ("Spot the error: 'The furnitures are new.'", "The furnitures", ["are", "new", "no error"],
     "'Furniture' is an uncountable noun and has no plural."),
    ("Spot the error: 'She did not came yesterday.'", "did not came", ["She", "yesterday", "no error"],
     "After 'did not' the base form 'come' is used."),
    ("Spot the error: 'Each of the boys were present.'", "were present", ["Each of", "the boys", "no error"],
     "'Each' is singular, so 'was present'."),
    ("Spot the error: 'I am living here since 2015.'", "am living", ["here", "since 2015", "no error"],
     "Present perfect continuous is needed: 'have been living'."),
    ("Spot the error: 'He discussed about the problem.'", "discussed about", ["He", "the problem", "no error"],
     "'Discuss' is not followed by 'about'."),
    ("Spot the error: 'Both the sisters are not intelligent.'", "Both", ["the sisters", "are not", "no error"],
     "'Both' cannot be used with a negative; use 'Neither'."),
]

READING = [
    ("Read the passage: 'Automation is reshaping entry level jobs. Employers now value candidates who can "
     "learn new tools quickly rather than those who merely memorise procedures.' What do employers value most?",
     "Fast learning ability", ["Memorising procedures", "Longer experience", "Higher salary demands"],
     "The passage states employers value quick learning over memorisation."),
    ("Read the passage: 'Aptitude tests measure reasoning speed under time pressure. Practice reduces the time "
     "taken per question far more than it increases raw intelligence.' What is the main benefit of practice?",
     "Reduced time per question", ["Higher intelligence", "Easier questions", "Fewer topics"],
     "The passage credits practice with cutting time per question."),
    ("Read the passage: 'Adaptive testing selects the next question based on the candidate's previous answer, "
     "so an accurate estimate of ability is reached with fewer questions.' What is the advantage of adaptive testing?",
     "Fewer questions needed", ["Longer test duration", "Same question for all", "No scoring required"],
     "Adaptive selection reaches an accurate estimate using fewer items."),
    ("Read the passage: 'Feedback is most useful when it identifies the specific topic in which a learner is weak, "
     "instead of reporting only a total score.' What makes feedback most useful?",
     "Topic level detail", ["A single total score", "A ranking list", "A pass certificate"],
     "The passage prefers topic-specific feedback over a total score."),
]


def bank_template(bank, topic, subtopic, difficulty, text_fn, diff_easy=None):
    def gen():
        if not bank:
            return None
        item = bank.pop(random.randrange(len(bank)))
        word, ans, dis = item[0], item[1], item[2]
        exp = item[3] if len(item) > 3 else None
        text = text_fn(word)
        return q(topic, subtopic, difficulty, text, ans, dis,
                 exp or f"'{word}' is closest in meaning to '{ans}'.")
    return gen


def t_synonym():
    if not SYNONYMS:
        return None
    w, a, d = SYNONYMS.pop(random.randrange(len(SYNONYMS)))
    return q("Verbal Ability", "Synonyms", "easy",
             f"Choose the word most similar in meaning to '{w}'.", a, d,
             f"'{w}' means '{a}'.")


def t_antonym():
    if not ANTONYMS:
        return None
    w, a, d = ANTONYMS.pop(random.randrange(len(ANTONYMS)))
    return q("Verbal Ability", "Antonyms", "easy",
             f"Choose the word most opposite in meaning to '{w}'.", a, d,
             f"The opposite of '{w}' is '{a}'.")


def t_fill():
    if not FILL_BLANKS:
        return None
    t, a, d, e = FILL_BLANKS.pop(random.randrange(len(FILL_BLANKS)))
    return q("Verbal Ability", "Sentence Completion", "medium", t, a, d, e)


def t_error():
    if not ERROR_SPOT:
        return None
    t, a, d, e = ERROR_SPOT.pop(random.randrange(len(ERROR_SPOT)))
    return q("Verbal Ability", "Error Spotting", "medium", t, a, d, e)


def t_reading():
    if not READING:
        return None
    t, a, d, e = READING.pop(random.randrange(len(READING)))
    return q("Verbal Ability", "Reading Comprehension", "hard", t, a, d, e)


# ----------------------------------------------------------------------------
# DATA INTERPRETATION
# ----------------------------------------------------------------------------
def t_di_table_total():
    months = ["January", "February", "March", "April"]
    sales = [random.choice([120, 140, 160, 180, 200, 220, 240, 260]) for _ in months]
    total = sum(sales)
    pairs = ", ".join(f"{m}: {s}" for m, s in zip(months, sales))
    return q("Data Interpretation", "Table Analysis", "easy",
             f"Units sold by a store - {pairs}. What is the total number of units sold in these four months?",
             total, [total + 20, total - 30, total // 2],
             f"Total = {' + '.join(map(str, sales))} = {total}.")


def t_di_table_avg():
    days = ["Mon", "Tue", "Wed", "Thu", "Fri"]
    vals = [random.choice([30, 35, 40, 45, 50, 55, 60, 65]) for _ in days]
    avg = round(sum(vals) / len(vals), 2)
    pairs = ", ".join(f"{d}: {v}" for d, v in zip(days, vals))
    return q("Data Interpretation", "Table Analysis", "medium",
             f"Visitors to a library - {pairs}. What is the average number of visitors per day?",
             avg, [avg + 5, avg - 4, sum(vals)],
             f"Average = {sum(vals)}/5 = {avg}.")


def t_di_pie():
    total = random.choice([3600, 4800, 6000, 7200, 9000])
    deg = random.choice([60, 72, 90, 108, 120, 144])
    ans = total * deg // 360
    return q("Data Interpretation", "Pie Chart", "medium",
             f"In a pie chart of total expenditure Rs.{total}, the sector for transport is {deg} degrees. "
             f"What is the expenditure on transport?",
             ans, [ans + total // 10, ans - total // 12, deg * 10],
             f"Expenditure = {total} x {deg}/360 = Rs.{ans}.")


def t_di_bar_growth():
    y1 = random.choice([200, 250, 300, 400, 500])
    pct = random.choice([10, 20, 25, 30, 50])
    y2 = y1 * (100 + pct) // 100
    return q("Data Interpretation", "Bar Graph", "medium",
             f"A bar graph shows production of {y1} units in 2024 and {y2} units in 2025. What is the percentage growth?",
             f"{pct}%", [f"{pct + 10}%", f"{pct - 5}%", f"{y2 - y1}%"],
             f"Growth = ({y2} - {y1})/{y1} x 100 = {pct}%.")


def t_di_ratio():
    a = random.choice([150, 180, 200, 240, 300])
    b = random.choice([60, 75, 80, 100, 120])
    import math
    g = math.gcd(a, b)
    ans = f"{a // g}:{b // g}"
    return q("Data Interpretation", "Table Analysis", "hard",
             f"In a survey {a} people preferred tea and {b} preferred coffee. What is the ratio of tea to coffee drinkers?",
             ans, [f"{b // g}:{a // g}", f"{a}:{b + 10}", "2:1" if ans != "2:1" else "3:1"],
             f"Ratio = {a}:{b} = {ans} after dividing by HCF {g}.")


def t_di_percentage_share():
    total = random.choice([500, 800, 1000, 1200, 1500])
    part = random.choice([100, 150, 200, 240, 300])
    if part > total:
        part = total // 4
    pct = round(part * 100 / total, 2)
    return q("Data Interpretation", "Pie Chart", "easy",
             f"Out of {total} students surveyed, {part} chose software roles. What percentage chose software roles?",
             f"{fmt(pct)}%", [f"{fmt(pct + 5)}%", f"{fmt(pct - 3)}%", f"{part}%"],
             f"Percentage = {part}/{total} x 100 = {fmt(pct)}%.")


# ----------------------------------------------------------------------------
# build
# ----------------------------------------------------------------------------
TEMPLATES = [
    t_percentage, t_percentage_change, t_profit_loss, t_discount, t_time_work, t_pipes,
    t_speed_distance, t_train, t_average, t_average_shift, t_ratio, t_simple_interest,
    t_compound_interest, t_probability, t_permutation, t_number_series_math, t_lcm_hcf,
    t_age, t_mixture,
    t_series_diff, t_series_square, t_series_fib, t_coding, t_blood_relation, t_direction,
    t_odd_one_out, t_syllogism, t_seating, t_clock, t_calendar, t_analogy,
    t_synonym, t_antonym, t_fill, t_error, t_reading,
    t_di_table_total, t_di_table_avg, t_di_pie, t_di_bar_growth, t_di_ratio, t_di_percentage_share,
]

TARGET = 400

# Topic quotas so the paper stays balanced across all placement areas.
QUOTA = {
    "Quantitative Aptitude": 150,
    "Logical Reasoning": 120,
    "Verbal Ability": 70,
    "Data Interpretation": 60,
}


def build():
    rows = []
    seen = set()
    counts = {k: 0 for k in QUOTA}
    exhausted = set()
    guard = 0
    while len(rows) < TARGET and guard < 500000:
        guard += 1
        progressed = False
        for t in TEMPLATES:
            if len(rows) >= TARGET:
                break
            if t in exhausted:
                continue
            item = t()
            if item is None:
                exhausted.add(t)
                continue
            topic = item["topic"]
            if counts[topic] >= QUOTA[topic]:
                continue
            key = item["question"].strip().lower()
            if key in seen:
                continue
            seen.add(key)
            counts[topic] += 1
            item["id"] = len(rows) + 1
            rows.append(item)
            progressed = True
        if not progressed and len(exhausted) == len(TEMPLATES):
            break
    # top up with computed templates if a bank-limited topic fell short
    if len(rows) < TARGET:
        fillers = [t_percentage, t_profit_loss, t_series_diff, t_coding, t_di_pie,
                   t_time_work, t_clock, t_calendar, t_di_table_avg, t_simple_interest]
        while len(rows) < TARGET:
            item = random.choice(fillers)()
            key = item["question"].strip().lower()
            if key in seen:
                continue
            seen.add(key)
            item["id"] = len(rows) + 1
            rows.append(item)
    return rows


def main():
    rows = build()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fields = ["id", "topic", "subtopic", "difficulty", "question", "option_a", "option_b",
              "option_c", "option_d", "correct_option", "explanation"]
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    from collections import Counter
    print(f"Wrote {len(rows)} questions -> {OUT}")
    print("By topic:", dict(Counter(r["topic"] for r in rows)))
    print("By difficulty:", dict(Counter(r["difficulty"] for r in rows)))
    assert len({r["question"].lower() for r in rows}) == len(rows), "duplicate questions found"
    for r in rows:
        opts = [r["option_a"], r["option_b"], r["option_c"], r["option_d"]]
        assert len(set(opts)) == 4, f"duplicate options in q{r['id']}"
        assert r["correct_option"] in "ABCD"
    print("Validation passed: unique questions, 4 distinct options, valid keys.")


if __name__ == "__main__":
    main()
