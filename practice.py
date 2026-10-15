python3 - <<'PY'
from pathlib import Path

root = Path("artifacts/v1.168-max/cta_max")
names = [
    "att_pooling_max.py",
    "grecbase_aux_branches_max.py",
    "grecbase_fusion_full_head_72_max.py",
    "grecbase_get_path_max.py",
    "live_cta_pipeline_bridge.py",
    "main_context_max.py",
    "nlp_bert_in_graph.py",
    "parallel_transformer_block_2layers.py",
    "run_live_max_inference.py",
    "run_real_sanity_input_adapter.py",
    "sequence_postprocess_max.py",
    "sequence_transformer_max.py",
    "serve_max.py",
    "sibling_context_max.py",
]

missing = [name for name in names if not (root / name).is_file()]
if missing:
    print("MISSING FILES:", missing)
else:
    output = Path("artifacts/v1.168-max/RELEASE_CANDIDATE.txt")
    output.write_text(
        "# MAX runtime Python files — initial review list\n"
        "# Model weights and additional runtime assets require separate review.\n"
        + "\n".join(str(root / name) for name in names)
        + "\n"
    )
    print("CLEAN RELEASE FILE LIST: READY")
    print("PYTHON FILES:", len(names))
    print("NO EXISTING FILES MOVED OR DELETED")
PY
