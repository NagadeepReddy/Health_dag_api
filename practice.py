python - <<'PY'
p="artifacts/v1.168-max/cta_max/test_transformer_rms_max.py"

s=open(p).read()

s=s.replace(
    "max_rms = np.asarray(result)",
    """if hasattr(result, "to_numpy"):
    max_rms = result.to_numpy()
elif hasattr(result, "numpy"):
    max_rms = result.numpy()
else:
    max_rms = np.asarray(result)"""
)

open(p,"w").write(s)
print("RMS MAX TENSOR CONVERSION FIXED")
PY

python -m py_compile artifacts/v1.168-max/cta_max/test_transformer_rms_max.py && echo "RMS TEST SYNTAX CLEAN"
