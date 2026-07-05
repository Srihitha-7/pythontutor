"""
learner_env.py — simulated learner used ONLY to train the hint-level
policy offline (see train.py).

This is deliberately NOT the real game. It is a lightweight student
model whose hidden 'ability' the policy can never observe directly —
exactly like a real learner. The policy only ever sees the same five
behavioural signals it will see in production (success_rate, mistakes,
hints_used, time_spent, progress), so a policy trained here transfers
directly to hint_policy.py for live play.

Design intent
─────────────
A good hint policy should:
  • give MORE help when a learner is genuinely stuck (many mistakes,
    long time-on-line, low recent success rate)
  • give LESS help when a learner is doing fine, to avoid spoon-feeding
    and protect their own problem-solving practice
  • ultimately maximise completion while minimising unnecessary
    hand-holding

That trade-off is encoded in the reward function below: correct
attempts are rewarded, hints stronger than what was actually needed
are mildly penalised, and getting stuck with no help is penalised
more the longer it persists.
"""

import random

from config import HINT_LEVELS

# How much each hint level boosts the learner's odds of a correct attempt
HINT_BOOST = {"none": 0.00, "weak": 0.15, "medium": 0.35, "strong": 0.65}
# Pedagogical "cost" of leaning on a stronger-than-needed hint
HINT_COST  = {"none": 0.00, "weak": 0.10, "medium": 0.30, "strong": 0.40}

MAX_MISTAKES_NORM = 3      # normalisation caps used to build the state vector
MAX_HINTS_NORM     = 5
MAX_TIME_NORM      = 30.0
MAX_ATTEMPTS_PER_EPISODE = 60   # safety cap so a low-ability run can't stall forever


class SimulatedLearner:
    """One simulated learner working through a multi-line problem."""

    def __init__(self, n_lines=None):
        # Hidden skill the policy never gets to see directly.
        self.ability = random.uniform(0.1, 0.95)
        self.n_lines = n_lines or random.randint(3, 6)
        self.reset()

    def reset(self):
        self.line_idx        = 0
        self.attempts_total   = 0
        self.correct_total    = 0
        self.mistakes_total   = 0
        self.hints_total      = 0
        self.line_mistakes    = 0
        self.line_time        = 0.0
        self.done             = False
        return self._state()

    # ── State helpers ────────────────────────────────────────────────────
    def _success_rate(self):
        if self.attempts_total == 0:
            return 1.0
        return self.correct_total / self.attempts_total

    def _state(self):
        return [
            self._success_rate(),
            min(self.line_mistakes / MAX_MISTAKES_NORM, 1.0),
            min(self.hints_total   / MAX_HINTS_NORM, 1.0),
            min(self.line_time     / MAX_TIME_NORM, 1.0),
            self.line_idx / self.n_lines,
        ]

    # ── Step ─────────────────────────────────────────────────────────────
    def step(self, hint_level_idx):
        """
        Apply the chosen hint level, simulate the learner's next attempt
        at the current line, and return (next_state, reward, done).
        """
        level = HINT_LEVELS[hint_level_idx]
        if level != "none":
            self.hints_total += 1

        p_correct = self.ability + HINT_BOOST[level] - 0.05 * self.line_mistakes
        p_correct = max(0.02, min(0.97, p_correct))

        self.attempts_total += 1
        self.line_time      += random.uniform(3, 9)   # seconds "spent" on this attempt
        correct               = random.random() < p_correct

        reward = 0.0

        if correct:
            self.correct_total += 1
            reward += 1.0
            reward -= HINT_COST[level]

            # Good learners should receive less help
            if self._success_rate() > 0.8:
                if level == "strong":
                    reward -= 1.5
                elif level == "weak":
                    reward += 0.5

            # Struggling learners benefit from stronger help
            if self._success_rate() < 0.4:
                if level == "strong":
                    reward += 1.0
                elif level == "none":
                    reward -= 1.0

            if level == "none":
                reward += 0.3

            self.line_idx += 1
            self.line_mistakes = 0
            self.line_time = 0.0

        else:
            self.mistakes_total += 1
            self.line_mistakes += 1
            reward -= 0.4

            if self.line_mistakes >= 3:
                if level == "none":
                    reward -= 1.0
                elif level == "weak":
                    reward -= 0.5
                elif level == "strong":
                    reward += 0.5

            if level == "none" and self.line_mistakes >= 2:
                reward -= 0.3

        if self.line_idx >= self.n_lines:
            self.done = True
            reward   += 2.0                      # completion bonus

        if self.attempts_total >= MAX_ATTEMPTS_PER_EPISODE:
            self.done = True

        return self._state(), reward, self.done