"""7단계 도메인 미세 조정 — 맥(MPS)에서만 실행한다. 저장소 루트에서: python src/train_ft.py

원문과 다른 점
- 보드에서는 학습하지 않는다 (CLAUDE.md, decisions.md 2026-10-23). Jetson이면 바로 종료한다.
- 맥 MPS는 bfloat16 학습 지원이 불안정해 float32로 학습한다(원문 bf16=True). 저장할 때만 bfloat16으로 바꿔
  용량을 절반으로 줄인다(보드는 어차피 bfloat16으로 올린다).
- 경로를 저장소 기준으로 바꿨다: data/train.jsonl, runs/eg2-classroom, models/eg2-classroom (둘 다 .gitignore).
- --epochs, --batch, --lr 인자로 원문 확인 포인트(과적합 시 epoch·lr 낮추기, OOM 시 배치 줄이기)를 바로 시험한다.
- 학습 시간, 장치, 최종 평가 값을 runs/eg2-classroom/summary.json에 남긴다 (보고서에 옮길 숫자).
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

if Path("/etc/nv_tegra_release").exists():
    sys.exit("Jetson 보드에서는 학습하지 않는다. 맥에서 실행한다 (docs/reports/step-07.md).")

import torch
from datasets import load_dataset
from sentence_transformers import (SentenceTransformer, SentenceTransformerTrainer,
                                   SentenceTransformerTrainingArguments)
from sentence_transformers.sentence_transformer.losses import MultipleNegativesRankingLoss, MatryoshkaLoss
from sentence_transformers.sentence_transformer.training_args import BatchSamplers

sys.path.insert(0, os.path.dirname(__file__))
from eval_ir import build_evaluator, pick_device

ap = argparse.ArgumentParser()
ap.add_argument("--epochs", type=float, default=3)
ap.add_argument("--batch", type=int, default=8)          # 원문: OOM이면 4로
ap.add_argument("--accum", type=int, default=2)          # 원문: 배치 4면 4로
ap.add_argument("--lr", type=float, default=2e-5)        # 원문: 과적합이면 1e-5
ap.add_argument("--out", default="models/eg2-classroom")
args = ap.parse_args()

device = pick_device()
use_bf16 = device == "cuda"
model = SentenceTransformer("google/embeddinggemma-2", device=device,
    model_kwargs={"torch_dtype": torch.bfloat16 if use_bf16 else torch.float32},
    config_kwargs={"vision_config": None, "audio_config": None})
model.max_seq_length = 512   # 학습 데이터는 짧은 문장뿐. 길이를 묶어 메모리를 아낀다.

# gradient checkpointing은 Trainer 인자 대신 내부 HF 모델에 직접 켠다 (원문 Q9: every_n_layers TypeError)
hf = getattr(model[0], "auto_model", None) or getattr(model[0], "model", None)
hf.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})

train = load_dataset("json", data_files="data/train.jsonl", split="train")

# MatryoshkaLoss로 감싸야 학습 후에도 256/128차원 절단이 유지된다
loss = MatryoshkaLoss(model, MultipleNegativesRankingLoss(model),
                      matryoshka_dims=[768, 512, 256, 128])

targs = SentenceTransformerTrainingArguments(
    output_dir="runs/eg2-classroom",
    num_train_epochs=args.epochs,
    per_device_train_batch_size=args.batch,
    gradient_accumulation_steps=args.accum,
    learning_rate=args.lr, warmup_steps=0.1,      # Transformers v5: 비율을 float로
    bf16=use_bf16,
    batch_sampler=BatchSamplers.NO_DUPLICATES,    # 배치 안 중복 문서 방지 (같은 문서 3질의)
    prompts={"anchor": model.prompts["SearchQuery"],
             "positive": model.prompts["Document"]},
    eval_strategy="epoch", save_strategy="epoch", save_total_limit=1,
    logging_steps=10, report_to="none",
)

evaluator = build_evaluator()
before = evaluator(model)
t = time.perf_counter()
trainer = SentenceTransformerTrainer(model=model, args=targs, train_dataset=train,
                                     loss=loss, evaluator=evaluator)
trainer.train()
train_sec = time.perf_counter() - t
after = evaluator(model)

model.to(torch.bfloat16)
model.save_pretrained(args.out)

keys = ["accuracy@1", "accuracy@3", "accuracy@5", "ndcg@10"]
summary = {
    "device": device, "torch": torch.__version__, "epochs": args.epochs, "batch": args.batch,
    "accum": args.accum, "lr": args.lr, "train_pairs": len(train), "train_seconds": round(train_sec, 1),
    "before": {k: round(before[f"classroom_cosine_{k}"], 3) for k in keys},
    "after": {k: round(after[f"classroom_cosine_{k}"], 3) for k in keys},
    "loss_log": [h for h in trainer.state.log_history if "loss" in h],
}
Path("runs/eg2-classroom").mkdir(parents=True, exist_ok=True)
Path("runs/eg2-classroom/summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
print(json.dumps({k: v for k, v in summary.items() if k != "loss_log"}, ensure_ascii=False, indent=2))
print(f"saved {args.out}")
