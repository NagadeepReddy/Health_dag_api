echo "=== MOUNTS ==="
findmnt /application1
echo "=== DISKS ==="
lsblk -f
echo "=== ROOT FOLDERS ==="
ls -ld /application /application1 2>&1
