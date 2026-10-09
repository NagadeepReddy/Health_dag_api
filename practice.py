python - <<'PY'
p="artifacts/v1.168-max/cta_max/parallel_transformer_block.py"
s=open(p).read()

lines=s.splitlines()
out=[]
for line in lines:
    stripped=line.strip()
    if stripped in {
        "dtype=DType.float32,",
        "shape=Shape((256,)),",
        "shape=Shape((2048,)),",
    }:
        continue
    out.append(line)

open(p,"w").write("\n".join(out)+"\n")
print("ORPHANED RMSNORM ARGUMENTS FULLY REMOVED")
PY
