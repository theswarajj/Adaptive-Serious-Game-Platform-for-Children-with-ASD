"""
Game Launcher — Manages launching Python games from the platform.
Handles subprocess spawning, status tracking, and clean termination.
"""

import subprocess
import os
import sys
import signal
import threading
from typing import Optional, Dict
from datetime import datetime


# Map game IDs to their Python script paths (relative to project root)
GAME_SCRIPTS = {
    "bubble-hunt": "LEVEL_1/bubble_hunt.py",
    "follow-the-star": "LEVEL_1/follow_the_star.py",
    "pattern-trail": "LEVEL_1/pattern_trail.py",
    "emotion-mirror": "LEVEL_2/emotion_mirror.py",
    "body-says-it": "LEVEL_2/body_says_it.py",
    "object-quest": "LEVEL_2/objectquest.py",
    "talk-and-build": "LEVEL_3/talk_and_build.py",
    "describe-the-scene": "LEVEL_3/describe_the_scene.py",
    "object-quest-see-say": "LEVEL_3/object_quest.py",
    "object-quest-3": "LEVEL_3/object_quest.py",
    "look-point-share": "LEVEL4/look_point_and_share.py",
    "my-turn-your-turn": "LEVEL4/my_turn_your_turn.py",
    "social-echo": "LEVEL4/copymymove.py",
    "copy-my-move": "LEVEL4/copymymove.py",
    "shopping-adventure": "LEVEL5/shopping_adventure.py",
    "supermarket-adventure": "LEVEL5/supermarket_adventure.py",
    "community-travel-simulator": "LEVEL5/community_travel_simulator.py",
    "school-day-simulator": "LEVEL5/school_day_simulator.py",
}

# Track running game processes
_running_games: Dict[str, Dict] = {}


def get_project_root() -> str:
    """Get the project root directory (parent of FINAL/)."""
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def launch_game(game_id: str, child_id: str, session_id: str) -> Dict:
    """
    Launch a Python game as a subprocess.
    Returns launch status and process info.
    """
    if game_id not in GAME_SCRIPTS:
        return {
            "success": False,
            "error": f"Unknown game: {game_id}",
            "game_id": game_id,
        }
    
    # Check if game is already running for this child
    key = f"{child_id}:{game_id}"
    if key in _running_games:
        proc_info = _running_games[key]
        if proc_info.get("process") and proc_info["process"].poll() is None:
            return {
                "success": True,
                "already_running": True,
                "game_id": game_id,
                "session_id": proc_info.get("session_id"),
                "pid": proc_info["process"].pid,
            }
    
    # Build the full script path
    project_root = get_project_root()
    script_path = os.path.normpath(os.path.join(project_root, GAME_SCRIPTS[game_id]))
    
    if not os.path.exists(script_path):
        return {
            "success": False,
            "error": f"Script not found: {script_path}",
            "game_id": game_id,
        }
    
    try:
        # Launch the game in a new window with its own console
        python_exe = sys.executable
        process = subprocess.Popen(
            [python_exe, script_path],
            cwd=os.path.dirname(script_path),
            creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0,
        )
        
        # Track the process
        _running_games[key] = {
            "process": process,
            "game_id": game_id,
            "child_id": child_id,
            "session_id": session_id,
            "started_at": datetime.utcnow().isoformat(),
            "pid": process.pid,
        }
        
        # Start a thread to monitor the process
        def monitor():
            process.wait()
            if key in _running_games:
                _running_games[key]["ended_at"] = datetime.utcnow().isoformat()
                _running_games[key]["return_code"] = process.returncode
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
        
        return {
            "success": True,
            "game_id": game_id,
            "session_id": session_id,
            "pid": process.pid,
            "script": GAME_SCRIPTS[game_id],
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "game_id": game_id,
        }


def stop_game(game_id: str, child_id: str) -> Dict:
    """Stop a running game process."""
    key = f"{child_id}:{game_id}"
    
    if key not in _running_games:
        return {"success": False, "error": "Game not running"}
    
    proc_info = _running_games[key]
    process = proc_info.get("process")
    
    if process and process.poll() is None:
        try:
            # Try graceful termination first
            if os.name == 'nt':
                process.terminate()
            else:
                process.send_signal(signal.SIGTERM)
            
            # Wait briefly for clean exit
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                process.kill()
            
            return {
                "success": True,
                "game_id": game_id,
                "return_code": process.returncode,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    return {"success": True, "game_id": game_id, "note": "Already stopped"}


def get_game_status(game_id: str, child_id: str) -> Dict:
    """Get the status of a running game."""
    key = f"{child_id}:{game_id}"
    
    if key not in _running_games:
        return {"running": False, "game_id": game_id}
    
    proc_info = _running_games[key]
    process = proc_info.get("process")
    is_running = process and process.poll() is None
    
    return {
        "running": is_running,
        "game_id": game_id,
        "pid": proc_info.get("pid"),
        "session_id": proc_info.get("session_id"),
        "started_at": proc_info.get("started_at"),
        "ended_at": proc_info.get("ended_at"),
        "return_code": proc_info.get("return_code"),
    }
