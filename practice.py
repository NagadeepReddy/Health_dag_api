python3 - <<'PY'
import json
from pathlib import Path

root = Path("/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension")
model = root / "bplan_native_model"
model.mkdir(parents=True, exist_ok=True)

config = {
    "model_type": "llama",
    "architectures": ["BPlanMaxPipelineModel"],
    "vocab_size": 32000,
    "hidden_size": 256,
    "intermediate_size": 1024,
    "num_hidden_layers": 2,
    "num_attention_heads": 8,
    "num_key_value_heads": 8,
    "max_position_embeddings": 128,
    "bos_token_id": 1,
    "eos_token_id": 2
}

(model / "config.json").write_text(json.dumps(config, indent=2) + "\n")
print("BPLAN ISOLATED MODEL CONFIG: CREATED")
print("MODEL PATH:", model)
print("ORIGINAL DS AND CTA: UNCHANGED")
PY
