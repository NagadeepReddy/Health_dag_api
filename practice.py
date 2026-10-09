python - <<'PY'
p="artifacts/v1.168-max/cta_max/parallel_transformer_block.py"

with open(p) as f:
    s=f.read()

s=s.replace("            shape=[2048],\n", "")

with open(p, "w") as f:
    f.write(s)

print("ORPHANED RMSNORM 2048 SHAPE REMOVED")
PY
