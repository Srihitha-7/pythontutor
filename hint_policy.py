"""
hint_policy.py — bridges the trained learner-model DQN to live gameplay.

Pipeline for every hint request:
  1. Build a 5-feature state vector from the learner's REAL metrics
     (success_rate, mistakes, hints_used, time_spent, progress).
  2. Ask the trained DQN which hint LEVEL fits: none / weak / medium /
     strong (config.HINT_LEVELS).
  3. If a hint is warranted (anything but "none"), call Groq to phrase
     the actual hint text at that level of directness, given the
     correct line + why it's correct (and the learner's last wrong
     pick, if any, for extra context).

If no trained weights are found, the DQN falls back to a freshly
initialised network (still produces an action, just not a learned
one) — run train.py first for a real policy. If GROQ_API_KEY isn't
set, generate_hint_text() falls back to a simple templated hint so
the game still works without a Groq account.
"""

import os
import json
import urllib.request
import urllib.error

import torch

from config import (
    HINT_LEVELS, LEARNER_STATE_SIZE, HINT_ACTION_SIZE,
    HINT_POLICY_WEIGHTS, GROQ_API_KEY, GROQ_MODEL, GROQ_API_URL,
)
from dqn_agent import DQNAgent

_agent = None


# ── DQN loading / inference ─────────────────────────────────────────────
def load_agent(weights_path=HINT_POLICY_WEIGHTS):
    """Load (or lazily create) the hint-level policy network."""
    global _agent
    agent = DQNAgent(state_size=LEARNER_STATE_SIZE, action_size=HINT_ACTION_SIZE)
    if os.path.exists(weights_path):
        agent.model.load_state_dict(torch.load(weights_path, map_location="cpu"))
        agent.model.eval()
    _agent = agent
    return agent


def build_state(success_rate, mistakes, hints_used, time_spent, progress):
    """Normalise raw learner metrics into the DQN's expected state vector."""
    return [
        max(0.0, min(1.0, success_rate)),
        max(0.0, min(1.0, mistakes / 3)),
        max(0.0, min(1.0, hints_used / 5)),
        max(0.0, min(1.0, time_spent / 30.0)),
        max(0.0, min(1.0, progress)),
    ]


def predict_hint_level(metrics):
    """
    metrics: dict with keys success_rate, mistakes, hints_used,
             time_spent, progress (see game.CodeBuilderGame.get_metrics()).
    Returns one of config.HINT_LEVELS.
    """
    global _agent
    if _agent is None:
        load_agent()
    state = build_state(**metrics)
    import torch

    state_t = torch.FloatTensor(state).unsqueeze(0)

    with torch.no_grad():
        q = _agent.model(state_t)

    print("STATE:", state)
    print("Q VALUES:", q.numpy())

    action = torch.argmax(q, dim=1).item()
    # action = _agent.act(state, epsilon=0.0)   # greedy — no exploration at play time
    print("\n========== DQN DEBUG ==========")
    print("Metrics:", metrics)
    print("Chosen Hint Level:", HINT_LEVELS[action])
    print("===============================\n")
    return HINT_LEVELS[action]


# ── Hint-text generation via Groq ───────────────────────────────────────
_STYLE_INSTRUCTIONS = {
    "weak": (
        "Give a very subtle nudge. Do NOT reveal the line or its exact "
        "structure — ask a guiding question or point at the *concept* only."
    ),
    "medium": (
        "Give a moderately direct hint. You may describe what the "
        "correct line should *do*, without writing the exact code."
    ),
    "strong": (
        "Be direct: reveal the correct line of code, with one short "
        "sentence on why it's correct."
    ),
}


def generate_hint_text(level, correct_line, why_correct,
                        wrong_line=None, wrong_reason=None, problem_name=""):
    """
    Returns hint text appropriate to `level` ("weak"/"medium"/"strong").
    Returns None if level == "none" (no hint should be shown at all).
    """
    if level == "none":
        return None

    if not GROQ_API_KEY:
        return _fallback_hint(level, correct_line, why_correct)

    prompt = (
        f"You are a patient, encouraging coding tutor helping a learner "
        f"with the exercise '{problem_name}'.\n"
        f"The correct next line is: {correct_line!r}\n"
        f"Why it's correct: {why_correct}\n"
    )
    if wrong_line:
        prompt += f"The learner just tried: {wrong_line!r} ({wrong_reason}).\n"
    prompt += (
        f"\nInstruction: {_STYLE_INSTRUCTIONS[level]}\n"
        f"Respond with 1-2 short, warm sentences. No preamble, no markdown."
    )

    try:
        body = json.dumps({
            "model": GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.7,
            "max_tokens": 120,
        }).encode("utf-8")
        req = urllib.request.Request(
            GROQ_API_URL,
            data=body,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()
    except (urllib.error.URLError, KeyError, IndexError, ValueError, TimeoutError):
        return _fallback_hint(level, correct_line, why_correct)


def _fallback_hint(level, correct_line, why_correct):
    """Used when Groq is unreachable/unconfigured, so the game still works."""
    if level == "weak":
        return "Think about what needs to happen at this step — what's the purpose of this line?"
    if level == "medium":
        return f"This line needs to: {why_correct}" if why_correct else "Look closely at what the previous line set up."
    return f"Try: {correct_line.strip()}" + (f"  —  {why_correct}" if why_correct else "")