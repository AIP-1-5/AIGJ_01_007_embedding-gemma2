# 실제로 겪은 오류

원문 Q&A에 없거나 우리 보드에서만 난 것 위주. 지어내지 않는다.

| 날짜 | 단계 | 증상 (오류 메시지 핵심) | 원인 | 해결 |
|---|---|---|---|---|
| 2026-10-23 | 1 | `ls: cannot access '/srv/team5'` | 공용 폴더 미생성, `/srv`는 root 소유 | sudo로 생성, `users` 그룹 2775 + 기본 ACL (step-01.md) |
| 2026-10-23 | 1 | Claude Code `! sudo ...` → `a terminal is required to read the password` | `!` 입력은 비밀번호를 받을 터미널이 아님 | 별도 SSH 터미널에서 sudo 실행 |
