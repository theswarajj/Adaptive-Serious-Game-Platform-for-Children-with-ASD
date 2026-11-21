"""
Student Model — Skill Estimation & Progress Tracking
Computes per-skill estimates from session data using Bayesian-inspired updates.
"""

import json
import math
from typing import Dict, List, Optional, Tuple
from datetime import datetime


# ─── Skill Definitions ───────────────────────────────────────────────

SKILLS = {
    "attention": {"label": "Attention & Focus", "level": 1, "games": ["bubble-hunt", "follow-the-star", "pattern-trail", "object-quest"]},
    "motor": {"label": "Motor Control", "level": 1, "games": ["bubble-hunt", "pattern-trail", "copy-my-move"]},
    "emotion-recognition": {"label": "Emotion Recognition", "level": 2, "games": ["emotion-mirror", "body-says-it"]},
    "visual-processing": {"label": "Visual Processing", "level": 2, "games": ["object-quest", "emotion-mirror", "pattern-trail"]},
    "expressive-language": {"label": "Expressive Language", "level": 3, "games": ["talk-and-build", "describe-the-scene", "object-quest-see-say"]},
    "receptive-language": {"label": "Receptive Language", "level": 3, "games": ["talk-and-build", "object-quest-see-say", "describe-the-scene"]},
    "joint-attention": {"label": "Joint Attention", "level": 4, "games": ["look-point-share", "my-turn-your-turn"]},
    "turn-taking": {"label": "Turn Taking", "level": 4, "games": ["my-turn-your-turn", "talk-and-build"]},
    "imitation": {"label": "Imitation", "level": 4, "games": ["copy-my-move", "emotion-mirror"]},
    "social-reasoning": {"label": "Social Reasoning", "level": 5, "games": ["school-day-simulator", "community-travel-simulator", "shopping-adventure"]},
    "daily-living": {"label": "Daily Living Skills", "level": 5, "games": ["school-day-simulator", "community-travel-simulator", "shopping-adventure"]},
}

# Progress labels — describe practice history, NOT ability
PROGRESS_LABELS = [
    (0.0, 0.2, "Just started"),
    (0.2, 0.4, "Exploring"),
    (0.4, 0.6, "Practising"),
    (0.6, 0.8, "Growing"),
    (0.8, 1.0, "Confident"),
]


class StudentModel:
    """
    Maintains per-skill estimates for a single child.
    
    Each skill has:
      - estimate: float 0..1  (practice level, not ability score)
      - confidence: float 0..1 (how much data we have)
      - session_count: int
      - last_updated: ISO string
    
    Uses a simple exponential moving average with session-based updates.
    NOT a diagnostic tool. Labels describe practice history only.
    """

    def __init__(self, initial_data: Optional[Dict] = None):
        if initial_data:
            self.skills = initial_data
        else:
            self.skills = {}
            for skill_id, meta in SKILLS.items():
                self.skills[skill_id] = {
                    "estimate": 0.0,
                    "confidence": 0.0,
                    "session_count": 0,
                    "last_updated": None,
                    "label": meta["label"],
                    "level": meta["level"],
                }

    def update_from_session(self, game_id: str, metrics: Dict, difficulty: str = "easy") -> Dict[str, float]:
        """
        Update skill estimates after a game session.
        Returns dict of {skill_id: new_estimate} for changed skills.
        """
        changes = {}
        
        # Find which skills this game affects
        affected_skills = []
        for skill_id, meta in SKILLS.items():
            if game_id in meta["games"]:
                affected_skills.append(skill_id)
        
        if not affected_skills:
            return changes
        
        # Compute a normalized performance score from metrics (0..1)
        performance = self._compute_performance(game_id, metrics, difficulty)
        
        for skill_id in affected_skills:
            skill = self.skills[skill_id]
            old_estimate = skill["estimate"]
            
            # EMA update: weight new evidence more when we have less data
            n = skill["session_count"] + 1
            alpha = max(0.1, 1.0 / n)  # Learning rate decreases with more sessions
            
            # Difficulty multiplier: harder difficulty = more weight
            diff_mult = {"easy": 0.8, "medium": 1.0, "hard": 1.2, "standard": 1.0}.get(difficulty, 1.0)
            
            new_estimate = old_estimate + alpha * (performance * diff_mult - old_estimate)
            new_estimate = max(0.0, min(1.0, new_estimate))
            
            # Update confidence based on session count
            new_confidence = min(1.0, n * 0.15)
            
            skill["estimate"] = round(new_estimate, 4)
            skill["confidence"] = round(new_confidence, 4)
            skill["session_count"] = n
            skill["last_updated"] = datetime.utcnow().isoformat()
            
            changes[skill_id] = new_estimate
        
        return changes

    def _compute_performance(self, game_id: str, metrics: Dict, difficulty: str) -> float:
        """
        Normalize raw game metrics to a 0..1 performance score.
        Each game has its own metric mapping.
        """
        score = 0.5  # Default: middle-of-the-road
        
        # Try to extract meaningful metrics
        if "accuracy" in metrics or "accuracy_pct" in metrics:
            acc = metrics.get("accuracy", metrics.get("accuracy_pct", 50))
            if isinstance(acc, (int, float)):
                score = min(1.0, max(0.0, acc / 100.0))
        
        elif "score" in metrics:
            raw_score = metrics.get("score", 0)
            if isinstance(raw_score, (int, float)):
                # Normalize score — assume max ~50 for most games
                score = min(1.0, max(0.0, raw_score / 50.0))
        
        elif "completion_pct" in metrics:
            score = min(1.0, max(0.0, metrics["completion_pct"] / 100.0))
        
        # Bonus for completing without hints
        if metrics.get("hints_used", 0) == 0 and score > 0.3:
            score = min(1.0, score + 0.05)
        
        return score

    def get_progress_label(self, skill_id: str) -> str:
        """Get a human-friendly practice label for a skill."""
        if skill_id not in self.skills:
            return "Not started"
        
        estimate = self.skills[skill_id]["estimate"]
        for low, high, label in PROGRESS_LABELS:
            if low <= estimate < high:
                return label
        return "Confident"

    def get_level_readiness(self, level: int) -> Dict:
        """
        Assess readiness for a given level based on skills from previous levels.
        Returns {ready: bool, score: float, skills: [...]}
        """
        prev_skills = {sid: s for sid, s in self.skills.items() 
                       if SKILLS.get(sid, {}).get("level", 0) == level - 1}
        
        if not prev_skills:
            return {"ready": level <= 1, "score": 0.0, "skills": []}
        
        avg_estimate = sum(s["estimate"] for s in prev_skills.values()) / len(prev_skills)
        avg_confidence = sum(s["confidence"] for s in prev_skills.values()) / len(prev_skills)
        
        # Ready if average estimate >= 0.3 and at least 1 session per skill
        ready = avg_estimate >= 0.3 and avg_confidence >= 0.15
        
        skill_details = [
            {"id": sid, "label": s.get("label", sid), "estimate": s["estimate"], 
             "progress": self.get_progress_label(sid)}
            for sid, s in prev_skills.items()
        ]
        
        return {
            "ready": ready or level <= 1,
            "score": round(avg_estimate, 3),
            "confidence": round(avg_confidence, 3),
            "skills": skill_details,
        }

    def get_snapshot(self) -> Dict:
        """Return the full model as a serializable dict."""
        return {
            "skills": self.skills,
            "summary": {
                skill_id: {
                    "estimate": s["estimate"],
                    "label": self.get_progress_label(skill_id),
                    "sessions": s["session_count"],
                }
                for skill_id, s in self.skills.items()
            }
        }

    def to_json(self) -> str:
        return json.dumps(self.skills)

    @classmethod
    def from_json(cls, data: str) -> "StudentModel":
        return cls(initial_data=json.loads(data))
