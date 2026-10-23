# 실제로 겪은 오류

원문 Q&A에 없거나 우리 보드에서만 난 것 위주. 지어내지 않는다.

| 날짜 | 단계 | 증상 (오류 메시지 핵심) | 원인 | 해결 |
|---|---|---|---|---|
| 2026-10-23 | 1 | `ls: cannot access '/srv/team5'` | 공용 폴더 미생성, `/srv`는 root 소유 | sudo로 생성, `users` 그룹 2775 + 기본 ACL (step-01.md) |
| 2026-10-23 | 1 | Claude Code `! sudo ...` → `a terminal is required to read the password` | `!` 입력은 비밀번호를 받을 터미널이 아님 | 별도 SSH 터미널에서 sudo 실행 |
| 2026-10-23 | 2 | `check.py`: `Could not import module 'AutoProcessor'` | `[audio]` extra가 PyPI torchaudio 2.11.0 설치 (torch는 cu132) — 원문 Q7 | `pip uninstall -y torchaudio` |
| 2026-10-23 | 2 | 설치 후 numpy 2.5.4 → 1.26.4 | pyctcdecode가 `numpy<2` 요구 | 지금은 그대로. 8단계에서 확인 (원문 Q12) |
