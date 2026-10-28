echo "=== TOP MEMORY CONSUMERS WITH OWNERS AND COMMANDS ==="
ps -eo pid,ppid,user,etime,rss,stat,args --sort=-rss --cols 260 | head -18

echo "=== ACTIVE PODMAN CONTAINERS ==="
podman \
  --root /application1/podman/storage \
  --runroot /run/containers/storage \
  ps --format 'ID={{.ID}} NAME={{.Names}} STATUS={{.Status}}'
