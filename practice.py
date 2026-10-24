P="podman --root /application1/podman/storage --runroot /run/containers/storage"
CID=$($P ps -q | head -1)
if [ -n "$CID" ]; then
  $P logs --tail 60 "$CID"
else
  echo "NO RUNNING CONTAINER"
fi
