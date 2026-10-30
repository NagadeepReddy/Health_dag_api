
POD=(podman --root /application1/podman/storage --runroot /run/containers/storage)
CID=cta-batch2-trace-8766-10g

"${POD[@]}" inspect --format 'STATE={{.State.Status}} WORKDIR={{.Config.WorkingDir}} MOUNTS={{range .Mounts}}{{.Destination}}={{.Source}} {{end}}' "$CID"

"${POD[@]}" exec "$CID" /opt/venv/bin/python -B -c '
import os
p="artifacts/v1.168-max/cta_max/sequence_weights/fn_norm1_g.npy"
print("CONTAINER CWD:", os.getcwd())
print("SERVER CWD:", os.readlink("/proc/1/cwd"))
print("RELATIVE WEIGHT:", os.path.isfile(p))
print("WORKSPACE WEIGHT:", os.path.isfile("/workspace/"+p))
'
