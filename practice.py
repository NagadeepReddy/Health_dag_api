podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  logs cta-native-live 2>&1 | python3 -c '
import sys
lines = sys.stdin.readlines()
for i, line in enumerate(lines):
    if any(x in line for x in (
        "CTA HTTP QUEUE ITEM:",
        "CTA HTTP BRIDGE ENQUEUED:",
        "Traceback",
        "Exception",
        "Error in background",
    )):
        print("".join(lines[max(0,i-2):i+8]))
'
