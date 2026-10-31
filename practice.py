echo "=== APPLICATION1 DISK UUID ==="
blkid /dev/nvme2n1

echo "=== CURRENT MOUNT ==="
findmnt /application1

echo "=== AUTOMOUNT CONFIGURATION ==="
grep -nE '^[^#].*[[:space:]]/application1[[:space:]]' /etc/fstab ||
echo "FSTAB: NOT CONFIGURED"

echo "=== SYSTEMD MOUNT ==="
systemctl is-enabled application1.mount 2>/dev/null || true

echo "=== HANDOFF ARCHIVE ==="
cd /application1 &&
sha256sum -c CTA_MAX_TEAM_HANDOFF_20261031.tar.gz.sha256
