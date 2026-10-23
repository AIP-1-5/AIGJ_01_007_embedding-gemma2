# 2단계 패키지·모델 설치

2026-10-23 · 보드 A (team5-a) · yj

## 완료 조건 판정

| 조건 (원문 확인 포인트) | 측정값 | 통과 여부 | 미통과 원인 |
|---|---|---|---|
| torch 버전 고정 파일 | `~/eg2/torch-pin.txt`: `torch==2.14.1+cu132`, `torchvision==0.29.1+cu132` | 통과 | |
| `check.py` 세 줄 출력 + assert 통과 | `torch 2.14.1+cu132 cuda True` / `transformers 5.20.1` / `sentence-transformers 6.2.0` | 통과 (Q7 조치 후) | 첫 실행은 Q7 오류 |
| sentence-transformers 6.1.0 이상 | 6.2.0 | 통과 | |
| 모델 미리 받기 | 1.5G (`/srv/team5/hf/hub`), 199 s | 통과 | |
| `load()` → `encode('test').shape` = `(768,)` | `(768,) float32`, NaN 없음 | 통과 | |

## 실행 조건

- torch 2.14.1+cu132, torchvision 0.29.1+cu132, transformers 5.20.1, sentence-transformers 6.2.0, huggingface_hub 2.2.0, numpy 1.26.4
- dtype bfloat16 (`src/eg2.py`), 출력은 float32
- 같은 보드: 다른 계정의 모델 로드 없음. 팀원 시계열 서비스·수집기만 실행 중 (건드리지 않음)

## 원문과 다른 점

| 원문 | 우리 환경 | 이유 |
|---|---|---|
| `~/eg2-lab`에 `check.py`, `eg2.py` | `src/check.py`, `src/eg2.py` | 저장소에서 관리 |
| `HF_HOME=/ssd/hf` (`.bashrc`) | `src/eg2.py`에서 `HF_HOME` 기본값 `/srv/team5/hf` | 계정 4개 공용 캐시 |
| 설치 후 바로 `check.py` 통과 | torchaudio 2.11.0(PyPI)이 같이 설치돼 Q7 오류 → torchaudio 제거 | 원문 Q7 방법 1 |

## 관찰

- 첫 `check.py`: `ModuleNotFoundError: Could not import module 'AutoProcessor'`. 원인은 `[audio]` extra가 PyPI torchaudio 2.11.0을 끌고 온 것(torch는 cu132). `pip uninstall torchaudio` 후 통과.
- 설치 중 `pyctcdecode`가 numpy를 2.5.4 → **1.26.4로 내림**. 원문 Q12와 반대 방향. 8단계에서 OpenCV·ultralytics가 numpy 2를 요구하면 다시 본다.
- `pip check`: `nvidia-cusparselt-cu13 0.8.1 is not supported on this platform` 한 줄. torch GPU 동작에는 영향 없음(1단계 커널 검증, 이번 encode 통과).
- 텍스트 전용 로드: 17.1 s, 프로세스 RSS 2328 MB (CUDA 컨텍스트 포함).
- 버전 고정 효과(`--dry-run`, 실제 설치 없음):
  - 고정 없이 `pip install -U --force-reinstall --no-deps torch` → `Would install torch-2.14.1` (PyPI 빌드, `+cu132` 없음)
  - `-c ~/eg2/torch-pin.txt` 붙이면 → `ResolutionImpossible` (설치 거부)
- 보드 ffmpeg는 NVIDIA 최소 빌드(`--disable-gpl`, 필터 33개). `sine`·`anoisesrc` 필터와 libx264가 없다 → 4·5단계에서 우회.
