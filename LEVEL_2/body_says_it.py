from game_card import show_quit_card, format_time
# body_says_it.py
# Standalone desktop game — graphically enhanced for autism students.
#
# BODY SAYS IT — Understand that emotions can be expressed through body posture,
# not just facial expression.
#
# An animated cartoon character demonstrates a body-language emotion:
#   - Excited (jumping)
#   - Sad (low, slouched posture)
#   - Angry (tense, wide stance)
#   - Surprised (sudden startled movement)
# The child identifies which emotion it was by holding up 1-4 fingers.
#
# NOTE ON "AI role": the task as specified is IDENTIFICATION (the child picks an
# answer), not physical imitation — so the natural input is the same hand-gesture
# selection pattern used in your other games (MediaPipe HANDS, finger-count = choice),
# not MediaPipe Pose. The avatar is a cartoon video clip, not a real
# tracked body. See the bottom of this file for how you'd adapt this into a POSE-based
# variant instead, where the child physically performs the posture rather than naming it.
#
# Metrics tracked: classification accuracy (running %) and response time (per round + average).
#
# Install:  pip install opencv-python mediapipe numpy
# Run:      python body_says_it.py
# Quit:     press 'q' in the window

import cv2
import mediapipe as mp
import numpy as np
import random
import time
import math
import os
import ctypes
import threading
import winsound

def play_success_sound():
    def sound():
        winsound.Beep(600, 150)
        winsound.Beep(800, 150)
        winsound.Beep(1200, 300)
    threading.Thread(target=sound, daemon=True).start()

def play_wrong_sound():
    threading.Thread(target=winsound.Beep, args=(300, 300), daemon=True).start()


try:
    user32 = ctypes.windll.user32
    user32.SetProcessDPIAware()
    SCREEN_WIDTH = user32.GetSystemMetrics(0)
    SCREEN_HEIGHT = user32.GetSystemMetrics(1)
except Exception:
    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 720

def process_frame_for_fullscreen(frame):
    h, w = frame.shape[:2]
    target_aspect = SCREEN_WIDTH / SCREEN_HEIGHT
    frame_aspect = w / h
    
    if frame_aspect > target_aspect:
        new_w = int(h * target_aspect)
        offset = (w - new_w) // 2
        frame = frame[:, offset:offset+new_w]
    else:
        new_h = int(w / target_aspect)
        offset = (h - new_h) // 2
        frame = frame[offset:offset+new_h, :]
        
    return cv2.resize(frame, (SCREEN_WIDTH, SCREEN_HEIGHT))

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles

INDEX_TIP, INDEX_PIP = 8, 6
MIDDLE_TIP, MIDDLE_PIP = 12, 10
RING_TIP, RING_PIP = 16, 14
PINKY_TIP, PINKY_PIP = 20, 18
THUMB_TIP, INDEX_MCP = 4, 5
WRIST, MIDDLE_MCP = 0, 9

# ---------------------- Layout ----------------------
CANVAS_W, CANVAS_H = 1280, 720
AVATAR_CX = CANVAS_W // 2
AVATAR_BASE_Y = 560   # "ground" level

# ---------------------- Timing ----------------------
DEMO_DURATION_S = 3.5        # slightly longer to let kids absorb the video
HOLD_MS_TO_LOCK = 800
FEEDBACK_DISPLAY_MS = 1800
TRAIN_HOLD_MS = 900
CELEBRATION_DURATION_S = 2.5  # celebration screen duration
CELEBRATION_EVERY_N = 5       # celebrate every N correct answers

# ---------------------- Mini-TV webcam corner ----------------------
TV_W, TV_H = 280, 210
TV_MARGIN = 30
TV_X = CANVAS_W - TV_W - TV_MARGIN
TV_Y = TV_MARGIN
TV_BEZEL = 16
TV_CORNER_RADIUS = 22

EMOTIONS = ["Excited", "Sad", "Angry", "Surprised"]

# Softer, child-friendly pastel colors (BGR)
EMOTION_COLOR = {
    "Excited":   (0, 230, 255),   # bright yellow
    "Sad":       (255, 140, 100), # bright blue
    "Angry":     (100, 100, 255), # bright red
    "Surprised": (255, 200, 50),  # bright cyan/teal
}

# Pastel card background colors (BGR) — softer for option cards
EMOTION_CARD_COLOR = {
    "Excited":   (170, 255, 255),
    "Sad":       (255, 200, 180),
    "Angry":     (180, 180, 255),
    "Surprised": (255, 240, 180),
}

# Simple emoji-style face representations (drawn procedurally)
EMOTION_EMOJI = {
    "Excited":   "happy",
    "Sad":       "sad",
    "Angry":     "angry",
    "Surprised": "surprised",
}

# ---------------------- Asset paths ----------------------
ASSET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "NEEDS", "body_says_it")

EMOTION_VIDEO_FILES = {
    "Excited":   os.path.join(ASSET_DIR, "excited.mp4"),
    "Sad":       os.path.join(ASSET_DIR, "sad.mp4"),
    "Angry":     os.path.join(ASSET_DIR, "angry.mp4"),
    "Surprised": os.path.join(ASSET_DIR, "surpriced.mp4"),
}

FINGER_IMAGE_FILES = {
    1: os.path.join(ASSET_DIR, "one in finger.jpeg"),
    2: os.path.join(ASSET_DIR, "two in finger.jpeg"),
    3: os.path.join(ASSET_DIR, "three in finger.jpeg"),
    4: os.path.join(ASSET_DIR, "four in finger.jpeg"),
    5: os.path.join(ASSET_DIR, "five in finger.jpeg"),
}

BACKGROUND_FILE = os.path.join(ASSET_DIR, "baground.jpeg")


# ==================== Asset Loading ====================

def load_background():
    """Load and resize the cartoon background image to canvas size."""
    img = cv2.imread(BACKGROUND_FILE)
    if img is None:
        print(f"WARNING: Could not load background from {BACKGROUND_FILE}, using gradient fallback.")
        return _make_gradient_fallback()
    return cv2.resize(img, (CANVAS_W, CANVAS_H), interpolation=cv2.INTER_AREA)


def _make_gradient_fallback():
    """Fallback gradient if background image is missing."""
    top = np.array([250, 235, 210], dtype=np.float32)
    bottom = np.array([235, 210, 220], dtype=np.float32)
    grad = np.zeros((CANVAS_H, CANVAS_W, 3), dtype=np.uint8)
    for y in range(CANVAS_H):
        f = y / (CANVAS_H - 1)
        row_color = (top * (1 - f) + bottom * f).astype(np.uint8)
        grad[y, :] = row_color
    return grad


def load_emotion_video_frames():
    """Pre-load all frames from each emotion video into memory for smooth looping."""
    all_frames = {}
    for emotion, path in EMOTION_VIDEO_FILES.items():
        frames = []
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            print(f"WARNING: Could not load video {path} for '{emotion}'")
            all_frames[emotion] = None
            continue
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            frames.append(frame)
        cap.release()
        if frames:
            all_frames[emotion] = frames
        else:
            all_frames[emotion] = None
            print(f"WARNING: No frames loaded from {path} for '{emotion}'")
    return all_frames


def _remove_white_bg(img, threshold=230):
    """Create a mask that removes near-white background pixels from the image.
    Returns (img_bgr, mask) where mask is 0 for white-bg pixels, 255 for foreground."""
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Pixels brighter than threshold are considered 'white background'
    _, mask = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY_INV)
    # Slight blur to soften edges
    mask = cv2.GaussianBlur(mask, (3, 3), 0)
    return mask


def load_finger_images(target_size=(100, 100)):
    """Load cartoon finger images, resize, and pre-compute their masks for compositing."""
    finger_data = {}
    for num, path in FINGER_IMAGE_FILES.items():
        img = cv2.imread(path)
        if img is None:
            print(f"WARNING: Could not load finger image {path}")
            finger_data[num] = None
            continue
        img = cv2.resize(img, target_size, interpolation=cv2.INTER_AREA)
        mask = _remove_white_bg(img)
        finger_data[num] = {"image": img, "mask": mask}
    return finger_data


def load_finger_images_small(target_size=(55, 55)):
    """Smaller version of finger images for option card icons."""
    return load_finger_images(target_size)


def load_finger_images_large(target_size=(180, 180)):
    """Larger version of finger images for training phase display."""
    return load_finger_images(target_size)


# ==================== Drawing Helpers ====================

def composite_image(canvas, img, mask, x, y):
    """Overlay img onto canvas at position (x, y) using the mask.
    Only non-white-background pixels are drawn."""
    h, w = img.shape[:2]
    # Clamp to canvas bounds
    x1, y1 = max(0, x), max(0, y)
    x2, y2 = min(CANVAS_W, x + w), min(CANVAS_H, y + h)
    if x1 >= x2 or y1 >= y2:
        return
    # Source region offset
    sx1, sy1 = x1 - x, y1 - y
    sx2, sy2 = sx1 + (x2 - x1), sy1 + (y2 - y1)

    roi = canvas[y1:y2, x1:x2]
    src = img[sy1:sy2, sx1:sx2]
    m = mask[sy1:sy2, sx1:sx2]

    # Normalize mask to 0.0-1.0
    m_f = m.astype(np.float32) / 255.0
    m_3 = np.stack([m_f, m_f, m_f], axis=-1)

    blended = (src.astype(np.float32) * m_3 + roi.astype(np.float32) * (1.0 - m_3)).astype(np.uint8)
    canvas[y1:y2, x1:x2] = blended


def draw_rounded_rect(canvas, x1, y1, x2, y2, color, radius=18, thickness=-1, border_color=None, border_thickness=2):
    """Draw a rounded rectangle with optional border. Works with filled (-1) or outline."""
    # Use OpenCV's basic shapes to approximate rounded corners
    r = min(radius, (x2 - x1) // 2, (y2 - y1) // 2)

    # Create an overlay for alpha blending if needed
    if thickness == -1:
        # Top bar
        cv2.rectangle(canvas, (x1 + r, y1), (x2 - r, y2), color, -1)
        # Left bar
        cv2.rectangle(canvas, (x1, y1 + r), (x2, y2 - r), color, -1)
        # Four corner circles
        cv2.circle(canvas, (x1 + r, y1 + r), r, color, -1)
        cv2.circle(canvas, (x2 - r, y1 + r), r, color, -1)
        cv2.circle(canvas, (x1 + r, y2 - r), r, color, -1)
        cv2.circle(canvas, (x2 - r, y2 - r), r, color, -1)

    if border_color is not None:
        # Draw border outline on top
        cv2.line(canvas, (x1 + r, y1), (x2 - r, y1), border_color, border_thickness)
        cv2.line(canvas, (x1 + r, y2), (x2 - r, y2), border_color, border_thickness)
        cv2.line(canvas, (x1, y1 + r), (x1, y2 - r), border_color, border_thickness)
        cv2.line(canvas, (x2, y1 + r), (x2, y2 - r), border_color, border_thickness)
        cv2.ellipse(canvas, (x1 + r, y1 + r), (r, r), 180, 0, 90, border_color, border_thickness)
        cv2.ellipse(canvas, (x2 - r, y1 + r), (r, r), 270, 0, 90, border_color, border_thickness)
        cv2.ellipse(canvas, (x1 + r, y2 - r), (r, r), 90, 0, 90, border_color, border_thickness)
        cv2.ellipse(canvas, (x2 - r, y2 - r), (r, r), 0, 0, 90, border_color, border_thickness)


def draw_emoji_face(canvas, cx, cy, radius, emotion_type):
    """Draw a simple cartoon emoji face for the given emotion type."""
    r = radius
    # Face circle with soft yellow
    cv2.circle(canvas, (cx, cy), r, (60, 220, 255), -1)
    cv2.circle(canvas, (cx, cy), r, (40, 180, 220), 2)

    if emotion_type == "happy":
        # Happy eyes (solid dots)
        cv2.circle(canvas, (cx - r // 3, cy - r // 5), r // 7, (50, 50, 50), -1)
        cv2.circle(canvas, (cx + r // 3, cy - r // 5), r // 7, (50, 50, 50), -1)
        # Smile arc
        cv2.ellipse(canvas, (cx, cy + r // 6), (r // 2, r // 3), 0, 10, 170, (50, 50, 50), 2)

    elif emotion_type == "sad":
        # Sad eyes (dots lower)
        cv2.circle(canvas, (cx - r // 3, cy - r // 6), r // 7, (50, 50, 50), -1)
        cv2.circle(canvas, (cx + r // 3, cy - r // 6), r // 7, (50, 50, 50), -1)
        # Frown arc
        cv2.ellipse(canvas, (cx, cy + r // 2), (r // 2, r // 4), 0, 190, 350, (50, 50, 50), 2)
        # Tear drop
        cv2.circle(canvas, (cx - r // 3, cy + r // 8), r // 9, (200, 150, 80), -1)

    elif emotion_type == "angry":
        # Angry eyebrows (V-shaped)
        cv2.line(canvas, (cx - r // 2, cy - r // 3), (cx - r // 6, cy - r // 5), (50, 50, 50), 2)
        cv2.line(canvas, (cx + r // 2, cy - r // 3), (cx + r // 6, cy - r // 5), (50, 50, 50), 2)
        # Angry eyes
        cv2.circle(canvas, (cx - r // 3, cy - r // 8), r // 8, (50, 50, 50), -1)
        cv2.circle(canvas, (cx + r // 3, cy - r // 8), r // 8, (50, 50, 50), -1)
        # Tight frown
        cv2.line(canvas, (cx - r // 3, cy + r // 3), (cx + r // 3, cy + r // 3), (50, 50, 50), 2)

    elif emotion_type == "surprised":
        # Wide open eyes (circles)
        cv2.circle(canvas, (cx - r // 3, cy - r // 5), r // 5, (50, 50, 50), 2)
        cv2.circle(canvas, (cx + r // 3, cy - r // 5), r // 5, (50, 50, 50), 2)
        cv2.circle(canvas, (cx - r // 3, cy - r // 5), r // 9, (50, 50, 50), -1)
        cv2.circle(canvas, (cx + r // 3, cy - r // 5), r // 9, (50, 50, 50), -1)
        # Open mouth (O shape)
        cv2.circle(canvas, (cx, cy + r // 3), r // 4, (50, 50, 50), 2)
        # Raised eyebrows
        cv2.line(canvas, (cx - r // 2, cy - r // 2), (cx - r // 6, cy - r * 2 // 3), (50, 50, 50), 2)
        cv2.line(canvas, (cx + r // 2, cy - r // 2), (cx + r // 6, cy - r * 2 // 3), (50, 50, 50), 2)


def draw_star(canvas, cx, cy, outer_r, inner_r, color, thickness=-1):
    """Draw a 5-pointed star at (cx, cy)."""
    points = []
    for i in range(10):
        angle = math.radians(i * 36 - 90)
        r = outer_r if i % 2 == 0 else inner_r
        px = int(cx + r * math.cos(angle))
        py = int(cy + r * math.sin(angle))
        points.append([px, py])
    pts = np.array(points, np.int32).reshape((-1, 1, 2))
    cv2.fillPoly(canvas, [pts], color)
    cv2.polylines(canvas, [pts], True, (max(0, color[0] - 40), max(0, color[1] - 40), max(0, color[2] - 40)), 2)


def put_text_shadow(canvas, text, pos, font, scale, color, thickness, shadow_color=(40, 40, 40)):
    """Draw text with a subtle shadow underneath for better readability."""
    sx, sy = pos[0] + 2, pos[1] + 2
    cv2.putText(canvas, text, (sx, sy), font, scale, shadow_color, thickness + 1, cv2.LINE_AA)
    cv2.putText(canvas, text, pos, font, scale, color, thickness, cv2.LINE_AA)


# ==================== Confetti Particle System ====================

class ConfettiSystem:
    """Simple confetti particle system for celebration moments."""

    def __init__(self):
        self.particles = []
        self.colors = [
            (80, 210, 255),   # yellow
            (120, 255, 120),  # green
            (255, 170, 100),  # blue
            (180, 130, 255),  # pink
            (100, 255, 255),  # cyan
            (200, 200, 100),  # light blue
            (130, 220, 255),  # orange
        ]

    def spawn(self, count=80):
        """Spawn a burst of confetti particles across the top of the screen."""
        for _ in range(count):
            self.particles.append({
                "x": random.uniform(50, CANVAS_W - 50),
                "y": random.uniform(-50, 50),
                "vx": random.uniform(-3, 3),
                "vy": random.uniform(1.5, 5),
                "size": random.randint(5, 12),
                "color": random.choice(self.colors),
                "rotation": random.uniform(0, 360),
                "rot_speed": random.uniform(-8, 8),
                "life": random.uniform(1.5, 3.5),
                "born": time.time(),
                "shape": random.choice(["rect", "circle", "triangle"]),
            })

    def update_and_draw(self, canvas):
        """Update physics and draw all living particles."""
        now = time.time()
        alive = []
        for p in self.particles:
            age = now - p["born"]
            if age > p["life"]:
                continue
            # Gravity + drift
            p["x"] += p["vx"]
            p["vy"] += 0.08  # gentle gravity
            p["y"] += p["vy"]
            p["vx"] *= 0.995  # slight air resistance
            p["rotation"] += p["rot_speed"]

            # Fade out near end of life
            alpha = max(0.0, 1.0 - age / p["life"])
            if alpha < 0.1:
                continue

            x, y = int(p["x"]), int(p["y"])
            s = p["size"]
            color = p["color"]

            if 0 <= x < CANVAS_W and 0 <= y < CANVAS_H:
                if p["shape"] == "circle":
                    cv2.circle(canvas, (x, y), s // 2, color, -1)
                elif p["shape"] == "rect":
                    angle = math.radians(p["rotation"])
                    # Rotated rectangle
                    pts = []
                    for dx, dy in [(-s // 2, -s // 4), (s // 2, -s // 4), (s // 2, s // 4), (-s // 2, s // 4)]:
                        rx = int(x + dx * math.cos(angle) - dy * math.sin(angle))
                        ry = int(y + dx * math.sin(angle) + dy * math.cos(angle))
                        pts.append([rx, ry])
                    pts_arr = np.array(pts, np.int32).reshape((-1, 1, 2))
                    cv2.fillPoly(canvas, [pts_arr], color)
                elif p["shape"] == "triangle":
                    angle = math.radians(p["rotation"])
                    pts = []
                    for i in range(3):
                        a = angle + math.radians(i * 120)
                        px = int(x + s * 0.6 * math.cos(a))
                        py = int(y + s * 0.6 * math.sin(a))
                        pts.append([px, py])
                    pts_arr = np.array(pts, np.int32).reshape((-1, 1, 2))
                    cv2.fillPoly(canvas, [pts_arr], color)

            alive.append(p)
        self.particles = alive

    @property
    def active(self):
        return len(self.particles) > 0


# ==================== Video Playback for Emotion Clips ====================

def draw_emotion_video_frame(canvas, emotion_frames, emotion, t, display_size=(300, 300)):
    """Draw the current frame of the emotion video clip centered on screen.
    Loops the video based on elapsed time t."""
    frames = emotion_frames.get(emotion)
    if frames is None or len(frames) == 0:
        # Fallback: draw a text label if video is missing
        put_text_shadow(canvas, f"[{emotion}]", (AVATAR_CX - 60, AVATAR_BASE_Y - 120),
                        cv2.FONT_HERSHEY_DUPLEX, 1.2, EMOTION_COLOR[emotion], 2)
        return

    # Pick frame based on time, looping
    num_frames = len(frames)
    # Use a consistent 15fps playback rate for smooth looping
    frame_idx = int(t * 15) % num_frames
    frame = frames[frame_idx]

    # Resize to display size
    disp = cv2.resize(frame, display_size, interpolation=cv2.INTER_AREA)

    # Remove white/light background from the video frame
    mask = _remove_white_bg(disp, threshold=225)

    # Center position
    cx = AVATAR_CX - display_size[0] // 2
    cy = AVATAR_BASE_Y - display_size[1] - 20  # position above "ground"

    composite_image(canvas, disp, mask, cx, cy)


# ==================== Stick-figure fallback (kept for safety if videos fail) ====================

def _draw_limb(canvas, p1, p2, color, thickness=6):
    cv2.line(canvas, (int(p1[0]), int(p1[1])), (int(p2[0]), int(p2[1])), color, thickness, cv2.LINE_AA)


def draw_excited(canvas, t, color):
    bounce = abs(math.sin(t * 2 * math.pi * 2)) * 55
    cx = AVATAR_CX
    hip_y = AVATAR_BASE_Y - 90 - bounce
    head_y = hip_y - 70
    cv2.circle(canvas, (cx, int(head_y)), 26, color, -1)
    _draw_limb(canvas, (cx, head_y + 26), (cx, hip_y), color, 8)
    arm_lift = 40 + bounce * 0.3
    _draw_limb(canvas, (cx, head_y + 45), (cx - 55, head_y - arm_lift), color)
    _draw_limb(canvas, (cx, head_y + 45), (cx + 55, head_y - arm_lift), color)
    leg_spread = 8 if bounce > 25 else 22
    _draw_limb(canvas, (cx, hip_y), (cx - leg_spread, AVATAR_BASE_Y - bounce * 0.4), color)
    _draw_limb(canvas, (cx, hip_y), (cx + leg_spread, AVATAR_BASE_Y - bounce * 0.4), color)


def draw_sad(canvas, t, color):
    droop = 8 * math.sin(t * 2 * math.pi * 0.4)
    cx = AVATAR_CX
    hip_y = AVATAR_BASE_Y - 90
    head_y = hip_y - 55 + droop
    cv2.circle(canvas, (cx, int(head_y)), 26, color, -1)
    _draw_limb(canvas, (cx, head_y + 26), (cx, hip_y), color, 8)
    _draw_limb(canvas, (cx, head_y + 35), (cx - 30, hip_y - 10), color)
    _draw_limb(canvas, (cx, head_y + 35), (cx + 30, hip_y - 10), color)
    _draw_limb(canvas, (cx, hip_y), (cx - 16, AVATAR_BASE_Y), color)
    _draw_limb(canvas, (cx, hip_y), (cx + 16, AVATAR_BASE_Y), color)


def draw_angry(canvas, t, color):
    jitter = math.sin(t * 2 * math.pi * 9) * 3
    cx = AVATAR_CX + jitter
    hip_y = AVATAR_BASE_Y - 90
    head_y = hip_y - 65
    cv2.circle(canvas, (int(cx), int(head_y)), 26, color, -1)
    cv2.line(canvas, (int(cx - 16), int(head_y - 8)), (int(cx - 4), int(head_y - 2)), (255, 255, 255), 2)
    cv2.line(canvas, (int(cx + 16), int(head_y - 8)), (int(cx + 4), int(head_y - 2)), (255, 255, 255), 2)
    _draw_limb(canvas, (cx, head_y + 26), (cx, hip_y), color, 9)
    _draw_limb(canvas, (cx, head_y + 35), (cx - 35, hip_y - 20), color)
    _draw_limb(canvas, (cx, head_y + 35), (cx + 35, hip_y - 20), color)
    cv2.circle(canvas, (int(cx - 35), int(hip_y - 20)), 8, color, -1)
    cv2.circle(canvas, (int(cx + 35), int(hip_y - 20)), 8, color, -1)
    _draw_limb(canvas, (cx, hip_y), (cx - 32, AVATAR_BASE_Y), color)
    _draw_limb(canvas, (cx, hip_y), (cx + 32, AVATAR_BASE_Y), color)


def draw_surprised(canvas, t, color):
    cycle = t % 1.0
    if cycle < 0.15:
        pulse = cycle / 0.15
    elif cycle < 0.35:
        pulse = 1.0 - (cycle - 0.15) / 0.2
    else:
        pulse = 0.0
    cx = AVATAR_CX
    hip_y = AVATAR_BASE_Y - 90 - pulse * 15
    head_y = hip_y - 65 - pulse * 10
    cv2.circle(canvas, (cx, int(head_y)), 26, color, -1)
    cv2.circle(canvas, (cx - 9, int(head_y - 3)), 5, (255, 255, 255), 1)
    cv2.circle(canvas, (cx + 9, int(head_y - 3)), 5, (255, 255, 255), 1)
    cv2.circle(canvas, (cx, int(head_y + 10)), 4, (255, 255, 255), 1)
    _draw_limb(canvas, (cx, head_y + 26), (cx, hip_y), color, 8)
    arm_lift = 30 + pulse * 60
    _draw_limb(canvas, (cx, head_y + 40), (cx - 45, head_y - arm_lift), color)
    _draw_limb(canvas, (cx, head_y + 40), (cx + 45, head_y - arm_lift), color)
    _draw_limb(canvas, (cx, hip_y), (cx - 18, AVATAR_BASE_Y), color)
    _draw_limb(canvas, (cx, hip_y), (cx + 18, AVATAR_BASE_Y), color)


AVATAR_DRAWERS = {
    "Excited": draw_excited,
    "Sad": draw_sad,
    "Angry": draw_angry,
    "Surprised": draw_surprised,
}


# ==================== Hand gesture: finger counting (1-4) ====================

def count_selection_fingers(landmarks):
    """1-4 count, used by the main game's 4-option answer (Excited/Sad/Angry/Surprised)."""
    result = count_fingers_1_to_5(landmarks)
    return result if result in (1, 2, 3, 4) else None


def _finger_extended(hand_lm, tip_idx, pip_idx):
    return hand_lm[tip_idx].y < hand_lm[pip_idx].y

def count_fingers_1_to_5(landmarks):
    """
    Simple 1-5 finger count using simple y-coordinate logic as requested.
    Ignores thumb for 1-3 because kids might tuck it weirdly.
    """
    count = 0
    if _finger_extended(landmarks, INDEX_TIP, INDEX_PIP): count += 1
    if _finger_extended(landmarks, MIDDLE_TIP, MIDDLE_PIP): count += 1
    if _finger_extended(landmarks, RING_TIP, RING_PIP): count += 1
    if _finger_extended(landmarks, PINKY_TIP, PINKY_PIP): count += 1

    if count in (1, 2, 3):
        return count
    elif count == 4:
        # Distinguish 4 from 5 by checking if thumb is extended outwards.
        d_thumb_pinky = math.hypot(landmarks[4].x - landmarks[17].x, landmarks[4].y - landmarks[17].y)
        d_palm = math.hypot(landmarks[5].x - landmarks[17].x, landmarks[5].y - landmarks[17].y)
        
        # If thumb is extended, it's much further from the pinky base than the width of the palm.
        if d_thumb_pinky > d_palm * 1.2:
            return 5
        else:
            return 4
    elif count == 0:
        d_thumb_pinky = math.hypot(landmarks[4].x - landmarks[17].x, landmarks[4].y - landmarks[17].y)
        d_palm = math.hypot(landmarks[5].x - landmarks[17].x, landmarks[5].y - landmarks[17].y)
        if d_thumb_pinky > d_palm * 1.2:
            return 1
            
    return None


# ==================== Round management ====================

def spawn_round(previous=None):
    choices = [e for e in EMOTIONS if e != previous] or EMOTIONS
    target = random.choice(choices)
    options = EMOTIONS[:]
    random.shuffle(options)
    correct_option = options.index(target) + 1
    return {"target": target, "options": options, "correct_option": correct_option}


# ==================== Drawing: Mini-TV with rounded corners ====================

def draw_big_webcam(canvas, webcam_frame):
    """Draws a large webcam feed on the right side of the screen for the training phase,
    so kids can clearly see themselves and their hand gestures."""
    big_w, big_h = 480, 360
    big_x = CANVAS_W - big_w - 30
    big_y = (CANVAS_H - big_h) // 2
    bezel = 12
    corner_r = 20

    # Antenna with colorful balls
    cx_big = big_x + big_w // 2
    cv2.line(canvas, (cx_big - 8, big_y - bezel), (cx_big - 45, big_y - 50), (80, 80, 90), 3, cv2.LINE_AA)
    cv2.line(canvas, (cx_big + 8, big_y - bezel), (cx_big + 45, big_y - 50), (80, 80, 90), 3, cv2.LINE_AA)
    cv2.circle(canvas, (cx_big - 45, big_y - 50), 7, (100, 200, 255), -1)
    cv2.circle(canvas, (cx_big + 45, big_y - 50), 7, (255, 150, 100), -1)

    # Bezel (outer frame)
    bx1, by1 = big_x - bezel, big_y - bezel
    bx2, by2 = big_x + big_w + bezel, big_y + big_h + bezel
    draw_rounded_rect(canvas, bx1, by1, bx2, by2, (55, 55, 65), radius=corner_r,
                      border_color=(130, 130, 140), border_thickness=3)

    # Video feed
    thumb = cv2.resize(webcam_frame, (big_w, big_h))
    canvas[big_y:big_y + big_h, big_x:big_x + big_w] = thumb

    # Stand below the TV
    stand_w = 55
    draw_rounded_rect(canvas, cx_big - stand_w // 2, by2, cx_big + stand_w // 2, by2 + 14,
                      (55, 55, 65), radius=6)
    draw_rounded_rect(canvas, cx_big - stand_w, by2 + 14, cx_big + stand_w, by2 + 24,
                      (55, 55, 65), radius=6)

    # Label
    put_text_shadow(canvas, "You", (big_x, by1 - 12), cv2.FONT_HERSHEY_DUPLEX, 0.7, (220, 220, 230), 1)


def draw_mini_tv(canvas, webcam_frame):
    """Draws the webcam feed as a small 'mini TV' in the top-right corner with
    a cartoon-style rounded bezel, antenna, and stand."""
    cx = TV_X + TV_W // 2

    # Antenna with little balls on top
    cv2.line(canvas, (cx - 6, TV_Y - TV_BEZEL), (cx - 35, TV_Y - 40), (80, 80, 90), 3, cv2.LINE_AA)
    cv2.line(canvas, (cx + 6, TV_Y - TV_BEZEL), (cx + 35, TV_Y - 40), (80, 80, 90), 3, cv2.LINE_AA)
    cv2.circle(canvas, (cx - 35, TV_Y - 40), 5, (100, 200, 255), -1)
    cv2.circle(canvas, (cx + 35, TV_Y - 40), 5, (255, 150, 100), -1)

    # Bezel (outer frame) — rounded rectangle
    bx1, by1 = TV_X - TV_BEZEL, TV_Y - TV_BEZEL
    bx2, by2 = TV_X + TV_W + TV_BEZEL, TV_Y + TV_H + TV_BEZEL
    draw_rounded_rect(canvas, bx1, by1, bx2, by2, (55, 55, 65), radius=TV_CORNER_RADIUS,
                      border_color=(130, 130, 140), border_thickness=2)

    # Video feed
    thumb = cv2.resize(webcam_frame, (TV_W, TV_H))
    canvas[TV_Y:TV_Y + TV_H, TV_X:TV_X + TV_W] = thumb

    # Small stand below the TV
    stand_w = 40
    draw_rounded_rect(canvas, cx - stand_w // 2, by2, cx + stand_w // 2, by2 + 12,
                      (55, 55, 65), radius=5)
    draw_rounded_rect(canvas, cx - stand_w, by2 + 12, cx + stand_w, by2 + 20,
                      (55, 55, 65), radius=5)

    # Label
    put_text_shadow(canvas, "You", (TV_X, by1 - 10), cv2.FONT_HERSHEY_DUPLEX, 0.5, (220, 220, 230), 1)


# ==================== Drawing: Option Cards (main game HUD) ====================

def draw_options_hud(canvas, round_data, locked_option, finger_icons_small, hold_selection, hold_progress):
    """Draw option cards with emoji faces, finger icons, and highlight for locked selection."""
    card_x = 30
    card_y_start = 30
    card_w = 340
    card_h = 75
    card_gap = 15

    for i, label in enumerate(round_data["options"]):
        option_number = i + 1
        cy = card_y_start + i * (card_h + card_gap)

        # Determine card state
        is_locked = locked_option is not None and locked_option == option_number
        is_holding = hold_selection == option_number and locked_option is None

        # Card background color
        if is_locked:
            is_correct = locked_option == round_data["correct_option"]
            bg_color = (160, 255, 160) if is_correct else (180, 190, 255)
            border_col = (50, 220, 50) if is_correct else (120, 120, 255)
        elif is_holding:
            bg_color = EMOTION_CARD_COLOR[label]
            border_col = EMOTION_COLOR[label]
        else:
            bg_color = (250, 250, 255)
            border_col = (200, 200, 220)

        # Draw card background
        draw_rounded_rect(canvas, card_x, cy, card_x + card_w, cy + card_h,
                          bg_color, radius=20, border_color=border_col, border_thickness=5)

        # If holding this option, draw a small progress indicator on the card
        if is_holding and hold_progress > 0:
            progress_w = int((card_w - 12) * hold_progress)
            bar_y = cy + card_h - 10
            cv2.rectangle(canvas, (card_x + 6, bar_y), (card_x + 6 + progress_w, bar_y + 5),
                          EMOTION_COLOR[label], -1)

        # Finger icon (small cartoon hand)
        icon_data = finger_icons_small.get(option_number)
        if icon_data is not None:
            icon_x = card_x + 12
            icon_y = cy + (card_h - icon_data["image"].shape[0]) // 2
            composite_image(canvas, icon_data["image"], icon_data["mask"], icon_x, icon_y)

        # Emoji face next to the label
        emoji_cx = card_x + 95
        emoji_cy = cy + card_h // 2
        draw_emoji_face(canvas, emoji_cx, emoji_cy, 22, EMOTION_EMOJI[label])

        # Label text
        text_x = card_x + 130
        text_y = cy + card_h // 2 + 10
        text_color = (30, 30, 40) if not is_locked else ((20, 140, 20) if locked_option == round_data["correct_option"] else (50, 50, 180))
        put_text_shadow(canvas, f"{option_number}. {label}", (text_x, text_y),
                        cv2.FONT_HERSHEY_DUPLEX, 0.9, text_color, 2, (180, 180, 180))


# ==================== Drawing: Stats HUD with Stars ====================

def draw_stats_hud(canvas, correct_count, total_rounds, avg_response_s, last_response_s):
    """Draw stats with star icons instead of raw numbers."""
    stats_x = TV_X - 20
    stats_y = TV_Y + TV_H + 50

    # Draw a soft glassmorphic backdrop for stats
    draw_rounded_rect(canvas, stats_x - 15, stats_y - 15, stats_x + 280, stats_y + 110, (255, 255, 255), radius=16, border_color=(200, 230, 255), border_thickness=3)
    overlay = canvas.copy()
    draw_rounded_rect(overlay, stats_x - 15, stats_y - 15, stats_x + 280, stats_y + 110, (230, 240, 250), radius=16)
    cv2.addWeighted(overlay, 0.8, canvas, 0.2, 0, canvas)

    # Stars earned
    for i in range(min(correct_count, 14)):  # show up to 14 stars to fit
        row = i // 7
        col = i % 7
        sx = stats_x + col * 35 + 15
        sy = stats_y + row * 35 + 10
        draw_star(canvas, sx, sy, 14, 7, (30, 210, 255))  # gold stars

    # Text stats below stars
    star_rows = min(2, (min(correct_count, 14) + 6) // 7) if correct_count > 0 else 0
    text_y = stats_y + star_rows * 35 + 25

    accuracy = (correct_count / total_rounds * 100) if total_rounds else 0.0
    put_text_shadow(canvas, f"Score: {correct_count}/{total_rounds} ({accuracy:.0f}%)",
                    (stats_x, text_y), cv2.FONT_HERSHEY_DUPLEX, 0.6, (40, 100, 200), 2)
    if total_rounds > 0:
        put_text_shadow(canvas, f"Avg: {avg_response_s:.1f}s",
                        (stats_x, text_y + 28), cv2.FONT_HERSHEY_DUPLEX, 0.55, (60, 60, 80), 2)
    if last_response_s is not None:
        put_text_shadow(canvas, f"Last: {last_response_s:.1f}s",
                        (stats_x + 130, text_y + 28), cv2.FONT_HERSHEY_DUPLEX, 0.55, (60, 60, 80), 2)


# ==================== Drawing: Circular Progress Ring (Training) ====================

def draw_progress_ring(canvas, cx, cy, radius, progress, color, bg_color=(220, 220, 225), thickness=8):
    """Draw a circular progress ring."""
    # Background ring
    cv2.circle(canvas, (cx, cy), radius, bg_color, thickness, cv2.LINE_AA)
    # Progress arc
    if progress > 0:
        end_angle = int(progress * 360)
        cv2.ellipse(canvas, (cx, cy), (radius, radius), -90, 0, end_angle, color, thickness, cv2.LINE_AA)


# ==================== Drawing: Pulsing Text ====================

def draw_pulsing_text(canvas, text, base_pos, font, base_scale, color, thickness, t):
    """Draw text with a gentle pulsing scale animation."""
    pulse = 1.0 + 0.06 * math.sin(t * 2 * math.pi * 0.8)
    scale = base_scale * pulse
    # Adjust position slightly to keep it visually centered during pulse
    text_size = cv2.getTextSize(text, font, scale, thickness)[0]
    base_text_size = cv2.getTextSize(text, font, base_scale, thickness)[0]
    dx = (base_text_size[0] - text_size[0]) // 2
    dy = (base_text_size[1] - text_size[1]) // 2
    pos = (base_pos[0] + dx, base_pos[1] - dy)
    put_text_shadow(canvas, text, pos, font, scale, color, thickness)


# ==================== Drawing: Screen Border Flash ====================

def draw_border_flash(canvas, is_correct, alpha):
    """Flash the screen border green (correct) or soft orange (try again)."""
    if alpha <= 0:
        return
    color = (80, 220, 100) if is_correct else (80, 180, 240)  # green or soft orange
    thickness = int(12 * alpha)
    if thickness < 1:
        return
    overlay = canvas.copy()
    cv2.rectangle(overlay, (0, 0), (CANVAS_W - 1, CANVAS_H - 1), color, thickness)
    cv2.addWeighted(overlay, alpha * 0.7, canvas, 1.0 - alpha * 0.7, 0, canvas)


# ==================== Drawing: Celebration Screen ====================

def draw_celebration_screen(canvas, t, correct_count, confetti):
    """Draw a brief celebration screen with stars and confetti."""
    # Semi-transparent overlay
    overlay = canvas.copy()
    cv2.rectangle(overlay, (0, 0), (CANVAS_W, CANVAS_H), (220, 255, 255), -1)
    cv2.addWeighted(overlay, 0.6, canvas, 0.4, 0, canvas)

    # Big "Great Job!" text with gentle bounce
    bounce = abs(math.sin(t * 4)) * 15
    put_text_shadow(canvas, "AWESOME!", (CANVAS_W // 2 - 250, int(CANVAS_H // 2 - 60 - bounce)),
                    cv2.FONT_HERSHEY_DUPLEX, 3.0, (50, 200, 255), 6)

    # Star burst around the text
    for i in range(12):
        angle = math.radians(i * 30 + t * 90)
        dist = 180 + 30 * math.sin(t * 5 + i)
        sx = int(CANVAS_W // 2 + dist * math.cos(angle))
        sy = int(CANVAS_H // 2 - 40 + dist * math.sin(angle))
        draw_star(canvas, sx, sy, 20, 10, (0, 240, 255))
        draw_star(canvas, sx, sy, 12, 6, (255, 255, 255))

    # Score text
    put_text_shadow(canvas, f"{correct_count} Stars Earned!",
                    (CANVAS_W // 2 - 130, CANVAS_H // 2 + 30),
                    cv2.FONT_HERSHEY_DUPLEX, 1.0, (60, 180, 255), 2)

    # Confetti
    confetti.update_and_draw(canvas)


# ==================== Finger Training Phase ====================

def run_finger_training(cap, hands, bg_image, finger_imgs_large):
    """Teaches numbers 1-5 in order before the main game starts. Shows cartoon finger
    guide images. Returns False if the user quit ('q') during training, True if completed."""
    for target_number in range(1, 6):
        hold_start = None
        while True:
            success, frame = cap.read()
            if not success:
                return False
            frame = cv2.flip(frame, 1)

            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = hands.process(rgb)
            detected = None
            if results.multi_hand_landmarks:
                hand_landmarks = results.multi_hand_landmarks[0]
                detected = count_fingers_1_to_5(hand_landmarks.landmark)
                mp_drawing.draw_landmarks(
                    frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                    mp_styles.get_default_hand_landmarks_style(),
                    mp_styles.get_default_hand_connections_style(),
                )

            # Use cartoon background
            canvas = bg_image.copy()

            # Semi-transparent dark overlay for training focus
            overlay = canvas.copy()
            cv2.rectangle(overlay, (0, 0), (CANVAS_W, CANVAS_H), (30, 25, 20), -1)
            cv2.addWeighted(overlay, 0.35, canvas, 0.65, 0, canvas)

            # Draw BIG webcam feed for training (kids need to see themselves clearly)
            draw_big_webcam(canvas, frame)

            progress = 0.0
            if detected == target_number:
                if hold_start is None:
                    hold_start = time.time()
                held_ms = (time.time() - hold_start) * 1000
                progress = min(1.0, held_ms / TRAIN_HOLD_MS)
                if held_ms >= TRAIN_HOLD_MS:
                    break
            else:
                hold_start = None

            # Title
            put_text_shadow(canvas, "Finger Training", (40, 65),
                            cv2.FONT_HERSHEY_DUPLEX, 1.2, (255, 255, 255), 3)

            # Instruction with pulsing
            draw_pulsing_text(canvas, f"Show me {target_number} finger{'s' if target_number > 1 else ''}!",
                              (40, 130), cv2.FONT_HERSHEY_DUPLEX, 1.6, (80, 245, 255), 4, time.time())

            # Show the large cartoon finger guide image — on the LEFT side
            # (big webcam is on the right side)
            left_center_x = (CANVAS_W - 480 - 30) // 2  # left half center (accounting for big webcam)
            finger_data = finger_imgs_large.get(target_number)
            if finger_data is not None:
                img = finger_data["image"]
                mask = finger_data["mask"]
                fx = left_center_x - img.shape[1] // 2
                fy = CANVAS_H // 2 - img.shape[0] // 2 + 30
                composite_image(canvas, img, mask, fx, fy)

            # Detected count display
            detected_text = f"Detected: {detected}" if detected is not None else "Detected: —"
            detected_color = (120, 255, 120) if detected == target_number else (220, 220, 230)
            put_text_shadow(canvas, detected_text, (40, 155),
                            cv2.FONT_HERSHEY_DUPLEX, 0.7, detected_color, 1)

            # Circular progress ring — on the LEFT side
            ring_cx = left_center_x
            ring_cy = CANVAS_H // 2 + 30
            ring_color = (120, 255, 120) if detected == target_number else (200, 200, 210)
            draw_progress_ring(canvas, ring_cx, ring_cy, 110, progress, ring_color, thickness=10)

            # Number step indicators at the bottom — on the LEFT side
            for n in range(1, 6):
                nx = left_center_x + (n - 3) * 60
                ny = CANVAS_H - 60
                if n < target_number:
                    color, fill = (120, 230, 120), -1     # completed — green
                elif n == target_number:
                    color, fill = (80, 245, 255), -1       # current — yellow
                else:
                    color, fill = (180, 180, 190), 2       # upcoming — outline

                cv2.circle(canvas, (nx, ny), 22, color, fill, cv2.LINE_AA)
                if fill == -1:
                    cv2.circle(canvas, (nx, ny), 22, (max(0, color[0] - 30), max(0, color[1] - 30), max(0, color[2] - 30)), 2, cv2.LINE_AA)
                text_color = (30, 30, 40) if fill == -1 else color
                cv2.putText(canvas, str(n), (nx - 8, ny + 8),
                            cv2.FONT_HERSHEY_DUPLEX, 0.6, text_color, 2, cv2.LINE_AA)

            display_frame = process_frame_for_fullscreen(canvas)
            last_display_frame = display_frame
            cv2.imshow("Body Says It", display_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                return False

        # Brief "Nice!" celebration between numbers
        confetti = ConfettiSystem()
        confetti.spawn(40)
        pause_start = time.time()
        while time.time() - pause_start < 1.0:
            success, frame = cap.read()
            if not success:
                return False
            frame = cv2.flip(frame, 1)
            canvas = bg_image.copy()
            overlay = canvas.copy()
            cv2.rectangle(overlay, (0, 0), (CANVAS_W, CANVAS_H), (30, 25, 20), -1)
            cv2.addWeighted(overlay, 0.35, canvas, 0.65, 0, canvas)
            draw_big_webcam(canvas, frame)

            put_text_shadow(canvas, "Nice!", (CANVAS_W // 2 - 70, CANVAS_H // 2 - 10),
                            cv2.FONT_HERSHEY_DUPLEX, 1.8, (120, 255, 120), 3)

            # Show a small star
            draw_star(canvas, CANVAS_W // 2, CANVAS_H // 2 + 50, 25, 12, (30, 210, 255))

            confetti.update_and_draw(canvas)

            display_frame = process_frame_for_fullscreen(canvas)
            cv2.imshow("Body Says It", display_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                return False

    return True


# ==================== Main Game Loop ====================

def main():
    # ---- Load assets ----
    print("Loading assets...")
    bg_image = load_background()
    emotion_frames = load_emotion_video_frames()
    finger_icons_small = load_finger_images_small()
    finger_icons_large = load_finger_images_large()
    print("Assets loaded.")

    # ---- Camera ----
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Could not open webcam.")
        return
        
    cv2.namedWindow("Body Says It", cv2.WND_PROP_FULLSCREEN)
    cv2.setWindowProperty("Body Says It", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    hands = mp_hands.Hands(
        max_num_hands=1,
        model_complexity=0,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6,
    )

    # ---- Finger training ----
    completed_training = run_finger_training(cap, hands, bg_image, finger_icons_large)
    if not completed_training:
        cap.release()
        hands.close()
        cv2.destroyAllWindows()
        return

    # ---- Game state ----
    confetti = ConfettiSystem()
    start_time = time.time()
    last_display_frame = None
    correct_count = 0
    total_rounds = 0
    response_times = []
    last_response_s = None
    last_celebration_at = 0  # tracks the correct_count at which we last celebrated

    round_data = spawn_round()
    demo_start = time.time()
    demo_phase = True
    answer_open_time = None

    hold_selection = None
    hold_start = None
    locked_option = None
    locked_at = None
    flash_start = None
    flash_correct = False

    # Celebration state
    celebrating = False
    celebration_start = 0

    while True:
        success, frame = cap.read()
        if not success:
            break
        frame = cv2.flip(frame, 1)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(rgb)
        selection = None
        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            selection = count_selection_fingers(hand_landmarks.landmark)
            mp_drawing.draw_landmarks(
                frame, hand_landmarks, mp_hands.HAND_CONNECTIONS,
                mp_styles.get_default_hand_landmarks_style(),
                mp_styles.get_default_hand_connections_style(),
            )

        # ---- Build canvas ----
        canvas = bg_image.copy()

        # ---- Celebration screen ----
        if celebrating:
            cel_t = time.time() - celebration_start
            draw_celebration_screen(canvas, cel_t, correct_count, confetti)
            draw_mini_tv(canvas, frame)

            if cel_t >= CELEBRATION_DURATION_S and not confetti.active:
                celebrating = False

            display_frame = process_frame_for_fullscreen(canvas)
            cv2.imshow("Body Says It", display_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            continue

        # ---- Draw webcam mini-TV ----
        draw_mini_tv(canvas, frame)

        # ---- Draw emotion demo (video or fallback stick figure) ----
        t = time.time() - demo_start
        color = EMOTION_COLOR[round_data["target"]]

        # Try video first, fall back to stick figure
        if emotion_frames.get(round_data["target"]) is not None:
            draw_emotion_video_frame(canvas, emotion_frames, round_data["target"], t)
        else:
            AVATAR_DRAWERS[round_data["target"]](canvas, t, color)

        # ---- Emotion label below the video ----
        if not demo_phase:
            # Show which emotion the video was showing (as a reminder during answer phase)
            pass  # The child should identify it, so we don't show the answer!

        # ---- Game phases ----
        if demo_phase:
            draw_pulsing_text(canvas, "Watch the body...", (30, CANVAS_H - 35),
                              cv2.FONT_HERSHEY_DUPLEX, 0.7, (60, 60, 70), 2, time.time())

            # Show a subtle label of what phase we're in
            remaining = max(0, DEMO_DURATION_S - t)
            # Animated dots
            dots = "." * (int(time.time() * 2) % 4)
            put_text_shadow(canvas, f"Watching{dots}", (CANVAS_W // 2 - 80, CANVAS_H - 35),
                            cv2.FONT_HERSHEY_DUPLEX, 0.5, (100, 100, 110), 1)

            if t >= DEMO_DURATION_S:
                demo_phase = False
                answer_open_time = time.time()
        else:
            # ---- Answer phase ----
            hold_progress = 0.0
            if locked_option is None:
                if selection is not None:
                    if selection == hold_selection:
                        held_ms = (time.time() - hold_start) * 1000
                        hold_progress = min(1.0, held_ms / HOLD_MS_TO_LOCK)
                        if held_ms >= HOLD_MS_TO_LOCK:
                            locked_option = selection
                            locked_at = time.time()
                            flash_start = time.time()
                            response_s = locked_at - answer_open_time
                            response_times.append(response_s)
                            last_response_s = response_s
                            total_rounds += 1
                            flash_correct = (locked_option == round_data["correct_option"])
                            if flash_correct:
                                correct_count += 1
                                confetti.spawn(60)
                                play_success_sound()
                            else:
                                play_wrong_sound()
                    else:
                        hold_selection = selection
                        hold_start = time.time()
                else:
                    hold_selection = None
                    hold_start = None

                draw_pulsing_text(canvas, "Which emotion? Hold up 1-4 fingers!",
                                  (30, CANVAS_H - 35), cv2.FONT_HERSHEY_DUPLEX, 0.6,
                                  (50, 50, 60), 2, time.time())
                draw_options_hud(canvas, round_data, locked_option=None,
                                 finger_icons_small=finger_icons_small,
                                 hold_selection=hold_selection,
                                 hold_progress=hold_progress)
            else:
                draw_options_hud(canvas, round_data, locked_option,
                                 finger_icons_small=finger_icons_small,
                                 hold_selection=None, hold_progress=0)
                is_correct = locked_option == round_data["correct_option"]
                msg = "Correct!" if is_correct else f"It was {round_data['target']}!"
                msg_color = (80, 220, 100) if is_correct else (100, 160, 240)
                put_text_shadow(canvas, msg, (30, CANVAS_H - 35),
                                cv2.FONT_HERSHEY_DUPLEX, 0.8, msg_color, 2)

                if (time.time() - locked_at) * 1000 >= FEEDBACK_DISPLAY_MS:
                    # Check if we should celebrate
                    if correct_count > 0 and correct_count % CELEBRATION_EVERY_N == 0 and correct_count > last_celebration_at:
                        celebrating = True
                        celebration_start = time.time()
                        last_celebration_at = correct_count
                        confetti.spawn(100)

                    round_data = spawn_round(previous=round_data["target"])
                    demo_start = time.time()
                    demo_phase = True
                    answer_open_time = None
                    hold_selection = None
                    hold_start = None
                    locked_option = None
                    locked_at = None
                    flash_start = None

        # ---- Confetti (always update if active) ----
        confetti.update_and_draw(canvas)

        # ---- Border flash ----
        if flash_start is not None:
            flash_elapsed = time.time() - flash_start
            flash_alpha = max(0, 1.0 - flash_elapsed / 0.6)
            draw_border_flash(canvas, flash_correct, flash_alpha)

        # ---- Stats HUD ----
        avg_response_s = sum(response_times) / len(response_times) if response_times else 0.0
        draw_stats_hud(canvas, correct_count, total_rounds, avg_response_s, last_response_s)

        # ---- Display ----
        display_frame = process_frame_for_fullscreen(canvas)
        last_display_frame = display_frame
        cv2.imshow("Body Says It", display_frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Show attractive Level 2 4-second quit card before closing
    if last_display_frame is None:
        last_display_frame = np.zeros((CANVAS_H, CANVAS_W, 3), dtype=np.uint8)
    if True:
        play_duration = max(1.0, time.time() - start_time)
        accuracy_pct = int((correct_count / max(1, total_rounds)) * 100) if total_rounds > 0 else (100 if correct_count > 0 else 0)
        avg_resp = (sum(response_times) / len(response_times)) if response_times else 0.0

        if correct_count >= 10 or (total_rounds >= 6 and accuracy_pct >= 85):
            rank_grade = "S+"
            stars = 3
            verdict = "Exceptional Posture Intuition!"
        elif correct_count >= 4 or accuracy_pct >= 65:
            rank_grade = "A"
            stars = 2
            verdict = "Great Body Language Skill!"
        else:
            rank_grade = "B"
            stars = 1
            verdict = "Good Effort! Keep Observing!"

        stats = [
            {"label": "Play Time", "value": format_time(play_duration), "color": (255, 220, 0), "percent": min(1.0, play_duration / 180.0)},
            {"label": "Accuracy", "value": f"{accuracy_pct}%", "color": (100, 255, 120), "percent": accuracy_pct / 100.0},
            {"label": "Avg Response", "value": f"{avg_resp:.1f}s" if avg_resp > 0 else "--", "color": (80, 180, 255), "percent": max(0.2, min(1.0, 1.0 - (avg_resp - 1.0) / 4.0))},
            {"label": "Total Rounds", "value": str(total_rounds), "color": (220, 80, 255), "percent": min(1.0, total_rounds / 15.0)},
        ]

        show_quit_card(
            window_name="Body Says It",
            last_frame=last_display_frame,
            game_title="Body Says It",
            score=correct_count,
            score_label="Gestures Identified",
            stats=stats,
            stars=stars,
            verdict=verdict,
            duration_s=4.0,
            accent_color=(80, 220, 255),
            rank_grade=rank_grade,
        )

    cap.release()
    hands.close()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

# ==================== Optional POSE-based variant ====================
# If you'd rather have the child PHYSICALLY PERFORM the posture (matching the spec's
# literal "AI role: MediaPipe Pose") instead of just naming it, the pattern from
# emotion_mirror_standalone.py and copy_my_move_standalone.py is what to reuse:
#   1. Use mp.solutions.pose instead of mp.solutions.hands.
#   2. After the avatar demo, prompt "Now you try!" instead of showing options.
#   3. Score the child's own body landmarks against simple geometric rules per emotion,
#      e.g. Excited = wrists above shoulders + vertical hip movement (jumping);
#      Sad = shoulders/head lower than calibrated neutral; Angry = wide stance + tense
#      jitter in wrist position; Surprised = sudden arm-raise velocity spike.
#   4. Replace the finger-count lock-in with a hold-the-matching-pose lock-in, same as
#      copy_my_move_standalone.py's Raise/Clap logic.
# That turns this from an identification game into an imitation game — a good Level 4/5
# extension once identification is solid.