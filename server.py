"""
server.py — web backend for AdaptCode.

Replicates the pygame game's mechanics (game_visual.py: spawn_snippets,
step, use_hint, reset) as a session-based HTTP API instead of a local
pygame window, so students can play from any browser via one shared URL.

Session state lives in memory, keyed by a session_id the browser
generates and keeps in localStorage. If the server process restarts
(e.g. Render free-tier idling), in-progress sessions are lost — the
frontend simply starts a new session automatically in that case.
Questionnaire responses go straight from the browser to Supabase, so
those are NOT affected by server restarts.
"""

import random
import uuid
from typing import Dict, Optional

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import snippets as snip_mod
import hint_policy
import config
from game import CodeBuilderGame
from problem_generator import generate_problem

GRID_SIZE = 10  # matches config.GRID_SIZE — kept fixed for the web board

app = FastAPI(title="AdaptCode Web")

# session_id -> state dict
SESSIONS: Dict[str, dict] = {}

# Hint policy: lazily loads trained weights (or a fresh net if train.py
# hasn't been run yet — see hint_policy.load_agent).
hint_policy.load_agent()


# ── Session state helpers (mirrors game_visual.SnakeGameVisual) ────────────
def _spawn_snippets(state, engine):
    snippets = {}
    pos_of = {}
    used = set(state["snake"])
    indices = list(range(len(engine.all_snippets)))
    random.shuffle(indices)
    for i in indices:
        while True:
            pos = (random.randint(0, GRID_SIZE - 1), random.randint(0, GRID_SIZE - 1))
            if pos not in used:
                snippets[pos] = i
                pos_of[i] = pos
                used.add(pos)
                break
    state["snippets"] = snippets
    state["_pos_of"] = pos_of


def _new_state(problem_idx=0) -> dict:
    engine = CodeBuilderGame(problem_idx=problem_idx)
    state = {
        "engine": engine,
        "snake": [(5, 5)],
        "facing": (1, 0),
        "game_state": "playing",
        "hint_active": False, "hint_level": None, "hint_text": "",
        "suggested_level": None,
        "fb_msg": "", "fb_detail": "",
        "wrong_msg": "", "wrong_detail": "", "wrong_active": False,
        "_last_wrong_text": None, "_last_wrong_reason": None,
    }
    _spawn_snippets(state, engine)
    return state


def _reset_state(state: dict, problem_idx: Optional[int] = None):
    engine = state["engine"]
    if problem_idx is not None:
        engine.select_problem(problem_idx)
    else:
        engine.reset()
    state["snake"] = [(5, 5)]
    state["facing"] = (1, 0)
    state["game_state"] = "playing"
    state["hint_active"] = False
    state["hint_level"] = None
    state["hint_text"] = ""
    state["suggested_level"] = None
    state["fb_msg"] = ""
    state["fb_detail"] = ""
    state["wrong_msg"] = ""
    state["wrong_detail"] = ""
    state["wrong_active"] = False
    state["_last_wrong_text"] = None
    state["_last_wrong_reason"] = None
    _spawn_snippets(state, engine)


def _do_move(state: dict, action: int):
    engine = state["engine"]
    if state["game_state"] != "playing":
        return

    state["hint_active"] = False
    state["wrong_active"] = False

    x, y = state["snake"][0]
    if action == 0:
        x -= 1; state["facing"] = (-1, 0)
    elif action == 1:
        x += 1; state["facing"] = (1, 0)
    elif action == 2:
        y -= 1; state["facing"] = (0, -1)
    elif action == 3:
        y += 1; state["facing"] = (0, 1)

    x = max(0, min(GRID_SIZE - 1, x))
    y = max(0, min(GRID_SIZE - 1, y))
    new_head = (x, y)

    if new_head in state["snippets"]:
        idx = state["snippets"][new_head]
        picked_text = engine.all_snippets[idx]
        result = engine.attempt(picked_text)

        if result["correct"]:
            state["fb_msg"] = f"✓ {picked_text}"
            state["fb_detail"] = result.get("note", "")
            state["suggested_level"] = None
            del state["snippets"][new_head]
            del state["_pos_of"][idx]
            state["snake"].insert(0, new_head)

            if result["done"]:
                state["game_state"] = "complete"
        else:
            state["_last_wrong_text"] = picked_text
            state["_last_wrong_reason"] = result["reason"]
            state["wrong_msg"] = f"✗ Wrong: {picked_text}"
            state["wrong_detail"] = result["reason"]
            state["wrong_active"] = True
            state["suggested_level"] = hint_policy.predict_hint_level(engine.get_metrics())
            state["snake"].insert(0, new_head)
            state["snake"].pop()
    else:
        state["snake"].insert(0, new_head)
        state["snake"].pop()


def _do_hint(state: dict):
    engine = state["engine"]
    if state["game_state"] != "playing" or engine.done:
        return

    metrics = engine.get_metrics()
    level = hint_policy.predict_hint_level(metrics)

    if level == "none":
        state["hint_active"] = False
        state["fb_msg"] = "You've got this — try once more before asking for a hint!"
        state["fb_detail"] = ""
        return

    correct_line, why = engine.correct_line_info()
    text = hint_policy.generate_hint_text(
        level, correct_line, why,
        wrong_line=state["_last_wrong_text"],
        wrong_reason=state["_last_wrong_reason"],
        problem_name=engine.problem_name,
    )
    engine.register_hint()
    state["hint_level"] = level
    state["hint_text"] = text
    state["hint_active"] = True


def _problems_list():
    return [{"idx": i, "name": p["name"], "description": p["description"]}
            for i, p in enumerate(snip_mod.PROBLEMS)]


def _serialize(state: dict) -> dict:
    engine = state["engine"]
    return {
        "problem_idx": engine.problem_idx,
        "problem_name": engine.problem_name,
        "description": engine.description,
        "grid_size": GRID_SIZE,
        "snake": state["snake"],
        "facing": state["facing"],
        "snippets": {f"{x},{y}": engine.all_snippets[idx]
                     for (x, y), idx in state["snippets"].items()},
        "collected": engine.target_code[:engine.expected_idx],
        "total_lines": len(engine.target_code),
        "expected_idx": engine.expected_idx,
        "game_state": state["game_state"],
        "hint_active": state["hint_active"],
        "hint_level": state["hint_level"],
        "hint_text": state["hint_text"],
        "suggested_level": state["suggested_level"],
        "fb_msg": state["fb_msg"],
        "fb_detail": state["fb_detail"],
        "wrong_msg": state["wrong_msg"],
        "wrong_detail": state["wrong_detail"],
        "wrong_active": state["wrong_active"],
        "stats": engine.completion_stats(),
        "run_hints_used": engine.run_hints_used,
        "problems": _problems_list(),
    }


def _get_state(session_id: str) -> dict:
    state = SESSIONS.get(session_id)
    if state is None:
        raise HTTPException(
            status_code=404,
            detail="Session not found or expired — start a new session.")
    return state


# ── Request bodies ──────────────────────────────────────────────────────
class MoveBody(BaseModel):
    action: int   # 0=left 1=right 2=up 3=down


class GenerateBody(BaseModel):
    topic: str


# ── Routes ───────────────────────────────────────────────────────────────
@app.post("/api/session")
def create_session():
    session_id = str(uuid.uuid4())
    state = _new_state(0)
    SESSIONS[session_id] = state
    return {"session_id": session_id, **_serialize(state)}


@app.get("/api/{session_id}/state")
def get_state(session_id: str):
    return _serialize(_get_state(session_id))


@app.post("/api/{session_id}/move")
def move(session_id: str, body: MoveBody):
    state = _get_state(session_id)
    _do_move(state, body.action)
    return _serialize(state)


@app.post("/api/{session_id}/hint")
def hint(session_id: str):
    state = _get_state(session_id)
    _do_hint(state)
    return _serialize(state)


@app.post("/api/{session_id}/reset")
def reset(session_id: str):
    state = _get_state(session_id)
    _reset_state(state)
    return _serialize(state)


@app.post("/api/{session_id}/select/{idx}")
def select_problem(session_id: str, idx: int):
    state = _get_state(session_id)
    _reset_state(state, problem_idx=idx)
    return _serialize(state)


@app.post("/api/{session_id}/generate")
def generate(session_id: str, body: GenerateBody):
    state = _get_state(session_id)
    topic = body.topic.strip()
    if not topic:
        raise HTTPException(400, "Topic can't be empty.")

    problem = generate_problem(topic)
    if not problem:
        return {"ok": False, "error": "Problem generation failed "
                                       "(check GROQ_API_KEY on the server).",
                **_serialize(state)}

    snip_mod.PROBLEMS.append(problem)
    _reset_state(state, problem_idx=len(snip_mod.PROBLEMS) - 1)
    return {"ok": True, **_serialize(state)}


@app.get("/api/config")
def get_config():
    """Frontend fetches this once on load to know where to POST
    questionnaire responses. The Supabase anon key is meant to be
    public — access is controlled by Row Level Security policies on
    the Supabase side, not by hiding this key."""
    return {
        "supabase_url": config.SUPABASE_URL,
        "supabase_anon_key": config.SUPABASE_KEY,
    }


# Serve the frontend last, so it doesn't shadow the /api/* routes above.
app.mount("/", StaticFiles(directory="static", html=True), name="static")
