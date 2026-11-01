DST=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_max_dev

DST="$DST" python3 - <<'PY'
import os, re
from pathlib import Path

root = Path(os.environ["DST"])
checks = {
    "nlp_bert_max.py": r"vocab_size|Embedding\(|10727|10094|WDIR",
    "sequence_postprocess_max.py": r"seq_dense|vocab_size|512|256|WDIR",
    "grecbase_fusion_full_head_72_max.py": r"input_types|fused_dims|graph.output|BPLAN_BASE_PT|WDIR",
    "main_context_max.py": r"WDIR|deep_embedding|Embedding\(|3146|3506",
}

for name, pattern in checks.items():
    print(f"\n=== {name} ===")
    p = root / name
    if not p.is_file():
        print("MISSING FILE")
        continue
    for number, line in enumerate(p.read_text().splitlines(), 1):
        if re.search(pattern, line):
            print(f"{number}: {line.strip()[:180]}")
PY
