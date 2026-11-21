"""
Database Schema & Migration Module for AI-Powered Adaptive Serious Game Platform
Defines and migrates all 12+ tables for Teachers, Students, Parents, Observations, Messages, Assignments, and AI Recommendations.
"""

import os
import sqlite3
import hashlib
import json
from datetime import datetime

DB_PATH = os.environ.get("DATABASE_PATH", os.path.join(os.path.dirname(__file__), "platform.db"))


def hash_password(password: str) -> str:
    """Deterministic salted SHA-256 hash for secure authentication."""
    salt = "asd_serious_games_salt_2026"
    return hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def migrate_users_table(conn):
    """Safely migrate users table to support teacher, student, and parent roles."""
    cur = conn.cursor()
    cur.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='users';")
    row = cur.fetchone()
    if row and "teacher" not in row[0]:
        print("Migrating users table to support 'teacher', 'student', and 'parent' roles...")
        conn.execute("PRAGMA foreign_keys=OFF;")
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users_new (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                display_name TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('teacher', 'student', 'parent', 'caregiver', 'therapist', 'developer')),
                password_hash TEXT,
                pin_hash TEXT,
                status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'inactive', 'suspended')),
                created_at TEXT NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
        """)
        
        cur.execute("""
            INSERT OR IGNORE INTO users_new (id, username, display_name, role, pin_hash, created_at, updated_at)
            SELECT id, username, display_name, role, pin_hash, created_at, updated_at FROM users;
        """)
        
        cur.execute("DROP TABLE users;")
        cur.execute("ALTER TABLE users_new RENAME TO users;")
        conn.commit()
        conn.execute("PRAGMA foreign_keys=ON;")
        print("Users table migration complete.")


def init_enhanced_db():
    """Create all core and extended tables with full relationships."""
    conn = get_db_connection()
    migrate_users_table(conn)

    cur = conn.cursor()

    # 1. Users Table (Ensured)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            display_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('teacher', 'student', 'parent', 'caregiver', 'therapist', 'developer')),
            password_hash TEXT,
            pin_hash TEXT,
            status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'inactive', 'suspended')),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """)

    # 2. Classes Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS classes (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            description TEXT,
            teacher_id TEXT NOT NULL REFERENCES users(id),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """)

    # 3. Students Table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id TEXT PRIMARY KEY,
            user_id TEXT UNIQUE REFERENCES users(id),
            full_name TEXT NOT NULL,
            dob TEXT,
            age INTEGER,
            class_id TEXT REFERENCES classes(id),
            learning_objectives TEXT,
            interests TEXT,
            preferred_activities TEXT,
            support_requirements TEXT,
            avatar TEXT DEFAULT 'default',
            status TEXT NOT NULL DEFAULT 'active' CHECK(status IN ('active', 'inactive')),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """)

    # 4. Backward-compatible child_profiles
    cur.execute("""
        CREATE TABLE IF NOT EXISTS child_profiles (
            id TEXT PRIMARY KEY,
            caregiver_id TEXT,
            display_name TEXT NOT NULL,
            avatar TEXT DEFAULT 'default',
            theme TEXT DEFAULT 'calm',
            settings_json TEXT DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """)

    # 5. Parent-Student Links
    cur.execute("""
        CREATE TABLE IF NOT EXISTS parent_student_links (
            id TEXT PRIMARY KEY,
            parent_id TEXT NOT NULL REFERENCES users(id),
            student_id TEXT NOT NULL REFERENCES students(id),
            relationship TEXT DEFAULT 'Parent/Guardian',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            UNIQUE(parent_id, student_id)
        );
    """)

    # 6. Teacher Classroom Observations
    cur.execute("""
        CREATE TABLE IF NOT EXISTS teacher_observations (
            id TEXT PRIMARY KEY,
            student_id TEXT NOT NULL REFERENCES students(id),
            teacher_id TEXT NOT NULL REFERENCES users(id),
            date TEXT NOT NULL,
            attention_rating INTEGER CHECK(attention_rating BETWEEN 1 AND 5),
            emotional_regulation INTEGER CHECK(emotional_regulation BETWEEN 1 AND 5),
            peer_interaction INTEGER CHECK(peer_interaction BETWEEN 1 AND 5),
            motor_skills INTEGER CHECK(motor_skills BETWEEN 1 AND 5),
            triggers_observed TEXT,
            strategies_used TEXT,
            notes TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """)

    # 7. Parent Home Observations
    cur.execute("""
        CREATE TABLE IF NOT EXISTS parent_observations (
            id TEXT PRIMARY KEY,
            student_id TEXT NOT NULL REFERENCES students(id),
            parent_id TEXT NOT NULL REFERENCES users(id),
            date TEXT NOT NULL,
            routine_transitions INTEGER CHECK(routine_transitions BETWEEN 1 AND 5),
            communication_attempts INTEGER CHECK(communication_attempts BETWEEN 1 AND 5),
            sensory_sensitivity INTEGER CHECK(sensory_sensitivity BETWEEN 1 AND 5),
            regulation_strategies TEXT,
            home_notes TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """)

    # 8. Parent Game Feedback
    cur.execute("""
        CREATE TABLE IF NOT EXISTS parent_game_feedback (
            id TEXT PRIMARY KEY,
            student_id TEXT NOT NULL REFERENCES students(id),
            game_id TEXT NOT NULL,
            parent_id TEXT NOT NULL REFERENCES users(id),
            enjoyment_rating INTEGER CHECK(enjoyment_rating BETWEEN 1 AND 5),
            frustration_level INTEGER CHECK(frustration_level BETWEEN 1 AND 5),
            assistance_needed INTEGER CHECK(assistance_needed BETWEEN 1 AND 5),
            comments TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """)

    # 9. Parent-Teacher Messaging
    cur.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            sender_id TEXT NOT NULL REFERENCES users(id),
            receiver_id TEXT NOT NULL REFERENCES users(id),
            student_id TEXT REFERENCES students(id),
            content TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """)

    # 10. Notifications
    cur.execute("""
        CREATE TABLE IF NOT EXISTS notifications (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL REFERENCES users(id),
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            body TEXT NOT NULL,
            link TEXT,
            is_read INTEGER DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """)

    # 11. Game Assignments (Sequenced Learning Path)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS game_assignments (
            id TEXT PRIMARY KEY,
            student_id TEXT NOT NULL REFERENCES students(id),
            game_id TEXT NOT NULL,
            sequence_order INTEGER DEFAULT 1,
            difficulty TEXT DEFAULT 'easy',
            is_unlocked INTEGER DEFAULT 1,
            assigned_by TEXT NOT NULL REFERENCES users(id),
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'in_progress', 'completed')),
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """)

    # 12. AI Recommendations with Teacher Approval Workflow
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ai_recommendations (
            id TEXT PRIMARY KEY,
            student_id TEXT NOT NULL REFERENCES students(id),
            recommended_game_id TEXT NOT NULL,
            difficulty TEXT DEFAULT 'easy',
            target_skill TEXT NOT NULL,
            rationale TEXT NOT NULL,
            confidence REAL DEFAULT 0.85,
            status TEXT DEFAULT 'pending_approval' CHECK(status IN ('pending_approval', 'approved', 'modified', 'rejected')),
            teacher_notes TEXT,
            reviewed_by TEXT REFERENCES users(id),
            reviewed_at TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """)

    # 13. Student Multi-Source Behavioral Profile (Radar 6-Domain)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS student_behavioral_profiles (
            id TEXT PRIMARY KEY,
            student_id TEXT NOT NULL REFERENCES students(id) UNIQUE,
            attention_focus REAL DEFAULT 0.65,
            motor_skills REAL DEFAULT 0.70,
            communication_language REAL DEFAULT 0.55,
            emotion_recognition REAL DEFAULT 0.60,
            social_interaction REAL DEFAULT 0.50,
            daily_living REAL DEFAULT 0.58,
            strengths_json TEXT DEFAULT '["Visual tracking", "Pincer motor grasp"]',
            growth_areas_json TEXT DEFAULT '["Verbal turn-taking", "Sensory transition"]',
            confidence_score REAL DEFAULT 0.82,
            last_calculated_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
    """)

    conn.commit()
    conn.close()
    print("Database schema successfully verified and updated.")


def seed_demo_data():
    """Seed initial Teacher, Student, Parent, Class, and Observation data."""
    conn = get_db_connection()
    cur = conn.cursor()

    now = datetime.utcnow().isoformat()

    # 1. Teacher Admin Account
    cur.execute("SELECT id FROM users WHERE username = 'teacher'")
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO users (id, username, display_name, role, password_hash, status, created_at)
            VALUES ('usr-teacher-01', 'teacher', 'Ms. Sarah Wilson (Lead Educator)', 'teacher', ?, 'active', ?)
        """, (hash_password("teacher123"), now))

    # 2. Parent Account
    cur.execute("SELECT id FROM users WHERE username = 'parent'")
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO users (id, username, display_name, role, password_hash, status, created_at)
            VALUES ('usr-parent-01', 'parent', 'Elena Miller (Parent)', 'parent', ?, 'active', ?)
        """, (hash_password("parent123"), now))

    # 3. Class
    cur.execute("SELECT id FROM classes WHERE id = 'cls-sunflower'")
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO classes (id, name, description, teacher_id, created_at)
            VALUES ('cls-sunflower', 'Sunflower Room (Early Primary)', 'Supportive classroom focusing on communication and joint attention.', 'usr-teacher-01', ?)
        """, (now,))

    # 4. Student 1: Alex Miller
    cur.execute("SELECT id FROM users WHERE username = 'alex'")
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO users (id, username, display_name, role, password_hash, pin_hash, status, created_at)
            VALUES ('usr-student-01', 'alex', 'Alex Miller', 'student', ?, ?, 'active', ?)
        """, (hash_password("1234"), hash_password("1234"), now))

    cur.execute("SELECT id FROM students WHERE id = 'STU-1001'")
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO students (id, user_id, full_name, dob, age, class_id, learning_objectives, interests, preferred_activities, support_requirements, avatar, status, created_at)
            VALUES ('STU-1001', 'usr-student-01', 'Alex Miller', '2019-04-12', 7, 'cls-sunflower',
                    'Develop joint attention, practice reciprocal waiting during turn-taking, expand expressive vocabulary in school settings.',
                    'Trains, Space, Dinosaurs, Bubbles',
                    'Bubble Hunt, Talk & Build, Shopping Adventure',
                    'Responds best to visual timers and gentle auditory chimes; avoid sudden loud buzzer sounds.',
                    'boy-1', 'active', ?)
        """, (now,))

    # Backward compatibility: child_profiles for Alex & demo-child
    cur.execute("""
        INSERT OR IGNORE INTO child_profiles (id, caregiver_id, display_name, avatar, theme, settings_json, created_at)
        VALUES ('STU-1001', 'usr-parent-01', 'Alex Miller', 'boy-1', 'calm', '{}', ?)
    """, (now,))
    cur.execute("""
        INSERT OR IGNORE INTO child_profiles (id, caregiver_id, display_name, avatar, theme, settings_json, created_at)
        VALUES ('demo-child', 'usr-parent-01', 'Alex Miller', 'boy-1', 'calm', '{}', ?)
    """, (now,))
    cur.execute("""
        INSERT OR IGNORE INTO child_profiles (id, caregiver_id, display_name, avatar, theme, settings_json, created_at)
        VALUES ('STU-1002', 'usr-parent-01', 'Maya Lin', 'girl-1', 'calm', '{}', ?)
    """, (now,))

    # 7. Initial Student Behavioral Profile for Alex
    cur.execute("SELECT id FROM student_behavioral_profiles WHERE student_id = 'STU-1001'")
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO student_behavioral_profiles (id, student_id, attention_focus, motor_skills, communication_language, emotion_recognition, social_interaction, daily_living, strengths_json, growth_areas_json, confidence_score, last_calculated_at, updated_at)
            VALUES ('prof-1001', 'STU-1001', 0.72, 0.78, 0.58, 0.65, 0.52, 0.62,
                    ?, ?, 0.84, ?, ?)
        """, (json.dumps(["Visual tracking and bubble popping", "Finger tracing precision", "Object recognition"]),
              json.dumps(["Patience during red-light turn waiting", "Multi-word verbal descriptions"]), now, now))

    # 8. Initial Teacher Observation
    cur.execute("SELECT id FROM teacher_observations WHERE student_id = 'STU-1001'")
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO teacher_observations (id, student_id, teacher_id, date, attention_rating, emotional_regulation, peer_interaction, motor_skills, triggers_observed, strategies_used, notes, created_at)
            VALUES ('obs-t-01', 'STU-1001', 'usr-teacher-01', '2026-11-17', 4, 4, 3, 5,
                    'Slight restlessness during group transitions',
                    'Provided visual countdown before activity switch',
                    'Alex demonstrated exceptional hand-eye coordination during Bubble Hunt and Pattern Trail. Was very engaged with the mascot in Talk & Build. Ready to practice turn-taking in My Turn / Your Turn.', ?)
        """, (now,))

    # 9. Initial Parent Home Observation
    cur.execute("SELECT id FROM parent_observations WHERE student_id = 'STU-1001'")
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO parent_observations (id, student_id, parent_id, date, routine_transitions, communication_attempts, sensory_sensitivity, regulation_strategies, home_notes, created_at)
            VALUES ('obs-p-01', 'STU-1001', 'usr-parent-01', '2026-11-16', 4, 5, 2,
                    'Listening to calm nature sounds',
                    'Alex enthusiastically talked about Nutmeg the squirrel at dinner and practiced naming fruits after playing. Slept well and smoothly transitioned from evening tablet time to bedtime.', ?)
        """, (now,))

    # 10. Initial Game Assignments for Alex
    cur.execute("SELECT id FROM game_assignments WHERE student_id = 'STU-1001'")
    if not cur.fetchone():
        assignments = [
            ('asg-01', 'STU-1001', 'bubble-hunt', 1, 'easy', 1, 'usr-teacher-01', 'completed'),
            ('asg-02', 'STU-1001', 'pattern-trail', 2, 'easy', 1, 'usr-teacher-01', 'completed'),
            ('asg-03', 'STU-1001', 'talk-and-build', 3, 'easy', 1, 'usr-teacher-01', 'in_progress'),
            ('asg-04', 'STU-1001', 'my-turn-your-turn', 4, 'easy', 1, 'usr-teacher-01', 'pending'),
            ('asg-05', 'STU-1001', 'shopping-adventure', 5, 'easy', 0, 'usr-teacher-01', 'pending'),
        ]
        cur.executemany("""
            INSERT INTO game_assignments (id, student_id, game_id, sequence_order, difficulty, is_unlocked, assigned_by, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        """, assignments)

    # 11. Initial AI Recommendation Awaiting Teacher Approval
    cur.execute("SELECT id FROM ai_recommendations WHERE student_id = 'STU-1001'")
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO ai_recommendations (id, student_id, recommended_game_id, difficulty, target_skill, rationale, confidence, status, created_at)
            VALUES ('rec-01', 'STU-1001', 'my-turn-your-turn', 'easy', 'Turn Taking & Impulse Control',
                    'Alex has demonstrated solid motor control (78%) and completed Level 1 & Level 3 communication tasks. Based on teacher observations noting restlessness during transitions, practicing the visual traffic-light waiting mechanic in My Turn / Your Turn will reinforce inhibitory control.',
                    0.88, 'pending_approval', ?)
        """, (now,))

    # 12. Initial Messages between Parent and Teacher
    cur.execute("SELECT id FROM messages WHERE student_id = 'STU-1001'")
    if not cur.fetchone():
        cur.execute("""
            INSERT INTO messages (id, sender_id, receiver_id, student_id, content, is_read, created_at)
            VALUES ('msg-01', 'usr-parent-01', 'usr-teacher-01', 'STU-1001',
                    'Hello Ms. Wilson, Alex really enjoyed the Talk & Build game this afternoon! We noticed he was much more communicative during dinner.', 1, ?)
        """, (now,))
        cur.execute("""
            INSERT INTO messages (id, sender_id, receiver_id, student_id, content, is_read, created_at)
            VALUES ('msg-02', 'usr-teacher-01', 'usr-parent-01', 'STU-1001',
                    'Wonderful news, Elena! I have assigned My Turn / Your Turn next to help with turn-taking and impulse control. Let me know how he does!', 0, ?)
        """, (now,))

    conn.commit()
    conn.close()
    print("Seed data successfully populated.")


if __name__ == "__main__":
    init_enhanced_db()
    seed_demo_data()
