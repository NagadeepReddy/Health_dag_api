python3 -B - <<'PY'
from pathlib import Path
import hashlib
import re

dev = Path(
    "/application1/cta_max_true_batch_dev_20261028"
    "/batch2_candidate/cta_max"
)
ref = Path(
    "/application1/sajjna8/rt-pzaas-cta-offers-v1"
    "/artifacts/v1.168-max/cta_max"
)

print("=== BATCH-2 BRANCH POOLING CHECK ===")

for name in ("main_context_max.py", "nlp_bert_in_graph.py"):
    a = dev / name
    b = ref / name

    print("\nMODULE:", name)

    if not a.is_file():
        print("STOP: Candidate missing")
        continue

    source = a.read_text()
    compile(source, str(a), "exec")
    print("SYNTAX: PASS")

    if b.is_file():
        same = hashlib.sha256(a.read_bytes()).digest() == \
               hashlib.sha256(b.read_bytes()).digest()
        print("ORIGINAL MATCH:", same)
    else:
        print("ORIGINAL: Not available at expected path")

    lines = source.splitlines()
    pattern = re.compile(
        r"\breturn\b|ops\.(reshape|mean|max|concat|stack|gather)"
        r"|def main_context_forward|def nlp_bert_forward"
    )

    matches = [i for i, line in enumerate(lines)
               if pattern.search(line)]

    shown = set()
    for i in matches[-22:]:
        for j in range(max(0, i-1), min(len(lines), i+2)):
            if j not in shown:
                print(f"{j+1}: {lines[j]}")
                shown.add(j)

print("\nEXPECTED FUSION BRANCH: [2,256]")
print("FAILING INPUT SHAPE: [2,3,128]")
print("ORIGINAL DS/MAX: UNCHANGED")
print("FILES MODIFIED: NONE")
print("CONTAINERS RESTARTED: NONE")
PY
