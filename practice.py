git add --dry-run -- artifacts/v1.168-max/cta_max/__init__.py

echo "ORIGINAL DS TRACKED CHANGES:"
git status --short --untracked-files=no -- artifacts/v1.168
