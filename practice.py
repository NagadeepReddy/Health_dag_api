cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path

base = Path("/application1/cta_max_true_batch_dev_20261028")
files = {
    "WORKING RUNNER": base / "cta_max/run_live_max_inference.py",
    "BATCH-2 RUNNER": base / "batch2_candidate/cta_max/run_batch2_live_max_inference.py",
    "WORKING NLP GRAPH": base / "cta_max/nlp_bert_in_graph.py",
    "BATCH-2 NLP GRAPH": base / "batch2_candidate/cta_max/nlp_bert_in_graph.py",
}

terms = (
    "nlp_encoder",
    "word_embeddings",
    "weights_registry",
    "aliases",
    "alias",
    "checkpoint",
    "missing nlp weight",
)

for label, path in files.items():
    print(f"\n=== {label} ===")
    print("FILE:", path)
    if not path.is_file():
        print("MISSING")
        continue

    lines = path.read_text().splitlines()
    selected = set()

    for i, line in enumerate(lines):
        if any(term in line.lower() for term in terms):
            selected.update(range(max(0, i-2), min(len(lines), i+4)))

    for i in sorted(selected):
        print(f"{i+1}: {lines[i][:200]}")

print("\nDIAGNOSTIC: COMPLETE")
print("MODEL STARTUP: NOT PERFORMED")
print("FILES MODIFIED: NONE")
PY
