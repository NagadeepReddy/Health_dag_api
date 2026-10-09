python - <<'PY'
p="artifacts/v1.168-max/cta_max/parallel_transformer_block.py"

with open(p) as f:
    s=f.read()

old="variance1 = ops.mean(x * x, axis=-1, keepdims=True)"
new="variance1 = ops.mean(x * x, axis=-1)"

assert old in s, "Expected keepdims line not found"
s=s.replace(old,new)

with open(p,"w") as f:
    f.write(s)

print("MAX MEAN KEEPDIMS REMOVED")
PY
