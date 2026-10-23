"""7단계 보조 평가 (원문에 없음): 차원별(768/256/128) 점수 + 문서별 1위 흡수 수(hubness).
저장소 루트에서: python src/eval_dims.py [모델경로]
"""
import sys, collections
sys.path.insert(0, "src")
import eval_ir, torch
from sentence_transformers import SentenceTransformer
path = sys.argv[1] if len(sys.argv) > 1 else "google/embeddinggemma-2"
m = SentenceTransformer(path, device="cuda", model_kwargs={"torch_dtype": torch.bfloat16},
                        config_kwargs={"vision_config": None, "audio_config": None})
m.max_seq_length = 8192
for dim in (768, 256, 128):
    ev = eval_ir.build_evaluator(); ev.truncate_dim = dim
    r = ev(m)
    print(f"dim={dim} acc@1 {r['classroom_cosine_accuracy@1']:.3f} acc@3 {r['classroom_cosine_accuracy@3']:.3f} ndcg@10 {r['classroom_cosine_ndcg@10']:.3f}")
rows = eval_ir.load_pairs("data/eval.jsonl")
docs = list(dict.fromkeys(r["positive"] for r in rows))
d = m.encode(docs, prompt_name="Document", normalize_embeddings=True)
q = m.encode([r["anchor"] for r in rows], prompt_name="SearchQuery", normalize_embeddings=True)
top = (q @ d.T).argmax(1)
c = collections.Counter(int(i) for i in top)
print("1위로 뽑힌 횟수 상위 (정상이면 문서마다 3):", [(docs[i][:18], n) for i, n in c.most_common(4)])
print("한 번도 1위가 안 된 문서 수:", len(docs) - len(c))
