cd /application1/sajjna8/rt-pzaas-cta-offers-v1 && \
grep -niE 'response.worker|zmq|msgpack|serializ|deserializ|decode|unpack|queue.*error|task exception|traceback|connection.*error' \
/application1/cta_env_e2e_1028.log \
| grep -v 'CTA WORKER RESPONSE IDS:' \
| tail -45
