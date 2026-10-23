"""3단계 텍스트 테스트. 한국어 질의가 알맞은 문서를 1위로 찾는지, 차원(768/256/128)별로 본다.

--no-prompt: prompt_name을 빼고 돌린다 (원문 변형 과제, 점수 차이 비교용).
원문과 다른 점: 로드 후 RSS(6단계 측정표용)와 1위-2위 점수 차이를 함께 출력한다.
"""
import sys
import time

import psutil

from eg2 import load

use_prompt = "--no-prompt" not in sys.argv
model = load()  # 텍스트 전용
print(f"로드 후 RSS: {psutil.Process().memory_info().rss / 2**20:.0f} MB")

docs = [
    "환기가 부족하면 강의실 CO2 농도가 1000ppm을 넘어 집중력이 떨어진다.",
    "에어컨 설정 온도는 하계 26도, 동계 20도가 권장된다.",
    "조도가 300lux 미만이면 필기 작업 시 눈의 피로가 커진다.",
    "Jetson Orin Nano는 67 TOPS의 AI 성능을 제공한다.",
]
queries = ["수업 중에 졸리고 머리가 맑지 않아요", "여름에 냉방 몇 도로 맞춰야 하나요?"]

d = model.encode(docs, prompt_name="Document" if use_prompt else None,
                 normalize_embeddings=True)

print("prompt:", "on" if use_prompt else "off")
for dim in [768, 256, 128]:
    t = time.perf_counter()
    q = model.encode(queries, prompt_name="SearchQuery" if use_prompt else None,
                     truncate_dim=dim, normalize_embeddings=True)
    ms = (time.perf_counter() - t) * 1000
    dd = d[:, :dim]
    dd = dd / (dd ** 2).sum(1, keepdims=True) ** 0.5   # 자른 뒤 재정규화
    sim = q @ dd.T
    print(f"\n[dim={dim}] {ms:.0f} ms")
    for qi, row in zip(queries, sim):
        best = row.argmax()
        second = sorted(row)[-2]
        print(f"  {qi} -> {docs[best][:25]}... ({row[best]:.3f}, 2위와 차이 {row[best] - second:.3f})")
