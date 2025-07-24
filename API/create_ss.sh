#!/usr/bin/bash
# ./create_ss.sh {token} {name} {number}

WEB_PATH="/var/www/html/spectralvpn.ru"
SS_PATH="/etc/shadowsocks-libev"

if ! [-e "$WEB_PATH/$1"]; then
    mkdir "$WEB_PATH/$1/"
fi

p=$(cat $SS_PATH/ports.bin)
echo -e $($p+1) > $SS_PATH/ports.bin

echo -e "{\"server\":\"0.0.0.0\",\"server_port\":$p,\"local_port\":1080,\"password\":\"$1\",\"timeout\":60,\"method\":\"aes-256-gcm\",\"fast_open\":true,\"nameserver\":\"8.8.8.8\",\"mode\":\"tcp_and_udp\",\"plugin\":\"ss-v2ray-plugin\",\"plugin_opts\":\"server;tls;host=spectralvpn.ru;cert=/etc/letsencrypt/live/spectralvpn.ru/fullchain.pem;key=/etc/letsencrypt/live/spectralvpn.ru/privkey.pem\"}" > $SS_PATH/$2-$3.json

systemctl enable --now shadowsocks-libev-server@$2-$3.service

# Строчки написаные тварью, которая специально ограничевает подключение к впн до неболее чем 1 устройством :I
iptables -A INPUT -p udp --dport $p -m connlimit --connlimit-above 1 --connlimit-mask 0 -j DROP
iptables -A INPUT -p tcp --dport $p --syn -m connlimit --connlimit-above 1 --connlimit-mask 0 -j DROP
sudo netfilter-persistent save

echo -e "{\"server\":\"spectralvpn.ru\",\"server_port\":$p,\"password\":\"$1\",\"method\":\"aes-256-gcm\",\"plugin\":\"v2ray-plugin\",\"plugin_opts\":\"tls;host=spectralvpn.ru\"}" > $WEB_PATH/shadowsocks-$2-$3.json

echo -e "$1/ss-$2-$3.json"

unset WEB_PATH
unset SS_PATH
unset p
