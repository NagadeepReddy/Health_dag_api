echo "=== ACTUAL LIVE MAX SERVER ==="
ps -p 326785 -o pid,ppid,lstart,etime,cmd

echo "=== LIVE WORKERS ==="
ps --ppid 326785 -o pid,ppid,stat,etime,cmd

echo "=== LIVE CONTAINER IDENTITY ==="
cat /proc/326785/cgroup

echo "=== OPTIMIZED BACKEND MOUNT ==="
LIVE=/proc/326785/root/batch2/real_max_batch2_backend.py
DEV=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/real_max_batch2_backend.py

if [ -f "$LIVE" ]; then
    sha256sum "$LIVE" "$DEV"
    if cmp -s "$LIVE" "$DEV"; then
        echo "OPTIMIZED BACKEND FILE: MOUNTED"
    else
        echo "LIVE BACKEND FILE: DIFFERENT"
    fi
else
    echo "LIVE BACKEND MOUNT: NOT FOUND"
fi
