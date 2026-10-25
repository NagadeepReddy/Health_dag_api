P="podman --root /application1/podman/storage --runroot /run/containers/storage"

$P logs --tail 500 cta-native-live 2>&1 | grep -E -A 45 -B 3 'Timeout \(0:00:03\)|Current thread|CTA_NATIVE_FACTORY_ENTERED|Worker failed|Worker died' | tail -130
