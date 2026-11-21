from game_card import show_quit_card, format_time
import cv2
import mediapipe as mp
import random
import time
import math
import winsound
import threading

def play_success_sound():
    def sound():
        winsound.Beep(800, 150)
        winsound.Beep(1000, 300)
    threading.Thread(target=sound, daemon=True).start()

def play_beep(freq, duration):
    threading.Thread(target=winsound.Beep, args=(freq, duration), daemon=True).start()

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles

LEFT_WRIST, RIGHT_WRIST = 15, 16
LEFT_SHOULDER, RIGHT_SHOULDER = 11, 12

CANVAS_W, CANVAS_H = 1280, 720

# ---------------------- Tunable settings ----------------------
RED_DURATION_RANGE_S = (2.5, 6.0)
GREEN_TIMEOUT_S = 3.0
RAISE_MARGIN = 0.08  # Made slightly larger so it's a clear move
FEEDBACK_DISPLAY_MS = 2000  # Increased slightly to show animations longer

STATE_RED = "red"
STATE_GREEN = "green"
STATE_FEEDBACK = "feedback"
FEEDBACK_CORRECT = "correct"
FEEDBACK_EARLY = "early"
FEEDBACK_MISSED = "missed"

# ==================== Fun Animations & Particles ====================

class Particle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-15, 15)
        self.vy = random.uniform(-25, -5)
        # Bright kid-friendly colors
        colors = [(0, 255, 255), (255, 0, 255), (255, 255, 0), (0, 255, 0), (0, 165, 255)]
        self.color = random.choice(colors)
        self.radius = random.randint(8, 18)
        self.shape = random.choice(["circle", "square", "triangle"])

    def update(self):
        self.vy += 1.0  # gravity
        self.x += self.vx
        self.y += self.vy

    def draw(self, canvas):
        pts = None
        if self.shape == "circle":
            cv2.circle(canvas, (int(self.x), int(self.y)), self.radius, self.color, -1)
        elif self.shape == "square":
            cv2.rectangle(canvas, (int(self.x - self.radius), int(self.y - self.radius)),
                          (int(self.x + self.radius), int(self.y + self.radius)), self.color, -1)
        else: # triangle
            import numpy as np
            pts = np.array([[int(self.x), int(self.y - self.radius)],
                            [int(self.x - self.radius), int(self.y + self.radius)],
                            [int(self.x + self.radius), int(self.y + self.radius)]], np.int32)
            cv2.fillPoly(canvas, [pts], self.color)


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


def draw_traffic_light(canvas, state):
    bx, by, bw, bh = 40, 110, 160, 420
    draw_rounded_rect_overlay(canvas, bx, by, bw, bh, (15, 18, 28), 0.82, 22)
    cv2.rectangle(canvas, (bx, by), (bx + bw, by + bh), (90, 100, 120), 2, cv2.LINE_AA)

    centers = [
        (bx + bw // 2, by + 75),   # Red
        (bx + bw // 2, by + 185),  # Yellow
        (bx + bw // 2, by + 295),  # Green
    ]
    r = 42

    # 3D Visor Hoods over each lamp
    for cx, cy in centers:
        pts = np.array([
            [cx - r - 6, cy - 8],
            [cx - r, cy - r - 12],
            [cx + r, cy - r - 12],
            [cx + r + 6, cy - 8]
        ], np.int32)
        cv2.fillPoly(canvas, [pts], (25, 28, 38))
        cv2.polylines(canvas, [pts], False, (110, 120, 140), 2, cv2.LINE_AA)

    pulse = (math.sin(time.time() * 8.0) + 1.0) / 2.0

    # 1. Red Light
    is_red = (state == STATE_RED)
    cx, cy = centers[0]
    if is_red:
        glow_r = int(r + 14 + pulse * 8)
        overlay = canvas.copy()
        cv2.circle(overlay, (cx, cy), glow_r, (0, 0, 255), -1)
        cv2.addWeighted(overlay, 0.45, canvas, 0.55, 0, canvas)
        cv2.circle(canvas, (cx, cy), r, (20, 30, 240), -1)
        cv2.circle(canvas, (cx, cy), r - 8, (60, 80, 255), -1)
        cv2.circle(canvas, (cx, cy), r, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(canvas, "WAIT", (cx - 24, cy + 6), cv2.FONT_HERSHEY_DUPLEX, 0.55, (255, 255, 255), 2, cv2.LINE_AA)
    else:
        cv2.circle(canvas, (cx, cy), r, (0, 0, 45), -1)
        cv2.circle(canvas, (cx, cy), r, (40, 45, 60), 2, cv2.LINE_AA)

    # 2. Yellow Light
    cx, cy = centers[1]
    cv2.circle(canvas, (cx, cy), r, (0, 60, 75), -1)
    cv2.circle(canvas, (cx, cy), r, (40, 45, 60), 2, cv2.LINE_AA)

    # 3. Green Light
    is_green = (state == STATE_GREEN)
    cx, cy = centers[2]
    if is_green:
        glow_r = int(r + 16 + pulse * 10)
        overlay = canvas.copy()
        cv2.circle(overlay, (cx, cy), glow_r, (0, 255, 0), -1)
        cv2.addWeighted(overlay, 0.5, canvas, 0.5, 0, canvas)
        cv2.circle(canvas, (cx, cy), r, (30, 230, 50), -1)
        cv2.circle(canvas, (cx, cy), r - 8, (120, 255, 140), -1)
        cv2.circle(canvas, (cx, cy), r, (255, 255, 255), 2, cv2.LINE_AA)
        cv2.putText(canvas, "GO!", (cx - 20, cy + 7), cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 50, 0), 2, cv2.LINE_AA)
    else:
        cv2.circle(canvas, (cx, cy), r, (0, 45, 0), -1)
        cv2.circle(canvas, (cx, cy), r, (40, 45, 60), 2, cv2.LINE_AA)

    # Bottom Turn Badge
    pill_y = by + bh - 50
    if state == STATE_RED:
        draw_rounded_rect_overlay(canvas, bx + 12, pill_y, bw - 24, 36, (20, 20, 40), 0.8, 8)
        cv2.rectangle(canvas, (bx + 12, pill_y), (bx + bw - 12, pill_y + 36), (0, 0, 255), 2, cv2.LINE_AA)
        cv2.putText(canvas, "🔴 WAIT", (bx + 26, pill_y + 24), cv2.FONT_HERSHEY_DUPLEX, 0.65, (100, 140, 255), 2, cv2.LINE_AA)
    elif state == STATE_GREEN:
        draw_rounded_rect_overlay(canvas, bx + 12, pill_y, bw - 24, 36, (15, 35, 20), 0.85, 8)
        cv2.rectangle(canvas, (bx + 12, pill_y), (bx + bw - 12, pill_y + 36), (0, 255, 0), 2, cv2.LINE_AA)
        cv2.putText(canvas, "🟢 YOUR TURN", (bx + 16, pill_y + 24), cv2.FONT_HERSHEY_DUPLEX, 0.55, (120, 255, 140), 2, cv2.LINE_AA)
    else:
        draw_rounded_rect_overlay(canvas, bx + 12, pill_y, bw - 24, 36, (25, 28, 38), 0.7, 8)
        cv2.rectangle(canvas, (bx + 12, pill_y), (bx + bw - 12, pill_y + 36), (180, 180, 180), 1, cv2.LINE_AA)
        cv2.putText(canvas, "RESULT", (bx + 35, pill_y + 24), cv2.FONT_HERSHEY_DUPLEX, 0.55, (220, 220, 220), 1, cv2.LINE_AA)


def draw_hud(canvas, metrics):
    bx, by, bw, bh = CANVAS_W - 440, 16, 420, 95
    draw_rounded_rect_overlay(canvas, bx, by, bw, bh, (12, 16, 28), 0.82, 14)
    cv2.rectangle(canvas, (bx, by), (bx + bw, by + bh), (120, 100, 255), 2, cv2.LINE_AA)

    cv2.putText(canvas, f"STARS: {metrics.correct_count}   TOTAL: {metrics.correct_count + metrics.premature_count + metrics.missed_count}",
                (bx + 18, by + 30), cv2.FONT_HERSHEY_DUPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)

    avg_rt = (sum(metrics.response_times) / len(metrics.response_times)) if metrics.response_times else 0.0
    rt_str = f"{avg_rt:.2f}s" if avg_rt > 0 else "--"
    cv2.putText(canvas, f"React: {rt_str}  •  Early: {metrics.premature_count}  •  Missed: {metrics.missed_count}",
                (bx + 18, by + 60), cv2.FONT_HERSHEY_DUPLEX, 0.58, (255, 215, 80), 1, cv2.LINE_AA)

    cv2.putText(canvas, "LEVEL 4 • TURN-TAKING & IMPULSE CONTROL",
                (bx + 18, by + 84), cv2.FONT_HERSHEY_DUPLEX, 0.48, (120, 220, 255), 1, cv2.LINE_AA)


def draw_target_line(canvas, landmarks, state=STATE_RED):
    """Draws a futuristic holographic neon line with arrows and badge to show reach zone."""
    l_shoulder = landmarks[LEFT_SHOULDER]
    r_shoulder = landmarks[RIGHT_SHOULDER]

    if l_shoulder.visibility > 0.4 and r_shoulder.visibility > 0.4:
        sy = min(l_shoulder.y, r_shoulder.y) - RAISE_MARGIN
        px_y = int(sy * CANVAS_H)

        pulse = (math.sin(time.time() * 6.0) + 1.0) / 2.0
        line_col = (50, 255, 100) if state == STATE_GREEN else (80, 160, 240)

        cv2.line(canvas, (220, px_y), (CANVAS_W - 20, px_y), line_col, 3, cv2.LINE_AA)

        num_arrows = 6
        spacing = (CANVAS_W - 240) // max(1, num_arrows)
        for i in range(num_arrows):
            ax = 240 + i * spacing + int(pulse * 6)
            ay = px_y - 6
            cv2.line(canvas, (ax - 8, ay + 6), (ax, ay - 4), line_col, 2, cv2.LINE_AA)
            cv2.line(canvas, (ax, ay - 4), (ax + 8, ay + 6), line_col, 2, cv2.LINE_AA)

        badge_txt = "⬆️ REACH ABOVE THIS LINE WHEN GREEN! ⬆️"
        ts = cv2.getTextSize(badge_txt, cv2.FONT_HERSHEY_DUPLEX, 0.6, 2)[0]
        bx1 = max(230, CANVAS_W // 2 - ts[0] // 2 - 16)
        by1 = max(10, px_y - 36)
        bx2 = min(CANVAS_W - 20, CANVAS_W // 2 + ts[0] // 2 + 16)
        by2 = px_y - 8

        draw_rounded_rect_overlay(canvas, bx1, by1, bx2 - bx1, by2 - by1, (12, 16, 26), 0.8, 8)
        cv2.rectangle(canvas, (bx1, by1), (bx2, by2), line_col, 1, cv2.LINE_AA)
        cv2.putText(canvas, badge_txt, (bx1 + 16, by1 + 20), cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1, cv2.LINE_AA)


def draw_middle_feedback_card(canvas, kind, title, subtitle, elapsed, w, h):
    """
    Renders an exceptionally polished, animated feedback card right in the middle of the screen.
    kind: 'good' (green/gold victory) or 'wrong' (coral/red warning) or 'missed' (silver/amber)
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

    elif kind == "missed":
        bw = card_w
        bh = card_h
        bx = cx - bw // 2
        by = cy - bh // 2

        draw_rounded_rect_overlay(canvas, bx, by, bw, bh, (25, 25, 35), 0.90, 22)
        cv2.rectangle(canvas, (bx, by), (bx + bw, by + bh), (160, 160, 180), 2, cv2.LINE_AA)

        t_size = cv2.getTextSize(title, cv2.FONT_HERSHEY_DUPLEX, 1.2, 3)[0]
        tx = cx - t_size[0] // 2
        ty = cy - 8
        cv2.putText(canvas, title, (tx, ty), cv2.FONT_HERSHEY_DUPLEX, 1.2, (0, 0, 0), 6, cv2.LINE_AA)
        cv2.putText(canvas, title, (tx, ty), cv2.FONT_HERSHEY_DUPLEX, 1.2, (200, 220, 240), 2, cv2.LINE_AA)

        s_size = cv2.getTextSize(subtitle, cv2.FONT_HERSHEY_DUPLEX, 0.72, 2)[0]
        sx = cx - s_size[0] // 2
        sy = cy + 42
        cv2.putText(canvas, subtitle, (sx, sy), cv2.FONT_HERSHEY_DUPLEX, 0.72, (0, 0, 0), 4, cv2.LINE_AA)
        cv2.putText(canvas, subtitle, (sx, sy), cv2.FONT_HERSHEY_DUPLEX, 0.72, (200, 200, 220), 2, cv2.LINE_AA)


# ==================== Pose detection ====================

def is_hand_up(landmarks):
    def raised(wrist_idx, shoulder_idx):
        wrist, shoulder = landmarks[wrist_idx], landmarks[shoulder_idx]
        if wrist.visibility < 0.5 or shoulder.visibility < 0.5:
            return False
        return wrist.y < shoulder.y - RAISE_MARGIN
    return raised(LEFT_WRIST, LEFT_SHOULDER) or raised(RIGHT_WRIST, RIGHT_SHOULDER)


# ==================== Session metrics ====================

class SessionMetrics:
    def __init__(self):
        self.response_times = []
        self.correct_count = 0
        self.premature_count = 0
        self.missed_count = 0

    def print_summary(self):
        total = self.correct_count + self.premature_count + self.missed_count
        print("\n" + "=" * 50)
        print("MY TURN / YOUR TURN -- SESSION SUMMARY")
        print("=" * 50)
        print(f"Total rounds:          {total}")
        print(f"Awesome responses:     {self.correct_count}")
        print(f"Premature hand lifts:  {self.premature_count}")
        print(f"Missed green signals:  {self.missed_count}")
        if self.response_times:
            avg = sum(self.response_times) / len(self.response_times)
            print(f"Avg response time:     {avg:.2f}s (fastest: {min(self.response_times):.2f}s)")
        print("=" * 50 + "\n")


# ==================== Main ====================

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

    metrics = SessionMetrics()

    state = STATE_RED
    phase_start = time.time()
    red_duration = random.uniform(*RED_DURATION_RANGE_S)
    green_start = None
    
    feedback_type = None
    feedback_text = ""
    feedback_start = None
    particles = []
    last_canvas = None
    start_time = time.time()

    WINDOW_NAME = "My Turn / Your Turn"
    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    while True:
        success, frame = cap.read()
        if not success:
            break
        frame = cv2.flip(frame, 1)
        canvas = cv2.resize(frame, (CANVAS_W, CANVAS_H))
        last_canvas = canvas

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(rgb)

        hand_up = False
        if results.pose_landmarks:
            # Draw skeleton slightly thicker for kids
            mp_drawing.draw_landmarks(
                canvas, results.pose_landmarks, mp_pose.POSE_CONNECTIONS,
                mp_drawing.DrawingSpec(color=(245,117,66), thickness=4, circle_radius=4),
                mp_drawing.DrawingSpec(color=(245,66,230), thickness=4, circle_radius=4)
            )
            # Glowing Wrist keypoint tracking markers
            lms = results.pose_landmarks.landmark
            for idx in [LEFT_WRIST, RIGHT_WRIST]:
                lm = lms[idx]
                if lm.visibility > 0.4:
                    pt = (int(lm.x * CANVAS_W), int(lm.y * CANVAS_H))
                    ring_c = (0, 255, 0) if state == STATE_GREEN else (0, 140, 255)
                    cv2.circle(canvas, pt, 18, (0, 0, 0), 2)
                    cv2.circle(canvas, pt, 14, ring_c, -1)
                    cv2.circle(canvas, pt, 6, (255, 255, 255), -1)

            hand_up = is_hand_up(results.pose_landmarks.landmark)
            if state in [STATE_RED, STATE_GREEN]:
                draw_target_line(canvas, results.pose_landmarks.landmark, state)

        # Logic Update
        if state == STATE_RED:
            if hand_up:
                metrics.premature_count += 1
                feedback_type = FEEDBACK_EARLY
                feedback_text = "OOPS! TOO EARLY!"
                feedback_start = time.time()
                state = STATE_FEEDBACK
                play_beep(250, 400)
            elif time.time() - phase_start >= red_duration:
                state = STATE_GREEN
                green_start = time.time()
                play_beep(600, 300)

        elif state == STATE_GREEN:
            elapsed = time.time() - green_start
            if hand_up:
                rt = elapsed
                metrics.response_times.append(rt)
                metrics.correct_count += 1
                feedback_type = FEEDBACK_CORRECT
                feedback_text = "AWESOME! YAY!"
                feedback_start = time.time()
                
                # Spawn confetti!
                particles = [Particle(CANVAS_W // 2 + random.randint(-200, 200), CANVAS_H // 2) for _ in range(120)]
                state = STATE_FEEDBACK
                play_success_sound()
            elif elapsed >= GREEN_TIMEOUT_S:
                metrics.missed_count += 1
                feedback_type = FEEDBACK_MISSED
                feedback_text = "MISSED IT!"
                feedback_start = time.time()
                state = STATE_FEEDBACK
                play_beep(250, 400)

        elif state == STATE_FEEDBACK:
            elapsed_fb = time.time() - feedback_start
            if elapsed_fb * 1000 >= FEEDBACK_DISPLAY_MS:
                state = STATE_RED
                phase_start = time.time()
                red_duration = random.uniform(*RED_DURATION_RANGE_S)
                particles = []  # Clear confetti
                play_beep(300, 200)

        # Drawing Update
        draw_traffic_light(canvas, state)
        draw_hud(canvas, metrics)

        # Draw State text/animations
        if state == STATE_RED:
            pulse = math.sin(time.time() * 5) * 0.2
            draw_animated_text(canvas, "WAIT...", (0, 0, 255), 2.0 + pulse, y_offset=250)
        elif state == STATE_GREEN:
            pulse = math.sin(time.time() * 15) * 0.3
            draw_animated_text(canvas, "GO GO GO!!!", (0, 255, 0), 2.5 + pulse, y_offset=250)
        elif state == STATE_FEEDBACK:
            elapsed_fb = time.time() - feedback_start

            if feedback_type == FEEDBACK_CORRECT:
                for p in particles:
                    p.update()
                    p.draw(canvas)
                last_rt = metrics.response_times[-1] if metrics.response_times else 0.8
                draw_middle_feedback_card(canvas, "good", "🌟 GREAT JOB!", f"PERFECT TIMING! SPEED: {last_rt:.2f}s", elapsed_fb, CANVAS_W, CANVAS_H)

            elif feedback_type == FEEDBACK_EARLY:
                draw_middle_feedback_card(canvas, "wrong", "❌ WRONG MOVE!", "TOO EARLY! WAIT FOR GREEN!", elapsed_fb, CANVAS_W, CANVAS_H)

            elif feedback_type == FEEDBACK_MISSED:
                draw_middle_feedback_card(canvas, "missed", "⏰ MISSED IT!", "BE QUICKER TO RAISE YOUR HAND!", elapsed_fb, CANVAS_W, CANVAS_H)

        cv2.imshow(WINDOW_NAME, canvas)
        key = cv2.waitKey(1) & 0xFF
        if key in (ord('q'), ord('Q'), 27):
            break
        if key in (ord('f'), ord('F')):
            curr = cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN)
            new_val = cv2.WINDOW_NORMAL if curr == cv2.WINDOW_FULLSCREEN else cv2.WINDOW_FULLSCREEN
            cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, new_val)

    # Show attractive Level 4 4-second quit card before closing
    if last_canvas is None:
        last_canvas = np.zeros((CANVAS_H, CANVAS_W, 3), dtype=np.uint8)

    play_duration = max(1.0, time.time() - start_time)
    tot_turns = metrics.correct_count + metrics.premature_count + metrics.missed_count
    accuracy_pct = int((metrics.correct_count / max(1, tot_turns)) * 100) if tot_turns > 0 else (100 if metrics.correct_count > 0 else 0)
    avg_rt = (sum(metrics.response_times) / len(metrics.response_times)) if metrics.response_times else 0.0

    if metrics.correct_count >= 8 or accuracy_pct >= 80:
        tier_badge = "GRANDMASTER"
        stars = 3
        verdict = "Flawless Impulse Control!"
    elif metrics.correct_count >= 4 or accuracy_pct >= 55:
        tier_badge = "MASTER"
        stars = 2
        verdict = "Great Turn-Taking Timing!"
    else:
        tier_badge = "EXPERT"
        stars = 1
        verdict = "Good Effort! Keep Taking Turns!"

    stats = [
        {"label": "Play Time", "value": format_time(play_duration), "color": (30, 215, 255), "percent": min(1.0, play_duration / 180.0)},
        {"label": "Accuracy", "value": f"{accuracy_pct}%", "color": (100, 255, 140), "percent": accuracy_pct / 100.0},
        {"label": "Avg React", "value": f"{avg_rt:.2f}s" if avg_rt > 0 else "--", "color": (255, 220, 80), "percent": max(0.2, min(1.0, 1.0 - (avg_rt - 0.5) / 2.5))},
        {"label": "Early Moves", "value": str(metrics.premature_count), "color": (120, 100, 255), "percent": max(0.1, min(1.0, 1.0 - metrics.premature_count / 10.0))},
    ]

    show_quit_card(
        window_name=WINDOW_NAME,
        last_frame=last_canvas,
        game_title="My Turn / Your Turn",
        score=metrics.correct_count,
        score_label="Turns Completed",
        stats=stats,
        stars=stars,
        verdict=verdict,
        duration_s=4.0,
        accent_color=(30, 215, 255),
        tier_badge=tier_badge,
    )

    cap.release()
    pose.close()
    cv2.destroyAllWindows()
    metrics.print_summary()


if __name__ == "__main__":
    main()