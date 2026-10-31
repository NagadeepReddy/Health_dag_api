python3 -B - <<'PY'
from pathlib import Path
import hashlib

src = Path("/application1/sajjna8/rt-pzaas-cta-offers-v1/artifacts/v1.168-max/cta_max")
dst = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/artifacts/v1.168-max/cta_max")

names = [
    "att_pooling_max",
    "grecbase_aux_branches_max",
    "grecbase_fusion_full_head_72_max",
    "grecbase_get_path_max",
    "main_context_max",
    "nlp_bert_in_graph",
    "parallel_transformer_block_2layers",
    "run_real_sanity_input_adapter",
    "sequence_postprocess_max",
    "sequence_transformer_max",
    "sibling_context_max",
]

assert src.is_dir() and dst.is_dir(), "STOP: package directory missing"
assert not src.is_symlink() and not dst.is_symlink(), "STOP: symlink directory"

# Verify everything before copying.
for name in names:
    a, b = src / f"{name}.py", dst / f"{name}.py"
    assert a.is_file() and not a.is_symlink(), f"STOP: invalid source {name}"
    assert not b.is_symlink(), f"STOP: destination symlink {name}"
    if b.exists():
        assert b.is_file() and a.read_bytes() == b.read_bytes(), \
            f"STOP: existing destination differs {name}"

for name in names:
    a, b = src / f"{name}.py", dst / f"{name}.py"
    if not b.exists():
        with b.open("xb") as f:
            f.write(a.read_bytes())
        print("COPIED:", name)
    else:
        print("ALREADY IDENTICAL:", name)

    assert hashlib.sha256(a.read_bytes()).digest() == \
           hashlib.sha256(b.read_bytes()).digest(), f"FAIL: {name}"

print("MAX MODULE COPIES VERIFIED: PASS")
print("ORIGINAL FILES: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
PY
