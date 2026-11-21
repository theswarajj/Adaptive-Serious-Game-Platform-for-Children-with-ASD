"""
game_card.py
------------
Reusable, visually stunning game card displayed upon quitting for:
- Bubble Hunt (Balloon Pop Focus)
- Follow the Star (Follow the Face)
- Pattern Trail

Displays score and rich player telemetry for exactly 4 seconds with smooth
countdown animations, floating star particles, fanfare sound, and console-grade
glassmorphic UI aesthetics.
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
    """Plays a bright, pleasant victory arpeggio in a background thread."""
    if winsound is None:
        return

    def _play():
        try:
            # Ascending cheerful arpeggio: C5 -> E5 -> G5 -> C6
            notes = [(523, 90), (659, 90), (784, 110), (1046, 240)]
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


# ---------------------- Geometry & Drawing Utilities ----------------------
def draw_rounded_rect(img, x1, y1, x2, y2, color, radius=18, thickness=-1, border_color=None, border_thickness=1):
    """Draws a rounded rectangle with smooth corners and optional border."""
    x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
    w = x2 - x1
    h = y2 - y1
    radius = max(2, min(radius, w // 2, h // 2))

    if thickness == -1:
        # Filled body
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


def draw_trophy_icon(img, cx, cy, size=24, color=(30, 215, 255)):
    """Draws an elegant vector gold trophy icon at (cx, cy)."""
    cx, cy = int(cx), int(cy)
    s = size / 24.0

    # Cup Bowl
    bowl_pts = [
        (int(cx - 12 * s), int(cy - 10 * s)),
        (int(cx + 12 * s), int(cy - 10 * s)),
        (int(cx + 9 * s), int(cy + 2 * s)),
        (int(cx - 9 * s), int(cy + 2 * s)),
    ]
    cv2.fillPoly(img, [np.array(bowl_pts, dtype=np.int32)], color, cv2.LINE_AA)
    cv2.polylines(img, [np.array(bowl_pts, dtype=np.int32)], True, (255, 255, 255), 1, cv2.LINE_AA)

    # Stem
    cv2.rectangle(img, (int(cx - 3 * s), int(cy + 2 * s)), (int(cx + 3 * s), int(cy + 8 * s)), color, -1)

    # Base
    base_pts = [
        (int(cx - 8 * s), int(cy + 8 * s)),
        (int(cx + 8 * s), int(cy + 8 * s)),
        (int(cx + 10 * s), int(cy + 12 * s)),
        (int(cx - 10 * s), int(cy + 12 * s)),
    ]
    cv2.fillPoly(img, [np.array(base_pts, dtype=np.int32)], color, cv2.LINE_AA)
    cv2.polylines(img, [np.array(base_pts, dtype=np.int32)], True, (255, 255, 255), 1, cv2.LINE_AA)

    # Handles
    cv2.ellipse(img, (int(cx - 12 * s), int(cy - 4 * s)), (int(4 * s), int(6 * s)), 0, 90, 270, (255, 255, 255), 1, cv2.LINE_AA)
    cv2.ellipse(img, (int(cx + 12 * s), int(cy - 4 * s)), (int(4 * s), int(6 * s)), 0, -90, 90, (255, 255, 255), 1, cv2.LINE_AA)

    # Inner shine
    cv2.circle(img, (cx, int(cy - 4 * s)), max(1, int(2 * s)), (255, 255, 255), -1, cv2.LINE_AA)


def put_centered_text(img, text, cx, y, font, scale, color, thickness=2, shadow_color=(10, 10, 15)):
    """Draws centered text horizontally with drop shadow."""
    (tw, th), _ = cv2.getTextSize(text, font, scale, thickness)
    tx = int(cx - tw // 2)
    ty = int(y + th // 2)
    if shadow_color is not None:
        cv2.putText(img, text, (tx + 2, ty + 2), font, scale, shadow_color, thickness + 1, cv2.LINE_AA)
    cv2.putText(img, text, (tx, ty), font, scale, color, thickness, cv2.LINE_AA)
    return tw, th


# ---------------------- Animated Floating Particles ----------------------
class Particle:
    __slots__ = ['x', 'y', 'vx', 'vy', 'color', 'size', 'alpha', 'type', 'rot', 'rot_speed']

    def __init__(self, w, h):
        self.x = random.uniform(0, w)
        self.y = random.uniform(0, h)
        self.vx = random.uniform(-0.8, 0.8)
        self.vy = random.uniform(-1.8, -0.4)
        self.color = random.choice([
            (30, 215, 255),   # Radiant Gold
            (255, 215, 50),   # Cyan
            (80, 240, 120),   # Mint
            (240, 120, 255),  # Violet
            (255, 140, 100),  # Coral
        ])
        self.size = random.uniform(4, 9)
        self.alpha = random.uniform(0.45, 0.95)
        self.type = random.choice(['star', 'circle', 'bokeh'])
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
        elif self.type == 'bokeh':
            cv2.circle(img, (cx, cy), int(self.size * 1.6), c, -1, cv2.LINE_AA)
        else:
            cv2.circle(img, (cx, cy), int(self.size), c, -1, cv2.LINE_AA)
            cv2.circle(img, (cx, cy), max(1, int(self.size * 0.4)), (255, 255, 255), -1, cv2.LINE_AA)


class ParticleField:
    def __init__(self, count=45, w=1280, h=720):
        self.w = w
        self.h = h
        self.particles = [Particle(w, h) for _ in range(count)]

    def update_and_draw(self, img):
        h, w = img.shape[:2]
        for p in self.particles:
            p.update(w, h)
            p.draw(img)


# ---------------------- Quit Card Frame Renderer ----------------------
def render_quit_card_frame(
    base_frame,
    elapsed,
    duration_s,
    game_title,
    score,
    score_label,
    stats,
    stars=3,
    verdict="EXCELLENT WORK!",
    particles=None,
    accent_color=(30, 215, 255),  # BGR Radiant Gold
):
    """
    Renders an ultra-stylish game card on top of base_frame.
    Features:
    - Frosted dark sapphire-slate glass background
    - Smooth cubic ease-out entrance zoom
    - Outer glowing halo with gentle breathing animation
    - Trophy icon & pill status badge
    - Hero score showcase with 3D gradient look
    - Pulsing 5-pointed gold stars
    - 4 modern glassmorphic stat tiles with left accent bars
    - Smooth glowing 4-second countdown bar
    """
    h, w = base_frame.shape[:2]
    canvas = base_frame.copy()

    # Step 1: Cinematic Frosted Ambient Background
    small = cv2.resize(canvas, (max(16, w // 8), max(16, h // 8)), interpolation=cv2.INTER_LINEAR)
    small_blur = cv2.GaussianBlur(small, (21, 21), 0)
    frosted = cv2.resize(small_blur, (w, h), interpolation=cv2.INTER_LINEAR)

    # Dark midnight sapphire overlay: B=42, G=24, R=16 for rich deep indigo
    dark_overlay = np.full((h, w, 3), (40, 24, 16), dtype=np.uint8)
    canvas = cv2.addWeighted(frosted, 0.32, dark_overlay, 0.68, 0)

    # Step 2: Animated Floating Particles
    if particles is not None:
        particles.update_and_draw(canvas)

    # Step 3: Card Layout & Dimensions (Responsive)
    entrance_t = min(1.0, elapsed / 0.35)
    zoom = 0.90 + 0.10 * (1.0 - (1.0 - entrance_t) ** 3)
    card_alpha = min(1.0, elapsed / 0.22)

    # Dynamic scaling: scales naturally with resolution (1080p, 1440p, 4K)
    sf = min(w / 1280.0, h / 720.0)
    sf = max(0.85, min(2.5, sf))

    # Prominent fullscreen-filling card: 85% width and 88% height
    card_w = int(w * 0.85 * zoom)
    card_h = int(h * 0.88 * zoom)

    cx, cy = w // 2, h // 2
    x1 = cx - card_w // 2
    y1 = cy - card_h // 2
    x2 = cx + card_w // 2
    y2 = cy + card_h // 2

    # Step 4: Drop Shadow & Glowing Border
    overlay = canvas.copy()
    draw_rounded_rect(overlay, x1 + 10, y1 + 14, x2 + 10, y2 + 18, (0, 0, 0), radius=28, thickness=-1)
    cv2.addWeighted(overlay, 0.60 * card_alpha, canvas, 1.0 - 0.60 * card_alpha, 0, canvas)

    # Pulsing outer neon halo
    pulse = 0.5 + 0.5 * math.sin(elapsed * 4.5)
    halo_color = tuple(int(ch * (0.65 + 0.35 * pulse)) for ch in accent_color)
    overlay = canvas.copy()
    draw_rounded_rect(
        overlay,
        x1 - 5,
        y1 - 5,
        x2 + 5,
        y2 + 5,
        halo_color,
        radius=32,
        thickness=-1,
    )
    cv2.addWeighted(overlay, 0.22 * card_alpha, canvas, 1.0 - 0.22 * card_alpha, 0, canvas)

    # Main Card Body: Deep Obsidian/Indigo Glass
    # (B=48, G=30, R=22) in BGR
    card_bg = (48, 30, 22)
    draw_rounded_rect(
        canvas,
        x1,
        y1,
        x2,
        y2,
        card_bg,
        radius=26,
        thickness=-1,
        border_color=(190, 215, 255),
        border_thickness=2,
    )

    # Metallic top edge highlight
    cv2.line(canvas, (x1 + 35, y1 + 3), (x2 - 35, y1 + 3), (255, 255, 255), 1, cv2.LINE_AA)

    # ---------------------- Card Content ----------------------
    # A) Top Pill Badge with Trophy: "🏆 GAME SUMMARY"
    badge_w = int(200 * sf)
    badge_h = int(32 * sf)
    bx1 = cx - badge_w // 2
    by1 = y1 + int(20 * sf)
    bx2 = cx + badge_w // 2
    by2 = by1 + badge_h

    draw_rounded_rect(canvas, bx1, by1, bx2, by2, (65, 42, 32), radius=badge_h // 2, thickness=-1,
                      border_color=accent_color, border_thickness=1)

    # Draw small trophy inside badge
    draw_trophy_icon(canvas, bx1 + int(20 * sf), by1 + badge_h // 2, size=int(18 * sf), color=accent_color)

    # Badge text
    cv2.putText(canvas, "GAME SUMMARY", (bx1 + int(40 * sf), by1 + badge_h // 2 + int(5 * sf)),
                cv2.FONT_HERSHEY_DUPLEX, 0.44 * sf, (235, 240, 255), 1, cv2.LINE_AA)

    # B) Game Title (with comfortable spacing)
    title_y = by2 + int(34 * sf)
    put_centered_text(
        canvas,
        game_title.upper(),
        cx,
        title_y,
        cv2.FONT_HERSHEY_DUPLEX,
        0.98 * sf,
        (255, 255, 255),
        thickness=2,
        shadow_color=(0, 0, 0),
    )

    # Sleek Separator with Diamond
    sep_y = title_y + int(24 * sf)
    line_hw = int(card_w * 0.36)
    cv2.line(canvas, (cx - line_hw, sep_y), (cx - 18, sep_y), (110, 80, 65), 1, cv2.LINE_AA)
    cv2.line(canvas, (cx + 18, sep_y), (cx + line_hw, sep_y), (110, 80, 65), 1, cv2.LINE_AA)
    dm = [(cx, sep_y - 4), (cx + 5, sep_y), (cx, sep_y + 4), (cx - 5, sep_y)]
    cv2.fillPoly(canvas, [np.array(dm, dtype=np.int32)], accent_color, cv2.LINE_AA)

    # C) Hero Score Showcase Box
    hero_w = int(card_w * 0.88)
    hero_h = int(112 * sf)
    hx1 = cx - hero_w // 2
    hy1 = sep_y + int(16 * sf)
    hx2 = cx + hero_w // 2
    hy2 = hy1 + hero_h

    # Deep contrast container
    hero_bg = (60, 38, 28)
    draw_rounded_rect(
        canvas,
        hx1,
        hy1,
        hx2,
        hy2,
        hero_bg,
        radius=16,
        thickness=-1,
        border_color=(120, 85, 70),
        border_thickness=1,
    )

    # Hero Score Label
    put_centered_text(
        canvas,
        score_label.upper(),
        cx,
        hy1 + int(22 * sf),
        cv2.FONT_HERSHEY_DUPLEX,
        0.52 * sf,
        (200, 215, 235),
        thickness=1,
        shadow_color=None,
    )

    # Big Glowing Score Value
    score_str = str(score)
    score_pulse = 1.0 + 0.03 * math.sin(elapsed * 5.0)
    score_scale = 1.85 * sf * score_pulse
    put_centered_text(
        canvas,
        score_str,
        cx,
        hy1 + int(68 * sf),
        cv2.FONT_HERSHEY_DUPLEX,
        score_scale,
        accent_color,
        thickness=3,
        shadow_color=(15, 10, 10),
    )

    # D) Star Rating & Verdict Banner
    star_center_y = hy2 + int(24 * sf)
    star_count = max(1, min(3, stars))
    star_spacing = int(44 * sf)
    star_start_x = cx - ((star_count - 1) * star_spacing) // 2

    for i in range(star_count):
        sx = star_start_x + i * star_spacing
        sy = star_center_y
        pulse_i = 1.0 + 0.10 * math.sin(elapsed * 4.5 + i * 1.2)
        r_out = int(17 * sf * pulse_i)
        r_in = int(7.5 * sf * pulse_i)
        # Outer aura
        draw_star(canvas, sx, sy, r_out + 4, r_in + 2, (0, 160, 255), fill=True)
        # Gold Star
        draw_star(canvas, sx, sy, r_out, r_in, (30, 220, 255), fill=True)

    # Verdict text
    verdict_y = star_center_y + int(26 * sf)
    put_centered_text(
        canvas,
        verdict.upper(),
        cx,
        verdict_y,
        cv2.FONT_HERSHEY_DUPLEX,
        0.60 * sf,
        (255, 235, 140),
        thickness=2,
        shadow_color=(15, 12, 10),
    )

    # E) 4 Modern Stats Grid Tiles (2 x 2)
    grid_y = verdict_y + int(26 * sf)
    tile_gap_x = int(14 * sf)
    tile_gap_y = int(10 * sf)
    tile_w = int((hero_w - tile_gap_x) // 2)
    tile_h = int(72 * sf)

    display_stats = stats[:4]
    for idx, st in enumerate(display_stats):
        col = idx % 2
        row = idx // 2
        tx1 = hx1 + col * (tile_w + tile_gap_x)
        ty1 = grid_y + row * (tile_h + tile_gap_y)
        tx2 = tx1 + tile_w
        ty2 = ty1 + tile_h

        # Tile Body
        tile_color = (55, 35, 26)
        border_c = (95, 68, 55)
        draw_rounded_rect(canvas, tx1, ty1, tx2, ty2, tile_color, radius=12, thickness=-1,
                          border_color=border_c, border_thickness=1)

        # Left Vertical Accent Strip
        val_color = st.get("color", (255, 255, 255))
        cv2.line(canvas, (tx1 + 5, ty1 + 10), (tx1 + 5, ty2 - 10), val_color, int(3 * sf), cv2.LINE_AA)

        # Stat Label (uppercase, clean muted)
        lbl = str(st.get("label", "")).upper()
        cv2.putText(canvas, lbl, (tx1 + int(18 * sf), ty1 + int(22 * sf)),
                    cv2.FONT_HERSHEY_DUPLEX, 0.40 * sf, (180, 195, 215), 1, cv2.LINE_AA)

        # Stat Value (bold, bright highlight)
        val = str(st.get("value", ""))
        cv2.putText(canvas, val, (tx1 + int(18 * sf), ty1 + int(54 * sf)),
                    cv2.FONT_HERSHEY_DUPLEX, 0.72 * sf, val_color, 2, cv2.LINE_AA)

    # F) Countdown Bar at the Bottom (smooth 4.0s progress)
    remaining = max(0.0, duration_s - elapsed)
    prog_frac = max(0.0, min(1.0, remaining / duration_s))

    bar_w = int(hero_w)
    bar_h = int(12 * sf)
    bar_x1 = cx - bar_w // 2
    bar_y1 = y2 - int(44 * sf)
    bar_x2 = cx + bar_w // 2
    bar_y2 = bar_y1 + bar_h

    # Bar background track
    draw_rounded_rect(canvas, bar_x1, bar_y1, bar_x2, bar_y2, (55, 36, 28), radius=bar_h // 2, thickness=-1,
                      border_color=(90, 65, 52), border_thickness=1)

    # Animated filled bar
    fill_w = int(bar_w * prog_frac)
    if fill_w > bar_h:
        draw_rounded_rect(canvas, bar_x1, bar_y1, bar_x1 + fill_w, bar_y2, (90, 235, 140),
                          radius=bar_h // 2, thickness=-1)

    # Countdown text
    cd_text = f"Closing in {remaining:.1f}s... (press Q to exit)"
    put_centered_text(
        canvas,
        cd_text,
        cx,
        bar_y1 - int(14 * sf),
        cv2.FONT_HERSHEY_DUPLEX,
        0.44 * sf,
        (210, 220, 240),
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
    verdict="FANTASTIC PERFORMANCE!",
    duration_s=4.0,
    accent_color=(30, 215, 255),
):
    """
    Shows the attractive game card for `duration_s` (4 seconds) with smooth
    animation at ~60 FPS, then automatically returns so the game cleanly exits.
    """
    # 1. Play victory fanfare chime
    play_quit_fanfare()

    # 2. Setup particle field
    h, w = last_frame.shape[:2]
    particles = ParticleField(count=45, w=w, h=h)

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
        )

        cv2.imshow(window_name, card_frame)
        key = cv2.waitKey(16) & 0xFF
        # Allow instant skip if user presses Q or ESC during the 4 seconds
        if key == ord('q') or key == 27:
            break
