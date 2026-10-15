find . -type f -name 'README.md' \
  -not -path '*/.git/*' \
  -not -path '*/__pycache__/*' \
  -print
