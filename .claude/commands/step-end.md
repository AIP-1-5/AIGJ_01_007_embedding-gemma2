---
description: 실습 N단계 마무리 — 완료 조건 판정(docs/reports)과 학습 노트(docs/study) 작성
argument-hint: <단계 번호 1~10>
allowed-tools: Read, Edit, Write, Glob, Grep, Bash(git status:*), Bash(git diff:*), Bash(git log:*), Bash(git add:*), Bash(git commit:*), Bash(ls:*), Bash(date:*), Bash(grep:*)
---

# /step-end $ARGUMENTS

실습 $ARGUMENTS단계를 마무리한다. 문서를 쓰고 점검을 통과하면 **이 단계 결과를 커밋한다**(push는 사용자가).

## 1. 판정: `docs/reports/step-NN.md` (NN = 두 자리)

- `/step-start`에서 정한 완료 조건을 이 대화의 실제 출력으로 하나씩 판정한다.
- 숫자는 실제 출력에서 그대로 가져온다. **출력이 없는 조건은 "미측정"으로 쓰고 지어내지 않는다.**
- 형식은 `docs/reports/README.md`를 따른다. 6단계면 같은 파일의 측정표도 채운다.
- 이 단계에서 실제로 난 오류는 `docs/reports/troubleshooting.md`에 한 줄씩 추가한다.
- `README.md` 진행 상황 표의 해당 행(결과 링크, 판정)을 고친다.

## 2. 학습 노트: `docs/study/step-NN-<이름>.md`

`docs/study/README.md`의 단계 노트 형식을 그대로 따른다. 특히:

- **비교** 섹션: 무슨 문제를 푸는가 → 대안 1개 이상 → 대안을 썼다면 생기는 문제 → 이 방식의 약점 + 실무 Use Case.
- **세미나용 1분 설명**과 **회상 질문 5개**(개념/왜/트레이드오프/장애 상황/내 프로젝트 적용, 답은 `<details>`로 접기).
- **일부러 망가뜨려 볼 실험 1~2개**: 이 보드에서 안전하게 해볼 수 있는 것(dtype 바꾸기, 프롬프트 빼기, 차원 줄이기 등). sudo나 남의 프로세스에 영향 주는 실험은 넣지 않는다.
- 깊이: 임베딩·LLM·비전은 개념과 "왜"까지. 백엔드 개념(인덱스, 검색, 캐시, 동시성, 큐)에 대응시켜 설명한다.
- 코드·설계가 들어간 단계면 실패 시 되돌리기, 동시 실행(같은 보드 두 계정), 데이터가 늘었을 때의 병목을 짚는다.
- 앞 단계 노트에 이미 나온 개념은 다시 쓰지 말고 링크만 건다.
- `파일:라인`은 지금 파일을 열어 확인한 위치만 쓴다.
- 경진대회·팀 프로젝트로 이어질 아이디어가 있으면 마지막에 `> 💡 아이디어:` 1~2줄. 억지로 만들지 않는다.

## 3. 점검

- `grep -rnE 'rtsp://|hf_[A-Za-z0-9]{10,}' docs/` 결과가 비어 있어야 한다.
- 사람 이름이 없는지 확인한다.

## 4. 커밋

- 이 단계의 `src/`, `docs/reports/`, `docs/study/`, `README.md` 변경만 스테이징한다. `media/`, 모델 파일, `.env`가 섞이지 않았는지 `git status`로 확인한다.
- 메시지: `Step N: <이름>`.

## 5. 출력

- 판정 요약 3줄 이내
- 학습 노트에서 바로 회상해 볼 질문 1개 (답은 쓰지 않는다)
- 다음 단계 1줄
