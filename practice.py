python - <<'PY'
p="artifacts/v1.168-max/cta_max/run_transformer_max.py"

with open(p) as f:
    s=f.read()

old='''weights["weight"] = weights[
    "sequence_transformer.ptransformer.0.fn.norm1.g"
]'''

new='''weights["weight"] = WeightData(
    np.load(
        "artifacts/v1.168-max/cta_max/sequence_weights/"
        "sequence_transformer.ptransformer.0.fn.norm1.g.npy"
    ),
    name="weight",
)'''

assert old in s, "Old failing norm1 registry mapping not found"
assert "import numpy as np" in s, "numpy import missing"
assert "WeightData" in s, "WeightData import missing"

s=s.replace(old,new,1)

with open(p,"w") as f:
    f.write(s)

print("TRANSFORMER NORM1 DIRECT WEIGHT MAPPED")
PY
