podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  logs cta-native-live 2>&1 | python3 -c '
import sys
lines = sys.stdin.readlines()
for i, line in enumerate(lines):
    if (
        ("CTA WORKER RESPONSE IDS:" in line and "[]" not in line)
        or any(x in line for x in (
            "LIVE RESPONSE ID:",
            "LIVE DISPATCH MATCH:",
            "Failed to put message",
            "Socket operation",
            "ValidationError",
            "Exception in request session",
        ))
    ):
        print("".join(lines[max(0,i-2):i+8]))
'
