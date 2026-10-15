GIT_PAGER=cat git diff --cached --check && \
echo "BRANCH:" && git branch --show-current && \
echo "REMOTE:" && git remote -v && \
echo "STAGED FILES:" && git diff --cached --name-only | wc -l && \
echo "TRACKED CHANGES:" && GIT_PAGER=cat git status --short --untracked-files=no
