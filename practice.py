python - <<'PY'
p="artifacts/v1.168-max/cta_max/parallel_transformer_block.py"
s=open(p).read()

for name in [
    "sequence_transformer.ptransformer.0.norm1.weight",
    "sequence_transformer.ptransformer.0.norm2.weight",
]:
    lines=s.splitlines()
    lines=[x for x in lines if name not in x]
    s="\n".join(lines)+"\n"

open(p,"w").write(s)
print("ORPHANED RMSNORM WEIGHT ARGUMENTS REMOVED")
PY
