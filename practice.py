cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast

root = Path("artifacts/v1.472")
files = [
    root/"Model.py",
    root/"core-artifact/pipeline.py",
    root/"core-artifact/bplan/pipeline.py",
    root/"core-artifact/dynamic_offer/pipeline.py",
    root/"core-artifact/ngd_pros/pipeline.py",
]
for p in files:
    print(f"\n{'='*60}\nFILE: {p}")
    if not p.is_file():
        print("NOT FOUND")
        continue
    s = p.read_text(errors="replace")
    print("LINES:", len(s.splitlines()))
    try:
        tree = ast.parse(s)
    except SyntaxError as e:
        print("PARSE ERROR:", e)
        continue
    for n in ast.walk(tree):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            name = n.name.lower()
            if any(k in name for k in (
                "predict", "preprocess", "postprocess", "infer",
                "load", "model", "route", "init", "process"
            )):
                print(f"  LINE {n.lineno}: {type(n).__name__} {n.name}")
    for i, line in enumerate(s.splitlines(), 1):
        if any(k in line.lower() for k in (
            "torch.load(", "faiss.read_index(", "predict_raw(",
            "model_0_", "pipeline(", "model.predict("
        )):
            print(f"  REF {i}: {line.strip()[:150]}")
PY
