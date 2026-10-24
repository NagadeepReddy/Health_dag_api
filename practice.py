cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path
import py_compile

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_native_launcher.py")
s = p.read_text()

old = 'sys.argv = ["max.entrypoints.pipelines", "serve", *sys.argv[1:]]'
new = ('sys.argv = ["max.entrypoints.pipelines", "serve", '
       '"--custom-architectures", '
       '"/workspace/artifacts/v1.168-max:cta_native_model", '
       '*sys.argv[1:]]')

if new in s:
    print("CTA CUSTOM ARCHITECTURE FLAG ALREADY INSTALLED")
elif old in s:
    p.write_text(s.replace(old, new, 1))
    print("CTA CUSTOM ARCHITECTURE CONNECTED")
else:
    raise SystemExit("Launcher structure differs — no changes made")

py_compile.compile(str(p), doraise=True)
print("CTA LAUNCHER SYNTAX PASS")
PY
