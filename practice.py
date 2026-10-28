cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
grep -RInE \
'dump_traceback_later|faulthandler|setitimer|signal\.alarm' \
artifacts/v1.168-max/maxserve_cta_extension \
--include='*.py' | head -40
