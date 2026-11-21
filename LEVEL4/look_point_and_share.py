from game_card import show_quit_card, format_time
# point_the_animal_standalone.py
# Standalone desktop game. Run directly — no React, no server, no WebSocket.
#
# POINT THE ANIMAL — simple, text-only (no voice). The live webcam feed fills the
# whole screen. Three animals (dog, cat, rabbit) sit in a row along the TOP of the
# screen. A question asks the child to point to one — the first question is always
# "Point to the dog!" — and the child points directly at it with their finger,
# since it's right there on their own live video.
#
# Install:  pip install opencv-python mediapipe
# Run:      python point_the_animal_standalone.py
# Quit:     press 'q' in the window

import cv2
import mediapipe as mp
import numpy as np
import random
import time
import math
import winsound
import threading

def play_success_sound():
    def sound():
        try:
            if winsound:
                winsound.Beep(600, 120)
                winsound.Beep(800, 120)
                winsound.Beep(1200, 240)
        except Exception:
            pass
    threading.Thread(target=sound, daemon=True).start()

def play_wrong_sound():
    def sound():
        try:
            if winsound:
                winsound.Beep(320, 250)
        except Exception:
            pass
    threading.Thread(target=sound, daemon=True).start()

def play_hover_sound():
    def sound():
        try:
            if winsound:
                winsound.Beep(520, 80)
        except Exception:
            pass
    threading.Thread(target=sound, daemon=True).start()

mp_hands = mp.solutions.hands
mp_drawing = mp.solutions.drawing_utils
mp_styles = mp.solutions.drawing_styles

INDEX_TIP = 8

CANVAS_W, CANVAS_H = 1280, 720

# ---------------------- Tunable settings ----------------------
ICON_RADIUS = 55
ICON_Y = 130                  # how far down from the top the animals sit
HOLD_MS_TO_LOCK = 800         # how long the fingertip must stay on the animal
FEEDBACK_DISPLAY_MS = 1200


# ==================== Animal icons (simple drawn shapes, no copyrighted art) ====================

def draw_dog(canvas, cx, cy, s):
    cv2.ellipse(canvas, (cx - s // 2, cy - s // 4), (s // 3, s // 2), -20, 0, 360, (60, 110, 160), -1)
    cv2.ellipse(canvas, (cx + s // 2, cy - s // 4), (s // 3, s // 2), 20, 0, 360, (60, 110, 160), -1)
    cv2.circle(canvas, (cx, cy), s, (70, 130, 190), -1)
    cv2.circle(canvas, (cx, cy + s // 3), s // 3, (90, 150, 210), -1)
    cv2.circle(canvas, (cx - s // 3, cy - s // 5), 5, (30, 30, 30), -1)
    cv2.circle(canvas, (cx + s // 3, cy - s // 5), 5, (30, 30, 30), -1)
    cv2.circle(canvas, (cx, cy + s // 4), 6, (30, 30, 30), -1)


def draw_cat(canvas, cx, cy, s):
    tri_h = s // 2
    cv2.fillPoly(canvas, [np.array([[cx - s, cy - s // 2], [cx - s // 2, cy - s - tri_h // 2],
                                     [cx - s // 3, cy - s // 2]], np.int32)], (90, 140, 210))
    cv2.fillPoly(canvas, [np.array([[cx + s, cy - s // 2], [cx + s // 2, cy - s - tri_h // 2],
                                     [cx + s // 3, cy - s // 2]], np.int32)], (90, 140, 210))
    cv2.circle(canvas, (cx, cy), s, (110, 160, 230), -1)
    for dx in (-1, 1):
        for i in range(-1, 2):
            y = cy + i * 8
            cv2.line(canvas, (cx + dx * 15, y), (cx + dx * (s - 5), y + dx * i * 3), (60, 60, 60), 1)
    cv2.circle(canvas, (cx - s // 3, cy - s // 6), 5, (30, 30, 30), -1)
    cv2.circle(canvas, (cx + s // 3, cy - s // 6), 5, (30, 30, 30), -1)
    cv2.circle(canvas, (cx, cy + s // 8), 5, (60, 60, 150), -1)


def draw_rabbit(canvas, cx, cy, s):
    cv2.ellipse(canvas, (cx - s // 3, cy - s - s // 3), (s // 4, s), 0, 0, 360, (225, 225, 235), -1)
    cv2.ellipse(canvas, (cx + s // 3, cy - s - s // 3), (s // 4, s), 0, 0, 360, (225, 225, 235), -1)
    cv2.ellipse(canvas, (cx - s // 3, cy - s - s // 3), (s // 7, s - 10), 0, 0, 360, (255, 200, 220), -1)
    cv2.ellipse(canvas, (cx + s // 3, cy - s - s // 3), (s // 7, s - 10), 0, 0, 360, (255, 200, 220), -1)
    cv2.circle(canvas, (cx, cy), s, (235, 235, 245), -1)
    cv2.circle(canvas, (cx - s // 3, cy - s // 6), 5, (30, 30, 30), -1)
    cv2.circle(canvas, (cx + s // 3, cy - s // 6), 5, (30, 30, 30), -1)
    cv2.circle(canvas, (cx, cy + s // 6), 4, (255, 150, 170), -1)


def draw_pig(canvas, cx, cy, s):
    # Pink body
    cv2.circle(canvas, (cx, cy), s, (180, 175, 255), -1)
    # Snout
    cv2.ellipse(canvas, (cx, cy + s//6), (s//3, s//4), 0, 0, 360, (130, 100, 255), -1)
    # Nostrils
    cv2.circle(canvas, (cx - s//8, cy + s//6), 4, (80, 50, 180), -1)
    cv2.circle(canvas, (cx + s//8, cy + s//6), 4, (80, 50, 180), -1)
    # Eyes
    cv2.circle(canvas, (cx - s//3, cy - s//4), 5, (30, 30, 30), -1)
    cv2.circle(canvas, (cx + s//3, cy - s//4), 5, (30, 30, 30), -1)
    # Ears
    cv2.fillPoly(canvas, [np.array([[cx - s//2, cy - s//2 - 5], [cx - s, cy - s + 10], [cx - s + 10, cy - s//2]], np.int32)], (180, 175, 255))
    cv2.fillPoly(canvas, [np.array([[cx + s//2, cy - s//2 - 5], [cx + s, cy - s + 10], [cx + s - 10, cy - s//2]], np.int32)], (180, 175, 255))


ANIMALS = [
    {"id": "dog", "label": "Dog", "draw": draw_dog},
    {"id": "cat", "label": "Cat", "draw": draw_cat},
    {"id": "rabbit", "label": "Rabbit", "draw": draw_rabbit},
    {"id": "pig", "label": "Pig", "draw": draw_pig},
]
ANIMALS_BY_ID = {a["id"]: a for a in ANIMALS}


# ==================== Layout ====================

def layout_animals():
    n = len(ANIMALS)
    margin = 160
    usable = CANVAS_W - margin * 2
    placed = []
    for i, animal in enumerate(ANIMALS):
        x = margin + int(usable * (i + 0.5) / n)
        placed.append({"animal": animal, "x": x, "y": ICON_Y})
    return placed


def spawn_target(previous_id=None, first_round=False):
    if first_round:
        return ANIMALS_BY_ID["dog"]
    choices = [a for a in ANIMALS if a["id"] != previous_id]
    return random.choice(choices)


# ==================== Drawing ====================

def draw_card(canvas, x, y, is_target, is_correct_flash):
    r = ICON_RADIUS + 24
    overlay = canvas.copy()
    cv2.circle(overlay, (x + 6, y + 6), r, (40, 40, 40), -1)
    cv2.circle(overlay, (x, y), r, (255, 250, 245), -1)
    cv2.addWeighted(overlay, 0.8, canvas, 0.2, 0, canvas)

    # Only show feedback on locked-in answer (no yellow hint circle on target)
    if is_correct_flash is True:
        cv2.circle(canvas, (x, y), r + 10, (100, 255, 100), 8)
        cv2.circle(canvas, (x, y), r + 10, (0, 200, 0), 3)
    elif is_correct_flash is False:
        cv2.circle(canvas, (x, y), r + 10, (0, 100, 255), 8)
        cv2.circle(canvas, (x, y), r + 10, (0, 50, 255), 3)


def draw_progress_ring(canvas, x, y, progress):
    if progress <= 0:
        return
    angle = int(360 * progress)
    cv2.ellipse(canvas, (x, y), (ICON_RADIUS + 34, ICON_RADIUS + 34), -90, 0, angle, (0, 255, 255), 10)
    cv2.ellipse(canvas, (x, y), (ICON_RADIUS + 34, ICON_RADIUS + 34), -90, 0, angle, (0, 180, 255), 4)


def draw_instruction(canvas, text, locked_correct=None):
    size = cv2.getTextSize(text, cv2.FONT_HERSHEY_DUPLEX, 1.1, 2)[0]
    cx = CANVAS_W // 2
    pad_x = 32
    badge_w = size[0] + pad_x * 2
    bx1 = max(40, cx - badge_w // 2)
    bx2 = min(CANVAS_W - 40, cx + badge_w // 2)
    by1, by2 = 250, 310

    overlay = canvas.copy()
    cv2.rectangle(overlay, (bx1, by1), (bx2, by2), (18, 20, 32), -1)
    cv2.addWeighted(overlay, 0.85, canvas, 0.15, 0, canvas)

    badge_border = (80, 240, 120) if (locked_correct is True) else (
        (80, 80, 240) if (locked_correct is False) else (0, 210, 255)
    )
    cv2.rectangle(canvas, (bx1, by1), (bx2, by2), badge_border, 2, cv2.LINE_AA)

    txt_col = (120, 255, 140) if (locked_correct is True) else (
        (140, 140, 255) if (locked_correct is False) else (0, 255, 255)
    )
    tx = cx - size[0] // 2
    ty = by1 + 42
    cv2.putText(canvas, text, (tx, ty), cv2.FONT_HERSHEY_DUPLEX, 1.1, (0, 0, 0), 6, cv2.LINE_AA)
    cv2.putText(canvas, text, (tx, ty), cv2.FONT_HERSHEY_DUPLEX, 1.1, txt_col, 2, cv2.LINE_AA)


def draw_score(canvas, score, total):
    overlay = canvas.copy()
    cv2.rectangle(overlay, (20, 20), (280, 80), (0, 0, 0), -1)
    cv2.rectangle(overlay, (20, 20), (280, 80), (0, 210, 255), 3)
    cv2.addWeighted(overlay, 0.6, canvas, 0.4, 0, canvas)
    text = f"SCORE: {score}/{total}"
    cv2.putText(canvas, text, (40, 62), cv2.FONT_HERSHEY_DUPLEX, 0.9, (0, 0, 0), 6)
    cv2.putText(canvas, text, (40, 62), cv2.FONT_HERSHEY_DUPLEX, 0.9, (0, 210, 255), 2)


# ==================== Main ====================

def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Could not open webcam.")
        return

    hands = mp_hands.Hands(
        max_num_hands=1,
        model_complexity=0,
        min_detection_confidence=0.45,
        min_tracking_confidence=0.45,
    )

    placed = layout_animals()
    target = spawn_target(first_round=True)
    score, total_rounds = 0, 0
    start_time = time.time()
    last_canvas = None
    smooth_finger = None

    hold_id, hold_start = None, None
    locked_id, locked_at, locked_correct = None, None, None

    cv2.namedWindow("Point the Animal", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("Point the Animal", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    # Touch / Mouse click support
    def on_mouse(event, mx, my, flags, param):
        nonlocal locked_id, locked_at, locked_correct, total_rounds, score
        if event == cv2.EVENT_LBUTTONDOWN and locked_id is None:
            for p in placed:
                dx, dy = mx - p["x"], my - p["y"]
                if math.hypot(dx, dy) <= ICON_RADIUS + 24:
                    locked_id = p["animal"]["id"]
                    locked_correct = (locked_id == target["id"])
                    locked_at = time.time()
                    total_rounds += 1
                    if locked_correct:
                        score += 1
                        play_success_sound()
                    else:
                        play_wrong_sound()
                    break

    cv2.setMouseCallback("Point the Animal", on_mouse)

    while True:
        success, frame = cap.read()
        if not success:
            break
        frame = cv2.flip(frame, 1)
        canvas = cv2.resize(frame, (CANVAS_W, CANVAS_H))
        last_canvas = canvas

        rgb = cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)
        small = cv2.resize(rgb, (0, 0), fx=0.5, fy=0.5, interpolation=cv2.INTER_LINEAR)
        small.flags.writeable = False
        results = hands.process(small)

        finger_px = None
        if results.multi_hand_landmarks:
            for hand_lms in results.multi_hand_landmarks:
                mp_drawing.draw_landmarks(
                    canvas,
                    hand_lms,
                    mp_hands.HAND_CONNECTIONS,
                    mp_styles.get_default_hand_landmarks_style(),
                    mp_styles.get_default_hand_connections_style(),
                )
            lm = results.multi_hand_landmarks[0].landmark[INDEX_TIP]
            raw_x, raw_y = lm.x * CANVAS_W, lm.y * CANVAS_H
            if smooth_finger is None:
                smooth_finger = (raw_x, raw_y)
            else:
                smooth_finger = (0.65 * raw_x + 0.35 * smooth_finger[0], 0.65 * raw_y + 0.35 * smooth_finger[1])
            finger_px = (int(smooth_finger[0]), int(smooth_finger[1]))
        else:
            smooth_finger = None

        hovered_id = None
        if finger_px:
            for p in placed:
                dx, dy = finger_px[0] - p["x"], finger_px[1] - p["y"]
                if math.hypot(dx, dy) <= ICON_RADIUS + 30:
                    hovered_id = p["animal"]["id"]
                    break

        progress = 0.0
        instruction = f"Point to the {target['label']}!"

        if locked_id is None:
            if hovered_id is not None:
                if hovered_id == hold_id:
                    held_ms = (time.time() - hold_start) * 1000
                    progress = min(1.0, held_ms / HOLD_MS_TO_LOCK)
                    if held_ms >= HOLD_MS_TO_LOCK:
                        locked_id = hovered_id
                        locked_correct = (locked_id == target["id"])
                        locked_at = time.time()
                        total_rounds += 1
                        if locked_correct:
                            score += 1
                            play_success_sound()
                        else:
                            play_wrong_sound()
                else:
                    hold_id, hold_start = hovered_id, time.time()
                    play_hover_sound()
            else:
                hold_id, hold_start = None, None
        else:
            instruction = "Correct!" if locked_correct else f"That was the {ANIMALS_BY_ID[locked_id]['label']}"
            if (time.time() - locked_at) * 1000 >= FEEDBACK_DISPLAY_MS:
                target = spawn_target(previous_id=target["id"])
                locked_id, locked_at, locked_correct = None, None, None
                hold_id, hold_start = None, None

        for p in placed:
            is_target = (p["animal"]["id"] == target["id"]) and locked_id is None
            flash = locked_correct if (locked_id == p["animal"]["id"]) else None
            draw_card(canvas, p["x"], p["y"], is_target, flash)
            p["animal"]["draw"](canvas, p["x"], p["y"], ICON_RADIUS)
            if p["animal"]["id"] == hold_id and locked_id is None:
                draw_progress_ring(canvas, p["x"], p["y"], progress)

            # Label Pill - clean neutral border (no yellow hint on target)
            lbl = p["animal"]["label"]
            ts = cv2.getTextSize(lbl, cv2.FONT_HERSHEY_DUPLEX, 0.85, 2)[0]
            pill_y = p["y"] + ICON_RADIUS + 38
            cv2.rectangle(canvas, (p["x"] - ts[0]//2 - 12, pill_y - 20), (p["x"] + ts[0]//2 + 12, pill_y + 10), (20, 20, 30), -1)
            border_c = (100, 255, 100) if (flash is True) else ((0, 100, 255) if (flash is False) else (180, 180, 200))
            cv2.rectangle(canvas, (p["x"] - ts[0]//2 - 12, pill_y - 20), (p["x"] + ts[0]//2 + 12, pill_y + 10), border_c, 2)
            cv2.putText(canvas, lbl, (p["x"] - ts[0]//2, pill_y + 3), cv2.FONT_HERSHEY_DUPLEX, 0.85, (255, 255, 255), 2)

        if finger_px:
            cv2.circle(canvas, finger_px, 18, (0, 150, 255), -1)
            cv2.circle(canvas, finger_px, 12, (0, 210, 255), -1)
            cv2.circle(canvas, finger_px, 6, (255, 255, 255), -1)

        draw_score(canvas, score, total_rounds)
        draw_instruction(canvas, instruction, locked_correct)

        cv2.imshow("Point the Animal", canvas)
        key = cv2.waitKey(1) & 0xFF
        if key in (ord('q'), ord('Q'), 27):
            break
        # Also quit if window is closed via X
        try:
            if cv2.getWindowProperty("Point the Animal", cv2.WND_PROP_VISIBLE) < 1:
                break
        except Exception:
            pass

    # Show attractive Level 4 4-second quit card before closing
    if last_canvas is None:
        last_canvas = np.zeros((CANVAS_H, CANVAS_W, 3), dtype=np.uint8)

    play_duration = max(1.0, time.time() - start_time)
    accuracy_pct = int((score / max(1, total_rounds)) * 100) if total_rounds > 0 else (100 if score > 0 else 0)
    rate = (score / play_duration) * 60.0

    if score >= 8 or accuracy_pct >= 85:
        tier_badge = "GRANDMASTER"
        stars = 3
        verdict = "Sharp Joint Attention!"
    elif score >= 4 or accuracy_pct >= 60:
        tier_badge = "MASTER"
        stars = 2
        verdict = "Great Pointing & Focus!"
    else:
        tier_badge = "EXPERT"
        stars = 1
        verdict = "Good Effort! Keep Pointing!"

    stats = [
        {"label": "Play Time", "value": format_time(play_duration), "color": (30, 215, 255), "percent": min(1.0, play_duration / 180.0)},
        {"label": "Accuracy", "value": f"{accuracy_pct}%", "color": (100, 255, 140), "percent": accuracy_pct / 100.0},
        {"label": "Animals Found", "value": f"{score} / {total_rounds}", "color": (255, 220, 80), "percent": min(1.0, score / 12.0)},
        {"label": "Share Rate", "value": f"{rate:.1f} / min", "color": (120, 100, 255), "percent": min(1.0, rate / 10.0)},
    ]

    show_quit_card(
        window_name="Point the Animal",
        last_frame=last_canvas,
        game_title="Point the Animal",
        score=score,
        score_label="Animals Identified",
        stats=stats,
        stars=stars,
        verdict=verdict,
        duration_s=4.0,
        accent_color=(30, 215, 255),
        tier_badge=tier_badge,
    )

    cap.release()
    hands.close()
    cv2.destroyAllWindows()
    print(f"\nFinal score: {score}/{total_rounds}\n")


if __name__ == "__main__":
    main()