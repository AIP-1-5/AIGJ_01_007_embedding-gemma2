# 맥(MPS)에서 7단계 학습하기

보드에서는 학습하지 않는다([decisions.md](decisions.md) 2026-10-23). 학습은 맥에서, 평가는 보드에서 한다.

## 1. 코드·데이터 받기

보드에서 커밋한 것을 push한 뒤 맥에서:

```bash
cd ~/work/AIGJ_01_007_embedding-gemma2 && git pull     # 없으면 git clone
wc -l data/train.jsonl data/eval.jsonl                  # 300, 60
```

## 2. 맥 환경 (한 번만)

Python 3.10 이상. 맥은 PyPI torch가 MPS(애플 GPU)를 지원하므로 Jetson처럼 버전 고정이 필요 없다.

```bash
python3 -m venv ~/eg2-mac && source ~/eg2-mac/bin/activate
pip install -U pip
pip install torch "sentence-transformers[train]>=6.1.0" transformers accelerate datasets
python -c "import torch; print(torch.__version__, 'mps', torch.backends.mps.is_available())"   # mps True
hf download google/embeddinggemma-2      # 약 1.5GB
```

## 3. 학습

```bash
source ~/eg2-mac/bin/activate
cd ~/work/AIGJ_01_007_embedding-gemma2
python src/train_ft.py 2>&1 | tee runs/train.log      # 기본: 3 epoch, 배치 8, 누적 2, lr 2e-5
```

- 끝나면 학습 전후 점수와 학습 시간이 출력되고 `runs/eg2-classroom/summary.json`에 저장된다.
- 메모리 부족(`MPS backend out of memory`)이면: `python src/train_ft.py --batch 4 --accum 4`
- 학습 후 점수가 오히려 떨어지면(과적합): `python src/train_ft.py --epochs 1 --lr 1e-5`
- 맥은 float32로 학습하고 저장만 bfloat16으로 한다(약 0.5GB).

## 4. 보드로 옮기기

```bash
ssh board-a mkdir -p ~/work/AIGJ_01_007_embedding-gemma2/models ~/work/AIGJ_01_007_embedding-gemma2/runs/eg2-classroom
scp -r models/eg2-classroom board-a:~/work/AIGJ_01_007_embedding-gemma2/models/
scp runs/eg2-classroom/summary.json runs/train.log board-a:~/work/AIGJ_01_007_embedding-gemma2/runs/eg2-classroom/
```

`models/`, `runs/`는 `.gitignore`에 있어 커밋되지 않는다. 옮긴 뒤 Claude에게 알리면 보드에서 평가한다:

```bash
python src/eval_ir.py models/eg2-classroom
EG2_MODEL=models/eg2-classroom python src/test_text.py     # 도메인 밖 일반 질의(3단계)가 무너지지 않았는지
```
