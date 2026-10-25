podman --root /application1/podman/storage \
--runroot /run/containers/storage \
run --rm --pull=never --network=none \
--entrypoint /opt/venv/bin/python \
localhost/cta-max-faiss:local -c '
from max.pipelines.lib import SupportedEncoding, WeightsFormat
print("ENCODINGS:", [x.name for x in SupportedEncoding])
print("WEIGHT FORMATS:", [x.name for x in WeightsFormat])
'
