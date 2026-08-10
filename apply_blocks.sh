#!/bin/bash
BLOCKLIST="./data/blocklist.txt"

if [ ! -f "$BLOCKLIST" ]; then
    echo "Blocklist dosyası yok."
    exit 0
fi

while IFS= read -r ip; do
    # Daha önce engellenmiş mi diye kontrol et
    if ! sudo iptables -C INPUT -s "$ip" -j DROP 2>/dev/null; then
        sudo iptables -A INPUT -s "$ip" -j DROP
        echo "IP engellendi: $ip"
    fi
done < "$BLOCKLIST"

# Blocklist'i temizle (isteğe bağlı)
sudo sh -c "> $BLOCKLIST"