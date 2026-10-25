P="podman --root /application1/podman/storage --runroot /run/containers/storage"

$P logs cta-native-live 2>&1 | grep -iEn -B 8 -A 15 \
'Encountered an error in ModelWorker|An error occurred during scheduling|Worker ended|Worker died|exited with|out of memory|killed|worker process failed' | head -100
