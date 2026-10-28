for pid in 76140 77190 78013 78234; do
  echo "=== PID $pid ==="
  cid=$(sed -n 's/.*libpod-\([0-9a-f]\{64\}\)\.scope.*/\1/p' "/proc/$pid/cgroup" 2>/dev/null | head -1)

  if [ -n "$cid" ]; then
    podman \
      --root /application1/podman/storage \
      --runroot /run/containers/storage \
      inspect "$cid" \
      --format 'NAME={{.Name}} STATUS={{.State.Status}} IMAGE={{.Config.Image}} COMMAND={{json .Config.Cmd}}'
  else
    echo "Container ID unavailable"
  fi
done
