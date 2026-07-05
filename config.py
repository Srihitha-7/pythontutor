import os

# ── Puzzle board (visual layout only — not used for any learning/training) ──
GRID_SIZE = 10
CELL_SIZE = 100
WIDTH = GRID_SIZE * CELL_SIZE
HEIGHT = GRID_SIZE * CELL_SIZE

# ── Hint levels the learner-model DQN can choose between ────────────────────
HINT_LEVELS = ["none", "weak", "medium", "strong"]

# ── Learner-model DQN ─────────────────────────────────────────────────────
# State  = [success_rate, mistakes, hints_used, time_spent, progress]  (5 features)
# Action = index into HINT_LEVELS                                     (4 actions)
LEARNER_STATE_SIZE = 5
HINT_ACTION_SIZE    = len(HINT_LEVELS)

EPISODES   = 500
BATCH_SIZE = 64
GAMMA      = 0.99
LR         = 0.001

EPSILON_START = 1.0
EPSILON_MIN   = 0.05
EPSILON_DECAY = 0.995

DEVICE = "cpu"

HINT_POLICY_WEIGHTS = "hint_policy.pt"

# ── Groq — generates the actual hint *text* once the DQN has chosen a level ──
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL   = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"

# ── Supabase — shared cloud storage so questionnaire responses from every
#    laptop land in one place, instead of a separate CSV per machine.
#    Fill these in (or set the matching env vars) once, then copy the whole
#    project folder to every laptop — they'll all write to the same tables.
#    Project Settings → API in your Supabase dashboard gives you both values.
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")            # e.g. "https://xxxx.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")            # the "anon" public API key
