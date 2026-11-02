P=(podman --root /application1/podman/storage --runroot /run/containers/storage)

echo "=== BPLAN REQUEST AND WORKER EVENTS ==="
"${P[@]}" logs --timestamps bplan-debug 2>&1 |
  grep -iE 'BPLAN|POST /bplan|worker failed|validationerror|scheduling|model load|predict_raw|killed|out of memory|oom' |
  tail -100

echo "=== CONTAINER HEALTH ==="
"${P[@]}" inspect bplan-debug \
  --format 'Running={{.State.Running}} ExitCode={{.State.ExitCode}} OOMKilled={{.State.OOMKilled}}'
