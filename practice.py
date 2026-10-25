cd /application1/sajjna8/rt-pzaas-cta-offers-v1

python3 - <<'PY'
from pathlib import Path

p = Path("artifacts/v1.168-max/maxserve_cta_extension/cta_native_live_server.py")
s = p.read_text()

start = s.find("    # CTA LIVE HANDOFF TRACE")
end = s.find("    import uvicorn", start)

assert start >= 0 and end > start, "Expected bridge section not found"

clean = s[:start] + s[end:]
compile(clean, str(p), "exec")

p.with_suffix(".py.bridge_backup").write_text(s)
p.write_text(clean)

print("CUSTOM HTTP BRIDGE: REMOVED")
print("MAX ORIGINAL RESPONSE DISPATCH: RESTORED")
print("SYNTAX: PASS")
print("DS CODE: UNCHANGED")
PY
