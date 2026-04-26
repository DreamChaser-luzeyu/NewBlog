---
date: 2026-04-26
tags:
- Headscale
- Tailscale
- Nginx
- 自建服务
- 内网穿透
title: Headscale部署
---

# Headscale部署

## 下载Headscale-ui

```bash
wget https://github.com/gurucomputing/headscale-ui/releases/download/2024.02.24-beta1/headscale-ui.zip -O /tmp/headscale.zip
cd /tmp
unzip ./headscale.zip
mkdir /usr/local/www/
mv ./web /usr/local/www/headscale-ui
```

## 配置Headscale

- 修改`server_url`

- 修改`listen_addr`

其他按需修改

配置API:

```bash
headscale api create
```

## 配置Nginx

`nano /etc/nginx/conf.d/headscale.conf`

```nginx
server {
        server_name hs.020124.xyz;

        # Security / XSS Mitigation Headers
        add_header X-Frame-Options "SAMEORIGIN";
        add_header X-XSS-Protection "1; mode=block";
        add_header X-Content-Type-Options "nosniff";

        location /web {
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            alias /usr/local/www/headscale-ui;
            index index.html;
        }

        location / {
            proxy_pass http://127.0.0.1:10080;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_redirect http:// https://;
            proxy_buffering off;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $http_x_forwarded_proto;
            add_header Strict-Transport-Security "max-age=15552000; includeSubDomains" always;
        }
}

```

进入`https://hs.020124.xyz/web`后填入api key

## 客户端

```bash
tailscale up --login-server https://hs.020124.xyz/
```