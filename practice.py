cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
import ast, json, re

r = Path("artifacts/v1.472-max/pzaas_max")
m = json.loads((r/"pzaas_base_weights/manifest.json").read_text())

required = [
    "remove_tasks_dense1.weight",
    "remove_tasks_dense1.bias",
    "remove_tasks_act1.w1.weight",
    "remove_tasks_act1.w2.weight",
    "remove_tasks_act1.w3.weight",
    "nlp_encoder.embeddings.word_embeddings.weight",
    "nlp_dense_0.weight",
    "nlp_dense_1.weight",
]
for key in required:
    if key not in m or not (r/"pzaas_base_weights"/m[key]["file"]).is_file():
        raise SystemExit(f"STOP: Missing {key}")

updates = {}

# GetPath: connect directly to PZAAS weights
p = r/"grecbase_get_path_max.py"
s = p.read_text()
calls = [
    n for n in ast.walk(ast.parse(s))
    if isinstance(n, ast.Call)
    and ast.unparse(n.func) == "np.load"
]
if len(calls) != 1:
    raise SystemExit("STOP: Unexpected GetPath loader")
old = ast.get_source_segment(s, calls[0])
if "WEIGHTS" not in old or "name" not in old:
    raise SystemExit("STOP: Unexpected GetPath expression")
s = s.replace(old, "load_weight(name)", 1)
s = "from pzaas_max.pzaas_weight_loader import load_weight\n" + s
updates[p] = s

# NLP: remove missing reference-module dependency
p = r/"nlp_bert_in_graph.py"
s = p.read_text()
old_import = "from .nlp_bert_max import WEIGHTS"
if s.count(old_import) != 1:
    raise SystemExit("STOP: Unexpected NLP import")

lines = s.splitlines(keepends=True)
matches = [
    i for i, line in enumerate(lines)
    if "arr = np.load(path).astype(np.float32)" in line
]
if len(matches) != 1:
    raise SystemExit("STOP: Unexpected NLP loader")

i = matches[0]
if i < 2 or "path = WEIGHTS" not in lines[i-2] or \
        "assert path.is_file()" not in lines[i-1]:
    raise SystemExit("STOP: Unexpected NLP loading block")

indent = re.match(r"\s*", lines[i-2]).group()
lines[i-2:i+1] = [
    indent + "arr = np.asarray(load_weight(name), dtype=np.float32)\n"
]
s = "".join(lines).replace(
    old_import,
    "from pzaas_max.pzaas_weight_loader import load_weight",
    1
)
updates[p] = s

for p, source in updates.items():
    compile(source, str(p), "exec")

for p, source in updates.items():
    p.write_text(source)
    print("WIRED:", p.name)

print("PZAAS GETPATH / NLP WIRING: PASS")
print("SYNTAX: PASS")
print("ORIGINAL DS: UNCHANGED")
print("MAX COMPILATION: PENDING")
PY
