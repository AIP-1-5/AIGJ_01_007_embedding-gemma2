"""9-6 평가: 맥에서 학습한 GRU 동작 모델을 보드에서 추론만 해서 검증 정확도와 혼동 행렬을 다시 구한다. 저장소 루트에서:
  ~/practice.sh yj ~/eg2/bin/python src/eval_pose.py --model models/action.pt --data data/action

- 검증 세트는 train_pose.py와 같은 규칙으로 만든다: 추적 ID별 시퀀스(0.5초 넘게 끊기면 분리)의 뒤 20%, 윈도 30, 보폭 5.
  train_pose.py는 Jetson에서 바로 종료하고 import 시점에 학습을 시작하므로 load_sequences를 여기 옮겨 둔다(같은 내용).
- --extra로 학습에 안 쓴 CSV(예: 1차 녹화 data/action/_trial1)를 넣으면 파일 이름을 정답으로 보고 전체 윈도를 평가한다.
- 결과: runs/pose/eval_<모델 이름>.json
"""
import argparse, collections, csv, glob, json, os, sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from pose_model import load_model, predict

ap = argparse.ArgumentParser()
ap.add_argument("--model", required=True)
ap.add_argument("--data", required=True)
ap.add_argument("--extra", nargs="*", default=[], help="학습에 안 쓴 CSV (파일 이름 = 정답)")
ap.add_argument("--val", type=float, default=0.2)
ap.add_argument("--stride", type=int, default=5)
ap.add_argument("--device", default=None)
args = ap.parse_args()

ck = load_model(args.model, args.device)
W, labels = ck["window"], ck["labels"]


def load_sequences(path):
    """train_pose.py와 같다: 추적 ID별 시간순, 0.5초 넘게 끊기면 다른 시퀀스"""
    by_tid = collections.defaultdict(list)
    with open(path) as f:
        for row in csv.reader(f):
            if len(row) != 5 + 51:
                continue
            ts, tid = float(row[0]), row[1]
            fa, spd = float(row[3]), float(row[4])
            feat = np.array([float(x) for x in row[5:]] + [fa, spd], dtype=np.float32)
            by_tid[tid].append((ts, feat))
    seqs = []
    for rows in by_tid.values():
        rows.sort(key=lambda r: r[0])
        cur = [rows[0][1]]
        for (t0, _), (t1, f) in zip(rows, rows[1:]):
            if t1 - t0 > 0.5:
                seqs.append(cur); cur = []
            cur.append(f)
        seqs.append(cur)
    return [np.stack(s) for s in seqs if len(s) >= W]


def windows(seq):
    return [seq[i:i + W] for i in range(0, len(seq) - W + 1, args.stride)]


def evaluate(items):
    """items: [(정답 라벨, 윈도)] → 정확도, 혼동 행렬, 확률 0.7 미만 비율"""
    cm = np.zeros((len(labels), len(labels)), dtype=int)
    low = 0
    for true, w in items:
        lab, p = predict(ck, w)
        cm[labels.index(true), labels.index(lab)] += 1
        low += p < 0.7                      # pose_app.py의 ML_TH: 이 아래면 앱은 모델 판정을 버리고 규칙을 쓴다
    n = int(cm.sum())
    return {"n": n, "acc": round(float(np.trace(cm)) / max(n, 1), 3), "below_ml_th": round(low / max(n, 1), 3),
            "cm": cm.tolist()}


def show(name, r):
    print(f"\n[{name}] 윈도 {r['n']}, 정확도 {r['acc']:.3f}, 확률 0.7 미만 {r['below_ml_th']:.3f}\n혼동 행렬 (행=정답, 열=예측)")
    print(" " * 14 + "".join(f"{l[:9]:>10}" for l in labels))
    for l, row in zip(labels, r["cm"]):
        if sum(row):
            print(f"{l:>13} " + "".join(f"{v:>10}" for v in row))


val = []
for p in sorted(glob.glob(os.path.join(args.data, "*.csv"))):
    lab = os.path.splitext(os.path.basename(p))[0]
    for seq in load_sequences(p):
        cut = int(len(seq) * (1 - args.val))      # train_pose.py와 같은 시간순 분할
        val += [(lab, w) for w in windows(seq[cut:])]
out = {"model": args.model, "labels": labels, "window": W, "device": ck["device"], "val": evaluate(val)}
show("검증 (각 시퀀스 뒤 20%)", out["val"])

for p in args.extra:
    lab = os.path.splitext(os.path.basename(p))[0]
    if lab not in labels:
        continue
    items = [(lab, w) for seq in load_sequences(p) for w in windows(seq)]
    if items:
        out[p] = evaluate(items)
        show(f"추가: {p}", out[p])

name = os.path.splitext(os.path.basename(args.model))[0]
os.makedirs("runs/pose", exist_ok=True)
json.dump(out, open(f"runs/pose/eval_{name}.json", "w"), ensure_ascii=False, indent=1)
