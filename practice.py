ORIG=/application1/CTA_MAX_TRUE_BATCH2_DEV_20261029/real_max_batch2_backend.py
CLEAN=/application1/CTA_MAX_CLEAN_VM_CANDIDATE_20261030/artifacts/v1.168-max/cta_max/real_max_batch2_backend.py

diff -u "$ORIG" "$CLEAN" | head -120
