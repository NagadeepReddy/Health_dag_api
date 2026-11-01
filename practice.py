REF=/application1/sajjna8/rt-pzai-bplan-v1/artifacts/v1.113-max/maxserve_bplan_extension/cta_reference
grep -nE '^(class |def |async def |from |import )|predict_raw|predict_batch|MAX|Scheduler' "$REF"/*.py | head -110
