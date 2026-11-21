"""
game_card.py (LEVEL 4 EDITION - Royal Cosmic & Solar Gold Apex Style)
---------------------------------------------------------------------
Reusable, visually stunning game card displayed upon quitting for Level 4:
- Copy My Move (copymymove.py)
- Look, Point and Share / Point the Animal (look_point_and_share.py)
- My Turn / Your Turn (my_turn_your_turn.py)

Displays score, grandmaster tier badge, solar arc gauge, and 4 telemetry cards
for exactly 4 seconds with smooth animations, fanfare, and auto-close.
"""

import cv2
import numpy as np
import time
import math
import random
import threading

try:
    import winsound
except ImportError:
    winsound = None


# ---------------------- Sound Effect ----------------------
def play_quit_fanfare():
    """Plays a regal 4-tone victory fanfare in a background thread."""
    if winsound is None:
        return

    def _play():
        try:
            # Regal fanfare: G4 -> C5 -> E5 -> G5
            notes = [(392, 90), (523, 90), (659, 100), (784, 240)]
            for freq, dur in notes:
                winsound.Beep(freq, dur)
        except Exception:
            pass

    threading.Thread(target=_play, daemon=True).start()


# ---------------------- Time Formatter ----------------------
def format_time(seconds):
    """Formats seconds into MM:SS."""
    seconds = max(0, int(seconds))
    m = seconds // 60
    s = seconds % 60
    return f"{m:02d}:{s:02d}"


# ---------------------- Drawing Utilities ----------------------
def draw_rounded_rect(img, x1, y1, x2, y2, color, radius=18, thickness=-1, border_color=None, border_thickness=1):
    """Draws a rounded rectangle with smooth corners and optional border."""
    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
    w = x2 - x1
    h = y2 - y1
    radius = max(2, min(radius, w // 2, h // 2))

    if thickness == -1:
        cv2.rectangle(img, (x1 + radius, y1), (x2 - radius, y2), color, -1)
        cv2.rectangle(img, (x1, y1 + radius), (x2, y2 - radius), color, -1)
        cv2.circle(img, (x1 + radius, y1 + radius), radius, color, -1, cv2.LINE_AA)
        cv2.circle(img, (x2 - radius, y1 + radius), radius, color, -1, cv2.LINE_AA)
        cv2.circle(img, (x1 + radius, y2 - radius), radius, color, -1, cv2.LINE_AA)
        cv2.circle(img, (x2 - radius, y2 - radius), radius, color, -1, cv2.LINE_AA)

    if border_color is not None and border_thickness > 0:
        bt = border_thickness
        cv2.line(img, (x1 + radius, y1), (x2 - radius, y1), border_color, bt, cv2.LINE_AA)
        cv2.line(img, (x1 + radius, y2), (x2 - radius, y2), border_color, bt, cv2.LINE_AA)
        cv2.line(img, (x1, y1 + radius), (x1, y2 - radius), border_color, bt, cv2.LINE_AA)
        cv2.line(img, (x2, y1 + radius), (x2, y2 - radius), border_color, bt, cv2.LINE_AA)

        cv2.ellipse(img, (x1 + radius, y1 + radius), (radius, radius), 180, 0, 90, border_color, bt, cv2.LINE_AA)
        cv2.ellipse(img, (x2 - radius, y1 + radius), (radius, radius), 270, 0, 90, border_color, bt, cv2.LINE_AA)
        cv2.ellipse(img, (x2 - radius, y2 - radius), (radius, radius), 0, 0, 90, border_color, bt, cv2.LINE_AA)
        cv2.ellipse(img, (x1 + radius, y2 - radius), (radius, radius), 90, 0, 90, border_color, bt, cv2.LINE_AA)


def draw_crown_icon(img, cx, cy, size=22, color=(30, 215, 255)):
    """Draws a vector royal crown icon at (cx, cy)."""
    cx, cy = int(cx), int(cy)
    s = size / 22.0

    base_w = int(18 * s)
    base_h = int(5 * s)
    # Crown base
    cv2.rectangle(img, (cx - base_w // 2, cy + int(4 * s)), (cx + base_w // 2, cy + int(4 * s) + base_h), color, -1)

    # 3 Crown Peaks
    pts = [
        (cx - base_w // 2, cy + int(4 * s)),
        (cx - base_w // 2, cy - int(8 * s)),  # Left peak
        (cx - int(4 * s), cy),               # Left dip
        (cx, cy - int(12 * s)),              # Center high peak
        (cx + int(4 * s), cy),               # Right dip
        (cx + base_w // 2, cy - int(8 * s)), # Right peak
        (cx + base_w // 2, cy + int(4 * s)),
    ]
    cv2.fillPoly(img, [np.array(pts, dtype=np.int32)], color, cv2.LINE_AA)
    cv2.polylines(img, [np.array(pts, dtype=np.int32)], True, (255, 255, 255), 1, cv2.LINE_AA)

    # Jewels on top of peaks
    cv2.circle(img, (cx - base_w // 2, cy - int(8 * s)), max(1, int(2 * s)), (255, 255, 255), -1, cv2.LINE_AA)
    cv2.circle(img, (cx, cy - int(12 * s)), max(1, int(2.5 * s)), (255, 255, 255), -1, cv2.LINE_AA)
    cv2.circle(img, (cx + base_w // 2, cy - int(8 * s)), max(1, int(2 * s)), (255, 255, 255), -1, cv2.LINE_AA)


def draw_star(img, cx, cy, r_outer, r_inner, color, fill=True, rot_angle=0.0):
    """Draws a crisp 5-pointed solar star polygon centered at (cx, cy)."""
    cx, cy = int(cx), int(cy)
    pts = []
    for i in range(10):
        angle = rot_angle + i * math.pi / 5.0 - math.pi / 2.0
        r = r_outer if i % 2 == 0 else r_inner
        x = cx + r * math.cos(angle)
        y = cy + r * math.sin(angle)
        pts.append((int(x), int(y)))
    pts = np.array([pts], dtype=np.int32)
    if fill:
        cv2.fillPoly(img, pts, color, lineType=cv2.LINE_AA)
    cv2.polylines(img, pts, True, (255, 255, 255), 1, lineType=cv2.LINE_AA)


def draw_jewel(img, cx, cy, size, color):
    """Draws a glowing hexagonal jewel marker."""
    s = int(size)
    pts = []
    for i in range(6):
        a = i * math.pi / 3.0
        pts.append((int(cx + s * math.cos(a)), int(cy + s * math.sin(a))))
    cv2.fillPoly(img, [np.array(pts, dtype=np.int32)], color, lineType=cv2.LINE_AA)
    cv2.polylines(img, [np.array(pts, dtype=np.int32)], True, (255, 255, 255), 1, lineType=cv2.LINE_AA)


def put_centered_text(img, text, cx, y, font, scale, color, thickness=2, shadow_color=None):
    """Draws centered text horizontally with optional drop shadow."""
    (tw, th), _ = cv2.getTextSize(text, font, scale, thickness)
    tx = int(cx - tw // 2)
    ty = int(y + th // 2)
    if shadow_color is not None:
        cv2.putText(img, text, (tx + 2, ty + 2), font, scale, shadow_color, thickness + 1, cv2.LINE_AA)
    cv2.putText(img, text, (tx, ty), font, scale, color, thickness, cv2.LINE_AA)
    return tw, th


# ---------------------- Floating Cosmic Particles ----------------------
class CosmicParticle:
    __slots__ = ['x', 'y', 'vx', 'vy', 'color', 'size', 'alpha', 'type', 'rot', 'rot_speed']

    def __init__(self, w, h):
        self.x = random.uniform(0, w)
        self.y = random.uniform(0, h)
        self.vx = random.uniform(-0.8, 0.8)
        self.vy = random.uniform(-1.5, -0.3)
        self.color = random.choice([
            (30, 215, 255),   # Solar Gold
            (120, 100, 255),  # Rose Amethyst
            (255, 220, 80),   # Radiant Cyan
            (100, 255, 140),  # Emerald Aurora
            (255, 255, 255),  # Diamond
        ])
        self.size = random.uniform(3, 8)
        self.alpha = random.uniform(0.4, 0.95)
        self.type = random.choice(['star', 'circle', 'jewel'])
        self.rot = random.uniform(0, 360)
        self.rot_speed = random.uniform(-2.5, 2.5)

    def update(self, w, h):
        self.x += self.vx
        self.y += self.vy
        self.rot += self.rot_speed
        if self.y < -20:
            self.y = h + 10
            self.x = random.uniform(0, w)
        if self.x < -20:
            self.x = w + 10
        elif self.x > w + 20:
            self.x = -10

    def draw(self, img):
        cx, cy = int(self.x), int(self.y)
        c = tuple(int(ch * self.alpha) for ch in self.color)
        if self.type == 'star':
            draw_star(img, cx, cy, int(self.size), int(self.size * 0.45), c, fill=True, rot_angle=self.rot)
        elif self.type == 'jewel':
            draw_jewel(img, cx, cy, int(self.size * 0.9), c)
        else:
            cv2.circle(img, (cx, cy), int(self.size), c, -1, cv2.LINE_AA)


class CosmicParticleField:
    def __init__(self, count=50, w=1280, h=720):
        self.w = w
        self.h = h
        self.particles = [CosmicParticle(w, h) for _ in range(count)]

    def update_and_draw(self, img):
        h, w = img.shape[:2]
        for p in self.particles:
            p.update(w, h)
            p.draw(img)


# ---------------------- Level 4 Card Frame Renderer ----------------------
def render_quit_card_frame(
    base_frame,
    elapsed,
    duration_s,
    game_title,
    score,
    score_label,
    stats,
    stars=3,
    verdict="GRANDMASTER PERFORMANCE!",
    particles=None,
    accent_color=(30, 215, 255),  # Solar Gold default for Level 4
    tier_badge="GRANDMASTER",
):
    """
    Renders Level 4 Royal Cosmic & Solar Gold Apex Card.
    Features:
    - Large screen-filling dimensions (86% width x 88% height)
    - Royal Amethyst glassmorphic background
    - Solar Crown badge & Level 4 Reciprocity Mastery banner
    - Left Hero Pod: Solar Arc Ring, Big Score, Grandmaster Tier Pill, 3 Solar Stars
    - Right Telemetry Stack: 4 widescreen data cards with dual-tone progress meters
    - Real-time animated 4-second gold countdown bar
    """
    h, w = base_frame.shape[:2]
    canvas = base_frame.copy()

    # Step 1: Cinematic Frosted Royal Amethyst Background
    small = cv2.resize(canvas, (max(16, w // 8), max(16, h // 8)), interpolation=cv2.INTER_LINEAR)
    small_blur = cv2.GaussianBlur(small, (21, 21), 0)
    frosted = cv2.resize(small_blur, (w, h), interpolation=cv2.INTER_LINEAR)

    # Royal Amethyst Dark Overlay (B=48, G=20, R=36)
    amethyst_overlay = np.full((h, w, 3), (48, 20, 36), dtype=np.uint8)
    canvas = cv2.addWeighted(frosted, 0.28, amethyst_overlay, 0.72, 0)

    # Step 2: Animated Cosmic Particles
    if particles is not None:
        particles.update_and_draw(canvas)

    # Step 3: Resolution Scaling & Entrance Animation
    entrance_t = min(1.0, elapsed / 0.35)
    zoom = 0.90 + 0.10 * (1.0 - (1.0 - entrance_t) ** 3)
    card_alpha = min(1.0, elapsed / 0.22)

    sf = min(w / 1280.0, h / 720.0)
    sf = max(0.85, min(2.5, sf))

    # Prominent Widescreen Dimensions: 86% width x 88% height
    card_w = int(w * 0.86 * zoom)
    card_h = int(h * 0.88 * zoom)

    cx, cy = w // 2, h // 2
    x1 = cx - card_w // 2
    y1 = cy - card_h // 2
    x2 = cx + card_w // 2
    y2 = cy + card_h // 2

    # Step 4: Drop Shadow & Dual Solar-Amethyst Glowing Halo
    overlay = canvas.copy()
    draw_rounded_rect(overlay, x1 + 10, y1 + 14, x2 + 10, y2 + 18, (0, 0, 0), radius=28, thickness=-1)
    cv2.addWeighted(overlay, 0.65 * card_alpha, canvas, 1.0 - 0.65 * card_alpha, 0, canvas)

    # Pulsing outer solar halo
    pulse = 0.5 + 0.5 * math.sin(elapsed * 5.0)
    solar_glow = tuple(int(ch * (0.7 + 0.3 * pulse)) for ch in accent_color)
    overlay = canvas.copy()
    draw_rounded_rect(
        overlay,
        x1 - 5,
        y1 - 5,
        x2 + 5,
        y2 + 5,
        solar_glow,
        radius=32,
        thickness=-1,
    )
    cv2.addWeighted(overlay, 0.22 * card_alpha, canvas, 1.0 - 0.22 * card_alpha, 0, canvas)

    # Main Card Body: Deep Cosmic Amethyst (B=52, G=24, R=40)
    card_bg = (52, 24, 40)
    draw_rounded_rect(
        canvas,
        x1,
        y1,
        x2,
        y2,
        card_bg,
        radius=26,
        thickness=-1,
        border_color=(30, 215, 255),
        border_thickness=2,
    )

    # Royal Corner Ornaments
    corner_s = int(22 * sf)
    for ox, oy, dx, dy in [(x1+14, y1+14, 1, 1), (x2-14, y1+14, -1, 1), (x1+14, y2-14, 1, -1), (x2-14, y2-14, -1, -1)]:
        cv2.line(canvas, (ox, oy), (ox + dx * corner_s, oy), (30, 215, 255), 2, cv2.LINE_AA)
        cv2.line(canvas, (ox, oy), (ox, oy + dy * corner_s), (30, 215, 255), 2, cv2.LINE_AA)

    # ---------------------- Card Header ----------------------
    # A) Royal Crown Capsule Badge: "👑 LEVEL 4 • RECIPROCITY MASTERY"
    badge_w = int(270 * sf)
    badge_h = int(32 * sf)
    bx1 = cx - badge_w // 2
    by1 = y1 + int(20 * sf)
    bx2 = cx + badge_w // 2
    by2 = by1 + badge_h

    draw_rounded_rect(canvas, bx1, by1, bx2, by2, (75, 34, 55), radius=badge_h // 2, thickness=-1,
                      border_color=(30, 215, 255), border_thickness=1)

    draw_crown_icon(canvas, bx1 + int(22 * sf), by1 + badge_h // 2, size=int(18 * sf), color=(30, 215, 255))
    cv2.putText(canvas, "LEVEL 4 - RECIPROCITY MASTERY", (bx1 + int(42 * sf), by1 + badge_h // 2 + int(5 * sf)),
                cv2.FONT_HERSHEY_DUPLEX, 0.42 * sf, (245, 235, 255), 1, cv2.LINE_AA)

    # B) Game Title in Bold Solar Typography
    title_y = by2 + int(36 * sf)
    put_centered_text(
        canvas,
        game_title.upper(),
        cx,
        title_y,
        cv2.FONT_HERSHEY_DUPLEX,
        1.05 * sf,
        (255, 255, 255),
        thickness=2,
        shadow_color=(0, 0, 0),
    )

    # Triumphant separator with center jewel
    sep_y = title_y + int(24 * sf)
    line_hw = int(card_w * 0.40)
    cv2.line(canvas, (cx - line_hw, sep_y), (cx - 16, sep_y), (150, 100, 255), 1, cv2.LINE_AA)
    cv2.line(canvas, (cx + 16, sep_y), (cx + line_hw, sep_y), (30, 215, 255), 1, cv2.LINE_AA)
    draw_jewel(canvas, cx, sep_y, int(6 * sf), (30, 215, 255))

    # ---------------------- Main Split Architecture ----------------------
    body_y1 = sep_y + int(16 * sf)
    body_y2 = y2 - int(54 * sf)
    body_h = body_y2 - body_y1

    inner_margin = int(22 * sf)
    left_w = int((card_w - inner_margin * 3) * 0.42)
    right_w = (card_w - inner_margin * 3) - left_w

    lx1 = x1 + inner_margin
    ly1 = body_y1
    lx2 = lx1 + left_w
    ly2 = body_y2

    rx1 = lx2 + inner_margin
    ry1 = body_y1
    rx2 = x2 - inner_margin
    ry2 = body_y2

    # --- LEFT HERO POD (Solar Arc Meter & Apex Tier) ---
    draw_rounded_rect(canvas, lx1, ly1, lx2, ly2, (62, 28, 48), radius=18, thickness=-1,
                      border_color=(100, 50, 80), border_thickness=1)

    pod_cx = (lx1 + lx2) // 2
    put_centered_text(canvas, score_label.upper(), pod_cx, ly1 + int(24 * sf),
                      cv2.FONT_HERSHEY_DUPLEX, 0.46 * sf, (225, 210, 240), 1, None)

    # Solar Arc Gauge
    gauge_cy = ly1 + int(96 * sf)
    gauge_r = int(52 * sf)
    cv2.circle(canvas, (pod_cx, gauge_cy), gauge_r, (80, 36, 60), 4, cv2.LINE_AA)
    sweep_angle = int(240 + 60 * math.sin(elapsed * 3.5))
    cv2.ellipse(canvas, (pod_cx, gauge_cy), (gauge_r, gauge_r), -90, 0, sweep_angle, (30, 215, 255), 4, cv2.LINE_AA)
    cv2.circle(canvas, (pod_cx, gauge_cy), gauge_r + 7, (150, 100, 255), 1, cv2.LINE_AA)

    # Big Score Number
    score_str = str(score)
    score_pulse = 1.0 + 0.03 * math.sin(elapsed * 5.0)
    score_scale = 1.95 * sf * score_pulse
    put_centered_text(canvas, score_str, pod_cx, gauge_cy,
                      cv2.FONT_HERSHEY_DUPLEX, score_scale, (255, 255, 255), 3, (15, 10, 15))

    # Apex Tier Pill Badge (e.g., "TIER: GRANDMASTER")
    tier_badge_w = int(140 * sf)
    tier_badge_h = int(26 * sf)
    tbx1 = pod_cx - tier_badge_w // 2
    tby1 = gauge_cy + gauge_r + int(14 * sf)
    tbx2 = pod_cx + tier_badge_w // 2
    tby2 = tby1 + tier_badge_h

    tier_color = (30, 215, 255) if tier_badge == "GRANDMASTER" else (100, 255, 140)
    draw_rounded_rect(canvas, tbx1, tby1, tbx2, tby2, (78, 35, 60), radius=tier_badge_h // 2, thickness=-1,
                      border_color=tier_color, border_thickness=1)
    cv2.putText(canvas, f"TIER: {tier_badge}", (tbx1 + int(16 * sf), tby1 + tier_badge_h // 2 + int(4 * sf)),
                cv2.FONT_HERSHEY_DUPLEX, 0.44 * sf, tier_color, 1, cv2.LINE_AA)

    # 3 Solar Stars
    star_center_y = tby2 + int(24 * sf)
    star_count = max(1, min(3, stars))
    star_spacing = int(40 * sf)
    star_start_x = pod_cx - ((star_count - 1) * star_spacing) // 2
    for i in range(star_count):
        sx = star_start_x + i * star_spacing
        sy = star_center_y
        pulse_i = 1.0 + 0.10 * math.sin(elapsed * 4.5 + i * 1.2)
        r_out = int(16 * sf * pulse_i)
        r_in = int(7.0 * sf * pulse_i)
        draw_star(canvas, sx, sy, r_out + 4, r_in + 2, (150, 100, 255), fill=True)
        draw_star(canvas, sx, sy, r_out, r_in, (30, 215, 255), fill=True)

    # Verdict text with auto-fit
    verdict_text = verdict.upper()
    v_scale = 0.42 * sf
    (vtw, _), _ = cv2.getTextSize(verdict_text, cv2.FONT_HERSHEY_DUPLEX, v_scale, 1)
    max_vw = left_w - int(50 * sf)
    if vtw > max_vw:
        v_scale *= (max_vw / max(1, vtw))
    put_centered_text(canvas, verdict_text, pod_cx, star_center_y + int(24 * sf),
                      cv2.FONT_HERSHEY_DUPLEX, v_scale, (255, 235, 140), 1, None)

    # --- RIGHT COLUMN (4 Telemetry Cards with Dual Progress Meters) ---
    right_tiles = stats[:4]
    tile_h = int((body_h - int(12 * sf) * 3) // 4)

    for idx, st in enumerate(right_tiles):
        ty1 = ry1 + idx * (tile_h + int(12 * sf))
        ty2 = ty1 + tile_h
        tx1 = rx1
        tx2 = rx2

        draw_rounded_rect(canvas, tx1, ty1, tx2, ty2, (62, 28, 48), radius=12, thickness=-1,
                          border_color=(100, 50, 80), border_thickness=1)

        val_color = st.get("color", (30, 215, 255))
        # Left accent pill
        cv2.circle(canvas, (tx1 + int(14 * sf), ty1 + int(18 * sf)), int(4 * sf), val_color, -1, cv2.LINE_AA)

        lbl = str(st.get("label", "")).upper()
        cv2.putText(canvas, lbl, (tx1 + int(26 * sf), ty1 + int(22 * sf)),
                    cv2.FONT_HERSHEY_DUPLEX, 0.40 * sf, (220, 200, 235), 1, cv2.LINE_AA)

        val = str(st.get("value", ""))
        (vw, vh), _ = cv2.getTextSize(val, cv2.FONT_HERSHEY_DUPLEX, 0.68 * sf, 2)
        cv2.putText(canvas, val, (tx2 - vw - int(16 * sf), ty1 + int(24 * sf)),
                    cv2.FONT_HERSHEY_DUPLEX, 0.68 * sf, val_color, 2, cv2.LINE_AA)

        # Mini Progress Meter
        meter_x1 = tx1 + int(14 * sf)
        meter_x2 = tx2 - int(14 * sf)
        meter_y = ty2 - int(10 * sf)
        meter_w = meter_x2 - meter_x1
        cv2.line(canvas, (meter_x1, meter_y), (meter_x2, meter_y), (80, 36, 60), 2, cv2.LINE_AA)

        pct = float(st.get("percent", 0.75 + 0.05 * idx))
        pct = max(0.15, min(1.0, pct))
        fill_w = int(meter_w * pct)
        cv2.line(canvas, (meter_x1, meter_y), (meter_x1 + fill_w, meter_y), val_color, 2, cv2.LINE_AA)

    # ---------------------- 4-Second Countdown Bar ----------------------
    remaining = max(0.0, duration_s - elapsed)
    prog_frac = max(0.0, min(1.0, remaining / duration_s))

    bar_w = int(card_w * 0.92)
    bar_h = int(12 * sf)
    bar_x1 = cx - bar_w // 2
    bar_y1 = y2 - int(34 * sf)
    bar_x2 = cx + bar_w // 2
    bar_y2 = bar_y1 + bar_h

    draw_rounded_rect(canvas, bar_x1, bar_y1, bar_x2, bar_y2, (68, 30, 52), radius=bar_h // 2, thickness=-1,
                      border_color=(110, 55, 85), border_thickness=1)

    fill_w = int(bar_w * prog_frac)
    if fill_w > bar_h:
        draw_rounded_rect(canvas, bar_x1, bar_y1, bar_x1 + fill_w, bar_y2, (30, 215, 255),
                          radius=bar_h // 2, thickness=-1)

    cd_text = f"Closing in {remaining:.1f}s... (press Q to exit)"
    put_centered_text(
        canvas,
        cd_text,
        cx,
        bar_y1 - int(12 * sf),
        cv2.FONT_HERSHEY_DUPLEX,
        0.44 * sf,
        (230, 215, 245),
        thickness=1,
        shadow_color=None,
    )

    return canvas


# ---------------------- Main Interactive Quit Function ----------------------
def show_quit_card(
    window_name,
    last_frame,
    game_title,
    score,
    score_label,
    stats,
    stars=3,
    verdict="GRANDMASTER PERFORMANCE!",
    duration_s=4.0,
    accent_color=(30, 215, 255),
    tier_badge="GRANDMASTER",
):
    """
    Shows the Level 4 attractive game card for `duration_s` (4 seconds) with smooth
    animation at ~60 FPS, then automatically returns so the game cleanly exits.
    """
    # 1. Play regal fanfare chime
    play_quit_fanfare()

    # 2. Setup cosmic particle field
    h, w = last_frame.shape[:2]
    particles = CosmicParticleField(count=50, w=w, h=h)

    start_time = time.time()

    # 3. Animation loop for 4 seconds
    while True:
        now = time.time()
        elapsed = now - start_time
        if elapsed >= duration_s:
            break

        if elapsed > 0.5:
            try:
                prop = cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE)
                if prop < 1:
                    break
            except Exception:
                pass

        card_frame = render_quit_card_frame(
            base_frame=last_frame,
            elapsed=elapsed,
            duration_s=duration_s,
            game_title=game_title,
            score=score,
            score_label=score_label,
            stats=stats,
            stars=stars,
            verdict=verdict,
            particles=particles,
            accent_color=accent_color,
            tier_badge=tier_badge,
        )

        cv2.imshow(window_name, card_frame)
        key = cv2.waitKey(16) & 0xFF
        if key == ord('q') or key == 27:
            break
