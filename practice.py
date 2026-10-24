python3 - <<'PY'
from pathlib import Path
import re

s = Path("/tmp/cta_socket_trace.log").read_text(errors="replace")

http = re.findall(
    r'request_id=\s*(?:RequestID\(value=)?[\'"]?([0-9a-f]{32})',
    s, re.I
)
received = re.findall(
    r'CTA SOCKET RECEIVE:.*?RequestID\(value=[\'"]([0-9a-f]{32})',
    s, re.I
)

print("HTTP REQUEST ID:", http[-1] if http else "NOT FOUND")
print("ZMQ RESPONSE ID:", received[-1] if received else "NOT FOUND")

if http and received:
    print("SAME REQUEST:", "PASS" if http[-1] == received[-1] else "FAIL")
else:
    print("SAME REQUEST: NOT VERIFIED")

print("HTTP STATUS:", "PRESENT" if "CTA NATIVE HTTP STATUS:" in s else "MISSING")
PY
