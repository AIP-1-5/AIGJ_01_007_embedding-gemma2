"""공통 로더. 3~10단계가 load()로 필요한 인코더만 골라 올린다.

원문과 다른 점
- 모델 캐시: 원문은 HF_HOME=/ssd/hf. 우리는 팀 공용 /srv/team5/hf (계정마다 3GB씩 받지 않게).
  HF_HOME이 이미 설정돼 있으면 그 값을 쓴다.
"""
import os

os.environ.setdefault("HF_HOME", "/srv/team5/hf")

import torch
from sentence_transformers import SentenceTransformer

MODEL_ID = "google/embeddinggemma-2"
MAX_SEQ_LEN = 8192


def load(vision=False, audio=False):
    cfg = {}
    if not vision: cfg["vision_config"] = None   # 미사용 인코더는 로드하지 않음
    if not audio:  cfg["audio_config"] = None
    model = SentenceTransformer(
        MODEL_ID, device="cuda",
        model_kwargs={"torch_dtype": torch.bfloat16},  # float16 금지 (임베딩 NaN)
        config_kwargs=cfg,
    )
    # 원문에 없음. 기본 max_seq_length가 사실상 무제한(1e30)이라 긴 문서가 잘리지 않는다.
    # 약 14,000토큰 입력에서 attention mask 1.48GiB 할당으로 OOM (3단계 보고서). 모델 컨텍스트 8,192로 자른다.
    model.max_seq_length = MAX_SEQ_LEN
    return model
