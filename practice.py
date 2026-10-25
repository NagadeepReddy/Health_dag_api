P="podman --root /application1/podman/storage --runroot /run/containers/storage"
sleep 15
$P logs --tail 70 cta-native-live 2>&1
