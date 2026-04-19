FROM nginx:stable-alpine
COPY Web/ /usr/share/nginx/html/
COPY Nginx/spectralvpn.ru.nginx /etc/nginx/conf.d/spectralvpn.ru.conf
COPY Nginx/spectralvpn.ru_http.nginx /etc/nginx/conf.d/spectralvpn.ru_http.conf
COPY Nginx/spectralvpn_api.nginx /etc/nginx/conf.d/spectralvpn_api.conf
EXPOSE 80 443
CMD ["nginx", "-g", "daemon off;"]
