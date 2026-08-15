import random
from datetime import datetime
from pathlib import Path


def load_random_line(filename: str) -> str | None:
    try:
        text_file = Path(__file__).parent / filename
        with open(text_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
        if not lines:
            return None
        while True:
            line = random.choice(lines).strip()
            if line and not line.startswith("//"):
                return line
    except Exception:
        return None


def load_random_text() -> str | None:
    weekday = datetime.now().weekday()
    prob = 0.5 if weekday in (1, 4) else 0.2

    if random.random() < 0.4:
        sentence = load_random_line("sentences.txt")
        if sentence:
            return f"\n{sentence}"
    elif random.random() < prob:
        question = load_random_line("question.txt")
        if question:
            return f"\n{question}"
    return None