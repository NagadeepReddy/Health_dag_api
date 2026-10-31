podman --root /application1/podman/storage \
  --runroot /run/containers/storage \
  exec cta-clean-native-batch2 /opt/venv/bin/python -c \
  "from pathlib import Path; import numpy as np; p=Path('/batch2/cta_max/grecbase_integration_weights/seq_dense_weight.npy'); print('RESOLVED:',p.resolve()); print('LOAD:',np.load(p).shape)"
