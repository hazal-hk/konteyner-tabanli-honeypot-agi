#!/bin/bash
BLOCKLIST="./data/blocklist.txt"

if [ ! -f "$BLOCKLIST" ]; then
    echo "Blocklist dosyası yok."
    exit 0
fi

while IFS= read -r ip; do
    # Daha önce engellenmiş satırları atla
    [[ "$ip" == BLOCKED:* ]] && continue

    # Eğer iptables'ta yoksa ekle
    if ! sudo iptables -C INPUT -s "$ip" -j DROP 2>/dev/null; then
        sudo iptables -A INPUT -s "$ip" -j DROP
        echo "IP engellendi: $ip"
    else
        echo "IP zaten engellenmiş: $ip"
    fi

    # Satırı BLOCKED: olarak güncelle (sudo ile dosyayı düzenle)
    sudo sed -i "s/^${ip//./\\.}$/BLOCKED:$ip/" "$BLOCKLIST"
done < "$BLOCKLIST"

echo "İşlem tamamlandı. Panelde IP'ler 'engellendi' olarak görünecek."