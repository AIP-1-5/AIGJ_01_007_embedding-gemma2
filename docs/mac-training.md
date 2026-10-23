# 맥(MPS)에서 7단계 학습하기

보드에서는 학습하지 않는다([decisions.md](decisions.md) 2026-10-23). 학습은 맥에서, 평가는 보드에서 한다.

## 1. 코드·데이터 받기

보드에서 커밋한 것을 push한 뒤 맥에서 (이 맥의 저장소 위치: `~/Chosun_AIPJ/AIP-1-5/AIGJ_01_007_embedding-gemma2`):

```bash
cd ~/Chosun_AIPJ/AIP-1-5/AIGJ_01_007_embedding-gemma2 && git pull --ff-only
wc -l data/train.jsonl data/eval.jsonl                  # 300, 60
```

## 2. 맥 환경 (한 번만)

맥 기본 Python은 3.9.6이라 sentence-transformers 6을 못 쓴다. sudo 없이 uv로 Python 3.12를 받는다.
맥은 PyPI torch가 MPS(애플 GPU)를 지원하므로 Jetson처럼 torch 버전 고정이 필요 없다.

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh          # ~/.local/bin/uv
export PATH=$HOME/.local/bin:$PATH
uv venv --python 3.12 ~/eg2-mac
VIRTUAL_ENV=~/eg2-mac uv pip install "sentence-transformers[image,audio,video,train]>=6.1.0" torch torchvision transformers accelerate datasets
VIRTUAL_ENV=~/eg2-mac uv pip uninstall pyctcdecode        # numpy를 1.x로 묶어 pyarrow(datasets)가 깨진다 (원문 Q12)
VIRTUAL_ENV=~/eg2-mac uv pip install "numpy>=2"
~/eg2-mac/bin/python -c "import torch; print(torch.__version__, 'mps', torch.backends.mps.is_available())"   # mps True
~/eg2-mac/bin/hf download google/embeddinggemma-2      # 약 1.5GB
```

- 텍스트만 학습해도 `[image,video]` extra가 필요하다. 모델 프로세서가 모든 입력의 전처리기를 같이 불러 Pillow·torchvision이 없으면 로드에 실패한다.

## 3. 학습

```bash
cd ~/Chosun_AIPJ/AIP-1-5/AIGJ_01_007_embedding-gemma2 && mkdir -p runs
nohup caffeinate -i ~/eg2-mac/bin/python src/train_ft.py > runs/train.log 2>&1 < /dev/null &
tail -f runs/train.log        # Ctrl+C로 보기만 끈다 (학습은 계속)
```

- `nohup`: SSH가 끊겨도 계속. `caffeinate -i`: 학습 중 맥이 잠들지 않게. 전원 연결, 뚜껑 열기.
- 기본: 3 epoch, 배치 8, 누적 2, lr 2e-5. 끝나면 학습 전후 점수와 학습 시간이 `runs/eg2-classroom/summary.json`에 저장된다.
- 메모리 부족(`MPS backend out of memory`)이면: `--batch 4 --accum 4`
- 학습 후 점수가 오히려 떨어져도 **평가 결과를 보고 epoch·lr을 바꿔 다시 돌리지 않는다**(팀 규칙: 평가 데이터로 설정을 고르지 않는다).
  떨어진 결과를 그대로 보고서에 쓴다. 설정을 바꿔 보려면 학습 데이터에서 검증용을 따로 떼어 그걸로 고른다.
- 맥은 float32로 학습하고 저장만 bfloat16으로 한다.

## 4. 보드로 옮기기

```bash
ssh board-a mkdir -p ~/work/AIGJ_01_007_embedding-gemma2/models ~/work/AIGJ_01_007_embedding-gemma2/runs/eg2-classroom
scp -r models/eg2-classroom board-a:~/work/AIGJ_01_007_embedding-gemma2/models/
scp runs/eg2-classroom/summary.json runs/train.log board-a:~/work/AIGJ_01_007_embedding-gemma2/runs/eg2-classroom/
```

보드에서 맥 원격 로그인으로 가져와도 된다(맥 시스템 설정 → 공유 → 원격 로그인 + 보드 공개키 등록, 2026-10-23 설정):

```bash
# 보드에서
scp -r <맥 사용자>@<맥 Tailscale IP>:Chosun_AIPJ/AIP-1-5/AIGJ_01_007_embedding-gemma2/models/eg2-classroom models/
```

`models/`, `runs/`는 `.gitignore`에 있어 커밋되지 않는다. 옮긴 뒤 Claude에게 알리면 보드에서 평가한다:

```bash
python src/eval_ir.py models/eg2-classroom
EG2_MODEL=models/eg2-classroom python src/test_text.py     # 도메인 밖 일반 질의(3단계)가 무너지지 않았는지
```
