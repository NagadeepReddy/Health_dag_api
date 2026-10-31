python3 -B - <<'PY'
from pathlib import Path
import shutil, hashlib

src = Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate/cta_max")
dst = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/batch2/cta_max")

names = [
    "att_pooling_max",
    "grecbase_aux_branches_batch2_verified",
    "grecbase_fusion_full_head_72_max",
    "grecbase_get_path_max",
    "main_context_max_batch2_verified",
    "nlp_bert_in_graph",
    "nlp_bert_max",
    "parallel_transformer_block_2layers",
    "run_real_sanity_input_adapter",
    "sequence_pooling_max",
    "sequence_postprocess_max",
    "sequence_transformer_max",
    "sibling_context_max_batch2_fix",
]

if not src.is_dir() or dst.exists():
    raise SystemExit("STOP: source missing or destination already exists")

files = [src / (name + ".py") for name in names]
if any(not p.is_file() for p in files):
    raise SystemExit("STOP: required module missing")

if shutil.disk_usage(dst.parent).free < 2 * sum(p.stat().st_size for p in files):
    raise SystemExit("STOP: insufficient disk space")

dst.mkdir(parents=True)

for p in files:
    target = dst / p.name
    shutil.copy2(p, target)
    a = hashlib.sha256(p.read_bytes()).hexdigest()
    b = hashlib.sha256(target.read_bytes()).hexdigest()
    if a != b:
        raise SystemExit("FAIL: checksum mismatch: " + p.name)
    print("PASS:", p.name)

print("MODULES COPIED:", len(files))
print("ORIGINALS UNCHANGED")
PY
