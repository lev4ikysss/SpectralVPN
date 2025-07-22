#!/usr/bin/bash
# ./create_ss.sh {token} {name} {number}

WEB_PATH="/var/www/html/spectralvpn.ru"
SS_PATH="/etc/shadowsocks-libev"

if ! [-e "$WEB_PATH/$1"]; then
    mkdir "$WEB_PATH/$1/"
fi

