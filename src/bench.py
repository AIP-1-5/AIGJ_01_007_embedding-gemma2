"""6단계 성능 측정 (원문에 없는 스크립트: 원문은 각 테스트를 돌리며 tegrastats를 손으로 읽는다).
구성 하나를 올려 같은 입력을 두 번 encode하고, 원문 기준대로 두 번째 값을 지연으로 쓴다.
저장소 루트에서: python src/bench.py text|image|video|audio|full

출력 한 줄(JSON): 구성, 로드 시간, 로드 후 RSS, GPU 할당 최대, 1·2회 지연.
GPU 사용률은 bench_all.sh가 tegrastats로 따로 잰다.
"""
import json
import sys
import time

import av
import glob
import numpy as np
import psutil
import torch

from eg2 import load

cfg = sys.argv[1]
TEXT = ["수업 중에 졸리고 머리가 맑지 않아요", "여름에 냉방 몇 도로 맞춰야 하나요?"]   # 3단계 질의 2개
IMAGES = sorted(glob.glob("media/*.jpg"))
WAVS = sorted(f for f in glob.glob("media/*.wav") if "/raw_" not in f)


def video_frames(path="media/clip.mp4", fps=1.0):   # 4단계와 같은 1 fps 우회 (torchcodec 없음)
    c = av.open(path)
    s = c.streams.video[0]
    step = max(1, round(float(s.average_rate or 15) / fps))
    out = np.stack([f.to_ndarray(format="rgb24") for i, f in enumerate(c.decode(s)) if i % step == 0])
    c.close()
    return out


def inputs():
    if cfg == "text":
        return "질의 2개", lambda m: m.encode(TEXT, prompt_name="SearchQuery", normalize_embeddings=True)
    if cfg == "image":
        return f"이미지 {len(IMAGES)}장", lambda m: m.encode([{"image": p} for p in IMAGES], normalize_embeddings=True)
    if cfg == "video":
        v = video_frames()
        return f"동영상 10초 ({len(v)}프레임)", lambda m: m.encode({"video": v}, normalize_embeddings=True)
    if cfg == "audio":
        return f"WAV {len(WAVS)}개", lambda m: m.encode([{"audio": f} for f in WAVS], normalize_embeddings=True)
    if cfg == "full":
        v = video_frames()
        def mixed(m):
            m.encode(TEXT, prompt_name="SearchQuery", normalize_embeddings=True)
            m.encode([{"image": p} for p in IMAGES], normalize_embeddings=True)
            m.encode({"video": v}, normalize_embeddings=True)
            return m.encode([{"audio": f} for f in WAVS], normalize_embeddings=True)
        return f"혼합 (질의 2 + 이미지 {len(IMAGES)} + 동영상 1 + WAV {len(WAVS)})", mixed
    sys.exit("text|image|video|audio|full")


desc, run = inputs()
t = time.perf_counter()
model = load(vision=cfg in ("image", "video", "full"), audio=cfg in ("audio", "full"))
load_s = time.perf_counter() - t
rss_load = psutil.Process().memory_info().rss / 2**20
lat = []
for _ in range(2):
    torch.cuda.synchronize()
    t = time.perf_counter()
    run(model)
    torch.cuda.synchronize()   # 1단계: GPU는 비동기라 동기화 없이 재면 짧게 찍힌다
    lat.append((time.perf_counter() - t) * 1000)
print(json.dumps({
    "config": cfg, "input": desc, "load_s": round(load_s, 1), "rss_after_load_mb": round(rss_load),
    "gpu_alloc_peak_mb": round(torch.cuda.max_memory_allocated() / 2**20),
    "rss_final_mb": round(psutil.Process().memory_info().rss / 2**20),
    "latency_ms": [round(x) for x in lat],
}, ensure_ascii=False))
