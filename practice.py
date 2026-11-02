echo "=== BPLAN / MAX WORKER PROCESSES ==="
ps -eo pid,ppid,stat,etime,args | grep -E \
'[b]plan_native|[m]odel_worker|[m]ultiprocessing|[m]ax.serve|[p]ython' \
| head -45

echo "=== BPLAN SERVER LISTENER ==="
ss -ltnp | grep ':18768' || echo "BPLAN PORT NOT LISTENING"
