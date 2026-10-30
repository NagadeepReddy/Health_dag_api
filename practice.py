python3 - <<'PY'
from pathlib import Path
import ast

base = Path("/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/native_batch2_cached_overlay")
target = base / "cta_native_batch2_import_first.py"

assert base.is_dir(), "STOP: Isolated overlay missing"
assert (base / "cta_native_batch2_proven_server.py").is_file(), "STOP: Existing native server missing"
assert Path("/application1/cta_max_true_batch_dev_20261028/batch2_candidate/cta_max").is_dir(), "STOP: Batch-2 candidate missing"
assert not target.exists(), "STOP: Launcher already exists"

source = '''
import sys
import importlib
import importlib.util
import runpy

sys.path.insert(0, "/batch2")
sys.path.insert(1, "/workspace/artifacts/v1.168-max")

import cta_max
cta_max.__path__.insert(0, "/batch2/cta_max")
importlib.invalidate_caches()

modules = [
    "grecbase_aux_features_max",
    "grecbase_aux_branches_max",
    "parallel_transformer_block_2layers",
    "nlp_bert_in_graph",
]

for name in modules:
    spec = importlib.util.find_spec("cta_max." + name)
    assert spec and spec.origin.startswith("/batch2/cta_max/"), (
        "STOP: Wrong module loaded: " + name
    )
    print("BATCH-2 MODULE:", name, spec.origin, flush=True)

print("BATCH-2 IMPORT PRIORITY: PASS", flush=True)

runpy.run_path(
    "/workspace/artifacts/v1.168-max/maxserve_cta_extension/cta_native_batch2_proven_server.py",
    run_name="__main__"
)
'''

ast.parse(source)
target.write_text(source)

print("ISOLATED LAUNCHER: CREATED")
print("SYNTAX: PASS")
print("ORIGINAL DS/MAX: UNCHANGED")
print("CONTAINERS RESTARTED: NONE")
print("NEXT: RUN CORRECTED NATIVE BATCH-2")
PY
