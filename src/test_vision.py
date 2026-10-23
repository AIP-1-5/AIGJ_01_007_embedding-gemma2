"""4단계 영상 테스트. 텍스트 질의로 이미지·동영상을 검색한다. 저장소 루트에서 실행: python src/test_vision.py

원문과 다른 점
- 로드 후 프로세스 RSS를 출력한다 (6단계 측정표용).
- 각 encode를 두 번 돌려 두 번째 값을 지연으로 쓴다 (원문 6단계 "두 번째 실행 값" 기준).
"""
import glob
import time

import psutil

from eg2 import load

model = load(vision=True)
print(f"로드 후 RSS: {psutil.Process().memory_info().rss / 2**20:.0f} MB")

images = sorted(glob.glob("media/*.jpg"))
for run in (1, 2):
    t = time.perf_counter()
    img_emb = model.encode([{"image": p} for p in images], normalize_embeddings=True)
    print(f"[{run}회] 이미지 {len(images)}장: {(time.perf_counter()-t)*1000:.0f} ms")

vid_emb = None
try:
    for run in (1, 2):
        t = time.perf_counter()
        vid_emb = model.encode({"video": "media/clip.mp4"}, normalize_embeddings=True)
        print(f"[{run}회] 동영상 1개: {(time.perf_counter()-t)*1000:.0f} ms")
except Exception as e:  # 원문 6단계: 디코딩 실패 시 프레임 이미지 검색으로 대체
    print("동영상 실패:", type(e).__name__, str(e)[:200])

queries = ["사람이 없는 빈 강의실", "학생들이 앉아 수업을 듣는 모습", "화이트보드에 쓴 글씨"]
q = model.encode(queries, prompt_name="SearchQuery", normalize_embeddings=True)

sim = q @ img_emb.T
for qi, row in zip(queries, sim):
    order = row.argsort()[::-1][:3]
    print(qi, "->", [(images[i].split('/')[-1], round(float(row[i]), 3)) for i in order])

if vid_emb is not None:
    print("질의-동영상 유사도:", (q @ vid_emb).round(3))
print(f"최종 RSS: {psutil.Process().memory_info().rss / 2**20:.0f} MB")
