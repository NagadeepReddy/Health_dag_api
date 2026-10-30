POD=(podman --root /application1/podman/storage --runroot /run/containers/storage)

AVAIL=$(awk '/MemAvailable:/ {print $2}' /proc/meminfo)
if [ "$AVAIL" -lt 1200000 ]; then
  echo "STOP: Insufficient available memory"
else
  MATCHES=()
  while read -r ID; do
    MOUNTS=$("${POD[@]}" inspect --format '{{json .Mounts}}' "$ID" 2>/dev/null)
    if [[ "$MOUNTS" == *native_batch2_cached_overlay* ]]; then
      MATCHES+=("$ID")
    fi
  done < <("${POD[@]}" ps -a --format '{{.ID}}')

  if [ "${#MATCHES[@]}" -ne 1 ]; then
    echo "STOP: Expected one isolated optimized container; found ${#MATCHES[@]}"
  else
    CID="${MATCHES[0]}"
    STATE=$("${POD[@]}" inspect --format '{{.State.Status}}' "$CID")

    if [ "$STATE" = "exited" ] || [ "$STATE" = "created" ]; then
      if ss -H -ltn '( sport = :8766 )' | grep -q .; then
        echo "STOP: Port 8766 already occupied"
      else
        "${POD[@]}" start "$CID"
        echo "ISOLATED MAX SERVER: RESTART REQUESTED"
      fi
    else
      echo "CONTAINER STATE: $STATE"
    fi
  fi
fi

echo "ORIGINAL MAX HEALTH:"
curl --noproxy '*' -s -o /dev/null \
  -w '%{http_code}\n' --max-time 10 \
  http://127.0.0.1:8765/health
