cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
grep -RInE \
'dump_traceback_later|faulthandler|setitimer|signal\.alarm|timeout=3|timeout\(3\)' \
artifacts/v1.168-max artifacts/v1.168 \
--include='*.py' | head -30
