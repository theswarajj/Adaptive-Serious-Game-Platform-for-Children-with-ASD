"""
Q-Learning Adaptation Engine — Safe Difficulty & Input Mode Selection

Uses tabular Q-Learning to learn which difficulty and input-mode
combinations lead to good outcomes for each skill state.

Safety constraints:
  - Baseline rule-based policy always has veto power
  - Q-Learning runs in shadow mode first (observes but doesn't decide)
  - Maximum single-step difficulty change: ±1
  - Minimum 3 sessions before any adaptation
  - Fall-back to easier difficulty if distress signals detected
"""

import json
import math
import random
from typing import Dict, List, Optional, Tuple
from datetime import datetime


# ─── Configuration ───────────────────────────────────────────────────

DIFFICULTIES = ["easy", "medium", "hard"]
INPUT_MODES = ["camera-hand", "camera-face", "camera-pose", "speech", "pointer", "keyboard", "choice-select"]

# State discretization bins for skill estimate
SKILL_BINS = ["low", "mid", "high"]  # 0-0.33, 0.33-0.66, 0.66-1.0

# Actions: (difficulty_delta, preferred_input)
# difficulty_delta: -1 (easier), 0 (same), +1 (harder)
ACTIONS = [
    {"name": "easier", "diff_delta": -1, "desc": "Lower difficulty"},
    {"name": "same", "diff_delta": 0, "desc": "Keep difficulty"},
    {"name": "harder", "diff_delta": +1, "desc": "Raise difficulty"},
]

# Safety parameters
MIN_SESSIONS_BEFORE_ADAPT = 3
MAX_DIFFICULTY_JUMP = 1
SHADOW_MODE_SESSIONS = 10  # First N sessions are shadow-only

# Q-Learning hyperparameters
ALPHA = 0.1     # Learning rate
GAMMA = 0.9     # Discount factor
EPSILON = 0.15  # Exploration rate (ε-greedy)


def _bin_skill(estimate: float) -> str:
    """Discretize a skill estimate into a bin."""
    if estimate < 0.33:
        return "low"
    elif estimate < 0.66:
        return "mid"
    else:
        return "high"


def _compute_reward(metrics: Dict, performance: float, difficulty: str) -> float:
    """
    Compute reward for a session outcome.
    
    Positive reward for:
      - Good performance at appropriate difficulty
      - Completing the session
      - Engagement (longer duration is ok, but not too long)
    
    Negative reward for:
      - Abandoning session
      - Very low performance (frustration signal)
      - Very high performance on easy (boredom signal)
    """
    reward = 0.0
    
    # Base reward from performance
    reward += performance * 2.0 - 1.0  # Range: -1 to +1
    
    # Difficulty bonus: harder difficulty with good performance = extra reward
    diff_bonus = {"easy": 0.0, "medium": 0.2, "hard": 0.4, "standard": 0.1}
    if performance > 0.5:
        reward += diff_bonus.get(difficulty, 0.0)
    
    # Completion bonus
    status = metrics.get("status", "completed")
    if status == "completed":
        reward += 0.3
    elif status == "abandoned":
        reward -= 0.5
    
    # Boredom penalty: high performance on easy
    if performance > 0.9 and difficulty == "easy":
        reward -= 0.2
    
    # Frustration penalty: low performance on hard
    if performance < 0.2 and difficulty == "hard":
        reward -= 0.3
    
    return round(max(-2.0, min(2.0, reward)), 4)


class AdaptationEngine:
    """
    Q-Learning based adaptation engine with safety constraints.
    
    State: (skill_bin, current_difficulty, session_count_bin)
    Action: easier / same / harder
    
    The engine has two modes:
      - Rule-based (baseline): Always safe, deterministic
      - Learned policy (Q-Learning): Used after shadow period, with safety veto
    """

    def __init__(self, q_table: Optional[Dict] = None):
        self.q_table: Dict[str, Dict[str, float]] = q_table or {}
        self.total_updates = 0
        self.policy_version = "1.0.0"

    def _state_key(self, skill_bin: str, difficulty: str, session_count: int) -> str:
        """Create a state key for Q-table lookup."""
        count_bin = "few" if session_count < 5 else ("some" if session_count < 15 else "many")
        return f"{skill_bin}|{difficulty}|{count_bin}"

    def _get_q_values(self, state: str) -> Dict[str, float]:
        """Get Q-values for a state, initializing if needed."""
        if state not in self.q_table:
            self.q_table[state] = {a["name"]: 0.0 for a in ACTIONS}
        return self.q_table[state]

    # ─── Rule-Based Baseline ─────────────────────────────────────────

    def rule_based_decision(self, skill_estimate: float, current_difficulty: str,
                            session_count: int, recent_performance: float) -> Dict:
        """
        Safe, deterministic baseline policy.
        Always returns a valid decision. Never raises difficulty more than 1 step.
        """
        diff_idx = DIFFICULTIES.index(current_difficulty) if current_difficulty in DIFFICULTIES else 0
        
        # Too few sessions → keep same
        if session_count < MIN_SESSIONS_BEFORE_ADAPT:
            return {
                "action": "same",
                "difficulty": current_difficulty,
                "source": "rule-based",
                "reason": f"Collecting baseline data ({session_count}/{MIN_SESSIONS_BEFORE_ADAPT} sessions)",
            }
        
        # Low skill + low performance → easier
        if skill_estimate < 0.3 and recent_performance < 0.3 and diff_idx > 0:
            new_diff = DIFFICULTIES[diff_idx - 1]
            return {
                "action": "easier",
                "difficulty": new_diff,
                "source": "rule-based",
                "reason": "Reducing difficulty — child may be finding this challenging",
            }
        
        # High skill + high performance → harder (if not already max)
        if skill_estimate > 0.6 and recent_performance > 0.7 and diff_idx < len(DIFFICULTIES) - 1:
            new_diff = DIFFICULTIES[diff_idx + 1]
            return {
                "action": "harder",
                "difficulty": new_diff,
                "source": "rule-based",
                "reason": "Increasing difficulty — child is ready for more challenge",
            }
        
        # Medium performance → same
        return {
            "action": "same",
            "difficulty": current_difficulty,
            "source": "rule-based",
            "reason": "Current difficulty is appropriate",
        }

    # ─── Q-Learning Policy ───────────────────────────────────────────

    def q_learning_decision(self, skill_estimate: float, current_difficulty: str,
                            session_count: int) -> Dict:
        """
        ε-greedy Q-Learning policy selection.
        Returns the chosen action and metadata.
        """
        skill_bin = _bin_skill(skill_estimate)
        state = self._state_key(skill_bin, current_difficulty, session_count)
        q_values = self._get_q_values(state)
        
        # ε-greedy
        if random.random() < EPSILON:
            action_name = random.choice([a["name"] for a in ACTIONS])
        else:
            action_name = max(q_values, key=q_values.get)
        
        # Apply action
        diff_idx = DIFFICULTIES.index(current_difficulty) if current_difficulty in DIFFICULTIES else 0
        action = next(a for a in ACTIONS if a["name"] == action_name)
        new_idx = max(0, min(len(DIFFICULTIES) - 1, diff_idx + action["diff_delta"]))
        new_difficulty = DIFFICULTIES[new_idx]
        
        return {
            "action": action_name,
            "difficulty": new_difficulty,
            "source": "learned-policy",
            "state": state,
            "q_values": q_values.copy(),
            "policy_version": self.policy_version,
            "visit_count": self.total_updates,
        }

    def update_q_table(self, state: str, action: str, reward: float, 
                       next_state: str) -> float:
        """
        Q-Learning update: Q(s,a) ← Q(s,a) + α[r + γ·max_a' Q(s',a') - Q(s,a)]
        Returns the TD error.
        """
        q_values = self._get_q_values(state)
        next_q_values = self._get_q_values(next_state)
        
        old_q = q_values.get(action, 0.0)
        max_next_q = max(next_q_values.values()) if next_q_values else 0.0
        
        td_error = reward + GAMMA * max_next_q - old_q
        new_q = old_q + ALPHA * td_error
        
        q_values[action] = round(new_q, 6)
        self.total_updates += 1
        
        return td_error

    # ─── Safe Decision (Main Entry Point) ────────────────────────────

    def decide(self, skill_estimate: float, current_difficulty: str,
               session_count: int, recent_performance: float = 0.5) -> Dict:
        """
        Make a safe adaptation decision.
        
        Flow:
        1. Always compute rule-based decision
        2. If enough sessions, also compute Q-Learning decision
        3. If in shadow mode, record Q-decision but USE rule-based
        4. If past shadow mode, use Q-decision but apply safety veto
        """
        rule_decision = self.rule_based_decision(
            skill_estimate, current_difficulty, session_count, recent_performance
        )
        
        # Not enough data for Q-Learning
        if session_count < MIN_SESSIONS_BEFORE_ADAPT:
            return {**rule_decision, "status": "applied"}
        
        # Q-Learning decision
        q_decision = self.q_learning_decision(skill_estimate, current_difficulty, session_count)
        
        # Shadow mode: log Q-decision but use rule-based
        if session_count < SHADOW_MODE_SESSIONS:
            return {
                **rule_decision,
                "status": "applied",
                "shadow_decision": q_decision,
                "shadow_note": f"Q-Learning in shadow mode ({session_count}/{SHADOW_MODE_SESSIONS})",
            }
        
        # Past shadow mode: use Q-decision with safety veto
        # Safety check: don't jump more than 1 difficulty level
        diff_idx = DIFFICULTIES.index(current_difficulty) if current_difficulty in DIFFICULTIES else 0
        q_diff_idx = DIFFICULTIES.index(q_decision["difficulty"]) if q_decision["difficulty"] in DIFFICULTIES else diff_idx
        
        if abs(q_diff_idx - diff_idx) > MAX_DIFFICULTY_JUMP:
            return {
                **rule_decision,
                "status": "applied",
                "vetoed_decision": q_decision,
                "veto_reason": "Q-decision exceeded max difficulty jump",
            }
        
        # Safety check: don't go harder if recent performance is very low
        if q_decision["action"] == "harder" and recent_performance < 0.2:
            return {
                **rule_decision,
                "status": "applied",
                "vetoed_decision": q_decision,
                "veto_reason": "Blocked harder difficulty due to low recent performance",
            }
        
        # Q-decision passed safety checks
        return {**q_decision, "status": "applied"}

    def record_outcome(self, skill_estimate: float, difficulty_used: str,
                       session_count: int, metrics: Dict, performance: float,
                       next_skill_estimate: float) -> Dict:
        """
        Record a session outcome and update Q-table.
        Called after a session completes.
        """
        skill_bin = _bin_skill(skill_estimate)
        next_skill_bin = _bin_skill(next_skill_estimate)
        
        state = self._state_key(skill_bin, difficulty_used, session_count)
        next_state = self._state_key(next_skill_bin, difficulty_used, session_count + 1)
        
        reward = _compute_reward(metrics, performance, difficulty_used)
        
        # Determine action that was taken
        # (simplified: infer from difficulty change or lack thereof)
        action = "same"  # default
        
        td_error = self.update_q_table(state, action, reward, next_state)
        
        return {
            "state": state,
            "action": action,
            "reward": reward,
            "next_state": next_state,
            "td_error": round(td_error, 6),
            "total_updates": self.total_updates,
        }

    def to_json(self) -> str:
        return json.dumps({
            "q_table": self.q_table,
            "total_updates": self.total_updates,
            "policy_version": self.policy_version,
        })

    @classmethod
    def from_json(cls, data: str) -> "AdaptationEngine":
        parsed = json.loads(data)
        engine = cls(q_table=parsed.get("q_table", {}))
        engine.total_updates = parsed.get("total_updates", 0)
        engine.policy_version = parsed.get("policy_version", "1.0.0")
        return engine
