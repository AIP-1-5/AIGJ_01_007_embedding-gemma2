# 2단계 패키지·모델 설치

2026-10-23 · 결과: [docs/reports/step-02.md](../reports/step-02.md) · 앞 단계: [1단계](step-01-environment.md) (휠·CUDA 맞추기, 통합 메모리)

## 한 문장으로
Jetson torch를 버전 고정 파일로 묶은 채 sentence-transformers를 설치하고(torchaudio 충돌은 제거로 해결), 공용 캐시에 모델을 받아 `(768,)` 임베딩이 나오는 것을 확인했다.

## 세미나용 1분 설명
1단계에서 Jetson용 torch를 어렵게 깔았는데, 그 위에 다른 라이브러리를 설치하면 pip가 "torch 최신 버전도 필요하겠네" 하면서 PyPI의 일반 torch로 바꿔치기할 수 있습니다. 그래서 지금 깔린 torch 버전을 `torch-pin.txt`에 적고, 모든 설치에 `-c`로 붙입니다. Gradle의 dependency lock이나 package-lock.json과 같은 역할입니다. 실제로 고정 없이 dry-run을 해 보면 PyPI torch로 바꾸겠다고 하고, 고정을 붙이면 설치를 거부합니다. 실패하는 쪽이 조용히 바뀌는 쪽보다 안전합니다. 그다음 모델은 공용 캐시 한 곳에 받고, 로더 `load()`는 안 쓰는 인코더(비전·오디오)를 아예 올리지 않게 만듭니다. 쿼리에 필요한 컬럼만 SELECT하는 것처럼, 필요한 부분만 메모리에 올리는 겁니다.

## 핵심 개념

### 제약 파일(constraints)로 버전 고정
- 정의: `-c 파일`은 "이 패키지를 설치하게 되면 반드시 이 버전"이라는 조건. 그 자체로 설치를 일으키지는 않는다.
- 비유: package-lock / Gradle dependency locking. 전이 의존성이 핵심 라이브러리 버전을 몰래 올리는 것을 막는다.
- 이 레포에서는: `~/eg2/torch-pin.txt` (`torch==2.14.1+cu132`), `CLAUDE.md`의 "`pip install`은 반드시 `-c`" 규칙.
- 잘못하면: PyPI torch로 덮어써져 `cuda.is_available()`이 False가 되거나 GPU 커널이 없다. 증상은 2~3단계 뒤에 나타난다.

### 선택적 의존성(extras)이 끌고 오는 패키지
- 정의: `sentence-transformers[audio]`처럼 대괄호로 고른 기능 묶음. 그 묶음이 다른 패키지를 추가로 설치한다.
- 비유: Spring Boot starter 하나를 넣었더니 원치 않는 버전의 라이브러리가 따라 들어오는 것.
- 이 레포에서는: `[audio]`가 PyPI torchaudio 2.11.0을 설치 → transformers import 중 `AutoProcessor` 오류(원문 Q7). `docs/reports/step-02.md` 관찰.
- 잘못하면: 오류 메시지(`AutoProcessor`)가 진짜 원인(torchaudio CUDA 버전)과 멀어서 엉뚱한 곳을 고친다.

### 인코더 선택 로드
- 정의: 멀티모달 모델에서 비전·오디오 인코더 설정을 `None`으로 넘겨 가중치를 올리지 않는다.
- 비유: `SELECT *` 대신 필요한 컬럼만. 또는 지연 로딩(lazy loading).
- 이 레포에서는: `src/eg2.py:20-21` — `vision_config`, `audio_config`를 `None`으로.
- 잘못하면: 텍스트 검색만 하는데 740M 전체가 올라가 공용 8GB 메모리를 낭비한다. 텍스트 전용만으로도 RSS가 2328 MB였다.

## 비교
- 무슨 문제: 하드웨어 전용 빌드(torch+cu132)를 유지한 채 일반 PyPI 생태계 패키지를 설치하기.
- 대안 1 — 제약 없이 설치하고, 깨지면 torch만 재설치: 빠르다.
  - 이 대안의 문제: 깨진 줄 모르고 다음 단계로 간다(설치는 성공으로 끝난다). 재설치할 때마다 460MB.
- 대안 2 — `--no-deps`로 하나씩 설치: torch는 안전하다.
  - 이 대안의 문제: 필요한 의존성까지 빠져서 import 오류를 하나씩 손으로 채워야 한다.
- 이 방식의 약점: 제약 파일은 "버전"만 막는다. 이번 torchaudio처럼 **고정 목록에 없는 새 패키지**가 들어오는 것은 못 막는다. 그래서 설치 뒤 `check.py`로 import·GPU를 다시 확인해야 한다.
- 실무 Use Case: 사내 GPU 서버의 추론 서비스 이미지 빌드에서, 베이스 이미지의 CUDA torch를 constraints로 고정하고 앱 의존성만 설치한다. CI에서 `python -c "import torch; assert torch.cuda.is_available()"`를 스모크 테스트로 둔다.

## 실제로 겪은 문제 → 원인 → 해결
- `check.py`에서 `Could not import module 'AutoProcessor'` → `[audio]` extra가 PyPI torchaudio(다른 CUDA 빌드) 설치, transformers가 import 중 실패 → `pip uninstall torchaudio` (원문 Q7 방법 1). 오디오는 soundfile·librosa로 읽는다.
- numpy가 1.26.4로 내려감 → pyctcdecode가 `numpy<2` 요구 → 지금은 문제 없음. 8단계에서 확인.

## 일부러 망가뜨려 볼 실험
1. **버전 고정 없이 torch 재설치(dry-run)** — 예상: PyPI torch로 바꾸려 함. 실제: `Would install torch-2.14.1` (`+cu132` 없음). `-c torch-pin.txt`를 붙이면 `ResolutionImpossible`로 거부. 직접 해 볼 명령: `~/eg2/bin/pip install --dry-run -U --force-reinstall --no-deps torch` (dry-run이라 안전).
2. **torchaudio를 다시 넣고 check.py** — 예상: 같은 `AutoProcessor` 오류. (재현에 PyPI 다운로드가 필요해 이번엔 안 함. 해 보려면 끝난 뒤 `pip uninstall -y torchaudio`로 되돌린다.)

## 회상 질문 5개
<details><summary>1. 개념: `pip install -c torch-pin.txt`의 `-c`는 `-r`과 무엇이 다른가?</summary>`-r`은 목록의 패키지를 설치한다. `-c`는 설치하지 않고, 어떤 이유로든 그 패키지가 설치될 때 버전을 제한한다.</details>
<details><summary>2. 왜: 오류는 `AutoProcessor`를 import할 수 없다였는데 원인이 torchaudio였던 이유는?</summary>transformers는 torchaudio가 설치돼 있으면 import한다. PyPI torchaudio가 cu132 torch와 CUDA 버전이 달라 로드에 실패했고, 그 실패가 지연 import 래퍼에 감싸져 `AutoProcessor` 오류로 보였다.</details>
<details><summary>3. 트레이드오프: 제약 파일이 막지 못하는 것은? 그래서 무엇을 더 하나?</summary>고정 목록에 없는 새 패키지 설치(이번 torchaudio). 설치 뒤 import + GPU 스모크 테스트(`check.py`)를 매번 돌린다.</details>
<details><summary>4. 장애 상황: 팀원이 "어제까지 되던 encode가 오늘 CPU로 돈다"고 한다. 제일 먼저 볼 것은?</summary>`pip freeze | grep torch`에서 `+cu132`가 사라졌는지. 누군가 `-c` 없이 설치해 PyPI torch로 덮어썼을 가능성이 가장 크다.</details>
<details><summary>5. 내 프로젝트 적용: 팀 프로젝트 Docker 이미지에서 같은 문제를 어떻게 막을까?</summary>베이스 이미지의 torch 버전을 constraints 파일로 고정해 `pip install -c`로 설치하고, 빌드 마지막에 GPU 스모크 테스트를 넣어 실패하면 이미지 빌드를 실패시킨다.</details>
