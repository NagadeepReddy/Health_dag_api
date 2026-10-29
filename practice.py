python3 - <<'PY'
from pathlib import Path
import ast
import shutil

p = Path(
    "/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/"
    "native_batch2/cta_worker_adapter.py"
)
backup = p.with_name("cta_worker_adapter_before_cache_fix.py")

assert p.is_file(), "STOP: Adapter missing"
assert not backup.exists(), "STOP: Backup already exists"

source = p.read_text()

old = """                response = pipeline.predict_raw(body)"""
new = """                cached_result = prepared[i]
                original_method = pipeline.preprocess
                calls = [0]

                def cached_preprocess(request_body):
                    calls[0] += 1
                    if calls[0] != 1 or request_body is not body:
                        raise RuntimeError(
                            "Unexpected CTA preprocessing call"
                        )
                    return cached_result

                pipeline.preprocess = cached_preprocess
                try:
                    response = pipeline.predict_raw(body)
                finally:
                    pipeline.preprocess = original_method"""

assert source.count(old) == 1, "STOP: Expected call not found exactly once"

updated = source.replace(old, new)
ast.parse(updated)

shutil.copy2(p, backup)
p.write_text(updated)

print("BACKUP:", backup)
print("PREPROCESS CACHE FIX: INSTALLED")
print("SYNTAX: PASS")
print("MULTI-INFERENCE HANDLING: STILL PENDING")
print("ORIGINAL DS: UNCHANGED")
print("WORKING NATIVE RELEASE: UNCHANGED")
PY
