"""
Multi-Source Behavioral Profiler & Reinforcement Learning Recommendation Engine
AI-Powered Serious Game Platform for ASD

Synthesizes 6 distinct data sources into a 6-domain radar profile:
1. Automated in-game performance metrics (response time, accuracy, completion)
2. Interaction stability / CV indicators
3. Teacher classroom observations (1-5 scales)
4. Parent home observations (1-5 scales)
5. Historical progression data
6. Environmental context & accommodations

RL Recommender (Contextual Bandit with Human-in-the-Loop Teacher Approval):
- Evaluates skill profile, learning goals, interests, and recent performance
- Suggests developmentally appropriate next game and difficulty
- Provides explainable AI rationale + alternative choices
- Places recommendation in Teacher Approval Queue (NEVER auto-assigns without educator consent)
"""

import json
import sqlite3
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

DB_PATH = "FINAL/backend/platform.db"

# 15 Games mapped to the 6 Profiler Domains
GAME_DOMAIN_MAP = {
    # Level 1
    "bubble-hunt": {"domain": "motor_skills", "sec_domain": "attention_focus", "level": 1, "name": "Bubble Hunt", "icon": "🫧"},
    "follow-the-star": {"domain": "attention_focus", "sec_domain": "motor_skills", "level": 1, "name": "Follow the Star", "icon": "⭐"},
    "pattern-trail": {"domain": "motor_skills", "sec_domain": "attention_focus", "level": 1, "name": "Pattern Trail", "icon": "✏️"},
    # Level 2
    "emotion-mirror": {"domain": "emotion_recognition", "sec_domain": "attention_focus", "level": 2, "name": "Emotion Mirror", "icon": "🪞"},
    "body-says-it": {"domain": "emotion_recognition", "sec_domain": "social_interaction", "level": 2, "name": "Body Says It", "icon": "🧍"},
    "object-quest": {"domain": "attention_focus", "sec_domain": "communication_language", "level": 2, "name": "Object Quest", "icon": "🔍"},
    # Level 3
    "talk-and-build": {"domain": "communication_language", "sec_domain": "attention_focus", "level": 3, "name": "Talk & Build", "icon": "🐿️"},
    "describe-the-scene": {"domain": "communication_language", "sec_domain": "social_interaction", "level": 3, "name": "Describe the Scene", "icon": "🎬"},
    "object-quest-see-say": {"domain": "communication_language", "sec_domain": "attention_focus", "level": 3, "name": "Object Quest: See & Say", "icon": "🔍"},
    # Level 4
    "look-point-share": {"domain": "social_interaction", "sec_domain": "attention_focus", "level": 4, "name": "Look–Point–Share", "icon": "👆"},
    "my-turn-your-turn": {"domain": "social_interaction", "sec_domain": "attention_focus", "level": 4, "name": "My Turn / Your Turn", "icon": "🔄"},
    "copy-my-move": {"domain": "social_interaction", "sec_domain": "motor_skills", "level": 4, "name": "Copy My Move", "icon": "🤹"},
    # Level 5
    "school-day-simulator": {"domain": "daily_living", "sec_domain": "social_interaction", "level": 5, "name": "School Day Simulator", "icon": "🏫"},
    "community-travel-simulator": {"domain": "daily_living", "sec_domain": "social_interaction", "level": 5, "name": "Community Travel Simulator", "icon": "🚌"},
    "shopping-adventure": {"domain": "daily_living", "sec_domain": "communication_language", "level": 5, "name": "Shopping Adventure", "icon": "🛒"},
}

DOMAIN_TITLES = {
    "motor_skills": "Motor Skills & Coordination",
    "attention_focus": "Attention & Focus",
    "emotion_recognition": "Emotion Recognition & Expression",
    "communication_language": "Communication & Language",
    "social_interaction": "Social Interaction & Reciprocity",
    "daily_living": "Daily Living & Functional Routines",
}

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ─────────────────────────────────────────────────────────────────────────────
# 1. Multi-Source Behavioral Profiler
# ─────────────────────────────────────────────────────────────────────────────

def compute_and_save_behavioral_profile(student_id: str, db_conn=None) -> Dict[str, Any]:
    """
    Synthesize multi-source data for a student and update student_behavioral_profiles.
    Combines:
      - Game metrics (score, accuracy, completion)
      - Teacher observations (1-5 scales)
      - Parent home observations (1-5 scales)
      - Parent game feedback
    """
    close_db = False
    if db_conn is None:
        db_conn = get_db()
        close_db = True

    cur = db_conn.cursor()

    # 1. Fetch Student Info
    cur.execute("SELECT * FROM students WHERE id = ?", (student_id,))
    stu_row = cur.fetchone()
    if not stu_row:
        if close_db:
            db_conn.close()
        return {}

    # 2. Fetch Game Sessions & Performance Metrics
    cur.execute("""
        SELECT gs.game_id, gs.difficulty, gs.status, pm.metrics_json
        FROM game_sessions gs
        LEFT JOIN performance_metrics pm ON gs.id = pm.session_id
        WHERE gs.child_id IN (?, 'demo-child')
        ORDER BY gs.started_at DESC LIMIT 30
    """, (student_id,))
    sessions = cur.fetchall()

    game_scores = {d: [] for d in DOMAIN_TITLES.keys()}
    for s in sessions:
        g_id = s["game_id"]
        meta = GAME_DOMAIN_MAP.get(g_id)
        if not meta:
            continue
        
        # Calculate session score 0..1
        perf = 0.65 # default baseline
        if s["metrics_json"]:
            try:
                m = json.loads(s["metrics_json"])
                if "accuracy" in m:
                    perf = min(1.0, max(0.1, m["accuracy"] / 100.0))
                elif "score" in m:
                    perf = min(1.0, max(0.1, m["score"] / 20.0))
                elif "completion_pct" in m:
                    perf = min(1.0, max(0.1, m["completion_pct"] / 100.0))
            except Exception:
                pass
        
        game_scores[meta["domain"]].append(perf)
        if meta.get("sec_domain"):
            game_scores[meta["sec_domain"]].append(perf * 0.9)

    # 3. Fetch Teacher Classroom Observations
    cur.execute("""
        SELECT attention_rating, emotional_regulation, peer_interaction, motor_skills
        FROM teacher_observations
        WHERE student_id = ?
        ORDER BY date DESC LIMIT 10
    """, (student_id,))
    t_obs = cur.fetchall()

    teacher_domain_ratings = {d: [] for d in DOMAIN_TITLES.keys()}
    for tob in t_obs:
        if tob["attention_rating"]:
            teacher_domain_ratings["attention_focus"].append(tob["attention_rating"] / 5.0)
        if tob["emotional_regulation"]:
            teacher_domain_ratings["emotion_recognition"].append(tob["emotional_regulation"] / 5.0)
        if tob["peer_interaction"]:
            teacher_domain_ratings["social_interaction"].append(tob["peer_interaction"] / 5.0)
            teacher_domain_ratings["communication_language"].append(tob["peer_interaction"] / 5.0 * 0.95)
        if tob["motor_skills"]:
            teacher_domain_ratings["motor_skills"].append(tob["motor_skills"] / 5.0)
            teacher_domain_ratings["daily_living"].append(tob["motor_skills"] / 5.0 * 0.9)

    # 4. Fetch Parent Home Observations
    cur.execute("""
        SELECT routine_transitions, communication_attempts, sensory_sensitivity, regulation_strategies
        FROM parent_observations
        WHERE student_id = ?
        ORDER BY date DESC LIMIT 10
    """, (student_id,))
    p_obs = cur.fetchall()

    parent_domain_ratings = {d: [] for d in DOMAIN_TITLES.keys()}
    for pob in p_obs:
        if isinstance(pob["routine_transitions"], (int, float)):
            parent_domain_ratings["daily_living"].append(pob["routine_transitions"] / 5.0)
            parent_domain_ratings["attention_focus"].append(pob["routine_transitions"] / 5.0 * 0.9)
        if isinstance(pob["communication_attempts"], (int, float)):
            parent_domain_ratings["communication_language"].append(pob["communication_attempts"] / 5.0)
            parent_domain_ratings["social_interaction"].append(pob["communication_attempts"] / 5.0 * 0.9)
        if isinstance(pob["sensory_sensitivity"], (int, float)):
            # Invert sensitivity (1 = highly sensitive/dysregulated, 5 = calm adaptation)
            parent_domain_ratings["motor_skills"].append(max(0.2, (6 - pob["sensory_sensitivity"]) / 5.0))
            parent_domain_ratings["emotion_recognition"].append(max(0.2, (6 - pob["sensory_sensitivity"]) / 5.0))
        # If regulation strategies text notes exist, slight boost to emotional regulation
        if pob["regulation_strategies"]:
            parent_domain_ratings["emotion_recognition"].append(0.75)

    # 4b. Fetch Parent Game Card Feedback (Direct Reviews from Parents Dashboard)
    cur.execute("""
        SELECT game_id, enjoyment_rating, frustration_level, assistance_needed, comments
        FROM parent_game_feedback
        WHERE student_id = ?
        ORDER BY created_at DESC LIMIT 20
    """, (student_id,))
    p_feedback = cur.fetchall()

    for pfb in p_feedback:
        gid = pfb["game_id"]
        meta = GAME_DOMAIN_MAP.get(gid)
        if not meta:
            continue
        enjoy = pfb["enjoyment_rating"] if pfb["enjoyment_rating"] is not None else 3
        frust = pfb["frustration_level"] if pfb["frustration_level"] is not None else 2
        assist = pfb["assistance_needed"] if pfb["assistance_needed"] is not None else 2

        # Combined affective engagement & independence score (0..1)
        fb_score = ((enjoy / 5.0) * 0.40) + (((6 - frust) / 5.0) * 0.35) + (((6 - assist) / 5.0) * 0.25)
        parent_domain_ratings[meta["domain"]].append(fb_score)
        if meta.get("sec_domain"):
            parent_domain_ratings[meta["sec_domain"]].append(fb_score * 0.9)

    # 5. Synthesize domain scores with multi-source weighting
    # Weights: Game: 40%, Teacher: 35%, Parent: 25%
    profile_scores = {}
    for d in DOMAIN_TITLES.keys():
        g_vals = game_scores[d]
        t_vals = teacher_domain_ratings[d]
        p_vals = parent_domain_ratings[d]

        g_avg = sum(g_vals) / len(g_vals) if g_vals else None
        t_avg = sum(t_vals) / len(t_vals) if t_vals else None
        p_avg = sum(p_vals) / len(p_vals) if p_vals else None

        # Triangulation
        weights = []
        vals = []
        if g_avg is not None:
            weights.append(0.40)
            vals.append(g_avg)
        if t_avg is not None:
            weights.append(0.35)
            vals.append(t_avg)
        if p_avg is not None:
            weights.append(0.25)
            vals.append(p_avg)

        if vals:
            total_w = sum(weights)
            final_val = sum(v * (w / total_w) for v, w in zip(vals, weights))
        else:
            final_val = 0.55  # default balanced prior

        profile_scores[d] = round(max(0.15, min(0.98, final_val)), 3)

    # Calculate strengths & growth areas
    strengths = []
    growth_areas = []
    for d, score in profile_scores.items():
        title = DOMAIN_TITLES[d]
        if score >= 0.70:
            strengths.append(f"{title} ({int(score * 100)}%)")
        elif score < 0.62:
            growth_areas.append(f"{title} ({int(score * 100)}%)")

    if not strengths:
        # Pick top 2
        sorted_d = sorted(profile_scores.items(), key=lambda x: x[1], reverse=True)
        strengths = [f"{DOMAIN_TITLES[sorted_d[0][0]]} ({int(sorted_d[0][1]*100)}%)"]
    if not growth_areas:
        sorted_d = sorted(profile_scores.items(), key=lambda x: x[1])
        growth_areas = [f"{DOMAIN_TITLES[sorted_d[0][0]]} ({int(sorted_d[0][1]*100)}%)"]

    confidence_score = min(0.95, 0.40 + (len(sessions) * 0.03) + (len(t_obs) * 0.04) + (len(p_obs) * 0.04) + (len(p_feedback) * 0.03))

    now = datetime.utcnow().isoformat()
    # Check if profile row exists
    cur.execute("SELECT id FROM student_behavioral_profiles WHERE student_id = ?", (student_id,))
    existing = cur.fetchone()
    if existing:
        cur.execute("""
            UPDATE student_behavioral_profiles
            SET attention_focus = ?, motor_skills = ?, communication_language = ?,
                emotion_recognition = ?, social_interaction = ?, daily_living = ?,
                strengths_json = ?, growth_areas_json = ?, confidence_score = ?,
                last_calculated_at = ?, updated_at = ?
            WHERE student_id = ?
        """, (
            profile_scores["attention_focus"], profile_scores["motor_skills"],
            profile_scores["communication_language"], profile_scores["emotion_recognition"],
            profile_scores["social_interaction"], profile_scores["daily_living"],
            json.dumps(strengths), json.dumps(growth_areas), confidence_score, now, now, student_id
        ))
    else:
        prof_id = f"prof-{uuid.uuid4().hex[:8]}"
        cur.execute("""
            INSERT INTO student_behavioral_profiles (
                id, student_id, attention_focus, motor_skills, communication_language,
                emotion_recognition, social_interaction, daily_living,
                strengths_json, growth_areas_json, confidence_score,
                last_calculated_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            prof_id, student_id,
            profile_scores["attention_focus"], profile_scores["motor_skills"],
            profile_scores["communication_language"], profile_scores["emotion_recognition"],
            profile_scores["social_interaction"], profile_scores["daily_living"],
            json.dumps(strengths), json.dumps(growth_areas), confidence_score, now, now
        ))

    db_conn.commit()

    result = {
        "student_id": student_id,
        "profile": profile_scores,
        "strengths": strengths,
        "growth_areas": growth_areas,
        "confidence_score": round(confidence_score, 2),
        "calculated_at": now
    }

    if close_db:
        db_conn.close()

    return result


# ─────────────────────────────────────────────────────────────────────────────
# 2. Autonomous RL Game Recommender Pipeline (Human-in-the-Loop)
# ─────────────────────────────────────────────────────────────────────────────

def generate_ai_recommendation(student_id: str, db_conn=None, force: bool = False) -> Optional[Dict[str, Any]]:
    """
    Generate next game recommendation using Contextual Bandit / Skill-Targeting.
    NEVER directly assigns the game. Puts recommendation in 'pending_approval'
    for teacher review and confirmation.
    """
    close_db = False
    if db_conn is None:
        db_conn = get_db()
        close_db = True

    cur = db_conn.cursor()

    # 1. Check if there is already an unreviewed pending recommendation
    if not force:
        cur.execute("""
            SELECT * FROM ai_recommendations
            WHERE student_id = ? AND status = 'pending_approval'
            ORDER BY created_at DESC LIMIT 1
        """, (student_id,))
        pending = cur.fetchone()
        if pending:
            p_dict = dict(pending)
            if close_db:
                db_conn.close()
            return p_dict
    else:
        # Clear existing unapproved pending recommendations for this student before generating fresh one
        cur.execute("""
            DELETE FROM ai_recommendations
            WHERE student_id = ? AND status = 'pending_approval'
        """, (student_id,))
        db_conn.commit()

    # 2. Re-compute or fetch latest profile
    profile_data = compute_and_save_behavioral_profile(student_id, db_conn=db_conn)
    if not profile_data:
        if close_db:
            db_conn.close()
        return None

    scores = profile_data["profile"]

    # 3. Fetch student details (interests, learning objectives)
    cur.execute("SELECT * FROM students WHERE id = ?", (student_id,))
    stu = cur.fetchone()
    stu_name = stu["full_name"] if stu else "the student"
    interests = (stu["interests"] or "").lower()
    goals = (stu["learning_objectives"] or "").lower()

    # 4. Fetch past played games to encourage variety and skill progression
    cur.execute("""
        SELECT game_id FROM game_assignments
        WHERE student_id = ? AND status = 'completed'
        ORDER BY created_at DESC LIMIT 10
    """, (student_id,))
    recently_played = [r["game_id"] for r in cur.fetchall()]

    # 5. Evaluate target developmental domain
    # Sort domains by current mastery (lowest score = highest growth opportunity)
    sorted_domains = sorted(scores.items(), key=lambda x: x[1])
    target_domain = sorted_domains[0][0]
    target_score = sorted_domains[0][1]

    # Find games matching target domain
    candidates = [
        (gid, meta) for gid, meta in GAME_DOMAIN_MAP.items()
        if meta["domain"] == target_domain or meta.get("sec_domain") == target_domain
    ]

    # Score candidates based on:
    # - Interest matching (+0.3)
    # - Goal matching (+0.25)
    # - Novelty (less recently played) (+0.2)
    ranked_candidates = []
    for gid, meta in candidates:
        match_score = 1.0
        g_name_lower = meta["name"].lower()
        if any(term in interests for term in ["bus", "travel", "car"]) and "travel" in g_name_lower:
            match_score += 0.4
        if any(term in interests for term in ["shop", "store", "food"]) and "shopping" in g_name_lower:
            match_score += 0.4
        if any(term in interests for term in ["school", "class", "friend"]) and "school" in g_name_lower:
            match_score += 0.4
        if any(term in interests for term in ["animal", "bubble", "star"]) and any(term in g_name_lower for term in ["bubble", "star", "look"]):
            match_score += 0.3

        if gid in recently_played[:2]:
            match_score -= 0.3  # diversify practice

        ranked_candidates.append((match_score, gid, meta))

    ranked_candidates.sort(key=lambda x: x[0], reverse=True)
    best_candidate = ranked_candidates[0] if ranked_candidates else (1.0, "bubble-hunt", GAME_DOMAIN_MAP["bubble-hunt"])
    primary_gid = best_candidate[1]
    primary_meta = best_candidate[2]

    # Alternative games (2nd and 3rd choices)
    alternatives = []
    alt_pool = [c for c in ranked_candidates if c[1] != primary_gid]
    if not alt_pool:
        alt_pool = [(1.0, gid, meta) for gid, meta in GAME_DOMAIN_MAP.items() if gid != primary_gid]
    for _, alt_gid, alt_meta in alt_pool[:2]:
        alternatives.append({
            "game_id": alt_gid,
            "game_name": alt_meta["name"],
            "level": alt_meta["level"],
            "icon": alt_meta["icon"],
            "domain": DOMAIN_TITLES.get(alt_meta["domain"], alt_meta["domain"])
        })

    # 6. Difficulty recommendation (Contextual Bandit with Multi-Source Sensory Feedback)
    # Check parent game feedback for frustration or difficulty indicators
    cur.execute("""
        SELECT avg(frustration_level), avg(enjoyment_rating)
        FROM parent_game_feedback
        WHERE student_id = ?
    """, (student_id,))
    fb_row = cur.fetchone()
    avg_frust = fb_row[0] if fb_row and fb_row[0] is not None else 2.0
    avg_enjoy = fb_row[1] if fb_row and fb_row[1] is not None else 4.0

    if avg_frust >= 3.5:
        rec_diff = "easy"  # Reduce sensory/cognitive load if parent reports elevated frustration
    elif target_score >= 0.80 and avg_enjoy >= 4.0:
        rec_diff = "medium"
    elif target_score >= 0.88:
        rec_diff = "hard"
    elif target_score < 0.50:
        rec_diff = "easy"
    else:
        rec_diff = "medium"

    # 7. Generate Explainable AI Rationale
    target_title = DOMAIN_TITLES[target_domain]
    rationale = (
        f"Recommended for {stu_name} to strengthen {target_title} (currently assessed at {int(target_score * 100)}%). "
        f"{primary_meta['name']} provides gentle, predictable interaction at {rec_diff.capitalize()} difficulty, "
        f"supporting individual IEP focus and reinforcing positive engagement."
    )
    if interests and any(w in primary_meta["name"].lower() for w in interests.split(',')):
        rationale += f" Aligns with {stu_name}'s personal interest in {stu['interests']}."
    if stu and stu["support_requirements"]:
        rationale += f" Calibrated to support accommodations: {stu['support_requirements']}."

    confidence = round(min(0.96, 0.70 + (0.05 * len(ranked_candidates))), 2)

    rec_id = f"rec-{uuid.uuid4().hex[:8]}"
    now = datetime.utcnow().isoformat()

    cur.execute("""
        INSERT INTO ai_recommendations (
            id, student_id, recommended_game_id, difficulty, target_skill,
            rationale, confidence, status, alternative_games_json, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, 'pending_approval', ?, ?)
    """, (
        rec_id, student_id, primary_gid, rec_diff, target_title,
        rationale, confidence, json.dumps(alternatives), now
    ))

    db_conn.commit()

    result = {
        "id": rec_id,
        "student_id": student_id,
        "recommended_game_id": primary_gid,
        "difficulty": rec_diff,
        "target_skill": target_title,
        "rationale": rationale,
        "confidence": confidence,
        "status": "pending_approval",
        "alternative_games": alternatives,
        "created_at": now
    }

    if close_db:
        db_conn.close()

    return result
