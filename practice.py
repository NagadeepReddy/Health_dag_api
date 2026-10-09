python - <<'PY'
p="artifacts/v1.168-max/cta_max/run_transformer_max.py"

with open(p, "r") as f:
    s=f.read()

s=s.replace("\\n", "\n")

with open(p, "w") as f:
    f.write(s)

print("RUNNER LITERAL NEWLINES FIXED")
PY

python -m py_compile artifacts/v1.168-max/cta_max/run_transformer_max.py && \
echo "RUNNER SYNTAX CLEAN"
