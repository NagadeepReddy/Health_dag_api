P="podman --root /application1/podman/storage --runroot /run/containers/storage"

$P logs cta-native-live 2>&1 | \
grep -iEn -B 5 -A 8 \
'worker process|worker failed|worker healthy|worker exited|spawn|fatal|killed|traceback|exception|error' | \
grep -v 'CTA WORKER RESPONSE IDS: \[\]' | head -110
