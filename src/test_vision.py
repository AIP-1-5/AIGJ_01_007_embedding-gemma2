"""4단계 영상 테스트. 텍스트 질의로 이미지·동영상을 검색한다. 저장소 루트에서 실행: python src/test_vision.py

원문과 다른 점
- 로드 후 프로세스 RSS를 출력한다 (6단계 측정표용).
- 각 encode를 두 번 돌려 두 번째 값을 지연으로 쓴다 (원문 6단계 "두 번째 실행 값" 기준).
- 동영상: transformers 5.20은 영상 디코딩에 torchcodec을 요구하는데, 보드 FFmpeg(NVIDIA 최소 빌드)에
  libswscale이 없어 torchcodec이 로드되지 않는다. {"video": 경로}가 실패하면 PyAV로 1 fps(모델 기본 샘플링)
  프레임을 뽑아 배열로 넘긴다. 원문의 대안("프레임을 이미지로 입력")과 달리 영상 임베딩 하나로 유지된다.
"""
import glob
import time

import av
import numpy as np
import psutil

from eg2 import load

model = load(vision=True)
print(f"로드 후 RSS: {psutil.Process().memory_info().rss / 2**20:.0f} MB")

images = sorted(glob.glob("media/*.jpg"))
for run in (1, 2):
    t = time.perf_counter()
    img_emb = model.encode([{"image": p} for p in images], normalize_embeddings=True)
    print(f"[{run}회] 이미지 {len(images)}장: {(time.perf_counter()-t)*1000:.0f} ms")


def video_frames(path, fps=1.0):
    """PyAV로 디코딩해 초당 fps장만 남긴다 (프레임 번호 기준)."""
    c = av.open(path)
    s = c.streams.video[0]
    step = max(1, round(float(s.average_rate or 15) / fps))
    frames = [f.to_ndarray(format="rgb24") for i, f in enumerate(c.decode(s)) if i % step == 0]
    c.close()
    return np.stack(frames)


video = "media/clip.mp4"
try:
    model.encode({"video": video}, normalize_embeddings=True)
    print("동영상 입력: 파일 경로 (torchcodec)")
except ImportError as e:
    print("동영상 입력: PyAV 1fps 프레임 배열 (torchcodec 사용 불가:", str(e)[:60], ")")
    video = video_frames(video)
    print("  프레임", video.shape)

for run in (1, 2):
    t = time.perf_counter()
    vid_emb = model.encode({"video": video}, normalize_embeddings=True)
    print(f"[{run}회] 동영상 1개: {(time.perf_counter()-t)*1000:.0f} ms")

queries = ["사람이 없는 빈 강의실", "학생들이 앉아 수업을 듣는 모습", "화이트보드에 쓴 글씨",
           "물건을 넣어 두는 사물함", "컴퓨터 모니터 화면"]   # 뒤 2개는 원문에 없음: 우리가 찍은 장면(사물함·모니터) 확인용
q = model.encode(queries, prompt_name="SearchQuery", normalize_embeddings=True)

sim = q @ img_emb.T
for qi, row in zip(queries, sim):
    order = row.argsort()[::-1][:3]
    print(qi, "->", [(images[i].split('/')[-1], round(float(row[i]), 3)) for i in order])

print("질의-동영상 유사도:", (q @ vid_emb).round(3))
print("이미지-동영상 유사도:", dict(zip([p.split('/')[-1] for p in images], (img_emb @ vid_emb).round(3))))
print(f"최종 RSS: {psutil.Process().memory_info().rss / 2**20:.0f} MB")
