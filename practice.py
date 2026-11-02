ROOT=/application1/sajjna8/rt-pzai-bplan-v1
DIR="$ROOT/artifacts/v1.113-max/maxserve_bplan_extension/bplan_native_serve_dev"

for name in bplan_router.py bplan_http_pipeline.py bplan_spawn_worker.py bplan_native_scheduler.py bplan_context.py; do
  echo "========== $name =========="
  if [ -f "$DIR/$name" ]; then
    grep -nE 'class |def |async def |open_channel|response_worker|engine_queue|request_queue|response_queue|send_request|send_response|model_factory|predict|__aenter__|__aexit__' "$DIR/$name" | head -65
  else
    echo "FILE NOT FOUND"
  fi
done
