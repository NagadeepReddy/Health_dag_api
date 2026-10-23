cd /application1/sajjna8/rt-pzaas-cta-offers-v1 || exit 1

find . -type f \( -iname '*faiss*.whl' -o -iname '*faiss*.tar.gz' \) -print -quit
