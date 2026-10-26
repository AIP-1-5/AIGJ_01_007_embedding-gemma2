"""8-1 남은 확인: 8단계에서 저장한 크롭으로 "세탁기" 문장 검색을 다시 잰다 (카메라 없이). 저장소 루트에서, 팀 자물쇠 안에서:
  ~/practice.sh yj ~/eg2/bin/python src/search_crops.py

원문 8-1은 앱 검색창에 "세탁기"를 입력해 라벨과 무관하게 맞는 크롭이 나오는지 본다. 실행 중 검색창을 쓰지 않아 미측정이었다.
- 크롭 벡터는 app.py와 같은 방식(이미지 입력, 512차원, 정규화)으로 다시 만든다. 질의도 같은 SearchQuery 프롬프트.
- 정답(세탁기 크롭)은 검색 전에 눈으로 정했다(docs/reports/step-08.md). 검색 결과를 보고 정답을 바꾸지 않는다.
- 결과는 runs/app/search_crops.json (크롭 이미지는 커밋하지 않는다).
"""
import glob
import json
import os
import sys
import time

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(__file__))
from eg2 import load

DIM = 512                                   # app.py와 같은 값
torch.cuda.set_per_process_memory_fraction(0.4)   # app.py와 같은 GPU 상한
GT = {"crops/yolo/000084_microwave.jpg", "crops/yolo/000090_microwave.jpg", "crops/yolo/000091_microwave.jpg",
      "crops/yolo/000092_microwave.jpg", "crops/yolo/000093_microwave.jpg", "crops/yolo/000098_microwave.jpg",
      "crops/relabel/000019_microwave.jpg", "crops/relabel/000021_laptop.jpg",
      # 10/26 yoloe: 세탁기 사진 격자 화면을 keyboard로 검출한 4개
      "crops/yoloe/000015_keyboard.jpg", "crops/yoloe/000017_keyboard.jpg",
      "crops/yoloe/000018_keyboard.jpg", "crops/yoloe/000019_keyboard.jpg"}
QUERIES = ["세탁기", "드럼 세탁기", "washing machine", "전자레인지", "컵", "휴대폰"]

paths = sorted(glob.glob("crops/yolo/*.jpg") + glob.glob("crops/relabel/*.jpg") + glob.glob("crops/yoloe/*.jpg"))
assert GT <= set(paths), f"정답 크롭 없음: {GT - set(paths)}"
emb = load(vision=True)
t = time.perf_counter()
vecs = []
for i in range(0, len(paths), 8):
    vecs.append(np.asarray(emb.encode([{"image": p} for p in paths[i:i + 8]],
                                      truncate_dim=DIM, normalize_embeddings=True), dtype=np.float32))
vecs = np.concatenate(vecs)
enc_s = time.perf_counter() - t

out = {"n_crops": len(paths), "n_gt": len(GT), "encode_s": round(enc_s, 1), "queries": {}}
for q in QUERIES:
    qv = np.asarray(emb.encode(q, prompt_name="SearchQuery", truncate_dim=DIM, normalize_embeddings=True), dtype=np.float32)
    s = vecs @ qv
    order = s.argsort()[::-1]
    top = [(paths[i], round(float(s[i]), 3)) for i in order[:10]]
    rec = {"top10": top}
    if "세탁기" in q or "washing" in q:
        ranks = sorted(int(np.where(order == paths.index(g))[0][0]) + 1 for g in GT)
        rec |= {"gt_ranks": ranks, "hit_at_n": sum(r <= len(GT) for r in ranks), "top1_is_gt": paths[order[0]] in GT,
                "best_non_gt": round(float(max(s[i] for i in range(len(paths)) if paths[i] not in GT)), 3),
                "worst_gt": round(float(min(s[paths.index(g)] for g in GT)), 3)}
    out["queries"][q] = rec
    print(f"\n[{q}]" + (f"  정답 순위 {rec['gt_ranks']}  상위{len(GT)} 적중 {rec['hit_at_n']}/{len(GT)}" if "gt_ranks" in rec else ""))
    for p, sc in top:
        print(f"  {sc:.3f}  {'*' if p in GT else ' '} {p}")

out["max_mem_mb"] = round(torch.cuda.max_memory_allocated() / 2**20)
print(f"\n크롭 {len(paths)}개 인코딩 {enc_s:.1f} s, GPU 할당 최대 {out['max_mem_mb']} MB")
os.makedirs("runs/app", exist_ok=True)
json.dump(out, open("runs/app/search_crops.json", "w"), ensure_ascii=False, indent=1)
