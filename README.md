# whisk

Friendly UI/CLI for OpenAI Whisper tool.


UI version:
```
$ python src/ui.py
```


CLI version
```
$ python src/cli.py -f kyle.mp3
⏲  [Loading model] 0.40s
/Users/kfritz/.local/share/mise/installs/python/3.10.16/lib/python3.10/site-packages/whisper/transcribe.py:126: UserWarning: FP16 is not supported on CPU; using FP32 instead
warnings.warn("FP16 is not supported on CPU; using FP32 instead")
Hello, this is a test of the whisper system. I just wanted to see if I can record myself and then turn it back into text. So here's some words. This is the online voice recorder, our voice recorder is convenient and simple online tool. You can use it right in your browser to allow you to record your voice using a microphone and save it to an mp3 file.
⏲  [Transcribing] 0.85s
file duration= 21.02s
⏲  [Get mp3 file duration] 0.67s
⏲  [Overall] 1.93s
```

## Setup Instructions

```bash
pip install -r requirements.txt
```
