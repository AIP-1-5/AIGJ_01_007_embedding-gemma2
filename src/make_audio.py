"""5단계 테스트 소리 만들기 → media/speech.wav, beep.wav, noise.wav (16 kHz 모노). 저장소 루트에서 실행.

원문과 다른 점
- 원문은 espeak-ng(apt, sudo 필요)로 한국어 합성음을 만든다. 보드에 없어서 gTTS(pip)로 만든다.
  gTTS는 문장을 Google 번역 TTS로 보내 MP3를 받는다 (인터넷 필요, 고정 문장만 보낸다).
  gTTS는 click<8.2를 요구해 huggingface_hub(click>=8.4.2)와 충돌한다. 잠깐 설치하고 바로 지운다:
    pip install -c ~/eg2/torch-pin.txt gTTS && python src/make_audio.py
    pip uninstall -y gTTS && pip install -c ~/eg2/torch-pin.txt "click>=8.4.2"
- 원문은 ffmpeg의 sine·anoisesrc 필터로 경보음·잡음을 만든다. 보드 ffmpeg(NVIDIA 최소 빌드)에 없어서 numpy로 만든다.
- 16 kHz 모노 변환은 ffmpeg 대신 librosa로 한다 (원문: ffmpeg -ar 16000 -ac 1).
"""
import io
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

SR = 16000
OUT = Path("media")
OUT.mkdir(exist_ok=True)
rng = np.random.default_rng(0)

# 한국어 합성 음성 (원문과 같은 문장)
from gtts import gTTS

buf = io.BytesIO()
gTTS("강의실이 너무 덥습니다. 에어컨을 켜 주세요.", lang="ko").write_to_fp(buf)
(OUT / "raw_speech.mp3").write_bytes(buf.getvalue())
speech, _ = librosa.load(OUT / "raw_speech.mp3", sr=SR, mono=True)
sf.write(OUT / "speech.wav", speech, SR)

# 경보음: 1 kHz 사인파 3초 (원문: sine=frequency=1000:duration=3)
t = np.arange(3 * SR) / SR
sf.write(OUT / "beep.wav", (0.5 * np.sin(2 * np.pi * 1000 * t)).astype(np.float32), SR)

# 핑크 잡음 5초 (원문: anoisesrc=color=pink:duration=5). 백색 잡음 스펙트럼을 1/sqrt(f)로 깎는다.
n = 5 * SR
spec = np.fft.rfft(rng.standard_normal(n))
f = np.fft.rfftfreq(n, 1 / SR)
spec[1:] /= np.sqrt(f[1:])
pink = np.fft.irfft(spec, n)
sf.write(OUT / "noise.wav", (0.5 * pink / np.abs(pink).max()).astype(np.float32), SR)

for p in sorted(OUT.glob("*.wav")):
    info = sf.info(p)
    print(p.name, info.samplerate, info.channels, f"{info.duration:.1f}s")
