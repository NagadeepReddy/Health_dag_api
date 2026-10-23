(history; cat ~/.bash_history 2>/dev/null) | \
grep -E 'cta_native_launcher.py|max serve' | \
tail -15
