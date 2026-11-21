# describe_the_scene.py
# Standalone desktop game — Describe the Scene  (HIGH-ACCURACY SPEECH VERSION)
#
# DESCRIBE THE SCENE — the child is shown a scene VIDEO and asked to describe
# what is happening IN THEIR OWN WORDS (open-ended, not a fixed question with
# one right answer). The system checks how many expected concepts (action, who,
# what/where) their free description covers. Difficulty scales from describing a
# single action (Easy) up to explaining the complete situation (Hard).
#
# SPEECH ENGINE (new):
#   * faster-whisper (local, offline, free) instead of Google's free recognizer
#   * own microphone capture (sounddevice) with an adaptive voice detector
#   * waits for the child to FINISH the sentence (handles pauses / slow speech)
#   * quiet voices are auto-amplified before recognition
#   * live "You said..." text updates while the child is still speaking
#   * microphone is muted while the game is speaking (no self-echo)
#   * answer timer starts only AFTER the spoken question has finished
#   * hallucination filter (Whisper sometimes invents "thank you" on noise)
#   * forgiving word matching (sat/sitting, kid/kids, plural, near-spellings)
#
# Scene videos live in NEEDS/describe_the_scene/:
#   Cat_on_a_Chair.mp4, Dog_Under_a_Table.mp4, Kids_Playing_Ball.mp4,
#   Girl_Watering_a_Plant.mp4
#
# Install:
#   pip install opencv-python numpy Pillow faster-whisper sounddevice pyttsx3
#   (first run downloads the Whisper model once - internet needed only that time)
# Run:      python describe_the_scene.py
# Keys:     Q = quit (prints the metrics summary)   F = toggle fullscreen

import cv2
import time
import random
import threading
import queue
import string
import difflib
import os
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

try:
    import winsound
    WINSOUND_OK = True
except Exception:
    winsound = None
    WINSOUND_OK = False


def play_success_sound():
    if not WINSOUND_OK:
        return

    def sound():
        winsound.Beep(600, 150)
        winsound.Beep(800, 150)
        winsound.Beep(1200, 300)
    threading.Thread(target=sound, daemon=True).start()


def play_wrong_sound():
    if not WINSOUND_OK:
        return
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
    print("[speech] Run: pip install faster-whisper sounddevice")

# ==================== Configuration ====================

CANVAS_W, CANVAS_H = 1280, 720
_HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(_HERE, "NEEDS", "describe_the_scene")
CHARACTER_PATHS = [
    os.path.join(ASSETS_DIR, "typing_charater.png"),
    os.path.join(_HERE, "NEEDS", "talk_and_build", "typing_charater.png"),
]
VIDEO_EXTS = (".mp4", ".mov", ".avi", ".mkv", ".webm")
WINDOW_NAME = "Describe the Scene"
FULLSCREEN_ON_START = True

TV_W, TV_H = 200, 150
TV_MARGIN = 24
TV_X = CANVAS_W - TV_W - TV_MARGIN
TV_Y = TV_MARGIN

FEEDBACK_DISPLAY_MS = 3200
ROLLING_WINDOW = 4
PROMOTE_ACCURACY = 0.75
DEMOTE_ACCURACY = 0.35
TIERS = ["Easy", "Medium", "Hard"]

# Children speak slowly and pause, so the listening times are generous.
TIER_SETTINGS = {
    "Easy":   {"listen_s": 14.0, "min_words": None},
    "Medium": {"listen_s": 12.0, "min_words": None},
    "Hard":   {"listen_s": 11.0, "min_words": 5},
}
EXTRA_GRACE_S = 5.0   # if the child is still talking when time is up, wait this long at most

TIER_PROMPTS = {
    "Easy":   "What is happening in the picture? Tell me one thing!",
    "Medium": "Tell me more! Who is there and what are they doing?",
    "Hard":   "Tell me the whole story! What is happening, who is there, and where?",
}

TYPING_SPEED = 28
STATE_ASKING = "asking"
STATE_FEEDBACK = "feedback"

# ---------- Speech engine settings (tune these for best results) ----------
MIC_DEVICE = None            # None = system default mic. Run the game once to see the device list,
                             # then set e.g. MIC_DEVICE = 1 to pick a specific (better) microphone.
WHISPER_MODEL_CPU = "small"  # "small" = fast+accurate with prompts, "medium" = slower but best
WHISPER_MODEL_GPU = "medium" # used automatically when an NVIDIA GPU is found ("large-v3" is the best)
WHISPER_LANGUAGE = "en"      # set to None to auto-detect (e.g. if children mix Malayalam/English)
# The initial prompt primes Whisper with the vocabulary we expect — this dramatically
# reduces mishearings like "city" instead of "sitting". Include ALL key game words here.
INITIAL_PROMPT = ("cat sitting chair, dog sleeping table, kids children playing ball, "
                  "girl watering plant flower, sitting sleeping playing watering")

SAMPLE_RATE = 16000
BLOCK_SIZE = 512             # 32 ms per block
INPUT_GAIN = 5.0             # software volume boost for quiet laptop mics (try 3 - 8)
DEBUG_SPEECH = True          # prints what the detector / Whisper is doing in the terminal
MIN_RMS = 0.003              # absolute floor of the voice detector (lower = more sensitive)
START_MULT = 2.0             # voice starts when loudness > noise_floor * this
END_MULT = 1.5               # voice ends when loudness < noise_floor * this
START_BLOCKS = 3             # ~100 ms of sound needed to start an utterance
PREROLL_BLOCKS = 10          # ~320 ms of audio kept from BEFORE the voice started (no clipped first word)
END_SILENCE_S = 0.9          # silence that ends one chunk of speech
SETTLE_S = 1.0               # extra wait after the last words before the answer is scored
MAX_UTTERANCE_S = 15.0
MIN_VOICED_S = 0.35          # ignore clicks / coughs shorter than this
PARTIAL_EVERY_S = 1.2        # how often the live "You said..." text refreshes

FUZZY_THRESHOLD = 0.65       # word-matching leniency (lower = more forgiving)


# ==================== Scene + concept library ====================
# Each concept is a list of acceptable words (synonyms / inflections the child might use).
# The FIRST word in each list is what the feedback text shows.

SCENES = [
    {
        "id": "cat_on_chair",
        "stems": ["cat_on_a_chair"],
        "image_file": "Cat_on_a_Chair.mp4",
        "concepts": {
            "Easy":   [["sitting", "sit", "sits", "sat", "seated", "resting", "relaxing"]],
            "Medium": [["cat", "kitten", "kitty", "cats"],
                       ["sitting", "sit", "sits", "sat", "seated", "resting", "relaxing"]],
            "Hard":   [["cat", "kitten", "kitty", "cats"],
                       ["sitting", "sit", "sits", "sat", "seated", "resting", "relaxing"],
                       ["chair", "seat", "stool", "sofa"]],
        },
    },
    {
        "id": "dog_under_table",
        "stems": ["dog_under_a_table"],
        "image_file": "Dog_Under_a_Table.mp4",
        "concepts": {
            "Easy":   [["sleeping", "sleep", "sleeps", "slept", "asleep", "napping", "resting", "lying", "laying"]],
            "Medium": [["dog", "puppy", "doggy", "dogs"],
                       ["sleeping", "sleep", "sleeps", "slept", "asleep", "napping", "resting", "lying", "laying"]],
            "Hard":   [["dog", "puppy", "doggy", "dogs"],
                       ["sleeping", "sleep", "sleeps", "slept", "asleep", "napping", "resting", "lying", "laying"],
                       ["table", "desk"]],
        },
    },
    {
        "id": "kids_playing_ball",
        "stems": ["kids_playing_ball"],
        "image_file": "Kids_Playing_Ball.mp4",
        "concepts": {
            "Easy":   [["playing", "play", "plays", "played", "throwing", "kicking", "catching"]],
            "Medium": [["children", "kids", "kid", "child", "boy", "boys", "girl", "girls"],
                       ["playing", "play", "plays", "played", "throwing", "kicking", "catching"]],
            "Hard":   [["children", "kids", "kid", "child", "boy", "boys", "girl", "girls"],
                       ["playing", "play", "plays", "played", "throwing", "kicking", "catching"],
                       ["ball", "balls", "football"]],
        },
    },
    {
        "id": "girl_watering_plant",
        "stems": ["girl_watering_a_plant"],
        "image_file": "Girl_Watering_a_Plant.mp4",
        "concepts": {
            "Easy":   [["watering", "water", "waters", "watered", "pouring"]],
            "Medium": [["girl", "girls", "child", "kid"],
                       ["watering", "water", "waters", "watered", "pouring"]],
            "Hard":   [["girl", "girls", "child", "kid"],
                       ["watering", "water", "waters", "watered", "pouring"],
                       ["plant", "plants", "flower", "flowers", "pot", "tree"]],
        },
    },
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
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except Exception:
            continue
    try:
        return ImageFont.load_default(size)
    except Exception:
        return ImageFont.load_default()


FONT_TITLE = load_font(["segoeuib.ttf", "arialbd.ttf", "helveticaneue.ttc"], 28)
FONT_QUESTION = load_font(["segoeuib.ttf", "arialbd.ttf", "helveticaneue.ttc"], 32)
FONT_BODY = load_font(["segoeui.ttf", "arial.ttf", "helvetica.ttc"], 24)
FONT_HINT = load_font(["segoeui.ttf", "arial.ttf", "helvetica.ttc"], 20)
FONT_SMALL = load_font(["segoeui.ttf", "arial.ttf", "helvetica.ttc"], 16)
FONT_HUD = load_font(["segoeuib.ttf", "arialbd.ttf", "helveticaneue.ttc"], 20)
FONT_BUBBLE = load_font(["segoeui.ttf", "arial.ttf", "helvetica.ttc"], 22)


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
        lines.append(current)
    return lines or [""]


def fit_one_line(draw, text, font, max_w):
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
    h, w = frame.shape[:2]
    scale = max(width / w, height / h)
    nw, nh = max(width, int(w * scale + 0.5)), max(height, int(h * scale + 0.5))
    interp = cv2.INTER_AREA if scale < 1 else cv2.INTER_LINEAR
    resized = cv2.resize(frame, (nw, nh), interpolation=interp)
    x0, y0 = (nw - width) // 2, (nh - height) // 2
    return resized[y0:y0 + height, x0:x0 + width]


def build_video_index(directory):
    index = {}
    if os.path.isdir(directory):
        for fname in os.listdir(directory):
            stem, ext = os.path.splitext(fname)
            if ext.lower() in VIDEO_EXTS:
                index[stem.lower()] = os.path.join(directory, fname)
    return index


def resolve_video_path(scene, index):
    for stem in scene["stems"]:
        if stem.lower() in index:
            return index[stem.lower()]
    return None


class LoopingVideo:
    def __init__(self, width, height):
        self.width, self.height = width, height
        self.cap = None
        self.interval = 1 / 30
        self.next_time = 0.0
        self.frame = None

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
        if not ok:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ok, raw = self.cap.read()
            if not ok:
                return self.frame
        self.frame = cover_fit(raw, self.width, self.height)
        self.next_time += self.interval
        if now - self.next_time > self.interval * 2:
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


# ==================== HIGH-ACCURACY SPEECH ENGINE ====================

# Whisper sometimes "hears" these phrases in pure noise. Real children's answers never are only these.
HALLUCINATIONS = {
    "", "you", "thank you", "thanks", "thank you.", "thanks for watching",
    "thank you for watching", "bye", "bye bye", "okay", "ok", "the end",
    "subtitles by the amara.org community", "please subscribe",
}


def list_microphones():
    if sd is None:
        return
    try:
        print("\nAvailable input microphones (set MIC_DEVICE to the number you want):")
        for i, d in enumerate(sd.query_devices()):
            if d.get("max_input_channels", 0) > 0:
                print(f"  [{i}] {d['name']}")
        default_in = sd.default.device[0]
        print(f"  Using: {'system default' if MIC_DEVICE is None else MIC_DEVICE} "
              f"(default index = {default_in})\n")
    except Exception as e:
        print(f"[speech] Could not list microphones: {e}")


class SpeechEngine:
    """
    Continuous microphone capture -> adaptive voice detection -> Whisper transcription.
    Everything runs in background threads; the game loop only calls the small public API:

        start()            load model + open microphone
        reset_round()      forget everything heard so far (call at the start of each question)
        live_text()        text so far (updates while the child is still speaking)
        take_answer()      returns the finished answer once the child has stopped talking
        busy()             True while the child is talking or the text is still being recognised
        mute()/unmute()    ignore the microphone while the game itself is speaking
        status()           (label, level) for the on-screen microphone indicator
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

    # ----- public API -----
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
        """Returns the full answer text once the child has finished speaking
        (or immediately if force=True). Returns None otherwise."""
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

    # ----- model -----
    def _build_model(self, size, device, compute):
        print(f"[speech] Loading Whisper '{size}' on {device} ({compute}) - first run downloads it...")
        model = WhisperModel(size, device=device, compute_type=compute,
                             cpu_threads=max(2, (os.cpu_count() or 4) - 1))
        # warm-up so the first real answer is not slow
        model.transcribe(np.zeros(SAMPLE_RATE, dtype=np.float32), language=WHISPER_LANGUAGE)
        return model

    def _load_model(self):
        self.model = self._build_model(WHISPER_MODEL_CPU, "cpu", "int8")

    # ----- audio capture -----
    def _audio_cb(self, indata, frames, time_info, status):
        blk = np.clip(indata[:, 0] * INPUT_GAIN, -1.0, 1.0)
        self._audio_q.put(blk.astype(np.float32))

    def _calibrate(self):
        """Measure room noise for ~1.2 s so the voice detector fits this room."""
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

    # ----- voice activity detection -----
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

            # game asked us to forget / game is talking -> drop everything
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
                    # slowly track the room noise while nobody talks
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
                    keep_tail = 6  # ~190 ms of trailing silence
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

    # ----- transcription -----
    @staticmethod
    def _prepare(audio):
        audio = audio.astype(np.float32)
        audio = audio - float(np.mean(audio))                 # remove DC offset
        peak = float(np.max(np.abs(audio))) if audio.size else 0.0
        if peak > 1e-4:
            audio = audio * min(0.9 / peak, 25.0)             # amplify quiet voices
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
                continue                                       # probably noise, not speech
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
                        print("[speech] CPU fallback successful!")
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


# ==================== Rule-based concept-coverage analysis ====================

FILLER_WORDS = {"a", "an", "the", "is", "are", "was", "it", "its", "it's", "this", "that",
                "um", "uh", "like", "i", "think", "see", "there", "here", "and", "with"}


# Common Whisper misrecognitions → correct game words
WHISPER_CORRECTIONS = {
    "city": "sitting", "kitting": "sitting", "setting": "sitting",
    "seating": "sitting", "siting": "sitting", "sitting": "sitting",
    "sleep": "sleeping", "slipping": "sleeping",
    "plain": "playing", "plane": "playing", "praying": "playing",
    "watery": "watering", "wandering": "watering", "watching": "watering",
    "kid": "kids", "child": "children",
    "kitty": "cat", "kitten": "cat",
    "puppy": "dog", "doggy": "dog",
    "share": "chair", "cheer": "chair", "care": "chair",
    "tables": "table", "desk": "table",
    "balls": "ball", "bowl": "ball",
    "plants": "plant", "flowers": "flower",
}


def normalize_words(text):
    words = [w.strip(string.punctuation) for w in text.lower().split() if w.strip(string.punctuation)]
    return [WHISPER_CORRECTIONS.get(w, w) for w in words]


def content_words(text):
    return [w for w in normalize_words(text) if w not in FILLER_WORDS]


def _stem(w):
    for suf in ("ing", "ed", "es", "s"):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[:-len(suf)]
    return w


def word_matches(word, concept):
    if word == concept:
        return True
    if len(word) < 4 or len(concept) < 4:       # short words must match exactly (avoids "cap" = "cat")
        return False
    if _stem(word) == _stem(concept):
        return True
    return difflib.SequenceMatcher(None, word, concept).ratio() >= FUZZY_THRESHOLD


def concept_present(spoken_words, concept_group):
    for concept in concept_group:
        for word in spoken_words:
            if word_matches(word, concept):
                return True
    return False


def analyze_description(spoken_text, concepts, min_words):
    """Returns (matched, missing, meets_length, full_credit)."""
    if not spoken_text:
        return [], [c[0] for c in concepts], False, False

    words = content_words(spoken_text)
    matched, missing = [], []
    for group in concepts:
        (matched if concept_present(words, group) else missing).append(group[0])

    raw_word_count = len(normalize_words(spoken_text))
    meets_length = (min_words is None) or (raw_word_count >= min_words)
    full_credit = (len(missing) == 0) and meets_length
    return matched, missing, meets_length, full_credit


# ==================== Difficulty controller (rule-based) ====================

class DifficultyController:
    def __init__(self):
        self.tier_idx = 0
        self.history = []

    @property
    def tier(self):
        return TIERS[self.tier_idx]

    def record(self, full_credit):
        self.history.append(1 if full_credit else 0)
        if len(self.history) < ROLLING_WINDOW:
            return
        acc = sum(self.history) / len(self.history)
        if acc >= PROMOTE_ACCURACY and self.tier_idx < len(TIERS) - 1:
            self.tier_idx += 1
            self.history = []
        elif acc <= DEMOTE_ACCURACY and self.tier_idx > 0:
            self.tier_idx -= 1
            self.history = []


def spawn_round(controller, previous_scene_id=None):
    scene = random.choice([s for s in SCENES if s["id"] != previous_scene_id] or SCENES)
    concepts = scene["concepts"][controller.tier]
    min_words = TIER_SETTINGS[controller.tier]["min_words"]
    prompt = TIER_PROMPTS[controller.tier]
    return scene, concepts, min_words, prompt


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

    @property
    def is_finished(self):
        if not self._finished:
            if int((time.time() - self.start_time) * self.speed) >= len(self.full_text):
                self._finished = True
        return self._finished


# ==================== Drawing ====================

COL_BG_TOP = (255, 248, 235)
COL_BG_BOTTOM = (250, 242, 225)

LEFT_X, LEFT_W = 24, 420
RIGHT_EDGE = CANVAS_W - 24


def make_gradient_background():
    bg = np.zeros((CANVAS_H, CANVAS_W, 3), dtype=np.uint8)
    top = np.array(COL_BG_TOP, dtype=np.float32)
    bottom = np.array(COL_BG_BOTTOM, dtype=np.float32)
    for y in range(CANVAS_H):
        f = y / (CANVAS_H - 1)
        bg[y, :] = (top * (1 - f) + bottom * f).astype(np.uint8)
    return cv2.cvtColor(bg, cv2.COLOR_RGB2BGR)


def render_ui(canvas, typing_anim, webcam_frame, *, tier, full_credit_count,
              total_rounds, progress, question_text, feedback_lines, live_text,
              is_correct, mic_label="", mic_level=0.0, missing_video_name=None):
    """Draws every HUD element on top of the (video) canvas. Returns the finished BGR frame."""

    base = Image.fromarray(cv2.cvtColor(canvas, cv2.COLOR_BGR2RGB)).convert("RGBA")
    layer = Image.new("RGBA", base.size, (0, 0, 0, 0))
    dl = ImageDraw.Draw(layer)

    def draw_premium_panel(box, radius=16, bg_color=(20, 20, 25, 200), outline=(255, 255, 255, 40)):
        shadow_box = [box[0] + 4, box[1] + 4, box[2] + 4, box[3] + 4]
        dl.rounded_rectangle(shadow_box, radius=radius, fill=(0, 0, 0, 100))
        dl.rounded_rectangle(box, radius=radius, fill=bg_color, outline=outline, width=1)

    # 1. Webcam (Top Right)
    tw, th = 240, 180
    tx = CANVAS_W - tw - 30
    ty = 30

    tv_pil = Image.fromarray(cv2.cvtColor(webcam_frame, cv2.COLOR_BGR2RGB)).resize((tw, th)).convert("RGBA")
    mask = Image.new("L", (tw, th), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, tw, th], radius=16, fill=255)
    tv_pil.putalpha(mask)
    layer.paste(tv_pil, (tx, ty), tv_pil)
    dl.rounded_rectangle([tx, ty, tx + tw, ty + th], radius=16, outline=(255, 255, 255, 60), width=2)

    badge_w, badge_h = 75, 28
    bx = tx + tw - badge_w - 12
    by = ty + 12
    dl.rounded_rectangle([bx, by, bx + badge_w, by + badge_h], radius=14, fill=(0, 0, 0, 160))
    dl.ellipse([bx + 10, by + 9, bx + 20, by + 19], fill=(255, 60, 60, 255))
    dl.text((bx + 28, by + 4), "LIVE", fill=(255, 255, 255, 255), font=FONT_SMALL)

    # 2. Status Panel (Top Left)
    status_w = 340
    status_h = 100
    status_box = [30, 30, 30 + status_w, 30 + status_h]
    draw_premium_panel(status_box)

    dl.text((50, 42), f"LEVEL: {tier.upper()}", fill=(200, 230, 255, 255), font=FONT_TITLE)
    accuracy = (full_credit_count / total_rounds * 100) if total_rounds else 0
    dl.text((50, 78), f"Score: {full_credit_count}/{total_rounds} ({accuracy:.0f}%)",
            fill=(220, 220, 220, 255), font=FONT_HUD)

    filled = min(3, full_credit_count)
    for i in range(3):
        pts = star_points(30 + status_w - 90 + i * 32, 60, 12, 5)
        if i < filled:
            dl.polygon(pts, fill=(255, 210, 80, 255))
        else:
            dl.polygon(pts, fill=(255, 255, 255, 40), outline=(255, 255, 255, 80))

    bar_x, bar_w = 50, status_w - 40
    bar_y, bar_h = 118, 6
    dl.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], radius=3, fill=(255, 255, 255, 40))
    fill_w = int(bar_w * max(0.0, min(1.0, progress)))
    if fill_w > 0:
        dl.rounded_rectangle([bar_x, bar_y, bar_x + fill_w, bar_y + bar_h], radius=3, fill=(100, 200, 255, 255))

    hints_box = [30, 145, 250, 180]
    draw_premium_panel(hints_box, radius=10, bg_color=(20, 20, 25, 140))
    dl.text((42, 153), "Q = Quit   F = Fullscreen", fill=(200, 200, 200, 255), font=FONT_SMALL)

    if missing_video_name:
        dl.text((42, 190), f"Video not found: {missing_video_name}", fill=(255, 80, 80, 255), font=FONT_SMALL)

    # 3. Task / AI Panel (Bottom Left)
    task_box = [30, CANVAS_H - 220, 620, CANVAS_H - 30]
    is_feedback = len(feedback_lines) > 0

    if is_feedback:
        if is_correct is True:
            panel_bg = (30, 80, 40, 210)
            panel_border = (80, 200, 100, 150)
            title_text = "Awesome!"
            title_col = (150, 255, 180, 255)
        elif is_correct is False:
            panel_bg = (90, 60, 20, 210)
            panel_border = (220, 160, 60, 150)
            title_text = "Good Try!"
            title_col = (255, 200, 100, 255)
        else:
            panel_bg = (20, 20, 25, 200)
            panel_border = (255, 255, 255, 40)
            title_text = "Feedback"
            title_col = (200, 230, 255, 255)
    else:
        panel_bg = (20, 20, 25, 200)
        panel_border = (255, 255, 255, 40)
        title_text = "AI Task"
        title_col = (100, 200, 255, 255)

    draw_premium_panel(task_box, bg_color=panel_bg, outline=panel_border)
    dl.text((50, task_box[1] + 16), title_text, fill=title_col, font=FONT_HUD)

    visible_text = typing_anim.get_visible_text()
    if visible_text:
        if is_feedback:
            lines = visible_text.split(" | ")
            tyy = task_box[1] + 50
            for wl in lines:
                wrap = _wrap_text_pil(wl, FONT_BODY, 540)
                for w in wrap:
                    dl.text((50, tyy), w, fill=(255, 255, 255, 255), font=FONT_BODY)
                    tyy += 28
        else:
            lines = _wrap_text_pil(visible_text, FONT_QUESTION, 540)
            tyy = task_box[1] + 55
            for w in lines:
                dl.text((50, tyy), w, fill=(255, 255, 255, 255), font=FONT_QUESTION)
                tyy += 38

    # 4. User Speech Panel (Bottom Right)
    user_box = [CANVAS_W - 620, CANVAS_H - 220, CANVAS_W - 30, CANVAS_H - 30]
    draw_premium_panel(user_box)
    dl.text((user_box[0] + 20, user_box[1] + 16), "You said...", fill=(150, 150, 160, 255), font=FONT_HUD)

    # microphone status + level meter
    if mic_label:
        lab_col = (120, 230, 150, 255) if mic_label.startswith(("Listening", "Ready")) else (255, 210, 120, 255)
        lw = dl.textlength(mic_label, font=FONT_SMALL)
        dl.text((user_box[2] - 20 - lw, user_box[1] + 20), mic_label, fill=lab_col, font=FONT_SMALL)
    meter_x, meter_y = user_box[0] + 20, user_box[3] - 22
    meter_w = user_box[2] - user_box[0] - 40
    dl.rounded_rectangle([meter_x, meter_y, meter_x + meter_w, meter_y + 8], radius=4, fill=(255, 255, 255, 40))
    lvl_w = int(meter_w * max(0.0, min(1.0, mic_level * 8.0)))
    if lvl_w > 0:
        dl.rounded_rectangle([meter_x, meter_y, meter_x + lvl_w, meter_y + 8], radius=4, fill=(110, 220, 140, 255))

    if live_text:
        user_lines = _wrap_text_pil(live_text, FONT_QUESTION, 560)
        if len(user_lines) > 3:
            user_lines = user_lines[-3:]
        tyy = user_box[1] + 55
        for w in user_lines:
            dl.text((user_box[0] + 20, tyy), w, fill=(255, 255, 255, 255), font=FONT_QUESTION)
            tyy += 38
    else:
        dl.text((user_box[0] + 20, user_box[1] + 55), "... waiting for your description",
                fill=(120, 120, 130, 255), font=FONT_BODY)

    base = Image.alpha_composite(base, layer)
    return cv2.cvtColor(np.array(base.convert("RGB")), cv2.COLOR_RGB2BGR)


# ==================== Session metrics ====================

class SessionMetrics:
    def __init__(self):
        self.response_times = []
        self.rounds_completed = 0
        self.full_credit_count = 0
        self.concepts_matched_total = 0
        self.concepts_possible_total = 0

    def print_summary(self):
        print("\n" + "=" * 50)
        print("DESCRIBE THE SCENE -- SESSION SUMMARY")
        print("=" * 50)
        print(f"Rounds completed:        {self.rounds_completed}")
        acc = (self.full_credit_count / self.rounds_completed * 100) if self.rounds_completed else 0
        print(f"Full-description rate:   {acc:.0f}%  ({self.full_credit_count}/{self.rounds_completed})")
        if self.concepts_possible_total:
            coverage = self.concepts_matched_total / self.concepts_possible_total * 100
            print(f"Overall concept coverage: {coverage:.0f}% "
                  f"({self.concepts_matched_total}/{self.concepts_possible_total})")
        if self.response_times:
            avg_rt = sum(self.response_times) / len(self.response_times)
            print(f"Avg response time:       {avg_rt:.1f}s")
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
        print("Speech engine not running -- rounds will time out without an answer.")

    video_index = build_video_index(ASSETS_DIR)
    print(f"Looking for videos in: {ASSETS_DIR}")
    for s in SCENES:
        found = resolve_video_path(s, video_index)
        name = os.path.basename(found) if found else "NOT FOUND (expected " + s["stems"][0] + ".mp4)"
        print(f"  [{s['id']:24}] -> {name}")

    gradient_bg = make_gradient_background()
    video = LoopingVideo(CANVAS_W, CANVAS_H)
    controller = DifficultyController()
    typing_anim = TypingAnimator()
    metrics = SessionMetrics()

    def speak(text):
        """Speaks the text. The microphone is muted while speaking so the game never hears itself."""
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

    scene, concepts, min_words, prompt = spawn_round(controller)
    video_ok = video.open(resolve_video_path(scene, video_index))
    ask_start = time.time()
    clear_speech()
    typing_anim.start(prompt)
    speak(prompt)
    state = STATE_ASKING
    feedback_lines = []
    feedback_start = None
    last_correct = None
    progress = 1.0

    while True:
        success, cam_frame = cap.read()
        if not success:
            break
        cam_frame = cv2.flip(cam_frame, 1)
        settings = TIER_SETTINGS[controller.tier]

        # ---------- game logic ----------
        if state == STATE_ASKING:
            if speech_ready and speech.muted:
                # the game is still speaking the question: the answer timer has not started yet
                ask_start = time.time()
                progress = 1.0
                spoken = None
                timed_out = False
            else:
                elapsed = time.time() - ask_start
                progress = max(0.0, 1.0 - (elapsed / settings["listen_s"]))

                # finished answer = child spoke and then paused
                spoken = speech.take_answer() if speech_ready else None

                # time is up -- but if the child is still talking, give a little extra time
                grace_over = elapsed >= settings["listen_s"] + EXTRA_GRACE_S
                still_talking = speech_ready and speech.busy()
                timed_out = elapsed >= settings["listen_s"] and (grace_over or not still_talking)
                if timed_out and not spoken and speech_ready:
                    spoken = speech.take_answer(force=True)

            if spoken or timed_out:
                elapsed = time.time() - ask_start
                matched, missing, meets_length, full_credit = analyze_description(spoken or "", concepts, min_words)
                metrics.response_times.append(elapsed)
                metrics.rounds_completed += 1
                metrics.concepts_matched_total += len(matched)
                metrics.concepts_possible_total += len(concepts)
                controller.record(full_credit)

                fb = []
                fb.append(f'You said: "{spoken}"' if spoken else "No description heard that time -- that's okay!")

                if full_credit:
                    metrics.full_credit_count += 1
                    fb.append("\u2B50 Great description! You covered everything!")
                    speak("Great description!")
                    last_correct = True
                    play_success_sound()
                else:
                    if matched:
                        fb.append(f"Nice, you mentioned: {', '.join(matched)}")
                    if missing:
                        fb.append(f"Can you also tell me about: {', '.join(missing)}?")
                    if min_words and not meets_length:
                        fb.append("Try describing it with a longer sentence next time!")
                    speak("Good try! Let's add a bit more next time.")
                    last_correct = False
                    play_wrong_sound()

                feedback_lines = fb
                state = STATE_FEEDBACK
                feedback_start = time.time()
                typing_anim.start(" | ".join(fb))

        else:  # STATE_FEEDBACK
            progress = 1.0
            if (time.time() - feedback_start) * 1000 >= FEEDBACK_DISPLAY_MS:
                scene, concepts, min_words, prompt = spawn_round(controller, previous_scene_id=scene["id"])
                video_ok = video.open(resolve_video_path(scene, video_index))
                ask_start = time.time()
                clear_speech()
                typing_anim.start(prompt)
                speak(prompt)
                state = STATE_ASKING
                last_correct = None
                feedback_lines = []

        # ---------- drawing ----------
        bg = video.next_frame() if video_ok else None
        canvas = (bg if bg is not None else gradient_bg).copy()

        if speech_ready:
            mic_label, mic_level = speech.status()
            live = speech.live_text()
        else:
            mic_label, mic_level, live = "Mic off", 0.0, ""

        canvas = render_ui(
            canvas, typing_anim, cam_frame,
            tier=controller.tier,
            full_credit_count=metrics.full_credit_count,
            total_rounds=metrics.rounds_completed,
            progress=progress,
            question_text=prompt,
            feedback_lines=feedback_lines if state == STATE_FEEDBACK else [],
            live_text=live,
            is_correct=last_correct if state == STATE_FEEDBACK else None,
            mic_label=mic_label,
            mic_level=mic_level,
            missing_video_name=None if video_ok else scene["stems"][0] + ".mp4",
        )

        cv2.imshow(WINDOW_NAME, canvas)
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        if key == ord('f'):
            fullscreen = not fullscreen
            cv2.setWindowProperty(WINDOW_NAME, cv2.WND_PROP_FULLSCREEN,
                                  cv2.WINDOW_FULLSCREEN if fullscreen else cv2.WINDOW_NORMAL)

    speech.stop()
    video.release()
    cap.release()
    cv2.destroyAllWindows()
    metrics.print_summary()


if __name__ == "__main__":
    main()