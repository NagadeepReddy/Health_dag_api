cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
grep -RInE \
'def open_channel|def response_worker|response_worker|response_queue.get|SchedulerResult' \
/opt/venv/lib/python3.12/site-packages/max/serve/queues.py \
/opt/venv/lib/python3.12/site-packages/max/serve/pipelines \
--include='*.py' 2>/dev/null | head -65
