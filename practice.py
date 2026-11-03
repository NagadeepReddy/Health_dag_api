P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

echo "=== STOP OLD BPLAN DEBUG ==="

if "${P[@]}" ps --format '{{.Names}}' | grep -Fxq 'bplan-debug'; then
  "${P[@]}" stop -t 15 bplan-debug
else
  echo "bplan-debug is not running; no unknown service stopped."
fi

echo "=== CHECK PORT 18768 ==="

if ss -lnt '( sport = :18768 )' | grep -q LISTEN; then
  echo "PORT STILL OCCUPIED — identify owner:"
  ss -lntp '( sport = :18768 )'
else
  echo "PORT 18768: FREE — READY FOR FINAL TEST"
fi
