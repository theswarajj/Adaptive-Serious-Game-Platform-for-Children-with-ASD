
# Install:  pip install opencv-python mediapipe

import cv2
import mediapipe as mp
import random
import time
import math
import numpy as np
import threading
import winsound
from typing import Optional, Dict
from game_card import show_quit_card, format_time

def play_pop_sound():
    threading.Thread(target=winsound.Beep, args=(1200, 150), daemon=True).start()

def play_streak_sound():
    def sound():
        winsound.Beep(600, 150)
        winsound.Beep(800, 150)
        winsound.Beep(1200, 300)
    threading.Thread(target=sound, daemon=True).start()


# ---------------------- Landmarks we care about ----------------------
INDEX_TIP = 8
THUMB_TIP = 4

# ---------------------- Tunable settings ----------------------
CAM_WIDTH, CAM_HEIGHT = 1920, 1080
BALLOON_MIN_RADIUS = 75
BALLOON_MAX_RADIUS = 100
PINCH_THRESHOLD_PX = 50        # how close thumb+index must be to count as a pinch
POP_DISPLAY_MS = 900           # how long "POP!" shows before next balloon appears
BALLOON_MARGIN = 100           # keep balloons away from frame edges
BALLOON_COLORS = [
    (250, 130, 90),   # blue-ish (BGR)
    (90, 200, 255),   # orange
    (140, 230, 140),  # green
    (200, 130, 255),  # pink
    (80, 220, 255),   # gold/yellow
    (220, 180, 100),  # teal
    (120, 130, 250),  # coral
    (230, 190, 200),  # lavender
]

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles


# ---------------------- Particle system ----------------------
class Particle:
    __slots__ = ['x', 'y', 'vx', 'vy', 'color', 'radius', 'life', 'max_life']

    def __init__(self, x, y, color):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(3, 10)
        self.x = float(x)
        self.y = float(y)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.color = color
        self.radius = random.randint(4, 10)
        self.life = 1.0
        self.max_life = random.uniform(0.5, 1.0)

    def update(self, dt):
        self.x += self.vx
        self.y += self.vy
        self.vy += 2.0  # gravity
        self.vx *= 0.97  # drag
        self.life -= dt / self.max_life
        return self.life > 0

    def draw(self, frame):
        alpha = max(0.0, self.life)
        r = max(1, int(self.radius * alpha))
        # Blend particle color with fading
        c = tuple(int(ch * alpha) for ch in self.color)
        cv2.circle(frame, (int(self.x), int(self.y)), r, c, -1)


particles = []


def emit_particles(x, y, color, count=35):
    """Spawn a burst of particles at (x, y)."""
    for _ in range(count):
        # Vary the color slightly for each particle
        varied = tuple(min(255, max(0, ch + random.randint(-30, 30))) for ch in color)
        particles.append(Particle(x, y, varied))


def update_and_draw_particles(frame, dt):
    global particles
    alive = []
    for p in particles:
        if p.update(dt):
            p.draw(frame)
            alive.append(p)
    particles = alive


# ---------------------- Utility: semi-transparent rounded rectangle ----------------------
def draw_rounded_rect_overlay(frame, x, y, w, h, color=(0, 0, 0), alpha=0.55, radius=16):
    """Draw a semi-transparent rounded rectangle on frame."""
    overlay = frame.copy()
    # Draw filled rounded rect on overlay
    # Top-left to bottom-right with rounded corners
    cv2.rectangle(overlay, (x + radius, y), (x + w - radius, y + h), color, -1)
    cv2.rectangle(overlay, (x, y + radius), (x + w, y + h - radius), color, -1)
    cv2.circle(overlay, (x + radius, y + radius), radius, color, -1)
    cv2.circle(overlay, (x + w - radius, y + radius), radius, color, -1)
    cv2.circle(overlay, (x + radius, y + h - radius), radius, color, -1)
    cv2.circle(overlay, (x + w - radius, y + h - radius), radius, color, -1)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)


# ---------------------- Gradient overlay ----------------------
_vignette_lut = {}

def apply_vignette(frame):
    """Fast vectorized vignette gradient at top and bottom edges."""
    h, w = frame.shape[:2]
    band = h // 6
    if (h, w) not in _vignette_lut:
        top_factors = (1.0 - (np.linspace(1.0, 0.0, band) * 0.35))[:, None, None].astype(np.float32)
        bot_factors = (1.0 - (np.linspace(0.0, 1.0, band) * 0.25))[:, None, None].astype(np.float32)
        _vignette_lut[(h, w)] = (top_factors, bot_factors)
    top_f, bot_f = _vignette_lut[(h, w)]
    frame[:band] = (frame[:band].astype(np.float32) * top_f).astype(np.uint8)
    frame[-band:] = (frame[-band:].astype(np.float32) * bot_f).astype(np.uint8)


def spawn_balloon(frame_width, frame_height):
    # Use the ACTUAL frame size (not the requested constants) so the balloon
    # can never spawn outside what the webcam actually delivers.
    margin = min(BALLOON_MARGIN, frame_width // 3, frame_height // 3)
    margin = max(margin, BALLOON_MAX_RADIUS + 10)  # never smaller than a balloon needs

    x = random.randint(margin, max(margin, frame_width - margin))
    y = random.randint(margin, max(margin, frame_height - margin))
    radius = random.randint(BALLOON_MIN_RADIUS, BALLOON_MAX_RADIUS)
    color = random.choice(BALLOON_COLORS)
    return {"x": x, "y": y, "radius": radius, "color": color, "spawn_time": time.time()}


def draw_balloon(frame, balloon, hovered, t):
    x, y_base, r = balloon["x"], balloon["y"], balloon["radius"]
    color = balloon["color"]

    # Bobbing animation — gentle float up/down
    bob_offset = int(math.sin(t * 2.5) * 6)
    y = y_base + bob_offset

    # Glow ring when hovered/targeted (pulsing)
    if hovered:
        glow_r = r + 12 + int(math.sin(t * 6) * 3)
        # Draw outer glow with reduced opacity effect
        cv2.circle(frame, (x, y), glow_r + 4, (255, 255, 200), 2)
        cv2.circle(frame, (x, y), glow_r, (255, 255, 255), 4)

    # Balloon body
    cv2.circle(frame, (x, y), r, color, -1)
    cv2.circle(frame, (x, y), r, (255, 255, 255), 2)

    # 3D shine/highlight — small white ellipse in upper-left area of balloon
    shine_cx = x - r // 3
    shine_cy = y - r // 3
    shine_axes = (r // 4, r // 6)
    overlay = frame.copy()
    cv2.ellipse(overlay, (shine_cx, shine_cy), shine_axes, -30, 0, 360, (255, 255, 255), -1)
    cv2.addWeighted(overlay, 0.45, frame, 0.55, 0, frame)

    # Little string underneath for balloon look (follows bob)
    string_end = (x, y + r + 40)
    # Wavy string
    pts = []
    for i in range(20):
        frac = i / 19.0
        sx = x + int(math.sin(frac * math.pi * 2 + t * 3) * 4)
        sy = y + r + int(frac * 40)
        pts.append((sx, sy))
    for i in range(len(pts) - 1):
        cv2.line(frame, pts[i], pts[i + 1], (200, 200, 200), 2)


def draw_hud(frame, score, status_text, streak_timer):
    h, w = frame.shape[:2]

    # Semi-transparent HUD background
    draw_rounded_rect_overlay(frame, 10, 8, 440, 82, (20, 20, 20), 0.5, 12)

    cv2.putText(frame, f"Balloons popped: {score}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
    cv2.putText(frame, status_text, (20, 72),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (220, 220, 220), 2)

    # Streak celebration
    if streak_timer is not None:
        elapsed = time.time() - streak_timer
        if elapsed < 1.5:
            alpha = max(0, 1.0 - elapsed / 1.5)
            scale = 1.2 + 0.3 * math.sin(elapsed * 8)
            text = "STREAK!"
            text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, 3)[0]
            tx = w // 2 - text_size[0] // 2
            ty = h // 2 - 100
            color = (0, int(255 * alpha), int(255 * alpha))
            cv2.putText(frame, text, (tx, ty),
                        cv2.FONT_HERSHEY_SIMPLEX, scale, color, 3)


class BubbleHuntGame:
    """
    Core Bubble Hunt game engine.
    Can be run standalone with cv2.imshow or by the backend streamer for in-browser play.
    Optimized for high-FPS, zero-lag streaming.
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
            model_complexity=0,
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        self.score = 0
        self.start_time = time.time()
        self.total_pinches = 0
        self.was_pinching = False
        self.current_streak = 0
        self.best_streak = 0
        self.last_frame = None
        self.balloon = spawn_balloon(width, height)
        self.popped_at = None
        self.streak_timer = None
        self.last_time = time.time()
        self.status = "Point at the balloon, then pinch or tap to pop!"
        self.last_dims = (width, height)

    def pop_balloon(self):
        """Pop the current balloon and emit particles."""
        if self.popped_at is None and self.balloon:
            self.popped_at = time.time()
            self.score += 1
            self.current_streak += 1
            if self.current_streak > self.best_streak:
                self.best_streak = self.current_streak
            try:
                play_pop_sound()
            except Exception:
                pass
            emit_particles(self.balloon["x"], self.balloon["y"], self.balloon["color"], count=40)
            if self.score % 5 == 0 and self.score > 0:
                self.streak_timer = time.time()
                try:
                    play_streak_sound()
                except Exception:
                    pass

    def click(self, x_pct: float, y_pct: float):
        """Allow clicking/tapping directly on the balloon in the browser."""
        if not self.balloon or self.popped_at is not None:
            return
        w, h = self.last_dims
        click_x = int(x_pct * w)
        click_y = int(y_pct * h)
        dx = click_x - self.balloon["x"]
        dy = click_y - self.balloon["y"]
        if math.hypot(dx, dy) <= self.balloon["radius"] + 30:
            self.pop_balloon()

    def step(self) -> Optional[np.ndarray]:
        """Process one game tick and return the annotated frame."""
        now = time.time()
        dt = max(0.001, now - self.last_time)
        self.last_time = now

        frame = None
        if self.cap and self.cap.isOpened():
            success, raw = self.cap.read()
            if success and raw is not None:
                frame = cv2.flip(raw, 1)

        if frame is None:
            frame = np.full((self.height, self.width, 3), (35, 25, 20), dtype=np.uint8)

        self.last_frame = frame
        frame_height, frame_width = frame.shape[:2]
        self.last_dims = (frame_width, frame_height)

        apply_vignette(frame)

        hovered = False
        pinching = False

        if self.cap and self.cap.isOpened():
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Fast downscale for MediaPipe blazepalm detector (3-4x faster inference)
            # Landmarks are normalized [0.0, 1.0], so they map accurately to any frame size
            small_w, small_h = 640, 360
            rgb_small = cv2.resize(rgb, (small_w, small_h), interpolation=cv2.INTER_LINEAR)
            rgb_small.flags.writeable = False
            results = self.hands.process(rgb_small)

            if results.multi_hand_landmarks:
                hand_landmarks = results.multi_hand_landmarks[0]
                mp_drawing.draw_landmarks(
                    frame,
                    hand_landmarks,
                    mp_hands.HAND_CONNECTIONS,
                    mp_styles.get_default_hand_landmarks_style(),
                    mp_styles.get_default_hand_connections_style(),
                )

                h, w = frame.shape[:2]
                index_lm = hand_landmarks.landmark[INDEX_TIP]
                thumb_lm = hand_landmarks.landmark[THUMB_TIP]

                index_px = (int(index_lm.x * w), int(index_lm.y * h))
                thumb_px = (int(thumb_lm.x * w), int(thumb_lm.y * h))

                dx = index_px[0] - thumb_px[0]
                dy = index_px[1] - thumb_px[1]
                pinch_dist = math.hypot(dx, dy)
                pinching = pinch_dist < PINCH_THRESHOLD_PX

                if pinching and not self.was_pinching:
                    self.total_pinches += 1
                self.was_pinching = pinching

                mid = ((index_px[0] + thumb_px[0]) // 2, (index_px[1] + thumb_px[1]) // 2)
                marker_color = (0, 255, 0) if pinching else (0, 200, 255)
                marker_r = 10 + int(math.sin(now * 8) * 3) if pinching else 10
                cv2.circle(frame, mid, marker_r, marker_color, -1)
                cv2.circle(frame, mid, marker_r, (255, 255, 255), 2)

                if self.popped_at is None and self.balloon:
                    bob_offset = int(math.sin(now * 2.5) * 6)
                    balloon_y_visual = self.balloon["y"] + bob_offset
                    bdx = index_px[0] - self.balloon["x"]
                    bdy = index_px[1] - balloon_y_visual
                    dist_to_balloon = math.hypot(bdx, bdy)
                    hovered = dist_to_balloon <= self.balloon["radius"]

                    if hovered and pinching:
                        self.pop_balloon()

        update_and_draw_particles(frame, dt)

        if self.popped_at is None:
            if self.balloon is None:
                self.balloon = spawn_balloon(frame_width, frame_height)
            draw_balloon(frame, self.balloon, hovered, now)
            self.status = "Point at the balloon, then pinch or tap to pop!"
        else:
            elapsed_ms = (now - self.popped_at) * 1000
            if elapsed_ms < POP_DISPLAY_MS:
                progress = elapsed_ms / POP_DISPLAY_MS
                scale = 2.5 * (1.0 - progress * 0.6)
                alpha_val = max(0, 1.0 - progress)
                color = (0, int(255 * alpha_val), int(255 * alpha_val))
                text = "POP!"
                text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, 5)[0]
                tx = self.balloon["x"] - text_size[0] // 2
                ty = self.balloon["y"] + text_size[1] // 2
                cv2.putText(frame, text, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, scale, color, 5)
                self.status = "Nice!"
            else:
                self.balloon = spawn_balloon(frame_width, frame_height)
                self.popped_at = None
                self.status = "New balloon!"

        draw_hud(frame, self.score, self.status, self.streak_timer)
        return frame

    def get_metrics(self) -> Dict:
        play_duration = max(1.0, time.time() - self.start_time)
        accuracy_pct = int(min(100, (self.score / max(1, self.total_pinches)) * 100)) if self.total_pinches > 0 else (100 if self.score > 0 else 0)
        pops_per_min = (self.score / play_duration) * 60.0

        if self.score >= 10 or accuracy_pct >= 75:
            stars = 3
            verdict = "Sharp Focus & Quick Hands!"
        elif self.score >= 4 or accuracy_pct >= 45:
            stars = 2
            verdict = "Great Reflexes & Agility!"
        else:
            stars = 1
            verdict = "Good Effort! Keep Popping!"

        return {
            "score": self.score,
            "total_pinches": self.total_pinches,
            "best_streak": self.best_streak,
            "play_duration": play_duration,
            "accuracy_pct": accuracy_pct,
            "pops_per_min": pops_per_min,
            "stars": stars,
            "verdict": verdict,
        }

    def release(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()
            self.cap = None
        if self.hands:
            self.hands.close()


def main():
    game = BubbleHuntGame(CAM_WIDTH, CAM_HEIGHT, use_camera=True)
    if game.cap is None or not game.cap.isOpened():
        print("Could not open webcam.")
        return

    cv2.namedWindow("Balloon Pop Focus", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("Balloon Pop Focus", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    while True:
        frame = game.step()
        if frame is None:
            break

        cv2.imshow("Balloon Pop Focus", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Show attractive 4-second quit card before closing
    if game.last_frame is not None:
        metrics = game.get_metrics()
        stats = [
            {"label": "Play Time", "value": format_time(metrics["play_duration"]), "color": (255, 220, 100)},
            {"label": "Accuracy", "value": f"{metrics['accuracy_pct']}%", "color": (100, 255, 140)},
            {"label": "Best Streak", "value": f"x{max(metrics['best_streak'], 1)} Streak", "color": (255, 160, 100)},
            {"label": "Pace", "value": f"{metrics['pops_per_min']:.1f} / min", "color": (120, 220, 255)},
        ]

        show_quit_card(
            window_name="Balloon Pop Focus",
            last_frame=game.last_frame,
            game_title="Balloon Pop Focus",
            score=game.score,
            score_label="Balloons Popped",
            stats=stats,
            stars=metrics["stars"],
            verdict=metrics["verdict"],
            duration_s=4.0,
            accent_color=(30, 215, 255),
        )

    game.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()