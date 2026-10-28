# 결과 형식 문서: 카메라 2대 접근 감지 앱 v1 (나영준, 007)

`src/proximity_app.py`가 카메라 2대로 사람과 타겟의 바닥 위치를 구하고, 접근·이탈·충돌 위험 알람을 낸다. 결과는 조회 API(`GET /state`)와 기록 파일(`runs/prox/<모드>.jsonl`) 두 곳으로 나온다. 이 문서만 보고 결과를 받아 쓸 수 있게 적었다.

> 상시 서비스가 아니다. 실험할 때만 보드에서 켜며(10단계: 보드 B, 2026-10-27~28), 포트는 8002, Tailscale 주소에만 연다. 사람 이미지는 저장하지 않는다. 남는 것은 바닥 좌표와 알람 기록뿐이다.

## 0. 바로 써 보기

```bash
# 보드에서 실행 (보정 파일 calib/cam0.npz, calib/cam1.npz 가 있어야 함)
python src/proximity_app.py --cams 0 2 --target "brown cardboard box" --near 1.0 --far 3.0
python src/proximity_app.py --cams 0 2 --target "brown cardboard box" --moving --ttc 2.0   # 이동 타겟

curl http://<보드 주소>:8002/state                     # 지금 상태 (1절)
curl -X POST http://<보드 주소>:8002/retarget          # 타겟 다시 찾기
tail -f runs/prox/fused.jsonl | grep '"event"'       # 알람만 따라 보기 (2절)
```

- 대시보드: `GET /state`를 0.3~1초마다 부르고 `events`의 `ts`가 마지막으로 본 값보다 큰 것만 처리하면 중복 없이 받는다.
- 알람만 필요하면: `events[].label`이 `알람:`으로 시작하는 것만 쓴다(3절).

## 1. 조회 API

| 메서드·경로 | 응답 | 용도 |
|---|---|---|
| `GET /state` | JSON (아래) | 사람·타겟·알람 상태 |
| `POST /retarget` | `{"ok": true}` | 다음 프레임에서 타겟을 다시 찾음 |
| `GET /frame/{n}.jpg` | JPEG (없으면 503) | 카메라 n 최신 화면(관절·타겟 박스 표시) |
| `GET /stream/{n}` | MJPEG | 같은 화면 스트림 (Safari 비권장) |
| `GET /` | HTML | 평면도·화면·이벤트 대시보드 |

`GET /state` 예시 (값은 10-6 실측과 같은 범위의 예시):

```json
{
  "target": {"xyz": [-0.06, 0.30, -0.03], "how": "삼각측량 (재투영 8.4px)",
             "boxes": [[301, 255, 368, 322], [212, 240, 270, 300]], "scores": [0.689, 0.722]},
  "stats": {"fps": 23.0, "skew_ms": 20, "mode": "fused"},
  "people": [{"id": 211, "x": -0.35, "y": 0.80, "h": 1.02, "kind": "stereo", "pose": "앉음",
              "d": 0.53, "trend": "정지", "zone": "near", "v": [0.0, 0.01],
              "closing": 0.0, "ttc": null, "danger": false}],
  "events": [{"ts": 1793170119.4, "who": "#211", "label": "알람: 근접 0.5m"}],
  "room": [-1.36, -1.5, 0.85, 3.14], "near": 1.0, "far": 3.0, "cams": 2, "moving": false,
  "cam_pos": [[-1.03, -2.57, 1.35], [0.08, -2.94, 1.41]]
}
```

| 필드 | 단위 | 뜻 |
|---|---|---|
| `target.xyz` | m | 타겟 위치 (x, y, 높이). 이동 모드에서는 칼만 필터 예측값 |
| `target.how` | — | `삼각측량 (재투영 N px)` / `camN 단독 추정 (높이 0.8m 가정)` / `직접 지정`. 단독 추정은 오차가 클 수 있음 |
| `target.scores` | 코사인 | 카메라별 EmbeddingGemma 2 점수, 못 찾으면 `null` |
| `target.v`, `lost`, `trail` | m/s, —, m | 이동 모드만. 속도, 2초 넘게 놓쳤는지, 최근 경로 50점 |
| `stats.fps` / `skew_ms` | 1/s, ms | 처리 속도, 두 카메라 프레임 시간 차(80ms 넘으면 그 순간 삼각측량 생략) |
| `people[].id` | — | 추적 ID. 2초 안 보이면 퇴장, 다시 보이면 새 ID |
| `people[].x, y` | m | 바닥 위치 (최근 0.5초 중앙값, 이동 모드는 칼만) |
| `people[].h` | m | 어깨 높이. `kind`가 `stereo`일 때만 측정값 |
| `people[].kind` | — | `stereo`(두 카메라 삼각측량) / `single`(한 카메라, 어깨 1.2m 가정) / `ankle`(1대 모드) |
| `people[].pose` | — | `섬` / `앉음`(h < 1.15m) / `-`(stereo가 아니면 판정 안 함) |
| `people[].d` | m | 타겟까지 거리 |
| `people[].trend` | — | `접근 중` / `멀어지는 중` / `정지` (최근 1초 속도 ±0.3m/s 기준) |
| `people[].zone` | — | `near`(1.0m 안) / `mid` / `far`(3.0m 밖) |
| `people[].closing`, `ttc`, `danger` | m/s, 초, — | 이동 모드만. 접근 속도, 충돌 예상 시간, 충돌 위험 알람 켜짐 |
| `room` | m | 인식 범위 [x최소, y최소, x최대, y최대]. 밖의 점은 버림 |
| `cam_pos` | m | 보정으로 계산한 카메라 위치 |

좌표: 원점 = 보정 기준점 1번(10단계에서는 타겟 상자 자리 바닥), z = 위. 축 방향은 `calib/world_points.json`을 따른다.

## 2. 기록 파일 `runs/prox/<모드>[-moving].jsonl`

한 줄에 JSON 하나. `type`으로 나뉜다.

```json
{"ts": 1793170119.4, "type": "event", "who": "#211", "label": "알람: 근접 0.5m"}
{"ts": 1793170120.0, "type": "stats", "fps": 23.0, "skew_ms": 20, "mode": "fused", "target": [-0.06, 0.3, -0.03],
 "people": [{"id": 211, "x": -0.35, "y": 0.8, "h": 1.02, "kind": "stereo", "pose": "앉음", "d": 0.53,
             "trend": "정지", "zone": "near", "closing": 0.0, "ttc": null}]}
```

- `event`: 아래 3절의 이벤트가 날 때마다 1줄.
- `stats`: 1초마다 1줄. `people`은 `/state`와 같은 필드에서 `v`, `danger`를 뺀 것.
- `ts`는 유닉스 초(UTC 기준, 소수 2자리).

## 3. 이벤트 (`events[].label`, 기록 파일 `label`)

| `who` | `label` | 언제 | 중복 |
|---|---|---|---|
| `#ID` | `등장` / `퇴장 (머문 시간 N초)` | 새 추적 시작 / 2초 안 보임 | — |
| `#ID` | `접근 시작 (Nm)` | 추세가 `접근 중`으로 바뀌는 순간 3.0m 안 | 바뀔 때만 |
| `#ID` | `알람: 근접 Nm` | 1.0m 안으로 | 1.2m 밖으로 나가야 다시 무장 (히스테리시스 0.2m) |
| `#ID` | `알람: 이탈 Nm` | 안쪽에 있다가 3.0m 밖으로 | 2.8m 안으로 들어와야 다시 무장 |
| `#ID` | `알람: 충돌 위험 TTC N초 (접근 Vm/s, Dm)` | 이동 모드, 접근 속도 > 0.5m/s 이고 TTC < `--ttc` | 접근 < 0.2m/s 또는 TTC > 1.5×기준이면 다시 무장 |
| `타겟` | `찾음: [x, y, z] / 방식 / 점수 [...]` / `찾지 못함` | 시작·`/retarget` 때 | — |
| `타겟` | `다시 찾음 (임베딩 재식별)` | 이동 모드에서 2초 넘게 놓친 뒤 | — |

주의 (10단계 실측): 알람 상태는 추적 ID 단위다. 사람이 몸을 돌리거나 앉고 일어설 때 ID가 끊겨 0~1초짜리 ID가 생기고, 그 ID가 근접 알람을 한 번 더 낼 수 있다. 받는 쪽에서 "등장 후 1초 안의 알람은 무시"처럼 거르면 줄어든다(제안, 미실험).

## 4. 보정 파일 (`calib/`, 커밋하지 않음 — 예시 좌표만 커밋)

| 파일 | 내용 | 만드는 것 |
|---|---|---|
| `cam{n}_intr.npz` | `K`(3×3), `dist`(왜곡 계수), `res`([폭, 높이]) | `src/calib_intrinsics.py --cam n --square 0.022` |
| `cam{0,1}.npz` | 위 + `R`(3×3), `t`(3×1) | `src/calib_extrinsics.py` → 계산 |
| `world_points.json` | `{"points": [{"id", "xyz": [m, m, m], "check": true?}]}` (`check`는 검증용) | 줄자로 직접 작성 |

`/solve` 응답: `{"0": {"pos": [x,y,z], "reproj": {"P3": 2.1, ...}, "mean_px": 3.78}, "1": {...}, "verify": {"P1": {"check": true, "err_cm": 3.1}}}`. 기준: `mean_px` 3 이하, `pos`가 실측과 20cm 이내, 검증점 10cm 이내.

카메라가 움직이면 보정이 무효가 된다. 10단계에서 cam0이 약 6° 돌아가자 바닥 상자가 높이 -0.47m로 계산됐다. 보정 직후 두 화면(`/frame/{n}.jpg`)을 저장해 두고, 결과가 이상하면 먼저 비교한다.
