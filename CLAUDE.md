# CLAUDE.md

## 이 저장소

Jetson Orin Nano에서 EmbeddingGemma 2로 텍스트·영상·음성 임베딩 검색을 하고, 미세 조정과 카메라 응용(물체 검색, 동작 인식, 접근 감지)까지 확장하는 실습의 개인 저장소다.

- 실습 원문: `../embedding_gemma2/README.md`
  Private 저장소 `AIP-1/embedding_gemma2`에 있다. 이 저장소 옆에 clone하고 `claude --add-dir ../embedding_gemma2`로 연다.
  파일이 안 보이면 작업을 시작하기 전에 사용자에게 알린다.
- 원문 README에 코드가 들어 있다. 코드는 원문에서 옮겨 이 저장소의 `src/`에 둔다. 원문을 통째로 복사하지 않는다.
- 결과물: `docs/reports/` · 일정: `docs/roadmap.md` · 결정: `docs/decisions.md` · 학습 노트: `docs/study/`

## 작업 방식

- 실습 단계 하나 = 작업 단위 하나. 단계 번호는 원문과 맞춘다(1 환경 준비 ~ 10 카메라 2대 접근 감지).
- 단계를 시작할 때는 `/step-start N`. **읽고 계획만 하고 멈춘다.** 사용자가 승인하기 전에는 실행·설치하지 않는다.
- 원문의 해당 단계 "확인 포인트"와 "기대값"을 그 단계의 완료 조건으로 쓴다.
- 실행 후에는 완료 조건을 하나씩 실제로 확인하고, 통과/미통과를 숫자와 함께 `docs/reports/step-NN.md`에 남긴다.
- 단계가 끝나면 `/step-end N`으로 학습 노트를 쓴다. 하루 끝은 `/day-end`.
- 원문 코드가 오류를 내면 원문의 Q&A 섹션부터 찾는다. 해결한 오류는 `docs/reports/troubleshooting.md`에 `증상 | 원인 | 해결`로 남긴다.

## 장비와 역할

| | 보드 A | 보드 B | 맥 |
|---|---|---|---|
| 이 실습에서 | 실습 실행 (1~10단계). 팀원 계정의 시계열 수집기(약 27MB)가 상시 돈다 | 이 실습에서 쓰지 않음 | 코드 작성, 문서, 필요하면 7단계 학습 |
| 접속 | `ssh board-a` (Tailscale) | `ssh board-b` (Tailscale) | — |

- 보드: Jetson Orin Nano Super 8GB (CPU·GPU 메모리 공유), **JetPack 7.2.1, Ubuntu 24.04, Python 3.12**.
  따라서 원문 1단계의 torch 설치는 **JetPack 7 경로(cu132)**를 쓴다. JetPack 6 경로(jp6/cu126)를 쓰지 않는다.
- 보드 A의 팀원 시계열 수집기는 **멈추거나 건드리지 않는다**(kill, 재시작, 설정 변경, 그 파일 수정 모두 금지).
  메모리가 모자라면 수집기가 아니라 내 프로세스를 줄이거나 내린다.
- 같은 보드를 팀원 1명과 함께 쓴다. 계정은 따로지만 GPU·메모리·카메라는 하나다.
  - 모델을 올리기 전에 `free -h`로 남은 메모리를 확인하고, `ps -eo user,pid,rss,cmd | grep -i python`으로 다른 계정 프로세스를 확인한다.
    다른 사람이 모델을 올려 두었으면 실행하지 말고 사용자에게 알린다.
  - **4단계 이후(영상·비전, YOLO)는 실행 전에 사용자에게 묻는다.** `free -h` 결과를 같이 보여 준다.
  - 카메라는 한 번에 한 프로그램만 연다(`device busy` 오류).
- 교육장 네트워크는 SSH 22번 포트가 막혀 있다. GitHub는 `~/.ssh/config`에 설정한 443 포트(`ssh.github.com`)로 접속한다.
  push·clone이 22번에서 멈추면 이 설정부터 확인한다.
- 공용 큰 파일은 `/srv/team5`. 모델 캐시는 `HF_HOME=/srv/team5/hf`를 같이 쓴다(약 3GB를 계정마다 받지 않게).
  개인 venv는 `~/eg2`, 개인 작업 폴더는 이 저장소.
- **sudo가 필요한 명령(apt, nvpmodel, 스왑, fstab, usermod)은 실행하지 않는다.** 명령만 보여 주고 사용자가 직접 친다.
  보드 시스템 설정은 팀에서 한 명만 한 번 한다.

## 하지 말 것

- 이 저장소는 Public이다. 원문 README를 통째로 복사하지 않는다(필요한 확인 기준과 코드만 옮긴다).
- 사진·영상·음성 파일(`media/`)을 커밋하지 않는다. 강의실 사람 얼굴과 목소리가 들어 있다.
- RTSP 주소(카메라 계정·비밀번호 포함), HF 토큰을 코드·문서·커밋·로그에 쓰지 않는다. `.env`에서 읽는다.
- 모델 파일(`models/`, `runs/`, `*.pt`, `*.safetensors`)을 커밋하지 않는다.
- `float16`을 쓰지 않는다(임베딩 NaN). `bfloat16` 또는 `float32`.
- `pip install`은 반드시 `-c ~/eg2/torch-pin.txt`를 붙인다. Jetson용 torch가 PyPI torch로 덮어써지면 GPU를 못 쓴다.
- 보드에서 `sudo apt autoremove`, 보드 A 재부팅을 하지 않는다.
