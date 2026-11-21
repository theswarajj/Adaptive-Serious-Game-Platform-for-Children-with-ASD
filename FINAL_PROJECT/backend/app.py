"""
FastAPI Backend — Adaptive Multimodal Serious-Game Platform
Main application entry point.
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from enum import Enum
import uuid
import sqlite3
import os
import asyncio
import json
import time

from fastapi.responses import StreamingResponse
from student_model import StudentModel, SKILLS
from adaptation_engine import AdaptationEngine
from game_launcher import launch_game, stop_game, get_game_status
from game_streamer import stream_manager
from db_schema import init_enhanced_db, seed_demo_data
from api_platform import router as platform_router

# ─── App Configuration ───────────────────────────────────────────────

app = FastAPI(
    title="Autism Game Platform API",
    description="Backend for the Adaptive Multimodal Serious-Game Platform",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(platform_router)

# Initialize schema and seed data on startup
init_enhanced_db()
seed_demo_data()

# ─── Database Setup ──────────────────────────────────────────────────

DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "platform.db"))


def get_db():
    """Get a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Initialize the database schema."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            display_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('caregiver', 'therapist', 'developer')),
            pin_hash TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS child_profiles (
            id TEXT PRIMARY KEY,
            caregiver_id TEXT NOT NULL REFERENCES users(id),
            display_name TEXT NOT NULL,
            avatar TEXT DEFAULT 'default',
            theme TEXT DEFAULT 'calm',
            settings_json TEXT DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS game_sessions (
            id TEXT PRIMARY KEY,
            child_id TEXT NOT NULL REFERENCES child_profiles(id),
            game_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'created' CHECK(status IN ('created', 'running', 'completed', 'abandoned', 'error')),
            input_mode TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            started_at TEXT,
            ended_at TEXT,
            duration_seconds REAL,
            is_demo INTEGER DEFAULT 0,
            idempotency_key TEXT UNIQUE,
            app_version TEXT,
            game_version TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS game_events (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL REFERENCES game_sessions(id),
            game_id TEXT NOT NULL,
            event_type TEXT NOT NULL,
            payload_json TEXT DEFAULT '{}',
            elapsed_seconds REAL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS performance_metrics (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL REFERENCES game_sessions(id) UNIQUE,
            game_id TEXT NOT NULL,
            child_id TEXT NOT NULL REFERENCES child_profiles(id),
            metrics_json TEXT NOT NULL DEFAULT '{}',
            schema_version INTEGER DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS student_model_snapshots (
            id TEXT PRIMARY KEY,
            child_id TEXT NOT NULL REFERENCES child_profiles(id),
            skills_json TEXT NOT NULL DEFAULT '{}',
            per_game_json TEXT NOT NULL DEFAULT '{}',
            recent_history_json TEXT DEFAULT '[]',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS adaptation_decisions (
            id TEXT PRIMARY KEY,
            child_id TEXT NOT NULL REFERENCES child_profiles(id),
            session_id TEXT REFERENCES game_sessions(id),
            game_id TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            input_mode TEXT NOT NULL,
            state_json TEXT NOT NULL DEFAULT '{}',
            eligible_actions_json TEXT DEFAULT '[]',
            chosen_action TEXT NOT NULL,
            source TEXT NOT NULL CHECK(source IN ('rule-based', 'learned-policy')),
            policy_version TEXT,
            visit_count INTEGER,
            reason TEXT,
            status TEXT DEFAULT 'applied' CHECK(status IN ('applied', 'shadow-only', 'blocked', 'declined')),
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS consent_records (
            id TEXT PRIMARY KEY,
            child_id TEXT NOT NULL REFERENCES child_profiles(id),
            consent_type TEXT NOT NULL,
            granted INTEGER NOT NULL DEFAULT 0,
            version INTEGER NOT NULL DEFAULT 1,
            granted_by TEXT REFERENCES users(id),
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS goals (
            id TEXT PRIMARY KEY,
            child_id TEXT NOT NULL REFERENCES child_profiles(id),
            title TEXT NOT NULL,
            description TEXT,
            skill_area TEXT,
            target_json TEXT DEFAULT '{}',
            status TEXT DEFAULT 'active' CHECK(status IN ('active', 'achieved', 'archived')),
            review_date TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS plans (
            id TEXT PRIMARY KEY,
            child_id TEXT NOT NULL REFERENCES child_profiles(id),
            date TEXT NOT NULL,
            activities_json TEXT NOT NULL DEFAULT '[]',
            settings_json TEXT DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS settings_profiles (
            id TEXT PRIMARY KEY,
            child_id TEXT NOT NULL REFERENCES child_profiles(id) UNIQUE,
            audio_muted INTEGER DEFAULT 0,
            audio_volume REAL DEFAULT 0.7,
            speech_prompts INTEGER DEFAULT 1,
            reduce_motion INTEGER DEFAULT 0,
            celebration TEXT DEFAULT 'gentle',
            response_window_multiplier REAL DEFAULT 1.0,
            hide_timers INTEGER DEFAULT 1,
            text_scale REAL DEFAULT 1.0,
            font TEXT DEFAULT 'default',
            contrast TEXT DEFAULT 'standard',
            handedness TEXT DEFAULT 'either',
            preferred_input_mode TEXT DEFAULT 'pointer',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );

        CREATE INDEX IF NOT EXISTS idx_sessions_child ON game_sessions(child_id);
        CREATE INDEX IF NOT EXISTS idx_sessions_game ON game_sessions(game_id);
        CREATE INDEX IF NOT EXISTS idx_events_session ON game_events(session_id);
        CREATE INDEX IF NOT EXISTS idx_metrics_child ON performance_metrics(child_id);
        CREATE INDEX IF NOT EXISTS idx_model_child ON student_model_snapshots(child_id);

        -- Default seed users and demo child
        INSERT OR IGNORE INTO users (id, username, display_name, role)
        VALUES ('dev-user', 'developer', 'Developer', 'developer');

        INSERT OR IGNORE INTO users (id, username, display_name, role)
        VALUES ('parent-user', 'parent', 'Sarah (Parent)', 'caregiver');

        INSERT OR IGNORE INTO users (id, username, display_name, role)
        VALUES ('teacher-user', 'teacher', 'Ms. Davis (Teacher)', 'therapist');

        INSERT OR IGNORE INTO child_profiles (id, caregiver_id, display_name, avatar)
        VALUES ('demo-child', 'dev-user', 'Alex', 'default');

        INSERT OR IGNORE INTO settings_profiles (id, child_id)
        VALUES ('demo-settings', 'demo-child');
    """)
    
    conn.commit()
    conn.close()


# ─── Enums and Schemas ───────────────────────────────────────────────

class RuntimeKind(str, Enum):
    WEB_EMBEDDED = "web-embedded"
    PYTHON_LAUNCHED = "python-launched"
    PYTHON_STREAMED = "python-streamed"

class InputMode(str, Enum):
    CAMERA_HAND = "camera-hand"
    CAMERA_POSE = "camera-pose"
    CAMERA_FACE = "camera-face"
    SPEECH = "speech"
    POINTER = "pointer"
    TOUCH = "touch"
    KEYBOARD = "keyboard"
    CHOICE_SELECT = "choice-select"

class SessionStatus(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    ERROR = "error"

class GameAvailability(str, Enum):
    AVAILABLE = "available"
    NEEDS_ATTENTION = "needs-attention"
    PLANNED = "planned"
    UNAVAILABLE = "unavailable"


# ─── Game Catalogue ──────────────────────────────────────────────────

GAME_CATALOGUE = [
    {
        "id": "bubble-hunt", "level": 1, "name": "Bubble Hunt",
        "description": "Pop colorful bubbles by pinching with your fingers. Practice your hand-eye coordination and attention skills.",
        "runtime": "python-launched",
        "inputModes": ["camera-hand", "pointer"],
        "needs": {"camera": True, "microphone": False, "webgl": False},
        "difficultyScale": ["standard"],
        "status": "available",
        "sourcePath": "LEVEL_1/bubble_hunt.py",
        "version": "1.0.0",
        "icon": "🫧",
    },
    {
        "id": "follow-the-star", "level": 1, "name": "Follow the Star",
        "description": "Move your head to follow a friendly face target on screen. Practice visual tracking and motor control.",
        "runtime": "python-launched",
        "inputModes": ["camera-face", "pointer"],
        "needs": {"camera": True, "microphone": False},
        "difficultyScale": ["standard"],
        "status": "available",
        "sourcePath": "LEVEL_1/follow_the_star.py",
        "version": "1.0.0",
        "icon": "⭐",
    },
    {
        "id": "pattern-trail", "level": 1, "name": "Pattern Trail",
        "description": "Trace letters and numbers with your fingertip. Practice path tracking and motor precision.",
        "runtime": "python-launched",
        "inputModes": ["camera-hand", "pointer"],
        "needs": {"camera": True, "microphone": False},
        "difficultyScale": ["see", "follow", "control"],
        "status": "available",
        "sourcePath": "LEVEL_1/pattern_trail.py",
        "version": "1.0.0",
        "icon": "✏️",
    },
    {
        "id": "emotion-mirror", "level": 2, "name": "Emotion Mirror",
        "description": "Match facial expressions shown on screen. Practice recognizing and imitating emotions.",
        "runtime": "python-launched",
        "inputModes": ["camera-face", "choice-select"],
        "needs": {"camera": True, "microphone": False},
        "difficultyScale": ["standard"],
        "status": "available",
        "sourcePath": "LEVEL_2/emotion_mirror.py",
        "version": "1.0.0",
        "icon": "🪞",
    },
    {
        "id": "body-says-it", "level": 2, "name": "Body Says It",
        "description": "Watch animated characters show body language and identify the emotion they express.",
        "runtime": "python-launched",
        "inputModes": ["camera-hand", "choice-select"],
        "needs": {"camera": True, "microphone": False},
        "difficultyScale": ["standard"],
        "status": "planned",
        "sourcePath": "LEVEL_2/body_says_it.py",
        "version": "1.0.0",
        "icon": "🧍",
    },
    {
        "id": "object-quest", "level": 2, "name": "Object Quest",
        "description": "See everyday objects and name them out loud. Practice observation and naming skills.",
        "runtime": "python-launched",
        "inputModes": ["speech", "keyboard", "choice-select"],
        "needs": {"camera": False, "microphone": True},
        "difficultyScale": ["easy", "medium", "hard"],
        "status": "planned",
        "sourcePath": "level_3/object_quest.py",
        "version": "1.0.0",
        "icon": "🔍",
    },
    {
        "id": "talk-and-build", "level": 3, "name": "Talk & Build",
        "description": "Answer questions about scenes using your voice or tap candy buttons. Practice forming answers and building sentences.",
        "runtime": "python-launched",
        "inputModes": ["speech", "pointer", "choice-select"],
        "needs": {"camera": True, "microphone": True},
        "difficultyScale": ["word", "phrase", "sentence"],
        "status": "available",
        "sourcePath": "LEVEL_3/talk_and_build.py",
        "version": "1.0.0",
        "icon": "🐿️",
    },
    {
        "id": "describe-the-scene", "level": 3, "name": "Describe the Scene",
        "description": "Watch video scenes and describe what is happening in your own words. Practice expressive storytelling and vocabulary.",
        "runtime": "python-launched",
        "inputModes": ["speech", "pointer", "choice-select"],
        "needs": {"camera": True, "microphone": True},
        "difficultyScale": ["easy", "medium", "hard"],
        "status": "available",
        "sourcePath": "LEVEL_3/describe_the_scene.py",
        "version": "1.0.0",
        "icon": "🎬",
    },
    {
        "id": "object-quest-see-say", "level": 3, "name": "Object Quest: See & Say",
        "description": "Watch everyday objects in high definition and say what they are. Practice rapid naming and vocabulary retrieval.",
        "runtime": "python-launched",
        "inputModes": ["speech", "pointer", "choice-select"],
        "needs": {"camera": True, "microphone": True},
        "difficultyScale": ["easy", "medium", "hard"],
        "status": "available",
        "sourcePath": "LEVEL_3/object_quest.py",
        "version": "1.0.0",
        "icon": "🔍",
    },
    {
        "id": "look-point-share", "level": 4, "name": "Look–Point–Share",
        "description": "Point to the animal that matches the instruction. Practice pointing and sharing attention.",
        "runtime": "python-launched",
        "inputModes": ["camera-hand", "pointer", "touch"],
        "needs": {"camera": True, "microphone": False},
        "difficultyScale": ["standard"],
        "status": "available",
        "sourcePath": "LEVEL4/look_point_and_share.py",
        "version": "1.0.0",
        "icon": "👆",
    },
    {
        "id": "my-turn-your-turn", "level": 4, "name": "My Turn / Your Turn",
        "description": "Wait for your turn! Keep still on red and raise your hand when green appears.",
        "runtime": "python-launched",
        "inputModes": ["camera-pose", "keyboard"],
        "needs": {"camera": True, "microphone": False},
        "difficultyScale": ["standard"],
        "status": "available",
        "sourcePath": "LEVEL4/my_turn_your_turn.py",
        "version": "1.0.0",
        "icon": "🔄",
    },
    {
        "id": "copy-my-move", "level": 4, "name": "Copy My Move",
        "description": "Watch the stick figure and hand gestures, then mirror and hold the pose!",
        "runtime": "python-launched",
        "inputModes": ["camera-pose", "camera-hand", "choice-select"],
        "needs": {"camera": True, "microphone": False},
        "difficultyScale": ["standard"],
        "status": "available",
        "sourcePath": "LEVEL4/copymymove.py",
        "version": "1.0.0",
        "icon": "🤹",
    },
    {
        "id": "school-day-simulator", "level": 5, "name": "School Day Simulator",
        "description": "Navigate a realistic school day routine, interact with teachers and classmates, ask for help, and participate in classroom activities.",
        "runtime": "web-embedded",
        "inputModes": ["keyboard", "pointer", "touch"],
        "needs": {"camera": False, "microphone": False, "webgl": True},
        "difficultyScale": ["easy", "medium", "hard"],
        "status": "available",
        "sourcePath": "LEVEL5/School Day Simulator.html",
        "version": "1.0.0",
        "icon": "🏫",
    },
    {
        "id": "community-travel-simulator", "level": 5, "name": "Community Travel Simulator",
        "description": "Navigate public transport, read route boards, interact politely with the driver, pay bus fare, and travel safely to community destinations.",
        "runtime": "web-embedded",
        "inputModes": ["keyboard", "pointer", "touch"],
        "needs": {"camera": False, "microphone": False, "webgl": True},
        "difficultyScale": ["easy", "medium", "hard"],
        "status": "available",
        "sourcePath": "LEVEL5/Community Travel Simulator.html",
        "version": "1.0.0",
        "icon": "🚌",
    },
    {
        "id": "shopping-adventure", "level": 5, "name": "Shopping Adventure",
        "description": "Explore a 3D supermarket (Supermarket Adventure), collect items from your shopping list, chat with the cashier, and pay for your groceries.",
        "runtime": "web-embedded",
        "inputModes": ["keyboard", "pointer", "touch"],
        "needs": {"camera": False, "microphone": False, "webgl": True},
        "difficultyScale": ["easy", "medium", "hard"],
        "status": "available",
        "sourcePath": "LEVEL5/Shopping Adventure.html",
        "version": "1.0.0",
        "icon": "🛒",
    },
]

LEVEL_INFO = {
    1: {"name": "Attention & Motor", "color": "#3B82F6", "description": "Build focus and hand-eye coordination"},
    2: {"name": "Emotion & Visual", "color": "#8B5CF6", "description": "Understand expressions and visual cues"},
    3: {"name": "Communication", "color": "#F59E0B", "description": "Practice speaking and describing"},
    4: {"name": "Social Interaction", "color": "#10B981", "description": "Learn turn-taking and sharing attention"},
    5: {"name": "Social Reasoning", "color": "#EF4444", "description": "Navigate real-world social situations"},
}

# ─── API Routes ───────────────────────────────────────────────────────

@app.on_event("startup")
def startup():
    init_db()


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.get("/api/games")
async def get_games():
    """Return the full game catalogue."""
    return {"games": GAME_CATALOGUE, "levels": LEVEL_INFO}


@app.get("/api/games/{game_id}")
async def get_game(game_id: str):
    """Return a single game definition."""
    effective_id = "shopping-adventure" if game_id == "supermarket-adventure" else game_id
    game = next((g for g in GAME_CATALOGUE if g["id"] == effective_id), None)
    if not game:
        raise HTTPException(status_code=404, detail=f"Game '{game_id}' not found")
    return game


# ─── Session API ─────────────────────────────────────────────────────

class CreateSessionRequest(BaseModel):
    child_id: str
    game_id: str
    input_mode: str = "pointer"
    difficulty: str = "easy"

class CreateSessionResponse(BaseModel):
    session_id: str
    session_token: str
    game_id: str
    input_mode: str
    difficulty: str
    expires_at: str

@app.post("/api/sessions", response_model=CreateSessionResponse)
def create_session(req: CreateSessionRequest, db=Depends(get_db)):
    """Create a new game session."""
    game = next((g for g in GAME_CATALOGUE if g["id"] == req.game_id), None)
    if not game:
        raise HTTPException(status_code=404, detail=f"Game '{req.game_id}' not found")
    
    session_id = str(uuid.uuid4())
    session_token = str(uuid.uuid4())
    expires_at = (datetime.utcnow() + timedelta(hours=2)).isoformat()
    
    db.execute(
        """INSERT INTO game_sessions (id, child_id, game_id, status, input_mode, difficulty, started_at)
           VALUES (?, ?, ?, 'running', ?, ?, datetime('now'))""",
        (session_id, req.child_id, req.game_id, req.input_mode, req.difficulty)
    )
    db.commit()
    
    return CreateSessionResponse(
        session_id=session_id,
        session_token=session_token,
        game_id=req.game_id,
        input_mode=req.input_mode,
        difficulty=req.difficulty,
        expires_at=expires_at,
    )


class CompleteSessionRequest(BaseModel):
    idempotency_key: str
    metrics: Dict[str, Any] = {}
    duration_seconds: float = 0
    status: str = "completed"

@app.post("/api/sessions/{session_id}/complete")
def complete_session(session_id: str, req: CompleteSessionRequest, db=Depends(get_db)):
    """Complete a game session with results."""
    row = db.execute("SELECT * FROM game_sessions WHERE id = ?", (session_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if row["status"] == "completed":
        return {"message": "Session already completed", "session_id": session_id}
    
    # Check idempotency
    existing = db.execute(
        "SELECT id FROM game_sessions WHERE idempotency_key = ?", (req.idempotency_key,)
    ).fetchone()
    if existing and existing["id"] != session_id:
        raise HTTPException(status_code=409, detail="Duplicate idempotency key")
    
    db.execute(
        """UPDATE game_sessions SET status = ?, ended_at = datetime('now'),
           duration_seconds = ?, idempotency_key = ? WHERE id = ?""",
        (req.status, req.duration_seconds, req.idempotency_key, session_id)
    )
    
    # Store metrics
    metrics_id = str(uuid.uuid4())
    db.execute(
        """INSERT INTO performance_metrics (id, session_id, game_id, child_id, metrics_json)
           VALUES (?, ?, ?, ?, ?)""",
        (metrics_id, session_id, row["game_id"], row["child_id"], json.dumps(req.metrics))
    )
    
    db.commit()
    return {"message": "Session completed", "session_id": session_id}


@app.post("/api/sessions/{session_id}/abandon")
def abandon_session(session_id: str, db=Depends(get_db)):
    """Mark a session as abandoned."""
    row = db.execute("SELECT * FROM game_sessions WHERE id = ?", (session_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Session not found")
    if row["status"] == "completed":
        raise HTTPException(status_code=400, detail="Cannot abandon a completed session")
    
    db.execute(
        "UPDATE game_sessions SET status = 'abandoned', ended_at = datetime('now') WHERE id = ?",
        (session_id,)
    )
    db.commit()
    return {"message": "Session abandoned", "session_id": session_id}


@app.get("/api/sessions")
def list_sessions(child_id: Optional[str] = None, game_id: Optional[str] = None, db=Depends(get_db)):
    """List game sessions with optional filters."""
    query = "SELECT * FROM game_sessions WHERE 1=1"
    params = []
    if child_id:
        query += " AND child_id = ?"
        params.append(child_id)
    if game_id:
        query += " AND game_id = ?"
        params.append(game_id)
    query += " ORDER BY created_at DESC LIMIT 100"
    
    rows = db.execute(query, params).fetchall()
    return {"sessions": [dict(r) for r in rows]}


# ─── Child Profile API ───────────────────────────────────────────────

class CreateChildRequest(BaseModel):
    display_name: str
    caregiver_id: str = "dev-user"

@app.post("/api/children")
def create_child(req: CreateChildRequest, db=Depends(get_db)):
    """Create a child profile."""
    child_id = str(uuid.uuid4())
    db.execute(
        "INSERT INTO child_profiles (id, caregiver_id, display_name) VALUES (?, ?, ?)",
        (child_id, req.caregiver_id, req.display_name)
    )
    
    # Create default settings
    settings_id = str(uuid.uuid4())
    db.execute(
        "INSERT INTO settings_profiles (id, child_id) VALUES (?, ?)",
        (settings_id, child_id)
    )
    
    db.commit()
    return {"child_id": child_id, "display_name": req.display_name}


@app.get("/api/children")
def list_children(db=Depends(get_db)):
    """List all child profiles."""
    rows = db.execute("SELECT * FROM child_profiles ORDER BY created_at DESC").fetchall()
    return {"children": [dict(r) for r in rows]}


@app.get("/api/children/{child_id}")
def get_child(child_id: str, db=Depends(get_db)):
    """Get a child profile."""
    row = db.execute("SELECT * FROM child_profiles WHERE id = ?", (child_id,)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Child not found")
    return dict(row)


# ─── Progress API ────────────────────────────────────────────────────

@app.get("/api/progress/{child_id}")
def get_progress(child_id: str, db=Depends(get_db)):
    """Get progress summary for a child."""
    sessions = db.execute(
        """SELECT game_id, status, difficulty, input_mode, duration_seconds, created_at
           FROM game_sessions WHERE child_id = ? ORDER BY created_at DESC LIMIT 50""",
        (child_id,)
    ).fetchall()
    
    total = len(sessions)
    completed = sum(1 for s in sessions if s["status"] == "completed")
    
    games_played = {}
    for s in sessions:
        gid = s["game_id"]
        if gid not in games_played:
            games_played[gid] = {"total": 0, "completed": 0}
        games_played[gid]["total"] += 1
        if s["status"] == "completed":
            games_played[gid]["completed"] += 1
    
    return {
        "child_id": child_id,
        "total_sessions": total,
        "completed_sessions": completed,
        "games_played": games_played,
        "recent_sessions": [dict(s) for s in sessions[:10]],
    }


# ─── Dev Mode ─────────────────────────────────────────────────────────

@app.post("/api/dev/seed")
def seed_dev_data(db=Depends(get_db)):
    """Seed development data. Marked is_demo=true."""
    # Create dev user
    db.execute(
        """INSERT OR IGNORE INTO users (id, username, display_name, role)
           VALUES ('dev-user', 'developer', 'Developer', 'developer')"""
    )
    
    # Create demo child
    db.execute(
        """INSERT OR IGNORE INTO child_profiles (id, caregiver_id, display_name, avatar)
           VALUES ('demo-child', 'dev-user', 'Alex', 'default')"""
    )
    
    # Create default settings for demo child
    db.execute(
        """INSERT OR IGNORE INTO settings_profiles (id, child_id)
           VALUES ('demo-settings', 'demo-child')"""
    )
    
    db.commit()
    return {"message": "Dev seed data created", "child_id": "demo-child", "is_demo": True}


# ─── Student Model API ───────────────────────────────────────────────

def _get_student_model(child_id: str, db) -> StudentModel:
    """Load or create a student model for a child."""
    row = db.execute(
        "SELECT skills_json FROM student_model_snapshots WHERE child_id = ? ORDER BY created_at DESC LIMIT 1",
        (child_id,)
    ).fetchone()
    if row and row["skills_json"]:
        return StudentModel.from_json(row["skills_json"])
    return StudentModel()


def _save_student_model(child_id: str, model: StudentModel, db):
    """Save a student model snapshot."""
    # Ensure child profile exists
    db.execute(
        """INSERT OR IGNORE INTO child_profiles (id, caregiver_id, display_name)
           VALUES (?, 'dev-user', 'Alex')""",
        (child_id,)
    )
    snap_id = str(uuid.uuid4())
    db.execute(
        "INSERT INTO student_model_snapshots (id, child_id, skills_json) VALUES (?, ?, ?)",
        (snap_id, child_id, model.to_json())
    )


def _get_adaptation_engine(child_id: str, db) -> AdaptationEngine:
    """Load or create an adaptation engine for a child."""
    row = db.execute(
        "SELECT state_json FROM adaptation_decisions WHERE child_id = ? ORDER BY created_at DESC LIMIT 1",
        (child_id,)
    ).fetchone()
    if row and row["state_json"]:
        try:
            return AdaptationEngine.from_json(row["state_json"])
        except Exception:
            pass
    return AdaptationEngine()


@app.get("/api/student-model/{child_id}")
def get_student_model(child_id: str, db=Depends(get_db)):
    """Get the current student model for a child."""
    model = _get_student_model(child_id, db)
    snapshot = model.get_snapshot()
    
    # Add level readiness
    levels = {}
    for level in range(1, 6):
        levels[level] = model.get_level_readiness(level)
    
    return {
        "child_id": child_id,
        "skills": snapshot["summary"],
        "level_readiness": levels,
    }


class UpdateModelRequest(BaseModel):
    game_id: str
    metrics: Dict[str, Any] = {}
    difficulty: str = "easy"


@app.post("/api/student-model/{child_id}/update")
def update_student_model(child_id: str, req: UpdateModelRequest, db=Depends(get_db)):
    """Update the student model after a session."""
    model = _get_student_model(child_id, db)
    changes = model.update_from_session(req.game_id, req.metrics, req.difficulty)
    _save_student_model(child_id, model, db)
    db.commit()

    # Sync platform: mark assignment complete, unlock next sequential game, recompute multi-source profile
    try:
        student_target = "STU-1001" if child_id in ("demo-child", "kid-01", "kid", "alex") else child_id
        
        # Check active assignment
        cur = db.cursor()
        cur.execute("""
            SELECT id, sequence_order FROM game_assignments
            WHERE (student_id = ? OR student_id = 'STU-1001')
              AND game_id = ? AND status != 'completed'
            LIMIT 1
        """, (student_target, req.game_id))
        matching_asg = cur.fetchone()
        if matching_asg:
            cur.execute("UPDATE game_assignments SET status = 'completed' WHERE id = ?", (matching_asg["id"],))
            # Unlock next sequential activity
            cur.execute("""
                UPDATE game_assignments
                SET is_unlocked = 1
                WHERE (student_id = ? OR student_id = 'STU-1001')
                  AND sequence_order = ?
            """, (student_target, matching_asg["sequence_order"] + 1))
            db.commit()

        from profiler_recommender import compute_and_save_behavioral_profile, generate_ai_recommendation
        compute_and_save_behavioral_profile(student_target, db_conn=db)
        generate_ai_recommendation(student_target, db_conn=db)
    except Exception as e:
        print(f"Platform model sync error: {e}")

    return {
        "child_id": child_id,
        "updated_skills": changes,
        "snapshot": model.get_snapshot()["summary"],
    }


# ─── Adaptation API ──────────────────────────────────────────────────

class AdaptationRequest(BaseModel):
    game_id: str
    current_difficulty: str = "easy"
    recent_performance: float = 0.5


@app.post("/api/adaptation/{child_id}/decide")
def get_adaptation_decision(child_id: str, req: AdaptationRequest, db=Depends(get_db)):
    """Get an adaptation decision for the next session."""
    model = _get_student_model(child_id, db)
    engine = _get_adaptation_engine(child_id, db)
    
    # Get relevant skill estimate (average of skills for this game)
    relevant_skills = []
    for skill_id, meta in SKILLS.items():
        if req.game_id in meta["games"]:
            skill_data = model.skills.get(skill_id, {})
            relevant_skills.append(skill_data.get("estimate", 0.0))
    
    avg_skill = sum(relevant_skills) / max(len(relevant_skills), 1)
    session_count = sum(
        s.get("session_count", 0) for s in model.skills.values()
        if any(req.game_id in SKILLS.get(sid, {}).get("games", []) for sid in [s.get("id", "")])
    )
    
    # Get total sessions for this game
    row = db.execute(
        "SELECT COUNT(*) as cnt FROM game_sessions WHERE child_id = ? AND game_id = ?",
        (child_id, req.game_id)
    ).fetchone()
    total_sessions = row["cnt"] if row else 0
    
    decision = engine.decide(
        skill_estimate=avg_skill,
        current_difficulty=req.current_difficulty,
        session_count=total_sessions,
        recent_performance=req.recent_performance,
    )
    
    # Log the decision
    dec_id = str(uuid.uuid4())
    db.execute(
        """INSERT INTO adaptation_decisions 
           (id, child_id, game_id, difficulty, input_mode, state_json, chosen_action, source, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (dec_id, child_id, req.game_id, decision["difficulty"], "pointer",
         engine.to_json(), decision["action"], decision["source"], decision.get("status", "applied"))
    )
    db.commit()
    
    return {
        "child_id": child_id,
        "game_id": req.game_id,
        "decision": decision,
    }


# ─── Level Progression API ───────────────────────────────────────────

@app.get("/api/levels/{child_id}")
def get_level_status(child_id: str, db=Depends(get_db)):
    """Get level unlock status for a child."""
    model = _get_student_model(child_id, db)
    
    levels = {}
    for level in range(1, 6):
        readiness = model.get_level_readiness(level)
        
        # Check if any game in this level was completed
        completed_sessions = db.execute(
            """SELECT COUNT(*) as cnt FROM game_sessions 
               WHERE child_id = ? AND status = 'completed' 
               AND game_id IN (SELECT game_id FROM game_sessions WHERE child_id = ?)""",
            (child_id, child_id)
        ).fetchone()
        
        levels[level] = {
            "unlocked": readiness["ready"],
            "readiness_score": readiness["score"],
            "skills": readiness["skills"],
        }
    
    # Level 1 is always unlocked
    levels[1]["unlocked"] = True
    
    return {"child_id": child_id, "levels": levels}


# ─── Consent API ─────────────────────────────────────────────────────

class ConsentRequest(BaseModel):
    consent_type: str  # "camera", "microphone", "data-collection"
    granted: bool


@app.post("/api/consent/{child_id}")
def record_consent(child_id: str, req: ConsentRequest, db=Depends(get_db)):
    """Record a consent decision."""
    consent_id = str(uuid.uuid4())
    db.execute(
        "INSERT INTO consent_records (id, child_id, consent_type, granted) VALUES (?, ?, ?, ?)",
        (consent_id, child_id, req.consent_type, 1 if req.granted else 0)
    )
    db.commit()
    return {"message": "Consent recorded", "consent_type": req.consent_type, "granted": req.granted}


@app.get("/api/consent/{child_id}")
def get_consent(child_id: str, db=Depends(get_db)):
    """Get current consent status for a child."""
    rows = db.execute(
        """SELECT consent_type, granted FROM consent_records 
           WHERE child_id = ? ORDER BY created_at DESC""",
        (child_id,)
    ).fetchall()
    
    consents = {}
    for row in rows:
        if row["consent_type"] not in consents:
            consents[row["consent_type"]] = bool(row["granted"])
    
    return {"child_id": child_id, "consents": consents}


# ─── Settings API ────────────────────────────────────────────────────

@app.get("/api/settings/{child_id}")
def get_settings(child_id: str, db=Depends(get_db)):
    """Get settings for a child."""
    row = db.execute(
        "SELECT * FROM settings_profiles WHERE child_id = ?",
        (child_id,)
    ).fetchone()
    if not row:
        return {"child_id": child_id, "settings": {}}
    return {"child_id": child_id, "settings": dict(row)}


class UpdateSettingsRequest(BaseModel):
    audio_muted: Optional[bool] = None
    audio_volume: Optional[float] = None
    reduce_motion: Optional[bool] = None
    celebration: Optional[str] = None
    response_window_multiplier: Optional[float] = None
    hide_timers: Optional[bool] = None
    text_scale: Optional[float] = None
    contrast: Optional[str] = None
    handedness: Optional[str] = None


@app.patch("/api/settings/{child_id}")
def update_settings(child_id: str, req: UpdateSettingsRequest, db=Depends(get_db)):
    """Update settings for a child."""
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    if not updates:
        return {"message": "No changes"}
    
    set_clauses = ", ".join(f"{k} = ?" for k in updates.keys())
    values = list(updates.values()) + [child_id]
    
    db.execute(
        f"UPDATE settings_profiles SET {set_clauses}, updated_at = datetime('now') WHERE child_id = ?",
        values
    )
    db.commit()
    return {"message": "Settings updated", "updated": list(updates.keys())}


# ─── Game Launcher API ───────────────────────────────────────────────

class LaunchGameRequest(BaseModel):
    child_id: str
    session_id: Optional[str] = None


@app.post("/api/games/{game_id}/launch")
def api_launch_game(game_id: str, req: LaunchGameRequest, db=Depends(get_db)):
    """Launch a Python game as an external process."""
    session_id = req.session_id or str(uuid.uuid4())
    # Ensure child profile exists
    db.execute(
        """INSERT OR IGNORE INTO child_profiles (id, caregiver_id, display_name)
           VALUES (?, 'dev-user', 'Alex')""",
        (req.child_id,)
    )
    db.commit()

    result = launch_game(game_id, req.child_id, session_id)
    
    if result.get("success"):
        # Create a session record with valid status ('running') and default input_mode
        db.execute(
            """INSERT OR IGNORE INTO game_sessions (id, child_id, game_id, status, input_mode, difficulty, started_at)
               VALUES (?, ?, ?, 'running', 'pointer', 'easy', datetime('now'))""",
            (session_id, req.child_id, game_id)
        )
        db.commit()
    
    return result


@app.post("/api/games/{game_id}/stop")
def api_stop_game(game_id: str, req: LaunchGameRequest):
    """Stop a running Python game or stream and return evaluation metrics."""
    stream_stats = stream_manager.stop_session(game_id, req.child_id)
    stop_res = stop_game(game_id, req.child_id)
    return {"success": True, "stats": stream_stats, **stop_res}


@app.get("/api/games/{game_id}/status/{child_id}")
def api_game_status(game_id: str, child_id: str):
    """Check if a Python game is running."""
    return get_game_status(game_id, child_id)


import queue

@app.get("/api/games/{game_id}/stream")
async def api_game_stream(game_id: str, child_id: str = "demo-child"):
    """Stream live OpenCV game video feed directly into the browser via MJPEG at solid 30+ FPS."""
    session = stream_manager.get_or_create(game_id, child_id)

    async def generate():
        last_id = -1
        try:
            while session.is_running:
                frame_bytes, frame_id = session.broadcaster.get_latest_with_id()
                if frame_bytes and frame_id != last_id:
                    last_id = frame_id
                    content_len = len(frame_bytes)
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n'
                           b'Content-Length: ' + str(content_len).encode() + b'\r\n\r\n' +
                           frame_bytes + b'\r\n')
                await asyncio.sleep(0.012)
        except (asyncio.CancelledError, GeneratorExit):
            pass
        except Exception:
            pass

    return StreamingResponse(
        generate(),
        media_type="multipart/x-mixed-replace; boundary=frame",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )


class ReloadRequest(BaseModel):
    child_id: str = "demo-child"


@app.post("/api/games/{game_id}/reload")
async def api_reload_game(game_id: str, req: ReloadRequest = ReloadRequest()):
    """Reload and restart that section of the game code and camera cleanly."""
    session = stream_manager.reload_session(game_id, req.child_id)
    return {"success": True, "message": "Game engine reloaded cleanly", "stats": session.get_stats()}


class ClickRequest(BaseModel):
    child_id: str = "demo-child"
    x_pct: float
    y_pct: float


@app.post("/api/games/{game_id}/click")
async def api_game_click(game_id: str, req: ClickRequest):
    """Handle click or touch directly on the live video game feed."""
    session = stream_manager.get(game_id, req.child_id)
    if session:
        session.handle_click(req.x_pct, req.y_pct)
        return {"success": True, "stats": session.get_stats()}
    return {"success": False, "error": "Game stream not active"}


class SpeechRequest(BaseModel):
    child_id: str = "demo-child"
    text: str


@app.post("/api/games/{game_id}/speech")
async def api_game_speech(game_id: str, req: SpeechRequest):
    """Handle speech input from browser speech recognition or mic."""
    session = stream_manager.get(game_id, req.child_id)
    if session and hasattr(session, "handle_speech_input"):
        session.handle_speech_input(req.text)
        return {"success": True, "stats": session.get_stats()}
    return {"success": False, "error": "Game stream not active or does not support speech"}


@app.get("/api/games/{game_id}/stream-status/{child_id}")
async def api_stream_status(game_id: str, child_id: str):
    """Get real-time stats from the active stream."""
    session = stream_manager.get(game_id, child_id)
    if session:
        return session.get_stats()
    key = f"{child_id}:{game_id}"
    last = stream_manager.last_completed_stats.get(key)
    if last:
        return {**last, "is_running": False}
    return {"is_running": False, "score": 0, "streak": 0}


# ─── Run ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True, reload_dirs=[backend_dir])
