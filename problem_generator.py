"""
problem_generator.py — generates coding problems via Groq instead of
relying on a hardcoded bank.

Each generated problem matches exactly the schema the rest of the
game expects (see snippets.py): name, description, the correct lines
in order, a pool of decoy lines, an explanation for every decoy, and a
note on why each correct line belongs where it does.

If Groq is unconfigured, unreachable, or returns something that fails
validation after a couple of retries, generate_problem() returns None
and the caller (snippets.py) falls back to a small hardcoded bank so
the game keeps working without a Groq account or network access.
"""

import json
import random
import re
import urllib.request
import urllib.error
import ssl
import certifi
import requests
from config import GROQ_API_KEY, GROQ_MODEL, GROQ_API_URL

# Groq still writes ALL of the actual code, decoys, and explanations
# fresh every time — this list just keeps topics varied and scoped to
# something short enough to verify and display on a small grid.
TOPICS = [
    "a function that reverses a string",
    "a function that counts vowels in a string",
    "a function that checks if a number is prime",
    "a function that finds the maximum value in a list",
    "a function that removes duplicates from a list while preserving order",
    "FizzBuzz for the numbers 1 through n",
    "a function that flattens a one-level-nested list",
    "a stack-based function that checks if parentheses are balanced",
    "a function that computes the sum of the digits of a number",
    "a function that finds the second-largest number in a list",
    "a recursive function that computes the greatest common divisor",
    "a function that counts how many times each word appears in a string",
    "a function that checks if a list is sorted in ascending order",
    "a function that rotates a list left by k positions",
    "a function that merges two already-sorted lists into one sorted list",
    "a function that returns the first non-repeating character in a string",
]

_SCHEMA_PROMPT = """You are generating a coding exercise for an interactive line-by-line \
code-building game. The learner is shown a shuffled pool of code lines (some correct, some \
decoys) and must pick the correct next line, in order.

Return ONLY valid JSON, no markdown fences, no commentary, matching exactly this schema:

{{
  "name": "short title, 2-4 words",
  "description": "one sentence describing what is being built",
  "target": ["line 1", "line 2", "..."],
  "distractors": ["wrong line 1", "wrong line 2", "..."],
  "explanations": {{"wrong line 1": "one short sentence on why it's wrong", "...": "..."}},
  "correct_notes": {{"0": "one short sentence on why target[0] belongs there", "1": "...", "...": "..."}}
}}

Requirements:
- "target" is a short, CORRECT Python function (4-8 lines) solving: {topic}
- Each element of "target" is exactly one line of code, already indented with 2 spaces \
per nesting level (no tabs), in correct top-to-bottom order. Do not include comments or \
blank lines.
- "distractors" has 6-8 entries: plausible WRONG lines a learner might mistake for correct \
(off-by-one errors, swapped operators/conditions, wrong variable, infinite-recursion traps, \
inverted comparisons, etc). None may be identical to any line already in "target".
- "explanations" must have EXACTLY one key per distractor, copied character-for-character, \
mapped to a short reason it's wrong.
- "correct_notes" must have EXACTLY one key per target line, as its string index \
("0", "1", "2", ...), mapped to a short reason that line belongs there.
- Output JSON only — no backticks, no extra text before or after the JSON object.
"""


def _post_to_groq(payload):
    response = requests.post(
        GROQ_API_URL,
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=20,
    )

    print("STATUS:", response.status_code)

    if response.status_code != 200:
        print(response.text)
        response.raise_for_status()

    data = response.json()
    return data["choices"][0]["message"]["content"]


def _call_groq(prompt, max_tokens=1200):
    if not GROQ_API_KEY:
        return None

    payload = {
        "model": GROQ_MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
        "max_tokens": max_tokens,
    }

    try:
        return _post_to_groq(payload)
    except Exception as e:
        print("GROQ ERROR:", e)

        if hasattr(e, "read"):
            try:
                print(e.read().decode("utf-8"))
            except:
                pass

        return None


def _extract_json(text):
    """Parse the model's reply into a dict, tolerating stray fences/text."""
    if not text:
        return None
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            return None


def _validate_and_normalize(data):
    """Returns a clean problem dict, or None if anything looks off."""
    if not isinstance(data, dict):
        return None

    target        = data.get("target")
    distractors   = data.get("distractors")
    explanations  = data.get("explanations")
    correct_notes = data.get("correct_notes")
    name          = data.get("name") or "Generated Problem"
    description   = data.get("description") or ""

    if not (isinstance(target, list) and 2 <= len(target) <= 12
            and all(isinstance(t, str) and t.strip() for t in target)):
        return None
    if not (isinstance(distractors, list) and len(distractors) >= 3
            and all(isinstance(d, str) and d.strip() for d in distractors)):
        return None
    if set(target) & set(distractors):
        return None
    if not isinstance(explanations, dict) or not isinstance(correct_notes, dict):
        return None
    if any(d not in explanations for d in distractors):
        return None

    notes = {}
    for k, v in correct_notes.items():
        try:
            notes[int(k)] = str(v)
        except (ValueError, TypeError):
            continue
    if not notes:
        return None

    return {
        "name":          str(name)[:60],
        "description":   str(description)[:160],
        "target":        list(target),
        "distractors":   list(distractors),
        "explanations":  {d: str(explanations[d]) for d in distractors},
        "correct_notes": notes,
    }


def generate_problem(topic=None, attempts=2):
    """
    Ask Groq for a brand-new problem.

    Returns a problem dict matching the schema used throughout the
    game (target/distractors/explanations/correct_notes/name/
    description), or None if Groq is unconfigured/unreachable or kept
    returning something unusable after `attempts` tries.
    """
    print("GROQ_API_KEY loaded:", bool(GROQ_API_KEY))
    print("Using model:", GROQ_MODEL)
    if not GROQ_API_KEY:
        return None

    topic  = topic or random.choice(TOPICS)
    prompt = _SCHEMA_PROMPT.format(topic=topic)

    for _ in range(attempts):
        raw = _call_groq(prompt)
        problem = _validate_and_normalize(_extract_json(raw))
        if problem:
            return problem
    return None