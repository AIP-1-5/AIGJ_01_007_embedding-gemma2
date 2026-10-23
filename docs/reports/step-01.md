# 1단계 환경 준비

2026-10-23 · 보드 A (team5-a) · yj

## 완료 조건 판정

| 조건 (원문 확인 포인트) | 측정값 | 통과 여부 | 미통과 원인 |
|---|---|---|---|
| JetPack·Python 확인 → 맞는 torch 인덱스 선택 | `R39 (release), REVISION: 2.1`, Ubuntu 24.04, Python 3.12.3 → cu132 경로 | 통과 | |
| 최대 성능 모드 | `NV Power Mode: MAXN_SUPER` (이미 설정됨) | 통과 | |
| 스왑 8GB | `/swapfile file 8G` (이미 설정됨) | 통과 | |
| 시스템 패키지 | python3-venv, ffmpeg 8.0.1, libsndfile1, libopenblas-dev 설치됨 (이미 설정됨) | 통과 | |
| venv `~/eg2` | 생성, pip 26.2.2 | 통과 | |
| GPU 커널 실행 검증: `(8, 7)  True  숫자` | `2.14.1+cu132 (8, 7) True` / `268435312.0` | 통과 | |
| `no kernel image`, sm_87 경고 없음 | 출력에 없음 | 통과 | |

## 실행 조건

- torch 2.14.1+cu132, torchvision 0.29.1+cu132 (torchaudio 없음 — 원문 Q7 참고, 2단계에서 설치하지 않는다)
- 전원 모드 MAXN_SUPER. `jetson_clocks`는 실행하지 않음(sudo 필요, 재부팅 시 풀림, 측정 영향은 6단계에서 비고로 남긴다)
- 같은 보드에서 동시에 돈 프로세스: 다른 계정 3개(팀원 2명이 각자 홈에 모델 다운로드, 팀원 1명이 torch 설치·시계열 서비스·수집기). 수집기는 건드리지 않음.

## 원문과 다른 점

| 원문 | 우리 환경 | 이유 |
|---|---|---|
| 0번 NVMe SSD 마운트, `HF_HOME=/ssd/hf` | 생략. SSD로 부팅 중(`nvme0n1p1` → `/`), 캐시는 `/srv/team5/hf` | 이미 SSD 부팅, 계정 4개가 캐시 공유 |
| `/ssd/swapfile` | `/swapfile` (이미 있음) | SSD 부팅이라 같은 디스크 |
| JetPack 6 경로가 기본 | JetPack 7 경로 (cu132) | R39, Python 3.12 |
| `nvcc --version` | `nvcc: command not found` | 원문 Q5. torch는 자체 CUDA 런타임 휠(cuda-toolkit 13.2.2)을 쓰므로 nvcc 없이 동작. 설치하지 않음 |

## 실행한 sudo 명령 (사용자가 별도 터미널에서)

```bash
sudo mkdir -p /srv/team5/hf
sudo chown -R team5:users /srv/team5
sudo chmod -R 2775 /srv/team5
sudo setfacl -R -m g:users:rwX -m d:g:users:rwX /srv/team5
```

확인: `drwxrwsr-x+ team5 users /srv/team5/hf`, `default:group:users:rwx`, yj 계정 쓰기 테스트 통과.

## 관찰

- 2048×2048 행렬곱 5회 (ms): CPU `118.4, 120.1, 141.4, 122.0, 156.4` / GPU `69.2, 16.4, 12.9, 12.9, 12.8`.
  GPU 첫 회가 느린 것은 CUDA 초기화·커널 로드. 안정 후 약 9배.
- `torch.cuda.synchronize()` 없이 재면 GPU 행렬곱이 `0.08 ms`로 찍힌다(비동기 실행이라 계산이 끝나기 전에 시간을 잼).
- 모델 로드 전 메모리: `available 5.4Gi` (총 7.3Gi).
