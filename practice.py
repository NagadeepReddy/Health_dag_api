python - <<'PY'
p="artifacts/v1.168-max/cta_max/parallel_transformer_block.py"

with open(p) as f:
    s=f.read()

s=s.replace(
'        self.norm1.weight.name = "sequence_transformer.ptransformer.0.norm1.weight"\n',
''
)
s=s.replace(
'        self.norm2.weight.name = "sequence_transformer.ptransformer.0.norm2.weight"\n',
''
)

with open(p,"w") as f:
    f.write(s)

print("INVALID RMSNORM NAME MUTATION REMOVED")
PY
