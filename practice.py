podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  logs --tail 500 bplan-debug 2>&1 |
  grep -E 'POST /bplan/predict|BPLAN REAL MAX|BPLAN TRACE|BPLAN RESPONSE|ERROR|Traceback' |
  tail -60
