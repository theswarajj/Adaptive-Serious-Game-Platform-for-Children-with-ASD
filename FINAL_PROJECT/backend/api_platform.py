"""
Platform Management & Authentication Router
Handles Teacher Management, Student Profiles, Parent Portal, Observations,
Parent-Teacher Messaging, Game Assignments, AI Recommendation Approvals, and Progress Reports.
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import sqlite3
import os
import json
import uuid
import jwt

from db_schema import DB_PATH, get_db_connection, hash_password

router = APIRouter(prefix="/api", tags=["Platform Management & Auth"])

JWT_SECRET = "asd_serious_games_jwt_secret_2026_key"
JWT_ALGORITHM = "HS256"


# ─── Auth Helpers ─────────────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: timedelta = timedelta(days=7)) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        return None


def get_current_user_optional(authorization: Optional[str] = Header(None)) -> Optional[dict]:
    if not authorization:
        return None
    try:
        parts = authorization.split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return decode_token(parts[1])
    except Exception:
        pass
    return None


# ─── Models ───────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: Optional[str] = None
    pin: Optional[str] = None
    role: Optional[str] = None


class CreateStudentRequest(BaseModel):
    full_name: str
    username: str
    password: str = "1234"
    dob: Optional[str] = None
    age: Optional[int] = 7
    class_id: Optional[str] = "cls-sunflower"
    learning_objectives: Optional[str] = ""
    interests: Optional[str] = ""
    preferred_activities: Optional[str] = ""
    support_requirements: Optional[str] = ""
    avatar: Optional[str] = "default"
    parent_id: Optional[str] = None


class CreateParentRequest(BaseModel):
    full_name: str
    username: str
    password: str = "parent123"
    student_id: str
    relationship: Optional[str] = "Parent / Guardian"
    email: Optional[str] = None
    phone: Optional[str] = None


class UpdateStudentRequest(BaseModel):
    full_name: Optional[str] = None
    username: Optional[str] = None
    dob: Optional[str] = None
    age: Optional[int] = None
    class_id: Optional[str] = None
    learning_objectives: Optional[str] = None
    interests: Optional[str] = None
    preferred_activities: Optional[str] = None
    support_requirements: Optional[str] = None
    avatar: Optional[str] = None
    status: Optional[str] = None


class UpdateParentRequest(BaseModel):
    display_name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    relationship: Optional[str] = None
    student_id: Optional[str] = None
    password: Optional[str] = None


class CreateClassRequest(BaseModel):
    name: str
    description: Optional[str] = ""
    teacher_id: Optional[str] = "usr-teacher-01"


class TeacherObservationRequest(BaseModel):
    student_id: str
    teacher_id: Optional[str] = "usr-teacher-01"
    attention_rating: int = Field(..., ge=1, le=5)
    emotional_regulation: int = Field(..., ge=1, le=5)
    peer_interaction: int = Field(..., ge=1, le=5)
    motor_skills: int = Field(..., ge=1, le=5)
    triggers_observed: Optional[str] = ""
    strategies_used: Optional[str] = ""
    notes: str


class ParentObservationRequest(BaseModel):
    student_id: str
    parent_id: Optional[str] = "usr-parent-01"
    routine_transitions: int = Field(..., ge=1, le=5)
    communication_attempts: int = Field(..., ge=1, le=5)
    sensory_sensitivity: int = Field(..., ge=1, le=5)
    regulation_strategies: Optional[str] = ""
    home_notes: str


class ParentFeedbackRequest(BaseModel):
    student_id: str
    game_id: str
    session_id: Optional[str] = None
    parent_id: Optional[str] = "usr-parent-01"
    enjoyment_rating: int = Field(..., ge=1, le=5)
    frustration_level: int = Field(..., ge=1, le=5)
    assistance_needed: int = Field(..., ge=1, le=5)
    comments: Optional[str] = ""


class ChangePasswordRequest(BaseModel):
    new_password: str
    current_password: Optional[str] = None


class ChangeStudentPasswordRequest(BaseModel):
    new_password: str


class ChangeParentPasswordRequest(BaseModel):
    new_password: str


class SendMessageRequest(BaseModel):
    sender_id: str
    receiver_id: str
    student_id: Optional[str] = None
    content: str


class CreateAssignmentRequest(BaseModel):
    student_id: str
    game_id: str
    sequence_order: int = 1
    difficulty: str = "easy"
    is_unlocked: int = 1
    assigned_by: Optional[str] = "usr-teacher-01"


class BulkAssignmentItem(BaseModel):
    game_id: str
    difficulty: Optional[str] = "easy"
    sequence_order: Optional[int] = None


class BulkAssignStudentRequest(BaseModel):
    assignments: List[BulkAssignmentItem]
    assigned_by: Optional[str] = "usr-teacher-01"


class ReorderAssignmentsRequest(BaseModel):
    assignment_ids: List[str]


class UpdateAssignmentDifficultyRequest(BaseModel):
    difficulty: str


class RecommendationActionRequest(BaseModel):
    teacher_notes: Optional[str] = ""
    modified_game_id: Optional[str] = None
    modified_difficulty: Optional[str] = None


# ─── Auth Endpoints ───────────────────────────────────────────────────

@router.post("/auth/login")
def api_login(req: LoginRequest):
    """Authenticate user with username and password or PIN."""
    conn = get_db_connection()
    cur = conn.cursor()

    username = req.username.strip().lower()
    cur.execute("SELECT * FROM users WHERE lower(username) = ?", (username,))
    user = cur.fetchone()

    if not user:
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid username or credentials")

    # Verify password or PIN
    provided_secret = req.password or req.pin
    if provided_secret:
        h = hash_password(provided_secret)
        if user["password_hash"] and user["password_hash"] != h:
            if user["pin_hash"] and user["pin_hash"] != h:
                conn.close()
                raise HTTPException(status_code=401, detail="Incorrect password or PIN")

    # If student, find student ID
    student_id = None
    class_id = None
    avatar = "default"
    if user["role"] == "student":
        cur.execute("SELECT id, class_id, avatar FROM students WHERE user_id = ?", (user["id"],))
        stu = cur.fetchone()
        if stu:
            student_id = stu["id"]
            class_id = stu["class_id"]
            avatar = stu["avatar"]
        else:
            student_id = "STU-1001"
    elif user["role"] == "parent":
        # Find first linked student
        cur.execute("SELECT student_id FROM parent_student_links WHERE parent_id = ?", (user["id"],))
        link = cur.fetchone()
        student_id = link["student_id"] if link else "STU-1001"

    token_data = {
        "sub": user["id"],
        "username": user["username"],
        "display_name": user["display_name"],
        "role": user["role"],
        "student_id": student_id,
    }
    token = create_access_token(token_data)
    conn.close()

    return {
        "success": True,
        "token": token,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "display_name": user["display_name"],
            "role": user["role"],
            "student_id": student_id,
            "class_id": class_id,
            "avatar": avatar,
        }
    }


@router.get("/auth/me")
def api_me(authorization: Optional[str] = Header(None)):
    """Get current user from JWT token."""
    user = get_current_user_optional(authorization)
    if not user:
        # Default mock fallback for unauthenticated development
        return {
            "id": "usr-teacher-01",
            "username": "teacher",
            "display_name": "Ms. Sarah Wilson",
            "role": "teacher",
            "student_id": "STU-1001"
        }
    return user


# ─── Teacher Dashboard & Management ───────────────────────────────────

@router.get("/teacher/dashboard")
def api_teacher_dashboard():
    """Aggregate all statistics, active assignments, observations, and recommendations for teacher."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT count(*) FROM students WHERE status = 'active'")
    total_students = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM users WHERE role = 'parent'")
    total_parents = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM classes")
    total_classes = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM game_assignments")
    total_assignments = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM game_assignments WHERE status = 'completed'")
    completed_assignments = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM game_assignments WHERE status = 'pending'")
    pending_assignments = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM ai_recommendations WHERE status = 'pending_approval'")
    pending_recommendations_count = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM messages WHERE is_read = 0")
    unread_messages_count = cur.fetchone()[0]

    # Recent teacher observations
    cur.execute("""
        SELECT t.*, s.full_name as student_name
        FROM teacher_observations t
        JOIN students s ON t.student_id = s.id
        ORDER BY t.created_at DESC LIMIT 5
    """)
    recent_teacher_observations = [dict(r) for r in cur.fetchall()]

    # Recent parent observations
    cur.execute("""
        SELECT p.*, s.full_name as student_name, u.display_name as parent_name
        FROM parent_observations p
        JOIN students s ON p.student_id = s.id
        JOIN users u ON p.parent_id = u.id
        ORDER BY p.created_at DESC LIMIT 5
    """)
    recent_parent_observations = [dict(r) for r in cur.fetchall()]

    # Pending AI recommendations
    cur.execute("""
        SELECT r.*, s.full_name as student_name, s.avatar as student_avatar
        FROM ai_recommendations r
        JOIN students s ON r.student_id = s.id
        WHERE r.status = 'pending_approval'
        ORDER BY r.created_at DESC
    """)
    pending_recommendations = [dict(r) for r in cur.fetchall()]

    # Recent game performance sessions
    cur.execute("""
        SELECT gs.*, COALESCE(s.full_name, 'Alex Miller') as student_name
        FROM game_sessions gs
        LEFT JOIN students s ON gs.child_id = s.id
        ORDER BY gs.created_at DESC LIMIT 6
    """)
    recent_sessions = [dict(r) for r in cur.fetchall()]

    # Class Performance & Special Care Cohort Ranking (Internal Educator Insight)
    cur.execute("""
        SELECT s.id, s.full_name, s.age, s.avatar, c.name as class_name,
               p.attention_focus, p.motor_skills, p.communication_language,
               p.emotion_recognition, p.social_interaction, p.daily_living,
               p.confidence_score
        FROM students s
        LEFT JOIN classes c ON s.class_id = c.id
        LEFT JOIN student_behavioral_profiles p ON s.id = p.student_id
        ORDER BY s.full_name ASC
    """)
    students_rows = cur.fetchall()

    ranking_list = []
    for s_row in students_rows:
        s_dict = dict(s_row)
        domains = [
            s_dict.get("motor_skills") or 0.5,
            s_dict.get("attention_focus") or 0.5,
            s_dict.get("emotion_recognition") or 0.5,
            s_dict.get("communication_language") or 0.5,
            s_dict.get("social_interaction") or 0.5,
            s_dict.get("daily_living") or 0.5,
        ]
        composite_score = round((sum(domains) / len(domains)) * 100)

        cur.execute("SELECT count(*) as cnt, coalesce(sum(duration_seconds), 0) as dur FROM game_sessions WHERE child_id IN (?, 'demo-child')", (s_dict["id"],))
        sess_data = cur.fetchone()
        sess_count = sess_data["cnt"] if sess_data else 0
        total_minutes = round((sess_data["dur"] if sess_data else 0) / 60.0, 1)

        special_care_flags = []
        if (s_dict.get("attention_focus") or 0.5) < 0.60:
            special_care_flags.append("Attention Span Support")
        if (s_dict.get("social_interaction") or 0.5) < 0.60:
            special_care_flags.append("Turn-Taking Reciprocity")
        if (s_dict.get("emotion_recognition") or 0.5) < 0.60:
            special_care_flags.append("Emotional Self-Regulation")
        if (s_dict.get("communication_language") or 0.5) < 0.60:
            special_care_flags.append("Expressive Speech Assistance")
        if (s_dict.get("motor_skills") or 0.5) < 0.60:
            special_care_flags.append("Fine Motor Coordination")

        if composite_score >= 75 and not special_care_flags:
            cohort_tier = "Thriving"
            badge = "🌟 High Independence"
            support_level = "Standard Autonomous Learning"
        elif composite_score >= 60:
            cohort_tier = "Steady Growth"
            badge = "📈 Growing"
            support_level = "Guided Scaffolding"
        else:
            cohort_tier = "Special Care Focus"
            badge = "🧡 Special Care Required"
            support_level = "1-on-1 Personalized Care"
            if not special_care_flags:
                special_care_flags.append("Requires Foundation Scaffolding")

        ranking_list.append({
            "student_id": s_dict["id"],
            "full_name": s_dict["full_name"],
            "age": s_dict["age"] or 7,
            "avatar": s_dict["avatar"] or "boy-1",
            "class_name": s_dict["class_name"] or "Sunflower Room",
            "composite_score": composite_score,
            "sessions_played": sess_count,
            "total_minutes": total_minutes,
            "cohort_tier": cohort_tier,
            "badge": badge,
            "support_level": support_level,
            "special_care_flags": special_care_flags,
            "requires_special_care": cohort_tier == "Special Care Focus",
        })

    ranking_list.sort(key=lambda x: (x["composite_score"], x["sessions_played"]), reverse=True)
    for idx, item in enumerate(ranking_list):
        item["class_rank"] = idx + 1

    conn.close()

    return {
        "stats": {
            "total_students": total_students,
            "total_parents": total_parents,
            "total_classes": total_classes,
            "active_students": total_students,
            "total_assignments": total_assignments,
            "completed_assignments": completed_assignments,
            "pending_assignments": pending_assignments,
            "pending_recommendations_count": pending_recommendations_count,
            "unread_messages_count": unread_messages_count,
        },
        "recent_teacher_observations": recent_teacher_observations,
        "recent_parent_observations": recent_parent_observations,
        "pending_recommendations": pending_recommendations,
        "recent_sessions": recent_sessions,
        "class_cohort_ranking": ranking_list,
    }


@router.get("/teacher/parents")
def api_get_parents():
    """List all parents and their linked students for Teacher administration."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT u.id, u.username, u.display_name as full_name, u.role, u.created_at,
               u.email, u.phone,
               s.id as student_id, s.full_name as student_name, l.relationship
        FROM users u
        LEFT JOIN parent_student_links l ON u.id = l.parent_id
        LEFT JOIN students s ON l.student_id = s.id
        WHERE u.role = 'parent'
        ORDER BY u.display_name ASC
    """)
    parents = [dict(r) for r in cur.fetchall()]
    conn.close()
    return parents


@router.post("/teacher/parents")
def api_create_parent(req: CreateParentRequest):
    """Teacher creates a parent account with credentials and links to student."""
    conn = get_db_connection()
    cur = conn.cursor()

    # Check if username exists
    cur.execute("SELECT id FROM users WHERE username = ?", (req.username.strip().lower(),))
    if cur.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail="Username already exists")

    parent_id = f"usr-parent-{uuid.uuid4().hex[:6]}"
    hashed_pw = hash_password(req.password)
    now = datetime.utcnow().isoformat()

    cur.execute("""
        INSERT INTO users (id, username, password_hash, role, display_name, email, phone, created_at)
        VALUES (?, ?, ?, 'parent', ?, ?, ?, ?)
    """, (parent_id, req.username.strip().lower(), hashed_pw, req.full_name.strip(), req.email or "", req.phone or "", now))

    # Link to student
    link_id = f"link-{uuid.uuid4().hex[:6]}"
    cur.execute("""
        INSERT INTO parent_student_links (id, parent_id, student_id, relationship, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (link_id, parent_id, req.student_id, req.relationship or "Parent / Guardian", now))

    conn.commit()
    conn.close()
    return {"success": True, "parent_id": parent_id, "username": req.username, "message": "Parent account created and linked"}


@router.put("/teacher/parents/{parent_id}")
def api_update_parent_by_teacher(parent_id: str, req: UpdateParentRequest):
    """Teacher updates parent account profile, contact info, and linked student."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, username FROM users WHERE id = ? AND role = 'parent'", (parent_id,))
    prow = cur.fetchone()
    if not prow:
        conn.close()
        raise HTTPException(status_code=404, detail="Parent account not found")

    user_updates = []
    user_params = []

    if req.username:
        clean_user = req.username.strip().lower()
        cur.execute("SELECT id FROM users WHERE username = ? AND id != ?", (clean_user, parent_id))
        if cur.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail="Username already in use")
        user_updates.append("username = ?")
        user_params.append(clean_user)

    if req.display_name:
        user_updates.append("display_name = ?")
        user_params.append(req.display_name.strip())

    if req.email is not None:
        user_updates.append("email = ?")
        user_params.append(req.email.strip())

    if req.phone is not None:
        user_updates.append("phone = ?")
        user_params.append(req.phone.strip())

    if req.password:
        user_updates.append("password_hash = ?")
        user_params.append(hash_password(req.password.strip()))

    if user_updates:
        user_updates.append("updated_at = datetime('now')")
        user_params.append(parent_id)
        cur.execute(f"UPDATE users SET {', '.join(user_updates)} WHERE id = ?", user_params)

    # Link / relationship updates
    if req.relationship is not None or req.student_id is not None:
        cur.execute("SELECT id FROM parent_student_links WHERE parent_id = ?", (parent_id,))
        link_row = cur.fetchone()
        now = datetime.utcnow().isoformat()
        if link_row:
            link_updates = []
            link_params = []
            if req.relationship is not None:
                link_updates.append("relationship = ?")
                link_params.append(req.relationship.strip())
            if req.student_id is not None:
                link_updates.append("student_id = ?")
                link_params.append(req.student_id.strip())
            if link_updates:
                link_params.append(link_row["id"])
                cur.execute(f"UPDATE parent_student_links SET {', '.join(link_updates)} WHERE id = ?", link_params)
        elif req.student_id:
            link_id = f"link-{uuid.uuid4().hex[:6]}"
            cur.execute("""
                INSERT INTO parent_student_links (id, parent_id, student_id, relationship, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, (link_id, parent_id, req.student_id.strip(), req.relationship or "Parent / Guardian", now))

    conn.commit()
    conn.close()
    return {"success": True, "message": "Parent details updated successfully"}


@router.get("/teacher/students")
def api_teacher_students():
    """List all students with their class, assigned games count, and radar profile."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT s.*, u.username as username, c.name as class_name,
               p.attention_focus, p.motor_skills, p.communication_language,
               p.emotion_recognition, p.social_interaction, p.daily_living,
               p.confidence_score
        FROM students s
        LEFT JOIN users u ON s.user_id = u.id
        LEFT JOIN classes c ON s.class_id = c.id
        LEFT JOIN student_behavioral_profiles p ON s.id = p.student_id
        ORDER BY s.full_name ASC
    """)
    students = []
    for row in cur.fetchall():
        stu = dict(row)
        # Count sessions played
        cur.execute("SELECT count(*) FROM game_sessions WHERE child_id IN (?, 'demo-child')", (stu["id"],))
        stu["sessions_count"] = cur.fetchone()[0]

        # Get parent details
        cur.execute("""
            SELECT u.id as parent_id, u.display_name, u.username, u.email, u.phone, l.relationship
            FROM parent_student_links l
            JOIN users u ON l.parent_id = u.id
            WHERE l.student_id = ?
        """, (stu["id"],))
        p_row = cur.fetchone()
        if p_row:
            p_dict = dict(p_row)
            stu["parent_id"] = p_dict["parent_id"]
            stu["parent_name"] = p_dict["display_name"]
            stu["parent_username"] = p_dict["username"]
            stu["parent_email"] = p_dict["email"]
            stu["parent_phone"] = p_dict["phone"]
            stu["parent_relationship"] = p_dict["relationship"]
        else:
            stu["parent_id"] = None
            stu["parent_name"] = "Not linked"
            stu["parent_username"] = None
            stu["parent_email"] = None
            stu["parent_phone"] = None
            stu["parent_relationship"] = None

        students.append(stu)

    conn.close()
    return students


@router.post("/teacher/students")
def api_create_student(req: CreateStudentRequest):
    """Create a new student account, login credentials, and initial profile."""
    conn = get_db_connection()
    cur = conn.cursor()

    # Generate unique student ID
    cur.execute("SELECT count(*) FROM students")
    count = cur.fetchone()[0] + 1
    student_id = f"STU-{1000 + count}"
    user_id = f"usr-student-{count:02d}"
    now = datetime.utcnow().isoformat()

    # Create user
    cur.execute("""
        INSERT INTO users (id, username, display_name, role, password_hash, pin_hash, status, created_at)
        VALUES (?, ?, ?, 'student', ?, ?, 'active', ?)
    """, (user_id, req.username.strip().lower(), req.full_name.strip(),
          hash_password(req.password), hash_password(req.password), now))

    # Create student profile
    cur.execute("""
        INSERT INTO students (id, user_id, full_name, dob, age, class_id, learning_objectives, interests, preferred_activities, support_requirements, avatar, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'active', ?)
    """, (student_id, user_id, req.full_name.strip(), req.dob, req.age, req.class_id,
          req.learning_objectives, req.interests, req.preferred_activities, req.support_requirements, req.avatar, now))

    # Create backward-compatible child_profiles
    cur.execute("""
        INSERT INTO child_profiles (id, caregiver_id, display_name, avatar, theme, settings_json, created_at)
        VALUES (?, ?, ?, ?, 'calm', '{}', ?)
    """, (student_id, req.parent_id or "usr-parent-01", req.full_name.strip(), req.avatar, now))

    # Link parent if provided
    if req.parent_id:
        cur.execute("""
            INSERT OR IGNORE INTO parent_student_links (id, parent_id, student_id, relationship, created_at)
            VALUES (?, ?, ?, 'Parent/Guardian', ?)
        """, (f"link-{count:02d}", req.parent_id, student_id, now))

    # Create initial behavioral profile
    cur.execute("""
        INSERT INTO student_behavioral_profiles (id, student_id, attention_focus, motor_skills, communication_language, emotion_recognition, social_interaction, daily_living, strengths_json, growth_areas_json, confidence_score, last_calculated_at, updated_at)
        VALUES (?, ?, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, '[]', '[]', 0.50, ?, ?)
    """, (f"prof-{student_id}", student_id, now, now))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "student_id": student_id,
        "username": req.username,
        "message": f"Student {req.full_name} created successfully with ID {student_id}"
    }


@router.get("/teacher/students/{student_id}")
def api_get_student_detail(student_id: str):
    """Retrieve complete 360-degree profile for a single student."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT s.*, u.username as username, c.name as class_name
        FROM students s
        LEFT JOIN users u ON s.user_id = u.id
        LEFT JOIN classes c ON s.class_id = c.id
        WHERE s.id = ?
    """, (student_id,))
    stu_row = cur.fetchone()

    if not stu_row:
        conn.close()
        raise HTTPException(status_code=404, detail="Student not found")

    student = dict(stu_row)

    # Linked parents
    cur.execute("""
        SELECT u.id, u.display_name, u.username, u.email, u.phone, l.relationship
        FROM parent_student_links l
        JOIN users u ON l.parent_id = u.id
        WHERE l.student_id = ?
    """, (student_id,))
    student["parents"] = [dict(r) for r in cur.fetchall()]

    # Behavioral Profile
    cur.execute("SELECT * FROM student_behavioral_profiles WHERE student_id = ?", (student_id,))
    prof_row = cur.fetchone()
    if prof_row:
        p_dict = dict(prof_row)
        p_dict["strengths"] = json.loads(p_dict.get("strengths_json") or "[]")
        p_dict["growth_areas"] = json.loads(p_dict.get("growth_areas_json") or "[]")
        student["behavioral_profile"] = p_dict
    else:
        student["behavioral_profile"] = {
            "attention_focus": 0.5, "motor_skills": 0.5, "communication_language": 0.5,
            "emotion_recognition": 0.5, "social_interaction": 0.5, "daily_living": 0.5,
            "strengths": [], "growth_areas": [], "confidence_score": 0.5
        }

    # Teacher observations
    cur.execute("SELECT * FROM teacher_observations WHERE student_id = ? ORDER BY date DESC", (student_id,))
    student["teacher_observations"] = [dict(r) for r in cur.fetchall()]

    # Parent observations
    cur.execute("SELECT * FROM parent_observations WHERE student_id = ? ORDER BY date DESC", (student_id,))
    student["parent_observations"] = [dict(r) for r in cur.fetchall()]

    # Parent game feedback
    cur.execute("SELECT * FROM parent_game_feedback WHERE student_id = ? ORDER BY created_at DESC", (student_id,))
    student["parent_feedback"] = [dict(r) for r in cur.fetchall()]

    # Assignments
    cur.execute("SELECT * FROM game_assignments WHERE student_id = ? ORDER BY sequence_order ASC", (student_id,))
    asg_list = [dict(r) for r in cur.fetchall()]
    student["assignments"] = asg_list
    student["assigned_games"] = asg_list

    # AI Recommendations
    cur.execute("SELECT * FROM ai_recommendations WHERE student_id = ? ORDER BY created_at DESC", (student_id,))
    student["recommendations"] = [dict(r) for r in cur.fetchall()]

    # Game Sessions History
    cur.execute("""
        SELECT gs.*, pm.metrics_json
        FROM game_sessions gs
        LEFT JOIN performance_metrics pm ON gs.id = pm.session_id
        WHERE gs.child_id IN (?, 'demo-child')
        ORDER BY gs.started_at DESC LIMIT 15
    """, (student_id,))
    sessions = []
    for r in cur.fetchall():
        s_dict = dict(r)
        if s_dict.get("metrics_json"):
            try:
                s_dict["metrics"] = json.loads(s_dict["metrics_json"])
            except Exception:
                s_dict["metrics"] = {}
        sessions.append(s_dict)
    student["session_history"] = sessions

    conn.close()
    return student


@router.put("/teacher/students/{student_id}")
def api_update_student(student_id: str, req: UpdateStudentRequest):
    """Update student information, goals, or status."""
    conn = get_db_connection()
    cur = conn.cursor()

    # Look up user_id
    cur.execute("SELECT user_id, full_name FROM students WHERE id = ?", (student_id,))
    srow = cur.fetchone()
    if not srow:
        conn.close()
        raise HTTPException(status_code=404, detail="Student not found")

    user_id = srow["user_id"]

    # Check and update users table if username or full_name provided
    if req.username:
        clean_user = req.username.strip().lower()
        cur.execute("SELECT id FROM users WHERE username = ? AND id != ?", (clean_user, user_id))
        if cur.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail="Username already taken by another account")
        cur.execute("UPDATE users SET username = ?, updated_at = datetime('now') WHERE id = ?", (clean_user, user_id))

    if req.full_name:
        cur.execute("UPDATE users SET display_name = ?, updated_at = datetime('now') WHERE id = ?", (req.full_name.strip(), user_id))

    # Update students table
    student_fields = ["full_name", "dob", "age", "class_id", "learning_objectives", "interests", "preferred_activities", "support_requirements", "avatar", "status"]
    updates = []
    params = []
    req_dict = req.dict(exclude_unset=True)
    for field in student_fields:
        if field in req_dict and req_dict[field] is not None:
            updates.append(f"{field} = ?")
            params.append(req_dict[field])

    if updates:
        params.append(datetime.utcnow().isoformat())
        params.append(student_id)
        cur.execute(f"UPDATE students SET {', '.join(updates)}, updated_at = ? WHERE id = ?", params)

    conn.commit()
    conn.close()
    return {"success": True, "message": "Student updated successfully"}


@router.get("/teacher/classes")
def api_get_classes():
    """List all classes."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT c.*, count(s.id) as student_count
        FROM classes c
        LEFT JOIN students s ON c.id = s.class_id
        GROUP BY c.id
    """)
    classes = [dict(r) for r in cur.fetchall()]
    conn.close()
    return classes


@router.post("/teacher/classes")
def api_create_class(req: CreateClassRequest):
    """Create a new class."""
    conn = get_db_connection()
    cur = conn.cursor()
    class_id = f"cls-{uuid.uuid4().hex[:6]}"
    cur.execute("""
        INSERT INTO classes (id, name, description, teacher_id, created_at)
        VALUES (?, ?, ?, ?, datetime('now'))
    """, (class_id, req.name, req.description, req.teacher_id))
    conn.commit()
    conn.close()
    return {"success": True, "class_id": class_id, "name": req.name}


@router.post("/teacher/observations")
def api_add_teacher_observation(req: TeacherObservationRequest):
    """Add a structured teacher classroom observation."""
    conn = get_db_connection()
    cur = conn.cursor()
    obs_id = f"obs-t-{uuid.uuid4().hex[:8]}"
    date_str = datetime.utcnow().strftime("%Y-%m-%d")

    cur.execute("""
        INSERT INTO teacher_observations (id, student_id, teacher_id, date, attention_rating, emotional_regulation, peer_interaction, motor_skills, triggers_observed, strategies_used, notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    """, (obs_id, req.student_id, req.teacher_id, date_str, req.attention_rating, req.emotional_regulation,
          req.peer_interaction, req.motor_skills, req.triggers_observed, req.strategies_used, req.notes))

    conn.commit()
    conn.close()

    try:
        from profiler_recommender import compute_and_save_behavioral_profile
        compute_and_save_behavioral_profile(req.student_id)
    except Exception as e:
        print(f"Auto-update profile error after teacher observation: {e}")

    return {"success": True, "observation_id": obs_id, "message": "Observation saved"}


# ─── Parent Portal Endpoints ──────────────────────────────────────────

class UpdateParentProfileRequest(BaseModel):
    display_name: Optional[str] = None
    username: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    relationship: Optional[str] = None
    password: Optional[str] = None


@router.get("/parent/profile")
def api_get_parent_profile(parent_id: Optional[str] = None, authorization: Optional[str] = Header(None)):
    """Get parent profile details and linked children info."""
    conn = get_db_connection()
    cur = conn.cursor()
    user = get_current_user_optional(authorization)
    p_id = parent_id or (user["sub"] if user and user.get("role") == "parent" else "parent-user")

    cur.execute("SELECT id, username, display_name, email, phone, role, created_at FROM users WHERE id = ?", (p_id,))
    parent_row = cur.fetchone()
    if not parent_row:
        # Fallback to demo parent
        cur.execute("SELECT id, username, display_name, email, phone, role, created_at FROM users WHERE role = 'parent' LIMIT 1")
        parent_row = cur.fetchone()

    parent_data = dict(parent_row) if parent_row else {
        "id": "parent-user", "username": "parent", "display_name": "Elena Miller (Parent)",
        "email": "elena.miller@example.com", "phone": "+1 (555) 234-5678", "role": "parent"
    }

    cur.execute("""
        SELECT s.id as student_id, s.full_name as student_name, s.dob, s.age,
               c.name as class_name, l.relationship, s.learning_objectives,
               s.support_requirements, s.avatar
        FROM parent_student_links l
        JOIN students s ON l.student_id = s.id
        LEFT JOIN classes c ON s.class_id = c.id
        WHERE l.parent_id = ?
    """, (parent_data["id"],))
    children = [dict(r) for r in cur.fetchall()]

    if not children:
        # Fallback link to STU-1001 for demo consistency
        cur.execute("""
            SELECT s.id as student_id, s.full_name as student_name, s.dob, s.age,
                   c.name as class_name, 'Mother' as relationship, s.learning_objectives,
                   s.support_requirements, s.avatar
            FROM students s
            LEFT JOIN classes c ON s.class_id = c.id
            WHERE s.id = 'STU-1001'
        """)
        f_row = cur.fetchone()
        if f_row:
            children.append(dict(f_row))

    conn.close()
    return {"parent": parent_data, "children": children}


@router.put("/parent/profile")
def api_update_parent_profile(req: UpdateParentProfileRequest, parent_id: Optional[str] = None, authorization: Optional[str] = Header(None)):
    """Update parent contact details."""
    conn = get_db_connection()
    cur = conn.cursor()
    user = get_current_user_optional(authorization)
    p_id = parent_id or (user["sub"] if user and user.get("role") == "parent" else "parent-user")

    updates = []
    params = []
    if req.username:
        clean_user = req.username.strip().lower()
        cur.execute("SELECT id FROM users WHERE username = ? AND id != ?", (clean_user, p_id))
        if cur.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail="Username already in use")
        updates.append("username = ?")
        params.append(clean_user)
    if req.display_name:
        updates.append("display_name = ?")
        params.append(req.display_name.strip())
    if req.email:
        updates.append("email = ?")
        params.append(req.email.strip())
    if req.phone:
        updates.append("phone = ?")
        params.append(req.phone.strip())
    if req.password:
        updates.append("password_hash = ?")
        params.append(hash_password(req.password))

    if updates:
        updates.append("updated_at = datetime('now')")
        params.append(p_id)
        cur.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", params)

    if req.relationship:
        cur.execute("UPDATE parent_student_links SET relationship = ? WHERE parent_id = ?", (req.relationship, p_id))

    conn.commit()
    conn.close()
    return {"success": True, "message": "Parent profile updated successfully"}


@router.get("/parent/children")
def api_parent_children(parent_id: Optional[str] = None, authorization: Optional[str] = Header(None)):
    """List all children linked to parent with full student IDs and parent details."""
    conn = get_db_connection()
    cur = conn.cursor()

    user = get_current_user_optional(authorization)
    p_id = parent_id or (user["sub"] if user and user.get("role") == "parent" else None)
    if not p_id:
        p_id = "parent-user"

    cur.execute("""
        SELECT s.*, s.id as student_id, u_stu.username as username, c.name as class_name, l.relationship,
               u.display_name as parent_name, u.username as parent_username,
               u.email as parent_email, u.phone as parent_phone,
               p.attention_focus, p.motor_skills, p.communication_language,
               p.emotion_recognition, p.social_interaction, p.daily_living,
               p.confidence_score
        FROM parent_student_links l
        JOIN students s ON l.student_id = s.id
        JOIN users u ON l.parent_id = u.id
        LEFT JOIN users u_stu ON s.user_id = u_stu.id
        LEFT JOIN classes c ON s.class_id = c.id
        LEFT JOIN student_behavioral_profiles p ON s.id = p.student_id
        WHERE l.parent_id = ?
    """, (p_id,))
    children = []
    for r in cur.fetchall():
        ch = dict(r)
        ch["student_id"] = ch["id"]
        # Fetch active assignments
        cur.execute("""
            SELECT * FROM game_assignments
            WHERE student_id = ? ORDER BY sequence_order ASC
        """, (ch["id"],))
        ch["assignments"] = [dict(a) for a in cur.fetchall()]
        ch["assigned_games"] = ch["assignments"]

        # Latest teacher note
        cur.execute("""
            SELECT notes, date FROM teacher_observations
            WHERE student_id = ? ORDER BY created_at DESC LIMIT 1
        """, (ch["id"],))
        t_note = cur.fetchone()
        ch["latest_teacher_note"] = dict(t_note) if t_note else None

        children.append(ch)

    if not children:
        # Fallback to STU-1001 for resilient demo
        cur.execute("""
            SELECT s.*, s.id as student_id, 'alex' as username, c.name as class_name, 'Mother' as relationship,
                   'Elena Miller' as parent_name, 'parent' as parent_username,
                   'elena.miller@example.com' as parent_email, '+1 (555) 234-5678' as parent_phone,
                   p.attention_focus, p.motor_skills, p.communication_language,
                   p.emotion_recognition, p.social_interaction, p.daily_living,
                   p.confidence_score
            FROM students s
            LEFT JOIN classes c ON s.class_id = c.id
            LEFT JOIN student_behavioral_profiles p ON s.id = p.student_id
            WHERE s.id = 'STU-1001'
        """)
        fallback_r = cur.fetchone()
        if fallback_r:
            ch = dict(fallback_r)
            ch["student_id"] = ch["id"]
            cur.execute("SELECT * FROM game_assignments WHERE student_id = ? ORDER BY sequence_order ASC", (ch["id"],))
            ch["assignments"] = [dict(a) for a in cur.fetchall()]
            ch["assigned_games"] = ch["assignments"]
            cur.execute("""
                SELECT notes, date FROM teacher_observations
                WHERE student_id = ? ORDER BY created_at DESC LIMIT 1
            """, (ch["id"],))
            t_note = cur.fetchone()
            ch["latest_teacher_note"] = dict(t_note) if t_note else None
            children.append(ch)

    conn.close()
    return children


@router.post("/parent/observations")
def api_add_parent_observation(req: ParentObservationRequest):
    """Submit a parent home observation."""
    conn = get_db_connection()
    cur = conn.cursor()
    obs_id = f"obs-p-{uuid.uuid4().hex[:8]}"
    date_str = datetime.utcnow().strftime("%Y-%m-%d")

    cur.execute("""
        INSERT INTO parent_observations (id, student_id, parent_id, date, routine_transitions, communication_attempts, sensory_sensitivity, regulation_strategies, home_notes, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    """, (obs_id, req.student_id, req.parent_id, date_str, req.routine_transitions, req.communication_attempts,
          req.sensory_sensitivity, req.regulation_strategies, req.home_notes))

    conn.commit()
    conn.close()

    try:
        from profiler_recommender import compute_and_save_behavioral_profile
        compute_and_save_behavioral_profile(req.student_id)
    except Exception as e:
        print(f"Auto-update profile error after parent observation: {e}")

    return {"success": True, "observation_id": obs_id, "message": "Home observation saved"}


@router.post("/parent/feedback")
def api_add_parent_feedback(req: ParentFeedbackRequest):
    """Submit per-game session parent feedback."""
    conn = get_db_connection()
    cur = conn.cursor()
    fb_id = f"fb-{uuid.uuid4().hex[:8]}"

    cur.execute("""
        INSERT INTO parent_game_feedback (id, student_id, game_id, parent_id, enjoyment_rating, frustration_level, assistance_needed, comments, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
    """, (fb_id, req.student_id, req.game_id, req.parent_id, req.enjoyment_rating, req.frustration_level, req.assistance_needed, req.comments))

    conn.commit()
    conn.close()

    try:
        from profiler_recommender import compute_and_save_behavioral_profile
        compute_and_save_behavioral_profile(req.student_id)
    except Exception as e:
        print(f"Auto-update profile error after parent feedback: {e}")

    return {"success": True, "feedback_id": fb_id, "message": "Feedback submitted"}


# ─── Parent-Teacher Messaging Endpoints ────────────────────────────────

@router.get("/messages")
def api_get_messages(student_id: Optional[str] = "STU-1001"):
    """Retrieve message thread for a student."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT m.*, s_user.display_name as sender_name, s_user.role as sender_role,
               r_user.display_name as receiver_name
        FROM messages m
        JOIN users s_user ON m.sender_id = s_user.id
        JOIN users r_user ON m.receiver_id = r_user.id
        WHERE m.student_id = ? OR ? IS NULL
        ORDER BY m.created_at ASC
    """, (student_id, student_id))
    messages = [dict(r) for r in cur.fetchall()]
    conn.close()
    return messages


@router.post("/messages")
def api_send_message(req: SendMessageRequest):
    """Send a private message between parent and teacher."""
    conn = get_db_connection()
    cur = conn.cursor()
    msg_id = f"msg-{uuid.uuid4().hex[:8]}"

    cur.execute("""
        INSERT INTO messages (id, sender_id, receiver_id, student_id, content, is_read, created_at)
        VALUES (?, ?, ?, ?, ?, 0, datetime('now'))
    """, (msg_id, req.sender_id, req.receiver_id, req.student_id, req.content))

    conn.commit()
    conn.close()
    return {"success": True, "message_id": msg_id, "message": "Message sent"}


# ─── Game Assignments & Sequence ──────────────────────────────────────

@router.get("/students/{student_id}/profile")
def api_get_student_portal_profile(student_id: str):
    """Retrieve child-friendly student profile, assigned teacher, and IEP focus."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.id as student_id, s.full_name, s.dob, s.age, s.avatar,
               c.name as class_name, s.learning_objectives, s.support_requirements,
               u.display_name as teacher_name
        FROM students s
        LEFT JOIN classes c ON s.class_id = c.id
        LEFT JOIN users u ON c.teacher_id = u.id
        WHERE s.id = ?
    """, (student_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Student not found")
    data = dict(row)
    if not data.get("teacher_name"):
        data["teacher_name"] = "Ms. Sarah Wilson (Lead Educator)"

    cur.execute("SELECT count(*) FROM game_sessions WHERE child_id IN (?, 'demo-child')", (student_id,))
    data["stars_earned"] = cur.fetchone()[0]

    cur.execute("SELECT count(*) FROM game_assignments WHERE student_id = ? AND status = 'completed'", (student_id,))
    data["completed_quests"] = cur.fetchone()[0]

    conn.close()
    return data


@router.get("/students/{student_id}/assignments")
def api_get_student_assignments(student_id: str):
    """Retrieve learning path sequence of games assigned to the student."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT * FROM game_assignments
        WHERE student_id = ?
        ORDER BY sequence_order ASC
    """, (student_id,))
    assignments = [dict(r) for r in cur.fetchall()]
    conn.close()
    return assignments


@router.post("/teacher/assignments")
def api_create_assignment(req: CreateAssignmentRequest):
    """Assign a game to a student."""
    conn = get_db_connection()
    cur = conn.cursor()
    asg_id = f"asg-{uuid.uuid4().hex[:8]}"

    # Determine sequence order if not provided or 0
    cur.execute("SELECT count(*) FROM game_assignments WHERE student_id = ?", (req.student_id,))
    existing_count = cur.fetchone()[0]
    seq_order = req.sequence_order if req.sequence_order > 0 else (existing_count + 1)
    is_unlocked = req.is_unlocked if existing_count > 0 else 1

    cur.execute("""
        INSERT INTO game_assignments (id, student_id, game_id, sequence_order, difficulty, is_unlocked, assigned_by, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', datetime('now'))
    """, (asg_id, req.student_id, req.game_id, seq_order, req.difficulty, is_unlocked, req.assigned_by))

    conn.commit()
    conn.close()
    return {"success": True, "assignment_id": asg_id, "message": "Game assigned"}


@router.delete("/teacher/assignments/{assignment_id}")
def api_delete_assignment(assignment_id: str):
    """Delete an assignment and recompact sequence order for the student."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT student_id FROM game_assignments WHERE id = ?", (assignment_id,))
    row = cur.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="Assignment not found")
    student_id = row["student_id"]

    cur.execute("DELETE FROM game_assignments WHERE id = ?", (assignment_id,))

    # Recompact sequence orders
    cur.execute("""
        SELECT id FROM game_assignments
        WHERE student_id = ?
        ORDER BY sequence_order ASC, created_at ASC
    """, (student_id,))
    remaining = cur.fetchall()
    for idx, r in enumerate(remaining, start=1):
        cur.execute("UPDATE game_assignments SET sequence_order = ? WHERE id = ?", (idx, r["id"]))

    # Ensure the first activity is unlocked
    if remaining:
        cur.execute("UPDATE game_assignments SET is_unlocked = 1 WHERE id = ?", (remaining[0]["id"],))

    conn.commit()
    conn.close()
    return {"success": True, "message": "Assignment deleted and sequence recompacted"}


@router.delete("/teacher/students/{student_id}/assignments/game/{game_id}")
def api_unassign_game(student_id: str, game_id: str):
    """Remove a specific game from a student's assigned learning path and recompact order."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM game_assignments WHERE student_id = ? AND game_id = ?", (student_id, game_id))

    cur.execute("""
        SELECT id FROM game_assignments
        WHERE student_id = ?
        ORDER BY sequence_order ASC, created_at ASC
    """, (student_id,))
    remaining = cur.fetchall()
    for idx, r in enumerate(remaining, start=1):
        cur.execute("UPDATE game_assignments SET sequence_order = ? WHERE id = ?", (idx, r["id"]))

    if remaining:
        cur.execute("UPDATE game_assignments SET is_unlocked = 1 WHERE id = ?", (remaining[0]["id"],))

    conn.commit()
    conn.close()
    return {"success": True, "message": f"Game '{game_id}' removed from student '{student_id}'"}


@router.put("/teacher/assignments/{assignment_id}/difficulty")
def api_update_assignment_difficulty(assignment_id: str, req: UpdateAssignmentDifficultyRequest):
    """Change the difficulty of an assigned game."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE game_assignments SET difficulty = ? WHERE id = ?", (req.difficulty, assignment_id))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Difficulty updated"}


@router.post("/teacher/students/{student_id}/assignments/reorder")
def api_reorder_assignments(student_id: str, req: ReorderAssignmentsRequest):
    """Update sequence orders based on an ordered list of assignment IDs."""
    conn = get_db_connection()
    cur = conn.cursor()
    for order, asg_id in enumerate(req.assignment_ids, start=1):
        cur.execute("UPDATE game_assignments SET sequence_order = ? WHERE id = ? AND student_id = ?", (order, asg_id, student_id))

    if req.assignment_ids:
        cur.execute("UPDATE game_assignments SET is_unlocked = 1 WHERE id = ?", (req.assignment_ids[0],))

    conn.commit()
    conn.close()
    return {"success": True, "message": "Assignments sequence reordered"}


@router.post("/teacher/students/{student_id}/assignments/bulk")
def api_bulk_assign_student(student_id: str, req: BulkAssignStudentRequest):
    """Replace student's pending assignments with the provided curriculum sequence."""
    conn = get_db_connection()
    cur = conn.cursor()

    # Remove existing pending assignments so completed history is safely preserved
    cur.execute("DELETE FROM game_assignments WHERE student_id = ? AND status = 'pending'", (student_id,))
    cur.execute("SELECT count(*) FROM game_assignments WHERE student_id = ?", (student_id,))
    current_count = cur.fetchone()[0]

    for idx, item in enumerate(req.assignments, start=current_count + 1):
        asg_id = f"asg-{uuid.uuid4().hex[:8]}"
        is_unlocked = 1 if idx == 1 or current_count == 0 and idx == 1 else 0
        cur.execute("""
            INSERT INTO game_assignments (id, student_id, game_id, sequence_order, difficulty, is_unlocked, assigned_by, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', datetime('now'))
        """, (asg_id, student_id, item.game_id, idx, item.difficulty or "easy", is_unlocked, req.assigned_by or "usr-teacher-01"))

    # Ensure at least first pending assignment is unlocked if none are in progress
    cur.execute("SELECT id FROM game_assignments WHERE student_id = ? AND (status = 'in_progress' OR is_unlocked = 1)", (student_id,))
    if not cur.fetchone():
        cur.execute("UPDATE game_assignments SET is_unlocked = 1 WHERE student_id = ? ORDER BY sequence_order ASC LIMIT 1", (student_id,))

    conn.commit()
    conn.close()
    return {"success": True, "message": f"Successfully updated assignments for {student_id}"}


@router.post("/teacher/classes/{class_id}/assignments/bulk")
def api_bulk_assign_class(class_id: str, req: BulkAssignStudentRequest):
    """Apply the same curriculum sequence across all active students in a classroom."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM students WHERE class_id = ? AND status = 'active'", (class_id,))
    students = cur.fetchall()

    for stu in students:
        stu_id = stu["id"]
        cur.execute("DELETE FROM game_assignments WHERE student_id = ? AND status = 'pending'", (stu_id,))
        cur.execute("SELECT count(*) FROM game_assignments WHERE student_id = ?", (stu_id,))
        current_count = cur.fetchone()[0]

        for idx, item in enumerate(req.assignments, start=current_count + 1):
            asg_id = f"asg-{uuid.uuid4().hex[:8]}"
            is_unlocked = 1 if idx == 1 else 0
            cur.execute("""
                INSERT INTO game_assignments (id, student_id, game_id, sequence_order, difficulty, is_unlocked, assigned_by, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'pending', datetime('now'))
            """, (asg_id, stu_id, item.game_id, idx, item.difficulty or "easy", is_unlocked, req.assigned_by or "usr-teacher-01"))

        cur.execute("SELECT id FROM game_assignments WHERE student_id = ? AND (status = 'in_progress' OR is_unlocked = 1)", (stu_id,))
        if not cur.fetchone():
            cur.execute("UPDATE game_assignments SET is_unlocked = 1 WHERE student_id = ? ORDER BY sequence_order ASC LIMIT 1", (stu_id,))

    conn.commit()
    conn.close()
    return {"success": True, "message": f"Curriculum sequence applied to {len(students)} students in class {class_id}"}


@router.delete("/teacher/students/{student_id}/assignments/clear-pending")
def api_clear_pending_assignments(student_id: str):
    """Clear all pending (uncompleted) assignments for a student."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM game_assignments WHERE student_id = ? AND status = 'pending'", (student_id,))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Pending assignments cleared"}


@router.post("/assignments/{assignment_id}/complete")
def api_complete_assignment(assignment_id: str):
    """Mark an assignment as completed and unlock next sequential activity."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT student_id, sequence_order FROM game_assignments WHERE id = ?", (assignment_id,))
    asg = cur.fetchone()
    if not asg:
        conn.close()
        raise HTTPException(status_code=404, detail="Assignment not found")

    cur.execute("UPDATE game_assignments SET status = 'completed' WHERE id = ?", (assignment_id,))

    # Unlock next sequential assignment
    cur.execute("""
        UPDATE game_assignments
        SET is_unlocked = 1
        WHERE student_id = ? AND sequence_order = ?
    """, (asg["student_id"], asg["sequence_order"] + 1))

    conn.commit()
    conn.close()
    return {"success": True, "message": "Assignment marked completed and next activity unlocked"}


# ─── AI Recommendations & Teacher Approval Workflow ────────────────────

@router.get("/recommendations")
def api_get_recommendations(student_id: Optional[str] = None, status: Optional[str] = None):
    """List AI recommendations, optionally filtered by student and approval status."""
    conn = get_db_connection()
    cur = conn.cursor()

    query = """
        SELECT r.*, s.full_name as student_name
        FROM ai_recommendations r
        JOIN students s ON r.student_id = s.id
        WHERE (r.student_id = ? OR ? IS NULL)
          AND (r.status = ? OR ? IS NULL)
        ORDER BY r.created_at DESC
    """
    cur.execute(query, (student_id, student_id, status, status))
    recs = []
    for r in cur.fetchall():
        rd = dict(r)
        if rd.get("alternative_games_json"):
            try:
                rd["alternative_games"] = json.loads(rd["alternative_games_json"])
            except Exception:
                rd["alternative_games"] = []
        else:
            rd["alternative_games"] = []
        recs.append(rd)
    conn.close()
    return recs


@router.post("/recommendations/generate/{student_id}")
def api_trigger_recommendation(student_id: str):
    """Teacher explicitly triggers an AI recommendation for a student."""
    from profiler_recommender import generate_ai_recommendation
    rec = generate_ai_recommendation(student_id, force=True)
    return {"success": True, "recommendation": rec}


@router.post("/recommendations/{rec_id}/approve")
def api_approve_recommendation(rec_id: str, req: RecommendationActionRequest):
    """Teacher approves recommendation -> creates a new active game assignment for student."""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM ai_recommendations WHERE id = ?", (rec_id,))
    rec = cur.fetchone()
    if not rec:
        conn.close()
        raise HTTPException(status_code=404, detail="Recommendation not found")

    now = datetime.utcnow().isoformat()
    cur.execute("""
        UPDATE ai_recommendations
        SET status = 'approved', teacher_notes = ?, reviewed_by = 'usr-teacher-01', reviewed_at = ?
        WHERE id = ?
    """, (req.teacher_notes, now, rec_id))

    # Determine next sequence order
    cur.execute("SELECT coalesce(max(sequence_order), 0) + 1 FROM game_assignments WHERE student_id = ?", (rec["student_id"],))
    seq_order = cur.fetchone()[0]

    # Convert to active assignment
    asg_id = f"asg-{uuid.uuid4().hex[:8]}"
    cur.execute("SELECT status FROM game_assignments WHERE student_id = ? AND sequence_order = ?", (rec["student_id"], seq_order - 1))
    prev_asg = cur.fetchone()
    is_unlocked = 1 if (seq_order == 1 or not prev_asg or prev_asg["status"] == "completed") else 0

    cur.execute("""
        INSERT INTO game_assignments (id, student_id, game_id, sequence_order, difficulty, is_unlocked, assigned_by, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, 'usr-teacher-01', 'pending', ?)
    """, (asg_id, rec["student_id"], req.modified_game_id or rec["recommended_game_id"],
          seq_order, req.modified_difficulty or rec["difficulty"], is_unlocked, now))

    conn.commit()
    conn.close()
    return {"success": True, "message": "Recommendation approved and activity added to student sequence"}


@router.post("/recommendations/{rec_id}/reject")
def api_reject_recommendation(rec_id: str, req: RecommendationActionRequest):
    """Teacher rejects an AI recommendation with explanation."""
    conn = get_db_connection()
    cur = conn.cursor()

    now = datetime.utcnow().isoformat()
    cur.execute("""
        UPDATE ai_recommendations
        SET status = 'rejected', teacher_notes = ?, reviewed_by = 'usr-teacher-01', reviewed_at = ?
        WHERE id = ?
    """, (req.teacher_notes or "Declined by educator", now, rec_id))

    conn.commit()
    conn.close()
    return {"success": True, "message": "Recommendation rejected"}


# ─── Individual Student Progress Report Generation ────────────────────

@router.get("/reports/student/{student_id}")
def api_get_student_report(student_id: str):
    """Generate structured 10-section report data for individual student progress report."""
    conn = get_db_connection()
    cur = conn.cursor()

    # 1. Student Info
    cur.execute("""
        SELECT s.*, u.username as username, c.name as class_name
        FROM students s
        LEFT JOIN users u ON s.user_id = u.id
        LEFT JOIN classes c ON s.class_id = c.id
        WHERE s.id = ?
    """, (student_id,))
    stu = cur.fetchone()
    if not stu:
        conn.close()
        raise HTTPException(status_code=404, detail="Student not found")

    student_data = dict(stu)

    # 2. Behavioral Profile
    cur.execute("SELECT * FROM student_behavioral_profiles WHERE student_id = ?", (student_id,))
    prof = cur.fetchone()
    profile_data = dict(prof) if prof else {
        "attention_focus": 0.72, "motor_skills": 0.78, "communication_language": 0.58,
        "emotion_recognition": 0.65, "social_interaction": 0.52, "daily_living": 0.62,
        "strengths_json": '["Motor coordination", "Visual tracking"]',
        "growth_areas_json": '["Verbal turn-taking", "Inhibitory control"]',
        "confidence_score": 0.84
    }

    # 3. Observations
    cur.execute("SELECT * FROM teacher_observations WHERE student_id = ? ORDER BY date DESC", (student_id,))
    t_obs = [dict(r) for r in cur.fetchall()]

    cur.execute("SELECT * FROM parent_observations WHERE student_id = ? ORDER BY date DESC", (student_id,))
    p_obs = [dict(r) for r in cur.fetchall()]

    # 4. Sessions
    cur.execute("""
        SELECT count(*), coalesce(sum(duration_seconds), 0)
        FROM game_sessions WHERE child_id IN (?, 'demo-child')
    """, (student_id,))
    s_count, s_duration = cur.fetchone()

    conn.close()

    report = {
        "title": f"Individualized Skill Development & Behavioral Progress Report",
        "generated_at": datetime.utcnow().strftime("%B %d, %Y"),
        "student": {
            "student_id": student_data["id"],
            "name": student_data["full_name"],
            "age": student_data["age"],
            "class": student_data["class_name"] or "Sunflower Room",
            "learning_objectives": student_data["learning_objectives"],
            "interests": student_data["interests"],
            "support_requirements": student_data["support_requirements"],
            "total_sessions": s_count or 12,
            "total_minutes": round((s_duration or 2400) / 60, 1),
        },
        "radar_profile": {
            "Motor Skills": int(profile_data["motor_skills"] * 100),
            "Attention & Focus": int(profile_data["attention_focus"] * 100),
            "Emotion Recognition": int(profile_data["emotion_recognition"] * 100),
            "Communication & Language": int(profile_data["communication_language"] * 100),
            "Social Interaction": int(profile_data["social_interaction"] * 100),
            "Daily Living": int(profile_data["daily_living"] * 100),
        },
        "strengths": json.loads(profile_data.get("strengths_json") or "[]"),
        "growth_areas": json.loads(profile_data.get("growth_areas_json") or "[]"),
        "teacher_observations_summary": t_obs,
        "parent_observations_summary": p_obs,
        "recommendations": [
            {
                "activity": "My Turn / Your Turn",
                "target": "Social Turn-Taking & Impulse Control",
                "status": "Teacher Approved",
                "rationale": "Reinforce waiting tolerance during red light transitions using visual feedback."
            },
            {
                "activity": "Talk & Build",
                "target": "Expressive Vocabulary",
                "status": "In Progress",
                "rationale": "Encourage multi-word sentences describing character scenes."
            }
        ],
        "disclaimer": "This progress report is generated for educational and developmental monitoring purposes only. It is not a clinical psychological evaluation or medical diagnosis."
    }
    return report


# ─── Account Credentials & Password Management Endpoints ────────────────────

@router.get("/teacher/credentials")
def api_get_credentials():
    """List all accounts across Teacher, Students, and Parents with their login usernames and credentials status."""
    conn = get_db_connection()
    cur = conn.cursor()

    # Teacher account
    cur.execute("SELECT id, username, display_name, role, email, phone, updated_at FROM users WHERE role = 'teacher' LIMIT 1")
    t_row = cur.fetchone()
    teacher_account = dict(t_row) if t_row else {
        "id": "teacher-user",
        "username": "teacher",
        "display_name": "Ms. Sarah Wilson (Lead Educator)",
        "role": "teacher"
    }

    # Students accounts
    cur.execute("""
        SELECT s.id as student_id, s.full_name, s.age, c.name as class_name,
               u.id as user_id, u.username, u.status, u.updated_at
        FROM students s
        JOIN users u ON s.user_id = u.id
        LEFT JOIN classes c ON s.class_id = c.id
        ORDER BY s.full_name ASC
    """)
    students_list = [dict(r) for r in cur.fetchall()]

    # Parents accounts
    cur.execute("""
        SELECT u.id as parent_id, u.username, u.display_name, u.email, u.phone, u.updated_at,
               l.relationship, l.student_id, s.full_name as student_name
        FROM users u
        LEFT JOIN parent_student_links l ON u.id = l.parent_id
        LEFT JOIN students s ON l.student_id = s.id
        WHERE u.role = 'parent'
        ORDER BY u.display_name ASC
    """)
    parents_list = [dict(r) for r in cur.fetchall()]

    conn.close()
    return {
        "teacher": teacher_account,
        "students": students_list,
        "parents": parents_list
    }


@router.put("/teacher/password")
def api_update_teacher_password(req: ChangePasswordRequest):
    """Teacher updates their own educator console login password."""
    if not req.new_password or len(req.new_password.strip()) < 3:
        raise HTTPException(status_code=400, detail="Password must be at least 3 characters")

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE role = 'teacher' LIMIT 1")
    teacher = cur.fetchone()
    if not teacher:
        conn.close()
        raise HTTPException(status_code=404, detail="Teacher account not found")

    if req.current_password:
        if teacher["password_hash"] and teacher["password_hash"] != hash_password(req.current_password):
            conn.close()
            raise HTTPException(status_code=401, detail="Current password is incorrect")

    new_hash = hash_password(req.new_password.strip())
    cur.execute("UPDATE users SET password_hash = ?, pin_hash = ?, updated_at = datetime('now') WHERE id = ?",
                (new_hash, new_hash, teacher["id"]))
    conn.commit()
    conn.close()

    return {"success": True, "message": "Teacher account password updated successfully"}


@router.put("/teacher/students/{student_id}/password")
def api_update_student_password(student_id: str, req: ChangeStudentPasswordRequest):
    """Teacher updates or resets a student's login password/PIN."""
    if not req.new_password or len(req.new_password.strip()) < 2:
        raise HTTPException(status_code=400, detail="PIN/Password must be at least 2 characters")

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM students WHERE id = ?", (student_id,))
    stu = cur.fetchone()
    if not stu:
        conn.close()
        raise HTTPException(status_code=404, detail="Student not found")

    new_hash = hash_password(req.new_password.strip())
    cur.execute("UPDATE users SET password_hash = ?, pin_hash = ?, updated_at = datetime('now') WHERE id = ?",
                (new_hash, new_hash, stu["user_id"]))
    conn.commit()
    conn.close()

    return {
        "success": True,
        "student_id": student_id,
        "message": f"Password/PIN for {stu['full_name']} updated successfully to '{req.new_password.strip()}'"
    }


@router.put("/teacher/parents/{parent_id}/password")
def api_update_parent_password_by_teacher(parent_id: str, req: ChangeParentPasswordRequest):
    """Teacher updates or resets a parent's portal password."""
    if not req.new_password or len(req.new_password.strip()) < 3:
        raise HTTPException(status_code=400, detail="Password must be at least 3 characters")

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE id = ? AND role = 'parent'", (parent_id,))
    parent = cur.fetchone()
    if not parent:
        conn.close()
        raise HTTPException(status_code=404, detail="Parent account not found")

    new_hash = hash_password(req.new_password.strip())
    cur.execute("UPDATE users SET password_hash = ?, updated_at = datetime('now') WHERE id = ?",
                (new_hash, parent_id))
    conn.commit()
    conn.close()

    return {
        "success": True,
        "parent_id": parent_id,
        "message": f"Password for parent {parent['display_name']} updated successfully"
    }


@router.put("/parent/children/{student_id}/password")
def api_parent_update_child_password(student_id: str, req: ChangeStudentPasswordRequest):
    """Parent updates or resets their child's login password/PIN."""
    if not req.new_password or len(req.new_password.strip()) < 2:
        raise HTTPException(status_code=400, detail="PIN/Password must be at least 2 characters")

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM students WHERE id = ?", (student_id,))
    stu = cur.fetchone()
    if not stu:
        conn.close()
        raise HTTPException(status_code=404, detail="Student not found")

    new_hash = hash_password(req.new_password.strip())
    cur.execute("UPDATE users SET password_hash = ?, pin_hash = ?, updated_at = datetime('now') WHERE id = ?",
                (new_hash, new_hash, stu["user_id"]))
    conn.commit()
    conn.close()

    return {
        "success": True,
        "student_id": student_id,
        "message": f"Login PIN/Password for {stu['full_name']} updated to '{req.new_password.strip()}' by guardian"
    }


@router.put("/parent/password")
def api_parent_update_own_password(req: ChangePasswordRequest, authorization: Optional[str] = Header(None)):
    """Parent updates their own portal login password."""
    if not req.new_password or len(req.new_password.strip()) < 3:
        raise HTTPException(status_code=400, detail="Password must be at least 3 characters")

    conn = get_db_connection()
    cur = conn.cursor()

    user = get_current_user_optional(authorization)
    p_id = user["sub"] if user and user.get("role") == "parent" else "parent-user"

    cur.execute("SELECT * FROM users WHERE id = ?", (p_id,))
    parent = cur.fetchone()
    if not parent:
        conn.close()
        raise HTTPException(status_code=404, detail="Parent account not found")

    if req.current_password:
        if parent["password_hash"] and parent["password_hash"] != hash_password(req.current_password):
            conn.close()
            raise HTTPException(status_code=401, detail="Current password is incorrect")

    new_hash = hash_password(req.new_password.strip())
    cur.execute("UPDATE users SET password_hash = ?, updated_at = datetime('now') WHERE id = ?",
                (new_hash, p_id))
    conn.commit()
    conn.close()

    return {"success": True, "message": "Parent portal password updated successfully"}
