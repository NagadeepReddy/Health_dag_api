cd /application1/sajjna8/rt-pzai-bplan-v1 && python3 - <<'PY'
import sys
import importlib.util

print("Python:", sys.executable)
for name in ("torch", "transformers", "faiss", "numpy", "pandas", "max"):
    try:
        found = importlib.util.find_spec(name) is not None
        print(f"{name}: {'AVAILABLE' if found else 'MISSING'}")
    except Exception as e:
        print(f"{name}: CHECK FAILED ({type(e).__name__})")
PY
