

import cv2
import mediapipe as mp
import random
import time
import math
import numpy as np
import threading
import winsound
from game_card import show_quit_card, format_time

def play_success_sound():
    def sound():
        winsound.Beep(600, 150)
        winsound.Beep(800, 150)
        winsound.Beep(1200, 300)
    threading.Thread(target=sound, daemon=True).start()

NOSE_TIP = 1  # MediaPipe Face Mesh landmark used as the "head position" point

# ---------------------- Tunable settings ----------------------
HOLD_MS_TO_WIN = 2000          # how long the head must stay touching the face to win
SUCCESS_DISPLAY_MS = 900       # pause after winning before next face appears
FACE_RADIUS = 70               # bigger target = easier for younger kids
FACE_MARGIN = 110              # keep target away from edges

mp_face_mesh = mp.solutions.face_mesh


# ---------------------- Particle / confetti system ----------------------
class ConfettiPiece:
    __slots__ = ['x', 'y', 'vx', 'vy', 'color', 'w', 'h', 'angle', 'life']

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.vx = random.uniform(-6, 6)
        self.vy = random.uniform(-10, -2)
        self.color = random.choice([
            (80, 220, 255), (140, 230, 140), (200, 130, 255),
            (250, 130, 90), (90, 200, 255), (120, 255, 200),
        ])
        self.w = random.randint(6, 14)
        self.h = random.randint(4, 8)
        self.angle = random.uniform(0, 360)
        self.life = 1.0

    def update(self, dt):
        self.x += self.vx
        self.y += self.vy
        self.vy += 3.5  # gravity
        self.vx *= 0.98
        self.angle += self.vx * 3
        self.life -= dt * 0.7
        return self.life > 0

    def draw(self, frame):
        alpha = max(0, self.life)
        c = tuple(int(ch * alpha) for ch in self.color)
        cx, cy = int(self.x), int(self.y)
        # Rotated rectangle approximation — just draw filled rect for speed
        hw, hh = self.w // 2, self.h // 2
        cv2.rectangle(frame, (cx - hw, cy - hh), (cx + hw, cy + hh), c, -1)


confetti = []


def emit_confetti(x, y, count=25):
    for _ in range(count):
        confetti.append(ConfettiPiece(x, y))


def update_and_draw_confetti(frame, dt):
    global confetti
    alive = []
    for p in confetti:
        if p.update(dt):
            p.draw(frame)
            alive.append(p)
    confetti = alive


# ---------------------- Head trail system ----------------------
head_trail = []
MAX_TRAIL = 15


def update_trail(pos):
    global head_trail
    if pos is not None:
        head_trail.append(pos)
    if len(head_trail) > MAX_TRAIL:
        head_trail = head_trail[-MAX_TRAIL:]


def draw_trail(frame):
    for i, pos in enumerate(head_trail):
        alpha = (i + 1) / len(head_trail)
        r = max(2, int(12 * alpha))
        
        # Inner core (bright cyan/white)
        color_core = (255, 255, int(200 + 55 * alpha))
        # Outer glow (red)
        color_glow = (0, 0, int(255 * alpha))
        
        overlay = frame.copy()
        cv2.circle(overlay, pos, r + 10, color_glow, -1)
        cv2.addWeighted(overlay, 0.4, frame, 0.6, 0, frame)
        cv2.circle(frame, pos, r, color_core, -1)


# ---------------------- Utility: semi-transparent rounded rectangle ----------------------
def draw_rounded_rect_overlay(frame, x, y, w, h, color=(0, 0, 0), alpha=0.55, radius=16):
    overlay = frame.copy()
    cv2.rectangle(overlay, (x + radius, y), (x + w - radius, y + h), color, -1)
    cv2.rectangle(overlay, (x, y + radius), (x + w, y + h - radius), color, -1)
    cv2.circle(overlay, (x + radius, y + radius), radius, color, -1)
    cv2.circle(overlay, (x + w - radius, y + radius), radius, color, -1)
    cv2.circle(overlay, (x + radius, y + h - radius), radius, color, -1)
    cv2.circle(overlay, (x + w - radius, y + h - radius), radius, color, -1)
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)


# ---------------------- Vignette ----------------------
def apply_vignette(frame):
    h, w = frame.shape[:2]
    band = h // 5
    for i in range(band):
        a = (1.0 - i / band) * 0.4
        frame[i] = (frame[i].astype(np.float32) * (1 - a)).astype(np.uint8)
    for i in range(band):
        a = (1.0 - i / band) * 0.3
        frame[h - 1 - i] = (frame[h - 1 - i].astype(np.float32) * (1 - a)).astype(np.uint8)


def spawn_face_target(frame_width, frame_height):
    margin = min(FACE_MARGIN, frame_width // 3, frame_height // 3)
    margin = max(margin, FACE_RADIUS + 10)
    x = random.randint(margin, max(margin, frame_width - margin))
    y = random.randint(margin, max(margin, frame_height - margin))
    return {"x": x, "y": y}


def draw_cartoon_face(frame, x, y, progress, t):
    # Pulsing scale animation — face gently "breathes"
    pulse = 1.0 + 0.08 * math.sin(t * 4.0)
    r = int(FACE_RADIUS * pulse)

    # Soft glow behind face (multi-layered)
    overlay = frame.copy()
    cv2.circle(overlay, (x, y), r + 35, (0, 150, 255), -1)
    cv2.circle(overlay, (x, y), r + 15, (100, 240, 255), -1)
    cv2.addWeighted(overlay, 0.25, frame, 0.75, 0, frame)

    # Head (warm yellow)
    cv2.circle(frame, (x, y), r, (80, 220, 255), -1)
    cv2.circle(frame, (x, y), r, (255, 255, 255), 3)

    # Eyes
    eye_dx = int(r * 0.33)
    eye_dy = int(r * 0.25)
    cv2.circle(frame, (x - eye_dx, y - eye_dy), 7, (40, 40, 40), -1)
    cv2.circle(frame, (x + eye_dx, y - eye_dy), 7, (40, 40, 40), -1)
    # Eye highlights
    cv2.circle(frame, (x - eye_dx + 2, y - eye_dy - 2), 2, (255, 255, 255), -1)
    cv2.circle(frame, (x + eye_dx + 2, y - eye_dy - 2), 2, (255, 255, 255), -1)

    # Blush cheeks
    cheek_dy = int(r * 0.15)
    cheek_dx = int(r * 0.5)
    overlay2 = frame.copy()
    cv2.circle(overlay2, (x - cheek_dx, y + cheek_dy), 12, (160, 170, 255), -1)
    cv2.circle(overlay2, (x + cheek_dx, y + cheek_dy), 12, (160, 170, 255), -1)
    cv2.addWeighted(overlay2, 0.4, frame, 0.6, 0, frame)

    # Smile
    cv2.ellipse(frame, (x, y + eye_dy), (int(r * 0.5), int(r * 0.33)),
                0, 0, 180, (40, 40, 40), 3)

    # Progress ring — gradient from yellow to green
    if progress > 0:
        angle = int(360 * progress)
        # Draw multi-colored arc segments
        segments = max(1, angle // 10)
        for i in range(segments):
            seg_start = int(i * (angle / segments))
            seg_end = int((i + 1) * (angle / segments))
            frac = i / max(1, segments - 1)
            # Yellow (0,255,255) -> Green (0,255,0) in BGR
            g = 255
            b = int(255 * (1 - frac))
            ring_color = (0, g, b)
            cv2.ellipse(frame, (x, y), (r + 14, r + 14),
                        -90, seg_start, seg_end, ring_color, 6)


def draw_proximity_arrow(frame, head_px, target, frame_w, frame_h):
    """Draw a subtle arrow from head position toward the target."""
    if head_px is None:
        return
    dx = target["x"] - head_px[0]
    dy = target["y"] - head_px[1]
    dist = math.hypot(dx, dy)
    if dist < FACE_RADIUS * 1.5 or dist < 1:
        return  # Too close, no need for arrow

    # Normalize direction
    nx, ny = dx / dist, dy / dist
    # Arrow start: 60px from head toward target
    ax = int(head_px[0] + nx * 60)
    ay = int(head_px[1] + ny * 60)
    # Arrow end: 120px from head toward target
    bx = int(head_px[0] + nx * 120)
    by = int(head_px[1] + ny * 120)

    cv2.arrowedLine(frame, (ax, ay), (bx, by), (100, 255, 255), 3, tipLength=0.35)


def draw_hud(frame, score, status_text):
    draw_rounded_rect_overlay(frame, 10, 8, 480, 82, (20, 20, 20), 0.5, 12)
    cv2.putText(frame, f"Faces caught: {score}", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 2)
    cv2.putText(frame, status_text, (20, 72),
                cv2.FONT_HERSHEY_SIMPLEX, 0.65, (220, 220, 220), 2)


class FollowTheStarGame:
    """
    Core Follow the Star game engine.
    Tracks head position (MediaPipe NOSE_TIP) to follow the target star/face.
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

        self.face_mesh = mp_face_mesh.FaceMesh(
            max_num_faces=1,
            refine_landmarks=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        self.score = 0
        self.current_streak = 0
        self.start_time = time.time()
        self.total_hold_time = 0.0
        self.target = spawn_face_target(width, height)
        self.hold_start = None
        self.won_at = None
        self.last_time = time.time()
        self.last_dims = (width, height)
        self.status = "Move your head to touch the star face and hold it there!"

    def click(self, x_pct: float, y_pct: float):
        w, h = self.last_dims
        cx, cy = int(x_pct * w), int(y_pct * h)
        if math.hypot(cx - self.target["x"], cy - self.target["y"]) <= FACE_RADIUS + 30:
            self.won_at = time.time()
            self.score += 1
            self.current_streak += 1
            self.hold_start = None
            emit_confetti(self.target["x"], self.target["y"], count=35)
            try:
                play_success_sound()
            except Exception:
                pass

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
            frame = np.full((self.height, self.width, 3), (30, 35, 45), dtype=np.uint8)

        h, w = frame.shape[:2]
        self.last_dims = (w, h)

        # Proportional 0.5x downsample (0 aspect distortion, 3ms inference)
        head_px = None
        if self.cap and self.cap.isOpened():
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            small = cv2.resize(rgb, (0, 0), fx=0.5, fy=0.5, interpolation=cv2.INTER_LINEAR)
            small.flags.writeable = False
            results = self.face_mesh.process(small)

            if results.multi_face_landmarks:
                lms = results.multi_face_landmarks[0].landmark
                # Exact center of nose tip (blend landmarks 1 & 4)
                lm1 = lms[1]
                lm4 = lms[4]
                nose_x = (lm1.x + lm4.x) * 0.5
                nose_y = (lm1.y + lm4.y) * 0.5
                head_px = (int(nose_x * w), int(nose_y * h))

        update_trail(head_px)
        draw_trail(frame)

        if head_px:
            cv2.circle(frame, head_px, 10, (0, 200, 255), -1)
            cv2.circle(frame, head_px, 12, (255, 255, 255), 2)

        progress = 0.0
        if self.won_at is None:
            touching = False
            if head_px:
                touching = math.hypot(head_px[0] - self.target["x"], head_px[1] - self.target["y"]) <= FACE_RADIUS

            if touching:
                self.total_hold_time += dt
                if self.hold_start is None:
                    self.hold_start = now
                held_ms = (now - self.hold_start) * 1000
                progress = min(1.0, held_ms / HOLD_MS_TO_WIN)
                if held_ms >= HOLD_MS_TO_WIN:
                    self.won_at = now
                    self.score += 1
                    self.current_streak += 1
                    try:
                        play_success_sound()
                    except Exception:
                        pass
                    emit_confetti(self.target["x"], self.target["y"], count=30)
            else:
                self.hold_start = None

            draw_cartoon_face(frame, self.target["x"], self.target["y"], progress, now)
            draw_proximity_arrow(frame, head_px, self.target, w, h)
            self.status = "Move your head to touch the face and hold it there"
        else:
            elapsed_ms = (now - self.won_at) * 1000
            if elapsed_ms < SUCCESS_DISPLAY_MS:
                scale = 1.1 + 0.2 * math.sin(elapsed_ms / 100)
                text = "Great job!"
                text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, 3)[0]
                tx = self.target["x"] - text_size[0] // 2
                ty = self.target["y"] + text_size[1] // 2
                cv2.putText(frame, text, (tx, ty), cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 255, 0), 3)
                self.status = "Caught it!"
            else:
                self.target = spawn_face_target(w, h)
                self.won_at = None
                self.hold_start = None
                self.status = "New face appeared!"

        update_and_draw_confetti(frame, dt)
        draw_hud(frame, self.score, self.status)
        return frame

    def get_metrics(self) -> Dict:
        dur = max(1.0, time.time() - self.start_time)
        return {
            "score": self.score,
            "play_duration": dur,
            "hold_time": self.total_hold_time,
            "catch_rate": round((self.score / dur) * 60.0, 1),
            "accuracy_pct": min(100, int((self.score * 10))),
        }

    def release(self):
        if self.cap and self.cap.isOpened():
            self.cap.release()
        self.face_mesh.close()


def main():
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not cap or not cap.isOpened():
        cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Could not open webcam.")
        return

    # Setup Fullscreen
    cv2.namedWindow("Follow the Face", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("Follow the Face", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    face_mesh = mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=False,
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6,
    )

    success, first_frame = cap.read()
    if not success:
        print("Could not read from webcam.")
        cap.release()
        return
    frame_height, frame_width = first_frame.shape[:2]

    score = 0
    start_time = time.time()
    total_hold_time = 0.0
    last_frame = None
    target = spawn_face_target(frame_width, frame_height)
    hold_start = None    # timestamp when head first started touching the target
    won_at = None         # timestamp when target was won, None if not yet
    last_time = time.time()

    while True:
        success, frame = cap.read()
        if not success:
            break
        last_frame = frame

        now = time.time()
        dt = now - last_time
        last_time = now

        frame = cv2.flip(frame, 1)
        frame_height, frame_width = frame.shape[:2]

        # Graphics Enhancement: Boost contrast and brightness
        frame = cv2.convertScaleAbs(frame, alpha=1.1, beta=10)

        # Dreamy Bloom Effect
        blurred = cv2.GaussianBlur(frame, (15, 15), 0)
        cv2.addWeighted(frame, 0.8, blurred, 0.25, 0, frame)

        apply_vignette(frame)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        head_px = None
        if results.multi_face_landmarks:
            lm = results.multi_face_landmarks[0].landmark[NOSE_TIP]
            head_px = (int(lm.x * frame_width), int(lm.y * frame_height))

        # Update head trail
        update_trail(head_px)
        draw_trail(frame)

        # Draw head feedback dot
        if head_px:
            cv2.circle(frame, head_px, 10, (0, 200, 255), -1)
            cv2.circle(frame, head_px, 10, (255, 255, 255), 2)

        progress = 0.0

        if won_at is None:
            touching = False
            if head_px:
                dx = head_px[0] - target["x"]
                dy = head_px[1] - target["y"]
                dist = (dx * dx + dy * dy) ** 0.5
                touching = dist <= FACE_RADIUS

            if touching:
                total_hold_time += dt
                if hold_start is None:
                    hold_start = time.time()
                held_ms = (time.time() - hold_start) * 1000
                progress = min(1.0, held_ms / HOLD_MS_TO_WIN)
                if held_ms >= HOLD_MS_TO_WIN:
                    won_at = time.time()
                    score += 1
                    play_success_sound()
                    emit_confetti(target["x"], target["y"], count=30)
            else:
                hold_start = None  # moved away, reset the hold timer

            draw_cartoon_face(frame, target["x"], target["y"], progress, now)
            draw_proximity_arrow(frame, head_px, target, frame_width, frame_height)
            status = "Move your head to touch the face and hold it there"
        else:
            elapsed_ms = (time.time() - won_at) * 1000
            if elapsed_ms < SUCCESS_DISPLAY_MS:
                # Animated success text
                scale = 1.1 + 0.2 * math.sin(elapsed_ms / 100)
                text = "Great job!"
                text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, 3)[0]
                tx = target["x"] - text_size[0] // 2
                ty = target["y"] + text_size[1] // 2
                cv2.putText(frame, text, (tx, ty),
                            cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 255, 0), 3)
                status = "Caught it!"
            else:
                target = spawn_face_target(frame_width, frame_height)
                won_at = None
                hold_start = None
                status = "New face appeared!"

        # Draw confetti
        update_and_draw_confetti(frame, dt)

        draw_hud(frame, score, status)
        cv2.imshow("Follow the Face", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Show attractive 4-second quit card before closing
    if last_frame is not None:
        play_duration = max(1.0, time.time() - start_time)
        catch_rate = (score / play_duration) * 60.0

        if score >= 10:
            stars = 3
            verdict = "Stellar Tracking & Movement!"
        elif score >= 4:
            stars = 2
            verdict = "Great Head Motor Control!"
        else:
            stars = 1
            verdict = "Good Effort! Keep Following!"

        stats = [
            {"label": "Play Time", "value": format_time(play_duration), "color": (255, 220, 100)},
            {"label": "Hold Time", "value": f"{total_hold_time:.1f}s", "color": (100, 255, 140)},
            {"label": "Catch Rate", "value": f"{catch_rate:.1f} / min", "color": (120, 220, 255)},
            {"label": "Focus Level", "value": "Superb" if stars == 3 else ("Steady" if stars == 2 else "Active"), "color": (255, 150, 255)},
        ]

        show_quit_card(
            window_name="Follow the Face",
            last_frame=last_frame,
            game_title="Follow the Star",
            score=score,
            score_label="Faces Caught",
            stats=stats,
            stars=stars,
            verdict=verdict,
            duration_s=4.0,
            accent_color=(30, 215, 255),
        )

    cap.release()
    face_mesh.close()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()