echo "=== NATIVE MAX SERVER ==="
ps -p 326785 -o pid,ppid,etime,%cpu,%mem,rss,stat,wchan:25,cmd

echo "=== WORKER PROCESSES ==="
ps --ppid 326785 -o pid,ppid,etime,%cpu,%mem,rss,stat,wchan:25,cmd

echo "=== SERVER THREADS ==="
ps -T -p 326785 -o pid,tid,%cpu,stat,wchan:25,comm | head -30
