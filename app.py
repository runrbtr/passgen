import json
import os
import random
import string
import threading

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

WORDS_PATH = os.path.join(os.path.dirname(__file__), "data", "words.txt")
COUNTER_PATH = os.path.join(os.path.dirname(__file__), "data", "counter.json")
SYMBOLS = "!@#$%&*-_"

_lock = threading.Lock()

with open(WORDS_PATH, encoding="utf-8") as f:
    WORDS = [w.strip() for w in f if w.strip()]


def _load_counter():
    if os.path.exists(COUNTER_PATH):
        try:
            with open(COUNTER_PATH, encoding="utf-8") as f:
                return json.load(f).get("count", 0)
        except (json.JSONDecodeError, OSError):
            return 0
    return 0


def _save_counter(count):
    with open(COUNTER_PATH, "w", encoding="utf-8") as f:
        json.dump({"count": count}, f)


_counter = _load_counter()


def increment_counter():
    global _counter
    with _lock:
        _counter += 1
        _save_counter(_counter)
        return _counter


def random_word():
    return random.choice(WORDS)


def random_digits(n):
    return "".join(random.choice(string.digits) for _ in range(n))


def random_case(word):
    return "".join(c.upper() if random.random() < 0.4 else c.lower() for c in word)


def gen_basic():
    return f"{random_word().capitalize()}.{random_digits(2)}"


def gen_medium():
    n_words = random.choice([1, 2])
    symbol = random.choice(SYMBOLS)
    words_part = symbol.join(random_word().capitalize() for _ in range(n_words))
    return f"{words_part}{symbol}{random_digits(2)}"


def gen_hard():
    n_words = random.choice([2, 3])
    parts = [random_case(random_word()) for _ in range(n_words)]
    symbol1 = random.choice(SYMBOLS)
    symbol2 = random.choice(SYMBOLS)
    return f"{symbol1.join(parts)}{symbol2}{random_digits(3)}"


GENERATORS = {"basic": gen_basic, "medium": gen_medium, "hard": gen_hard}


def generate_password(complexity, min_length):
    gen_fn = GENERATORS.get(complexity, gen_basic)

    pwd = gen_fn()
    attempts = 0
    while len(pwd) < min_length and attempts < 30:
        pwd = gen_fn()
        attempts += 1

    pad_chars = SYMBOLS + string.digits
    while len(pwd) < min_length:
        pwd += random.choice(pad_chars)

    return pwd


@app.route("/")
def index():
    return render_template("index.html", count=_counter)


@app.route("/generate", methods=["POST"])
def generate():
    data = request.get_json(silent=True) or {}
    complexity = data.get("complexity", "basic")
    if complexity not in GENERATORS:
        complexity = "basic"

    try:
        min_length = int(data.get("min_length", 8))
    except (TypeError, ValueError):
        min_length = 8
    min_length = max(4, min(min_length, 64))

    password = generate_password(complexity, min_length)
    count = increment_counter()

    return jsonify({"password": password, "count": count})


@app.route("/count")
def count():
    return jsonify({"count": _counter})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
