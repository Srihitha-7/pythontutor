"""
game.py — headless puzzle engine for the adaptive code-builder game.

This module owns ONLY the pedagogical logic: which snippet is correct
next, session/run statistics, and the 5-feature learner-state vector
consumed by the hint-level policy (hint_policy.py). It has no UI and
no grid/navigation concept of its own — any front end (pygame, web,
CLI...) drives it by calling `attempt()` with the text of whichever
snippet the learner picked. game_visual.py is the pygame front end;
it owns the snake/grid purely as a UI affordance for picking a
snippet, not as something an agent navigates.

Wrong picks never end a run — the learner can always keep trying.
Only a successful run (or an explicit reset) ends it.
"""

import time

import snippets as snip_mod


class CodeBuilderGame:
    def __init__(self, problem_idx=0):
        # Session-wide stats — persist across resets, only re-zeroed
        # by the front end if it explicitly wants a fresh session.
        self.session_attempts  = 0
        self.session_correct   = 0
        self.session_completed = 0
        self.session_runs      = 0

        self.load_problem(problem_idx)
        self.reset()

    # ── Problem selection ────────────────────────────────────────────────
    def load_problem(self, idx):
        self.problem_idx   = idx % snip_mod.problem_count()
        p = snip_mod.get_problem(self.problem_idx)
        self.target_code   = p["target"]
        self.all_snippets  = p["target"] + p["distractors"]
        self.explanations  = p["explanations"]
        self.correct_notes = p["correct_notes"]
        self.problem_name  = p["name"]
        self.description   = p["description"]

    def select_problem(self, idx):
        self.load_problem(idx)
        self.reset()

    def next_problem(self):
        self.select_problem(self.problem_idx + 1)

    def prev_problem(self):
        self.select_problem(self.problem_idx - 1)

    # ── Reset (start a fresh run on the current problem) ───────────────────
    def reset(self):
        self.expected_idx = 0
        self.done          = False
        self.score         = 0

        # Per-line metrics — these feed the hint-level policy
        self.line_mistakes = 0
        self.line_hints    = 0
        self.line_started  = time.time()

        # Per-run aggregate (shown on the completion screen)
        self.run_hints_used = 0

        self.session_runs += 1
        return self.get_metrics()

    # ── Attempt a pick ───────────────────────────────────────────────────
    def attempt(self, picked_text):
        """
        picked_text: the literal snippet string the learner selected.
        Returns a dict describing the outcome. The run is NEVER ended
        by a wrong pick — only by completing the problem.
        """
        if self.done:
            return {"correct": False, "done": True, "picked": picked_text,
                     "message": "This run is already complete — restart to play again."}

        self.session_attempts += 1
        is_correct = (picked_text == self.target_code[self.expected_idx])
        result = {"correct": is_correct, "done": False, "picked": picked_text}

        if is_correct:
            self.session_correct += 1
            result["note"] = self.correct_notes.get(self.expected_idx, "")
            self.expected_idx += 1
            self.score        += 1

            # Reset per-line tracking for the next line
            self.line_mistakes = 0
            self.line_hints    = 0
            self.line_started  = time.time()

            if self.expected_idx >= len(self.target_code):
                self.done = True
                self.session_completed += 1
                result["done"] = True
        else:
            self.line_mistakes += 1
            result["reason"] = self.explanations.get(
                picked_text,
                "That line doesn't fit here — think about what should happen at this step."
            )

        return result

    # ── Hint bookkeeping ─────────────────────────────────────────────────
    def register_hint(self):
        """Call once a hint has actually been shown to the learner."""
        self.line_hints    += 1
        self.run_hints_used += 1

    def correct_line_info(self):
        """The line the learner currently needs, plus why it's correct."""
        if self.expected_idx >= len(self.target_code):
            return None, ""
        return (self.target_code[self.expected_idx],
                self.correct_notes.get(self.expected_idx, ""))

    # ── Metrics for the learner-model DQN ─────────────────────────────────
    def success_rate(self):
        if self.session_attempts == 0:
            return 1.0
        return self.session_correct / self.session_attempts

    def progress(self):
        return self.expected_idx / max(len(self.target_code), 1)

    def time_on_line(self):
        return time.time() - self.line_started

    def get_metrics(self):
        """5-feature state for hint_policy.predict_hint_level()."""
        return {
            "success_rate": self.success_rate(),
            "mistakes":     self.line_mistakes,
            "hints_used":   self.line_hints,
            "time_spent":   self.time_on_line(),
            "progress":     self.progress(),
        }

    def completion_stats(self):
        """Session-wide stats shown in the sidebar / completion overlay."""
        return {
            "runs":          self.session_runs,
            "completed":     self.session_completed,
            "success_rate":  self.success_rate(),
            "attempts":      self.session_attempts,
            "correct":       self.session_correct,
        }