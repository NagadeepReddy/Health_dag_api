python - <<'PY'
p="artifacts/v1.168-max/cta_max/parallel_transformer_block.py"

with open(p) as f:
    lines=f.readlines()

lines = [line for i, line in enumerate(lines, 1) if i not in (38, 39)]

with open(p, "w") as f:
    f.writelines(lines)

print("FINAL RMSNORM REMNANTS REMOVED")
PY
