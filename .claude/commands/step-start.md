---
description: 실습 N단계 시작 — 원문을 읽고 계획·완료 조건·주의점만 정리하고 멈춘다
argument-hint: <단계 번호 1~10>
allowed-tools: Read, Glob, Grep, Bash(git status:*), Bash(git log:*), Bash(ls:*), Bash(cat /etc/nv_tegra_release), Bash(python3 -V), Bash(free:*), Bash(df:*), Bash(nvidia-smi:*), Bash(ps:*), Bash(date:*)
---

# /step-start $ARGUMENTS

실습 $ARGUMENTS단계를 시작한다. **읽고 계획만 한다. 설치·실행·파일 수정을 하지 않는다.**

## 1. 읽을 것

1. `../embedding_gemma2/README.md`에서 $ARGUMENTS단계 전체와, Q&A 섹션 중 이 단계 관련 항목.
   파일이 없으면 맨 위에 알리고 멈춘다.
2. `CLAUDE.md`의 장비 정보 (JetPack 7 → cu132 경로, 보드 A에서 실행·팀원 수집기 건드리지 않음, 4단계 이후는 실행 전 확인, sudo는 사용자가).
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

마지막 줄: "진행할까요?" 승인을 받기 전에는 실행하지 않는다.

## 규칙

- 확실하지 않으면 문장 끝에 "추정" 또는 "확인 필요".
- 원문 README를 통째로 옮기지 않는다.
