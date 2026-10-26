# AIGJ_01_007_embedding-gemma2

Jetson Orin Nano Super 8GB에서 EmbeddingGemma 2로 텍스트·영상·음성을 하나의 벡터 공간에서 검색하고, 강의실 도메인 미세 조정과 카메라 응용으로 확장하는 실습 저장소.

## 진행 상황

일정: [docs/roadmap.md](docs/roadmap.md) · 결정 기록: [docs/decisions.md](docs/decisions.md) · 학습 노트: [docs/study/](docs/study/) · 오류 기록: [docs/reports/troubleshooting.md](docs/reports/troubleshooting.md)

| 단계 | 결과 | 판정 |
|---|---|---|
| 1 환경 준비 | [step-01](docs/reports/step-01.md) | 통과 |
| 2 패키지·모델 설치 | [step-02](docs/reports/step-02.md) | 통과 |
| 3 텍스트 테스트 | [step-03](docs/reports/step-03.md) | 통과 (질의 1 여유 0.006) |
| 4 영상 테스트 | [step-04](docs/reports/step-04.md) | 부분 통과 (원문 질의 1/3 + 애매 1, 추가 2/2, 영상 통과) |
| 5 음성 테스트 | [step-05](docs/reports/step-05.md) | 부분 통과 (2/3, 음성 질의 0.001 차) |
| 6 성능 측정 | [step-06](docs/reports/step-06.md) | 통과 (5개 구성 실측) |
| 7 도메인 미세 조정 | [step-07](docs/reports/step-07.md) | 부분 통과 (acc@1 0.817→0.867, 일반 질의 1개 회귀) |
| 8 웹캠 물체 추출·검색 | [step-08](docs/reports/step-08.md) · [노트](docs/study/step-08-object-search.md) | 부분 통과 (relabel이 세탁기 바로잡음, "세탁기" 검색 통과, yoloe는 세탁기를 keyboard로) |
| 9 사람 동작 인식 | [step-09](docs/reports/step-09.md) | 진행 중 (9-1·9-2 통과: 이벤트 44→12, 손흔들기 0→3. 9-5 재실행, 9-3·9-6 대기) |
| 10 카메라 2대 접근 감지 | [step-10](docs/reports/step-10.md) | 준비 (코드 이식·가상 카메라 검증, 카메라 2대 대기) |

## 구성

| 경로 | 내용 |
|---|---|
| `src/` | 원문에서 옮긴 실행 코드 (`eg2.py`, `test_*.py`, `app.py` …) |
| `data/` | 7단계 학습·평가 jsonl (텍스트만) |
| `docs/reports/` | 단계별 결과와 측정표 |
| `docs/study/` | 단계별 학습 노트 |
| `CLAUDE.md` | Claude Code 작업 규칙, 장비 정보 |
| `.claude/commands/` | `/day-start` `/day-end` `/step-start` `/step-end` |

## 시작하기 (보드 A, 내 계정)

실습 원문은 Private 저장소 `AIP-1/embedding_gemma2`에 있다. 두 저장소를 나란히 clone한다.

```bash
mkdir -p ~/work && cd ~/work
git clone git@github.com:AIP-1/embedding_gemma2.git
git clone git@github.com:AIP-1-5/AIGJ_01_007_embedding-gemma2.git
cd AIGJ_01_007_embedding-gemma2
cp .env.example .env                       # RTSP 주소 등. 커밋 금지
claude --add-dir ../embedding_gemma2       # 원문도 읽을 수 있게 Claude Code 실행
```

진행 순서 (단계 하나씩):

1. `/step-start N` — 원문 N단계를 읽고 계획과 완료 조건 정리. 여기서 멈추고 검토
2. 실행 — sudo 명령은 직접 치고, 나머지는 Claude Code가 실행
3. `/step-end N` — 결과 판정(`docs/reports/`)과 학습 노트(`docs/study/`) 작성
4. `/day-end` — roadmap 갱신, 하루 문서, 커밋
