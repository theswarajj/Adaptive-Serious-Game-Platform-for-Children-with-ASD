from game_card import show_quit_card, format_time


import cv2
import mediapipe as mp
import random
import time
import math
import numpy as np
from collections import deque
import winsound
import threading

def play_success_sound():
    def sound():
        winsound.Beep(600, 150)
        winsound.Beep(800, 150)
        winsound.Beep(1200, 300)
    threading.Thread(target=sound, daemon=True).start()

def play_new_gesture_sound():
    threading.Thread(target=winsound.Beep, args=(400, 200), daemon=True).start()

def play_wrong_sound():
    threading.Thread(target=winsound.Beep, args=(280, 240), daemon=True).start()

mp_pose = mp.solutions.pose
mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles

# Pose landmark indices we use
# SWAPPED: After cv2.flip(frame, 1), MediaPipe's anatomical LEFT appears on the
# RIGHT side of the mirrored image.  We swap the indices so that "Raise Left Hand"
# checks the hand that the child sees on their LEFT in the mirror.
LEFT_SHOULDER, RIGHT_SHOULDER = 12, 11   # swapped for mirrored display
LEFT_WRIST, RIGHT_WRIST = 16, 15         # swapped for mirrored display

# Hand landmark indices for finger detection
THUMB_TIP, THUMB_IP, THUMB_MCP = 4, 3, 2
INDEX_TIP, INDEX_PIP = 8, 6
MIDDLE_TIP, MIDDLE_PIP = 12, 10
RING_TIP, RING_PIP = 16, 14
PINKY_TIP, PINKY_PIP = 20, 18
WRIST_LM = 0

# ---------------------- Tunable settings ----------------------
HOLD_MS_TO_WIN = 1200            # for Raise Hand / Clap: how long to hold the pose
SUCCESS_DISPLAY_MS = 900         # pause after winning before next gesture
RAISE_MARGIN_PX = 20             # wrist must be at least this far above shoulder (pixels)
CLAP_DISTANCE_PX = 90            # max distance between wrists to count as a clap

WAVE_WINDOW_SEC = 2.0            # how far back we look for wave motion
WAVE_MIN_AMPLITUDE_PX = 35       # minimum side-to-side movement to count as a wave
WAVE_MIN_REVERSALS = 3           # how many direction changes needed to call it a wave

# All available gestures — body gestures + hand gestures
BODY_GESTURES = ["Raise Left Hand", "Raise Right Hand", "Raise Both Hands", "Clap Hands", "Wave"]
HAND_GESTURES = ["Thumbs Up", "Show 1 Finger", "Show 2 Fingers", "Show 3 Fingers", "Show 5 Fingers"]
GESTURES = BODY_GESTURES + HAND_GESTURES

# Gesture-specific hint colors (BGR)
GESTURE_COLORS = {
    "Raise Left Hand": (255, 255, 0),     # cyan
    "Raise Right Hand": (255, 255, 0),    # cyan
    "Raise Both Hands": (255, 255, 0),    # cyan
    "Clap Hands": (0, 230, 255),          # yellow
    "Wave": (255, 100, 230),              # magenta-ish
    "Thumbs Up": (0, 200, 100),           # green
    "Show 1 Finger": (255, 180, 100),     # light blue
    "Show 2 Fingers": (180, 255, 100),    # light green-blue
    "Show 3 Fingers": (100, 200, 255),    # orange
    "Show 5 Fingers": (200, 150, 255),    # pink
}


# ---------------------- Success burst particles ----------------------
class BurstParticle:
    __slots__ = ['x', 'y', 'vx', 'vy', 'color', 'radius', 'life']

    def __init__(self, x, y):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(4, 12)
        self.x = float(x)
        self.y = float(y)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.color = random.choice([
            (0, 255, 0), (0, 255, 255), (255, 255, 0),
            (255, 200, 100), (200, 150, 255), (100, 255, 200),
        ])
        self.radius = random.randint(4, 10)
        self.life = 1.0

    def update(self, dt):
        self.x += self.vx
        self.y += self.vy
        self.vy += 2.5
        self.vx *= 0.96
        self.life -= dt * 1.2
        return self.life > 0

    def draw(self, frame):
        alpha = max(0, self.life)
        r = max(1, int(self.radius * alpha))
        c = tuple(int(ch * alpha) for ch in self.color)
        cv2.circle(frame, (int(self.x), int(self.y)), r + 6, (0, 0, 0), -1)
        cv2.circle(frame, (int(self.x), int(self.y)), r + 3, c, -1)
        cv2.circle(frame, (int(self.x), int(self.y)), max(1, r - 2), (255, 255, 255), -1)


burst_particles = []


def emit_burst(x, y, count=20):
    for _ in range(count):
        burst_particles.append(BurstParticle(x, y))


def update_and_draw_burst(frame, dt):
    global burst_particles
    alive = []
    for p in burst_particles:
        if p.update(dt):
            p.draw(frame)
            alive.append(p)
    burst_particles = alive


# ---------------------- Utilities ----------------------
def draw_rounded_rect_overlay(frame, x, y, w, h, color=(15, 18, 28), alpha=0.75, radius=16):
    ch, cw = frame.shape[:2]
    x1, y1 = max(0, x), max(0, y)
    x2, y2 = min(cw, x + w), min(ch, y + h)
    if x2 <= x1 or y2 <= y1:
        return
    roi = frame[y1:y2, x1:x2]
    overlay = roi.copy()
    rx, ry = x - x1, y - y1
    cv2.rectangle(overlay, (rx + radius, ry), (rx + w - radius, ry + h), color, -1)
    cv2.rectangle(overlay, (rx, ry + radius), (rx + w, ry + h - radius), color, -1)
    cv2.circle(overlay, (rx + radius, ry + radius), radius, color, -1)
    cv2.circle(overlay, (rx + w - radius, ry + radius), radius, color, -1)
    cv2.circle(overlay, (rx + radius, ry + h - radius), radius, color, -1)
    cv2.circle(overlay, (rx + w - radius, ry + h - radius), radius, color, -1)
    cv2.addWeighted(overlay, alpha, roi, 1.0 - alpha, 0, roi)


def apply_vignette(frame):
    h, w = frame.shape[:2]
    band = h // 6
    for i in range(band):
        a = (1.0 - i / band) * 0.35
        frame[i] = (frame[i].astype(np.float32) * (1 - a)).astype(np.uint8)
    for i in range(band):
        a = (1.0 - i / band) * 0.25
        frame[h - 1 - i] = (frame[h - 1 - i].astype(np.float32) * (1 - a)).astype(np.uint8)


def spawn_gesture(previous=None):
    choices = [g for g in GESTURES if g != previous] or GESTURES
    return random.choice(choices)


# ===================== BODY GESTURE CHECKS (Pose landmarks) =====================

def get_point(landmarks, idx, w, h):
    lm = landmarks[idx]
    return (int(lm.x * w), int(lm.y * h)), lm.visibility


def get_raised_flags(landmarks, w, h):
    """
    Returns (left_raised, right_raised) as booleans.
    After the index swap above, 'left' matches the child's visual left in the mirror.
    """
    (lw, lw_vis) = get_point(landmarks, LEFT_WRIST, w, h)
    (rw, rw_vis) = get_point(landmarks, RIGHT_WRIST, w, h)
    (ls, ls_vis) = get_point(landmarks, LEFT_SHOULDER, w, h)
    (rs, rs_vis) = get_point(landmarks, RIGHT_SHOULDER, w, h)

    left_raised = lw_vis > 0.5 and ls_vis > 0.5 and lw[1] < ls[1] - RAISE_MARGIN_PX
    right_raised = rw_vis > 0.5 and rs_vis > 0.5 and rw[1] < rs[1] - RAISE_MARGIN_PX
    return left_raised, right_raised


def check_raise_left_only(landmarks, w, h):
    left_raised, right_raised = get_raised_flags(landmarks, w, h)
    return left_raised and not right_raised


def check_raise_right_only(landmarks, w, h):
    left_raised, right_raised = get_raised_flags(landmarks, w, h)
    return right_raised and not left_raised


def check_raise_both(landmarks, w, h):
    left_raised, right_raised = get_raised_flags(landmarks, w, h)
    return left_raised and right_raised


def check_clap(landmarks, w, h):
    (lw, lw_vis) = get_point(landmarks, LEFT_WRIST, w, h)
    (rw, rw_vis) = get_point(landmarks, RIGHT_WRIST, w, h)
    if lw_vis < 0.5 or rw_vis < 0.5:
        return False
    dist = ((lw[0] - rw[0]) ** 2 + (lw[1] - rw[1]) ** 2) ** 0.5
    return dist <= CLAP_DISTANCE_PX


def update_wave_and_check(landmarks, w, h, history):
    """
    history: deque of (timestamp, x) for whichever wrist is currently raised.
    Returns True once enough side-to-side motion has been seen in the recent window.
    """
    (lw, lw_vis) = get_point(landmarks, LEFT_WRIST, w, h)
    (rw, rw_vis) = get_point(landmarks, RIGHT_WRIST, w, h)
    (ls, ls_vis) = get_point(landmarks, LEFT_SHOULDER, w, h)
    (rs, rs_vis) = get_point(landmarks, RIGHT_SHOULDER, w, h)

    raised_x = None
    if rw_vis > 0.5 and rs_vis > 0.5 and rw[1] < rs[1] - RAISE_MARGIN_PX:
        raised_x = rw[0]
    elif lw_vis > 0.5 and ls_vis > 0.5 and lw[1] < ls[1] - RAISE_MARGIN_PX:
        raised_x = lw[0]

    now = time.time()
    if raised_x is not None:
        history.append((now, raised_x))
    else:
        history.clear()  # hand dropped, reset the wave attempt

    # Drop samples older than the window
    while history and now - history[0][0] > WAVE_WINDOW_SEC:
        history.popleft()

    if len(history) < 4:
        return False, 0

    xs = [p[1] for p in history]
    amplitude = max(xs) - min(xs)
    if amplitude < WAVE_MIN_AMPLITUDE_PX:
        return False, 0

    # Count direction reversals (sign changes) in the x movement
    reversals = 0
    last_dir = 0
    for i in range(1, len(xs)):
        dx = xs[i] - xs[i - 1]
        if abs(dx) < 4:  # ignore tiny jitter
            continue
        direction = 1 if dx > 0 else -1
        if last_dir != 0 and direction != last_dir:
            reversals += 1
        last_dir = direction

    return reversals >= WAVE_MIN_REVERSALS, reversals


# ===================== HAND GESTURE CHECKS (Hand landmarks) =====================

def _finger_extended(hand_lm, tip_idx, pip_idx):
    """Check if a finger is extended (tip is above pip in y — screen coords, so lower y = higher)."""
    return hand_lm[tip_idx].y < hand_lm[pip_idx].y


def _thumb_extended(hand_lm):
    """
    Check if thumb is extended outward.
    We compare thumb tip x vs thumb IP x relative to the wrist to handle both hands.
    Also check thumb tip is above thumb IP (for thumbs-up specifically).
    """
    # Thumb tip should be significantly above thumb IP for a thumbs-up
    tip = hand_lm[THUMB_TIP]
    ip = hand_lm[THUMB_IP]
    mcp = hand_lm[THUMB_MCP]
    return tip.y < ip.y and tip.y < mcp.y


def count_fingers_up(hand_lm):
    """
    Count how many of the 4 main fingers (index, middle, ring, pinky) are extended.
    Does NOT count the thumb.
    """
    count = 0
    if _finger_extended(hand_lm, INDEX_TIP, INDEX_PIP):
        count += 1
    if _finger_extended(hand_lm, MIDDLE_TIP, MIDDLE_PIP):
        count += 1
    if _finger_extended(hand_lm, RING_TIP, RING_PIP):
        count += 1
    if _finger_extended(hand_lm, PINKY_TIP, PINKY_PIP):
        count += 1
    return count


def check_thumbs_up(hand_lm):
    """Thumb extended upward, all other fingers curled."""
    if not _thumb_extended(hand_lm):
        return False
    fingers_up = count_fingers_up(hand_lm)
    return fingers_up == 0


def check_show_n_fingers(hand_lm, n):
    """
    Check if exactly N fingers are shown.
    For n=1: only index up
    For n=2: index + middle up
    For n=3: index + middle + ring up
    For n=5: all 4 fingers + thumb up (open hand)
    """
    fingers_up = count_fingers_up(hand_lm)

    if n == 5:
        # Open hand: all 4 fingers extended, thumb also extended
        thumb_up = _thumb_extended(hand_lm)
        return fingers_up >= 4 and thumb_up
    else:
        # For 1, 2, 3: exactly that many main fingers, thumb NOT counted
        return fingers_up == n


def check_wrong_gesture(gesture, pose_landmarks, hand_landmarks, w, h):
    """
    Returns (is_wrong, wrong_title, wrong_subtitle) when user is performing an incorrect pose.
    """
    is_body = gesture in BODY_GESTURES
    is_hand = gesture in HAND_GESTURES

    if is_body and pose_landmarks:
        landmarks = pose_landmarks.landmark
        left_raised, right_raised = get_raised_flags(landmarks, w, h)
        (lw, lw_vis) = get_point(landmarks, LEFT_WRIST, w, h)
        (rw, rw_vis) = get_point(landmarks, RIGHT_WRIST, w, h)

        if gesture == "Raise Left Hand":
            if right_raised and not left_raised:
                return True, "WRONG MOVE!", "Wrong hand raised! Raise your LEFT hand!"
            if left_raised and right_raised:
                return True, "WRONG MOVE!", "Only raise ONE hand (your Left hand)!"
        elif gesture == "Raise Right Hand":
            if left_raised and not right_raised:
                return True, "WRONG MOVE!", "Wrong hand raised! Raise your RIGHT hand!"
            if left_raised and right_raised:
                return True, "WRONG MOVE!", "Only raise ONE hand (your Right hand)!"
        elif gesture == "Raise Both Hands":
            if (left_raised and not right_raised) or (right_raised and not left_raised):
                return True, "WRONG MOVE!", "Raise BOTH hands up together!"
        elif gesture == "Clap Hands":
            if lw_vis > 0.5 and rw_vis > 0.5:
                dist = math.hypot(lw[0] - rw[0], lw[1] - rw[1])
                if dist > 210 and (left_raised or right_raised):
                    return True, "WRONG MOVE!", "Bring both hands together to CLAP!"

    elif is_hand and hand_landmarks:
        hand_lm = hand_landmarks[0].landmark
        fingers_up = count_fingers_up(hand_lm)
        thumb_up = _thumb_extended(hand_lm)

        if gesture == "Thumbs Up":
            if fingers_up >= 2:
                return True, "WRONG MOVE!", "Make a fist with THUMB UP only!"
        elif gesture == "Show 1 Finger":
            if fingers_up in (2, 3, 4) or (fingers_up == 0 and thumb_up):
                return True, "WRONG MOVE!", f"Showing {fingers_up} fingers! Show only 1 finger!"
        elif gesture == "Show 2 Fingers":
            if fingers_up in (1, 3, 4) or (fingers_up == 0 and thumb_up):
                return True, "WRONG MOVE!", f"Showing {fingers_up} fingers! Show 2 fingers!"
        elif gesture == "Show 3 Fingers":
            if fingers_up in (1, 2, 4) or (fingers_up == 0 and thumb_up):
                return True, "WRONG MOVE!", f"Showing {fingers_up} fingers! Show 3 fingers!"
        elif gesture == "Show 5 Fingers":
            if fingers_up < 3:
                return True, "WRONG MOVE!", "Open your entire hand (5 fingers)!"

    return False, "", ""


def draw_middle_feedback_card(canvas, kind, title, subtitle, elapsed, w, h):
    """
    Renders an exceptionally polished, animated feedback card right in the middle of the screen.
    kind: 'good' (green/gold victory) or 'holding' (cyan/green progress) or 'wrong' (coral/red warning)
    """
    card_w = 600
    card_h = 165
    cx = w // 2
    cy = h // 2

    if kind == "good":
        bounce = abs(math.sin(elapsed * 6.0)) * 0.12
        bw = int(card_w * (1.0 + bounce))
        bh = int(card_h * (1.0 + bounce))
        bx = cx - bw // 2
        by = cy - bh // 2

        draw_rounded_rect_overlay(canvas, bx, by, bw, bh, (15, 30, 20), 0.92, 22)
        cv2.rectangle(canvas, (bx, by), (bx + bw, by + bh), (0, 240, 255), 3, cv2.LINE_AA)
        cv2.rectangle(canvas, (bx + 4, by + 4), (bx + bw - 4, by + bh - 4), (80, 255, 120), 1, cv2.LINE_AA)

        t_size = cv2.getTextSize(title, cv2.FONT_HERSHEY_DUPLEX, 1.3, 3)[0]
        tx = cx - t_size[0] // 2
        ty = cy - 8
        cv2.putText(canvas, title, (tx, ty), cv2.FONT_HERSHEY_DUPLEX, 1.3, (0, 0, 0), 6, cv2.LINE_AA)
        cv2.putText(canvas, title, (tx, ty), cv2.FONT_HERSHEY_DUPLEX, 1.3, (0, 255, 255), 3, cv2.LINE_AA)

        s_size = cv2.getTextSize(subtitle, cv2.FONT_HERSHEY_DUPLEX, 0.75, 2)[0]
        sx = cx - s_size[0] // 2
        sy = cy + 42
        cv2.putText(canvas, subtitle, (sx, sy), cv2.FONT_HERSHEY_DUPLEX, 0.75, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(canvas, subtitle, (sx, sy), cv2.FONT_HERSHEY_DUPLEX, 0.75, (120, 255, 140), 2, cv2.LINE_AA)

    elif kind == "wrong":
        shake_x = int(math.sin(elapsed * 35.0) * 10)
        bw = card_w
        bh = card_h
        bx = cx - bw // 2 + shake_x
        by = cy - bh // 2

        draw_rounded_rect_overlay(canvas, bx, by, bw, bh, (35, 15, 20), 0.92, 22)
        cv2.rectangle(canvas, (bx, by), (bx + bw, by + bh), (50, 60, 255), 3, cv2.LINE_AA)
        cv2.rectangle(canvas, (bx + 4, by + 4), (bx + bw - 4, by + bh - 4), (100, 120, 255), 1, cv2.LINE_AA)

        t_size = cv2.getTextSize(title, cv2.FONT_HERSHEY_DUPLEX, 1.25, 3)[0]
        tx = cx - t_size[0] // 2 + shake_x
        ty = cy - 8
        cv2.putText(canvas, title, (tx, ty), cv2.FONT_HERSHEY_DUPLEX, 1.25, (0, 0, 0), 6, cv2.LINE_AA)
        cv2.putText(canvas, title, (tx, ty), cv2.FONT_HERSHEY_DUPLEX, 1.25, (80, 100, 255), 3, cv2.LINE_AA)

        s_size = cv2.getTextSize(subtitle, cv2.FONT_HERSHEY_DUPLEX, 0.72, 2)[0]
        sx = cx - s_size[0] // 2 + shake_x
        sy = cy + 42
        cv2.putText(canvas, subtitle, (sx, sy), cv2.FONT_HERSHEY_DUPLEX, 0.72, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(canvas, subtitle, (sx, sy), cv2.FONT_HERSHEY_DUPLEX, 0.72, (200, 220, 255), 2, cv2.LINE_AA)

    elif kind == "holding":
        bw = 500
        bh = 75
        bx = cx - bw // 2
        by = cy - bh // 2

        draw_rounded_rect_overlay(canvas, bx, by, bw, bh, (15, 25, 35), 0.82, 16)
        cv2.rectangle(canvas, (bx, by), (bx + bw, by + bh), (0, 220, 255), 2, cv2.LINE_AA)

        t_size = cv2.getTextSize(title, cv2.FONT_HERSHEY_DUPLEX, 0.88, 2)[0]
        tx = cx - t_size[0] // 2
        ty = cy + 8
        cv2.putText(canvas, title, (tx, ty), cv2.FONT_HERSHEY_DUPLEX, 0.88, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(canvas, title, (tx, ty), cv2.FONT_HERSHEY_DUPLEX, 0.88, (0, 255, 220), 2, cv2.LINE_AA)


# ===================== DRAWING =====================

def draw_gesture_hint(frame, gesture, w, h, t):
    # Semi-transparent panel background for the hint
    draw_rounded_rect_overlay(frame, 20, 100, 150, 140, (30, 30, 40), 0.5, 12)

    cx, cy = 90, 160
    arm_color = GESTURE_COLORS.get(gesture, (0, 255, 255))

    # Subtle pulse on the active elements
    pulse_thick = 5 + int(math.sin(t * 4) * 1.5)

    # ---------- Body gestures (stick figure) ----------
    if gesture == "Raise Left Hand":
        cv2.line(frame, (cx, cy), (cx, cy + 60), (255, 255, 255), 4)          # body
        cv2.circle(frame, (cx, cy - 20), 18, (255, 255, 255), 3)              # head
        cv2.line(frame, (cx, cy + 10), (cx - 40, cy - 40), arm_color, pulse_thick)
        cv2.line(frame, (cx, cy + 10), (cx + 25, cy + 35), (255, 255, 255), 4)
    elif gesture == "Raise Right Hand":
        cv2.line(frame, (cx, cy), (cx, cy + 60), (255, 255, 255), 4)
        cv2.circle(frame, (cx, cy - 20), 18, (255, 255, 255), 3)
        cv2.line(frame, (cx, cy + 10), (cx + 40, cy - 40), arm_color, pulse_thick)
        cv2.line(frame, (cx, cy + 10), (cx - 25, cy + 35), (255, 255, 255), 4)
    elif gesture == "Raise Both Hands":
        cv2.line(frame, (cx, cy), (cx, cy + 60), (255, 255, 255), 4)
        cv2.circle(frame, (cx, cy - 20), 18, (255, 255, 255), 3)
        cv2.line(frame, (cx, cy + 10), (cx - 40, cy - 40), arm_color, pulse_thick)
        cv2.line(frame, (cx, cy + 10), (cx + 40, cy - 40), arm_color, pulse_thick)
    elif gesture == "Clap Hands":
        cv2.line(frame, (cx, cy), (cx, cy + 60), (255, 255, 255), 4)
        cv2.circle(frame, (cx, cy - 20), 18, (255, 255, 255), 3)
        cv2.line(frame, (cx, cy + 10), (cx + 25, cy - 5), arm_color, pulse_thick)
        cv2.line(frame, (cx, cy + 10), (cx - 25, cy - 5), arm_color, pulse_thick)
        cv2.circle(frame, (cx, cy - 5), 6, arm_color, -1)
    elif gesture == "Wave":
        cv2.line(frame, (cx, cy), (cx, cy + 60), (255, 255, 255), 4)
        cv2.circle(frame, (cx, cy - 20), 18, (255, 255, 255), 3)
        wave_offset = int(math.sin(t * 6) * 8)
        cv2.line(frame, (cx, cy + 10), (cx + 40 + wave_offset, cy - 40), arm_color, pulse_thick)
        cv2.putText(frame, "~", (cx + 45 + wave_offset, cy - 45),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, arm_color, 2)

    # ---------- Hand gestures (hand icon) ----------
    elif gesture == "Thumbs Up":
        # Draw a fist with thumb sticking up
        # Palm/fist body
        cv2.rectangle(frame, (cx - 15, cy - 5), (cx + 15, cy + 30), arm_color, -1)
        cv2.rectangle(frame, (cx - 15, cy - 5), (cx + 15, cy + 30), (255, 255, 255), 2)
        # Thumb going up
        thumb_wobble = int(math.sin(t * 3) * 3)
        cv2.line(frame, (cx - 10, cy - 5), (cx - 10 + thumb_wobble, cy - 40), arm_color, pulse_thick)
        cv2.circle(frame, (cx - 10 + thumb_wobble, cy - 42), 6, arm_color, -1)
        cv2.circle(frame, (cx - 10 + thumb_wobble, cy - 42), 6, (255, 255, 255), 2)

    elif gesture in ("Show 1 Finger", "Show 2 Fingers", "Show 3 Fingers", "Show 5 Fingers"):
        n = {"Show 1 Finger": 1, "Show 2 Fingers": 2, "Show 3 Fingers": 3, "Show 5 Fingers": 5}[gesture]
        # Draw palm
        palm_y = cy + 15
        cv2.rectangle(frame, (cx - 22, palm_y), (cx + 22, palm_y + 28), arm_color, -1)
        cv2.rectangle(frame, (cx - 22, palm_y), (cx + 22, palm_y + 28), (255, 255, 255), 2)

        # Draw fingers going up from palm
        finger_positions = []
        if n >= 1:
            finger_positions.append(cx - 10)  # index
        if n >= 2:
            finger_positions.append(cx)        # middle
        if n >= 3:
            finger_positions.append(cx + 10)   # ring
        if n >= 5:
            finger_positions.append(cx + 20)   # pinky
            # Also draw thumb on the left side
            thumb_x = cx - 22
            cv2.line(frame, (thumb_x, palm_y + 8), (thumb_x - 14, palm_y - 5),
                     arm_color, pulse_thick)

        wobble = int(math.sin(t * 4) * 2)
        for fx in finger_positions:
            finger_top = palm_y - 30 + wobble
            cv2.line(frame, (fx, palm_y), (fx, finger_top), arm_color, pulse_thick)
            cv2.circle(frame, (fx, finger_top), 3, (255, 255, 255), -1)

        # Big number label
        cv2.putText(frame, str(n), (cx + 28, cy + 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 3)


def draw_progress_bar(frame, progress, w, t):
    bar_x, bar_y, bar_w, bar_h = 25, 300, 320, 28

    # Background
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (20, 20, 20), -1)
    cv2.rectangle(frame, (bar_x, bar_y), (bar_x + bar_w, bar_y + bar_h), (0, 210, 255), 3)

    fill_w = int(bar_w * min(1.0, progress))
    if fill_w > 0:
        # Gradient fill: dark green -> bright green
        for col in range(fill_w):
            frac = col / max(1, fill_w - 1)
            g = int(180 + 75 * frac)
            b = int(50 * (1 - frac))
            r = 0
            cv2.line(frame, (bar_x + col, bar_y + 2), (bar_x + col, bar_y + bar_h - 2), (b, g, r), 1)

        # Shimmer line sliding across
        shimmer_x = int((t * 120) % (fill_w + 30)) + bar_x - 15
        if bar_x <= shimmer_x <= bar_x + fill_w:
            for offset in range(-4, 5):
                sx = shimmer_x + offset
                if bar_x <= sx <= bar_x + fill_w:
                    intensity = max(0, 255 - abs(offset) * 50)
                    cv2.line(frame, (sx, bar_y + 2), (sx, bar_y + bar_h - 2),
                             (intensity, 255, intensity), 1)


def draw_hud(frame, score, gesture, status_text, round_num):
    draw_rounded_rect_overlay(frame, 10, 8, 420, 105, (10, 10, 10), 0.7, 12)
    cv2.rectangle(frame, (10, 8), (430, 113), (0, 210, 255), 2, cv2.LINE_AA)

    cv2.putText(frame, f"Copied: {score}   Round: {round_num}", (25, 45),
                cv2.FONT_HERSHEY_DUPLEX, 0.9, (0, 0, 0), 4)
    cv2.putText(frame, f"Copied: {score}   Round: {round_num}", (25, 45),
                cv2.FONT_HERSHEY_DUPLEX, 0.9, (0, 255, 0), 2)

    gesture_color = GESTURE_COLORS.get(gesture, (0, 255, 255))
    cv2.putText(frame, f"Do this: {gesture}", (25, 80),
                cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 0, 0), 4)
    cv2.putText(frame, f"Do this: {gesture}", (25, 80),
                cv2.FONT_HERSHEY_DUPLEX, 0.8, gesture_color, 2)

    # Status at bottom of HUD area
    cv2.putText(frame, status_text, (25, 360),
                cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 0, 0), 3)
    cv2.putText(frame, status_text, (25, 360),
                cv2.FONT_HERSHEY_DUPLEX, 0.7, (220, 220, 220), 1)


def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Could not open webcam.")
        return

    pose = mp_pose.Pose(
        model_complexity=1,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6,
    )

    hands = mp_hands.Hands(
        max_num_hands=1,
        model_complexity=0,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6,
    )

    score = 0
    round_num = 1
    start_time = time.time()
    last_frame = None
    gesture = spawn_gesture()
    hold_start = None
    won_at = None
    wrong_start = None
    wrong_at = None
    wrong_title = ""
    wrong_sub = ""
    wave_history = deque()
    last_time = time.time()
    
    play_new_gesture_sound()

    cv2.namedWindow("Copy My Move", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("Copy My Move", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    while True:
        success, frame = cap.read()
        if not success:
            break

        now = time.time()
        dt = now - last_time
        last_time = now

        frame = cv2.flip(frame, 1)
        last_frame = frame
        h, w = frame.shape[:2]

        apply_vignette(frame)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Run both detectors
        pose_results = pose.process(rgb)
        hand_results = hands.process(rgb)

        progress = 0.0
        status = f"Copy the move: {gesture}"

        is_body_gesture = gesture in BODY_GESTURES
        is_hand_gesture = gesture in HAND_GESTURES
        matched = False

        # ---------- Body gesture detection ----------
        if is_body_gesture and pose_results.pose_landmarks:
            landmarks = pose_results.pose_landmarks.landmark
            for idx in [LEFT_WRIST, RIGHT_WRIST]:
                (pt, vis) = get_point(landmarks, idx, w, h)
                if vis > 0.5:
                    cv2.circle(frame, pt, 18, (0, 150, 255), -1)
                    cv2.circle(frame, pt, 12, (0, 210, 255), -1)
                    cv2.circle(frame, pt, 6, (255, 255, 255), -1)

            if won_at is None:
                if gesture == "Raise Left Hand":
                    matched = check_raise_left_only(landmarks, w, h)
                elif gesture == "Raise Right Hand":
                    matched = check_raise_right_only(landmarks, w, h)
                elif gesture == "Raise Both Hands":
                    matched = check_raise_both(landmarks, w, h)
                elif gesture == "Clap Hands":
                    matched = check_clap(landmarks, w, h)
                elif gesture == "Wave":
                    matched, _reversals = update_wave_and_check(landmarks, w, h, wave_history)

        elif is_body_gesture and not pose_results.pose_landmarks:
            hold_start = None
            status = "Step into view of the camera"

        # ---------- Hand gesture detection ----------
        if is_hand_gesture and hand_results.multi_hand_landmarks:
            hand_lm_list = hand_results.multi_hand_landmarks[0]

            hand_lm = hand_lm_list.landmark
            for idx in [THUMB_TIP, INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP]:
                pt = (int(hand_lm[idx].x * w), int(hand_lm[idx].y * h))
                cv2.circle(frame, pt, 15, (0, 150, 255), -1)
                cv2.circle(frame, pt, 10, (0, 210, 255), -1)
                cv2.circle(frame, pt, 5, (255, 255, 255), -1)

            if won_at is None:
                if gesture == "Thumbs Up":
                    matched = check_thumbs_up(hand_lm)
                elif gesture == "Show 1 Finger":
                    matched = check_show_n_fingers(hand_lm, 1)
                elif gesture == "Show 2 Fingers":
                    matched = check_show_n_fingers(hand_lm, 2)
                elif gesture == "Show 3 Fingers":
                    matched = check_show_n_fingers(hand_lm, 3)
                elif gesture == "Show 5 Fingers":
                    matched = check_show_n_fingers(hand_lm, 5)

        elif is_hand_gesture and not hand_results.multi_hand_landmarks:
            hold_start = None
            status = "Show your hand to the camera"

        # Optionally, draw wrists even during hand gestures for tracking awareness
        if is_hand_gesture and pose_results.pose_landmarks:
            landmarks = pose_results.pose_landmarks.landmark
            for idx in [LEFT_WRIST, RIGHT_WRIST]:
                (pt, vis) = get_point(landmarks, idx, w, h)
                if vis > 0.5:
                    cv2.circle(frame, pt, 15, (50, 50, 50), -1)
                    cv2.circle(frame, pt, 8, (150, 150, 150), -1)

        # ---------- Hold / win logic ----------
        if won_at is None:
            if gesture == "Wave":
                # Wave has its own internal windowed progress
                xs = [p[1] for p in wave_history]
                amplitude = (max(xs) - min(xs)) if len(xs) >= 2 else 0
                progress = min(1.0, amplitude / (WAVE_MIN_AMPLITUDE_PX * 1.4)) if not matched else 1.0
                if matched:
                    won_at = time.time()
                    score += 1
                    wave_history.clear()
                    emit_burst(w // 2, h // 2, count=45)
                    play_success_sound()
            else:
                # All other gestures: hold for HOLD_MS_TO_WIN
                if matched:
                    if hold_start is None:
                        hold_start = time.time()
                    held_ms = (time.time() - hold_start) * 1000
                    progress = min(1.0, held_ms / HOLD_MS_TO_WIN)
                    if held_ms >= HOLD_MS_TO_WIN:
                        won_at = time.time()
                        score += 1
                        emit_burst(w // 2, h // 2, count=45)
                        play_success_sound()
                else:
                    hold_start = None

        # Check wrong gesture when not matched and not already won
        if won_at is None and not matched:
            is_wrong, w_title, w_sub = check_wrong_gesture(
                gesture, pose_results.pose_landmarks, hand_results.multi_hand_landmarks, w, h
            )
            if is_wrong:
                if wrong_start is None:
                    wrong_start = now
                elif now - wrong_start >= 0.40:
                    if wrong_at is None or now - wrong_at > 1.3:
                        wrong_at = now
                        wrong_title = w_title
                        wrong_sub = w_sub
                        play_wrong_sound()
            else:
                wrong_start = None
        else:
            wrong_start = None
            if matched:
                wrong_at = None

        # Draw Middle-of-Screen Feedback Animations (Good / Wrong / Holding)
        if won_at is not None:
            elapsed_won = now - won_at
            if elapsed_won * 1000 < SUCCESS_DISPLAY_MS:
                draw_middle_feedback_card(frame, "good", "🌟 GREAT JOB!", "PERFECT MOVE! YOU COPIED IT!", elapsed_won, w, h)
                status = "Awesome! Perfect Move!"
            else:
                gesture = spawn_gesture(previous=gesture)
                won_at = None
                hold_start = None
                wrong_at = None
                wave_history.clear()
                round_num += 1
                status = "New move!"
                play_new_gesture_sound()

        elif wrong_at is not None and (now - wrong_at) < 1.25:
            elapsed_wrong = now - wrong_at
            draw_middle_feedback_card(frame, "wrong", wrong_title, wrong_sub, elapsed_wrong, w, h)
            status = f"Wrong: {wrong_sub}"

        elif hold_start is not None and matched:
            held_s = now - hold_start
            pct = int(min(1.0, (held_s * 1000) / HOLD_MS_TO_WIN) * 100)
            draw_middle_feedback_card(frame, "holding", f"✨ GOOD! HOLD IT... {pct}%", "Stay steady!", held_s, w, h)

        # Draw particles
        update_and_draw_burst(frame, dt)

        draw_gesture_hint(frame, gesture, w, h, now)
        draw_progress_bar(frame, progress, w, now)
        draw_hud(frame, score, gesture, status, round_num)

        cv2.imshow("Copy My Move", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Show attractive Level 4 4-second quit card before closing
    if last_frame is None:
        last_frame = np.zeros((h, w, 3), dtype=np.uint8)

    play_duration = max(1.0, time.time() - start_time)
    accuracy_pct = int((score / max(1, round_num)) * 100) if round_num > 0 else (100 if score > 0 else 0)
    pace = (score / play_duration) * 60.0

    if score >= 8 or accuracy_pct >= 80:
        tier_badge = "GRANDMASTER"
        stars = 3
        verdict = "Supreme Movement Reciprocity!"
    elif score >= 4 or accuracy_pct >= 55:
        tier_badge = "MASTER"
        stars = 2
        verdict = "Superb Motor Mimicry!"
    else:
        tier_badge = "EXPERT"
        stars = 1
        verdict = "Great Energy! Keep Moving!"

    stats = [
        {"label": "Play Time", "value": format_time(play_duration), "color": (30, 215, 255), "percent": min(1.0, play_duration / 180.0)},
        {"label": "Accuracy", "value": f"{accuracy_pct}%", "color": (100, 255, 140), "percent": accuracy_pct / 100.0},
        {"label": "Rounds Won", "value": f"{score} / {round_num}", "color": (255, 220, 80), "percent": min(1.0, score / 12.0)},
        {"label": "Pace", "value": f"{pace:.1f} / min", "color": (120, 100, 255), "percent": min(1.0, pace / 8.0)},
    ]

    show_quit_card(
        window_name="Copy My Move",
        last_frame=last_frame,
        game_title="Copy My Move",
        score=score,
        score_label="Moves Mimicked",
        stats=stats,
        stars=stars,
        verdict=verdict,
        duration_s=4.0,
        accent_color=(30, 215, 255),
        tier_badge=tier_badge,
    )

    cap.release()
    pose.close()
    hands.close()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()