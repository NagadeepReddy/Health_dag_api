python - <<'PY'
from pathlib import Path

base = Path("artifacts/v1.168-max/cta_max")
terms = (
    "weights_registry",
    "InferenceSession(",
    "session.load(",
    "fused_attn_ff_proj.weight",
)

matches = []

for p in sorted(base.rglob("*.py")):
    lines = p.read_text().splitlines()
    for i, line in enumerate(lines):
        if any(term in line for term in terms):
            matches.append((p, lines, i))

print("MATCHES FOUND:", len(matches))

for p, lines, i in matches[:12]:
    print(f"\n===== {p.name}:{i+1} =====")
    for j in range(max(0, i-3), min(len(lines), i+5)):
        print(f"{j+1}: {lines[j]}")

print("\nREAD ONLY — NO FILES MODIFIED")
PY
