echo "=== RELEASE LAUNCHER ==="
sed -n '1,90p' \
/application1/cta_max_native_release_candidate_20261028/cta_native_launcher.py

echo "=== INSTANCE RESOURCES ==="
free -h
df -h /application1

echo "=== PORT 18080 ==="
ss -lnt '( sport = :18080 )'

echo "CHECK COMPLETE — NO CONTAINERS MODIFIED"
