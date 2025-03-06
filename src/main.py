import whisper
import argparse
from contextlib import contextmanager
import time
import librosa
import sounddevice as sd
import soundfile as sf
import numpy as np
import tempfile
import os

def parse_args():
    parser = argparse.ArgumentParser(description='Transcribe audio using Whisper')
    parser.add_argument(
        '-f', '--file',
        type=str,
        required=False,
        help='Path to the audio file to transcribe'
    )
    parser.add_argument(
        '-d', '--duration',
        type=float,
        default=5,
        help='Recording duration in seconds (default: 5)'
    )
    return parser.parse_args()

def record_audio(wav_path, duration, samplerate=44100):
    """Record audio from microphone and save to WAV file."""
    print(f"🎤 Recording for {duration} seconds...")
    recording = sd.rec(
        int(duration * samplerate),
        samplerate=samplerate,
        channels=1,
        dtype=np.float32
    )
    sd.wait()
    print("✅ Recording finished")
    sf.write(wav_path, recording, samplerate)


@contextmanager
def timer(description):
    start = time.time()
    yield
    elapsed = time.time() - start
    print(f"⏲  [{description}] {elapsed:.2f}s")

@timer("Overall")
def main():
    args = parse_args()

    
    with tempfile.NamedTemporaryFile(suffix='.wav') as temp_wav:
        with timer("Recording"):
            record_audio(temp_wav.name, args.duration)

        with timer("Loading model"):
            model = whisper.load_model("tiny.en")

        with timer("Transcribing"):
            result = model.transcribe(temp_wav.name)
            print(result["text"])

        with timer("Get audio duration"):
            duration = sf.info(temp_wav.name).duration
            print(f"file duration= {duration:.2f}s")
    

if __name__ == "__main__":
    main()
