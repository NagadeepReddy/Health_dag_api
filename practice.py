python - <<'PY'
p="artifacts/v1.168-max/cta_max/parallel_transformer_block.py"

with open(p) as f:
    lines=f.readlines()

out=[]
for line in lines:
    if "norm1_g = self.norm1_g" in line:
        continue
    if "x_norm = x_norm * norm1_g" in line:
        indent=line[:len(line)-len(line.lstrip())]
        out.append(indent + "x_norm = self.norm1(x)\n")
    else:
        out.append(line)

with open(p,"w") as f:
    f.writelines(out)

print("NORM1_G RUNTIME REFERENCE FULLY REMOVED")
PY
