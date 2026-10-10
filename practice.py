python - <<'PY'
p = "artifacts/v1.168-max/cta_max/test_transformer_attention_max.py"

s = open(p).read()

s = s.replace(
    "max_probs = np.asarray(outputs[0])",
    "max_probs = outputs[0].to_numpy()"
)

s = s.replace(
    "max_out = np.asarray(outputs[1])",
    "max_out = outputs[1].to_numpy()"
)

open(p, "w").write(s)
PY

python -m py_compile artifacts/v1.168-max/cta_max/test_transformer_attention_max.py && \
echo "ATTENTION OUTPUT CONVERSION FIXED - SYNTAX CLEAN"
