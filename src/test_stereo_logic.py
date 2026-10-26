"""10단계 오프라인 검증: 가상 카메라 2대로 stereo.py와 ProximityAlarm 판정을 확인한다 (카메라·모델 없음).
사용법 (저장소 루트): ~/eg2/bin/python src/test_stereo_logic.py
가상 보정 파일(cam0/1.npz)은 임시 폴더에 쓴다. calib/의 실제 보정값을 건드리지 않는다."""
import ast, json, os, sys, types
import numpy as np, cv2
import tempfile
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, f"{REPO}/src")
import stereo as S
OUT = tempfile.mkdtemp()
rng = np.random.default_rng(0)
W, H = 640, 480
K = np.array([[600., 0, 320], [0, 600., 240], [0, 0, 1]])
DIST = np.array([-0.10, 0.02, 0, 0, 0])

def look_at(C, tgt):
    f = np.asarray(tgt, float) - C; f /= np.linalg.norm(f)
    r = np.cross(f, [0, 0, 1.0]); r /= np.linalg.norm(r)
    d = np.cross(f, r)
    R = np.vstack([r, d, f]); t = -R @ C
    return R, t

def make_cam(path, C, tgt, Kc=K, dist=DIST):
    R, t = look_at(np.asarray(C, float), tgt)
    np.savez(path, K=Kc, dist=dist, R=R, t=t, res=np.array([W, H]))
    return S.load_cam(path)

def proj_dist(R, t, X, Kc=K, dist=DIST):
    rv, _ = cv2.Rodrigues(R)
    p, _ = cv2.projectPoints(np.float64(X).reshape(-1, 3), rv, t.reshape(3, 1), Kc, dist)
    return p.reshape(-1, 2)

res = {}
# --- 1. 10-1 렌즈 보정 수식: 가상 체커보드(9x6, 25mm) 20자세 → calibrateCamera가 K·dist를 되찾는지
objp = np.zeros((54, 3), np.float32); objp[:, :2] = np.mgrid[0:9, 0:6].T.reshape(-1, 2) * 0.025
obj, img = [], []
while len(img) < 20:
    rv = rng.normal(0, 0.35, 3); tv = np.array([rng.uniform(-0.15, 0.05), rng.uniform(-0.1, 0.05), rng.uniform(0.35, 0.7)])
    p, _ = cv2.projectPoints(objp.astype(np.float64), rv, tv, K, DIST)
    p = p.reshape(-1, 2)
    if p.min() < 5 or p[:, 0].max() > W - 5 or p[:, 1].max() > H - 5:
        continue
    obj.append(objp); img.append((p + rng.normal(0, 0.2, p.shape)).astype(np.float32).reshape(-1, 1, 2))
rms, K_est, d_est, _, _ = cv2.calibrateCamera(obj, img, (W, H), None, None)
res["10-1"] = {"rms_px": round(rms, 3), "fx": round(K_est[0, 0], 1), "cx": round(K_est[0, 2], 1),
               "k1": round(float(d_est.ravel()[0]), 3), "true": "fx 600, cx 320, k1 -0.100, 코너 잡음 0.2px"}

# --- 2. 배치: 앞쪽 두 모서리 높이 2.3m, 교실 중앙 쪽을 봄 (시선 교차각 기록)
C0, C1, AIM = np.array([0.3, 0.2, 2.3]), np.array([5.7, 0.2, 2.3]), np.array([3.0, 3.0, 0.8])
v0, v1 = C0[:2] - AIM[:2], C1[:2] - AIM[:2]
res["layout"] = {"cross_angle_deg": round(float(np.degrees(np.arccos(v0 @ v1 / np.linalg.norm(v0) / np.linalg.norm(v1)))), 1)}

# --- 3. 10-2 위치 보정: 원문 calib_extrinsics.solve()와 같은 solvePnP 두 번 + 검증점 삼각측량 (클릭 잡음 1px)
world = S.load_world(f"{REPO}/calib/world_points.json")
true_cams = [look_at(C0, AIM), look_at(C1, AIM)]
vis = {}
for n, (R, t) in enumerate(true_cams):
    pts = proj_dist(R, t, [p["xyz"] for p in world])
    infront = [(R @ np.array(p["xyz"]) + t)[2] > 0 for p in world]
    vis[n] = {p["id"]: uv for p, uv, f in zip(world, pts, infront) if f and 0 <= uv[0] < W and 0 <= uv[1] < H}
res["10-2_visible_example_points"] = {n: sorted(v) for n, v in vis.items()}
# 예시 기준점이 이 배치에서 다 보이지 않으면, 같은 규칙(바닥·책상·벽 높이 섞기)의 가상 기준점으로 계산한다
grid = [{"id": f"G{i}", "xyz": [x, y, z]} for i, (x, y, z) in enumerate(
    [(1.5, 2.0, 0), (4.5, 2.0, 0), (4.5, 4.5, 0), (1.5, 4.5, 0), (2.2, 3.0, 0.74), (3.8, 3.0, 0.74),
     (3.0, 5.5, 1.5), (2.0, 5.5, 1.5), (2.5, 2.5, 0), (3.5, 2.5, 0), (2.5, 3.8, 0.74), (3.5, 3.8, 0.74), (3.0, 3.3, 0)])] + [{"id": "C1", "xyz": [3.0, 2.0, 0.0], "check": True},
                                             {"id": "C2", "xyz": [3.0, 4.0, 0.74], "check": True}]
def in_both(p):
    for R, t in true_cams:
        uv = proj_dist(R, t, [p["xyz"]])[0]
        if not (0 <= uv[0] < W and 0 <= uv[1] < H):
            return False
    return True
res["10-2_grid_dropped"] = [p["id"] for p in grid if not in_both(p)]
grid = [p for p in grid if in_both(p)]
assert sum(not p.get("check") for p in grid) >= 6 and sum(bool(p.get("check")) for p in grid) == 2, res["10-2_grid_dropped"]
WMAP = {p["id"]: p for p in grid}
clicks = {}
for n, (R, t) in enumerate(true_cams):
    uv = proj_dist(R, t, [p["xyz"] for p in grid])
    clicks[str(n)] = {p["id"]: (u + rng.normal(0, 1.0, 2)).tolist() for p, u in zip(grid, uv)}
solved = {}
for n in ("0", "1"):
    ids = [i for i in clicks[n] if not WMAP[i].get("check")]
    o = np.float64([WMAP[i]["xyz"] for i in ids]); im = np.float64([clicks[n][i] for i in ids])
    ok, rvec, tvec = cv2.solvePnP(o, im, K_est, d_est, flags=cv2.SOLVEPNP_ITERATIVE)
    ok, rvec, tvec = cv2.solvePnP(o, im, K_est, d_est, rvec, tvec, True, cv2.SOLVEPNP_ITERATIVE)
    pr, _ = cv2.projectPoints(o, rvec, tvec, K_est, d_est)
    R, _ = cv2.Rodrigues(rvec)
    np.savez(f"{OUT}/cam{n}.npz", K=K_est, dist=d_est, R=R, t=tvec, res=np.array([W, H]))
    Ce = (-R.T @ tvec).ravel()
    solved[n] = {"mean_px": round(float(np.linalg.norm(pr.reshape(-1, 2) - im, axis=1).mean()), 2),
                 "pos_err_cm": round(float(np.linalg.norm(Ce - [C0, C1][int(n)])) * 100, 1)}
c0, c1 = S.load_cam(f"{OUT}/cam0.npz"), S.load_cam(f"{OUT}/cam1.npz")
for i in ("C1", "C2"):
    p0, p1 = S.undistort(c0, [clicks["0"][i]])[0], S.undistort(c1, [clicks["1"][i]])[0]
    X, _ = S.triangulate(c0, c1, p0, p1)
    solved[f"verify_{i}_cm"] = round(float(np.linalg.norm(X - WMAP[i]["xyz"])) * 100, 1)
res["10-2"] = solved

# 이후는 "실제" 카메라(true)에서 관절 픽셀을 만들고, 보정된 c0/c1으로 계산한다
def obs_px(n, X, noise):
    R, t = true_cams[n]
    return proj_dist(R, t, [X])[0] + rng.normal(0, noise, 2)

# --- 4. 10-4 삼각측량: 어깨 중심(서 1.4m / 앉음 1.0m), 관절 잡음 2px
errs, hs = [], {"섬": [], "앉음": []}
for _ in range(300):
    xy = rng.uniform([1.0, 1.5], [5.0, 5.0]); pose, h = ("섬", 1.4) if rng.random() < .5 else ("앉음", 1.0)
    X = np.array([*xy, h])
    p0 = S.undistort(c0, [obs_px(0, X, 2)])[0]; p1 = S.undistort(c1, [obs_px(1, X, 2)])[0]
    Xe, e = S.triangulate(c0, c1, p0, p1)
    errs.append(np.linalg.norm(Xe[:2] - xy)); hs[pose].append(Xe[2])
res["10-4"] = {"xy_err_cm_median": round(float(np.median(errs)) * 100, 1), "xy_err_cm_p95": round(float(np.percentile(errs, 95)) * 100, 1),
               "sit_judged_ok": f'{sum(h < 1.15 for h in hs["앉음"])}/{len(hs["앉음"])}',
               "stand_judged_ok": f'{sum(h >= 1.15 for h in hs["섬"])}/{len(hs["섬"])}'}

# --- 5. 10-5 한 카메라 추정 (H_GUESS 1.2m): 실제 어깨 높이 1.0 / 1.4m일 때 오차
single = {}
for h in (1.0, 1.2, 1.4):
    e = []
    for _ in range(200):
        xy = rng.uniform([1.0, 1.5], [5.0, 5.0])
        X = S.ray_plane(c0, S.undistort(c0, [obs_px(0, np.array([*xy, h]), 2)])[0], 1.2)
        e.append(np.linalg.norm(X[:2] - xy))
    single[f"true_h_{h}"] = {"median_m": round(float(np.median(e)), 2), "max_m": round(float(np.max(e)), 2)}
res["10-5"] = single

# --- 6. 10-3 발목 → 바닥: 발목 잡음 2px일 때 거리 오차 (카메라에서 먼 쪽)
e_near, e_far = [], []
for _ in range(200):
    for ylo, bucket in ((1.0, e_near), (4.5, e_far)):
        xy = np.array([rng.uniform(1, 5), ylo + rng.uniform(0, 0.5)])
        X = S.ray_plane(c0, S.undistort(c0, [obs_px(0, np.array([*xy, 0.08]), 2)])[0], 0.0)
        bucket.append(np.linalg.norm(X[:2] - xy))
res["10-3"] = {"ankle_err_cm_near_y1": round(float(np.median(e_near)) * 100, 1), "ankle_err_cm_far_y4.5": round(float(np.median(e_far)) * 100, 1),
               "note": "발목 높이 0.08m를 바닥(0)으로 보는 원문 가정 포함"}

# --- 7. match_people: 3명(두 명은 0.5m 간격), 카메라마다 순서 섞음
people = [np.array([2.0, 3.0, 1.4]), np.array([2.5, 3.0, 1.0]), np.array([4.0, 4.0, 1.4])]
p0 = S.undistort(c0, [obs_px(0, X, 2) for X in people])
perm = [2, 0, 1]
p1 = S.undistort(c1, [obs_px(1, people[k], 2) for k in perm])
m, r0, r1 = S.match_people(c0, c1, p0, p1)
res["match_people"] = {"pairs": [(i, perm[j] if True else j) for i, j, _, _ in m], "correct": all(i == perm[j] for i, j, _, _ in m),
                       "unmatched": [sorted(r0), sorted(r1)], "max_err_px": round(max(e for *_, e in m), 2)}

# --- 8. Kalman2D + relative_state: 카트 1.2m/s, 약 7fps, 위치 잡음 5cm, 사람은 (3,1)에 정지
kf_t, kf_p = None, S.Kalman2D((3.0, 1.0))
dt, t = 1 / 7, 0.0
start = np.array([3.0, 5.0]); vel = np.array([0, -1.2])
first_danger, first_near, v_hist = None, None, []
for k in range(60):
    t = k * dt
    true = start + vel * t
    z = true + rng.normal(0, 0.05, 2)
    if kf_t is None:
        kf_t = S.Kalman2D(z)
    else:
        kf_t.predict(dt); kf_t.update(z)
    kf_p.predict(dt); kf_p.update(np.array([3.0, 1.0]) + rng.normal(0, 0.05, 2))
    d, closing, ttc = S.relative_state(kf_p.x, kf_t.x)
    v_hist.append((round(t, 2), round(float(np.linalg.norm(kf_t.x[2:])), 2)))
    if first_danger is None and closing > 0.5 and ttc is not None and ttc < 2.0:
        first_danger = (round(t, 2), round(d, 2), round(ttc, 2))
    if first_near is None and d < 1.0:
        first_near = (round(t, 2), round(d, 2))
    if np.linalg.norm(true - [3.0, 1.0]) < 0.3:
        break
t90 = next(tt for tt, v in v_hist if v >= 0.9 * 1.2)
res["10-8"] = {"danger_alarm_(t,d,ttc)": first_danger, "near_alarm_(t,d)": first_near,
               "lead_s": round(first_near[0] - first_danger[0], 2), "speed_90pct_after_s": t90}

# --- 9. ProximityAlarm: 원문 클래스 코드를 그대로 꺼내 실행 (앱 전체는 카메라·모델을 올리므로 import하지 않음)
src = open(f"{REPO}/src/proximity_app.py", encoding="utf-8").read()
cls = next(n for n in ast.parse(src).body if isinstance(n, ast.ClassDef) and n.name == "ProximityAlarm")
ns = {"args": types.SimpleNamespace(ttc=2.0), "CLOSE_V": 0.5}
exec(compile(ast.Module([cls], []), "ProximityAlarm", "exec"), ns)
PA = ns["ProximityAlarm"]

def run(dists, fps=7):
    a, ev = PA(1.0, 3.0), []
    for k, d in enumerate(dists):
        ev += [(round(k / fps, 1), e) for e in a.update(k / fps, d)]
    return ev
n = lambda s: rng.normal(0, 0.05, s)
sc = {}
sc["4m→타겟 걸어옴(1m/s)"] = run(list(np.linspace(4, 0.5, 25) + n(25)))
sc["0.5m→4m 밖 나감"] = run(list(np.linspace(0.5, 4.2, 26) + n(26)))
sc["1.0m 경계 10초 (잡음 5cm)"] = run(list(1.0 + n(70)))
side = [float(np.hypot(x, 2.0)) for x in np.linspace(-4, 4, 57)]
sc["2m 옆 지나감"] = run(side)
sc["4m 밖 서성임"] = run(list(4.2 + n(70)))
res["ProximityAlarm"] = sc
ttc_a = PA(1.0, 3.0)
res["update_ttc"] = {"closing1.2_ttc1.5": ttc_a.update_ttc(1.2, 1.5, 1.8), "repeat": ttc_a.update_ttc(1.2, 1.4, 1.7),
                     "release_then_again": (ttc_a.update_ttc(0.1, None, 2.0), ttc_a.update_ttc(1.2, 1.5, 1.8))}
print(json.dumps(res, ensure_ascii=False, indent=1, default=lambda o: o.tolist() if hasattr(o, "tolist") else str(o)))
