"""
game_card.py (LEVEL 2 EDITION - Neo-Arcade / Cyber Glassmorphic Style)
---------------------------------------------------------------------
Reusable, ultra-attractive game card displayed upon quitting for Level 2:
- Object Quest (objectyolo.py)
- Emotion Mirror (emotion_mirror.py)
- Body Says It (body_says_it.py)

Displays score, rank badge, radial score pod, and 4 telemetry tiles with
mini gauge bars for exactly 4 seconds with smooth animations and auto-close.
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
    """Plays a high-tech arcade victory chime in a background thread."""
    if winsound is None:
        return

    def _play():
        try:
            # Sci-fi / arcade chime: E5 -> A5 -> E6
            notes = [(659, 90), (880, 100), (1318, 220)]
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


def draw_star(img, cx, cy, r_outer, r_inner, color, fill=True, rot_angle=0.0):
    """Draws a crisp 5-pointed star polygon centered at (cx, cy)."""
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


def draw_diamond(img, cx, cy, size, color):
    """Draws a glowing diamond marker."""
    s = int(size)
    pts = np.array([(cx, cy - s), (cx + s, cy), (cx, cy + s), (cx - s, cy)], dtype=np.int32)
    cv2.fillPoly(img, [pts], color, lineType=cv2.LINE_AA)
    cv2.polylines(img, [pts], True, (255, 255, 255), 1, lineType=cv2.LINE_AA)


def put_centered_text(img, text, cx, y, font, scale, color, thickness=2, shadow_color=None):
    """Draws centered text horizontally with drop shadow."""
    (tw, th), _ = cv2.getTextSize(text, font, scale, thickness)
    tx = int(cx - tw // 2)
    ty = int(y + th // 2)
    if shadow_color is not None:
        cv2.putText(img, text, (tx + 2, ty + 2), font, scale, shadow_color, thickness + 1, cv2.LINE_AA)
    cv2.putText(img, text, (tx, ty), font, scale, color, thickness, cv2.LINE_AA)
    return tw, th


# ---------------------- Floating Cyber Particles ----------------------
class CyberParticle:
    __slots__ = ['x', 'y', 'vx', 'vy', 'color', 'size', 'alpha', 'type', 'rot', 'rot_speed']

    def __init__(self, w, h):
        self.x = random.uniform(0, w)
        self.y = random.uniform(0, h)
        self.vx = random.uniform(-0.9, 0.9)
        self.vy = random.uniform(-1.6, -0.3)
        self.color = random.choice([
            (255, 220, 0),    # Neon Cyan (BGR)
            (100, 255, 80),   # Neon Lime
            (220, 80, 255),   # Cyber Magenta
            (80, 180, 255),   # Radiant Amber
            (255, 255, 255),  # Pure White
        ])
        self.size = random.uniform(3, 8)
        self.alpha = random.uniform(0.4, 0.9)
        self.type = random.choice(['diamond', 'circle', 'square'])
        self.rot = random.uniform(0, 360)
        self.rot_speed = random.uniform(-3, 3)

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
        if self.type == 'diamond':
            draw_diamond(img, cx, cy, int(self.size), c)
        elif self.type == 'square':
            s = int(self.size)
            cv2.rectangle(img, (cx - s, cy - s), (cx + s, cy + s), c, -1)
        else:
            cv2.circle(img, (cx, cy), int(self.size), c, -1, cv2.LINE_AA)


class CyberParticleField:
    def __init__(self, count=45, w=1280, h=720):
        self.w = w
        self.h = h
        self.particles = [CyberParticle(w, h) for _ in range(count)]

    def update_and_draw(self, img):
        h, w = img.shape[:2]
        for p in self.particles:
            p.update(w, h)
            p.draw(img)


# ---------------------- Level 2 Card Frame Renderer ----------------------
def render_quit_card_frame(
    base_frame,
    elapsed,
    duration_s,
    game_title,
    score,
    score_label,
    stats,
    stars=3,
    verdict="EXCEPTIONAL PERFORMANCE!",
    particles=None,
    accent_color=(255, 220, 0),  # Electric Cyan BGR default for Level 2
    rank_grade="S",
):
    """
    Renders Level 2 Neo-Arcade / Cyber Glassmorphic Game Card.
    Features:
    - Charcoal-Carbon background with cyan/magenta ambient glow
    - Split-pod architecture:
      - Left: Circular glowing energy ring around big score, with Rank Grade & Stars
      - Right: 4 telemetry cards with mini gradient gauge bars
    - Animated cyber countdown bar with dual-color sweep
    """
    h, w = base_frame.shape[:2]
    canvas = base_frame.copy()

    # Step 1: Cinematic Frosted Carbon Background
    small = cv2.resize(canvas, (max(16, w // 8), max(16, h // 8)), interpolation=cv2.INTER_LINEAR)
    small_blur = cv2.GaussianBlur(small, (21, 21), 0)
    frosted = cv2.resize(small_blur, (w, h), interpolation=cv2.INTER_LINEAR)

    # Carbon Dark Overlay: B=28, G=20, R=16 for rich graphite
    carbon_overlay = np.full((h, w, 3), (28, 20, 16), dtype=np.uint8)
    canvas = cv2.addWeighted(frosted, 0.28, carbon_overlay, 0.72, 0)

    # Step 2: Animated Cyber Particles
    if particles is not None:
        particles.update_and_draw(canvas)

    # Step 3: Responsive Card Sizing & Entrance Animation
    entrance_t = min(1.0, elapsed / 0.35)
    # Snappy cyber spring ease
    zoom = 0.90 + 0.10 * (1.0 - (1.0 - entrance_t) ** 3)
    card_alpha = min(1.0, elapsed / 0.22)

    # Dynamic scaling: scales naturally with resolution (1080p, 1440p, 4K)
    sf = min(w / 1280.0, h / 720.0)
    sf = max(0.85, min(2.5, sf))

    # Prominent fullscreen-filling card: 88% width and 88% height
    card_w = int(w * 0.88 * zoom)
    card_h = int(h * 0.88 * zoom)

    cx, cy = w // 2, h // 2
    x1 = cx - card_w // 2
    y1 = cy - card_h // 2
    x2 = cx + card_w // 2
    y2 = cy + card_h // 2

    # Step 4: Drop Shadow & Dual-Tone Neon Halo
    overlay = canvas.copy()
    draw_rounded_rect(overlay, x1 + 10, y1 + 14, x2 + 10, y2 + 18, (0, 0, 0), radius=28, thickness=-1)
    cv2.addWeighted(overlay, 0.65 * card_alpha, canvas, 1.0 - 0.65 * card_alpha, 0, canvas)

    # Pulsing outer neon cyan-magenta halo
    pulse = 0.5 + 0.5 * math.sin(elapsed * 5.0)
    neon_glow_color = tuple(int(ch * (0.7 + 0.3 * pulse)) for ch in accent_color)
    overlay = canvas.copy()
    draw_rounded_rect(
        overlay,
        x1 - 5,
        y1 - 5,
        x2 + 5,
        y2 + 5,
        neon_glow_color,
        radius=32,
        thickness=-1,
    )
    cv2.addWeighted(overlay, 0.22 * card_alpha, canvas, 1.0 - 0.22 * card_alpha, 0, canvas)

    # Main Card Body: Deep Obsidian/Carbon (B=36, G=26, R=22)
    card_bg = (36, 26, 22)
    draw_rounded_rect(
        canvas,
        x1,
        y1,
        x2,
        y2,
        card_bg,
        radius=26,
        thickness=-1,
        border_color=(255, 220, 100),
        border_thickness=2,
    )

    # High-tech corner bracket accents
    bracket_len = int(24 * sf)
    b_col = accent_color
    cv2.line(canvas, (x1 + 14, y1 + 14), (x1 + 14 + bracket_len, y1 + 14), b_col, 2, cv2.LINE_AA)
    cv2.line(canvas, (x1 + 14, y1 + 14), (x1 + 14, y1 + 14 + bracket_len), b_col, 2, cv2.LINE_AA)
    cv2.line(canvas, (x2 - 14, y1 + 14), (x2 - 14 - bracket_len, y1 + 14), b_col, 2, cv2.LINE_AA)
    cv2.line(canvas, (x2 - 14, y1 + 14), (x2 - 14, y1 + 14 + bracket_len), b_col, 2, cv2.LINE_AA)

    # ---------------------- Card Header ----------------------
    # A) Futuristic Chamfered Badge: "⚡ LEVEL 2 • MISSION COMPLETE"
    badge_w = int(240 * sf)
    badge_h = int(30 * sf)
    bx1 = cx - badge_w // 2
    by1 = y1 + int(18 * sf)
    bx2 = cx + badge_w // 2
    by2 = by1 + badge_h

    draw_rounded_rect(canvas, bx1, by1, bx2, by2, (50, 34, 28), radius=badge_h // 2, thickness=-1,
                      border_color=(100, 255, 120), border_thickness=1)
    # Mini pulsing green neon dot
    dot_pulse = 3 + int(2 * math.sin(elapsed * 6.0))
    cv2.circle(canvas, (bx1 + int(18 * sf), by1 + badge_h // 2), int(dot_pulse * sf), (100, 255, 120), -1, cv2.LINE_AA)
    cv2.putText(canvas, "LEVEL 2 - MISSION COMPLETE", (bx1 + int(28 * sf), by1 + badge_h // 2 + int(4 * sf)),
                cv2.FONT_HERSHEY_DUPLEX, 0.42 * sf, (230, 245, 255), 1, cv2.LINE_AA)

    # B) Game Title in Sleek Cyber Typography
    title_y = by2 + int(32 * sf)
    put_centered_text(
        canvas,
        game_title.upper(),
        cx,
        title_y,
        cv2.FONT_HERSHEY_DUPLEX,
        1.02 * sf,
        (255, 255, 255),
        thickness=2,
        shadow_color=(0, 0, 0),
    )

    # Dual-tone separator
    sep_y = title_y + int(22 * sf)
    line_hw = int(card_w * 0.40)
    cv2.line(canvas, (cx - line_hw, sep_y), (cx - 15, sep_y), (255, 200, 50), 1, cv2.LINE_AA)
    cv2.line(canvas, (cx + 15, sep_y), (cx + line_hw, sep_y), (80, 240, 120), 1, cv2.LINE_AA)
    draw_diamond(canvas, cx, sep_y, int(5 * sf), accent_color)

    # ---------------------- Main Split Architecture ----------------------
    body_y1 = sep_y + int(16 * sf)
    body_y2 = y2 - int(55 * sf)
    body_h = body_y2 - body_y1

    # Left Column: Hero Score Pod & Rank (Width: ~40% of inner width)
    inner_margin = int(24 * sf)
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

    # --- LEFT POD (Circular Radial Power Meter & Score) ---
    draw_rounded_rect(canvas, lx1, ly1, lx2, ly2, (44, 30, 24), radius=18, thickness=-1,
                      border_color=(80, 60, 50), border_thickness=1)

    pod_cx = (lx1 + lx2) // 2
    # Score label
    put_centered_text(canvas, score_label.upper(), pod_cx, ly1 + int(24 * sf),
                      cv2.FONT_HERSHEY_DUPLEX, 0.46 * sf, (190, 210, 230), 1, None)

    # Radial Energy Ring around Score
    gauge_cy = ly1 + int(96 * sf)
    gauge_r = int(50 * sf)
    # Background ring track
    cv2.circle(canvas, (pod_cx, gauge_cy), gauge_r, (60, 42, 34), 4, cv2.LINE_AA)
    # Animated glowing arc
    sweep_angle = int(240 + 60 * math.sin(elapsed * 3.5))
    cv2.ellipse(canvas, (pod_cx, gauge_cy), (gauge_r, gauge_r), -90, 0, sweep_angle, (100, 255, 120), 4, cv2.LINE_AA)
    cv2.circle(canvas, (pod_cx, gauge_cy), gauge_r + 7, (255, 220, 0), 1, cv2.LINE_AA)

    # Big Score Number
    score_str = str(score)
    score_pulse = 1.0 + 0.03 * math.sin(elapsed * 6.0)
    score_scale = 1.85 * sf * score_pulse
    put_centered_text(canvas, score_str, pod_cx, gauge_cy,
                      cv2.FONT_HERSHEY_DUPLEX, score_scale, (255, 255, 255), 3, None)

    # Rank Grade Pill Badge (e.g., "RANK: S" or "RANK: A+")
    rank_badge_w = int(120 * sf)
    rank_badge_h = int(26 * sf)
    rbx1 = pod_cx - rank_badge_w // 2
    rby1 = gauge_cy + gauge_r + int(14 * sf)
    rbx2 = pod_cx + rank_badge_w // 2
    rby2 = rby1 + rank_badge_h

    rank_color = (80, 220, 255) if rank_grade == "S" else (100, 255, 120)
    draw_rounded_rect(canvas, rbx1, rby1, rbx2, rby2, (55, 38, 30), radius=rank_badge_h // 2, thickness=-1,
                      border_color=rank_color, border_thickness=1)
    cv2.putText(canvas, f"RANK: {rank_grade}", (rbx1 + int(24 * sf), rby1 + rank_badge_h // 2 + int(4 * sf)),
                cv2.FONT_HERSHEY_DUPLEX, 0.46 * sf, rank_color, 1, cv2.LINE_AA)

    # 3 Cyber Stars
    star_center_y = rby2 + int(24 * sf)
    star_count = max(1, min(3, stars))
    star_spacing = int(38 * sf)
    star_start_x = pod_cx - ((star_count - 1) * star_spacing) // 2
    for i in range(star_count):
        sx = star_start_x + i * star_spacing
        sy = star_center_y
        pulse_i = 1.0 + 0.10 * math.sin(elapsed * 4.5 + i * 1.2)
        r_out = int(15 * sf * pulse_i)
        r_in = int(6.5 * sf * pulse_i)
        draw_star(canvas, sx, sy, r_out + 4, r_in + 2, (255, 150, 0), fill=True)
        draw_star(canvas, sx, sy, r_out, r_in, (80, 240, 255), fill=True)

    # Verdict Ribbon with auto-fit
    verdict_text = verdict.upper()
    v_scale = 0.40 * sf
    (vtw, _), _ = cv2.getTextSize(verdict_text, cv2.FONT_HERSHEY_DUPLEX, v_scale, 1)
    max_vw = left_w - int(70 * sf)
    if vtw > max_vw:
        v_scale *= (max_vw / max(1, vtw))
    put_centered_text(canvas, verdict_text, pod_cx, star_center_y + int(24 * sf),
                      cv2.FONT_HERSHEY_DUPLEX, v_scale, (255, 235, 140), 1, None)

    # --- RIGHT COLUMN (4 Telemetry Cards with Mini Gauge Bars) ---
    right_tiles = stats[:4]
    tile_h = int((body_h - int(12 * sf) * 3) // 4)

    for idx, st in enumerate(right_tiles):
        ty1 = ry1 + idx * (tile_h + int(12 * sf))
        ty2 = ty1 + tile_h
        tx1 = rx1
        tx2 = rx2

        # Card body
        draw_rounded_rect(canvas, tx1, ty1, tx2, ty2, (44, 30, 24), radius=12, thickness=-1,
                          border_color=(80, 60, 50), border_thickness=1)

        # Left Neon Accent Dot
        val_color = st.get("color", (255, 220, 0))
        cv2.circle(canvas, (tx1 + int(14 * sf), ty1 + int(18 * sf)), int(4 * sf), val_color, -1, cv2.LINE_AA)

        # Label
        lbl = str(st.get("label", "")).upper()
        cv2.putText(canvas, lbl, (tx1 + int(26 * sf), ty1 + int(22 * sf)),
                    cv2.FONT_HERSHEY_DUPLEX, 0.40 * sf, (175, 195, 215), 1, cv2.LINE_AA)

        # Value
        val = str(st.get("value", ""))
        (vw, vh), _ = cv2.getTextSize(val, cv2.FONT_HERSHEY_DUPLEX, 0.65 * sf, 2)
        cv2.putText(canvas, val, (tx2 - vw - int(16 * sf), ty1 + int(24 * sf)),
                    cv2.FONT_HERSHEY_DUPLEX, 0.65 * sf, val_color, 2, cv2.LINE_AA)

        # Mini Progress Meter Line underneath
        meter_x1 = tx1 + int(14 * sf)
        meter_x2 = tx2 - int(14 * sf)
        meter_y = ty2 - int(10 * sf)
        meter_w = meter_x2 - meter_x1
        cv2.line(canvas, (meter_x1, meter_y), (meter_x2, meter_y), (60, 42, 34), 2, cv2.LINE_AA)

        # Compute fill percentage
        pct = float(st.get("percent", 0.75 + 0.05 * idx))
        pct = max(0.15, min(1.0, pct))
        fill_w = int(meter_w * pct)
        cv2.line(canvas, (meter_x1, meter_y), (meter_x1 + fill_w, meter_y), val_color, 2, cv2.LINE_AA)

    # ---------------------- 4-Second Countdown Bar ----------------------
    remaining = max(0.0, duration_s - elapsed)
    prog_frac = max(0.0, min(1.0, remaining / duration_s))

    bar_w = int(card_w * 0.92)
    bar_h = int(10 * sf)
    bar_x1 = cx - bar_w // 2
    bar_y1 = y2 - int(32 * sf)
    bar_x2 = cx + bar_w // 2
    bar_y2 = bar_y1 + bar_h

    # Bar track
    draw_rounded_rect(canvas, bar_x1, bar_y1, bar_x2, bar_y2, (50, 34, 26), radius=bar_h // 2, thickness=-1,
                      border_color=(80, 55, 45), border_thickness=1)

    # Animated neon fill
    fill_w = int(bar_w * prog_frac)
    if fill_w > bar_h:
        draw_rounded_rect(canvas, bar_x1, bar_y1, bar_x1 + fill_w, bar_y2, (100, 255, 120),
                          radius=bar_h // 2, thickness=-1)

    # Countdown text
    cd_text = f"Closing in {remaining:.1f}s... (press Q to exit)"
    put_centered_text(
        canvas,
        cd_text,
        cx,
        bar_y1 - int(12 * sf),
        cv2.FONT_HERSHEY_DUPLEX,
        0.42 * sf,
        (200, 215, 235),
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
    verdict="EXCEPTIONAL PERFORMANCE!",
    duration_s=4.0,
    accent_color=(255, 220, 0),
    rank_grade="S",
):
    """
    Shows the Level 2 attractive game card for `duration_s` (4 seconds) with smooth
    animation at ~60 FPS, then automatically returns so the game cleanly exits.
    """
    # 1. Play arcade victory fanfare chime
    play_quit_fanfare()

    # 2. Setup cyber particle field
    h, w = last_frame.shape[:2]
    particles = CyberParticleField(count=45, w=w, h=h)

    start_time = time.time()

    # 3. Animation loop for 4 seconds
    while True:
        now = time.time()
        elapsed = now - start_time
        if elapsed >= duration_s:
            break

        # Check if window was closed by user
        try:
            prop = cv2.getWindowProperty(window_name, cv2.WND_PROP_VISIBLE)
            if prop < 1:
                break
        except Exception:
            pass

        # Render frame
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
            rank_grade=rank_grade,
        )

        cv2.imshow(window_name, card_frame)
        key = cv2.waitKey(16) & 0xFF
        if key == ord('q') or key == 27:
            break
