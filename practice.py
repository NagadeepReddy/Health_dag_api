POD=(podman --root /application1/podman/storage --runroot /run/containers/storage)

BASE_STATUS=$(curl --noproxy '*' -sS --max-time 10 \
  -o /dev/null -w '%{http_code}' http://127.0.0.1:8765/health)

[ "$BASE_STATUS" = 200 ] || {
  echo "STOP: Working native MAX server not healthy"
  exit 1
}

PID=$(ss -H -ltnp '( sport = :8766 )' |
  grep -oE 'pid=[0-9]+' | head -1 | cut -d= -f2)

[ -n "$PID" ] || {
  echo "Optimized server already stopped"
  echo "WORKING NATIVE MAX: PASS"
  exit 0
}

CID=$(sed -nE 's/.*libpod-([0-9a-f]{64})\.scope.*/\1/p' \
  "/proc/$PID/cgroup" | head -1)

[ -n "$CID" ] || {
  echo "STOP: Container identity unavailable"
  exit 1
}

"${POD[@]}" inspect --format '{{json .Mounts}}' "$CID" |
grep -Fq 'native_batch2_cached_overlay' || {
  echo "STOP: Container is not isolated optimized MAX"
  exit 1
}

"${POD[@]}" stop --time 15 "$CID" || exit 1

echo "OPTIMIZED TEST SERVER: STOPPED"
echo "OPTIMIZED CODE: PRESERVED"
echo "ORIGINAL DS: UNCHANGED"

curl --noproxy '*' -sS --max-time 10 \
  -o /dev/null -w 'WORKING MAX HTTP STATUS: %{http_code}\n' \
  http://127.0.0.1:8765/health
