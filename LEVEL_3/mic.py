# mic_test.py - find out WHY speech is not recognised
# Run:  python mic_test.py
import sys
import numpy as np
import sounddevice as sd

SR = 16000
SECONDS = 6

print("\nInput devices:")
for i, d in enumerate(sd.query_devices()):
    if d.get("max_input_channels", 0) > 0:
        print(f"  [{i}] {d['name']}")

choice = input("\nType the device number to test (Enter = default): ").strip()
device = int(choice) if choice else None

print(f"\nSpeak a sentence NOW for {SECONDS} seconds, e.g. 'The cat is sitting on the chair'...")
audio = sd.rec(int(SECONDS * SR), samplerate=SR, channels=1, dtype="float32", device=device)
sd.wait()
audio = audio[:, 0]

peak = float(np.max(np.abs(audio)))
rms = float(np.sqrt(np.mean(audio ** 2)))
blocks = audio[: len(audio) // 512 * 512].reshape(-1, 512)
block_rms = np.sqrt(np.mean(blocks ** 2, axis=1))
noise = float(np.percentile(block_rms, 10))
loud = float(np.percentile(block_rms, 95))

print(f"\nPeak level      : {peak:.4f}")
print(f"Average level   : {rms:.4f}")
print(f"Background noise: {noise:.4f}")
print(f"Voice level     : {loud:.4f}")

if peak < 0.01:
    print("\n>>> PROBLEM: the microphone is almost SILENT. Windows is blocking it or the volume is ~0.")
    print("    Fix: Settings > Privacy & security > Microphone > allow apps + desktop apps,")
    print("    then Sound settings > Input > pick the mic > set volume to 100.")
elif loud < 0.03:
    print("\n>>> PROBLEM: the microphone is VERY QUIET (needs a higher INPUT_GAIN or Windows boost).")
elif loud < noise * 2.5:
    print("\n>>> PROBLEM: voice is barely louder than the background noise. Move closer / use another mic.")
else:
    print("\n>>> Microphone level looks OK.")

print("\nLoading Whisper (small) to test recognition...")
from faster_whisper import WhisperModel
model = WhisperModel("small", device="cpu", compute_type="int8")

a = audio - float(np.mean(audio))
p = float(np.max(np.abs(a)))
if p > 1e-4:
    a = a * min(0.9 / p, 25.0)
segs, info = model.transcribe(a.astype(np.float32), language="en", beam_size=5,
                              vad_filter=False, condition_on_previous_text=False)
text = " ".join(s.text.strip() for s in segs).strip()
print(f"\nWhisper heard: {text!r}")
if not text:
    print(">>> Whisper heard nothing -> the audio itself is the problem (device / Windows settings).")