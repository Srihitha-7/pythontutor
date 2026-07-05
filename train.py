"""
train.py — trains the learner-model DQN that decides hint levels.

The agent's STATE is a 5-feature snapshot of a learner's behaviour
(success_rate, mistakes, hints_used, time_spent, progress) and its
ACTION is which hint level to give next: none / weak / medium /
strong (config.HINT_LEVELS). There is no navigation, grid, or snake
involved in training — none of that is learned behaviour any more,
it's just a UI affordance for picking a snippet.

The agent trains against a simulated-learner environment
(learner_env.py) so a usable policy exists before any real learner
data is collected. The resulting weights are loaded by hint_policy.py
to drive live, adaptive hinting in game_visual.py.

Metrics recorded per episode
─────────────────────────────
  • total_reward
  • success_rate   — fraction of attempts that were correct
  • completed      — whether the simulated learner finished the problem
  • epsilon

A CSV log is written to metrics.csv for offline analysis.
"""

import csv
from collections import deque

import torch

from learner_env import SimulatedLearner
from dqn_agent import DQNAgent
from config import (
    LEARNER_STATE_SIZE, HINT_ACTION_SIZE,
    EPISODES, BATCH_SIZE, GAMMA, LR,
    EPSILON_START, EPSILON_MIN, EPSILON_DECAY,
    HINT_POLICY_WEIGHTS,
)

# ── Hyper-parameters ──────────────────────────────────────────────────────
PRINT_EVERY        = 10     # console summary interval (episodes)
LEARN_EVERY         = 2      # gradient step every N env steps
TARGET_UPDATE_FREQ  = 100    # hard target-network sync every N learn() calls
MEMORY_CAPACITY     = 10_000
WINDOW               = 50    # rolling-average window size

# ── Initialise ────────────────────────────────────────────────────────────
agent = DQNAgent(
    state_size=LEARNER_STATE_SIZE,
    action_size=HINT_ACTION_SIZE,
    lr=LR,
    gamma=GAMMA,
    memory_capacity=MEMORY_CAPACITY,
    target_update_freq=TARGET_UPDATE_FREQ,
)

epsilon = EPSILON_START

# ── Metrics containers ───────────────────────────────────────────────────
reward_window  = deque(maxlen=WINDOW)
success_window = deque(maxlen=WINDOW)

best_reward  = float("-inf")
completions  = 0

csv_path   = "metrics.csv"
csv_file   = open(csv_path, "w", newline="")
csv_writer = csv.writer(csv_file)
csv_writer.writerow(["episode", "total_reward", "success_rate", "completed", "epsilon"])

# ── Training loop ────────────────────────────────────────────────────────
for episode in range(1, EPISODES + 1):
    learner      = SimulatedLearner()
    state        = learner.reset()
    total_reward = 0.0
    step         = 0

    while True:
        action = agent.act(state, epsilon)
        next_state, reward, done = learner.step(action)
        agent.remember(state, action, reward, next_state, done)

        state         = next_state
        total_reward += reward
        step         += 1

        if step % LEARN_EVERY == 0:
            agent.learn(batch_size=BATCH_SIZE)

        if done:
            break

    epsilon = max(EPSILON_MIN, epsilon * EPSILON_DECAY)

    success_rate = learner._success_rate()
    completed    = learner.line_idx >= learner.n_lines
    completions += int(completed)

    reward_window.append(total_reward)
    success_window.append(success_rate)
    best_reward = max(best_reward, total_reward)

    csv_writer.writerow([episode, f"{total_reward:.3f}", f"{success_rate:.3f}",
                          int(completed), f"{epsilon:.4f}"])
    csv_file.flush()

    if episode % PRINT_EVERY == 0:
        avg_r = sum(reward_window)  / len(reward_window)
        avg_s = sum(success_window) / len(success_window)
        print(
            f"Ep {episode:>4}/{EPISODES} | "
            f"AvgReward({WINDOW}): {avg_r:>7.2f} | "
            f"AvgSuccessRate({WINDOW}): {avg_s:6.1%} | "
            f"Completed: {completions}/{episode} | "
            f"ε: {epsilon:.3f} | BestReward: {best_reward:.2f}"
        )

csv_file.close()
torch.save(agent.model.state_dict(), HINT_POLICY_WEIGHTS)

# ── Final summary ────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("Training complete")
print(f"  Episodes         : {EPISODES}")
print(f"  Completion rate  : {completions / EPISODES:.1%}")
print(f"  Best reward      : {best_reward:.2f}")
print(f"  Final epsilon    : {epsilon:.4f}")
print(f"  Policy weights   : {HINT_POLICY_WEIGHTS}")
print(f"  Metrics saved    : {csv_path}")
print("=" * 60)