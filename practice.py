find /application1 -maxdepth 4 -type f \
  \( -name '*concurr*.py' -o -name '*concurr*.sh' \
     -o -name '*native*live*.py' \) \
  -not -path '*/podman/*' \
  -not -path '*/.git/*' \
  -printf '%p\n' | sort
