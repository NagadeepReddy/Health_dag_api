find /application1/CTA_MAX_TEAM_HANDOFF_STAGE_20261031 \
-type f \( \
-name 'cta_native_launcher.py' -o \
-name 'cta_native_scheduler.py' -o \
-name 'cta_worker_adapter.py' -o \
-name 'cta_router.py' -o \
-name 'cta_http_pipeline.py' \
\) -print | sort
