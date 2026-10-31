python3 -B - <<'PY'
from pathlib import Path
import shutil, ast, hashlib

src = Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate/cta_max/nlp_bert_max.py")
dst = Path("/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/artifacts/v1.168-max/cta_max/nlp_bert_max.py")

assert src.is_file(), "STOP: Development module missing"
assert dst.parent.is_dir(), "STOP: Clean package missing"

ast.parse(src.read_bytes(), filename=str(src))

if dst.exists():
    assert dst.read_bytes() == src.read_bytes(), "STOP: Existing clean file differs"
    print("CLEAN MODULE: ALREADY PRESENT AND MATCHING")
else:
    shutil.copy2(src, dst)
    print("CLEAN MODULE: COPIED")

assert hashlib.sha256(src.read_bytes()).digest() == hashlib.sha256(dst.read_bytes()).digest()

print("MODULE CHECKSUM: PASS")
print("ORIGINAL CTA: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
PY
