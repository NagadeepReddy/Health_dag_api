python3 - <<'PY'
from pathlib import Path
import tarfile

base = Path("/application1")
candidate = base / "cta_max_true_batch_dev_20261028/batch2_candidate/cta_max"
original = base / "sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_max"
backend = base / "CTA_MAX_TRUE_BATCH2_DEV_20261029"

names = [
    "grecbase_fusion_batch2_draft.py",
    "grecbase_aux_features_max.py",
    "grecbase_aux_branches_max.py",
    "main_context_max.py",
    "nlp_bert_in_graph.py",
    "parallel_transformer_block_2layers.py",
    "run/batch2_contract.py",
]

sources = (
    [(candidate / n, "candidate/" + n) for n in names]
    + [
        (original / "grecbase_fusion_full_head_72_max.py",
         "reference/grecbase_fusion_full_head_72_max.py"),
        (original / "main_context_max.py",
         "reference/main_context_max.py"),
        (original / "nlp_bert_in_graph.py",
         "reference/nlp_bert_in_graph.py"),
        (backend / "real_max_batch2_backend.py",
         "backend/real_max_batch2_backend.py"),
    ]
)

out = backend / "batch2_source_review.tar.gz"
assert out.parent.is_dir(), "STOP: Development directory missing"
assert (candidate / names[0]).is_file(), "STOP: Active graph missing"

with tarfile.open(out, "w:gz") as archive:
    for src, name in sources:
        if src.is_file():
            archive.add(src, arcname=name)
            print("INCLUDED:", name)
        else:
            print("MISSING:", name)

print("SOURCE ARCHIVE:", out)
print("ORIGINAL DS/MAX: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
PY
