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
