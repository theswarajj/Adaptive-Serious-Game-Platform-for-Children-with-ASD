# object_quest.py
# Standalone desktop game — Object Quest (Final Version, See & Say mode)
#
# OBJECT QUEST — SEE & SAY. A looping video of a familiar object fills the whole
# screen and the game asks "What is this?" The child SAYS its name. Speech-to-Text
# checks the answer; correct answers get positive feedback, incorrect/unclear answers
# get a gentle hint and another attempt (never a hard failure).
#
# LAYOUT: the video is full-screen background. Every piece of UI (level, score,
# question, "You said", hint, attempts, webcam, character) lives on the LEFT or RIGHT
# edges / corners. The centre of the screen is deliberately left clear.
#
# Objects (11, grouped into 3 tiers) come from the MP4s in NEEDS/object_quest/:
#   Easy   : apple, ball, book, orange
#   Medium : coffee, key, watch, backpack
#   Hard   : socks, spoon, umbrella
#
# Performance metrics tracked: naming accuracy, response time, number of attempts,
# incorrect responses, hint usage, task completion (all summarized on quit).
#
# Adaptive difficulty (rule-based, promotes/demotes on rolling first-attempt accuracy):
#   Easy   -> generous response time, hints freely available
#   Medium -> less response time, hints reduced
#   Hard   -> shortest response time, no hints
#
# Install:  pip install opencv-python SpeechRecognition pyaudio numpy Pillow
# Optional voice narration:  pip install pyttsx3
# Run:      python object_quest.py
# Keys:     Q = quit (prints the metrics summary)   F = toggle fullscreen
#
# NOTE: OpenCV plays the video picture only (no sound from the MP4s).

import cv2
import time
import random
import threading
import string
import difflib
import queue
import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import winsound

def play_success_sound():
    def sound():
        winsound.Beep(600, 150)
        winsound.Beep(800, 150)
        winsound.Beep(1200, 300)
    threading.Thread(target=sound, daemon=True).start()

def play_wrong_sound():
    threading.Thread(target=winsound.Beep, args=(300, 300), daemon=True).start()


try:
    import pyttsx3
    _tts_engine = pyttsx3.init()
    VOICE_AVAILABLE = True
except Exception:
    _tts_engine = None
    VOICE_AVAILABLE = False

try:
    import sounddevice as sd
    from faster_whisper import WhisperModel
    SPEECH_AVAILABLE = True
except Exception as _e:
    sd = None
    WhisperModel = None
    SPEECH_AVAILABLE = False
    print(f"[speech] Missing package: {_e}")

# ==================== Configuration ====================

CANVAS_W, CANVAS_H = 1280, 720
_HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(_HERE, "NEEDS", "object_quest")
# The typing character lives in Talk & Build's folder; look in both places.
CHARACTER_PATHS = [
    os.path.join(ASSETS_DIR, "typing_charater.png"),
    os.path.join(_HERE, "NEEDS", "talk_and_build", "typing_charater.png"),
]
VIDEO_EXTS = (".mp4", ".mov", ".avi", ".mkv", ".webm")
WINDOW_NAME = "Object Quest"
FULLSCREEN_ON_START = True

# Webcam tile (top-right corner)
TV_W, TV_H = 200, 150
TV_MARGIN = 24
TV_X = CANVAS_W - TV_W - TV_MARGIN
TV_Y = TV_MARGIN

FEEDBACK_DISPLAY_MS = 2400
ROLLING_WINDOW = 4
PROMOTE_ACCURACY = 0.75
DEMOTE_ACCURACY = 0.35
TIERS = ["Easy", "Medium", "Hard"]
MAX_ATTEMPTS = 2   # attempts allowed before the answer is gently revealed

# Per-tier knobs: how long we listen, and how generous hints are
TIER_SETTINGS = {
    "Easy":   {"listen_s": 10.0, "hints_allowed": 2},
    "Medium": {"listen_s": 7.0,  "hints_allowed": 1},
    "Hard":   {"listen_s": 5.0,  "hints_allowed": 0},
}

# ---------- Speech engine settings (tuned for child voice & local Whisper) ----------
MIC_DEVICE = None
WHISPER_MODEL_CPU = "small"
WHISPER_LANGUAGE = "en"
INITIAL_PROMPT = (
    "apple, ball, football, soccer, book, orange, coffee, cup, mug, tea, "
    "key, keys, watch, wristwatch, clock, backpack, bag, schoolbag, rucksack, "
    "socks, sock, spoon, spoons, fork, forks, umbrella, What is this?"
)

SAMPLE_RATE = 16000
BLOCK_SIZE = 512
INPUT_GAIN = 5.0
DEBUG_SPEECH = True
MIN_RMS = 0.003
START_MULT = 2.0
END_MULT = 1.5
START_BLOCKS = 3
PREROLL_BLOCKS = 10
END_SILENCE_S = 0.6
SETTLE_S = 0.6
MAX_UTTERANCE_S = 6.0
PARTIAL_EVERY_S = 0.5
MIN_VOICED_S = 0.20

TYPING_SPEED = 28

STATE_ASKING = "asking"
STATE_FEEDBACK = "feedback"


# ==================== Object library ====================
# "stems" = accepted video file names (without extension, case-insensitive), so
# your existing names (coffe, umberla, Spoon, Backpack...) work as they are.
# "synonyms" = spoken answers that count as correct.

OBJECTS = [
    # ---- Easy ----
    {"id": "apple", "stems": ["apple"], "label": "apple", "tier": "Easy",
     "synonyms": ["apple"],
     "hint": "It's a fruit you can eat, red or green!"},
    {"id": "ball", "stems": ["ball"], "label": "ball", "tier": "Easy",
     "synonyms": ["ball", "football", "soccer"],
     "hint": "You kick or bounce this to play!"},
    {"id": "book", "stems": ["book"], "label": "book", "tier": "Easy",
     "synonyms": ["book"],
     "hint": "You read this and turn the pages!"},
    {"id": "orange", "stems": ["orange"], "label": "orange", "tier": "Easy",
     "synonyms": ["orange"],
     "hint": "It's a round fruit, and it's also a color!"},

    # ---- Medium ----
    {"id": "coffee", "stems": ["coffe", "coffee"], "label": "coffee cup", "tier": "Medium",
     "synonyms": ["coffee", "cup", "mug", "tea"],
     "hint": "It's warm, and you drink from it!"},
    {"id": "key", "stems": ["key"], "label": "key", "tier": "Medium",
     "synonyms": ["key", "keys"],
     "hint": "You use this to unlock a door!"},
    {"id": "watch", "stems": ["watch"], "label": "watch", "tier": "Medium",
     "synonyms": ["watch", "wristwatch", "clock"],
     "hint": "You wear this on your wrist to see the time!"},
    {"id": "backpack", "stems": ["backpack"], "label": "backpack", "tier": "Medium",
     "synonyms": ["backpack", "bag", "schoolbag", "rucksack"],
     "hint": "You wear this on your back to carry things!"},

    # ---- Hard ----
    {"id": "socks", "stems": ["socks", "sock"], "label": "socks", "tier": "Hard",
     "synonyms": ["socks", "sock"],
     "hint": "You wear these on your feet, inside your shoes!"},
    # The Spoon video shows a fork AND a spoon, so both words are accepted.
    {"id": "spoon", "stems": ["spoon"], "label": "spoon", "tier": "Hard",
     "synonyms": ["spoon", "spoons", "fork", "forks"],
     "hint": "You use these to eat your food!"},
    {"id": "umbrella", "stems": ["umberla", "umbrella"], "label": "umbrella", "tier": "Hard",
     "synonyms": ["umbrella"],
     "hint": "You open this up when it rains!"},
]


# ==================== Font setup ====================

def _find_font(names):
    font_dirs = ["C:/Windows/Fonts", "/usr/share/fonts", "/System/Library/Fonts",
                 os.path.expanduser("~/.fonts")]
    for name in names:
        for d in font_dirs:
            path = os.path.join(d, name)
            if os.path.exists(path):
                return path
    return None


def load_font(names, size):
    path = _find_font(names)
    if path:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    for name in names:                      # let Pillow search system font dirs itself
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default(size)
    except Exception:
        return ImageFont.load_default()


FONT_TITLE = load_font(["comicbd.ttf", "comic.ttf", "calibrib.ttf", "arialbd.ttf"], 34)
FONT_QUESTION = load_font(["comicbd.ttf", "comic.ttf", "calibrib.ttf", "arialbd.ttf"], 44)
FONT_BODY = load_font(["comic.ttf", "calibri.ttf", "segoeui.ttf", "arial.ttf"], 26)
FONT_HINT = load_font(["comic.ttf", "calibri.ttf", "segoeui.ttf", "arial.ttf"], 24)
FONT_SMALL = load_font(["comic.ttf", "calibri.ttf", "segoeui.ttf", "arial.ttf"], 22)
FONT_HUD = load_font(["comicbd.ttf", "calibrib.ttf", "segoeuib.ttf", "arialbd.ttf"], 26)
FONT_BUBBLE = load_font(["comicbd.ttf", "comic.ttf", "arialbd.ttf"], 36)


# ==================== Small helpers ====================

def overlay_rgba_on_bgr(canvas, overlay_bgra, x, y):
    oh, ow = overlay_bgra.shape[:2]
    ch, cw = canvas.shape[:2]
    x1, y1 = max(0, x), max(0, y)
    x2, y2 = min(cw, x + ow), min(ch, y + oh)
    if x1 >= x2 or y1 >= y2:
        return
    ox1, oy1 = x1 - x, y1 - y
    ox2, oy2 = ox1 + (x2 - x1), oy1 + (y2 - y1)
    crop = overlay_bgra[oy1:oy2, ox1:ox2]
    alpha = crop[:, :, 3:4].astype(np.float32) / 255.0
    bgr = crop[:, :, :3].astype(np.float32)
    bg = canvas[y1:y2, x1:x2].astype(np.float32)
    canvas[y1:y2, x1:x2] = (bgr * alpha + bg * (1.0 - alpha)).astype(np.uint8)


def _wrap_text_pil(text, font, max_width):
    words = text.split()
    lines, current = [], ""
    for w in words:
        test = (current + " " + w).strip()
        bbox = font.getbbox(test)
        tw = bbox[2] - bbox[0] if bbox else 0
        if tw > max_width and current:
            lines.append(current)
            current = w
        else:
            current = test
    if current:
        lines.append(current)          # <- the last line must be kept
    return lines or [""]


def fit_one_line(draw, text, font, max_w):
    """Keeps the END of the text (most recent words) if it is too long for one line."""
    if draw.textlength(text, font=font) <= max_w:
        return text
    while len(text) > 1 and draw.textlength("..." + text, font=font) > max_w:
        text = text[1:]
    return "..." + text


def star_points(cx, cy, r_out, r_in):
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        r = r_out if i % 2 == 0 else r_in
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    return pts


# ==================== Looping full-screen video ====================

def cover_fit(frame, width, height):
    """Scale to FILL the screen without stretching, cropping any overflow from the centre."""
    h, w = frame.shape[:2]
    scale = max(width / w, height / h)
    nw, nh = max(width, int(w * scale + 0.5)), max(height, int(h * scale + 0.5))
    interp = cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR
    resized = cv2.resize(frame, (nw, nh), interpolation=interp)
    x0, y0 = (nw - width) // 2, (nh - height) // 2
    return resized[y0:y0 + height, x0:x0 + width]


def build_video_index(directory):
    """Maps lowercase file stem -> full path for every video file in the folder."""
    index = {}
    if os.path.isdir(directory):
        for fname in os.listdir(directory):
            stem, ext = os.path.splitext(fname)
            if ext.lower() in VIDEO_EXTS:
                index[stem.lower()] = os.path.join(directory, fname)
    return index


def resolve_video_path(obj, index):
    for stem in obj["stems"]:
        if stem.lower() in index:
            return index[stem.lower()]
    return None


class LoopingVideo:
    """Plays one video at a time, forever, paced by the video's own frame rate."""

    def __init__(self, width, height):
        self.width, self.height = width, height
        self.cap = None
        self.interval = 1 / 30
        self.next_time = 0.0
        self.frame = None            # last frame, already cover-fitted to the screen

    def open(self, path):
        self.release()
        self.frame = None
        if not path:
            return False
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            return False
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        self.interval = 1.0 / min(60.0, max(5.0, fps))
        self.cap = cap
        self.next_time = time.time()
        return True

    def next_frame(self):
        if self.cap is None:
            return None
        now = time.time()
        if self.frame is not None and now < self.next_time:
            return self.frame
        ok, raw = self.cap.read()
        if not ok:                                   # reached the end -> loop back to the start
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, raw = self.cap.read()
            if not ok:
                return self.frame
        self.frame = cover_fit(raw, self.width, self.height)
        self.next_time += self.interval
        if now - self.next_time > self.interval * 2:  # fell behind: don't burst to catch up
            self.next_time = now
        return self.frame

    def release(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None


def load_character_image():
    for path in CHARACTER_PATHS:
        if os.path.exists(path):
            img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            if img is not None:
                if img.shape[2] == 3:
                    img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
                    img[:, :, 3] = 255
                return img
    return None


# ==================== HIGH-ACCURACY OFFLINE SPEECH ENGINE ====================

HALLUCINATIONS = {
    "", "you", "thank you", "thanks", "thank you.", "thanks for watching",
    "thank you for watching", "bye", "bye bye", "okay", "ok", "the end",
    "subtitles by the amara.org community", "please subscribe",
}


def list_microphones():
    if sd is None:
        return
    try:
        print("\nAvailable input microphones:")
        for i, d in enumerate(sd.query_devices()):
            if d.get("max_input_channels", 0) > 0:
                print(f"  [{i}] {d['name']}")
        default_in = sd.default.device[0]
        print(f"  Using: {'system default' if MIC_DEVICE is None else MIC_DEVICE} (default index = {default_in})\n")
    except Exception as e:
        print(f"[speech] Could not list microphones: {e}")


class SpeechEngine:
    """
    Continuous microphone capture -> adaptive voice detection -> Whisper transcription.
    Everything runs in background threads; the game loop only calls the small public API:
        start()            load model + open microphone
        reset_round()      forget everything heard so far
        live_text()        text so far (updates while speaking)
        take_answer()      returns the finished answer once paused
        busy()             True while talking or transcribing
        mute()/unmute()    ignore microphone while TTS is speaking
        status()           (label, level) for audio indicator
    """

    def __init__(self):
        self.ok = False
        self.model = None
        self.stream = None
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._audio_q = queue.Queue()
        self._jobs_q = queue.Queue()
        self._mute_depth = 0
        self._epoch = 0
        self._flush = False

        self.round_text = ""
        self.partial_text = ""
        self.last_final_time = 0.0
        self.in_speech = False
        self.pending = 0
        self.level = 0.0
        self.noise_floor = 0.01

    @property
    def muted(self):
        return self._mute_depth > 0

    def mute(self):
        with self._lock:
            self._mute_depth += 1

    def unmute(self):
        with self._lock:
            self._mute_depth = max(0, self._mute_depth - 1)
            now_open = self._mute_depth == 0
        if now_open:
            self.reset_round()

    def reset_round(self):
        with self._lock:
            self._epoch += 1
            self.round_text = ""
            self.partial_text = ""
            self.last_final_time = 0.0
            self._flush = True

    def live_text(self):
        with self._lock:
            return (self.round_text + " " + self.partial_text).strip()

    def busy(self):
        with self._lock:
            return self.in_speech or self.pending > 0

    def status(self):
        with self._lock:
            if self.muted:
                return "Wait... I'm talking", 0.0
            if self.in_speech:
                return "Listening...", self.level
            if self.pending > 0:
                return "Thinking...", self.level
            return "Ready - speak!", self.level

    def take_answer(self, force=False):
        with self._lock:
            if force:
                text = (self.round_text + " " + self.partial_text).strip()
            else:
                finished = (self.round_text
                            and not self.in_speech
                            and self.pending == 0
                            and (time.time() - self.last_final_time) >= SETTLE_S)
                if not finished:
                    return None
                text = self.round_text.strip()
        self.reset_round()
        return text or None

    def start(self):
        if not SPEECH_AVAILABLE:
            return False
        try:
            list_microphones()
            self._load_model()
            self.stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32",
                                         blocksize=BLOCK_SIZE, device=MIC_DEVICE,
                                         callback=self._audio_cb)
            self.stream.start()
            self._calibrate()
            threading.Thread(target=self._vad_loop, daemon=True).start()
            threading.Thread(target=self._worker_loop, daemon=True).start()
            self.ok = True
            print("[speech] Ready. Speak clearly, ~15-20 cm from the microphone.")
            return True
        except Exception as e:
            print(f"[speech] Speech recognition unavailable ({e}).")
            return False

    def stop(self):
        self._stop.set()
        try:
            if self.stream:
                self.stream.stop()
                self.stream.close()
        except Exception:
            pass

    def _build_model(self, size, device, compute):
        print(f"[speech] Loading Whisper '{size}' on {device} ({compute})...")
        model = WhisperModel(size, device=device, compute_type=compute,
                             cpu_threads=max(2, (os.cpu_count() or 4) - 1))
        model.transcribe(np.zeros(SAMPLE_RATE, dtype=np.float32), language=WHISPER_LANGUAGE)
        return model

    def _load_model(self):
        self.model = self._build_model(WHISPER_MODEL_CPU, "cpu", "int8")

    def _audio_cb(self, indata, frames, time_info, status):
        blk = np.clip(indata[:, 0] * INPUT_GAIN, -1.0, 1.0)
        self._audio_q.put(blk.astype(np.float32))

    def _calibrate(self):
        n_blocks = int(1.2 * SAMPLE_RATE / BLOCK_SIZE)
        vals = []
        t0 = time.time()
        while len(vals) < n_blocks and time.time() - t0 < 5:
            try:
                blk = self._audio_q.get(timeout=0.5)
                vals.append(float(np.sqrt(np.mean(blk ** 2))))
            except queue.Empty:
                pass
        if vals:
            self.noise_floor = float(np.clip(np.median(vals), 0.001, 0.05))
        print(f"[speech] Room noise level: {self.noise_floor:.4f}")

    def _vad_loop(self):
        preroll = []
        buf = []
        speech_blocks = 0
        silence_blocks = 0
        last_partial = 0.0
        block_s = BLOCK_SIZE / SAMPLE_RATE

        while not self._stop.is_set():
            try:
                blk = self._audio_q.get(timeout=0.2)
            except queue.Empty:
                continue

            rms = float(np.sqrt(np.mean(blk ** 2)))
            self.level = 0.7 * self.level + 0.3 * rms

            if self._flush or self.muted:
                self._flush = False
                buf, preroll = [], []
                speech_blocks = silence_blocks = 0
                with self._lock:
                    self.in_speech = False
                if self.muted:
                    continue

            thr_start = max(MIN_RMS, self.noise_floor * START_MULT)
            thr_end = max(MIN_RMS * 0.6, self.noise_floor * END_MULT)

            if not self.in_speech:
                preroll.append(blk)
                if len(preroll) > PREROLL_BLOCKS:
                    preroll.pop(0)
                if rms > thr_start:
                    speech_blocks += 1
                else:
                    speech_blocks = 0
                    self.noise_floor = float(np.clip(0.97 * self.noise_floor + 0.03 * rms, 0.001, 0.05))
                if speech_blocks >= START_BLOCKS:
                    if DEBUG_SPEECH:
                        print(f"[speech] voice detected (level {rms:.4f}, threshold {thr_start:.4f})")
                    with self._lock:
                        self.in_speech = True
                    buf = list(preroll)
                    silence_blocks = 0
                    last_partial = time.time()
            else:
                buf.append(blk)
                silence_blocks = silence_blocks + 1 if rms < thr_end else 0
                dur = len(buf) * block_s

                if silence_blocks * block_s >= END_SILENCE_S or dur >= MAX_UTTERANCE_S:
                    keep_tail = 6
                    trimmed = buf[:len(buf) - max(0, silence_blocks - keep_tail)]
                    voiced = (len(buf) - silence_blocks) * block_s
                    with self._lock:
                        self.in_speech = False
                        epoch = self._epoch
                        if voiced >= MIN_VOICED_S:
                            self.pending += 1
                            queue_it = True
                        else:
                            queue_it = False
                    if queue_it:
                        self._jobs_q.put(("final", epoch, np.concatenate(trimmed)))
                    buf, preroll = [], []
                    speech_blocks = silence_blocks = 0
                elif (time.time() - last_partial >= PARTIAL_EVERY_S and dur > 0.8
                      and self._jobs_q.empty() and self.pending == 0):
                    last_partial = time.time()
                    self._jobs_q.put(("partial", self._epoch, np.concatenate(buf)))

    @staticmethod
    def _prepare(audio):
        audio = audio.astype(np.float32)
        audio = audio - float(np.mean(audio))
        peak = float(np.max(np.abs(audio))) if audio.size else 0.0
        if peak > 1e-4:
            audio = audio * min(0.9 / peak, 25.0)
        pad = np.zeros(int(0.25 * SAMPLE_RATE), dtype=np.float32)
        return np.concatenate([pad, audio, pad])

    def _transcribe(self, audio, final):
        audio = self._prepare(audio)
        segments, _info = self.model.transcribe(
            audio,
            language=WHISPER_LANGUAGE,
            task="transcribe",
            beam_size=5 if final else 1,
            temperature=0.0,
            vad_filter=True,
            vad_parameters=dict(threshold=0.3, min_silence_duration_ms=500, speech_pad_ms=400),
            condition_on_previous_text=False,
            initial_prompt=INITIAL_PROMPT,
            no_speech_threshold=0.6,
            log_prob_threshold=-1.0,
            compression_ratio_threshold=2.4,
            without_timestamps=True,
        )
        parts = []
        for s in segments:
            if s.no_speech_prob > 0.6 and s.avg_logprob < -1.0:
                continue
            parts.append(s.text.strip())
        text = " ".join(parts).strip()
        if text.lower().strip(string.punctuation + " ") in HALLUCINATIONS:
            return ""
        return text

    def _worker_loop(self):
        while not self._stop.is_set():
            try:
                kind, epoch, audio = self._jobs_q.get(timeout=0.2)
            except queue.Empty:
                continue
            is_final = (kind == "final")
            text = ""
            try:
                text = self._transcribe(audio, final=is_final)
            except Exception as e:
                err = str(e).lower()
                if "cublas" in err or "cuda" in err or "dll" in err or "gpu" in err:
                    print(f"[speech] GPU transcription failed ({e}), switching to CPU...")
                    try:
                        self.model = self._build_model(WHISPER_MODEL_CPU, "cpu", "int8")
                        text = self._transcribe(audio, final=is_final)
                    except Exception as e2:
                        print(f"[speech] CPU transcription also failed: {e2}")
                else:
                    print(f"[speech] transcription error: {e}")
            if DEBUG_SPEECH and is_final:
                print(f"[speech] Whisper heard: {text!r}")
            with self._lock:
                if epoch == self._epoch:
                    if is_final:
                        if text:
                            self.round_text = (self.round_text + " " + text).strip()
                        self.partial_text = ""
                        self.last_final_time = time.time()
                    elif self.in_speech:
                        self.partial_text = text
                if is_final:
                    self.pending = max(0, self.pending - 1)


# ==================== Answer matching (fuzzy, tolerant of mispronunciation) ====================

FILLER_WORDS = {"a", "an", "the", "its", "it's", "thats", "that's", "this", "is",
                 "i", "see", "think", "look", "looks", "like"}

# Common speech recognition mishearings → correct game words
SPEECH_CORRECTIONS = {
    "appel": "apple", "apples": "apple", "april": "apple",
    "balls": "ball", "bowl": "ball", "bolt": "ball",
    "books": "book", "brook": "book", "cook": "book",
    "oranges": "orange",
    "copy": "coffee", "cosy": "coffee", "toffee": "coffee",
    "cups": "cup", "cap": "cup",
    "keys": "key", "ki": "key", "keen": "key",
    "wash": "watch", "much": "watch", "match": "watch",
    "backpacks": "backpack", "back pack": "backpack",
    "bags": "bag", "back": "bag",
    "sock": "socks", "fox": "socks", "blocks": "socks",
    "spoons": "spoon", "soon": "spoon", "moon": "spoon",
    "forks": "fork", "fort": "fork", "four": "fork",
    "umberla": "umbrella", "umbrellas": "umbrella", "brella": "umbrella",
}


def normalize_words(text):
    words = [w.strip(string.punctuation) for w in text.lower().split()]
    words = [SPEECH_CORRECTIONS.get(w, w) for w in words if w]
    return [w for w in words if w not in FILLER_WORDS]


def matches_label(spoken_text, obj):
    if not spoken_text:
        return False
    spoken_words = normalize_words(spoken_text)
    if not spoken_words:
        return False

    def word_close(a, b):
        return difflib.SequenceMatcher(None, a, b).ratio() > 0.65

    for synonym in obj["synonyms"]:
        syn_words = synonym.split()
        if all(any(word_close(sw, w) for w in spoken_words) for sw in syn_words):
            return True

    spoken_joined = " ".join(spoken_words)
    for synonym in obj["synonyms"]:
        if difflib.SequenceMatcher(None, spoken_joined, synonym).ratio() > 0.60:
            return True
    return False


# ==================== Difficulty controller (rule-based) ====================

class DifficultyController:
    def __init__(self):
        self.tier_idx = 0
        self.history = []

    @property
    def tier(self):
        return TIERS[self.tier_idx]

    def record(self, first_attempt_correct):
        self.history.append(1 if first_attempt_correct else 0)
        if len(self.history) < ROLLING_WINDOW:
            return
        acc = sum(self.history) / len(self.history)
        if acc >= PROMOTE_ACCURACY and self.tier_idx < len(TIERS) - 1:
            self.tier_idx += 1
            self.history = []
        elif acc <= DEMOTE_ACCURACY and self.tier_idx > 0:
            self.tier_idx -= 1
            self.history = []


def spawn_object(tier, previous_id=None):
    pool = [o for o in OBJECTS if o["tier"] == tier and o["id"] != previous_id]
    if not pool:
        pool = [o for o in OBJECTS if o["tier"] == tier] or OBJECTS
    return random.choice(pool)


# ==================== Typing animation ====================

class TypingAnimator:
    def __init__(self):
        self.full_text = ""
        self.start_time = 0
        self.speed = TYPING_SPEED
        self._finished = True

    def start(self, text):
        self.full_text = text
        self.start_time = time.time()
        self._finished = False

    def get_visible_text(self):
        if self._finished:
            return self.full_text
        elapsed = time.time() - self.start_time
        chars = int(elapsed * self.speed)
        if chars >= len(self.full_text):
            self._finished = True
            return self.full_text
        return self.full_text[:chars]

    def get_scale(self):
        """Returns a bouncy scale factor based on animation time."""
        elapsed = time.time() - self.start_time
        if elapsed < 0.3:
            return 1.0 + 0.1 * math.sin((elapsed / 0.3) * math.pi)
        return 1.0

    @property
    def is_finished(self):
        if not self._finished:
            if int((time.time() - self.start_time) * self.speed) >= len(self.full_text):
                self._finished = True
        return self._finished


# ==================== Drawing ====================
# All colours below are RGB (Pillow). Panels are semi-transparent so the video shows through.

COL_BG_TOP = (170, 230, 255)
COL_BG_BOTTOM = (255, 240, 180)
COL_LEVEL_BG = (255, 100, 130, 240)
COL_LEVEL_BAR_BG = (200, 50, 80, 255)
COL_LEVEL_BAR_FILL = (255, 220, 100, 255)
COL_PANEL = (255, 255, 255, 230)
COL_PANEL_BORDER = (230, 230, 240, 255)
COL_QUESTION_BG = (255, 240, 150, 240)
COL_QUESTION_BORDER = (255, 180, 50, 255)
COL_HINT_BG = (255, 250, 230, 240)
COL_HINT_BORDER = (255, 200, 100, 255)
COL_TEXT_DARK = (40, 30, 80, 255)
COL_TEXT_MID = (100, 90, 140, 255)
COL_HINT_TEXT = (255, 120, 50, 255)
COL_ON_AIR = (255, 60, 60, 255)
COL_STAR_FILLED = (255, 210, 50, 255)
COL_STAR_EMPTY = (180, 220, 240, 255)
COL_ACCENT = (255, 150, 50, 255)

# Screen zones (nothing is drawn between x=460 and x=800)
LEFT_X, LEFT_W = 24, 420
RIGHT_EDGE = CANVAS_W - 24


def make_gradient_background():
    """Create a vibrant sunny sky and grassy hill background."""
    bg = np.zeros((CANVAS_H, CANVAS_W, 3), dtype=np.uint8)
    top = np.array([255, 210, 120], dtype=np.float32)
    bottom = np.array([255, 240, 180], dtype=np.float32)
    for y in range(CANVAS_H):
        f = y / (CANVAS_H - 1)
        bg[y, :] = (top * (1 - f) + bottom * f).astype(np.uint8)
    
    pil_img = Image.fromarray(cv2.cvtColor(bg, cv2.COLOR_BGR2RGB))
    draw = ImageDraw.Draw(pil_img)
    # Sun
    draw.ellipse([CANVAS_W - 200, -50, CANVAS_W + 50, 200], fill=(255, 230, 80))
    # Hills
    draw.ellipse([-200, CANVAS_H - 280, CANVAS_W // 2 + 100, CANVAS_H + 400], fill=(120, 220, 90))
    draw.ellipse([CANVAS_W // 2 - 200, CANVAS_H - 350, CANVAS_W + 300, CANVAS_H + 500], fill=(140, 240, 110))
    
    return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)


def draw_video_panel(canvas, frame):
    """Draw the object video perfectly centered in a playful border frame."""
    if frame is None:
        return
    panel_w, panel_h = 640, 480
    px = (CANVAS_W - panel_w) // 2  # 320
    py = (CANVAS_H - panel_h) // 2 + 10  # 130
    border = 14

    resized = cv2.resize(frame, (panel_w, panel_h))
    b, g, r = (50, 150, 255)  # Bright orange
    
    # Outer white shadow/stroke
    cv2.rectangle(canvas, (px - border - 4, py - border - 4), (px + panel_w + border + 4, py + panel_h + border + 4), (255, 255, 255), -1)
    # Main thick border
    cv2.rectangle(canvas, (px - border, py - border), (px + panel_w + border, py + panel_h + border), (b, g, r), -1)

    canvas[py:py + panel_h, px:px + panel_w] = resized
    # White inner highlight
    cv2.rectangle(canvas, (px, py), (px + panel_w, py + panel_h), (255, 255, 255), 3)


def render_ui(canvas, char_img, typing_anim, webcam_frame, *, tier, first_try_correct,
              total_rounds, progress, attempt_num, max_attempts, hint_text, question_text,
              live_text, is_correct, missing_video_name=None, video_frame=None,
              status_label=None, mic_level=0.0):
    
    draw_video_panel(canvas, video_frame)

    # ---- webcam tile, top-right corner ----
    tv_x, tv_y = CANVAS_W - TV_W - 20, 20
    cv2.rectangle(canvas, (tv_x - 6, tv_y - 6), (tv_x + TV_W + 6, tv_y + TV_H + 6), (255, 255, 255), -1)
    canvas[tv_y:tv_y + TV_H, tv_x:tv_x + TV_W] = cv2.resize(webcam_frame, (TV_W, TV_H))

    base = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)).convert("RGBA")
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    dl = ImageDraw.Draw(layer)

    # ---------- UI Panels (Corners & Edges) ----------
    
    # Level Badge (Top Left Corner)
    badge = (20, 20, 280, 95)
    dl.rounded_rectangle(badge, radius=20, fill=COL_LEVEL_BG, outline=(255, 255, 255, 255), width=4)
    bar_x, bar_y, bar_w, bar_h = badge[0] + 20, badge[1] + 50, 200, 12
    dl.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], radius=6, fill=COL_LEVEL_BAR_BG)
    fill_w = int(bar_w * max(0.0, min(1.0, progress)))
    if fill_w > 8:
        dl.rounded_rectangle([bar_x, bar_y, bar_x + fill_w, bar_y + bar_h], radius=6, fill=COL_LEVEL_BAR_FILL)

    # Score Box (Top Left, under Level)
    score_box = (20, 105, 280, 180)
    dl.rounded_rectangle(score_box, radius=20, fill=COL_PANEL, outline=COL_PANEL_BORDER, width=4)

    # Question Box (Top Center)
    qx, qy, qw, qh = 320, 20, 640, 85
    dl.rounded_rectangle([qx+4, qy+4, qx+qw+4, qy+qh+4], radius=24, fill=(220, 150, 30, 200)) # shadow
    dl.rounded_rectangle([qx, qy, qx+qw, qy+qh], radius=24, fill=COL_QUESTION_BG, outline=COL_QUESTION_BORDER, width=4)

    # You Said Box (Bottom Left)
    you_box = (20, 610, 480, 700)
    dl.rounded_rectangle([you_box[0]+4, you_box[1]+4, you_box[2]+4, you_box[3]+4], radius=24, fill=(180, 180, 200, 180))
    dl.rounded_rectangle(you_box, radius=24, fill=COL_PANEL, outline=COL_PANEL_BORDER, width=4)

    # Hint / Attempts Box (Bottom Center)
    hint_box = (500, 610, 1000, 700)
    dl.rounded_rectangle([hint_box[0]+4, hint_box[1]+4, hint_box[2]+4, hint_box[3]+4], radius=24, fill=(180, 180, 200, 180))
    dl.rounded_rectangle(hint_box, radius=24, fill=COL_PANEL, outline=COL_PANEL_BORDER, width=4)

    # Speech Feedback Banner (Large bottom-right panel)
    visible_text = typing_anim.get_visible_text()
    if visible_text:
        # Dynamically size the speech bubble to fit text without cutting off
        bw = 380
        b_lines = _wrap_text_pil(visible_text, FONT_BUBBLE, bw - 40)
        bh = max(200, len(b_lines) * 44 + 60)
        
        # Position in bottom-right corner, ensuring it doesn't go off-screen
        bx = CANVAS_W - bw - 20
        by = CANVAS_H - bh - 20
        
        # draw to temp
        temp = Image.new("RGBA", (bw, bh), (0,0,0,0))
        td = ImageDraw.Draw(temp)
        
        if is_correct is True:
            fill, outline = (220, 255, 230, 255), (100, 200, 130, 255)
        elif is_correct is False:
            fill, outline = (255, 235, 220, 255), (250, 160, 80, 255)
        else:
            fill, outline = (255, 255, 255, 255), (200, 220, 250, 255)
            
        td.rounded_rectangle([4, 4, bw-4, bh-4], radius=32, fill=fill, outline=outline, width=6)
        
        # draw centered text
        ty = (bh - len(b_lines) * 44) // 2
        for line in b_lines:
            tw = td.textlength(line, font=FONT_BUBBLE)
            td.text(((bw - tw)/2, ty), line, fill=COL_TEXT_DARK, font=FONT_BUBBLE)
            ty += 44
            
        scale = typing_anim.get_scale()
        if scale != 1.0:
            sw, sh = int(bw * scale), int(bh * scale)
            temp = temp.resize((sw, sh), Image.Resampling.LANCZOS)
            base.alpha_composite(temp, (bx - (sw - bw)//2, by - (sh - bh)//2))
        else:
            base.alpha_composite(temp, (bx, by))

    base = Image.alpha_composite(base, layer)
    d = ImageDraw.Draw(base)

    # ---------- Text ----------
    # Level & Score
    d.text((badge[0] + 20, badge[1] + 12), f"LEVEL: {tier.upper()}", fill=(255, 255, 255, 255), font=FONT_TITLE)
    accuracy = (first_try_correct / total_rounds * 100) if total_rounds else 0
    d.text((score_box[0] + 20, score_box[1] + 10), f"Score: {first_try_correct}/{total_rounds} ({accuracy:.0f}%)", fill=COL_TEXT_DARK, font=FONT_HUD)
    filled = min(3, first_try_correct)
    for i in range(3):
        pts = star_points(score_box[0] + 40 + i * 40, score_box[1] + 50, 12, 5)
        d.polygon(pts, fill=COL_STAR_FILLED if i < filled else COL_STAR_EMPTY)

    # Question
    q_lines = _wrap_text_pil(question_text, FONT_QUESTION, qw - 40)
    total_h = len(q_lines) * 44
    qy_text = qy + (qh - total_h) // 2
    for i, line in enumerate(q_lines):
        tw = d.textlength(line, font=FONT_QUESTION)
        d.text((qx + (qw - tw) / 2, qy_text + i * 44), line, fill=COL_TEXT_DARK, font=FONT_QUESTION)

    # Hint / Attempts
    att_text = f"Attempt {attempt_num} of {max_attempts}"
    d.text((hint_box[0] + 20, hint_box[1] + 10), att_text, fill=COL_TEXT_MID, font=FONT_HUD)
    if hint_text:
        h_lines = _wrap_text_pil("Hint: " + hint_text, FONT_HINT, hint_box[2] - hint_box[0] - 40)
        for i, line in enumerate(h_lines):
            d.text((hint_box[0] + 20, hint_box[1] + 40 + i * 26), line, fill=COL_HINT_TEXT, font=FONT_HINT)

    # You Said
    d.text((you_box[0] + 20, you_box[1] + 10), "You said:", fill=COL_TEXT_MID, font=FONT_HUD)

    # Dynamic status tag pill on top right
    if live_text:
        tag_text = "HEARING YOU"
        tag_bg = (236, 253, 245)
        tag_border = (16, 185, 129)
        tag_col = (6, 95, 70)
    elif status_label and "Wait" in status_label:
        tag_text = "I'M TALKING"
        tag_bg = (254, 243, 199)
        tag_border = (245, 158, 11)
        tag_col = (180, 83, 9)
    elif status_label and "Thinking" in status_label:
        tag_text = "THINKING..."
        tag_bg = (243, 232, 255)
        tag_border = (147, 51, 234)
        tag_col = (107, 33, 168)
    else:
        tag_text = "LISTENING"
        tag_bg = (239, 246, 255)
        tag_border = (59, 130, 246)
        tag_col = (29, 78, 216)

    tw = int(d.textlength(tag_text, font=FONT_SMALL))
    pill_w = tw + 36
    pill_x = you_box[2] - pill_w - 20
    pill_y = you_box[1] + 10
    d.rounded_rectangle([pill_x, pill_y, pill_x + pill_w, pill_y + 28], radius=12, fill=tag_bg, outline=tag_border, width=2)
    d.ellipse([pill_x + 10, pill_y + 9, pill_x + 19, pill_y + 18], fill=tag_border)
    d.text((pill_x + 24, pill_y + 3), tag_text, fill=tag_col, font=FONT_SMALL)

    # Content line with glowing status dot
    dot_color = (16, 185, 129) if live_text else (59, 130, 246)
    d.ellipse([you_box[0] + 20, you_box[1] + 52, you_box[0] + 32, you_box[1] + 64], fill=dot_color)

    if live_text:
        shown = fit_one_line(d, f'"{live_text}"', FONT_HUD, you_box[2] - you_box[0] - 55)
        d.text((you_box[0] + 40, you_box[1] + 44), shown, fill=(25, 20, 75), font=FONT_HUD)
    else:
        d.text((you_box[0] + 40, you_box[1] + 46), "... speak clearly into your mic!", fill=(140, 150, 175), font=FONT_BODY)

    return cv2.cvtColor(np.array(base.convert("RGB")), cv2.COLOR_RGB2BGR)


# ==================== Session metrics ====================

class SessionMetrics:
    def __init__(self):
        self.response_times = []
        self.attempts_per_round = []
        self.incorrect_responses = 0
        self.hints_used = 0
        self.rounds_completed = 0
        self.first_attempt_correct = 0

    def print_summary(self):
        print("\n" + "=" * 50)
        print("OBJECT QUEST -- SESSION SUMMARY")
        print("=" * 50)
        print(f"Rounds completed:        {self.rounds_completed}")
        acc = (self.first_attempt_correct / self.rounds_completed * 100) if self.rounds_completed else 0
        print(f"Naming accuracy (1st try): {acc:.0f}%  ({self.first_attempt_correct}/{self.rounds_completed})")
        if self.response_times:
            print(f"Avg response time:       {sum(self.response_times) / len(self.response_times):.1f}s")
        if self.attempts_per_round:
            print(f"Avg attempts per round:  {sum(self.attempts_per_round) / len(self.attempts_per_round):.1f}")
        print(f"Incorrect responses:     {self.incorrect_responses}")
        print(f"Hints used:              {self.hints_used}")
        print("=" * 50 + "\n")


# ==================== Main ====================

_tts_lock = threading.Lock()


def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Could not open webcam.")
        return

    if not VOICE_AVAILABLE:
        print("pyttsx3 not installed -- no spoken prompts, text-only. pip install pyttsx3 to enable.")

    speech = SpeechEngine()
    speech_ready = speech.start()
    if not speech_ready:
        print("Speech engine not running -- timeouts will gently reveal answers instead.")

    video_index = build_video_index(ASSETS_DIR)
    print(f"Looking for videos in: {ASSETS_DIR}")
    for o in OBJECTS:
        found = resolve_video_path(o, video_index)
        name = os.path.basename(found) if found else "NOT FOUND (expected " + o["stems"][0] + ".mp4)"
        print(f"  [{o['tier']:6}] {o['id']:9} -> {name}")

    char_img = load_character_image()
    gradient_bg = make_gradient_background()
    video = LoopingVideo(CANVAS_W, CANVAS_H)
    controller = DifficultyController()
    typing_anim = TypingAnimator()
    metrics = SessionMetrics()

    def speak(text):
        """Speaks the text. Microphone is muted while speaking so the game never hears itself."""
        if not VOICE_AVAILABLE:
            return
        if speech_ready:
            speech.mute()

        def run():
            try:
                with _tts_lock:
                    _tts_engine.say(text)
                    _tts_engine.runAndWait()
                time.sleep(0.3)  # let the room echo die out
            except Exception as e:
                print(f"[tts] {e}")
            finally:
                if speech_ready:
                    speech.unmute()
        threading.Thread(target=run, daemon=True).start()

    def clear_speech():
        if speech_ready:
            speech.reset_round()

    cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)
    fullscreen = FULLSCREEN_ON_START
    if fullscreen:
        cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    obj = spawn_object(controller.tier)
    video_ok = video.open(resolve_video_path(obj, video_index))
    attempt_num = 1
    hints_used_this_round = 0
    round_start_time = time.time()
    ask_start = time.time()
    clear_speech()
    typing_anim.start("What is this?")
    speak("What is this?")
    state = STATE_ASKING
    last_correct = None
    feedback_start = None
    current_hint_text = None
    last_spoken = ""
    progress = 1.0

    while True:
        key = cv2.waitKey(1) & 0xFF
        success, cam_frame = cap.read()
        if not success:
            break
        cam_frame = cv2.flip(cam_frame, 1)
        settings = TIER_SETTINGS[controller.tier]

        # ---------- game logic ----------
        spoken = None
        timed_out = False
        early_correct = False

        if state == STATE_ASKING:
            if speech_ready and speech.muted:
                # Still speaking question or hint: timer has not started yet
                ask_start = time.time()
                progress = 1.0
                elapsed = 0.0
            else:
                elapsed = time.time() - ask_start
                progress = max(0.0, 1.0 - (elapsed / settings["listen_s"]))

                # Real-time check: if child already said the correct object name,
                # immediately succeed without waiting for timer to expire!
                live = speech.live_text().strip() if speech_ready else ""
                if live:
                    early_correct = matches_label(live, obj)
                    if early_correct:
                        spoken = live
                        last_spoken = spoken
                        speech.reset_round()

                if not early_correct:
                    # Finished answer = child spoke and paused
                    spoken = speech.take_answer() if speech_ready else None

                    # Time is up -- if child is still talking, give grace
                    grace_over = elapsed >= (settings["listen_s"] + 2.5)
                    still_talking = speech_ready and speech.busy()
                    timed_out = elapsed >= settings["listen_s"] and (grace_over or not still_talking)
                    if timed_out and not spoken and speech_ready:
                        spoken = speech.take_answer(force=True)
        else:
            elapsed = 0.0
            progress = 1.0

        if key == ord('q'):
            break
        if key == ord('f'):
            fullscreen = not fullscreen
            cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN,
                                  cv2.WINDOW_FULLSCREEN if fullscreen else cv2.WINDOW_NORMAL)

        manual_submit = (state == STATE_ASKING) and (key in (ord(' '), 13))
        if manual_submit and not spoken and speech_ready:
            spoken = speech.take_answer(force=True) or (speech.live_text().strip() if speech_ready else None)

        if state == STATE_ASKING and (early_correct or spoken or timed_out or manual_submit):
            spoken_clean = spoken.strip() if spoken else None
            if spoken_clean:
                last_spoken = spoken_clean
            is_correct = matches_label(spoken_clean or "", obj)

            if is_correct:
                if attempt_num == 1:
                    metrics.first_attempt_correct += 1
                metrics.response_times.append(time.time() - round_start_time)
                metrics.attempts_per_round.append(attempt_num)
                metrics.rounds_completed += 1
                controller.record(attempt_num == 1)

                feedback_text = "Correct! Well done!"
                speak(feedback_text)
                last_correct = True
                state = STATE_FEEDBACK
                feedback_start = time.time()
                typing_anim.start(feedback_text)
                play_success_sound()
            else:
                metrics.incorrect_responses += 1
                can_hint = hints_used_this_round < settings["hints_allowed"]
                can_retry = attempt_num < MAX_ATTEMPTS

                if can_retry:
                    attempt_num += 1
                    ask_start = time.time()
                    clear_speech()
                    last_spoken = ""
                    if can_hint:
                        hints_used_this_round += 1
                        metrics.hints_used += 1
                        current_hint_text = obj["hint"]
                        prompt = f"Good try! Here's a hint: {obj['hint']}"
                    else:
                        current_hint_text = None
                        prompt = "Good try! Try saying it again."
                    speak(prompt)
                    typing_anim.start(prompt)
                    play_wrong_sound()
                else:
                    metrics.response_times.append(time.time() - round_start_time)
                    metrics.attempts_per_round.append(attempt_num)
                    metrics.rounds_completed += 1
                    controller.record(False)

                    feedback_text = f"That's okay! This is a {obj['label']}. Try saying: \"{obj['label']}\""
                    speak(feedback_text)
                    last_correct = False
                    state = STATE_FEEDBACK
                    feedback_start = time.time()
                    typing_anim.start(feedback_text)
                    play_wrong_sound()

        elif state == STATE_FEEDBACK:
            progress = 1.0
            if (time.time() - feedback_start) * 1000 >= FEEDBACK_DISPLAY_MS:
                obj = spawn_object(controller.tier, previous_id=obj["id"])
                video_ok = video.open(resolve_video_path(obj, video_index))
                attempt_num = 1
                hints_used_this_round = 0
                current_hint_text = None
                round_start_time = time.time()
                ask_start = time.time()
                clear_speech()
                last_spoken = ""
                typing_anim.start("What is this?")
                speak("What is this?")
                state = STATE_ASKING
                last_correct = None

        # ---------- drawing ----------
        bg = video.next_frame() if video_ok else None
        canvas = (bg if bg is not None else gradient_bg).copy()

        if speech_ready:
            mic_label, mic_level = speech.status()
            live = speech.live_text()
        else:
            mic_label, mic_level, live = "Mic off", 0.0, ""

        display_text = last_spoken if (state == STATE_FEEDBACK and last_spoken) else live

        canvas = render_ui(
            canvas, char_img, typing_anim, cam_frame,
            tier=controller.tier,
            first_try_correct=metrics.first_attempt_correct,
            total_rounds=metrics.rounds_completed,
            progress=progress,
            attempt_num=attempt_num, max_attempts=MAX_ATTEMPTS,
            hint_text=current_hint_text,
            question_text="What is this?",
            live_text=display_text,
            is_correct=last_correct if state == STATE_FEEDBACK else None,
            missing_video_name=None if video_ok else obj["stems"][0] + ".mp4",
            status_label=mic_label,
            mic_level=mic_level,
        )

        cv2.imshow(WINDOW_NAME, canvas)

    if speech_ready:
        speech.stop()
    video.release()
    cap.release()
    cv2.destroyAllWindows()
    metrics.print_summary()


if __name__ == "__main__":
    main()