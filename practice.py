find /application1 -maxdepth 6 -type d \( -name 'site-packages' -o -name 'max-full' -o -name 'max' \) -print 2>/dev/null | head -30
