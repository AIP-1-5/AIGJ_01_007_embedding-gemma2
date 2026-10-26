"""9단계 판정 로직 오프라인 검증 — 카메라·YOLO·GPU 없이 합성 관절 좌표로 규칙을 확인한다.
사용법 (저장소 루트, 보드 또는 맥): CUDA_VISIBLE_DEVICES= ~/eg2/bin/python src/test_pose_logic.py
YOLO는 가짜 모듈로 바꾸고, GRU는 무작위 가중치로 저장·불러오기 형식만 확인한다(학습 아님)."""
import ast, csv, os, sys, tempfile, types
import numpy as np

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, f"{REPO}/src")
fake = types.ModuleType("ultralytics")
fake.YOLO = lambda *a, **k: None
sys.modules["ultralytics"] = fake
tmp = tempfile.mkdtemp()
rec_path = f"{tmp}/wave.csv"
os.chdir(tmp)
sys.argv = ["pose_app.py", "--behavior", "--record", rec_path]
import pose_app as P
import pose_model as PM
for _n in ("EAR_L", "EAR_R", "EYE_L", "EYE_R"): setattr(P, _n, getattr(PM, _n))
from pose_model import N_FEAT, PoseGRU, load_model, predict
import torch

results = []
def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))

def person(cx=640, cy=300, sw=100, lw=None, rw=None, face=True, yaw=0.0):
    """정면에 선 사람. lw/rw = 손목 (x, y). yaw: 코를 귀 사이에서 옮긴 비율"""
    k = np.zeros((17, 3), np.float32)
    k[:, 2] = 0.9
    k[P.LS, :2] = (cx + sw / 2, cy); k[P.RS, :2] = (cx - sw / 2, cy)   # 이미지상 좌우
    k[11, :2] = (cx + 40, cy + 2.5 * sw); k[12, :2] = (cx - 40, cy + 2.5 * sw)
    k[7, :2] = (cx + sw / 2 + 10, cy + 0.8 * sw); k[8, :2] = (cx - sw / 2 - 10, cy + 0.8 * sw)
    k[P.LW, :2] = lw if lw is not None else (cx + sw / 2 + 10, cy + 1.5 * sw)
    k[P.RW, :2] = rw if rw is not None else (cx - sw / 2 - 10, cy + 1.5 * sw)
    ear = 0.35 * sw
    k[P.EAR_L, :2] = (cx + ear, cy - 0.8 * sw); k[P.EAR_R, :2] = (cx - ear, cy - 0.8 * sw)
    k[P.EYE_L, :2] = (cx + 0.15 * sw, cy - 0.9 * sw); k[P.EYE_R, :2] = (cx - 0.15 * sw, cy - 0.9 * sw)
    k[P.NOSE, :2] = (cx + yaw * 2 * ear, cy - 0.85 * sw)
    if not face:
        k[P.NOSE, 2] = 0.1
    return k

# ---- 1. 한 프레임 자세 규칙 ----
k = person(); b = P.body(k)
check("기본 자세 → 기본", P.pose_label(k, b) == "기본", P.pose_label(k, b))
up_l, up_r = (700, 150), (580, 150)
check("두 손목 위 → 만세", P.pose_label(person(lw=up_l, rw=up_r), b) == "만세")
check("한 손목 위 → 한팔들기", P.pose_label(person(lw=up_l), b) == "한팔들기")
check("어깨 안 보임 → body None", P.body(np.zeros((17, 3), np.float32)) is None)
check("정면 facing ≈ 1", P.facing_score(person()) > 0.95, f"{P.facing_score(person()):.3f}")
f_side = P.facing_score(person(yaw=0.3))
check("고개 돌림(yaw 0.3) → FACE_TH 미만", f_side < P.FACE_TH, f"{f_side:.3f}")

# ---- 2. 손 흔들기 (1.5초, 손목 x 좌우 반복) ----
t0 = 1000.0
wave = [(t0 + i / 15, 0.6 + 0.3 * np.sign(np.sin(i / 15 * 2 * np.pi * 2))) for i in range(22)]
still = [(t0 + i / 15, 0.6 + 0.01 * i) for i in range(22)]
check("좌우 2 Hz 흔들기 → is_wave True", P.is_wave(wave))
check("손 올리고 정지 → is_wave False", not P.is_wave(still))
check("7프레임 미만 → False", not P.is_wave(wave[:7]))

# ---- 3. 깜빡임: raw vs smooth (update_person 경로) ----
def run_sequence(mode, frames, tid):
    P.MODE = mode
    P.events.clear(); P.counts.clear()
    for t, kk in frames:
        P.update_person(tid, kk, t)
    return dict(P.counts)

flick = []
t = 2000.0
for i in range(45):                      # 3초 한팔들기, 관절 잡음으로 3프레임마다 1프레임 손목이 내려감
    lw = up_l if i % 3 else (700, 270)   # 어깨선 근처 → 기본으로 판정
    flick.append((t + i / 15, person(lw=lw)))
for i in range(30):
    flick.append((t + 3 + i / 15, person()))
raw_c = run_sequence("raw", flick, 1)
P.tracks.clear()
sm_c = run_sequence("smooth", flick, 2)
check("raw: 한팔들기 1회 동작이 여러 번 셈", raw_c.get("한팔들기", 0) > 1, str(raw_c))
check("smooth: 한팔들기 1회로 셈", sm_c.get("한팔들기", 0) == 1, str(sm_c))

P.tracks.clear()
wave_frames = []
for i in range(45):
    x = 700 + 40 * np.sign(np.sin(i / 15 * 2 * np.pi * 1.5))
    wave_frames.append((3000 + i / 15, person(lw=(x, 150))))
wv = run_sequence("smooth", wave_frames, 3)
wv_raw = (P.tracks.clear(), run_sequence("raw", wave_frames, 4))[1]
check("smooth: 손 흔들기 → 손흔들기 이벤트", wv.get("손흔들기", 0) >= 1, str(wv))
check("raw: 손 흔들기는 한팔들기로만", "손흔들기" not in wv_raw, str(wv_raw))

# ---- 4. 행동 패턴 ----
def behave(frames_fn, n, fps=10):
    P.tracks.clear(); P.MODE = "smooth"
    st = None
    for i in range(n):
        t = 5000 + i / fps
        st = P.update_person(9, frames_fn(i, i / fps), t)
    return st["bstate"], st["best"], round(st["look"], 1)

passing = behave(lambda i, s: person(cx=200 + 150 * s, face=False), 40)
glance = behave(lambda i, s: person(cx=200 + 150 * s, face=(1.0 <= s < 3.0)), 45)
interest = behave(lambda i, s: person(), 60)
linger = behave(lambda i, s: person(face=False), 120)
check("지나감 (이동, 정면 없음)", passing[1] == "지나감", str(passing))
check("힐끗 봄 (이동, 정면 2초)", glance[1] == "힐끗 봄", str(glance))
check("관심 있음 (정지, 정면 6초)", interest[1] == "관심 있음", str(interest))
check("머무름 (정지, 옆 보기 12초)", linger[1] == "머무름", str(linger))

# ---- 5. 악수 ----
a = person(cx=500, rw=None, lw=(600, 400)); bb = person(cx=720, rw=(610, 400))
P.pairs.clear()
f = P.handshake_pairs(np.stack([a, bb]), [1, 2], 6000.0)
check("손목 10px, 가슴 높이 → 악수 후보", P.pairs[(1, 2)][-1][1], str(list(P.pairs[(1, 2)])))
far = person(cx=900)
P.pairs.clear(); P.handshake_pairs(np.stack([a, far]), [1, 3], 6000.0)
check("멀리 떨어진 두 사람 → 후보 아님", not P.pairs[(1, 3)][-1][1])

# ---- 6. --record CSV → train_pose.load_sequences 형식 호환 ----
P.rec_f.flush()
rows = list(csv.reader(open(rec_path)))
check("CSV 열 수 = 5 + 51", all(len(r) == 56 for r in rows), f"{len(rows)}행, 열 {set(map(len, rows))}")
src = open(f"{REPO}/src/train_pose.py").read()
fn = next(n for n in ast.parse(src).body if isinstance(n, ast.FunctionDef) and n.name == "load_sequences")
ns = {"np": np, "csv": csv, "collections": __import__("collections"), "args": types.SimpleNamespace(window=30)}
exec(compile(ast.Module([fn], []), "train_pose", "exec"), ns)
seqs = ns["load_sequences"](rec_path)
check("load_sequences 특징 차원 = N_FEAT", seqs and all(s.shape[1] == N_FEAT for s in seqs),
      f"{len(seqs)}개 시퀀스, shape {[s.shape for s in seqs][:4]}")

# ---- 7. 체크포인트 저장 형식 → load_model/predict (CPU, 무작위 가중치, 학습 아님) ----
m = PoseGRU(N_FEAT, 3, 64)
ck_path = f"{tmp}/fake.pt"
torch.save({"state": m.state_dict(), "labels": ["idle", "wave", "clap"], "task": "action", "window": 30,
            "hidden": 64, "mean": [0.0] * N_FEAT, "std": [1.0] * N_FEAT}, ck_path)
ck = load_model(ck_path, device="cpu")
lab, p = predict(ck, np.random.randn(30, N_FEAT).astype(np.float32))
check("load_model/predict 동작", lab in ck["labels"] and 0 <= p <= 1, f"{lab} {p:.3f}")
check("BEH_RANK에 영문 행동 라벨 없음 (원문 동일)", "interested" not in P.BEH_RANK,
      "모델 라벨 passing/glance/interested는 BEH_RANK.get(…, 1)로 모두 1 → best가 첫 라벨에 고정될 수 있음")

ok = sum(r[1] for r in results)
for name, passed, detail in results:
    print(f"{'PASS' if passed else 'FAIL'}  {name}  {detail}")
print(f"\n{ok}/{len(results)} 통과")
