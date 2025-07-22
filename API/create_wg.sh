#!/usr/bin/bash
# ./create_wg.sh {token} {name} {number}

WEB_PATH="/var/www/html/spectralvpn.ru"
WG_PATH="/etc/wireguard"
HOST="217.11.166.248:51820"

if ! [-e "$WEB_PATH/$1"]; then
    mkdir "$WEB_PATH/$1/"
fi

s=$($(cat $WG_PATH/score.bin)+1)

wg genkey | tee /tmp/wg-prv-$2-$3 | wg pubkey | tee /tmp/wg-pub-$2-$3
prk=$(cat /tmp/wg-prv-$2-$3)
puk=$(cat /tmp/wg-pub-$2-$3)

echo -e "\n[Peer]\nPublicKey = $puk\nAllowedIPs = 10.66.66.$s/32\n" >> $WG_PATH/wg0.conf

echo -e "[Interface]\nAddress = 10.66.66.$s/32\nDNS = 8.8.8.8, 8.8.4.4\nPrivateKey = $prk\n\n[Peer]AllowedIPs = 0.0.0.0/0, ::/0\nEndpoint = $HOST\nPersistentKeepalive = 20\nPublicKey = EjnZqvkE403vSb/INlrQ5y4N3rUHn2xF0bRP97Hp2VY=" > $WEB_PATH/$1/wg-$2-$3.conf
echo -e "[Interface]\nAddress = 10.66.66.$s/32\nDNS = 8.8.8.8, 8.8.4.4\nPrivateKey = $prk\nJc = 120\nJmin = 98\nJmax = 911\nS1 = 0\nS2 = 0\nH1 = 1\nH2 = 2\nH3 = 3\nH4 = 4\n\n[Peer]AllowedIPs = 0.0.0.0/0, ::/0\nEndpoint = $HOST\nPersistentKeepalive = 20\nPublicKey = EjnZqvkE403vSb/INlrQ5y4N3rUHn2xF0bRP97Hp2VY=" > $WEB_PATH/$1/awg-$2-$3.conf

systemctl restart wg-quick@wg0.service

echo -e "/$1/wg-$2-$3.conf,/$1/awg-$2-$3.conf"

unset WEB_PATH
unset WG_PATH
unset HOST
unset s
unset prk
unset puk
