from game_card import show_quit_card, format_time
import cv2
import time
import random
import math
import numpy as np
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

def play_appear_sound():
    threading.Thread(target=winsound.Beep, args=(900, 150), daemon=True).start()


from ultralytics import YOLO

# Get screen resolution for true fullscreen without stretching
try:
    import ctypes
    user32 = ctypes.windll.user32
    user32.SetProcessDPIAware()
    SCREEN_WIDTH = user32.GetSystemMetrics(0)
    SCREEN_HEIGHT = user32.GetSystemMetrics(1)
except Exception:
    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 720

try:
    import pyttsx3
    _tts_engine = pyttsx3.init()
    # Try to make the voice friendlier
    voices = _tts_engine.getProperty('voices')
    for voice in voices:
        if 'zira' in voice.name.lower() or 'female' in voice.name.lower():
            _tts_engine.setProperty('voice', voice.id)
            break
    _tts_engine.setProperty('rate', 160) # Slightly slower and clearer
    VOICE_AVAILABLE = True
except Exception:
    _tts_engine = None
    VOICE_AVAILABLE = False

_speaking_lock = threading.Lock()
_is_speaking = False

def speak_async(text):
    global _is_speaking
    if not VOICE_AVAILABLE:
        return
    with _speaking_lock:
        if _is_speaking:
            return
        _is_speaking = True

    def _run():
        global _is_speaking
        try:
            _tts_engine.say(text)
            _tts_engine.runAndWait()
        finally:
            with _speaking_lock:
                _is_speaking = False

    threading.Thread(target=_run, daemon=True).start()

CONF_THRESHOLD = 0.25
STABLE_HOLD_MS_BEFORE_ASK = 750
LISTEN_WINDOW_S = 12.0
FEEDBACK_DISPLAY_MS = 3500
INFERENCE_SIZE = 384

TARGET_MAPPING = {
    "cell phone": "cell phone",
    "laptop": "cell phone",
    "tv": "cell phone",
    "remote": "cell phone",
    "cup": "cup",
    "bottle": "bottle",
    "book": "book",
    "banana": "banana",
    "apple": "apple",
    "orange": "orange",
    "teddy bear": "teddy bear",
    "scissors": "scissors",
    "toothbrush": "toothbrush",
    "spoon": "spoon",
    "fork": "fork",
    "bowl": "bowl",
    "clock": "clock",
    "mouse": "mouse",
    "backpack": "backpack",
    "umbrella": "umbrella",
}

TARGET_OBJECTS = [
    "cell phone", "cup", "bottle", "banana", "apple", "book",
    "scissors", "teddy bear", "clock", "spoon", "fork",
    "backpack", "umbrella", "toothbrush", "orange", "bowl", "mouse"
]

# Kid-friendly bright, vibrant colors for the 4 buttons (BGR format)
BUTTON_COLORS = [
    ((255, 120, 80), (255, 150, 110)),  # Soft Blue
    ((200, 100, 255), (230, 130, 255)), # Bright Pink
    ((100, 220, 100), (140, 250, 140)), # Lime Green
    ((50, 210, 255), (100, 230, 255)),  # Sunny Yellow
]

STATE_IDLE = "idle"
STATE_ASKING = "asking"
STATE_FEEDBACK = "feedback"

_mouse_pos = (0, 0)
_clicked_point = None

def mouse_callback(event, x, y, flags, param):
    global _clicked_point, _mouse_pos
    _mouse_pos = (x, y)
    if event == cv2.EVENT_LBUTTONDOWN:
        _clicked_point = (x, y)

class ConfettiPiece:
    __slots__ = ['x', 'y', 'vx', 'vy', 'color', 'w', 'h', 'life', 'rot', 'rot_speed']

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.vx = random.uniform(-18, 18)
        self.vy = random.uniform(-28, -12)
        # Bright vibrant confetti
        self.color = random.choice([
            (80, 220, 255), (140, 230, 140), (200, 130, 255),
            (250, 130, 90), (90, 200, 255), (120, 255, 200),
            (255, 255, 0), (255, 0, 255), (0, 255, 255)
        ])
        self.w = random.randint(15, 35)
        self.h = random.randint(10, 25)
        self.life = 1.0
        self.rot = random.uniform(0, 360)
        self.rot_speed = random.uniform(-15, 15)

    def update(self, dt):
        self.x += self.vx
        self.y += self.vy
        self.vy += 6.0  # gravity
        self.vx *= 0.95
        self.rot += self.rot_speed
        self.life -= dt * 0.4
        return self.life > 0

    def draw(self, frame):
        alpha = max(0, self.life)
        c = tuple(int(ch * alpha) for ch in self.color)
        rect = ((self.x, self.y), (self.w, self.h), self.rot)
        box = cv2.boxPoints(rect)
        box = np.int32(box)
        cv2.fillPoly(frame, [box], c, lineType=cv2.LINE_AA)

confetti_particles = []

def emit_confetti(x, y, count=80):
    for _ in range(count):
        confetti_particles.append(ConfettiPiece(x, y))

def update_and_draw_confetti(frame, dt):
    global confetti_particles
    alive = []
    for p in confetti_particles:
        if p.update(dt):
            p.draw(frame)
            alive.append(p)
    confetti_particles = alive

def draw_rounded_rect_overlay(frame, x, y, w, h, color, alpha=0.55, radius=16, border_color=None, border_thickness=2):
    # Optimized ROI-based drawing so fullscreen runs fast without lag
    fh, fw = frame.shape[:2]
    x_min = max(0, x)
    y_min = max(0, y)
    x_max = min(fw, x + w)
    y_max = min(fh, y + h)
    
    if x_min >= x_max or y_min >= y_max:
        return
        
    roi = frame[y_min:y_max, x_min:x_max].copy()
    rx = x - x_min
    ry = y - y_min
    
    cv2.rectangle(roi, (rx + radius, ry), (rx + w - radius, ry + h), color, -1, lineType=cv2.LINE_AA)
    cv2.rectangle(roi, (rx, ry + radius), (rx + w, ry + h - radius), color, -1, lineType=cv2.LINE_AA)
    cv2.circle(roi, (rx + radius, ry + radius), radius, color, -1, lineType=cv2.LINE_AA)
    cv2.circle(roi, (rx + w - radius, ry + radius), radius, color, -1, lineType=cv2.LINE_AA)
    cv2.circle(roi, (rx + radius, ry + h - radius), radius, color, -1, lineType=cv2.LINE_AA)
    cv2.circle(roi, (rx + w - radius, ry + h - radius), radius, color, -1, lineType=cv2.LINE_AA)
    
    cv2.addWeighted(roi, alpha, frame[y_min:y_max, x_min:x_max], 1 - alpha, 0, frame[y_min:y_max, x_min:x_max])
    
    if border_color is not None:
        cv2.line(frame, (max(0, x + radius), max(0, y)), (min(fw, x + w - radius), max(0, y)), border_color, border_thickness, lineType=cv2.LINE_AA)
        cv2.line(frame, (max(0, x + radius), min(fh, y + h)), (min(fw, x + w - radius), min(fh, y + h)), border_color, border_thickness, lineType=cv2.LINE_AA)
        cv2.line(frame, (max(0, x), max(0, y + radius)), (max(0, x), min(fh, y + h - radius)), border_color, border_thickness, lineType=cv2.LINE_AA)
        cv2.line(frame, (min(fw, x + w), max(0, y + radius)), (min(fw, x + w), min(fh, y + h - radius)), border_color, border_thickness, lineType=cv2.LINE_AA)
        
        cv2.ellipse(frame, (x + radius, y + radius), (radius, radius), 180, 0, 90, border_color, border_thickness, lineType=cv2.LINE_AA)
        cv2.ellipse(frame, (x + w - radius, y + radius), (radius, radius), 270, 0, 90, border_color, border_thickness, lineType=cv2.LINE_AA)
        cv2.ellipse(frame, (x + radius, y + h - radius), (radius, radius), 90, 0, 90, border_color, border_thickness, lineType=cv2.LINE_AA)
        cv2.ellipse(frame, (x + w - radius, y + h - radius), (radius, radius), 0, 0, 90, border_color, border_thickness, lineType=cv2.LINE_AA)

def draw_button(frame, text, x, y, w, h, base_color, hover_color, is_hovered, text_color=(255,255,255)):
    color = hover_color if is_hovered else base_color
    # Thick white cartoon border
    draw_rounded_rect_overlay(frame, x, y, w, h, color, alpha=1.0, radius=30, border_color=(255,255,255), border_thickness=5)
    
    font = cv2.FONT_HERSHEY_DUPLEX
    font_scale = 1.4
    thickness = 4
    text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
    tx = x + (w - text_size[0]) // 2
    ty = y + (h + text_size[1]) // 2
    
    # Text shadow for pop
    cv2.putText(frame, text, (tx+4, ty+4), font, font_scale, (0, 0, 0), thickness, lineType=cv2.LINE_AA)
    cv2.putText(frame, text, (tx, ty), font, font_scale, text_color, thickness, lineType=cv2.LINE_AA)

def draw_detection_box(frame, x1, y1, x2, y2, label, conf, is_locked, t, reveal_label):
    if is_locked:
        fh, fw = frame.shape[:2]
        pad = 30
        x_min = max(0, x1 - pad)
        y_min = max(0, y1 - pad)
        x_max = min(fw, x2 + pad)
        y_max = min(fh, y2 + pad)
        
        if x_min < x_max and y_min < y_max:
            glow_alpha = 0.3 + 0.15 * math.sin(t * 8)
            roi = frame[y_min:y_max, x_min:x_max].copy()
            cv2.rectangle(roi, (x1 - 15 - x_min, y1 - 15 - y_min), (x2 + 15 - x_min, y2 + 15 - y_min), (200, 100, 255), -1, lineType=cv2.LINE_AA)
            cv2.addWeighted(roi, glow_alpha, frame[y_min:y_max, x_min:x_max], 1 - glow_alpha, 0, frame[y_min:y_max, x_min:x_max])

        color = (255, 100, 200) # Hot pink
        thickness = 8
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, thickness, lineType=cv2.LINE_AA)
        
        label_text = label.upper() if reveal_label else "?"
        text_size = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_DUPLEX, 1.2, 4)[0]
        
        lx = x1 + (x2 - x1 - text_size[0]) // 2
        ly = max(0, y1 - text_size[1] - 40)
        draw_rounded_rect_overlay(frame, lx - 20, ly, text_size[0] + 40, text_size[1] + 30, color, alpha=1.0, radius=15, border_color=(255,255,255), border_thickness=3)
        
        cv2.putText(frame, label_text, (lx, ly + text_size[1] + 10), cv2.FONT_HERSHEY_DUPLEX, 1.2, (255, 255, 255), 4, lineType=cv2.LINE_AA)
    else:
        color = (255, 255, 255)
        thickness = 4
        dash_len = 25
        for i in range(x1, x2, dash_len*2):
            cv2.line(frame, (i, y1), (min(i + dash_len, x2), y1), color, thickness, lineType=cv2.LINE_AA)
            cv2.line(frame, (i, y2), (min(i + dash_len, x2), y2), color, thickness, lineType=cv2.LINE_AA)
        for i in range(y1, y2, dash_len*2):
            cv2.line(frame, (x1, i), (x1, min(i + dash_len, y2)), color, thickness, lineType=cv2.LINE_AA)
            cv2.line(frame, (x2, i), (x2, min(i + dash_len, y2)), color, thickness, lineType=cv2.LINE_AA)

def draw_progress_bar(frame, progress, x, y, bar_w=300, bar_h=30, color_override=None):
    draw_rounded_rect_overlay(frame, x, y, bar_w, bar_h, (255, 255, 255), alpha=0.9, radius=15, border_color=(100,100,100), border_thickness=3)
    fill_w = int((bar_w - 6) * min(1.0, max(0.0, progress)))
    if fill_w > 0:
        color = color_override or (50, 220, 50)
        r = 12
        if fill_w >= 2*r:
            cv2.circle(frame, (x + 3 + r, y + 3 + r), r, color, -1, lineType=cv2.LINE_AA)
            cv2.circle(frame, (x + 3 + fill_w - r, y + 3 + r), r, color, -1, lineType=cv2.LINE_AA)
            cv2.rectangle(frame, (x + 3 + r, y + 3), (x + 3 + fill_w - r, y + 3 + bar_h - 6), color, -1, lineType=cv2.LINE_AA)
            cv2.rectangle(frame, (x + 3, y + 3 + r), (x + 3 + fill_w, y + 3 + bar_h - 6 - r), color, -1, lineType=cv2.LINE_AA)
        else:
            cv2.rectangle(frame, (x + 3, y + 3), (x + 3 + fill_w, y + 3 + bar_h - 6), color, -1, lineType=cv2.LINE_AA)

def draw_score_stars(frame, score, x, y, t):
    stars_to_show = min(score, 15)
    for i in range(stars_to_show):
        sx = x + i * 55
        sy = y
        star_size = 22 + int(math.sin(t * 6 + i * 0.5) * 4)
        pts = []
        for j in range(10):
            angle = math.pi / 2 + j * math.pi / 5
            r = star_size if j % 2 == 0 else star_size * 0.45
            pts.append([int(sx + r * math.cos(angle)), int(sy - r * math.sin(angle))])
        cv2.fillPoly(frame, [np.array(pts, np.int32)], (0, 230, 255), lineType=cv2.LINE_AA)
        cv2.polylines(frame, [np.array(pts, np.int32)], True, (0, 120, 255), 3, lineType=cv2.LINE_AA)

def draw_hud(frame, score, status_text, sub_text, progress, progress_color, t):
    hud_w = 800
    hud_h = 160
    hx, hy = 40, 40
    
    # Very bright, happy white HUD background
    draw_rounded_rect_overlay(frame, hx, hy, hud_w, hud_h, (250, 245, 235), 0.95, 30, border_color=(0, 150, 255), border_thickness=6)
    
    cv2.putText(frame, "STARS:", (hx + 30, hy + 50), cv2.FONT_HERSHEY_DUPLEX, 1.2, (0, 120, 255), 4, lineType=cv2.LINE_AA)
    draw_score_stars(frame, score, hx + 210, hy + 40, t)
    
    cv2.putText(frame, status_text, (hx + 30, hy + 100), cv2.FONT_HERSHEY_DUPLEX, 1.1, (200, 50, 150), 3, lineType=cv2.LINE_AA)
    if sub_text:
        cv2.putText(frame, sub_text, (hx + 30, hy + 135), cv2.FONT_HERSHEY_DUPLEX, 0.8, (100, 100, 100), 2, lineType=cv2.LINE_AA)
        
    if progress is not None:
        draw_progress_bar(frame, progress, hx + 30, hy + hud_h + 20, bar_w=hud_w - 60, bar_h=25, color_override=progress_color)

def generate_options(target_label, all_labels):
    options = [target_label]
    others = [lbl for lbl in all_labels if lbl != target_label]
    random.shuffle(others)
    options.extend(others[:3])
    random.shuffle(options)
    return options

def main():
    print("Loading YOLO model...")
    model = YOLO("yolov8n.pt")
    class_names = model.names

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Could not open webcam.")
        return
        
    # Request higher resolution from webcam if available
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    if not VOICE_AVAILABLE:
        print("pyttsx3 not installed — no spoken prompts.")

    cv2.namedWindow("Object Quest", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("Object Quest", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    cv2.setMouseCallback("Object Quest", mouse_callback)

    score = 0
    start_time = time.time()
    total_attempts = 0
    current_streak = 0
    best_streak = 0
    response_times = []
    last_frame = None
    state = STATE_IDLE

    candidate_label = None
    candidate_start = None
    target_label = None
    ask_start = None
    
    current_options = []
    
    feedback_text = ""
    feedback_sub = ""
    feedback_start = None
    
    global _clicked_point, _mouse_pos
    
    last_time = time.time()

    while True:
        success, frame = cap.read()
        if not success:
            break
        frame = cv2.flip(frame, 1)
        
        # Crop and resize to fill fullscreen exactly without distortion
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
            
        frame = cv2.resize(frame, (SCREEN_WIDTH, SCREEN_HEIGHT))
        h, w = frame.shape[:2]
        last_frame = frame

        now = time.time()
        dt = now - last_time
        last_time = now

        click = _clicked_point
        _clicked_point = None

        results = model.predict(frame, imgsz=INFERENCE_SIZE, conf=CONF_THRESHOLD, verbose=False)
        detections = results[0].boxes

        best_label, best_conf, best_box = None, 0.0, None
        detected_boxes = []

        if detections is not None:
            for box in detections:
                cls_id = int(box.cls[0])
                conf = float(box.conf[0])
                raw_label = class_names.get(cls_id, "?").lower()
                if raw_label not in TARGET_MAPPING:
                    continue
                label = TARGET_MAPPING[raw_label]
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                detected_boxes.append((label, conf, (x1, y1, x2, y2)))
                if conf > best_conf:
                    best_conf = conf
                    best_label = label
                    best_box = (x1, y1, x2, y2)

        progress = None
        progress_color = None
        status_text = ""
        sub_text = ""

        if state == STATE_IDLE:
            for label, conf, box in detected_boxes:
                draw_detection_box(frame, *box, label, conf, False, now, reveal_label=False)

            if best_label is not None:
                if best_label == candidate_label:
                    held_ms = (now - candidate_start) * 1000
                    progress = held_ms / STABLE_HOLD_MS_BEFORE_ASK
                    progress_color = (0, 200, 255) # Fun cyan
                    if held_ms >= STABLE_HOLD_MS_BEFORE_ASK:
                        target_label = candidate_label
                        state = STATE_ASKING
                        ask_start = now
                        current_options = generate_options(target_label, TARGET_OBJECTS)
                        speak_async("What is this? Click the correct option!")
                        play_appear_sound()
                else:
                    candidate_label = best_label
                    candidate_start = now
            else:
                candidate_label = None
                candidate_start = None

            status_text = "Show me a toy or object!"
            sub_text = "Hold it up to the camera..."

        elif state == STATE_ASKING:
            for label, conf, box in detected_boxes:
                draw_detection_box(frame, *box, label, conf, label == target_label, now, reveal_label=False)

            elapsed_s = now - ask_start
            progress = 1.0 - (elapsed_s / LISTEN_WINDOW_S)
            progress_color = (100, 100, 255) # Friendly redish

            btn_w, btn_h = 400, 130
            gap_x, gap_y = 60, 40
            start_x = (w - (2 * btn_w + gap_x)) // 2
            start_y = h - (2 * btn_h + gap_y) - 80
            
            button_rects = []
            for i, opt_label in enumerate(current_options):
                row = i // 2
                col = i % 2
                bx = start_x + col * (btn_w + gap_x)
                by = start_y + row * (btn_h + gap_y)
                button_rects.append((bx, by, btn_w, btn_h, opt_label))
                
                mx, my = _mouse_pos
                is_hovered = (bx <= mx <= bx + btn_w) and (by <= my <= by + btn_h)
                
                base_color, hover_color = BUTTON_COLORS[i % len(BUTTON_COLORS)]
                
                draw_button(frame, opt_label.upper(), bx, by, btn_w, btn_h, base_color, hover_color, is_hovered)

            if click:
                cx, cy = click
                clicked_option = None
                for bx, by, bw, bh, opt_label in button_rects:
                    if bx <= cx <= bx + bw and by <= cy <= by + bh:
                        clicked_option = opt_label
                        break
                
                if clicked_option:
                    total_attempts += 1
                    resp_s = now - ask_start if ask_start else 2.0
                    response_times.append(resp_s)
                    if clicked_option == target_label:
                        feedback_text = "YAY! You got it!"
                        feedback_sub = f"Awesome job, it is a {target_label}!"
                        speak_async(f"Yes! That's a {target_label}!")
                        score += 1
                        current_streak += 1
                        if current_streak > best_streak:
                            best_streak = current_streak
                        emit_confetti(w // 2, h // 2, count=120)
                        play_success_sound()
                    else:
                        current_streak = 0
                        feedback_text = "Oops! Nice try!"
                        feedback_sub = f"It was actually a {target_label}!"
                        speak_async(f"Oops! That is a {target_label}!")
                        play_wrong_sound()
                    
                    state = STATE_FEEDBACK
                    feedback_start = now

            elif elapsed_s >= LISTEN_WINDOW_S:
                feedback_text = "Time's up!"
                feedback_sub = f"This is a {target_label}."
                speak_async(f"Time's up! That's a {target_label}!")
                play_wrong_sound()
                state = STATE_FEEDBACK
                feedback_start = now

            status_text = "What is this?"
            sub_text = "Click the right answer!"

        elif state == STATE_FEEDBACK:
            for label, conf, box in detected_boxes:
                draw_detection_box(frame, *box, label, conf, label == target_label, now, reveal_label=True)

            status_text = feedback_text
            sub_text = feedback_sub

            if (now - feedback_start) * 1000 >= FEEDBACK_DISPLAY_MS:
                state = STATE_IDLE
                candidate_label = None
                candidate_start = None
                target_label = None

        update_and_draw_confetti(frame, dt)
        draw_hud(frame, score, status_text, sub_text, progress, progress_color, now)

        # Help message to exit
        cv2.putText(frame, "Press 'Q' to quit", (w - 240, 50), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 3, lineType=cv2.LINE_AA)

        cv2.imshow("Object Quest", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break

    # Show attractive Level 2 4-second quit card before closing
    if last_frame is None:
        last_frame = np.zeros((SCREEN_HEIGHT, SCREEN_WIDTH, 3), dtype=np.uint8)
    if True:
        play_duration = max(1.0, time.time() - start_time)
        accuracy_pct = int((score / max(1, total_attempts)) * 100) if total_attempts > 0 else (100 if score > 0 else 0)
        avg_resp = (sum(response_times) / len(response_times)) if response_times else 0.0

        if score >= 8 or (total_attempts >= 5 and accuracy_pct >= 80):
            rank_grade = "S"
            stars = 3
            verdict = "Sharp Visual Perception!"
        elif score >= 4 or accuracy_pct >= 60:
            rank_grade = "A"
            stars = 2
            verdict = "Great Object Recognition!"
        else:
            rank_grade = "B"
            stars = 1
            verdict = "Good Effort! Keep Questing!"

        stats = [
            {"label": "Play Time", "value": format_time(play_duration), "color": (255, 220, 0), "percent": min(1.0, play_duration / 180.0)},
            {"label": "Accuracy", "value": f"{accuracy_pct}%", "color": (100, 255, 120), "percent": accuracy_pct / 100.0},
            {"label": "Best Streak", "value": f"x{max(best_streak, 1)}", "color": (80, 180, 255), "percent": min(1.0, max(best_streak, 1) / 8.0)},
            {"label": "Avg Time", "value": f"{avg_resp:.1f}s" if avg_resp > 0 else "--", "color": (220, 80, 255), "percent": max(0.2, min(1.0, 1.0 - (avg_resp - 1.0) / 5.0))},
        ]

        show_quit_card(
            window_name="Object Quest",
            last_frame=last_frame,
            game_title="Object Quest",
            score=score,
            score_label="Objects Identified",
            stats=stats,
            stars=stars,
            verdict=verdict,
            duration_s=4.0,
            accent_color=(255, 220, 0),
            rank_grade=rank_grade,
        )

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()