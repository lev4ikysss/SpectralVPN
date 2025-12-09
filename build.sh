#!/bin/bash
mkdir /etc/spectralvpn_api
cp API/* /etc/spectralvpn_api/
cp configs/config/params.conf
python3 -m venv /etc/spectralvpn_api/.venv
/etc/spectralvpn_api/.venv/bin/pip -r requirments.txt

mkdir /var/www/html/spectralvpn.ru
cp -r Frontend/* /var/www/html/spectralvpn.ru/

cp configs/nginx/* /etc/nginx/sites-available/
ln -s /etc/nginx/sites-available/spectralvpn.ru.nginx /etc/nginx/sites-enabled/
ln -s /etc/nginx/sites-available/spectralvpn.ru_http.nginx /etc/nginx/sites-enabled/
ln -s /etc/nginx/sites-available/spectralvpn_api.nginx /etc/nginx/sites-enabled/

cp configs/systemd/* /etc/systemd/system/
systemctl restart nginx.service
systemctl enable --now spectralvpn_api.service