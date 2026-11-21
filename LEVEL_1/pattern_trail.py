# pattern_trail.py
# Standalone desktop game — visually enhanced for autism students.
#
# PATTERN TRAIL — Motor control, visual tracking, and sustained task attention.
# A number (0-9) or letter (A-Z) appears in the upper-middle of the screen.
# The child traces it with their index fingertip (MediaPipe Hands). The system measures:
#   - Trajectory deviation (how far off the path the finger strays)
#   - Pauses (stalls mid-trace, count + total duration)
#   - Speed (instantaneous + average)
#   - Completion time
#   - Consistency (variability of speed across the trace — smoothness)
# Every finished trace is also saved to  pattern_trail_log.csv  (next to this file)
# so a teacher / therapist can follow progress over time.
#
# Progression follows: SEE -> FOLLOW -> CONTROL
#   SEE     — numbers 0-9, shown by a moving guide ball first; wide tolerance.
#   FOLLOW  — letters A-Z, demo shown; medium tolerance.
#   CONTROL — numbers and letters again, no demo; tight tolerance.
#
# Install:  pip install opencv-python mediapipe numpy
# Run:      python pattern_trail.py
#
# Keys (for the teacher / helper):
#   q  quit            n  next letter/number     b  previous letter/number
#   r  retry this one  s  skip the demo          c  calm mode on/off (less sparkle, no flashing)
#   m  sound on/off

import cv2
import mediapipe as mp
import numpy as np
import random
import time
import math
import os
import csv
import threading
from collections import deque
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from game_card import show_quit_card, format_time

LAST_RENDERED_FRAME = None

try:
    import winsound  # Windows only
except ImportError:
    winsound = None

mp_hands = mp.solutions.hands

INDEX_TIP = 8

# ==================== Runtime settings (toggle with keys) ====================
SETTINGS = {"calm": False, "sound": True}


def play_success_sound():
    if winsound is None or not SETTINGS["sound"]:
        return

    def sound():
        try:
            winsound.Beep(600, 150)
            winsound.Beep(800, 150)
            winsound.Beep(1200, 300)
        except Exception:
            pass
    threading.Thread(target=sound, daemon=True).start()


# ==================== Layout ====================
CANVAS_W, CANVAS_H = 1280, 720

# ==================== Letter / Number placement ====================
GLYPH_W = 210          # medium width (each glyph scales this by its own width factor below)
GLYPH_H = 260          # medium height
GLYPH_CENTER_X = CANVAS_W // 2     # horizontally centered
GLYPH_TOP = 175                    # upper-middle; bottom edge ends ~440 (well above the bottom)

# How wide each glyph is, as a fraction of GLYPH_W (so "I" and "1" are slim, "M" and "W" are wide)
GLYPH_WIDTH = {
    "0": 0.80, "1": 0.50, "2": 0.85, "3": 0.85, "4": 0.95, "5": 0.85, "6": 0.85, "7": 0.85,
    "8": 0.80, "9": 0.85,
    "A": 1.00, "B": 0.85, "C": 0.90, "D": 0.90, "E": 0.80, "F": 0.75, "G": 0.95, "H": 0.90,
    "I": 0.50, "J": 0.70, "K": 0.90, "L": 0.75, "M": 1.10, "N": 0.90, "O": 1.00, "P": 0.85,
    "Q": 1.00, "R": 0.90, "S": 0.85, "T": 0.95, "U": 0.90, "V": 1.00, "W": 1.20, "X": 1.00,
    "Y": 1.00, "Z": 0.90,
}

# Look of the path "ribbon" the child follows
RIBBON_OUTER = 38      # soft outline thickness (px)
RIBBON_INNER = 30      # white ribbon thickness (px)
TRACED_GLOW = 24       # glow thickness of the already-traced part
TRACED_WIDTH = 16      # bright thickness of the already-traced part

# Calm, low-clutter background: the webcam image is blended with a soft pastel color
BG_SOFTEN = 0.0
GRADIENT_BG = None

def get_gradient_bg():
    global GRADIENT_BG
    if GRADIENT_BG is None:
        GRADIENT_BG = np.zeros((CANVAS_H, CANVAS_W, 3), dtype=np.uint8)
        c1 = np.array([255, 230, 210], dtype=np.float32)  # Soft warm cream/pink
        c2 = np.array([250, 200, 230], dtype=np.float32)  # Soft pastel purple
        for y in range(CANVAS_H):
            ratio = y / CANVAS_H
            GRADIENT_BG[y, :] = c1 * (1 - ratio) + c2 * ratio
    return GRADIENT_BG

# Fingertip smoothing (0 = very smooth/laggy, 1 = raw). Reduces MediaPipe jitter.
SMOOTH_ALPHA = 0.55

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pattern_trail_log.csv")

# ==================== Color Palette (soft, child-friendly) ====================
# Stage badge colors (BGR)
STAGE_COLORS = {
    "See":     (120, 220, 130),   # green
    "Follow":  (80, 200, 255),    # yellow-orange
    "Control": (200, 140, 255),   # pink-purple
}

# ==================== Stage settings (SEE -> FOLLOW -> CONTROL) ====================
# See: digits 0-9 (demo, wide tolerance) -> Follow: letters A-Z (demo) -> Control: all again, no demo
STAGES = {
    "See":     {"tolerance": 70, "min_completions": 0,  "show_demo": True},
    "Follow":  {"tolerance": 50, "min_completions": 10, "show_demo": True},
    "Control": {"tolerance": 32, "min_completions": 36, "show_demo": False},
}
STAGE_ORDER = ["See", "Follow", "Control"]

PAUSE_SPEED_THRESHOLD_PXPS = 25
PAUSE_MIN_MS = 400
DEMO_SPEED_PXPS = 220
LOOKAHEAD_FRACTION = 0.06
FINISH_ZONE_FRACTION = 0.08   # how close to the end (fraction of path) counts as 'reached the end'
SUMMARY_DISPLAY_S = 4.0


# ==================== Drawing Helpers ====================

def prepare_canvas(frame):
    """Resize the webcam frame to the game canvas and soften it so the path stands out."""
    canvas = cv2.resize(frame, (CANVAS_W, CANVAS_H))
    tint = get_gradient_bg()
    return cv2.addWeighted(canvas, 1.0 - BG_SOFTEN, tint, BG_SOFTEN, 0)


def draw_mini_star(canvas, cx, cy, r, color):
    """Draw a tiny 4-pointed star."""
    pts = []
    for i in range(8):
        angle = math.radians(i * 45 - 90)
        radius = r if i % 2 == 0 else r * 0.4
        px = int(cx + radius * math.cos(angle))
        py = int(cy + radius * math.sin(angle))
        pts.append([px, py])
    pts_arr = np.array(pts, np.int32).reshape((-1, 1, 2))
    cv2.fillPoly(canvas, [pts_arr], color)


def draw_star(canvas, cx, cy, outer_r, inner_r, color):
    """Draw a 5-pointed star."""
    points = []
    for i in range(10):
        angle = math.radians(i * 36 - 90)
        r = outer_r if i % 2 == 0 else inner_r
        px = int(cx + r * math.cos(angle))
        py = int(cy + r * math.sin(angle))
        points.append([px, py])
    pts = np.array(points, np.int32).reshape((-1, 1, 2))
    cv2.fillPoly(canvas, [pts], color)
    cv2.polylines(canvas, [pts], True,
                  (max(0, color[0] - 40), max(0, color[1] - 40), max(0, color[2] - 40)), 2)


def draw_rounded_rect(canvas, x1, y1, x2, y2, color, radius=16, thickness=-1,
                       border_color=None, border_thickness=2, shadow=False):
    """Draw a rounded rectangle."""
    r = min(radius, (x2 - x1) // 2, (y2 - y1) // 2)
    
    if shadow:
        shadow_offset = 5
        shadow_color = (60, 50, 50)
        overlay = canvas.copy()
        cv2.rectangle(overlay, (x1 + r + shadow_offset, y1 + shadow_offset), (x2 - r + shadow_offset, y2 + shadow_offset), shadow_color, -1)
        cv2.rectangle(overlay, (x1 + shadow_offset, y1 + r + shadow_offset), (x2 + shadow_offset, y2 - r + shadow_offset), shadow_color, -1)
        cv2.circle(overlay, (x1 + r + shadow_offset, y1 + r + shadow_offset), r, shadow_color, -1, cv2.LINE_AA)
        cv2.circle(overlay, (x2 - r + shadow_offset, y1 + r + shadow_offset), r, shadow_color, -1, cv2.LINE_AA)
        cv2.circle(overlay, (x1 + r + shadow_offset, y2 - r + shadow_offset), r, shadow_color, -1, cv2.LINE_AA)
        cv2.circle(overlay, (x2 - r + shadow_offset, y2 - r + shadow_offset), r, shadow_color, -1, cv2.LINE_AA)
        cv2.addWeighted(overlay, 0.25, canvas, 0.75, 0, canvas)

    if thickness == -1:
        cv2.rectangle(canvas, (x1 + r, y1), (x2 - r, y2), color, -1)
        cv2.rectangle(canvas, (x1, y1 + r), (x2, y2 - r), color, -1)
        cv2.circle(canvas, (x1 + r, y1 + r), r, color, -1, cv2.LINE_AA)
        cv2.circle(canvas, (x2 - r, y1 + r), r, color, -1, cv2.LINE_AA)
        cv2.circle(canvas, (x1 + r, y2 - r), r, color, -1, cv2.LINE_AA)
        cv2.circle(canvas, (x2 - r, y2 - r), r, color, -1, cv2.LINE_AA)
    if border_color is not None:
        cv2.line(canvas, (x1 + r, y1), (x2 - r, y1), border_color, border_thickness, cv2.LINE_AA)
        cv2.line(canvas, (x1 + r, y2), (x2 - r, y2), border_color, border_thickness, cv2.LINE_AA)
        cv2.line(canvas, (x1, y1 + r), (x1, y2 - r), border_color, border_thickness, cv2.LINE_AA)
        cv2.line(canvas, (x2, y1 + r), (x2, y2 - r), border_color, border_thickness, cv2.LINE_AA)
        cv2.ellipse(canvas, (x1 + r, y1 + r), (r, r), 180, 0, 90, border_color, border_thickness, cv2.LINE_AA)
        cv2.ellipse(canvas, (x2 - r, y1 + r), (r, r), 270, 0, 90, border_color, border_thickness, cv2.LINE_AA)
        cv2.ellipse(canvas, (x1 + r, y2 - r), (r, r), 90, 0, 90, border_color, border_thickness, cv2.LINE_AA)
        cv2.ellipse(canvas, (x2 - r, y2 - r), (r, r), 0, 0, 90, border_color, border_thickness, cv2.LINE_AA)


def put_text_shadow(canvas, text, pos, font, scale, color, thickness, shadow_color=(40, 40, 40)):
    """Draw text with a subtle shadow for readability."""
    cv2.putText(canvas, text, (pos[0] + 3, pos[1] + 3), font, scale, shadow_color, thickness + 2, cv2.LINE_AA)
    cv2.putText(canvas, text, (pos[0] + 1, pos[1] + 1), font, scale, shadow_color, thickness, cv2.LINE_AA)
    cv2.putText(canvas, text, pos, font, scale, color, thickness, cv2.LINE_AA)


def draw_progress_ring(canvas, cx, cy, radius, progress, color, bg_color=(220, 220, 225), thickness=8):
    """Draw a circular progress ring."""
    cv2.circle(canvas, (cx, cy), radius, bg_color, thickness, cv2.LINE_AA)
    if progress > 0:
        end_angle = int(progress * 360)
        overlay = canvas.copy()
        cv2.ellipse(overlay, (cx, cy), (radius, radius), -90, 0, end_angle, color, thickness + 6, cv2.LINE_AA)
        cv2.addWeighted(overlay, 0.4, canvas, 0.6, 0, canvas)
        cv2.ellipse(canvas, (cx, cy), (radius, radius), -90, 0, end_angle, color, thickness, cv2.LINE_AA)


def trace_color():
    """Solid glowing sky-blue used for the traced part of the path and the finger trail (BGR)."""
    return (255, 210, 50)


# ==================== Sparkle Particle System ====================

class SparkleSystem:
    """Particle system for trail sparkles, confetti, and celebrations."""

    def __init__(self):
        self.particles = []

    def emit_sparkles(self, x, y, count=3):
        """Emit trail sparkles at finger position."""
        for _ in range(count):
            self.particles.append({
                "x": x + random.uniform(-8, 8),
                "y": y + random.uniform(-8, 8),
                "vx": random.uniform(-1.5, 1.5),
                "vy": random.uniform(-2.5, -0.5),
                "size": random.uniform(2, 5),
                "color": random.choice([
                    (100, 255, 255), (120, 255, 200), (200, 220, 255),
                    (180, 255, 180), (255, 220, 150),
                ]),
                "life": random.uniform(0.4, 1.0),
                "born": time.time(),
            })

    def emit_confetti(self, x, y, count=80):
        """Emit a big confetti burst for celebrations."""
        colors = [
            (80, 210, 255), (120, 255, 120), (255, 170, 100),
            (180, 130, 255), (100, 255, 255), (130, 220, 255),
            (200, 200, 100), (255, 180, 200),
        ]
        for _ in range(count):
            self.particles.append({
                "x": x + random.uniform(-30, 30),
                "y": y + random.uniform(-30, 30),
                "vx": random.uniform(-6, 6),
                "vy": random.uniform(-10, -2),
                "size": random.uniform(4, 12),
                "color": random.choice(colors),
                "life": random.uniform(1.5, 3.5),
                "born": time.time(),
                "shape": random.choice(["rect", "circle", "triangle"]),
                "rotation": random.uniform(0, 360),
                "rot_speed": random.uniform(-8, 8),
            })

    def emit_stars(self, count=15):
        """Emit star-shaped particles across the screen."""
        for _ in range(count):
            self.particles.append({
                "x": random.uniform(100, CANVAS_W - 100),
                "y": random.uniform(-50, 100),
                "vx": random.uniform(-1, 1),
                "vy": random.uniform(1, 4),
                "size": random.uniform(8, 16),
                "color": (30, 210, 255),  # gold
                "life": random.uniform(2, 4),
                "born": time.time(),
                "shape": "star",
                "rotation": random.uniform(0, 360),
                "rot_speed": random.uniform(-3, 3),
            })

    def update_and_draw(self, canvas):
        now = time.time()
        alive = []
        for p in self.particles:
            age = now - p["born"]
            if age > p["life"]:
                continue

            p["x"] += p["vx"]
            p["vy"] += 0.06  # gentle gravity
            p["y"] += p["vy"]
            p["vx"] *= 0.995

            alpha = max(0.0, 1.0 - age / p["life"])
            if alpha < 0.05:
                continue

            x, y = int(p["x"]), int(p["y"])
            s = int(p["size"] * alpha)
            color = p["color"]

            if 0 <= x < CANVAS_W and 0 <= y < CANVAS_H and s > 0:
                shape = p.get("shape", "circle")
                if shape == "circle":
                    cv2.circle(canvas, (x, y), max(1, s // 2), color, -1, cv2.LINE_AA)
                elif shape == "star":
                    draw_mini_star(canvas, x, y, s, color)
                elif shape == "rect":
                    rot = p.get("rotation", 0) + p.get("rot_speed", 0) * age * 10
                    angle = math.radians(rot)
                    hw, hh = s // 2, s // 4
                    pts = []
                    for dx, dy in [(-hw, -hh), (hw, -hh), (hw, hh), (-hw, hh)]:
                        rx = int(x + dx * math.cos(angle) - dy * math.sin(angle))
                        ry = int(y + dx * math.sin(angle) + dy * math.cos(angle))
                        pts.append([rx, ry])
                    pts_arr = np.array(pts, np.int32).reshape((-1, 1, 2))
                    cv2.fillPoly(canvas, [pts_arr], color)
                elif shape == "triangle":
                    rot = p.get("rotation", 0) + p.get("rot_speed", 0) * age * 10
                    angle = math.radians(rot)
                    pts = []
                    for i in range(3):
                        a = angle + math.radians(i * 120)
                        px2 = int(x + s * 0.5 * math.cos(a))
                        py2 = int(y + s * 0.5 * math.sin(a))
                        pts.append([px2, py2])
                    pts_arr = np.array(pts, np.int32).reshape((-1, 1, 2))
                    cv2.fillPoly(canvas, [pts_arr], color)

            alive.append(p)
        self.particles = alive

    @property
    def active(self):
        return len(self.particles) > 0


# ==================== Path Generation: digits 0-9 and letters A-Z ====================
# Each glyph is ONE continuous stroke in a unit box (x: 0..1 left->right, y: 0..1 top->bottom).
# Round letters use true curves; letters with extra bars (A, E, F, H, K, T, X, Y) retrace a
# short piece so the child can finish the whole shape in a single go.

def _quad(p0, p1, p2, n=30):
    """Quadratic Bezier curve."""
    pts = []
    for i in range(n):
        t = i / (n - 1)
        u = 1 - t
        pts.append((u * u * p0[0] + 2 * u * t * p1[0] + t * t * p2[0],
                    u * u * p0[1] + 2 * u * t * p1[1] + t * t * p2[1]))
    return pts


def _cubic(p0, p1, p2, p3, n=40):
    """Cubic Bezier curve."""
    pts = []
    for i in range(n):
        t = i / (n - 1)
        u = 1 - t
        pts.append((u ** 3 * p0[0] + 3 * u * u * t * p1[0] + 3 * u * t * t * p2[0] + t ** 3 * p3[0],
                    u ** 3 * p0[1] + 3 * u * u * t * p1[1] + 3 * u * t * t * p2[1] + t ** 3 * p3[1]))
    return pts


def _arc(cx, cy, rx, ry, a0, a1, n=40):
    """Elliptical arc. Angles in degrees: 0=right, 90=bottom, 180=left, 270=top.
    Increasing angle = clockwise on screen, decreasing = counter-clockwise."""
    pts = []
    for i in range(n):
        a = math.radians(a0 + (a1 - a0) * i / (n - 1))
        pts.append((cx + rx * math.cos(a), cy + ry * math.sin(a)))
    return pts


def _spline(ctrl, per_segment=14):
    """Smooth curve through control points (Catmull-Rom spline)."""
    pts_in = [ctrl[0]] + list(ctrl) + [ctrl[-1]]
    out = []
    for i in range(1, len(pts_in) - 2):
        p0, p1, p2, p3 = pts_in[i - 1], pts_in[i], pts_in[i + 1], pts_in[i + 2]
        for k in range(per_segment):
            t = k / per_segment
            t2, t3 = t * t, t * t * t
            out.append(tuple(0.5 * ((2 * p1[j]) + (-p0[j] + p2[j]) * t
                                    + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * t2
                                    + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * t3) for j in (0, 1)))
    out.append(tuple(ctrl[-1]))
    return out


def _figure8(n=90):
    """A smooth figure eight that starts at the top and crosses in the middle."""
    pts = []
    for i in range(n):
        th = 1.5 * math.pi + 2 * math.pi * i / (n - 1)
        pts.append((0.5 + 0.45 * math.sin(2 * th), 0.5 + 0.5 * math.sin(th)))
    return pts


GLYPHS = {
    # ---------- Numbers ----------
    "0": _arc(0.5, 0.5, 0.5, 0.5, 270, -90, 60),
    "1": [(0.15, 0.25), (0.62, 0.0), (0.62, 1.0)],
    "2": _arc(0.5, 0.27, 0.45, 0.27, 180, 375) + _cubic((0.935, 0.34), (0.9, 0.58), (0.35, 0.78), (0.05, 1.0)) + [(0.97, 1.0)],
    "3": _arc(0.47, 0.25, 0.4, 0.25, 205, 450) + _arc(0.47, 0.75, 0.5, 0.25, 270, 515),
    "4": [(0.72, 1.0), (0.72, 0.0), (0.0, 0.68), (1.0, 0.68)],
    "5": [(0.88, 0.0), (0.22, 0.0), (0.23, 0.44)] + _arc(0.46, 0.7, 0.46, 0.3, 240, 510),
    "6": _cubic((0.85, 0.03), (0.3, 0.1), (0.06, 0.4), (0.06, 0.68)) + _arc(0.5, 0.68, 0.44, 0.32, 180, -180, 50),
    "7": [(0.03, 0.0), (0.97, 0.0), (0.4, 1.0)],
    "8": _figure8(),
    "9": _arc(0.5, 0.32, 0.43, 0.32, 0, 360, 50) + _cubic((0.93, 0.32), (0.93, 0.7), (0.7, 0.97), (0.2, 0.99)),

    # ---------- Letters ----------
    "A": [(0, 1), (0.5, 0), (1, 1), (0.81, 0.62), (0.19, 0.62)],
    "B": [(0, 1), (0, 0)] + _arc(0, 0.25, 0.85, 0.25, -90, 90, 30) + _arc(0, 0.75, 0.98, 0.25, -90, 90, 30),
    "C": _arc(0.5, 0.5, 0.5, 0.5, -40, -320, 50),
    "D": [(0, 0), (0, 1)] + _arc(0, 0.5, 0.98, 0.5, 90, -90),
    "E": [(1, 0), (0, 0), (0, 0.5), (0.78, 0.5), (0, 0.5), (0, 1), (1, 1)],
    "F": [(1, 0), (0, 0), (0, 0.5), (0.78, 0.5), (0, 0.5), (0, 1)],
    "G": _arc(0.5, 0.5, 0.5, 0.5, -40, -340, 50) + [(0.97, 0.5), (0.55, 0.5)],
    "H": [(0, 0), (0, 1), (0, 0.5), (1, 0.5), (1, 0), (1, 1)],
    "I": [(0.1, 0), (0.9, 0), (0.5, 0), (0.5, 1), (0.1, 1), (0.9, 1)],
    "J": [(0.8, 0), (0.8, 0.72)] + _arc(0.45, 0.72, 0.35, 0.28, 0, 170, 30),
    "K": [(0, 0), (0, 1), (0, 0.55), (1, 0), (0, 0.55), (1, 1)],
    "L": [(0, 0), (0, 1), (0.95, 1)],
    "M": [(0, 1), (0, 0), (0.5, 0.62), (1, 0), (1, 1)],
    "N": [(0, 1), (0, 0), (1, 1), (1, 0)],
    "O": _arc(0.5, 0.5, 0.5, 0.5, 270, -90, 60),
    "P": [(0, 1), (0, 0)] + _arc(0, 0.27, 0.92, 0.27, -90, 90, 30),
    "Q": [(0.55, 0.6), (1.0, 1.0), (0.82, 0.88)] + _arc(0.5, 0.5, 0.5, 0.5, 50, -310, 60),
    "R": [(0, 1), (0, 0)] + _arc(0, 0.27, 0.92, 0.27, -90, 90, 30) + [(1, 1)],
    "S": _spline([(0.92, 0.15), (0.72, 0.03), (0.42, 0.0), (0.14, 0.11), (0.08, 0.28), (0.25, 0.43),
                  (0.6, 0.54), (0.9, 0.68), (0.93, 0.85), (0.68, 0.99), (0.36, 1.0), (0.07, 0.88)]),
    "T": [(0, 0), (1, 0), (0.5, 0), (0.5, 1)],
    "U": [(0, 0), (0, 0.62)] + _arc(0.5, 0.62, 0.5, 0.38, 180, 0) + [(1, 0)],
    "V": [(0, 0), (0.5, 1), (1, 0)],
    "W": [(0, 0), (0.25, 1), (0.5, 0.3), (0.75, 1), (1, 0)],
    "X": [(0, 0), (1, 1), (0.5, 0.5), (1, 0), (0.5, 0.5), (0, 1)],
    "Y": [(0, 0), (0.5, 0.5), (1, 0), (0.5, 0.5), (0.5, 1)],
    "Z": [(0, 0), (1, 0), (0, 1), (1, 1)],
}

# Predictable order helps many learners: 0..9, then A..Z, then repeat
GLYPH_SEQUENCE = list("0123456789") + [chr(c) for c in range(ord("A"), ord("Z") + 1)]


def _resample(points, n=240):
    """Resample a polyline to n evenly spaced points (smooth, consistent speed for tracking)."""
    dists = [0.0]
    for i in range(1, len(points)):
        dists.append(dists[-1] + math.hypot(points[i][0] - points[i - 1][0],
                                            points[i][1] - points[i - 1][1]))
    total = dists[-1]
    out, j = [], 0
    for k in range(n):
        target = total * k / (n - 1)
        while j < len(dists) - 2 and dists[j + 1] < target:
            j += 1
        seg = dists[j + 1] - dists[j]
        f = 0.0 if seg == 0 else (target - dists[j]) / seg
        out.append((points[j][0] + (points[j + 1][0] - points[j][0]) * f,
                    points[j][1] + (points[j + 1][1] - points[j][1]) * f))
    return out


def build_glyph(ch):
    """Scale a unit-box glyph to screen pixels: centered horizontally, near the top/middle."""
    w = GLYPH_W * GLYPH_WIDTH.get(ch, 0.9)
    left = GLYPH_CENTER_X - w / 2
    scaled = [(left + x * w, GLYPH_TOP + y * GLYPH_H) for x, y in GLYPHS[ch]]
    return _resample(scaled, n=240)


# ==================== Stage / Progression ====================

def get_stage(total_completions):
    stage = STAGE_ORDER[0]
    for name in STAGE_ORDER:
        if total_completions >= STAGES[name]["min_completions"]:
            stage = name
    return stage


def spawn_path(stage_name, total_completions):
    """Letters/numbers come in a predictable order: 0..9, then A..Z, then repeat."""
    ch = GLYPH_SEQUENCE[total_completions % len(GLYPH_SEQUENCE)]
    return ch, build_glyph(ch)


# ==================== Trajectory Analysis ====================

class TraceSession:
    """Tracks one attempt at tracing a path and computes metrics."""

    def __init__(self, path_points, tolerance_px):
        self.path = path_points
        self.tolerance = tolerance_px
        self.progress_idx = 0
        self.started = False
        self.start_time = None
        self.end_time = None

        self.deviations = []
        self.speeds = []
        self.pause_count = 0
        self.total_pause_ms = 0.0
        self._pause_active = False
        self._pause_started_at = None

        self._last_pos = None
        self._last_time = None

    def lookahead_window(self):
        return max(12, int(len(self.path) * LOOKAHEAD_FRACTION))

    def update(self, fingertip_px):
        now = time.time()

        if fingertip_px is None:
            self._last_pos = None
            self._last_time = None
            return

        if not self.started:
            dist_to_start = math.hypot(fingertip_px[0] - self.path[0][0],
                                       fingertip_px[1] - self.path[0][1])
            if dist_to_start <= self.tolerance:
                self.started = True
                self.start_time = now
                self._last_pos = fingertip_px
                self._last_time = now
            return

        if self._last_pos is not None and self._last_time is not None:
            dt = max(1e-3, now - self._last_time)
            dist_moved = math.hypot(fingertip_px[0] - self._last_pos[0],
                                    fingertip_px[1] - self._last_pos[1])
            speed = dist_moved / dt
            self.speeds.append(speed)

            if speed < PAUSE_SPEED_THRESHOLD_PXPS:
                if not self._pause_active:
                    self._pause_active = True
                    self._pause_started_at = now
            else:
                if self._pause_active:
                    pause_ms = (now - self._pause_started_at) * 1000
                    if pause_ms >= PAUSE_MIN_MS:
                        self.pause_count += 1
                        self.total_pause_ms += pause_ms
                    self._pause_active = False

        self._last_pos = fingertip_px
        self._last_time = now

        window = self.lookahead_window()
        end_search = min(len(self.path), self.progress_idx + window)
        dists = [math.hypot(fingertip_px[0] - self.path[i][0], fingertip_px[1] - self.path[i][1])
                 for i in range(self.progress_idx, end_search)]
        if not dists:
            return
        min_d = min(dists)
        # Among points that are (almost) equally close, take the furthest one along the path.
        # This keeps progress moving at turn-around tips of retraced strokes (E, F, I, T...).
        best_idx = self.progress_idx + max(k for k, d in enumerate(dists) if d <= min_d + 1.5)
        best_dist = min_d

        self.deviations.append(best_dist)

        if best_dist <= self.tolerance and best_idx > self.progress_idx:
            self.progress_idx = best_idx

        # Finished when the last part of the path is reached and the finger is at the end star.
        dist_to_end = math.hypot(fingertip_px[0] - self.path[-1][0], fingertip_px[1] - self.path[-1][1])
        if self.progress_idx >= int(len(self.path) * 0.70) and dist_to_end <= max(90.0, self.tolerance * 1.25) and self.end_time is None:
            self.end_time = now
            self.progress_idx = len(self.path) - 1
            return

        finish_zone = max(20, int(len(self.path) * FINISH_ZONE_FRACTION))
        if self.progress_idx >= len(self.path) - 1 - finish_zone:
            if dist_to_end <= max(85.0, self.tolerance * 1.15) and self.end_time is None:
                self.end_time = now
                self.progress_idx = len(self.path) - 1

    def is_complete(self):
        return self.end_time is not None

    def progress_fraction(self):
        return self.progress_idx / max(1, len(self.path) - 1)

    def current_deviation(self):
        return self.deviations[-1] if self.deviations else 0.0

    def summary(self):
        completion_time_s = (self.end_time - self.start_time) if (self.end_time and self.start_time) else None
        avg_dev = sum(self.deviations) / len(self.deviations) if self.deviations else 0.0
        avg_speed = sum(self.speeds) / len(self.speeds) if self.speeds else 0.0
        if len(self.speeds) >= 2:
            mean_s = avg_speed
            variance = sum((s - mean_s) ** 2 for s in self.speeds) / len(self.speeds)
            speed_std = math.sqrt(variance)
        else:
            speed_std = 0.0

        # Star rating
        if avg_dev < 20:
            stars = 3
        elif avg_dev < 40:
            stars = 2
        else:
            stars = 1

        return {
            "completion_time_s": completion_time_s,
            "avg_deviation_px": avg_dev,
            "avg_speed_pxps": avg_speed,
            "speed_consistency_std": speed_std,
            "pause_count": self.pause_count,
            "total_pause_ms": self.total_pause_ms,
            "stars": stars,
        }


def log_result(character, stage_name, tolerance, summary):
    """Append one finished trace to pattern_trail_log.csv (for teachers / therapists)."""
    try:
        new_file = not os.path.exists(LOG_FILE)
        with open(LOG_FILE, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if new_file:
                writer.writerow(["timestamp", "character", "stage", "tolerance_px",
                                 "completion_time_s", "avg_deviation_px", "avg_speed_pxps",
                                 "speed_consistency_std", "pause_count", "total_pause_ms", "stars"])
            t = summary["completion_time_s"]
            writer.writerow([
                datetime.now().isoformat(timespec="seconds"), character, stage_name, tolerance,
                "" if t is None else round(t, 2),
                round(summary["avg_deviation_px"], 1),
                round(summary["avg_speed_pxps"], 1),
                round(summary["speed_consistency_std"], 1),
                summary["pause_count"],
                round(summary["total_pause_ms"]),
                summary["stars"],
            ])
    except OSError:
        pass  # never crash the game because the log file is locked / read-only


# ==================== Path Drawing (Enhanced) ====================

def draw_path_enhanced(canvas, path_points, progress_idx, t):
    """Draw the letter/number as a soft ribbon with flowing guide dots (runway lights effect)."""
    pts = np.array(path_points, dtype=np.int32)
    n = len(pts)
    progress_idx = max(0, min(int(progress_idx), n))

    # --- Ribbon: soft outline + white body with round joints, so the shape reads clearly ---
    overlay = canvas.copy()
    outline_col = (190, 175, 160)
    inner_shadow_col = (220, 210, 205)
    
    cv2.polylines(overlay, [pts], False, outline_col, RIBBON_OUTER + 4, cv2.LINE_AA)
    for px, py in pts[::3]:
        cv2.circle(overlay, (int(px), int(py)), (RIBBON_OUTER + 4) // 2, outline_col, -1, cv2.LINE_AA)
        
    cv2.polylines(overlay, [pts], False, inner_shadow_col, RIBBON_OUTER, cv2.LINE_AA)
    for px, py in pts[::3]:
        cv2.circle(overlay, (int(px), int(py)), RIBBON_OUTER // 2, inner_shadow_col, -1, cv2.LINE_AA)

    cv2.polylines(overlay, [pts], False, (255, 255, 255), RIBBON_INNER, cv2.LINE_AA)
    for px, py in pts[::3]:
        cv2.circle(overlay, (int(px), int(py)), RIBBON_INNER // 2, (255, 255, 255), -1, cv2.LINE_AA)
    cv2.addWeighted(overlay, 0.7, canvas, 0.3, 0, canvas)

    # --- Traced portion: bright glowing line ---
    if progress_idx > 1:
        seg = pts[:min(progress_idx + 1, n)]
        color = trace_color()
        glow = tuple(max(0, c - 60) for c in color)
        cv2.polylines(canvas, [seg], False, glow, TRACED_GLOW, cv2.LINE_AA)
        cv2.polylines(canvas, [seg], False, color, TRACED_WIDTH, cv2.LINE_AA)
        for end_pt, rad in ((seg[0], TRACED_GLOW // 2), (seg[-1], TRACED_GLOW // 2)):
            cv2.circle(canvas, (int(end_pt[0]), int(end_pt[1])), rad, glow, -1, cv2.LINE_AA)
        for end_pt in (seg[0], seg[-1]):
            cv2.circle(canvas, (int(end_pt[0]), int(end_pt[1])), TRACED_WIDTH // 2, color, -1, cv2.LINE_AA)

    # --- Untraced portion: flowing guide dots show the direction ---
    if progress_idx < n - 1:
        dot_spacing = max(8, n // 20)
        flow_offset = int(t * 15) % dot_spacing
        for i in range(progress_idx + flow_offset, n, dot_spacing):
            gx, gy = int(pts[i][0]), int(pts[i][1])
            pulse = 0.5 + 0.5 * math.sin(t * 4 + i * 0.3)
            dot_color = (int(220 + 35 * pulse), int(140 + 40 * pulse), int(50 + 30 * pulse))
            cv2.circle(canvas, (gx, gy), 5, dot_color, -1, cv2.LINE_AA)

        # Gentle "look here" ring a little ahead of the progress point
        if progress_idx > 0:
            ahead = pts[min(n - 1, progress_idx + 10)]
            ring_r = int(11 + 2 * math.sin(t * 4))
            cv2.circle(canvas, (int(ahead[0]), int(ahead[1])), ring_r, (60, 170, 255), 3, cv2.LINE_AA)

    sx, sy = int(pts[0][0]), int(pts[0][1])
    ex, ey = int(pts[-1][0]), int(pts[-1][1])
    # Closed shapes (0, O, 8, D) start and end at the same spot
    same_spot = math.hypot(sx - ex, sy - ey) < 40

    # --- Start point: pulsing green circle (hidden once the child has started) ---
    start_r = int(16 * (1.0 + 0.15 * math.sin(t * 3)))
    if progress_idx < 3:
        overlay = canvas.copy()
        cv2.circle(overlay, (sx, sy), start_r + 8, (120, 240, 130), -1)
        cv2.addWeighted(overlay, 0.25, canvas, 0.75, 0, canvas)
        if same_spot:
            # Green ring that sits around the gold end star
            cv2.circle(canvas, (sx, sy), start_r + 8, (120, 240, 130), 4, cv2.LINE_AA)
        else:
            cv2.circle(canvas, (sx, sy), start_r, (120, 240, 130), -1, cv2.LINE_AA)
            cv2.circle(canvas, (sx, sy), start_r, (255, 255, 255), 2, cv2.LINE_AA)
        put_text_shadow(canvas, "Start!", (sx - 22, sy - start_r - 16),
                        cv2.FONT_HERSHEY_DUPLEX, 0.5, (120, 240, 130), 1)

    # --- End point: golden star ---
    star_r = int(16 * (1.0 + 0.1 * math.sin(t * 2.5)))
    overlay = canvas.copy()
    cv2.circle(overlay, (ex, ey), star_r + 10, (50, 200, 255), -1)
    cv2.addWeighted(overlay, 0.2, canvas, 0.8, 0, canvas)
    draw_star(canvas, ex, ey, star_r, star_r // 2, (30, 210, 255))
    if same_spot:
        put_text_shadow(canvas, "End", (ex - 15, ey + star_r + 30),
                        cv2.FONT_HERSHEY_DUPLEX, 0.45, (60, 200, 255), 1)
    else:
        put_text_shadow(canvas, "End", (ex - 15, ey - star_r - 10),
                        cv2.FONT_HERSHEY_DUPLEX, 0.45, (60, 200, 255), 1)


# ==================== Finger Cursor ====================

def draw_finger_cursor(canvas, x, y, deviation, tolerance, sparkles):
    """Draw a simple glowing finger cursor that changes color based on accuracy."""
    ix, iy = int(x), int(y)
    # Color: green (on track) -> yellow (drifting) -> orange (far off)
    ratio = min(1.0, deviation / tolerance) if tolerance > 0 else 0
    if ratio < 0.5:
        t = ratio * 2
        color = (0, int(255 * (1 - t * 0.3)), int(255 * t))
    else:
        t = (ratio - 0.5) * 2
        color = (0, int(180 - 80 * t), 255)

    # Soft glow and drop shadow
    overlay = canvas.copy()
    cv2.circle(overlay, (ix + 4, iy + 4), 24, (50, 40, 40), -1) # shadow
    cv2.circle(overlay, (ix, iy), 28, color, -1)                # glow
    cv2.addWeighted(overlay, 0.35, canvas, 0.65, 0, canvas)

    # Ring + bright centre dot
    cv2.circle(canvas, (ix, iy), 15, color, 3, cv2.LINE_AA)
    cv2.circle(canvas, (ix, iy), 6, (255, 255, 255), -1, cv2.LINE_AA)

    if not SETTINGS["calm"]:
        sparkles.emit_sparkles(x, y, count=1)

        # Pulse wave when on track
        if ratio < 0.4:
            wave_r = int(20 + (time.time() * 60) % 30)
            wave_alpha = max(0, 1.0 - (wave_r - 20) / 30)
            if wave_alpha > 0.1:
                overlay = canvas.copy()
                cv2.circle(overlay, (ix, iy), wave_r, (120, 255, 120), 2, cv2.LINE_AA)
                cv2.addWeighted(overlay, wave_alpha * 0.3, canvas, 1.0 - wave_alpha * 0.3, 0, canvas)


# ==================== Demo Phase (Enhanced) ====================

def draw_demo_character(canvas, x, y, t):
    """Draw a cute bouncing ball character with face for the demo."""
    ix, iy = int(x), int(y)
    bounce = 0 if SETTINGS["calm"] else int(abs(math.sin(t * 6)) * 5)
    iy -= bounce

    # Glow
    overlay = canvas.copy()
    cv2.circle(overlay, (ix, iy), 22, (80, 220, 255), -1)
    cv2.addWeighted(overlay, 0.15, canvas, 0.85, 0, canvas)

    # Body
    cv2.circle(canvas, (ix, iy), 16, (80, 220, 255), -1, cv2.LINE_AA)
    cv2.circle(canvas, (ix, iy), 16, (255, 255, 255), 2, cv2.LINE_AA)

    # Eyes
    cv2.circle(canvas, (ix - 5, iy - 3), 3, (40, 40, 50), -1)
    cv2.circle(canvas, (ix + 5, iy - 3), 3, (40, 40, 50), -1)
    # Eye highlights
    cv2.circle(canvas, (ix - 4, iy - 4), 1, (255, 255, 255), -1)
    cv2.circle(canvas, (ix + 6, iy - 4), 1, (255, 255, 255), -1)

    # Smile
    cv2.ellipse(canvas, (ix, iy + 2), (5, 4), 0, 10, 170, (40, 40, 50), 2, cv2.LINE_AA)

    # Cheeks
    overlay2 = canvas.copy()
    cv2.circle(overlay2, (ix - 10, iy + 2), 4, (160, 180, 255), -1)
    cv2.circle(overlay2, (ix + 10, iy + 2), 4, (160, 180, 255), -1)
    cv2.addWeighted(overlay2, 0.3, canvas, 0.7, 0, canvas)


def handle_toggle_keys(key):
    """Keys that work everywhere: c = calm mode, m = sound."""
    if key == ord('c'):
        SETTINGS["calm"] = not SETTINGS["calm"]
    elif key == ord('m'):
        SETTINGS["sound"] = not SETTINGS["sound"]


def run_demo(cap, path_points, shape_name, stage_name):
    """Run the demo phase with a cute animated character tracing the path.
    Returns False if the user quit, True otherwise (also when the demo is skipped with 's')."""
    global LAST_RENDERED_FRAME
    total_length = 0.0
    for i in range(1, len(path_points)):
        total_length += math.hypot(path_points[i][0] - path_points[i - 1][0],
                                   path_points[i][1] - path_points[i - 1][1])
    duration_s = max(1.5, total_length / DEMO_SPEED_PXPS)
    demo_start = time.time()

    while True:
        success, frame = cap.read()
        if not success:
            return True
        frame = cv2.flip(frame, 1)

        now = time.time()
        t_elapsed = now - demo_start
        t_frac = t_elapsed / duration_s

        canvas = prepare_canvas(frame)
        LAST_RENDERED_FRAME = canvas

        draw_path_enhanced(canvas, path_points, 0, now)

        if t_frac >= 1.0:
            break

        # Demo character position
        idx = int(t_frac * (len(path_points) - 1))
        gx, gy = path_points[idx]
        draw_demo_character(canvas, gx, gy, now)

        # Dotted sparkle trail behind character
        if idx > 5:
            for back in range(1, min(8, idx), 2):
                bx, by = path_points[idx - back]
                alpha = 1.0 - back / 8
                dot_color = tuple(int(c * alpha) for c in (100, 230, 255))
                cv2.circle(canvas, (int(bx), int(by)), max(1, int(3 * alpha)),
                           dot_color, -1, cv2.LINE_AA)

        # Stage badge and big reference character
        draw_stage_badge(canvas, stage_name)
        draw_info_card(canvas, f"Trace: {shape_name}", 30, 85, 200, 35)
        draw_reference_card(canvas, shape_name)

        # "Watch me!" text
        scale = 0.7 if SETTINGS["calm"] else 0.7 * (1.0 + 0.05 * math.sin(now * 3))
        put_text_shadow(canvas, "Watch me trace it!", (30, CANVAS_H - 30),
                        cv2.FONT_HERSHEY_DUPLEX, scale, (60, 60, 70), 2)

        draw_key_hints(canvas)

        cv2.imshow("Pattern Trail", canvas)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            return False
        if key == ord('s'):
            return True
        handle_toggle_keys(key)
    return True


# ==================== HUD Elements ====================

def draw_stage_badge(canvas, stage_name):
    """Draw a rounded stage badge in the top-left."""
    color = STAGE_COLORS.get(stage_name, (200, 200, 200))
    badge_w = 140
    badge_h = 34
    bx, by = 30, 25

    # Badge background
    draw_rounded_rect(canvas, bx, by, bx + badge_w, by + badge_h, color, radius=12,
                      border_color=(255, 255, 255), border_thickness=2, shadow=True)

    # Stage icon (circle with letter)
    icon_cx = bx + 20
    icon_cy = by + badge_h // 2
    cv2.circle(canvas, (icon_cx, icon_cy), 10, (255, 255, 255), -1, cv2.LINE_AA)
    cv2.putText(canvas, stage_name[0], (icon_cx - 5, icon_cy + 5),
                cv2.FONT_HERSHEY_DUPLEX, 0.4, (40, 40, 50), 1, cv2.LINE_AA)

    # Stage name
    put_text_shadow(canvas, stage_name, (bx + 38, by + badge_h // 2 + 6),
                    cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)


def draw_info_card(canvas, text, x, y, w, h, bg_color=(50, 50, 60)):
    """Draw a small rounded info card with text."""
    overlay = canvas.copy()
    draw_rounded_rect(overlay, x, y, x + w, y + h, bg_color, radius=10, shadow=True)
    cv2.addWeighted(overlay, 0.85, canvas, 0.15, 0, canvas)
    put_text_shadow(canvas, text, (x + 12, y + h // 2 + 5),
                    cv2.FONT_HERSHEY_DUPLEX, 0.4, (230, 230, 240), 1)


def draw_reference_card(canvas, character):
    """A card showing the letter/number in normal print, so the child can match it."""
    x1, y1, x2, y2 = 30, 150, 150, 290
    draw_rounded_rect(canvas, x1, y1, x2, y2, (250, 248, 245), radius=18,
                      border_color=(200, 195, 185), border_thickness=3, shadow=True)
    (tw, th), _ = cv2.getTextSize(character, cv2.FONT_HERSHEY_DUPLEX, 3.2, 5)
    cv2.putText(canvas, character, (x1 + (x2 - x1 - tw) // 2, y1 + (y2 - y1 + th) // 2 - 6),
                cv2.FONT_HERSHEY_DUPLEX, 3.2, (95, 85, 80), 5, cv2.LINE_AA)
    caption = "Number" if character.isdigit() else "Letter"
    (cw, _), _ = cv2.getTextSize(caption, cv2.FONT_HERSHEY_DUPLEX, 0.5, 1)
    put_text_shadow(canvas, caption, (x1 + (x2 - x1 - cw) // 2, y2 + 24),
                    cv2.FONT_HERSHEY_DUPLEX, 0.5, (255, 255, 255), 1)


def draw_key_hints(canvas):
    """Small teacher hints in the bottom-right corner."""
    text = (f"N next | B back | R retry | C calm {'ON' if SETTINGS['calm'] else 'off'} | "
            f"M sound {'on' if SETTINGS['sound'] else 'OFF'} | Q quit")
    (tw, _), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1)
    cv2.putText(canvas, text, (CANVAS_W - tw - 20, CANVAS_H - 16),
                cv2.FONT_HERSHEY_SIMPLEX, 0.45, (90, 85, 90), 1, cv2.LINE_AA)


def draw_center_message(canvas, text, y):
    """Friendly message card centered horizontally."""
    (tw, th), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_DUPLEX, 0.8, 2)
    w, h = tw + 50, th + 36
    x1 = CANVAS_W // 2 - w // 2
    overlay = canvas.copy()
    draw_rounded_rect(overlay, x1, y, x1 + w, y + h, (60, 60, 75), radius=16, shadow=True)
    cv2.addWeighted(overlay, 0.85, canvas, 0.15, 0, canvas)
    cv2.putText(canvas, text, (x1 + 25, y + h // 2 + th // 2),
                cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 2, cv2.LINE_AA)


def draw_hud_enhanced(canvas, stage_name, shape_name, total_completions, total_stars,
                       session, status_text, t):
    """Draw the enhanced HUD with stage badge, progress ring, and stats cards."""
    # Stage badge
    draw_stage_badge(canvas, stage_name)

    # Info cards (left side, below badge)
    draw_info_card(canvas, f"Trace: {shape_name}", 30, 70, 190, 30)
    draw_info_card(canvas, f"Completed: {total_completions}", 30, 106, 190, 30)

    # Big reference letter / number
    draw_reference_card(canvas, shape_name)

    # Stars earned
    star_x = 235
    star_y = 114
    for i in range(min(total_stars, 15)):
        sx = star_x + (i % 8) * 22
        sy = star_y + (i // 8) * 22
        draw_star(canvas, sx, sy, 8, 4, (30, 210, 255))

    # Progress ring (bottom-left)
    progress = session.progress_fraction() if session else 0.0
    ring_cx, ring_cy = 80, CANVAS_H - 80
    ring_color = (120, 240, 130) if progress > 0 else (200, 200, 210)
    draw_progress_ring(canvas, ring_cx, ring_cy, 35, progress, ring_color, thickness=6)
    # Percentage text in center
    pct_text = f"{int(progress * 100)}%"
    text_size = cv2.getTextSize(pct_text, cv2.FONT_HERSHEY_DUPLEX, 0.45, 1)[0]
    put_text_shadow(canvas, pct_text, (ring_cx - text_size[0] // 2, ring_cy + 6),
                    cv2.FONT_HERSHEY_DUPLEX, 0.45, (255, 255, 255), 1)

    # Status text
    put_text_shadow(canvas, status_text, (130, CANVAS_H - 75),
                    cv2.FONT_HERSHEY_DUPLEX, 0.55, (60, 60, 70), 1)

    # Live deviation indicator (when tracing)
    if session and session.started and session.deviations:
        dev = session.current_deviation()
        tol = session.tolerance
        ratio = min(1.0, dev / tol)
        if ratio < 0.5:
            dev_color = (120, 240, 130)   # green
            dev_label = "On Track!"
        elif ratio < 0.8:
            dev_color = (60, 220, 255)    # yellow
            dev_label = "Drifting..."
        else:
            dev_color = (80, 160, 240)    # orange
            dev_label = "Come closer!"

        draw_info_card(canvas, dev_label, 130, CANVAS_H - 50, 140, 28,
                       bg_color=(dev_color[0] // 3, dev_color[1] // 3, dev_color[2] // 3))

    draw_key_hints(canvas)


# ==================== Completion Summary (Beautiful Card) ====================

def draw_completion_summary(canvas, summary, t, sparkles):
    """Draw a completion summary card with star ratings."""
    # Semi-transparent backdrop
    overlay = canvas.copy()
    cv2.rectangle(overlay, (0, 0), (CANVAS_W, CANVAS_H), (240, 235, 225), -1)
    cv2.addWeighted(overlay, 0.4, canvas, 0.6, 0, canvas)

    # Main card
    card_w, card_h = 450, 320
    cx, cy = CANVAS_W // 2, CANVAS_H // 2
    x1, y1 = cx - card_w // 2, cy - card_h // 2
    x2, y2 = cx + card_w // 2, cy + card_h // 2

    draw_rounded_rect(canvas, x1, y1, x2, y2, (250, 248, 245), radius=22,
                      border_color=(200, 195, 185), border_thickness=3, shadow=True)

    # Title: steady (does not flicker), chosen from the star rating
    stars = summary.get("stars", 1)
    title = {3: "Amazing!", 2: "Great Job!", 1: "Well Done!"}.get(stars, "Well Done!")
    bounce = 0 if SETTINGS["calm"] else abs(math.sin(t * 3)) * 5
    title_size = cv2.getTextSize(title, cv2.FONT_HERSHEY_DUPLEX, 1.2, 2)[0]
    put_text_shadow(canvas, title, (cx - title_size[0] // 2, int(y1 + 58 - bounce)),
                    cv2.FONT_HERSHEY_DUPLEX, 1.2, (60, 170, 90), 2, shadow_color=(170, 205, 170))

    # Star rating
    star_start_x = cx - (stars * 40) // 2
    for i in range(stars):
        sx = star_start_x + i * 40 + 20
        sy = y1 + 98
        star_pulse = 1.0 if SETTINGS["calm"] else 1.0 + 0.1 * math.sin(t * 4 + i)
        draw_star(canvas, sx, sy, int(18 * star_pulse), int(8 * star_pulse), (30, 210, 255))

    # Stats lines (plain dark text on the light card)
    lines = [
        f"Time: {summary['completion_time_s']:.1f}s" if summary["completion_time_s"] else "Time: --",
        f"Avg Deviation: {summary['avg_deviation_px']:.0f}px",
        f"Avg Speed: {summary['avg_speed_pxps']:.0f}px/s",
        f"Smoothness: {max(0, 100 - summary['speed_consistency_std']):.0f}/100",
        f"Pauses: {summary['pause_count']}",
    ]
    ly = y1 + 148
    for i, line in enumerate(lines):
        cv2.putText(canvas, line, (x1 + 60, ly + i * 32),
                    cv2.FONT_HERSHEY_DUPLEX, 0.6, (85, 75, 70), 1, cv2.LINE_AA)

    # Sparkles and particles
    sparkles.update_and_draw(canvas)

    # Gold border flash (skipped in calm mode)
    if not SETTINGS["calm"]:
        flash_alpha = 0.3 + 0.2 * math.sin(t * 5)
        overlay2 = canvas.copy()
        cv2.rectangle(overlay2, (0, 0), (CANVAS_W - 1, CANVAS_H - 1), (50, 210, 255), 8)
        cv2.addWeighted(overlay2, flash_alpha, canvas, 1.0 - flash_alpha, 0, canvas)


# ==================== Expanding Ring Animation ====================

class ExpandingRing:
    """Expanding ring animation that plays when the child reaches the end point."""
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.born = time.time()
        self.duration = 1.0

    def draw(self, canvas):
        age = time.time() - self.born
        if age > self.duration:
            return False
        frac = age / self.duration
        radius = int(20 + frac * 120)
        alpha = max(0, 1.0 - frac)
        color = (50, int(210 * alpha), int(255 * alpha))
        thickness = max(1, int(4 * (1 - frac)))
        overlay = canvas.copy()
        cv2.circle(overlay, (int(self.x), int(self.y)), radius, color, thickness, cv2.LINE_AA)
        cv2.addWeighted(overlay, alpha * 0.6, canvas, 1.0 - alpha * 0.6, 0, canvas)
        return True


# ==================== Reusable Game Class for Stream Engine ====================

class PatternTrailGame:
    """
    Core Pattern Trail game engine.
    Tracks index finger position to trace letters/numbers.
    Can be run standalone or streamed in-browser.
    """
    def __init__(self, width=1280, height=720, use_camera=True):
        self.width = width
        self.height = height
        self.use_camera = use_camera
        self.cap = None
        if self.use_camera:
            try:
                self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
                if not self.cap or not self.cap.isOpened():
                    self.cap = cv2.VideoCapture(0)
                if self.cap.isOpened():
                    self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
                    self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
                    self.cap.set(cv2.CAP_PROP_FPS, 30)
            except Exception:
                self.cap = None

        self.hands = mp_hands.Hands(
            max_num_hands=1,
            model_complexity=0,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        self.total_completions = 0
        self.total_stars = 0
        self.score = 0
        self.current_streak = 0
        self.start_time = time.time()
        self.sparkles = SparkleSystem()
        self.fingertip_trail = deque(maxlen=30)
        self.smooth_pos = None

        self.shape_name = GLYPH_SEQUENCE[0]
        self.path_points = build_glyph(self.shape_name)
        self.stage_name = get_stage(self.total_completions)
        self.stage_cfg = STAGES[self.stage_name]
        self.session = TraceSession(self.path_points, self.stage_cfg["tolerance"])
        self.showing_summary = False
        self.summary_shown_at = None
        self.completion_ring = None
        self.summary_data = None
        self.last_time = time.time()
        self.last_dims = (width, height)
        self.status = f"Trace the number '{self.shape_name}' with your finger!"

    def click(self, x_pct: float, y_pct: float):
        if not self.path_points or self.showing_summary:
            return
        step = max(25, len(self.path_points) // 4)
        new_idx = min(len(self.path_points) - 1, self.session.progress_idx + step)
        self.session.progress_idx = new_idx
        if self.session.completed:
            self._on_completion()

    def _on_completion(self):
        self.summary_data = self.session.summary()
        self.showing_summary = True
        self.summary_shown_at = time.time()
        self.total_completions += 1
        self.score = self.total_completions
        self.current_streak += 1
        end_pt = self.path_points[-1]
        self.completion_ring = ExpandingRing(end_pt[0], end_pt[1])
        self.sparkles.add_celebration(int(end_pt[0]), int(end_pt[1]))
        play_success_sound()
        self.status = f"Completed '{self.shape_name}'! Great tracing!"

    def step(self) -> Optional[np.ndarray]:
        now = time.time()
        dt = max(0.001, now - self.last_time)
        self.last_time = now

        frame = None
        if self.cap and self.cap.isOpened():
            success, raw = self.cap.read()
            if success and raw is not None:
                frame = cv2.flip(raw, 1)

        if frame is None:
            frame = np.full((self.height, self.width, 3), (35, 30, 45), dtype=np.uint8)

        h, w = frame.shape[:2]
        self.last_dims = (w, h)
        canvas = frame

        # Synchronous hand tracking on 0.5x
        finger_px = None
        try:
            rgb = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
            small = cv2.resize(rgb, (0, 0), fx=0.5, fy=0.5, interpolation=cv2.INTER_LINEAR)
            small.flags.writeable = False
            results = self.hands.process(small)

            if results.multi_hand_landmarks:
                lm = results.multi_hand_landmarks[0].landmark[INDEX_TIP]
                raw_x, raw_y = lm.x * w, lm.y * h
                if self.smooth_pos is None:
                    self.smooth_pos = (raw_x, raw_y)
                else:
                    self.smooth_pos = (self.smooth_pos[0] * 0.45 + raw_x * 0.55,
                                       self.smooth_pos[1] * 0.45 + raw_y * 0.55)
                finger_px = (int(self.smooth_pos[0]), int(self.smooth_pos[1]))
                self.fingertip_trail.append(finger_px)
        except Exception:
            pass

        # Summary / completion state
        if self.showing_summary:
            if now - self.summary_shown_at > 2.0:
                self.showing_summary = False
                self.stage_name = get_stage(self.total_completions)
                self.stage_cfg = STAGES[self.stage_name]
                self.shape_name, self.path_points = spawn_path(self.stage_name, self.total_completions)
                self.session = TraceSession(self.path_points, self.stage_cfg["tolerance"])
                self.fingertip_trail.clear()
                self.status = f"Trace '{self.shape_name}' along the path!"
            else:
                if self.summary_data:
                    draw_completion_summary(canvas, self.summary_data, now, self.sparkles)
        else:
            deviation = None
            if finger_px and not self.session.completed:
                deviation = self.session.update(finger_px, now)
                if self.session.completed:
                    self._on_completion()

            draw_path_enhanced(canvas, self.path_points, self.session.progress_idx, now)
            if finger_px:
                draw_finger_cursor(canvas, finger_px[0], finger_px[1], deviation, self.stage_cfg["tolerance"], self.sparkles)

            if self.completion_ring:
                if not self.completion_ring.draw(canvas):
                    self.completion_ring = None

        draw_hud_enhanced(canvas, self.stage_name, self.shape_name, self.total_completions, self.total_stars,
                          self.session, self.status, now)

        self.sparkles.update_and_draw(canvas)
        return canvas

    def get_metrics(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "streak": self.current_streak,
            "status": self.status,
            "duration": round(time.time() - self.start_time, 1),
            "stage": self.stage_name,
            "glyph": self.shape_name,
        }

    def release(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()
        try:
            self.hands.close()
        except Exception:
            pass


# ==================== Main ====================

def main():
    try:
        import ctypes
        if os.name == 'nt':
            ctypes.windll.winmm.timeBeginPeriod(1)
    except Exception:
        pass

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap or not cap.isOpened():
        cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Could not open webcam.")
        return

    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    cap.set(cv2.CAP_PROP_FPS, 30)

    hands = mp_hands.Hands(
        max_num_hands=1,
        model_complexity=0,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6,
    )

    # Setup Fullscreen
    cv2.namedWindow("Pattern Trail", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("Pattern Trail", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    sparkles = SparkleSystem()

    global LAST_RENDERED_FRAME
    start_time = time.time()
    completed_summaries = []
    total_completions = 0
    total_stars = 0
    fingertip_trail = deque(maxlen=30)
    smooth_pos = None   # smoothed fingertip position

    running = True
    while running:
        stage_name = get_stage(total_completions)
        stage_cfg = STAGES[stage_name]
        shape_name, path_points = spawn_path(stage_name, total_completions)

        if stage_cfg["show_demo"]:
            running = run_demo(cap, path_points, shape_name, stage_name)
            if not running:
                break

        session = TraceSession(path_points, stage_cfg["tolerance"])
        fingertip_trail.clear()
        showing_summary = False
        summary_shown_at = None
        completion_ring = None
        summary_data = None

        # Fade-in effect
        fade_start = time.time()
        FADE_DURATION = 0.5

        while True:
            success, frame = cap.read()
            if not success:
                running = False
                break
            frame = cv2.flip(frame, 1)

            now = time.time()
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            rgb.flags.writeable = False
            results = hands.process(rgb)

            # Fingertip, smoothed a little to remove camera/MediaPipe jitter
            fingertip_px = None
            if results.multi_hand_landmarks:
                lm = results.multi_hand_landmarks[0].landmark[INDEX_TIP]
                raw = (lm.x * CANVAS_W, lm.y * CANVAS_H)
                if smooth_pos is None:
                    smooth_pos = raw
                else:
                    smooth_pos = (SMOOTH_ALPHA * raw[0] + (1 - SMOOTH_ALPHA) * smooth_pos[0],
                                  SMOOTH_ALPHA * raw[1] + (1 - SMOOTH_ALPHA) * smooth_pos[1])
                fingertip_px = smooth_pos
                fingertip_trail.append((int(fingertip_px[0]), int(fingertip_px[1])))
            else:
                smooth_pos = None

            # Build canvas with softened webcam feed
            canvas = prepare_canvas(frame)
            LAST_RENDERED_FRAME = canvas

            if not showing_summary:
                session.update(fingertip_px)
                draw_path_enhanced(canvas, path_points, session.progress_idx, now)

                # Soft trail from finger history
                trail_list = list(fingertip_trail)
                for i in range(1, len(trail_list)):
                    frac = i / max(1, len(trail_list) - 1)
                    alpha = 0.3 + 0.7 * frac  # fade older points
                    thickness = max(1, int(3 * alpha))
                    cv2.line(canvas, trail_list[i - 1], trail_list[i],
                             trace_color(), thickness, cv2.LINE_AA)

                # Finger cursor
                if fingertip_px:
                    dev = session.current_deviation() if session.started else 0
                    draw_finger_cursor(canvas, fingertip_px[0], fingertip_px[1],
                                       dev, session.tolerance, sparkles)

                status = "Touch the green Start to begin!" if not session.started else "Trace the path..."
                draw_hud_enhanced(canvas, stage_name, shape_name, total_completions,
                                  total_stars, session, status, now)

                if fingertip_px is None:
                    draw_center_message(canvas, "Show me your pointing finger!", 500)

                if session.is_complete():
                    showing_summary = True
                    summary_shown_at = now
                    summary_data = session.summary()
                    total_completions += 1
                    total_stars += summary_data["stars"]
                    completed_summaries.append(summary_data)
                    log_result(shape_name, stage_name, session.tolerance, summary_data)
                    play_success_sound()
                    # Celebration effects (gentler in calm mode)
                    ex, ey = path_points[-1]
                    if SETTINGS["calm"]:
                        sparkles.emit_confetti(CANVAS_W // 2, CANVAS_H // 2, count=20)
                    else:
                        sparkles.emit_confetti(CANVAS_W // 2, CANVAS_H // 2, count=80)
                        sparkles.emit_stars(count=15)
                    completion_ring = ExpandingRing(ex, ey)
            else:
                # Show completed path (fully traced)
                draw_path_enhanced(canvas, path_points, len(path_points), now)

                # Completion ring animation
                if completion_ring:
                    if not completion_ring.draw(canvas):
                        completion_ring = None

                # Summary card
                cel_t = now - summary_shown_at
                draw_completion_summary(canvas, summary_data, cel_t, sparkles)

                if cel_t > SUMMARY_DISPLAY_S:
                    break

            # Sparkle particles (always update)
            sparkles.update_and_draw(canvas)

            # Fade-in effect for new path
            fade_elapsed = now - fade_start
            if fade_elapsed < FADE_DURATION:
                fade_alpha = fade_elapsed / FADE_DURATION
                black = np.zeros_like(canvas)
                canvas = cv2.addWeighted(canvas, fade_alpha, black, 1.0 - fade_alpha, 0)

            cv2.imshow("Pattern Trail", canvas)
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                running = False
                break
            elif key == ord('n'):          # next letter/number
                total_completions += 1
                break
            elif key == ord('b'):          # previous letter/number
                total_completions = max(0, total_completions - 1)
                break
            elif key == ord('r') and not showing_summary:   # retry this one
                session = TraceSession(path_points, stage_cfg["tolerance"])
                fingertip_trail.clear()
            else:
                handle_toggle_keys(key)

    # Show attractive 4-second quit card before closing
    frame_for_card = LAST_RENDERED_FRAME
    if frame_for_card is None:
        frame_for_card = np.zeros((CANVAS_H, CANVAS_W, 3), dtype=np.uint8)

    play_duration = max(1.0, time.time() - start_time)
    avg_dev = np.mean([s['avg_deviation_px'] for s in completed_summaries]) if completed_summaries else 0
    dev_str = f"{avg_dev:.0f} px" if completed_summaries else "--"

    if total_completions >= 6 or total_stars >= 15:
        stars = 3
        verdict = "Master Motor Control & Focus!"
    elif total_completions >= 2 or total_stars >= 5:
        stars = 2
        verdict = "Superb Tracing & Accuracy!"
    else:
        stars = 1
        verdict = "Great Effort! Keep Tracing!"

    current_stage = get_stage(total_completions)
    stats = [
        {"label": "Play Time", "value": format_time(play_duration), "color": (255, 220, 100)},
        {"label": "Total Stars", "value": f"{total_stars} Stars", "color": (80, 220, 255)},
        {"label": "Avg Dev", "value": dev_str, "color": (100, 255, 140)},
        {"label": "Stage", "value": current_stage, "color": (255, 160, 200)},
    ]

    show_quit_card(
        window_name="Pattern Trail",
        last_frame=frame_for_card,
        game_title="Pattern Trail",
        score=total_completions,
        score_label="Patterns Completed",
        stats=stats,
        stars=stars,
        verdict=verdict,
        duration_s=4.0,
        accent_color=(30, 215, 255),
    )

    cap.release()
    hands.close()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()