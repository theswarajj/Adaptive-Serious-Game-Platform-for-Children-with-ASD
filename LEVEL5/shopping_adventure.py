"""
Level 5: Shopping Adventure / Supermarket Adventure
Real in-code game name: "Supermarket Adventure" (also titled "Shopping Adventure – Premium Supermarket")

This runner serves the full 3D Supermarket Adventure game locally over HTTP
and opens it in your default web browser or Chrome app window, allowing
seamless 3D WebGL rendering, 360-degree product inspection, and interactive
checkout dialogue.
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

# Optional audio cues on Windows
try:
    import winsound
    def play_chime():
        winsound.MessageBeep(winsound.MB_ICONASTERISK)
except Exception:
    def play_chime():
        pass


def find_free_port(start_port=8055):
    """Find an available TCP port starting from start_port."""
    for port in range(start_port, start_port + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
    return 8055


class QuietHTTPHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler that serves LEVEL5 files quietly without spamming stdout."""
    def log_message(self, format, *args):
        # Only log errors, suppress normal 200 GET requests
        if args and len(args) > 1 and str(args[1]).startswith(('4', '5')):
            super().log_message(format, *args)

    def end_headers(self):
        # Enable CORS and caching headers for smooth Three.js asset loading
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
    html_target = "Shopping Adventure.html"
    full_html_path = os.path.join(script_dir, html_target)

    if not os.path.exists(full_html_path):
        print(f"[ERROR] Game file not found: {full_html_path}")
        sys.exit(1)

    port = find_free_port(8055)
    server = run_server(port, script_dir)

    game_url = f"http://127.0.0.1:{port}/{urllib.parse.quote(html_target)}"

    print("=" * 66)
    print(" 🛒  LEVEL 5: SUPERMARKET ADVENTURE (SHOPPING ADVENTURE)  🛒")
    print("=" * 66)
    print(f" • Real Name in Code : Supermarket Adventure")
    print(f" • Document Title    : Shopping Adventure – Premium Supermarket")
    print(f" • Level Category    : Social Reasoning & Daily Living Skills")
    print(f" • 3D Engine         : Three.js with Real-time Reflection & 360° Inspect")
    print(f" • Local Web Server  : http://127.0.0.1:{port}/")
    print(f" • Game URL          : {game_url}")
    print("=" * 66)
    print(" Controls:")
    print("   - W / A / S / D or Arrow Keys: Walk around aisles")
    print("   - Mouse Drag / Touch         : Look around 360°")
    print("   - Left Click on Product      : 3D inspect & add to basket")
    print("   - Checkout Counter           : Pay with cash or card & take receipt")
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
        print("\n [INFO] Stopping Shopping Adventure server...")
    finally:
        try:
            server.shutdown()
            server.server_close()
        except Exception:
            pass
        print(" [INFO] Session ended. Goodbye!")


if __name__ == "__main__":
    main()
