SRC=/application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031/artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension
DST=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension
mkdir -p "$DST/cta_reference" && \
for f in cta_native_launcher.py cta_native_scheduler.py cta_worker_adapter.py cta_router.py cta_http_pipeline.py; do
  cp -n "$SRC/$f" "$DST/cta_reference/" || exit 1
done && ls -lh "$DST/cta_reference"
