# 1단계 환경 준비

2026-10-23 · 결과: [docs/reports/step-01.md](../reports/step-01.md)

## 한 문장으로
JetPack 7(R39)에 맞는 cu132 torch를 개인 venv에 설치하고, 실제 GPU 커널이 도는 것(`(8, 7) True`, 행렬곱 결과 출력)까지 확인했다.

## 세미나용 1분 설명
Jetson은 노트북 GPU처럼 "그냥 pip install torch" 하면 안 되는 장비입니다. 일반 PyPI의 torch는 Jetson GPU(sm_87)에 맞는 커널을 갖고 있지 않거나 CPU 전용이라, 설치는 되는데 GPU를 못 씁니다. 비유하면 JDBC 드라이버 버전이 DB 서버 버전과 맞아야 쿼리가 되는 것과 같습니다. 그래서 먼저 JetPack 버전(R36이면 6, R38 이상이면 7)과 Python 버전을 보고, 거기에 맞는 인덱스(우리는 cu132)에서 받습니다. 검증도 `cuda.is_available()`만 보면 안 되고, 실제로 행렬곱을 GPU에서 돌려 숫자가 나오는지 봐야 합니다. "커넥션 풀이 만들어졌다"와 "쿼리가 실제로 돌았다"가 다른 것과 같습니다. 마지막으로 Jetson은 CPU와 GPU가 8GB 메모리를 나눠 쓰고, 이 보드는 4개 계정이 함께 쓰기 때문에, 모델 캐시는 공용 폴더 하나에 두고 스왑으로 순간적인 메모리 부족을 버팁니다.

## 핵심 개념

### 휠과 CUDA 아키텍처 맞추기
- 정의: torch 바이너리(휠)는 특정 CUDA 버전·GPU 아키텍처(Orin = sm_87)용으로 컴파일된다. 둘이 어긋나면 `no kernel image`.
- 비유: DB 드라이버와 서버 버전 호환표. 맞지 않으면 접속은 돼도 쿼리가 실패한다.
- 이 레포에서는: `CLAUDE.md`의 "JetPack 7 경로(cu132)" 규칙, `docs/reports/step-01.md` 원문과 다른 점 표.
- 잘못하면: `from versions: none`(Python 버전과 인덱스 불일치, 원문 Q1), 또는 설치는 되지만 GPU 연산에서 오류.

### `is_available()`와 실제 커널 실행의 차이
- 정의: `is_available()`은 드라이버·런타임이 보이는지만 본다. 실제 커널은 첫 연산에서 로드된다.
- 비유: 헬스체크 엔드포인트가 200을 줘도 실제 쿼리는 실패할 수 있다(얕은 헬스체크 vs 깊은 헬스체크).
- 이 레포에서는: `docs/reports/step-01.md` 판정표의 커널 검증 행 — `(x@x).sum()`이 숫자로 나와야 통과.
- 잘못하면: 2~3단계에서 모델 로드는 되고 첫 encode에서 터진다. 원인 추적이 한 단계 늦어진다.

### GPU 비동기 실행
- 정의: GPU 연산은 큐에 넣고 바로 반환된다. 끝났는지는 `torch.cuda.synchronize()`로 기다려야 안다.
- 비유: 메시지 큐에 publish하고 바로 202를 받는 것. 처리 시간을 재려면 consumer 완료를 기다려야 한다.
- 이 레포에서는: `docs/reports/step-01.md` 관찰 — 동기화 없이 재면 0.08 ms, 하면 12.8 ms.
- 잘못하면: 6단계 지연 측정표가 실제보다 수백 배 빠르게 찍힌다.

### 통합 메모리와 공용 캐시
- 정의: Jetson은 CPU와 GPU가 같은 8GB(실사용 7.3Gi)를 쓴다. "GPU 메모리"가 따로 없다.
- 비유: 한 DB 서버에 여러 서비스가 붙어 있는 것. 한 서비스가 커넥션을 다 잡으면 모두 느려진다.
- 이 레포에서는: `src/eg2.py:9` — `HF_HOME` 기본값을 `/srv/team5/hf`로. 디스크는 공유하고, 메모리는 각자 올린 만큼 쓴다.
- 잘못하면: 계정마다 모델을 올리면 4×(모델 크기)가 한 메모리에 쌓여 스왑으로 밀리고, 팀원 수집기까지 느려진다.

## 비교
- 무슨 문제: Jetson GPU에서 도는 PyTorch를 내 계정에, 다른 사람 환경을 깨지 않고 설치하기.
- 대안 1 — jetson-containers의 PyTorch 컨테이너(원문이 대안으로 제시): 버전 조합이 검증돼 있다.
  - 이 대안의 문제: 공용 보드에서 docker 권한(그룹 추가 = sudo)이 필요하고, 카메라·공용 캐시를 볼륨으로 다시 연결해야 한다. 컨테이너 이미지가 수 GB.
- 대안 2 — 시스템 Python에 설치: `externally-managed-environment`(원문 Q4)로 막히고, 막지 않으면 다른 계정 환경까지 바꾼다.
- 이 방식(개인 venv + cu132 휠)의 약점: torch 버전 고정을 내가 관리해야 한다. 2단계에서 다른 패키지를 설치할 때 PyPI torch로 덮어써질 수 있다(→ `torch-pin.txt`로 막는다).
- 실무 Use Case: 사내 GPU 서버에서 팀원마다 다른 CUDA 프로젝트를 돌릴 때, 시스템 CUDA는 그대로 두고 프로젝트별 venv + 버전 고정 파일(lock)로 격리한다.

## 실제로 겪은 문제 → 원인 → 해결
- `/srv/team5`가 없음 → 공용 폴더를 아직 아무도 안 만듦, `/srv`는 root 소유 → 사용자가 sudo로 생성 + `users` 그룹 쓰기 + 기본 ACL.
- Claude Code의 `!` 입력으로 `sudo`를 치면 `a terminal is required to read the password` → `!`는 비밀번호를 입력받을 터미널이 아님 → 별도 SSH 터미널에서 실행.
- `nvcc: command not found` → CUDA 툴킷 PATH 미등록 또는 미설치(원문 Q5) → torch 휠이 자체 CUDA 런타임을 갖고 있어 해결하지 않고 둠.

## 일부러 망가뜨려 볼 실험
1. **동기화 빼고 GPU 시간 재기** — 예상: 거의 0 ms. 실제: `0.08 ms`(동기화 시 `12.8 ms`). GPU 측정에는 항상 `synchronize()`가 필요하다.
2. **CPU로 같은 행렬곱** — 예상: GPU보다 수 배 느림. 실제: CPU `118~156 ms`, GPU 안정 후 `12.8 ms`(약 9배). GPU 첫 회는 `69.2 ms`로, 초기화 비용이 있다 → 3단계에서 "첫 실행은 제외하고 비교"하는 이유.

## 회상 질문 5개
<details><summary>1. 개념: `torch.cuda.is_available()`이 True인데도 GPU 연산이 실패할 수 있는 이유는?</summary>is_available은 드라이버·런타임이 보이는지만 본다. 휠이 sm_87용 커널을 갖고 있지 않으면 첫 연산에서 `no kernel image`가 난다. 그래서 실제 행렬곱으로 검증한다.</details>
<details><summary>2. 왜: Jetson에서 PyPI 기본 torch를 쓰면 안 되는 이유는?</summary>PyPI aarch64 torch는 Jetson의 JetPack CUDA·아키텍처에 맞춰 빌드되지 않았거나 CPU 전용이다. JetPack 버전에 맞는 인덱스(JP7 = cu132)에서 받아야 GPU를 쓴다.</details>
<details><summary>3. 트레이드오프: 개인 venv vs jetson-containers 컨테이너, 공용 보드에서는 무엇을 고르고 왜?</summary>개인 venv. 컨테이너는 버전 조합이 검증된 대신 docker 권한(sudo)과 볼륨·장치 연결이 필요하고 이미지가 크다. venv는 버전 고정을 직접 관리해야 하는 대신 권한이 필요 없다.</details>
<details><summary>4. 장애 상황: 6단계에서 GPU 지연이 0.1 ms로 찍혔다. 무엇을 의심하나?</summary>`torch.cuda.synchronize()` 없이 시간을 잰 것. GPU는 비동기라 큐에 넣는 시간만 잰 것이다. 실제로 1단계에서 동기화 없이 0.08 ms, 있으면 12.8 ms였다.</details>
<details><summary>5. 내 프로젝트 적용: 팀 프로젝트 서버에 여러 명이 모델을 올릴 때 메모리를 어떻게 관리할까?</summary>모델 파일(디스크)은 공용 캐시 하나로 공유하고, 메모리에 올리는 것은 한 프로세스(추론 서버)만 하게 해서 다른 사람은 API로 호출한다. 올리기 전에는 `free -h`로 확인한다. DB 커넥션 풀을 서비스마다 따로 두지 않고 프록시 하나로 모으는 것과 같다.</details>
