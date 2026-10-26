# 실제로 겪은 오류

원문 Q&A에 없거나 우리 보드에서만 난 것 위주. 지어내지 않는다.

| 날짜 | 단계 | 증상 (오류 메시지 핵심) | 원인 | 해결 |
|---|---|---|---|---|
| 2026-10-23 | 1 | `ls: cannot access '/srv/team5'` | 공용 폴더 미생성, `/srv`는 root 소유 | sudo로 생성, `users` 그룹 2775 + 기본 ACL (step-01.md) |
| 2026-10-23 | 1 | Claude Code `! sudo ...` → `a terminal is required to read the password` | `!` 입력은 비밀번호를 받을 터미널이 아님 | 별도 SSH 터미널에서 sudo 실행 |
| 2026-10-23 | 2 | `check.py`: `Could not import module 'AutoProcessor'` | `[audio]` extra가 PyPI torchaudio 2.11.0 설치 (torch는 cu132) — 원문 Q7 | `pip uninstall -y torchaudio` |
| 2026-10-23 | 2 | 설치 후 numpy 2.5.4 → 1.26.4 | pyctcdecode가 `numpy<2` 요구 | 지금은 그대로. 8단계에서 확인 (원문 Q12) |
| 2026-10-23 | 3 | 긴 문서 encode에서 `OutOfMemoryError: Tried to allocate 1.48 GiB` | `max_seq_length` 기본값이 1e30(무제한), attention mask가 길이²로 커짐 | `src/eg2.py`에서 `max_seq_length = 8192` |
| 2026-10-23 | 4 | 원문 `ffmpeg -rtsp_transport tcp ... -c:v libx264` 불가 | 보드 ffmpeg가 NVIDIA 최소 빌드(`--disable-gpl`, RTSP·libx264 없음) | PyAV로 녹화 (`src/grab_clip.py`) |
| 2026-10-23 | 4 | PyAV `TypeError: type av.rational.AVRational doesn't define __round__` | `average_rate`가 Fraction 계열 | `round(float(...))` |
| 2026-10-23 | 4 | 보드 모니터로 카메라 미리보기 불가 | 모니터는 다른 계정의 데스크톱 세션 | Tailscale 주소에만 여는 MJPEG 웹 미리보기 (`src/cam_preview.py`) |
| 2026-10-23 | 5 | espeak-ng 없음, ffmpeg `sine`·`anoisesrc` 필터 없음 | apt 미설치(sudo 필요), NVIDIA 최소 ffmpeg | gTTS·numpy로 생성 (`src/make_audio.py`) |
| 2026-10-23 | 5 | `huggingface-hub 2.2.0 requires click>=8.4.2, but you have click 8.1.8` | gTTS가 `click<8.2` 요구 | 생성 후 gTTS 제거, `click>=8.4.2` 재설치 |
| 2026-10-23 | 7 (맥) | 맥 기본 Python 3.9.6 | sentence-transformers 6은 3.10 이상 | uv로 Python 3.12 venv (`docs/mac-training.md`) |
| 2026-10-23 | 7 (맥) | `EmbeddingGemma2Processor requires the PIL library` → 이어서 `...VideoProcessor requires the Torchvision library` | 텍스트만 써도 프로세서가 이미지·비디오 전처리기를 같이 로드 | `sentence-transformers[image,audio,video,train]` + torchvision |
| 2026-10-23 | 7 (맥) | `ImportError: pyarrow requires NumPy 2.0 or newer, found 1.26.4` | `[audio]`의 pyctcdecode가 numpy<2로 내림 (보드 2단계와 같은 원인) | pyctcdecode 제거, `numpy>=2` (원문 Q12) |
| 2026-10-23 | 4 | Safari에서 미리보기 영상이 안 보임 (페이지·찍기는 됨) | `<img src=/stream>` MJPEG(multipart) 렌더링 문제로 추정 | `/frame.jpg`를 JS로 반복 요청 (`src/cam_preview.py`) |
| 2026-10-23 | 4 | 녹화 1회 `av.error.ArgumentError: Invalid argument: 'media/clip.mp4' returned 22` | 미확인 (바로 재실행 시 성공, 재현 안 됨) | 재실행 |
| 2026-10-23 | 4 | `{"video": 경로}` → `torchcodec is not installed`. torchcodec 설치 후에도 `Could not load this library: libtorchcodec_core4.so` | transformers 5.20이 영상 디코딩에 torchcodec 요구. torchcodec의 FFmpeg 8 백엔드는 `libswscale.so.9`가 필요한데 보드 FFmpeg(NVIDIA 최소 빌드)에 없음 (`ldd`로 확인) | torchcodec 제거, PyAV로 1 fps 프레임 배열을 넘김 (`src/test_vision.py`). 시스템 FFmpeg는 건드리지 않음 |
| 2026-10-23 | 4 | 1 fps로 뽑으려 했는데 151프레임 전부 들어가 영상 1개 7.6~9.2 s | `frame.time` 기준 비교가 의도대로 동작하지 않음 | 프레임 번호 기준 샘플링 → 11프레임, 2.0 s |
| 2026-10-23 | 8 | ultralytics 설치 시 numpy 1.26.4 → 2.5.4 충돌 예고 | pyctcdecode가 `numpy<2` 요구 (원문 Q12) | pyctcdecode 제거 후 설치 |
| 2026-10-23 | 8 | 앱 첫 실행에서 `Ultralytics requirement ['lap>=0.5.12'] not found, attempting AutoUpdate...`, 화면 0바이트 | 추적(track)에 lap 필요. ultralytics가 **torch 고정 없이** pip 자동 설치 | 앱 중지, 남은 pip 프로세스 종료, `pip install -c ~/eg2/torch-pin.txt lap`, `YOLO_AUTOINSTALL=False` (`src/app.py`). torch 그대로 확인 |
| 2026-10-23 | 8 | 프레임마다 `'half' is deprecated ... Use 'quantize' instead` | ultralytics 8.4 인자 변경 | 동작 영향 없음, 그대로 둠 |
| 2026-10-26 | 8 | yoloe `set_classes`에서 `ModuleNotFoundError: No module named 'clip'` (`AutoUpdate disabled by YOLO_AUTOINSTALL=False`) | YOLOE 텍스트 인코더가 ultralytics CLIP 패키지를 요구. 자동 설치는 꺼 둠 | 아래 행 |
| 2026-10-26 | 8 | `pip install git+…/CLIP.git` → `No matching distribution found for setuptools>=70`, 맥에서도 `No route to host` | 교육장 네트워크가 pypi.org·files.pythonhosted.org를 막음 (github.com, huggingface.co는 됨) | ftfy는 GitHub 릴리스 wheel, wcwidth·CLIP은 GitHub 소스를 `--no-index --no-build-isolation -c ~/eg2/torch-pin.txt`로 설치. torch `2.14.1+cu132` 그대로 확인 |
| 2026-10-26 | 8 | yoloe 첫 실행 때 `mobileclip_blt.ts` 572MB를 작업 폴더에 받음 | ultralytics가 텍스트 인코더를 현재 폴더에 저장 | 그대로 둠(`.gitignore`의 `mobileclip*`) |
| 2026-10-26 | 9 | 1차 동작 녹화에서 엉덩이 관절 0%, wave에 손 든 프레임 0 | 카메라가 앉은 사용자를 1m 앞에서 내려다봄 | 카메라를 눈높이 수평, 약 2.5m로 옮겨 재녹화. 1차는 `data/action/_trial1/`로 분리 |
| 2026-10-26 | 9 | 9-5 시도 12회에 요약 7개, 서 있는데 머무름 ↔ 지나감 반복 | 요약은 사람이 3초 넘게 사라져야 생김. 정지 중 흔들림이 `MOVE_TH` 근처로 추정 | 그대로 기록(사용자 결정). 기준값은 바꾸지 않음 |
| 2026-10-26 | 9 | `action.pt` 보드 평가 정확도 0.358, 확률이 전부 0.7 미만 → 앱이 모델 판정을 안 씀 | 저장된 가중치가 초기값 수준. 검증 최고 epoch 저장 방식에서 초반 epoch이 뽑힌 것으로 추정(맥 출력 미확인) | 미해결. 맥 학습 출력 확인 후 같은 설정으로 재학습 |
