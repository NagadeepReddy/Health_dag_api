for pid in 76140 77190 78013 78234; do
  echo "=== PID $pid ==="
  ps -p "$pid" -o pid,ppid,stat,etime,rss,args
  if [ -r "/proc/$pid/cgroup" ]; then
    cat "/proc/$pid/cgroup"
  fi
done
