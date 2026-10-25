P="podman --root /application1/podman/storage --runroot /run/containers/storage"

$P logs --since 15m --timestamps cta-native-live 2>&1 | python3 -c '
import sys
keys = (
    "CTA REQUEST RECEIVED",
    "CTA NATIVE RESPONSE TYPES",
    "CTA WORKER RESPONSE IDS: [RequestID",
    "LIVE RESPONSE ID:",
    "LIVE DISPATCH MATCH:",
    "CTA CALLBACK EXECUTED",
    "CTA QUEUE SIZE:",
    "CTA HTTP QUEUE ITEM:",
    "CTA HTTP BRIDGE ENQUEUED:",
    "Traceback",
    "Exception",
    "ERROR:",
)
matches = [line.strip() for line in sys.stdin if any(k in line for k in keys)]
print("=== LATEST REQUEST TIMELINE ===")
print("\n".join(matches[-30:]) if matches else "NO MATCHING EVENTS")
'
