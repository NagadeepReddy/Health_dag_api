DIR=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev

for f in bplan_worker_registration.py bplan_native_worker_adapter.py bplan_http_pipeline.py; do
  echo "========== $f =========="
  if [ -f "$DIR/$f" ]; then
    nl -ba "$DIR/$f" | head -180
  else
    echo "NOT FOUND"
  fi
done
