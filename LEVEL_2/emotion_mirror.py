from game_card import show_quit_card, format_time
import cv2
import mediapipe as mp
import random
import time
import math
import numpy as np
try:
    import winsound
except Exception:
    winsound = None
import threading

def play_success_sound():
    if not winsound:
        return
    def sound():
        try:
            winsound.Beep(600, 150)
            winsound.Beep(800, 150)
            winsound.Beep(1200, 300)
        except Exception:
            pass
    threading.Thread(target=sound, daemon=True).start()

def play_calib_sound():
    if not winsound:
        return
    try:
        threading.Thread(target=winsound.Beep, args=(1000, 200), daemon=True).start()
    except Exception:
        pass


# Screen resolution for true fullscreen without stretching
try:
    import ctypes
    user32 = ctypes.windll.user32
    user32.SetProcessDPIAware()
    SCREEN_WIDTH = user32.GetSystemMetrics(0)
    SCREEN_HEIGHT = user32.GetSystemMetrics(1)
except Exception:
    SCREEN_WIDTH = 1280
    SCREEN_HEIGHT = 720

mp_face_mesh = mp.solutions.face_mesh

# ---------------------- Landmarks ----------------------
LEFT_MOUTH_CORNER, RIGHT_MOUTH_CORNER = 61, 291
UPPER_LIP, LOWER_LIP = 13, 14
UPPER_LIP_OUTER, LOWER_LIP_OUTER = 0, 17

LEFT_EYEBROW_INNER, LEFT_EYEBROW_MID, LEFT_EYEBROW_OUTER = 107, 105, 70
RIGHT_EYEBROW_INNER, RIGHT_EYEBROW_MID, RIGHT_EYEBROW_OUTER = 336, 334, 300

LEFT_EYE_TOP, LEFT_EYE_BOTTOM = 159, 145
RIGHT_EYE_TOP, RIGHT_EYE_BOTTOM = 386, 374
LEFT_EYE_OUTER, RIGHT_EYE_OUTER = 33, 263

CHIN_BOTTOM = 152
NOSE_TIP = 1

# ---------------------- Tunable settings ----------------------
CALIBRATION_MS = 2200
HOLD_MS_TO_WIN = 800
SUCCESS_DISPLAY_MS = 1500
MATCH_THRESHOLD = 0.38
SCORE_SMOOTHING = 0.35

EMOTIONS = ["Happy", "Sad", "Angry", "Surprised"]

# Vibrant, kid-friendly colors
EMOTION_COLORS = {
    "Happy": (0, 220, 255),      # bright yellow
    "Sad": (255, 180, 100),      # soft blue
    "Angry": (80, 80, 255),      # bright red/pink
    "Surprised": (220, 220, 50), # bright teal
}

# ---------------------- Confetti system ----------------------
class ConfettiPiece:
    __slots__ = ['x', 'y', 'vx', 'vy', 'color', 'w', 'h', 'life', 'rot', 'rot_speed']

    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.vx = random.uniform(-20, 20)
        self.vy = random.uniform(-30, -10)
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


confetti = []

def emit_confetti(x, y, count=80):
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


# ---------------------- Utilities ----------------------
def draw_rounded_rect_overlay(frame, x, y, w, h, color, alpha=0.55, radius=16, border_color=None, border_thickness=2):
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


def dist(a, b):
    return ((a.x - b.x) ** 2 + (a.y - b.y) ** 2) ** 0.5


def get_metrics(landmarks):
    face_scale = dist(landmarks[LEFT_EYE_OUTER], landmarks[RIGHT_EYE_OUTER])
    if face_scale == 0:
        face_scale = 1e-6

    mouth_width = dist(landmarks[LEFT_MOUTH_CORNER], landmarks[RIGHT_MOUTH_CORNER]) / face_scale

    inner_lip_gap = dist(landmarks[UPPER_LIP], landmarks[LOWER_LIP]) / face_scale
    outer_lip_gap = dist(landmarks[UPPER_LIP_OUTER], landmarks[LOWER_LIP_OUTER]) / face_scale
    jaw_drop = dist(landmarks[NOSE_TIP], landmarks[CHIN_BOTTOM]) / face_scale
    mouth_open = inner_lip_gap * 0.6 + outer_lip_gap * 0.25 + jaw_drop * 0.15

    lip_center_y = (landmarks[UPPER_LIP].y + landmarks[LOWER_LIP].y) / 2
    left_corner_y = landmarks[LEFT_MOUTH_CORNER].y
    right_corner_y = landmarks[RIGHT_MOUTH_CORNER].y
    avg_corner_y = (left_corner_y + right_corner_y) / 2
    mouth_corner_y = (lip_center_y - avg_corner_y) / face_scale
    mouth_corner_y_abs = avg_corner_y / face_scale

    eb_eye_L_inner = (landmarks[LEFT_EYE_TOP].y - landmarks[LEFT_EYEBROW_INNER].y) / face_scale
    eb_eye_L_mid   = (landmarks[LEFT_EYE_TOP].y - landmarks[LEFT_EYEBROW_MID].y) / face_scale
    eb_eye_L_outer = (landmarks[LEFT_EYE_TOP].y - landmarks[LEFT_EYEBROW_OUTER].y) / face_scale
    eb_eye_R_inner = (landmarks[RIGHT_EYE_TOP].y - landmarks[RIGHT_EYEBROW_INNER].y) / face_scale
    eb_eye_R_mid   = (landmarks[RIGHT_EYE_TOP].y - landmarks[RIGHT_EYEBROW_MID].y) / face_scale
    eb_eye_R_outer = (landmarks[RIGHT_EYE_TOP].y - landmarks[RIGHT_EYEBROW_OUTER].y) / face_scale
    
    eyebrow_eye_left  = eb_eye_L_inner * 0.25 + eb_eye_L_mid * 0.5 + eb_eye_L_outer * 0.25
    eyebrow_eye_right = eb_eye_R_inner * 0.25 + eb_eye_R_mid * 0.5 + eb_eye_R_outer * 0.25
    eyebrow_eye_dist = (eyebrow_eye_left + eyebrow_eye_right) / 2

    left_eye_open  = dist(landmarks[LEFT_EYE_TOP], landmarks[LEFT_EYE_BOTTOM]) / face_scale
    right_eye_open = dist(landmarks[RIGHT_EYE_TOP], landmarks[RIGHT_EYE_BOTTOM]) / face_scale
    eye_openness = (left_eye_open + right_eye_open) / 2
    inner_brow_dist = dist(landmarks[LEFT_EYEBROW_INNER], landmarks[RIGHT_EYEBROW_INNER]) / face_scale

    return {
        "mouth_width": mouth_width,
        "mouth_open": mouth_open,
        "mouth_corner_y": mouth_corner_y,
        "mouth_corner_y_abs": mouth_corner_y_abs,
        "eyebrow_eye_dist": eyebrow_eye_dist,
        "inner_brow_dist": inner_brow_dist,
        "eye_openness": eye_openness,
    }


def clip01(x):
    return max(0.0, min(1.0, x))


def score_emotion(emotion, current, baseline):
    d_width = current["mouth_width"] - baseline["mouth_width"]
    d_open = current["mouth_open"] - baseline["mouth_open"]
    d_corner = current["mouth_corner_y"] - baseline["mouth_corner_y"]
    d_eyebrow = current["eyebrow_eye_dist"] - baseline["eyebrow_eye_dist"]
    d_inner = current.get("inner_brow_dist", 0.35) - baseline.get("inner_brow_dist", 0.35)
    d_eye_open = current["eye_openness"] - baseline["eye_openness"]

    if emotion == "Happy":
        s_corner = clip01(d_corner / 0.015)
        s_width  = clip01(d_width / 0.040)
        if current["mouth_corner_y"] > 0.012 and current["mouth_width"] > 0.72:
            return max(0.88, s_corner * 0.60 + s_width * 0.40)
        if d_corner < -0.003:
            return 0.0
        return s_corner * 0.60 + s_width * 0.40

    if emotion == "Surprised":
        s_open = clip01(d_open / 0.055)
        s_brow = clip01(d_eyebrow / 0.030)
        if current["mouth_open"] > 0.095:
            return max(0.88, s_open * 0.65 + s_brow * 0.35)
        if d_open < 0.015 and current["mouth_open"] < 0.08:
            return 0.0
        return s_open * 0.65 + s_brow * 0.35

    if emotion == "Sad":
        s_corner = clip01((-d_corner) / 0.012)
        s_width  = clip01((-d_width) / 0.040 + 0.2)
        if current["mouth_corner_y"] < -0.008 and current["mouth_open"] < 0.06:
            return max(0.82, s_corner * 0.70 + s_width * 0.30)
        if d_corner > 0.002 or d_open > 0.05 or d_eyebrow < -0.012:
            return 0.0
        return s_corner * 0.70 + s_width * 0.30

    if emotion == "Angry":
        s_brow  = clip01((-d_eyebrow) / 0.020)
        s_inner = clip01((-d_inner) / 0.022)
        if current["eyebrow_eye_dist"] < 0.34 and current.get("inner_brow_dist", 0.35) < 0.33:
            return max(0.85, s_brow * 0.50 + s_inner * 0.50)
        if d_eyebrow > 0.005 or d_open > 0.05:
            return 0.0
        return s_brow * 0.50 + s_inner * 0.50

    return 0.0


def draw_target_face_icon(frame, emotion, cx, cy, r, t):
    pulse = 1.0 + 0.05 * math.sin(t * 4.0)
    r = int(r * pulse)
    emo_color = EMOTION_COLORS.get(emotion, (80, 220, 255))
    
    # Outer glow
    cv2.circle(frame, (cx, cy), r + 15, emo_color, -1, lineType=cv2.LINE_AA)
    cv2.circle(frame, (cx, cy), r + 15, (255, 255, 255), 6, lineType=cv2.LINE_AA)
    
    # Head
    cv2.circle(frame, (cx, cy), r, (150, 240, 255), -1, lineType=cv2.LINE_AA)
    cv2.circle(frame, (cx, cy), r, (0, 0, 0), 5, lineType=cv2.LINE_AA)

    # Blush cheeks
    cv2.circle(frame, (cx - int(r * 0.5), cy + int(r * 0.15)), int(r * 0.15), (180, 180, 255), -1, lineType=cv2.LINE_AA)
    cv2.circle(frame, (cx + int(r * 0.5), cy + int(r * 0.15)), int(r * 0.15), (180, 180, 255), -1, lineType=cv2.LINE_AA)

    eye_dx, eye_dy = r // 3, r // 4

    if emotion == "Happy":
        cv2.ellipse(frame, (cx - eye_dx, cy - eye_dy), (int(r*0.15), int(r*0.15)), 0, 180, 360, (40, 40, 40), max(3, r//12), lineType=cv2.LINE_AA)
        cv2.ellipse(frame, (cx + eye_dx, cy - eye_dy), (int(r*0.15), int(r*0.15)), 0, 180, 360, (40, 40, 40), max(3, r//12), lineType=cv2.LINE_AA)
        cv2.ellipse(frame, (cx, cy + eye_dy), (r // 2, r // 3), 0, 0, 180, (40, 40, 40), max(4, r//10), lineType=cv2.LINE_AA)
    
    elif emotion == "Sad":
        cv2.circle(frame, (cx - eye_dx, cy - eye_dy), int(r*0.12), (40, 40, 40), -1, lineType=cv2.LINE_AA)
        cv2.circle(frame, (cx + eye_dx, cy - eye_dy), int(r*0.12), (40, 40, 40), -1, lineType=cv2.LINE_AA)
        cv2.circle(frame, (cx - eye_dx + r//20, cy - eye_dy - r//20), int(r*0.04), (255, 255, 255), -1, lineType=cv2.LINE_AA)
        cv2.circle(frame, (cx + eye_dx + r//20, cy - eye_dy - r//20), int(r*0.04), (255, 255, 255), -1, lineType=cv2.LINE_AA)
        cv2.ellipse(frame, (cx, cy + eye_dy + int(r*0.3)), (r // 2, r // 3), 0, 180, 360, (40, 40, 40), max(4, r//10), lineType=cv2.LINE_AA)
        
        tear_y = cy - eye_dy + int(r*0.25) + int(math.sin(t * 3) * (r*0.1))
        cv2.circle(frame, (cx + eye_dx + int(r*0.1), tear_y), int(r*0.1), (255, 200, 100), -1, lineType=cv2.LINE_AA)
    
    elif emotion == "Angry":
        cv2.line(frame, (cx - eye_dx - int(r*0.2), cy - eye_dy - int(r*0.2)), (cx - eye_dx + int(r*0.15), cy - eye_dy), (40, 40, 40), max(4, r//8), lineType=cv2.LINE_AA)
        cv2.line(frame, (cx + eye_dx + int(r*0.2), cy - eye_dy - int(r*0.2)), (cx + eye_dx - int(r*0.15), cy - eye_dy), (40, 40, 40), max(4, r//8), lineType=cv2.LINE_AA)
        cv2.circle(frame, (cx - eye_dx, cy - eye_dy + int(r*0.1)), int(r*0.08), (40, 40, 40), -1, lineType=cv2.LINE_AA)
        cv2.circle(frame, (cx + eye_dx, cy - eye_dy + int(r*0.1)), int(r*0.08), (40, 40, 40), -1, lineType=cv2.LINE_AA)
        cv2.line(frame, (cx - r // 2, cy + eye_dy + int(r*0.2)), (cx + r // 2, cy + eye_dy + int(r*0.2)), (40, 40, 40), max(4, r//8), lineType=cv2.LINE_AA)
    
    elif emotion == "Surprised":
        cv2.circle(frame, (cx - eye_dx, cy - eye_dy), int(r*0.2), (40, 40, 40), max(3, r//12), lineType=cv2.LINE_AA)
        cv2.circle(frame, (cx + eye_dx, cy - eye_dy), int(r*0.2), (40, 40, 40), max(3, r//12), lineType=cv2.LINE_AA)
        cv2.circle(frame, (cx - eye_dx, cy - eye_dy), int(r*0.08), (40, 40, 40), -1, lineType=cv2.LINE_AA)
        cv2.circle(frame, (cx + eye_dx, cy - eye_dy), int(r*0.08), (40, 40, 40), -1, lineType=cv2.LINE_AA)
        cv2.line(frame, (cx - eye_dx - int(r*0.2), cy - eye_dy - int(r*0.35)), (cx - eye_dx + int(r*0.2), cy - eye_dy - int(r*0.35)), (40, 40, 40), max(4, r//10), lineType=cv2.LINE_AA)
        cv2.line(frame, (cx + eye_dx - int(r*0.2), cy - eye_dy - int(r*0.35)), (cx + eye_dx + int(r*0.2), cy - eye_dy - int(r*0.35)), (40, 40, 40), max(4, r//10), lineType=cv2.LINE_AA)
        open_size = int(r*0.25) + int(math.sin(t * 4) * (r*0.05))
        cv2.circle(frame, (cx, cy + eye_dy + int(r*0.2)), open_size, (40, 40, 40), -1, lineType=cv2.LINE_AA)


def draw_progress_bar(frame, progress, x, y, w, h, t):
    draw_rounded_rect_overlay(frame, x, y, w, h, (255, 255, 255), alpha=0.9, radius=20, border_color=(0,0,0), border_thickness=4)
    fill_w = int((w - 8) * clip01(progress))
    if fill_w > 0:
        is_matched = progress >= MATCH_THRESHOLD
        color = (0, 230, 100) if is_matched else (0, 180, 255)
        r = 16
        if fill_w >= 2*r:
            cv2.circle(frame, (x + 4 + r, y + 4 + r), r, color, -1, lineType=cv2.LINE_AA)
            cv2.circle(frame, (x + 4 + fill_w - r, y + 4 + r), r, color, -1, lineType=cv2.LINE_AA)
            cv2.rectangle(frame, (x + 4 + r, y + 4), (x + 4 + fill_w - r, y + 4 + h - 8), color, -1, lineType=cv2.LINE_AA)
            cv2.rectangle(frame, (x + 4, y + 4 + r), (x + 4 + fill_w, y + 4 + h - 8 - r), color, -1, lineType=cv2.LINE_AA)
        else:
            cv2.rectangle(frame, (x + 4, y + 4), (x + 4 + fill_w, y + 4 + h - 8), color, -1, lineType=cv2.LINE_AA)
            
    thresh_x = x + 4 + int((w - 8) * MATCH_THRESHOLD)
    cv2.line(frame, (thresh_x, y - 5), (thresh_x, y + h + 5), (50, 50, 50), 4, lineType=cv2.LINE_AA)


def draw_hud(frame, score, status_text, emotion, progress, t):
    h, w = frame.shape[:2]
    
    draw_rounded_rect_overlay(frame, 30, 30, 300, 80, (250, 245, 235), 0.95, 20, border_color=(0, 150, 255), border_thickness=5)
    cv2.putText(frame, f"SCORE: {score}", (50, 85), cv2.FONT_HERSHEY_DUPLEX, 1.2, (0, 200, 50), 4, lineType=cv2.LINE_AA)
    
    panel_w, panel_h = 450, 280
    px, py = w - panel_w - 40, 40
    draw_rounded_rect_overlay(frame, px, py, panel_w, panel_h, (250, 245, 235), 0.95, 30, border_color=(0, 150, 255), border_thickness=6)
    
    emo_color = EMOTION_COLORS.get(emotion, (0, 255, 255))
    text = f"Be {emotion.upper()}!"
    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_DUPLEX, 1.3, 4)[0]
    cv2.putText(frame, text, (px + (panel_w - text_size[0])//2, py + 60), cv2.FONT_HERSHEY_DUPLEX, 1.3, emo_color, 4, lineType=cv2.LINE_AA)
    
    draw_target_face_icon(frame, emotion, px + panel_w // 2, py + 170, 75, t)

    status_w = 700
    status_h = 160
    sx = (w - status_w) // 2
    sy = h - status_h - 40
    draw_rounded_rect_overlay(frame, sx, sy, status_w, status_h, (250, 245, 235), 0.95, 25, border_color=(0, 150, 255), border_thickness=5)
    
    text_size = cv2.getTextSize(status_text, cv2.FONT_HERSHEY_DUPLEX, 1.1, 3)[0]
    cv2.putText(frame, status_text, (sx + (status_w - text_size[0])//2, sy + 60), cv2.FONT_HERSHEY_DUPLEX, 1.1, (200, 50, 150), 3, lineType=cv2.LINE_AA)
    
    if progress is not None:
        draw_progress_bar(frame, progress, sx + 50, sy + 90, w=status_w - 100, h=40, t=t)


def spawn_emotion(previous=None):
    choices = [e for e in EMOTIONS if e != previous] or EMOTIONS
    return random.choice(choices)


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


def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Could not open webcam.")
        return
        
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    face_mesh = mp_face_mesh.FaceMesh(
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )

    cv2.namedWindow("Emotion Mirror", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("Emotion Mirror", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    success, first_frame = cap.read()
    if not success:
        print("Could not read from webcam.")
        cap.release()
        return

    # ---------------- Calibration ----------------
    user_quit = False
    start_time = time.time()
    last_frame = None
    calib_metrics = {"mouth_width": [], "mouth_open": [], "mouth_corner_y": [],
                     "mouth_corner_y_abs": [], "eyebrow_eye_dist": [], "eye_openness": []}
    calib_start = time.time()

    while (time.time() - calib_start) * 1000 < CALIBRATION_MS:
        success, frame = cap.read()
        if not success:
            break
            
        frame = cv2.flip(frame, 1)
        frame = process_frame_for_fullscreen(frame)
        last_frame = frame
        h, w = frame.shape[:2]
        
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        if results.multi_face_landmarks:
            m = get_metrics(results.multi_face_landmarks[0].landmark)
            for k in calib_metrics:
                calib_metrics[k].append(m[k])

        draw_rounded_rect_overlay(frame, w // 2 - 400, h // 2 - 120, 800, 240, (250, 245, 235), 0.95, 30, border_color=(0, 150, 255), border_thickness=6)
        
        text1 = "Let's calibrate!"
        text2 = "Make a normal, relaxed face..."
        t1_sz = cv2.getTextSize(text1, cv2.FONT_HERSHEY_DUPLEX, 1.8, 4)[0]
        t2_sz = cv2.getTextSize(text2, cv2.FONT_HERSHEY_DUPLEX, 1.2, 3)[0]
        
        cv2.putText(frame, text1, (w // 2 - t1_sz[0] // 2, h // 2 - 20), cv2.FONT_HERSHEY_DUPLEX, 1.8, (0, 150, 255), 4, lineType=cv2.LINE_AA)
        cv2.putText(frame, text2, (w // 2 - t2_sz[0] // 2, h // 2 + 40), cv2.FONT_HERSHEY_DUPLEX, 1.2, (100, 100, 100), 3, lineType=cv2.LINE_AA)
        
        calib_progress = (time.time() - calib_start) * 1000 / CALIBRATION_MS
        draw_progress_bar(frame, calib_progress, w // 2 - 300, h // 2 + 70, w=600, h=30, t=time.time())

        cv2.imshow("Emotion Mirror", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            user_quit = True
            break

    DEFAULT_BASELINE = {
        "mouth_width": 0.72,
        "mouth_open": 0.05,
        "mouth_corner_y": 0.0,
        "mouth_corner_y_abs": 0.75,
        "eyebrow_eye_dist": 0.38,
        "inner_brow_dist": 0.35,
        "eye_openness": 0.18,
    }
    baseline = {}
    for k, vals in calib_metrics.items():
        baseline[k] = (sum(vals) / len(vals)) if vals else DEFAULT_BASELINE.get(k, 0.0)
    play_calib_sound()

    # ---------------- Game loop ----------------
    score = 0
    match_history = []
    emotion = spawn_emotion()
    hold_start = None
    won_at = None
    last_time = time.time()
    match_score = 0.0

    while not user_quit:
        success, frame = cap.read()
        if not success:
            break

        now = time.time()
        dt = now - last_time
        last_time = now

        frame = cv2.flip(frame, 1)
        frame = process_frame_for_fullscreen(frame)
        last_frame = frame
        h, w = frame.shape[:2]

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = face_mesh.process(rgb)

        match_score_raw = 0.0
        status = f"Try to look {emotion.upper()}!"

        if results.multi_face_landmarks:
            current = get_metrics(results.multi_face_landmarks[0].landmark)

            if won_at is None:
                match_score_raw = score_emotion(emotion, current, baseline)
                match_score = match_score * SCORE_SMOOTHING + match_score_raw * (1.0 - SCORE_SMOOTHING)

                if match_score >= MATCH_THRESHOLD:
                    match_history.append(match_score)
                    if hold_start is None:
                        hold_start = time.time()
                    held_ms = (time.time() - hold_start) * 1000
                    if held_ms >= HOLD_MS_TO_WIN:
                        won_at = time.time()
                        score += 1
                        emit_confetti(w // 2, h // 2, count=120)
                        play_success_sound()
                else:
                    hold_start = None
        else:
            status = "I can't see your face! :("

        if won_at is not None:
            elapsed_ms = (now - won_at) * 1000
            if elapsed_ms < SUCCESS_DISPLAY_MS:
                bounce = 1.8 + 0.3 * math.sin(elapsed_ms / 100)
                text = "FANTASTIC!"
                text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_DUPLEX, bounce, 6)[0]
                tx = w // 2 - text_size[0] // 2
                ty = h // 2
                cv2.putText(frame, text, (tx+6, ty+6), cv2.FONT_HERSHEY_DUPLEX, bounce, (0, 0, 0), 6, lineType=cv2.LINE_AA)
                cv2.putText(frame, text, (tx, ty), cv2.FONT_HERSHEY_DUPLEX, bounce, (0, 255, 0), 6, lineType=cv2.LINE_AA)
                status = "Awesome!"
            else:
                emotion = spawn_emotion(previous=emotion)
                won_at = None
                hold_start = None
                match_score = 0.0
                status = f"Can you look {emotion.upper()}?"

        update_and_draw_confetti(frame, dt)
        draw_hud(frame, score, status, emotion, match_score, now)
        
        cv2.putText(frame, "Press 'Q' to quit", (w - 240, 50), cv2.FONT_HERSHEY_DUPLEX, 0.8, (255, 255, 255), 3, lineType=cv2.LINE_AA)

        cv2.imshow("Emotion Mirror", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Show attractive Level 2 4-second quit card before closing
    if last_frame is None and first_frame is not None:
        last_frame = process_frame_for_fullscreen(cv2.flip(first_frame, 1))
    if last_frame is None:
        last_frame = np.zeros((SCREEN_HEIGHT, SCREEN_WIDTH, 3), dtype=np.uint8)

    if True:
        play_duration = max(1.0, time.time() - start_time)
        pace = (score / play_duration) * 60.0
        avg_acc = int(np.mean(match_history) * 100) if match_history else (85 if score > 0 else 0)

        if score >= 8 or pace >= 6.0:
            rank_grade = "S"
            stars = 3
            verdict = "Master of Facial Expression!"
        elif score >= 4 or pace >= 3.0:
            rank_grade = "A"
            stars = 2
            verdict = "Great Emotional Mimicry!"
        else:
            rank_grade = "B"
            stars = 1
            verdict = "Keep Practicing Expressions!"

        stats = [
            {"label": "Play Time", "value": format_time(play_duration), "color": (255, 220, 0), "percent": min(1.0, play_duration / 180.0)},
            {"label": "Match Accuracy", "value": f"{avg_acc}%", "color": (100, 255, 120), "percent": avg_acc / 100.0},
            {"label": "Pace", "value": f"{pace:.1f} / min", "color": (80, 180, 255), "percent": min(1.0, pace / 10.0)},
            {"label": "Expression Focus", "value": "Superb" if stars == 3 else ("Steady" if stars == 2 else "Active"), "color": (220, 80, 255), "percent": 0.90},
        ]

        show_quit_card(
            window_name="Emotion Mirror",
            last_frame=last_frame,
            game_title="Emotion Mirror",
            score=score,
            score_label="Emotions Matched",
            stats=stats,
            stars=stars,
            verdict=verdict,
            duration_s=4.0,
            accent_color=(100, 255, 120),
            rank_grade=rank_grade,
        )

    cap.release()
    face_mesh.close()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
