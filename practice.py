cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
p = Path("artifacts/v1.472/core-artifact/pipeline.py")
s = p.read_text().splitlines()
for a,b in [(1180,1260),(4717,4790),(7074,7120)]:
    print(f"\n===== LINES {a}-{b} =====")
    for i in range(a-1,min(b,len(s))):
        print(f"{i+1}: {s[i][:200]}")
PY
