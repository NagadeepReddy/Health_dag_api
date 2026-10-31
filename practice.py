echo "=== DISK UUID ==="
sudo blkid /dev/nvme2n1

echo "=== PERSISTENT MOUNT CONFIGURATION ==="
grep -nE 'application1|nvme2n1|UUID=' /etc/fstab || true

echo "=== MOUNT HEALTH ==="
mountpoint /application1 &&
echo "APPLICATION1 MOUNT: PASS"
