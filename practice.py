echo "=== ALTERNATE CONTAINER STORAGE ==="
find /application1 -maxdepth 5 -type d \( -name overlay-images -o -name overlay-containers \) -print 2>/dev/null
echo "=== CTA RELEASE ==="
ls -ld /application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031
ls -lh /application1/CTA_MAX_TEAM_HANDOFF_20261031.tar.gz
