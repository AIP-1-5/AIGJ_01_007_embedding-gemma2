"""5단계 음성 테스트. 텍스트 질의로 음성·소리 파일을 검색한다. 저장소 루트에서 실행: python src/test_audio.py

원문과 다른 점
- 로드 후 RSS와 두 번째 실행 지연을 출력한다 (6단계 측정표용).
- 샘플은 src/make_audio.py로 만든다 (보드의 ffmpeg에 sine·anoisesrc 필터가 없음).
"""
import glob
import time

import psutil
import soundfile as sf

from eg2 import load

model = load(audio=True)
print(f"로드 후 RSS: {psutil.Process().memory_info().rss / 2**20:.0f} MB")

files = sorted(f for f in glob.glob("media/*.wav") if "/raw_" not in f)
for f in files:
    info = sf.info(f)
    assert info.samplerate == 16000 and info.channels == 1, f"{f}: 16kHz 모노가 아님"

for run in (1, 2):
    t = time.perf_counter()
    aud_emb = model.encode([{"audio": f} for f in files], normalize_embeddings=True)
    print(f"[{run}회] 오디오 {len(files)}개: {(time.perf_counter()-t)*1000:.0f} ms")

queries = ["덥다고 냉방을 요청하는 목소리", "날카로운 경보음", "웅웅거리는 배경 소음"]
q = model.encode(queries, prompt_name="SearchQuery", normalize_embeddings=True)

sim = q @ aud_emb.T
for qi, row in zip(queries, sim):
    best = row.argmax()
    print(f"{qi} -> {files[best].split('/')[-1]} ({row[best]:.3f})  전체 {dict(zip([f.split('/')[-1] for f in files], row.round(3)))}")
print(f"최종 RSS: {psutil.Process().memory_info().rss / 2**20:.0f} MB")
