import whisper
import argparse
from contextlib import contextmanager
import time
import librosa

def parse_args():
    parser = argparse.ArgumentParser(description='Transcribe audio using Whisper')
    parser.add_argument(
        '-f', '--file',
        type=str,
        required=True,
        help='Path to the audio file to transcribe'
    )
    return parser.parse_args()

@contextmanager
def timer(description):
    start = time.time()
    yield
    elapsed = time.time() - start
    print(f"⏲  [{description}] {elapsed:.2f}s")

@timer("Overall")
def main():
    args = parse_args()

    with timer("Loading model"):
        model = whisper.load_model("turbo")

    with timer("Transcribing"):
        result = model.transcribe(args.file)
        print(result["text"])

    with timer("Get mp3 file duration"):
        duration = librosa.get_duration(path=args.file)
        print(f"file duration= {duration:.2f}s")


if __name__ == "__main__":
    main()
