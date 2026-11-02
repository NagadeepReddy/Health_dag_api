podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  logs --tail 1500 bplan-debug 2>&1 | python3 -c '
import sys
lines = sys.stdin.read().splitlines()
hits = [i for i, line in enumerate(lines) if "POST /bplan/predict" in line]
if hits:
    i = hits[-1]
    print("=== LAST BPLAN HTTP REQUEST ===")
    print("\n".join(lines[max(0,i-90):min(len(lines),i+100)]))
else:
    print("=== LATEST BPLAN SERVER LOGS ===")
    print("\n".join(lines[-100:]))
'
