P="podman --root /application1/podman/storage --runroot /run/containers/storage"

$P logs cta-native-live 2>&1 | python3 -c '
import sys
lines = sys.stdin.read().splitlines()
for i, line in enumerate(lines):
    if "Worker failed" in line or "Traceback (most recent call last)" in line:
        print("=== FIRST FAILURE ===")
        print("\n".join(lines[max(0,i-8):i+55]))
        break
else:
    print("\n".join(lines[-50:]))
'
