python - <<'PY'
p="artifacts/v1.168-max/cta_max/parallel_transformer_block.py"
with open(p) as f:
    lines=f.readlines()

for i in range(30, min(46, len(lines)+1)):
    print(f"{i:03}: {lines[i-1]!r}")
PY
