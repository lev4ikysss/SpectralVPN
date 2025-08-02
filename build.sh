#!/bin/bash
apt update && apt upgrade && apt install nginx wireguard wireguard-tools shadowsocks-libev shadowsocks-v2ray-plugin

mkdir /usr/share/SpectralVPN/
cp -r ./* /usr/share/SpectralVPN/

cp -r Frontend/spectralvpn.ru /var/www/html/
cp -r configs/nginx/* /etc/nginx/sites-available/
cp -r configs/nginx/* /etc/nginx/sites-enabled/
mkdir -p /etc/spectralvpn/api/ /etc/spectralvpn/server/ /etc/spectralvpn/bot/
cp -r API/* /etc/spectralvpn/api/
cp -r Backend/* /etc/spectralvpn/server/
cp -r Bot/* /etc/spectralvpn/bot/
