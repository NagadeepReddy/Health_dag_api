cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && python3 -S -B - <<'PY'
from pathlib import Path
import ast
import hashlib

src = Path("artifacts/v1.168-max/maxserve_cta_extension")
dst = Path("/application1/cta_max_native_release_candidate_20261028")

markers = (
    "CTA ROUTE QUEUE ID:",
    "CTA RECEIVER ENGINE ID:",
    "CTA RESPONSE ID MATCH:",
    "CTA RESPONSE SOCKET RECEIVED:",
    "CTA HTTP FANOUT:",
    "CTA QUEUE CONNECTION:",
    "CTA ACTUAL ENGINE QUEUE:",
)

class NormalizeDiagnostics(ast.NodeTransformer):
    def visit_Expr(self, node):
        if isinstance(node.value, ast.Call):
            call = node.value
            if isinstance(call.func, ast.Name) and call.func.id == "print":
                strings = [
                    x.value for x in ast.walk(call)
                    if isinstance(x, ast.Constant)
                    and isinstance(x.value, str)
                ]
                if any(m in s for m in markers for s in strings):
                    return ast.copy_location(ast.Pass(), node)
        return self.generic_visit(node)

assert src.is_dir() and dst.is_dir(), "STOP: Directory missing"

originals = {
    str(p.relative_to(src)): p
    for p in src.rglob("*.py")
}
candidates = {
    str(p.relative_to(dst)): p
    for p in dst.rglob("*.py")
}

assert originals.keys() == candidates.keys(), \
    "STOP: Python file sets differ"

changed = []

for name in sorted(originals):
    a = originals[name].read_text()
    b = candidates[name].read_text()

    original_ast = NormalizeDiagnostics().visit(ast.parse(a))
    candidate_ast = NormalizeDiagnostics().visit(ast.parse(b))

    assert ast.dump(original_ast) == ast.dump(candidate_ast), \
        f"STOP: Unexpected logic difference in {name}"

    if hashlib.sha256(a.encode()).digest() != \
       hashlib.sha256(b.encode()).digest():
        changed.append(name)

print("RELEASE CANDIDATE LOGIC: PASS")
print("PYTHON FILES VERIFIED:", len(originals))
print("FILES WITH DIAGNOSTIC CLEANUP:", len(changed))
print("UNEXPECTED LOGIC CHANGES: NONE")
print("WORKING HTTP 200 SOURCE: UNCHANGED")
print("ORIGINAL DS CODE: UNCHANGED")
print("MODEL STARTUP: NOT PERFORMED")
print("RUNTIME REVALIDATION: STILL PENDING")
PY
