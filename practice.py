ORIG=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/native_batch2_release_candidate/maxserve_cta_extension/cta_worker_adapter.py
CLEAN=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/artifacts/v1.168-max/cta_native_batch2_release_candidate/maxserve_cta_extension/cta_worker_adapter.py

diff -u "$ORIG" "$CLEAN" | head -120
