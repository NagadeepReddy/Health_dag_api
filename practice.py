echo "=== PERSISTENT MOUNT ==="
findmnt -T /application1 \
  -o TARGET,SOURCE,FSTYPE,OPTIONS

echo "=== DISK DETAILS ==="
lsblk -f

echo "=== HANDOFF BACKUP ==="
ls -lh /application1/CTA_MAX_TEAM_HANDOFF_20261031.tar.gz*

echo "=== VERIFY BACKUP ==="
cd /application1 &&
sha256sum -c CTA_MAX_TEAM_HANDOFF_20261031.tar.gz.sha256
