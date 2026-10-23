"""7단계 검색 평가 (학습 전후 모두). 저장소 루트에서 실행:
  python src/eval_ir.py                          # 기준 모델
  python src/eval_ir.py models/eg2-classroom     # 미세 조정 모델

원문과 다른 점
- 장치를 고른다: Jetson은 cuda, 맥은 mps (train_ft.py가 학습 중 같은 평가기를 쓴다).
- 보드에서는 공용 캐시 /srv/team5/hf를 쓴다 (맥에는 이 폴더가 없으므로 있을 때만).
- accuracy@5, 질의별 1위 오답 목록도 출력한다 (어디서 틀리는지 보려고).
- max_seq_length를 8192로 자른다 (3단계: 기본값이 무제한이라 긴 입력에서 OOM).
- 데이터는 원문 저장소에 없어 직접 썼다 (data/, docs/reports/step-07.md 한계 참고).
"""
import json
import os
import sys
import time

if os.path.isdir("/srv/team5/hf"):
    os.environ.setdefault("HF_HOME", "/srv/team5/hf")

import torch
from sentence_transformers import SentenceTransformer
try:  # 원문 경로(sentence_transformers.evaluation)는 6.2.0에서 DeprecationWarning
    from sentence_transformers.sentence_transformer.evaluation import InformationRetrievalEvaluator
except ImportError:
    from sentence_transformers.evaluation import InformationRetrievalEvaluator


def pick_device():
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def load_pairs(path):
    return [json.loads(l) for l in open(path, encoding="utf-8")]


def build_evaluator(path="data/eval.jsonl", name="classroom"):
    rows = load_pairs(path)
    corpus, queries, relevant, doc_id = {}, {}, {}, {}
    for i, r in enumerate(rows):
        d = doc_id.setdefault(r["positive"], f"d{len(doc_id)}")
        corpus[d] = r["positive"]
        queries[f"q{i}"] = r["anchor"]
        relevant.setdefault(f"q{i}", set()).add(d)
    return InformationRetrievalEvaluator(
        queries, corpus, relevant, name=name,
        query_prompt_name="SearchQuery", corpus_prompt_name="Document",
        accuracy_at_k=[1, 3, 5], truncate_dim=None)


def top1_misses(model, path="data/eval.jsonl"):
    rows = load_pairs(path)
    docs = list(dict.fromkeys(r["positive"] for r in rows))
    d = model.encode(docs, prompt_name="Document", normalize_embeddings=True)
    q = model.encode([r["anchor"] for r in rows], prompt_name="SearchQuery", normalize_embeddings=True)
    sim = q @ d.T
    misses = []
    for r, row in zip(rows, sim):
        best = int(row.argmax())
        if docs[best] != r["positive"]:
            misses.append((r["anchor"], docs[best][:30], round(float(row[best] - row[docs.index(r["positive"])]), 3)))
    return misses


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "google/embeddinggemma-2"
    device = pick_device()
    model = SentenceTransformer(path, device=device,
        model_kwargs={"torch_dtype": torch.bfloat16 if device == "cuda" else torch.float32},
        config_kwargs={"vision_config": None, "audio_config": None})
    model.max_seq_length = 8192
    t = time.perf_counter()
    res = build_evaluator()(model)
    print(f"model={path} device={device} eval {time.perf_counter() - t:.1f}s")
    for k in ["accuracy@1", "accuracy@3", "accuracy@5", "ndcg@10"]:
        print(k, round(res[f"classroom_cosine_{k}"], 3))
    misses = top1_misses(model)
    print(f"1위 오답 {len(misses)}개 (질의 | 1위로 나온 문서 | 정답보다 높은 점수 차)")
    for m in misses:
        print("  ", *m, sep=" | ")
