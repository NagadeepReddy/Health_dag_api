
cd /application1/sajjna8/rt-pzaas-v1.0 && \
echo "=== PZAAS EXISTING DEPENDENCY RECOVERY ===" && \
find \
/application1/sajjna8 \
/opt/venv/lib \
/usr/local/lib \
/usr/lib \
\( -type d \( \
-name apscheduler -o \
-name einops -o \
-name sklearn \
\) -o -type f \( \
-name pzaas_live_pack_72.py -o \
-name pzaas_worker_adapter.py \
\) \) -print 2>/dev/null | sort -u && \
echo "=== CONFIGURED PACKAGE SOURCE ===" && \
python3 -m pip config list 2>/dev/null | \
sed -E 's#(https?://)[^/@ ]+@#\1[credentials]@#g' | \
grep -Ei 'index|trusted-host' || true
