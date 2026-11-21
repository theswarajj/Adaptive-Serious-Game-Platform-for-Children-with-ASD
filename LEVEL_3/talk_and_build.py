# talk_and_build.py
# Standalone desktop game — Talk & Build
#
# TALK & BUILD — the child is shown a simple visual scene and asked a question about
# it, then answers using SPEECH. The system checks whether the response contains the
# expected meaning/concepts and, at higher difficulty, forms a reasonably complete
# sentence — not just a keyword. Difficulty rises from single-word answers to full
# sentences as the child succeeds.
#
# Features:
#   - Beautiful custom scene VIDEOS from NEEDS/talk_and_build/ (looping MP4)
#   - Nutmeg the Squirrel typing character with animated speech bubbles
#   - TrueType font rendering via Pillow for crisp, child-friendly text
#   - Smooth typing animation for questions and feedback
#   - Polished gradient UI with rounded panels
#
# Install:  pip install opencv-python SpeechRecognition pyaudio numpy Pillow
# Optional voice narration:  pip install pyttsx3
# Run:      python talk_and_build.py
# Quit:     press 'q' in the window

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

CANVAS_W, CANVAS_H = 1400, 780
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "NEEDS", "talk_and_build")

TV_W, TV_H = 180, 135
TV_MARGIN = 20
TV_X = CANVAS_W - TV_W - 35
TV_Y = 18

LISTEN_WINDOW_S = 18.0
FEEDBACK_DISPLAY_MS = 3200
ROLLING_WINDOW = 4
PROMOTE_ACCURACY = 0.75
DEMOTE_ACCURACY = 0.35
TIERS = ["word", "phrase", "sentence"]
MIN_SENTENCE_WORDS = 4

# ---------- Speech engine settings (tuned for child voice & local Whisper) ----------
MIC_DEVICE = None
WHISPER_MODEL_CPU = "small"
WHISPER_LANGUAGE = "en"
INITIAL_PROMPT = (
    "cat sitting chair, dog sleeping table, kids children playing ball, "
    "girl watering plant flower, red, blue, green, yellow, pink, "
    "plant, tree, book, park, school, home, beach, floor, bed, fish, bird, "
    "sitting sleeping playing watering"
)

SAMPLE_RATE = 16000
BLOCK_SIZE = 512
INPUT_GAIN = 8.0
DEBUG_SPEECH = True
MIN_RMS = 0.0015
START_MULT = 1.4
END_MULT = 1.1
START_BLOCKS = 2
PREROLL_BLOCKS = 10
END_SILENCE_S = 0.6
SETTLE_S = 0.5
MAX_UTTERANCE_S = 8.0
PARTIAL_EVERY_S = 0.5
MIN_VOICED_S = 0.2
FUZZY_THRESHOLD = 0.65

STATE_ASKING = "asking"
STATE_FEEDBACK = "feedback"

# Typing animation speed (characters per second)
TYPING_SPEED = 28

# ==================== Font Setup ====================

def _find_font(names, fallback_size=24):
    """Try to find a TrueType font from the system."""
    font_dirs = [
        "C:/Windows/Fonts",
        "/usr/share/fonts",
        "/System/Library/Fonts",
        os.path.expanduser("~/.fonts"),
    ]
    for name in names:
        for d in font_dirs:
            path = os.path.join(d, name)
            if os.path.exists(path):
                return path
    return None


def load_font(names, size):
    """Load a TrueType font, with graceful fallback."""
    path = _find_font(names)
    if path:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


# Font presets — large, bubbly, and kid-friendly
FONT_TITLE = load_font(["comicbd.ttf", "segoeprb.ttf", "segoeuib.ttf", "arialbd.ttf"], 28)
FONT_QUESTION = load_font(["comicbd.ttf", "segoeprb.ttf", "segoeuib.ttf", "arialbd.ttf"], 34)
FONT_BODY = load_font(["comic.ttf", "segoeui.ttf", "calibri.ttf", "arial.ttf"], 22)
FONT_SMALL = load_font(["comicbd.ttf", "segoeuib.ttf", "calibrib.ttf", "arialbd.ttf"], 18)
FONT_HUD = load_font(["comicbd.ttf", "segoeuib.ttf", "calibrib.ttf", "arialbd.ttf"], 24)
FONT_BUBBLE = load_font(["comic.ttf", "segoeui.ttf", "calibri.ttf"], 22)
FONT_TIER = load_font(["comicbd.ttf", "segoeuib.ttf", "arialbd.ttf"], 20)
FONT_PILL = load_font(["comicbd.ttf", "segoeuib.ttf", "arialbd.ttf"], 26)
FONT_EMOJI = load_font(["seguiemj.ttf"], 36)
FONT_EMOJI_SM = load_font(["seguiemj.ttf"], 22)


# ==================== Pillow ↔ OpenCV helpers ====================

def pil_to_cv2(pil_img):
    """Convert a Pillow RGBA/RGB image to an OpenCV BGR numpy array."""
    if pil_img.mode == "RGBA":
        arr = np.array(pil_img)
        return cv2.cvtColor(arr, cv2.COLOR_RGBA2BGRA)
    arr = np.array(pil_img.convert("RGB"))
    return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)


def cv2_to_pil(cv2_img):
    """Convert an OpenCV BGR/BGRA image to a Pillow RGB/RGBA image."""
    if cv2_img.shape[2] == 4:
        return Image.fromarray(cv2.cvtColor(cv2_img, cv2.COLOR_BGRA2RGBA))
    return Image.fromarray(cv2.cvtColor(cv2_img, cv2.COLOR_BGR2RGB))


def overlay_rgba_on_bgr(canvas, overlay_bgra, x, y):
    """Composite a BGRA overlay onto a BGR canvas at position (x, y)."""
    oh, ow = overlay_bgra.shape[:2]
    ch, cw = canvas.shape[:2]

    # Clipping
    x1 = max(0, x)
    y1 = max(0, y)
    x2 = min(cw, x + ow)
    y2 = min(ch, y + oh)
    if x1 >= x2 or y1 >= y2:
        return

    ox1 = x1 - x
    oy1 = y1 - y
    ox2 = ox1 + (x2 - x1)
    oy2 = oy1 + (y2 - y1)

    overlay_crop = overlay_bgra[oy1:oy2, ox1:ox2]
    alpha = overlay_crop[:, :, 3:4].astype(np.float32) / 255.0
    bgr = overlay_crop[:, :, :3].astype(np.float32)
    bg = canvas[y1:y2, x1:x2].astype(np.float32)
    canvas[y1:y2, x1:x2] = (bgr * alpha + bg * (1.0 - alpha)).astype(np.uint8)


# ==================== Scene + question library ====================

SCENES = [
    {
        "id": "cat_on_chair",
        "video_file": "Cat_on_a_Chair.mp4",
        "questions": {
            "word": [
                {"text": "What animal do you see?", "concepts": [["cat", "kitten"]],
                 "options": [("\U0001F431", "Cat", (90, 170, 255)), ("\U0001F436", "Dog", (255, 130, 170)),
                             ("\U0001F426", "Bird", (100, 190, 120)), ("\U0001F41F", "Fish", (255, 190, 70))]},
                {"text": "What color is the chair?", "concepts": [["red"]],
                 "options": [("\U0001F534", "Red", (230, 85, 85)), ("\U0001F535", "Blue", (90, 170, 255)),
                             ("\U0001F7E2", "Green", (100, 190, 120)), ("\U0001F7E1", "Yellow", (255, 190, 70))]},
            ],
            "phrase": [
                {"text": "What is the cat doing?", "concepts": [["sitting", "sit", "sits"]]},
            ],
            "sentence": [
                {"text": "Tell me what is happening in the video.",
                 "concepts": [["cat", "kitten"], ["sitting", "sit", "sits"], ["chair"]],
                 "min_words": MIN_SENTENCE_WORDS},
            ],
        },
    },
    {
        "id": "dog_under_table",
        "video_file": "Dog_Under_a_Table.mp4",
        "questions": {
            "word": [
                {"text": "What animal do you see?", "concepts": [["dog", "puppy"]],
                 "options": [("\U0001F436", "Dog", (90, 170, 255)), ("\U0001F431", "Cat", (255, 130, 170)),
                             ("\U0001F426", "Bird", (100, 190, 120)), ("\U0001F41F", "Fish", (255, 190, 70))]},
                {"text": "Where is the dog?", "concepts": [["table", "under"]],
                 "options": [("\U0001FA91", "Table", (90, 170, 255)), ("\U0001F6CF", "Bed", (255, 130, 170)),
                             ("\U0001FA91", "Chair", (100, 190, 120)), ("\U0001F3E0", "Floor", (255, 190, 70))]},
            ],
            "phrase": [
                {"text": "What is the dog doing?", "concepts": [["sleeping", "sleep", "sleeps"]]},
            ],
            "sentence": [
                {"text": "Tell me what is happening in the video.",
                 "concepts": [["dog", "puppy"], ["sleeping", "sleep", "sleeps"], ["table"]],
                 "min_words": MIN_SENTENCE_WORDS},
            ],
        },
    },
    {
        "id": "kids_playing_ball",
        "video_file": "Kids_Playing_Ball.mp4",
        "questions": {
            "word": [
                {"text": "What color is the ball?", "concepts": [["red"]],
                 "options": [("\U0001F534", "Red", (230, 85, 85)), ("\U0001F535", "Blue", (90, 170, 255)),
                             ("\U0001F7E2", "Green", (100, 190, 120)), ("\U0001F7E1", "Yellow", (255, 190, 70))]},
                {"text": "Where are the children?", "concepts": [["park", "outside", "grass"]],
                 "options": [("\U0001F333", "Park", (100, 190, 120)), ("\U0001F3EB", "School", (90, 170, 255)),
                             ("\U0001F3E0", "Home", (255, 130, 170)), ("\U0001F3D6", "Beach", (255, 190, 70))]},
            ],
            "phrase": [
                {"text": "What are the children doing?", "concepts": [["playing", "play", "plays"]]},
            ],
            "sentence": [
                {"text": "Tell me what is happening in the video.",
                 "concepts": [["children", "kids", "boy", "girl"], ["playing", "play"], ["ball"]],
                 "min_words": MIN_SENTENCE_WORDS},
            ],
        },
    },
    {
        "id": "girl_watering_plant",
        "video_file": "Girl_Watering_a_Plant.mp4",
        "questions": {
            "word": [
                {"text": "What is she watering?", "concepts": [["plant", "flower"]],
                 "options": [("\U0001F331", "Plant", (100, 190, 120)), ("\U0001F333", "Tree", (90, 170, 255)),
                             ("\U0001F431", "Cat", (255, 130, 170)), ("\U0001F4D6", "Book", (255, 190, 70))]},
                {"text": "What color is the watering can?", "concepts": [["blue"]],
                 "options": [("\U0001F4A7", "Blue", (90, 170, 255)), ("\U0001F338", "Pink", (255, 130, 170)),
                             ("\U0001F343", "Green", (100, 190, 120)), ("\U0001F33C", "Yellow", (255, 190, 70))]},
            ],
            "phrase": [
                {"text": "What is the girl doing?", "concepts": [["watering", "water"]]},
            ],
            "sentence": [
                {"text": "Tell me what is happening in the video.",
                 "concepts": [["girl"], ["watering", "water"], ["plant", "flower"]],
                 "min_words": MIN_SENTENCE_WORDS},
            ],
        },
    },
]


# ==================== Asset loading ====================

class SceneVideoManager:
    """Manages looping video playback for each scene.

    Each scene has its own VideoCapture. When a scene is active, we read
    frames at the video's native FPS.  When the video ends it loops from
    the beginning.
    """

    def __init__(self):
        self._caps = {}          # scene_id -> cv2.VideoCapture
        self._last_frames = {}   # scene_id -> last good BGR frame
        self._fps = {}           # scene_id -> native FPS
        self._last_read = {}     # scene_id -> timestamp of last frame read

    def load_all(self):
        """Open a VideoCapture for every scene that has a video file."""
        for scene in SCENES:
            path = os.path.join(ASSETS_DIR, scene["video_file"])
            if os.path.exists(path):
                cap = cv2.VideoCapture(path)
                if cap.isOpened():
                    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
                    self._caps[scene["id"]] = cap
                    self._fps[scene["id"]] = fps
                    self._last_read[scene["id"]] = 0.0
                    # Read the first frame as an initial thumbnail
                    ok, frm = cap.read()
                    if ok:
                        self._last_frames[scene["id"]] = frm
                    else:
                        self._last_frames[scene["id"]] = _draw_fallback_scene(scene["id"])
                    print(f"  Loaded video: {scene['video_file']} ({fps:.1f} FPS)")
                else:
                    print(f"  WARNING: Could not open video {path}, using fallback")
                    self._last_frames[scene["id"]] = _draw_fallback_scene(scene["id"])
            else:
                print(f"  WARNING: Missing {path}, using fallback")
                self._last_frames[scene["id"]] = _draw_fallback_scene(scene["id"])

    def get_frame(self, scene_id):
        """Return the current video frame for *scene_id*, advancing if needed."""
        cap = self._caps.get(scene_id)
        if cap is None:
            return self._last_frames.get(scene_id, _draw_fallback_scene(scene_id))

        fps = self._fps.get(scene_id, 30.0)
        now = time.time()
        # Only grab a new frame at roughly the video's native FPS
        if now - self._last_read.get(scene_id, 0) >= 1.0 / fps:
            ok, frm = cap.read()
            if not ok:
                # Loop — seek back to the beginning
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ok, frm = cap.read()
            if ok:
                self._last_frames[scene_id] = frm
            self._last_read[scene_id] = now

        return self._last_frames.get(scene_id, _draw_fallback_scene(scene_id))

    def release_all(self):
        """Release every open VideoCapture."""
        for cap in self._caps.values():
            cap.release()
        self._caps.clear()


def load_character_image():
    """Load the Nutmeg squirrel character image with alpha transparency."""
    clean_path = os.path.join(ASSETS_DIR, "typing_character_clean.png")
    path = clean_path if os.path.exists(clean_path) else os.path.join(ASSETS_DIR, "typing_charater.png")
    if os.path.exists(path):
        img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if img is not None:
            # Ensure BGRA
            if img.shape[2] == 3:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2BGRA)
                img[:, :, 3] = 255
            print(f"  Loaded character: {os.path.basename(path)}")
            return img
    print("  WARNING: Character image not found, using placeholder")
    return None


def _draw_fallback_scene(kind):
    """Simple drawn placeholder — basic shapes, no copyrighted art."""
    img = np.full((512, 512, 3), (235, 245, 250), dtype=np.uint8)
    if kind == "cat_on_chair":
        cv2.rectangle(img, (180, 320), (330, 460), (60, 60, 200), -1)
        cv2.ellipse(img, (255, 300), (55, 40), 0, 0, 360, (40, 130, 220), -1)
        cv2.circle(img, (255, 250), 30, (40, 130, 220), -1)
    elif kind == "dog_under_table":
        cv2.rectangle(img, (150, 260), (380, 280), (60, 90, 130), -1)
        cv2.rectangle(img, (160, 280), (175, 400), (60, 90, 130), -1)
        cv2.rectangle(img, (365, 280), (380, 400), (60, 90, 130), -1)
        cv2.ellipse(img, (255, 340), (60, 30), 0, 0, 360, (90, 110, 150), -1)
    elif kind == "kids_playing_ball":
        cv2.rectangle(img, (0, 380), (512, 512), (120, 200, 120), -1)
        cv2.circle(img, (260, 410), 20, (50, 50, 220), -1)
    elif kind == "girl_watering_plant":
        cv2.circle(img, (200, 220), 25, (240, 200, 150), -1)
        cv2.rectangle(img, (185, 245), (215, 340), (180, 100, 200), -1)
        cv2.ellipse(img, (315, 280), (30, 40), 0, 0, 360, (80, 180, 90), -1)
    return img


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


# ==================== Rule-based language analysis ====================

FILLER_WORDS = {"a", "an", "the", "is", "are", "was", "it", "its", "it's", "this", "that",
                 "um", "uh", "like", "i", "think", "see", "there", "here"}

WHISPER_CORRECTIONS = {
    "city": "sitting", "kitting": "sitting", "setting": "sitting",
    "seating": "sitting", "siting": "sitting", "sitting": "sitting",
    "sleep": "sleeping", "slipping": "sleeping", "sleeps": "sleeping",
    "plain": "playing", "plane": "playing", "praying": "playing",
    "watery": "watering", "wandering": "watering", "watching": "watering",
    "kid": "kids", "child": "children",
    "kitty": "cat", "kitten": "cat",
    "puppy": "dog", "doggy": "dog",
    "share": "chair", "cheer": "chair", "care": "chair",
    "tables": "table", "desk": "table",
    "balls": "ball", "bowl": "ball",
    "plants": "plant", "flowers": "flower",
    "read": "red", "bread": "red",
    "blew": "blue", "glue": "blue",
    "greens": "green",
    "parts": "park", "dark": "park",
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
    if len(word) < 4 or len(concept) < 4:
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


def analyze_answer(spoken_text, question):
    """Returns (matched_concepts, missing_concepts, is_complete_sentence, full_credit)."""
    if not spoken_text:
        return [], [c[0] for c in question["concepts"]], False, False

    words = content_words(spoken_text)
    matched, missing = [], []
    for group in question["concepts"]:
        if concept_present(words, group):
            matched.append(group[0])
        else:
            missing.append(group[0])

    raw_word_count = len(normalize_words(spoken_text))
    min_words = question.get("min_words")
    is_complete_sentence = (min_words is None) or (raw_word_count >= min_words)

    full_credit = (len(missing) == 0) and is_complete_sentence
    return matched, missing, is_complete_sentence, full_credit


# ==================== Difficulty controller ====================

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


# ==================== Typing Animation State ====================

class TypingAnimator:
    """Manages the typewriter-style text reveal for the character speech bubble."""

    def __init__(self):
        self.full_text = ""
        self.start_time = 0
        self.speed = TYPING_SPEED  # characters per second
        self._finished = True

    def start(self, text):
        self.full_text = text
        self.start_time = time.time()
        self._finished = False

    def get_visible_text(self):
        if self._finished:
            return self.full_text
        elapsed = time.time() - self.start_time
        chars_to_show = int(elapsed * self.speed)
        if chars_to_show >= len(self.full_text):
            self._finished = True
            return self.full_text
        return self.full_text[:chars_to_show]

    @property
    def is_finished(self):
        if not self._finished:
            elapsed = time.time() - self.start_time
            if int(elapsed * self.speed) >= len(self.full_text):
                self._finished = True
        return self._finished


# ==================== Drawing (Premium Kids Design System) ====================

_CACHED_BG = None

# Pre-computed corner masks for ultra-fast rounded video compositing
_CORNER_MASKS = {}

def _get_corner_mask(w, h, r):
    key = (w, h, r)
    if key not in _CORNER_MASKS:
        mask = Image.new("L", (w, h), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, w, h], radius=r, fill=255)
        mask_np = np.array(mask).astype(np.float32) / 255.0
        mask_3ch = np.stack([mask_np] * 3, axis=2)
        _CORNER_MASKS[key] = (
            mask_3ch[:r, :r],
            mask_3ch[:r, -r:],
            mask_3ch[-r:, :r],
            mask_3ch[-r:, -r:],
        )
    return _CORNER_MASKS[key]


def paste_rounded_frame(canvas, frame, x, y, pw, ph, radius=24):
    """Blends a frame into canvas with anti-aliased rounded corners in < 0.4ms."""
    if frame is None:
        return
    ch, cw = canvas.shape[:2]
    if x < 0 or y < 0 or x + pw > cw or y + ph > ch:
        return
    resized = cv2.resize(frame, (pw, ph))
    bg_copy = canvas[y:y+ph, x:x+pw].copy()
    canvas[y:y+ph, x:x+pw] = resized

    tl_m, tr_m, bl_m, br_m = _get_corner_mask(pw, ph, radius)
    r = radius
    canvas[y:y+r, x:x+r] = (resized[:r, :r] * tl_m + bg_copy[:r, :r] * (1.0 - tl_m)).astype(np.uint8)
    canvas[y:y+r, x+pw-r:x+pw] = (resized[:r, -r:] * tr_m + bg_copy[:r, -r:] * (1.0 - tr_m)).astype(np.uint8)
    canvas[y+ph-r:y+ph, x:x+r] = (resized[-r:, :r] * bl_m + bg_copy[-r:, :r] * (1.0 - bl_m)).astype(np.uint8)
    canvas[y+ph-r:y+ph, x+pw-r:x+pw] = (resized[-r:, -r:] * br_m + bg_copy[-r:, -r:] * (1.0 - br_m)).astype(np.uint8)


def make_gradient_background():
    """Create a magical storybook sunny sky and flower meadow background."""
    global _CACHED_BG
    if _CACHED_BG is not None:
        return _CACHED_BG.copy()

    img = Image.new("RGB", (CANVAS_W, CANVAS_H))
    draw = ImageDraw.Draw(img)

    # 1. Sky gradient: vibrant azure to soft sky cyan to warm golden horizon
    for y in range(CANVAS_H):
        f = y / CANVAS_H
        if f < 0.5:
            t = f / 0.5
            r = int(95 * (1 - t) + 140 * t)
            g = int(175 * (1 - t) + 215 * t)
            b = int(245 * (1 - t) + 252 * t)
        else:
            t = (f - 0.5) / 0.5
            r = int(140 * (1 - t) + 255 * t)
            g = int(215 * (1 - t) + 245 * t)
            b = int(252 * (1 - t) + 225 * t)
        draw.line([(0, y), (CANVAS_W, y)], fill=(r, g, b))

    # 2. Sun with radiant glow
    sun_x, sun_y = CANVAS_W - 180, 90
    for rad in range(120, 45, -15):
        overlay = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
        od = ImageDraw.Draw(overlay)
        od.ellipse([sun_x - rad, sun_y - rad, sun_x + rad, sun_y + rad], fill=(255, 235, 120, 40))
        img.paste(Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB"))

    draw = ImageDraw.Draw(img)
    draw.ellipse([sun_x - 45, sun_y - 45, sun_x + 45, sun_y + 45], fill=(255, 225, 70), outline=(255, 245, 160), width=4)

    # 3. Fluffy 3D clouds
    def draw_cloud(d, cx, cy, scale=1.0):
        blobs = [(-40, 5, 35), (-15, -15, 45), (20, -10, 40), (45, 5, 32), (0, 10, 38)]
        for ox, oy, r in blobs:
            sx, sy, sr = cx + int(ox * scale), cy + int((oy + 4) * scale), int(r * scale)
            d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(215, 235, 248))
        for ox, oy, r in blobs:
            sx, sy, sr = cx + int(ox * scale), cy + int(oy * scale), int(r * scale)
            d.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(255, 255, 255))

    draw_cloud(draw, 220, 90, 1.2)
    draw_cloud(draw, 560, 65, 0.9)
    draw_cloud(draw, 900, 110, 1.1)

    # 4. Layered rolling hills
    draw.ellipse([-150, CANVAS_H - 380, CANVAS_W // 2 + 200, CANVAS_H + 250], fill=(135, 205, 185))
    draw.ellipse([CANVAS_W // 2 - 100, CANVAS_H - 420, CANVAS_W + 350, CANVAS_H + 300], fill=(150, 218, 195))

    draw.ellipse([-250, CANVAS_H - 290, CANVAS_W // 2 + 150, CANVAS_H + 350], fill=(102, 195, 95))
    draw.ellipse([CANVAS_W // 2 - 220, CANVAS_H - 320, CANVAS_W + 280, CANVAS_H + 380], fill=(115, 210, 105))

    draw.ellipse([-100, CANVAS_H - 220, CANVAS_W + 100, CANVAS_H + 400], fill=(85, 185, 80))

    # 5. Colorful flower blossoms in foreground
    rng = np.random.RandomState(42)
    flower_colors = [(255, 255, 255), (255, 235, 100), (255, 180, 200), (180, 220, 255)]
    for _ in range(40):
        fx = rng.randint(40, CANVAS_W - 40)
        fy = rng.randint(CANVAS_H - 140, CANVAS_H - 15)
        col = flower_colors[rng.randint(len(flower_colors))]
        pr = rng.randint(4, 7)
        for ang in range(0, 360, 72):
            rad = math.radians(ang)
            px = fx + int(math.cos(rad) * pr)
            py = fy + int(math.sin(rad) * pr)
            draw.ellipse([px - 3, py - 3, px + 3, py + 3], fill=col)
        draw.ellipse([fx - 2, fy - 2, fx + 2, fy + 2], fill=(255, 160, 30))

    _CACHED_BG = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    return _CACHED_BG.copy()


def draw_3d_card(draw, box, radius, fill_color, bevel_color, outline_color=None, outline_w=2, shadow_color=(0, 0, 0, 45)):
    """Draw a tangible 3D card with soft drop shadow and bottom bevel."""
    x1, y1, x2, y2 = box
    if shadow_color:
        draw.rounded_rectangle([x1 + 4, y1 + 6, x2 + 4, y2 + 6], radius=radius, fill=shadow_color)
    draw.rounded_rectangle([x1, y1 + 4, x2, y2], radius=radius, fill=bevel_color)
    draw.rounded_rectangle([x1, y1, x2, y2 - 4], radius=radius, fill=fill_color, outline=outline_color, width=outline_w)


def draw_star(draw, cx, cy, r_out, r_in, fill_col, outline_col=None):
    """Draw a crisp 5-point star with 3D outline."""
    pts = []
    for i in range(10):
        r = r_out if i % 2 == 0 else r_in
        ang = -math.pi / 2 + i * (math.pi / 5)
        pts.append((cx + math.cos(ang) * r, cy + math.sin(ang) * r))
    draw.polygon(pts, fill=fill_col, outline=outline_col)


def _wrap_text_pil(text, font, max_width):
    """Word-wrap text to fit within max_width pixels using Pillow font metrics."""
    words = text.split()
    lines = []
    current = ""
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


def draw_scene_panel(canvas, scene_frame):
    """Draw the video panel with rounded corners, cream/golden 3D frame, and playing badge."""
    sx, sy, sw, sh = 45, 115, 640, 480
    paste_rounded_frame(canvas, scene_frame, sx, sy, sw, sh, radius=24)

    pil_img = cv2_to_pil(canvas)
    draw = ImageDraw.Draw(pil_img)

    # Frame stroke & highlight
    draw.rounded_rectangle([sx - 4, sy - 4, sx + sw + 4, sy + sh + 4], radius=26, outline=(255, 200, 70), width=4)
    draw.rounded_rectangle([sx - 1, sy - 1, sx + sw + 1, sy + sh + 1], radius=24, outline=(255, 255, 255), width=2)

    # Video playing badge
    badge_x, badge_y = sx + 18, sy + sh - 46
    draw.rounded_rectangle([badge_x, badge_y, badge_x + 145, badge_y + 30], radius=15, fill=(255, 55, 95), outline=(255, 255, 255), width=2)
    # White play triangle
    draw.polygon([(badge_x + 16, badge_y + 8), (badge_x + 28, badge_y + 15), (badge_x + 16, badge_y + 22)], fill=(255, 255, 255))
    draw.text((badge_x + 36, badge_y + 4), "PLAYING", fill=(255, 255, 255), font=FONT_SMALL)

    canvas[:] = pil_to_cv2(pil_img)[:, :, :3]


def draw_header(canvas, tier, correct_count, total_rounds, progress=1.0):
    """Draw explorer level badge with candy progress bar, and score card with golden stars."""
    pil_img = cv2_to_pil(canvas)
    draw = ImageDraw.Draw(pil_img)

    # 1. Level Explorer Banner (Top-Left)
    draw_3d_card(draw, [45, 18, 410, 96], radius=22, fill_color=(255, 95, 125), bevel_color=(210, 50, 80), outline_color=(255, 255, 255), outline_w=3)
    draw.text((68, 25), f"LEVEL: {tier.upper()}", fill=(255, 255, 255), font=FONT_TITLE)

    # Candy energy bar
    bar_x1, bar_y1, bar_x2, bar_y2 = 68, 66, 385, 82
    draw.rounded_rectangle([bar_x1, bar_y1, bar_x2, bar_y2], radius=8, fill=(180, 35, 65))
    fill_w = int((bar_x2 - bar_x1) * max(0.0, min(1.0, progress)))
    if fill_w > 8:
        draw.rounded_rectangle([bar_x1, bar_y1, bar_x1 + fill_w, bar_y2], radius=8, fill=(255, 225, 75))
        draw.rounded_rectangle([bar_x1, bar_y1, bar_x1 + fill_w, bar_y1 + 6], radius=3, fill=(255, 245, 150))

    # 2. Score & Golden Stars Card (Top-Right, left of webcam)
    draw_3d_card(draw, [720, 18, 1150, 96], radius=22, fill_color=(255, 255, 255), bevel_color=(235, 230, 220), outline_color=(255, 185, 65), outline_w=3)
    accuracy = (correct_count / total_rounds * 100) if total_rounds else 0
    draw.text((745, 34), f"Score: {correct_count}/{total_rounds} ({accuracy:.0f}%)", fill=(40, 30, 80), font=FONT_HUD)

    max_stars = 3
    filled = min(max_stars, correct_count)
    for i in range(max_stars):
        scx = 990 + i * 48
        if i < filled:
            draw_star(draw, scx, 56, 19, 9, fill_col=(255, 205, 40), outline_col=(230, 150, 20))
        else:
            draw_star(draw, scx, 56, 19, 9, fill_col=(230, 235, 245), outline_col=(195, 205, 225))

    canvas[:] = pil_to_cv2(pil_img)[:, :, :3]


def draw_mini_tv(canvas, webcam_frame):
    """Draw the webcam feed in a cute Magic Mirror frame with pulsing LIVE badge."""
    tw, th = 180, 135
    tx = CANVAS_W - tw - 35
    ty = 18
    paste_rounded_frame(canvas, webcam_frame, tx, ty, tw, th, radius=20)

    pil_img = cv2_to_pil(canvas)
    draw = ImageDraw.Draw(pil_img)

    # 3D Frame stroke
    draw.rounded_rectangle([tx - 4, ty - 4, tx + tw + 4, ty + th + 4], radius=22, outline=(155, 130, 245), width=3)
    draw.rounded_rectangle([tx - 1, ty - 1, tx + tw + 1, ty + th + 1], radius=20, outline=(255, 255, 255), width=2)

    # Floating LIVE pill badge
    draw.rounded_rectangle([tx + 10, ty + 10, tx + 85, ty + 36], radius=13, fill=(0, 0, 0, 180))
    draw.ellipse([tx + 18, ty + 17, tx + 28, ty + 27], fill=(255, 60, 60))
    draw.text((tx + 34, ty + 13), "LIVE", fill=(255, 255, 255), font=FONT_SMALL)

    canvas[:] = pil_to_cv2(pil_img)[:, :, :3]


def draw_question_area(canvas, question_text):
    """Draw the question in a warm, glossy buttercup yellow 3D card."""
    pil_img = cv2_to_pil(canvas)
    draw = ImageDraw.Draw(pil_img)

    qx, qy, qw, qh = 720, 115, 645, 175
    draw_3d_card(draw, [qx, qy, qx + qw, qy + qh], radius=28, fill_color=(255, 248, 205), bevel_color=(240, 180, 50), outline_color=(255, 195, 50), outline_w=4)

    # Mission / Question badge
    draw.rounded_rectangle([qx + 30, qy - 12, qx + 160, qy + 16], radius=14, fill=(255, 140, 30), outline=(255, 255, 255), width=2)
    draw.text((qx + 46, qy - 9), "QUESTION", fill=(255, 255, 255), font=FONT_SMALL)

    # Question text — centered, bold, large
    q_lines = _wrap_text_pil(question_text, FONT_QUESTION, qw - 60)
    line_h = 42
    total_h = len(q_lines) * line_h
    start_y = qy + (qh - total_h) // 2 + 6
    for i, line in enumerate(q_lines):
        tw = draw.textlength(line, font=FONT_QUESTION)
        tx = qx + (qw - int(tw)) // 2
        draw.text((tx, start_y + i * line_h), line, fill=(45, 30, 80), font=FONT_QUESTION)

    canvas[:] = pil_to_cv2(pil_img)[:, :, :3]


def draw_answer_hints(canvas, question):
    """Draw interactive 3D candy buttons for word tier, or challenge prompts for higher tiers."""
    options = question.get("options", [])
    pil_img = cv2_to_pil(canvas)
    draw = ImageDraw.Draw(pil_img)

    if options:
        # Word tier: 2x2 grid of squishy, tactile buttons with full-color emojis
        bx_start, by_start = 720, 308
        bw, bh = 308, 76
        gap_x, gap_y = 28, 20

        fallback_colors = [
            ((66, 165, 245), (30, 136, 229)),
            ((255, 107, 139), (224, 64, 94)),
            ((76, 175, 80), (46, 125, 50)),
            ((255, 167, 38), (245, 124, 0)),
        ]

        for i, opt in enumerate(options[:4]):
            emoji, label = opt[0], opt[1]
            col_top, col_bot = fallback_colors[i % len(fallback_colors)]

            col = i % 2
            row = i // 2
            px = bx_start + col * (bw + gap_x)
            py = by_start + row * (bh + gap_y)

            # 3D squishy button
            draw_3d_card(draw, [px, py, px + bw, py + bh], radius=bh // 2, fill_color=col_top, bevel_color=col_bot, outline_color=(255, 255, 255), outline_w=3)

            # White circular pedestal on left
            cr = 26
            cx = px + cr + 12
            cy = py + bh // 2 - 2
            draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr], fill=(255, 255, 255), outline=(240, 240, 240), width=2)

            # Emoji in full color
            try:
                draw.text((cx - 18, cy - 22), emoji, font=FONT_EMOJI, embedded_color=True)
            except Exception:
                draw.text((cx - 12, cy - 14), emoji, font=FONT_BODY, fill=(40, 30, 80))

            # Label text (bold white)
            draw.text((px + 82, py + 18), label, fill=(255, 255, 255), font=FONT_TITLE)
    else:
        # Phrase / Sentence tier: Show a story adventure helper card so screen is never empty!
        cx, cy, cw, ch = 720, 308, 645, 190
        is_sentence = question.get("min_words") is not None

        if is_sentence:
            # Sentence Challenge Card (lavender)
            draw_3d_card(draw, [cx, cy, cx + cw, cy + ch], radius=24, fill_color=(245, 243, 255), bevel_color=(196, 181, 253), outline_color=(167, 139, 250), outline_w=3)
            tag = "WHOLE STORY CHALLENGE!"
            tw_tag = int(draw.textlength(tag, font=FONT_HUD))
            draw.rounded_rectangle([cx + 25, cy + 18, cx + 25 + tw_tag + 36, cy + 56], radius=18, fill=(124, 58, 237))
            draw.text((cx + 43, cy + 23), tag, fill=(255, 255, 255), font=FONT_HUD)
            draw.text((cx + 30, cy + 72), "Include all 3 clues in your full sentence:", fill=(55, 48, 107), font=FONT_BODY)
            draw.text((cx + 30, cy + 106), "1. Who is there?   2. What are they doing?   3. Where?", fill=(109, 40, 217), font=FONT_BODY)
            draw.text((cx + 30, cy + 144), "Example: 'The dog is sleeping under the table!'", fill=(75, 85, 99), font=FONT_SMALL)
        else:
            # Phrase Challenge Card (sky blue)
            draw_3d_card(draw, [cx, cy, cx + cw, cy + ch], radius=24, fill_color=(239, 246, 255), bevel_color=(191, 219, 254), outline_color=(96, 165, 250), outline_w=3)
            tag = "DESCRIBE THE ACTION!"
            tw_tag = int(draw.textlength(tag, font=FONT_HUD))
            draw.rounded_rectangle([cx + 25, cy + 18, cx + 25 + tw_tag + 36, cy + 56], radius=18, fill=(37, 99, 235))
            draw.text((cx + 43, cy + 23), tag, fill=(255, 255, 255), font=FONT_HUD)
            draw.text((cx + 30, cy + 72), "Tell Nutmeg what the character is doing right now!", fill=(30, 58, 138), font=FONT_BODY)
            draw.text((cx + 30, cy + 112), "Example: 'The cat is sitting' or 'The kids are playing ball'", fill=(75, 85, 99), font=FONT_BODY)
            draw.text((cx + 30, cy + 148), "Speak clearly into your microphone!", fill=(37, 99, 235), font=FONT_SMALL)

    canvas[:] = pil_to_cv2(pil_img)[:, :, :3]


def draw_feedback_area(canvas, feedback_lines, is_correct, question):
    """Draw the celebration or encouragement card during feedback state."""
    pil_img = cv2_to_pil(canvas)
    draw = ImageDraw.Draw(pil_img)

    fx, fy, fw, fh = 720, 308, 645, 190

    if is_correct:
        # Celebration Card (radiant mint green)
        draw_3d_card(draw, [fx, fy, fx + fw, fy + fh], radius=24, fill_color=(236, 253, 245), bevel_color=(16, 185, 129), outline_color=(52, 211, 153), outline_w=3)
        draw.rounded_rectangle([fx + 25, fy + 18, fx + 340, fy + 56], radius=18, fill=(16, 185, 129))
        draw.text((fx + 42, fy + 23), "SUPER STAR ANSWER!", fill=(255, 255, 255), font=FONT_HUD)

        # Spoken text quote
        user_line = next((l for l in feedback_lines if "You said:" in l), "")
        if user_line:
            wrapped = _wrap_text_pil(user_line, FONT_BODY, fw - 60)
            draw.text((fx + 30, fy + 72), wrapped[0], fill=(20, 60, 40), font=FONT_BODY)

        # Concept badges with checkmarks
        concepts = [c[0] for c in question.get("concepts", [])]
        badge_x = fx + 30
        for concept in concepts[:2]:
            bw = int(draw.textlength(f"  {concept}  ", font=FONT_SMALL)) + 40
            draw.rounded_rectangle([badge_x, fy + 120, badge_x + bw, fy + 158], radius=12, fill=(209, 250, 229), outline=(16, 185, 129), width=2)
            # Green checkmark
            draw.line([(badge_x + 12, fy + 138), (badge_x + 18, fy + 146), (badge_x + 28, fy + 130)], fill=(16, 185, 129), width=3)
            draw.text((badge_x + 34, fy + 127), concept, fill=(6, 95, 70), font=FONT_SMALL)
            badge_x += bw + 18
    else:
        # Encouragement Card (warm honey peach)
        draw_3d_card(draw, [fx, fy, fx + fw, fy + fh], radius=24, fill_color=(255, 251, 235), bevel_color=(245, 158, 11), outline_color=(251, 191, 36), outline_w=3)
        draw.rounded_rectangle([fx + 25, fy + 18, fx + 340, fy + 56], radius=18, fill=(245, 158, 11))
        draw.text((fx + 42, fy + 23), "GOOD TRY! KEEP GOING!", fill=(255, 255, 255), font=FONT_HUD)

        cur_y = fy + 72
        for line in feedback_lines[:3]:
            wrapped = _wrap_text_pil(line, FONT_BODY, fw - 60)
            for wl in wrapped:
                if cur_y < fy + fh - 30:
                    draw.text((fx + 30, cur_y), wl, fill=(120, 53, 15), font=FONT_BODY)
                    cur_y += 34

    canvas[:] = pil_to_cv2(pil_img)[:, :, :3]


def draw_live_speech_panel(canvas, live_text, is_muted=False, status_label=None, mic_level=0.0):
    """Draw the Magic Microphone pod with animated EQ wave bars and spoken text."""
    pil_img = cv2_to_pil(canvas)
    draw = ImageDraw.Draw(pil_img)

    mx, my, mw, mh = 45, 620, 640, 110
    draw_3d_card(draw, [mx, my, mx + mw, my + mh], radius=24, fill_color=(255, 255, 255), bevel_color=(220, 230, 245), outline_color=(120, 180, 245), outline_w=3)

    # Magic Mic Title
    draw.text((mx + 25, my + 14), "MAGIC MIC", fill=(35, 115, 220), font=FONT_HUD)

    # Animated EQ wave bars next to title
    t = time.time()
    lvl_boost = min(1.0, mic_level * 25.0) if mic_level > 0.003 else 0.0
    for bi in range(5):
        base_h = 10 if not (live_text or lvl_boost > 0) else 24
        bounce = int(math.sin(t * 8.0 + bi * 1.3) * (6 if not (live_text or lvl_boost > 0) else (14 + int(lvl_boost * 10))))
        bar_h = max(6, min(32, base_h + bounce))
        bx_eq = mx + 185 + bi * 10
        by_eq = my + 38 - bar_h
        draw.rounded_rectangle([bx_eq, by_eq, bx_eq + 6, my + 38], radius=3, fill=(59, 130, 246))

    # Status tag pill on right
    if is_muted or (status_label and "Wait" in status_label):
        draw.rounded_rectangle([mx + mw - 225, my + 14, mx + mw - 20, my + 40], radius=13, fill=(254, 243, 199), outline=(245, 158, 11), width=2)
        draw.text((mx + mw - 212, my + 18), "• NUTMEG TALKING", fill=(180, 83, 9), font=FONT_SMALL)
    elif status_label and "Thinking" in status_label:
        draw.rounded_rectangle([mx + mw - 215, my + 14, mx + mw - 20, my + 40], radius=13, fill=(243, 232, 255), outline=(147, 51, 234), width=2)
        draw.text((mx + mw - 202, my + 18), "• THINKING...", fill=(107, 33, 168), font=FONT_SMALL)
    elif live_text or (status_label and "Listening" in status_label) or mic_level > 0.015:
        draw.rounded_rectangle([mx + mw - 215, my + 14, mx + mw - 20, my + 40], radius=13, fill=(239, 246, 255), outline=(59, 130, 246), width=2)
        draw.text((mx + mw - 202, my + 18), "• HEARING YOU!", fill=(29, 78, 216), font=FONT_SMALL)
    else:
        draw.rounded_rectangle([mx + mw - 215, my + 14, mx + mw - 20, my + 40], radius=13, fill=(236, 253, 245), outline=(16, 185, 129), width=2)
        draw.text((mx + mw - 202, my + 18), "• READY - SPEAK!", fill=(6, 95, 70), font=FONT_SMALL)

    # Live spoken text (large, clear, friendly navy)
    if live_text:
        display = f'"{live_text}"'
        lines = _wrap_text_pil(display, FONT_HUD, mw - 50)
        draw.text((mx + 25, my + 58), lines[0], fill=(25, 20, 75), font=FONT_HUD)
    else:
        draw.text((mx + 25, my + 58), "... waiting for your voice! Speak anytime!", fill=(148, 163, 184), font=FONT_BODY)

    canvas[:] = pil_to_cv2(pil_img)[:, :, :3]



def draw_character_and_bubble(canvas, char_img, typing_animator, bubble_color=None, is_correct=None):
    """Draw Nutmeg the squirrel with gentle organic breathing and a floating 3D speech bubble."""
    char_target_h = 220
    if char_img is not None:
        h, w = char_img.shape[:2]
        scale = char_target_h / h
        char_w = int(w * scale)
        char_h = char_target_h
        char_resized = cv2.resize(char_img, (char_w, char_h))

        char_x = CANVAS_W - char_w + 15
        char_y = CANVAS_H - char_h + 5

        # Gentle organic breathing bounce
        bounce = int(math.sin(time.time() * 3.5) * 3)
        char_y += bounce

        overlay_rgba_on_bgr(canvas, char_resized, char_x, char_y)
    else:
        char_x = CANVAS_W - 200
        char_y = CANVAS_H - 240
        char_w = 180

    visible_text = typing_animator.get_visible_text()
    if not visible_text:
        return

    pil_img = cv2_to_pil(canvas)
    draw = ImageDraw.Draw(pil_img)

    bubble_lines = _wrap_text_pil(visible_text, FONT_BUBBLE, 270)
    line_h = 26
    padding = 16
    bubble_w = 300
    bubble_h = len(bubble_lines) * line_h + padding * 2 + 4

    bx = char_x - bubble_w + 45
    by = char_y - bubble_h - 16

    bx = max(10, min(bx, CANVAS_W - bubble_w - 10))
    by = max(10, by)

    if is_correct is True:
        fill_col, bevel_col, border_col = (236, 253, 245), (167, 243, 208), (52, 211, 153)
        text_col = (6, 95, 70)
    elif is_correct is False:
        fill_col, bevel_col, border_col = (255, 251, 235), (253, 230, 138), (245, 158, 11)
        text_col = (120, 53, 15)
    else:
        fill_col, bevel_col, border_col = (255, 255, 255), (225, 235, 245), (180, 215, 255)
        text_col = (40, 30, 80)

    # 3D bubble body
    draw_3d_card(draw, [bx, by, bx + bubble_w, by + bubble_h], radius=20, fill_color=fill_col, bevel_color=bevel_col, outline_color=border_col, outline_w=3)

    # Pointer tail pointing down towards Nutmeg
    tail_x = min(bx + bubble_w - 45, char_x + 20)
    tail_y = by + bubble_h - 4
    draw.polygon([(tail_x, tail_y), (tail_x + 22, tail_y + 18), (tail_x + 28, tail_y)], fill=fill_col, outline=border_col)
    draw.line([(tail_x + 1, tail_y), (tail_x + 27, tail_y)], fill=fill_col, width=4)

    # Bubble text
    ty = by + padding
    for line in bubble_lines:
        draw.text((bx + padding, ty), line, fill=text_col, font=FONT_BUBBLE)
        ty += line_h

    # Blinking typing cursor
    if not typing_animator.is_finished:
        if int(time.time() * 3) % 2 == 0:
            cursor_x = bx + padding + int(draw.textlength(bubble_lines[-1], font=FONT_BUBBLE))
            draw.rectangle([cursor_x + 2, ty - line_h + 2, cursor_x + 5, ty - 4], fill=(255, 140, 30))

    canvas[:] = pil_to_cv2(pil_img)[:, :, :3]


def draw_footer_hint(canvas):
    """Draw a frosted pill hint at the bottom."""
    pil_img = cv2_to_pil(canvas)
    draw = ImageDraw.Draw(pil_img)
    hint = "Press [Q] to Quit  \u2022  Speak your answer aloud anytime!"
    tw = draw.textlength(hint, font=FONT_SMALL)
    fx = (CANVAS_W - int(tw)) // 2
    draw.rounded_rectangle([fx - 18, CANVAS_H - 36, fx + int(tw) + 18, CANVAS_H - 10], radius=13, fill=(255, 255, 255, 210), outline=(200, 220, 240), width=2)
    draw.text((fx, CANVAS_H - 33), hint, fill=(80, 95, 145), font=FONT_SMALL)
    canvas[:] = pil_to_cv2(pil_img)[:, :, :3]


# ==================== Round management ====================

def spawn_round(controller, previous_scene_id=None):
    scene = random.choice([s for s in SCENES if s["id"] != previous_scene_id] or SCENES)
    question = random.choice(scene["questions"][controller.tier])
    return scene, question


# ==================== Main Game Loop ====================

_tts_lock = threading.Lock()


def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Could not open webcam.")
        return

    if not VOICE_AVAILABLE:
        print("pyttsx3 not installed — no spoken prompts, text-only. pip install pyttsx3 to enable.")

    speech = SpeechEngine()
    speech_ready = speech.start()
    if not speech_ready:
        print("Speech engine not running — rounds will time out without an answer.")

    print("Loading scene videos from NEEDS/talk_and_build/...")
    video_mgr = SceneVideoManager()
    video_mgr.load_all()
    char_img = load_character_image()
    print("All assets ready!\n")

    gradient_bg = make_gradient_background()
    controller = DifficultyController()
    typing_anim = TypingAnimator()

    correct_count = 0
    total_rounds = 0

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

    scene, question = spawn_round(controller)
    ask_start = time.time()
    clear_speech()

    typing_anim.start(question["text"])
    speak(question["text"])
    state = STATE_ASKING
    feedback_lines = []
    feedback_start = None
    last_correct = None
    progress = 1.0
    last_spoken = ""

    while True:
        success, frame = cap.read()
        if not success:
            break
        frame = cv2.flip(frame, 1)

        canvas = gradient_bg.copy()

        # ---------- Round logic & speech checking ----------
        spoken = None
        timed_out = False
        early_correct = False

        if state == STATE_ASKING:
            if speech_ready and speech.muted:
                # Still speaking the question: timer has not started yet!
                ask_start = time.time()
                progress = 1.0
                elapsed = 0.0
            else:
                elapsed = time.time() - ask_start
                progress = max(0.0, 1.0 - (elapsed / LISTEN_WINDOW_S))

                # Real-time check: if child already said the right answer, immediately succeed without waiting!
                live_text_raw = speech.live_text().strip() if speech_ready else ""
                if live_text_raw:
                    _m, _miss, _comp, early_full = analyze_answer(live_text_raw, question)
                    if early_full:
                        spoken = live_text_raw
                        last_spoken = spoken
                        speech.reset_round()
                        early_correct = True

                if not early_correct:
                    # Finished answer = child spoke and then paused
                    spoken = speech.take_answer() if speech_ready else None

                    # Time is up -- if child is still talking, give grace
                    grace_over = elapsed >= (LISTEN_WINDOW_S + 3.0)
                    still_talking = speech_ready and speech.busy()
                    timed_out = elapsed >= LISTEN_WINDOW_S and (grace_over or not still_talking)
                    if timed_out and not spoken and speech_ready:
                        spoken = speech.take_answer(force=True)
        else:
            elapsed = 0.0
            progress = 1.0

        # Keypress checks
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        manual_submit = (state == STATE_ASKING) and (key in (ord(' '), 13))
        if manual_submit and not spoken and speech_ready:
            spoken = speech.take_answer(force=True) or (speech.live_text().strip() if speech_ready else None)

        # Check if we should transition to FEEDBACK
        if state == STATE_ASKING and (early_correct or spoken or timed_out or manual_submit):
            spoken_clean = spoken.strip() if spoken else None
            if spoken_clean:
                last_spoken = spoken_clean
            matched, missing, is_complete, full_credit = analyze_answer(spoken_clean or "", question)
            total_rounds += 1
            controller.record(full_credit)

            fb_parts = []
            if spoken_clean:
                fb_parts.append(f'You said: "{spoken_clean}"')
            else:
                fb_parts.append("No answer heard \u2014 that's okay!")

            if full_credit:
                correct_count += 1
                fb_parts.append("\U0001F31F Great answer!")
                speak("Great answer!")
                last_correct = True
                play_success_sound()
            else:
                if matched:
                    fb_parts.append(f"Good \u2014 you mentioned: {', '.join(matched)}")
                if missing:
                    fb_parts.append(f"Don't forget: {', '.join(missing)}")
                if question.get("min_words") and not is_complete:
                    fb_parts.append("Try a full sentence next time!")
                speak("Good try! Let's look at that together.")
                last_correct = False
                play_wrong_sound()

            feedback_lines = fb_parts
            state = STATE_FEEDBACK
            feedback_start = time.time()
            typing_anim.start(" | ".join(fb_parts))

        elif state == STATE_FEEDBACK:
            progress = 1.0
            if (time.time() - feedback_start) * 1000 >= FEEDBACK_DISPLAY_MS:
                scene, question = spawn_round(controller, previous_scene_id=scene["id"])
                ask_start = time.time()
                clear_speech()
                last_spoken = ""
                speak(question["text"])
                state = STATE_ASKING
                last_correct = None
                feedback_lines = []
                typing_anim.start(question["text"])

        # ── Draw all UI elements ──
        # Header with level badge + progress bar + score + stars
        draw_header(canvas, controller.tier, correct_count, total_rounds, progress)

        # Scene video frame
        scene_frame = video_mgr.get_frame(scene["id"])
        draw_scene_panel(canvas, scene_frame)

        # Webcam with ON AIR label
        draw_mini_tv(canvas, frame)

        # Live speech & mic status
        if speech_ready:
            mic_label, mic_level = speech.status()
            live = speech.live_text()
            is_muted = speech.muted
        else:
            mic_label, mic_level, live, is_muted = "Mic off", 0.0, "", False

        display_live = last_spoken if (state == STATE_FEEDBACK and last_spoken) else live

        if state == STATE_ASKING:
            draw_question_area(canvas, question["text"])
            draw_answer_hints(canvas, question)
            draw_character_and_bubble(canvas, char_img, typing_anim, is_correct=None)
            draw_live_speech_panel(canvas, display_live, is_muted=is_muted, status_label=mic_label, mic_level=mic_level)
        elif state == STATE_FEEDBACK:
            draw_question_area(canvas, question["text"])
            draw_feedback_area(canvas, feedback_lines, last_correct, question)
            draw_character_and_bubble(canvas, char_img, typing_anim, is_correct=last_correct)
            draw_live_speech_panel(canvas, display_live, is_muted=is_muted, status_label=mic_label, mic_level=mic_level)

        draw_footer_hint(canvas)

        cv2.imshow("Talk & Build", canvas)

    if speech_ready:
        speech.stop()
    video_mgr.release_all()
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()