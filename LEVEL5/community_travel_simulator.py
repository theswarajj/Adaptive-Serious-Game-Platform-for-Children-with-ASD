"""
Level 5: Community Travel Simulator
Safe public transportation navigation, route board reading, driver interaction,
and destination arrival simulator.
"""

import os
import sys
import time
import socket
import webbrowser
import threading
import http.server
import socketserver
import urllib.parse
from pathlib import Path

# Audio cue on Windows
try:
    import winsound
    def play_chime():
        winsound.MessageBeep(winsound.MB_ICONASTERISK)
except Exception:
    def play_chime():
        pass


def find_free_port(start_port=8056):
    """Find an available TCP port starting from start_port."""
    for port in range(start_port, start_port + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    return 8056


class QuietHTTPHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler that serves LEVEL5 files quietly."""
    def log_message(self, format, *args):
        if args and len(args) > 1 and str(args[1]).startswith(('4', '5')):
            super().log_message(format, *args)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        super().end_headers()


def run_server(port, folder):
    """Run ThreadingHTTPServer in the background."""
    handler = lambda *args, **kwargs: QuietHTTPHandler(*args, directory=folder, **kwargs)
    httpd = socketserver.ThreadingTCPServer(('127.0.0.1', port), handler)
    httpd.allow_reuse_address = True
    server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    server_thread.start()
    return httpd


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    html_target = "Community Travel Simulator.html"
    full_html_path = os.path.join(script_dir, html_target)

    if not os.path.exists(full_html_path):
        # Fallback to alternate filenames
        alternatives = ["community_travel_simulator.html", "Community Travel Simulator (3).html"]
        for alt in alternatives:
            p = os.path.join(script_dir, alt)
            if os.path.exists(p):
                html_target = alt
                full_html_path = p
                break

    if not os.path.exists(full_html_path):
        print(f"[ERROR] Game file not found in {script_dir}")
        sys.exit(1)

    port = find_free_port(8056)
    server = run_server(port, script_dir)

    game_url = f"http://127.0.0.1:{port}/{urllib.parse.quote(html_target)}"

    print("=" * 66)
    print(" 🚌  LEVEL 5: COMMUNITY TRAVEL SIMULATOR  🚌")
    print("=" * 66)
    print(" • Real In-Code Title: Community Travel Simulator")
    print(" • Level Category    : Social Reasoning & Daily Living")
    print(" • 3D City Engine    : Three.js with Unreal Bloom, Route Board & Bus")
    print(f" • Local Web Server  : http://127.0.0.1:{port}/")
    print(f" • Game URL          : {game_url}")
    print("=" * 66)
    print(" Controls:")
    print("   - W / A / S / D or Arrow Keys: Walk to bus stop & destinations")
    print("   - Mouse Drag / Touch         : Look around 360°")
    print("   - Dialogue Options           : Select numbers or click responses")
    print("   - Fare Payment               : Tap card or pay with cash")
    print("=" * 66)
    print(" Opening game in your web browser...")

    play_chime()
    webbrowser.open(game_url, new=2)
    print("\n [INFO] Game is running! Keep this window open while playing.")
    print(" Press Ctrl+C to stop the game server.\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n [INFO] Stopping Community Travel Simulator server...")
    finally:
        try:
            server.shutdown()
            server.server_close()
        except Exception:
            pass
        print(" [INFO] Session ended. Goodbye!")


if __name__ == "__main__":
    main()
