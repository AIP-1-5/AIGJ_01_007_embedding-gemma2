---
description: 실습 N단계 시작 — 원문을 읽고 계획·완료 조건·주의점만 정리하고 멈춘다
argument-hint: <단계 번호 1~10>
allowed-tools: Read, Glob, Grep, Bash(git status:*), Bash(git log:*), Bash(ls:*), Bash(cat /etc/nv_tegra_release), Bash(python3 -V), Bash(free:*), Bash(df:*), Bash(nvidia-smi:*), Bash(ps:*), Bash(date:*)
---

# /step-start $ARGUMENTS

실습 $ARGUMENTS단계를 시작한다. 읽고 계획을 세운 뒤, **연속 진행**이므로 승인을 기다리지 않고 바로 실행한다.
멈추는 경우는 `CLAUDE.md`의 "멈추고 사용자에게 묻는 경우"뿐이다.

## 1. 읽을 것

1. `../embedding_gemma2/README.md`에서 $ARGUMENTS단계 전체와, Q&A 섹션 중 이 단계 관련 항목.
   파일이 없으면 맨 위에 알리고 멈춘다.
2. `CLAUDE.md`의 장비 정보 (JetPack 7 → cu132 경로, 보드 A에서 실행·팀원 수집기 건드리지 않음, 4·8·9단계 큰 실행 직전 확인, 학습은 맥에서만, sudo는 사용자가).
3. `docs/reports/`의 앞 단계 결과, `docs/reports/troubleshooting.md`, `docs/roadmap.md` 현재 위치.
4. 지금 보드 상태: `free -h`, `ps -eo user,pid,rss,cmd | grep -i python | grep -v grep` (다른 계정이 모델을 올렸는지).

## 2. 출력 (이 순서, 한국어, 짧게)

### 이 단계가 푸는 문제
- 한두 줄. 처음 나오는 용어는 일상 비유 한 줄 + 쉬운 정의.

### 완료 조건
- 원문의 "확인 포인트"와 "기대값"을 표로: `조건 | 어떻게 확인 | 기대값`.

### 실행 계획
- 순서대로. 각 줄 앞에 `[내가]`(sudo, 카메라 연결, 팀 알림) 또는 `[Claude]`를 붙인다.
- 원문과 우리 환경이 다른 곳(JetPack 7, 공용 HF 캐시, 개인 계정)을 짚고 바꾼 명령을 쓴다.

### 미리 막을 문제
- 원문 Q&A와 앞 단계 오류 기록에서 이 단계에 걸릴 만한 것 3개 이내.
- 같은 보드 팀원과 겹치는 자원(GPU 메모리, 카메라)과 그 대처.

### 예상 시간
- 하루 5시간 기준으로 이 단계에 쓸 시간.

계획을 출력한 뒤 바로 실행한다. 단, `CLAUDE.md`의 멈춤 조건(sudo, 물리 작업·비밀값, 4·8·9단계 큰 실행 직전, 맥 학습, 10단계 카메라 1대, 같은 오류 2회)에 걸리면 그 지점에서 묻는다.

## 규칙

- 확실하지 않으면 문장 끝에 "추정" 또는 "확인 필요".
- 원문 README를 통째로 옮기지 않는다.
