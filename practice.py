python3 -B - <<'PY'
import subprocess
import json
from pathlib import Path

P = [
    "podman",
    "--root", "/application1/podman/storage",
    "--runroot", "/run/containers/storage"
]

target = "/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029"
ids = subprocess.check_output(P + ["ps", "-q"], text=True).split()

matches = []
for cid in ids:
    info = json.loads(
        subprocess.check_output(P + ["inspect", cid], text=True)
    )[0]
    for m in info.get("Mounts", []):
        if (m.get("Source") == target and
                m.get("Destination") == "/batch2"):
            matches.append(cid)

if len(matches) != 1:
    raise SystemExit(
        f"STOP: Expected one Batch-2 container, found {len(matches)}"
    )

code = '''
from pathlib import Path
import importlib.util

paths = [
    "/batch2/cta_max",
    "/batch2/batch2_candidate/cta_max",
    "/application1/cta_max_true_batch_dev_20261028/batch2_candidate/cta_max",
]

for root in paths:
    p = Path(root)
    print("PACKAGE:", root)
    print("  transformer:", (p / "parallel_transformer_block_2layers.py").is_file())
    print("  NLP:", (p / "nlp_bert_in_graph.py").is_file())
    print("  contract:", (p / "run_batch2_contract.py").is_file())

import cta_max
print("ACTIVE CTA PACKAGE:", list(cta_max.__path__))
print("CONTAINER PATH CHECK: COMPLETE")
'''

r = subprocess.run(
    P + [
        "exec", "-i",
        "-e", "PYTHONDONTWRITEBYTECODE=1",
        matches[0], "/opt/venv/bin/python", "-B", "-"
    ],
    input=code,
    text=True,
    capture_output=True,
    timeout=30
)

print(r.stdout)
if r.returncode:
    print(r.stderr[-1500:])
print("EXIT CODE:", r.returncode)
print("CONTAINERS RESTARTED: NONE")
PY
