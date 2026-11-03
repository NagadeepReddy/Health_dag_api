cd /application1/sajjna8/rt-pzaas-v1.0 && python3 - <<'PY'
from pathlib import Path
p=Path("artifacts/v1.472/core-artifact/pipeline.py")
s=p.read_text().splitlines()
for a,b in [(1260,1338),(6718,6790),(6980,7090)]:
    print(f"\n{'='*20} LINES {a}-{b} {'='*20}")
    for i in range(a-1,min(b,len(s))):
        print(f"{i+1}: {s[i][:180]}")
PY
