---
date: 2026-04-26
tags:
- Docker
- Netmaker
- WireGuard
- 容器部署
- 组网
title: docker部署netmaker
---

# docker部署netmaker

```bash
mkdir netmaker
cd netmaker
wget https://github.com/gravitl/netmaker/raw/master/compose/docker-compose.yml
sed -i "s/80:80/10080:80/g" ./docker-compose.yml
sed -i "s/443:443/10443:443/g" ./docker-compose.yml

cat << EOF > ./netmaker.env
SERVER_IMAGE_TAG=latest
UI_IMAGE_TAG=latest
SERVER_HOST=203.0.113.27
NM_DOMAIN=nm.dreamchaser-luzeyu.cn
EOF

cat << EOF > ./Caddyfile
{
    email yydluzeyu@gmail.com
}
# Dashboard
https://dashboard.nm.dreamchaser-luzeyu.cn {
    # Apply basic security headers
    header {
            # Enable cross origin access to *.NETMAKER_BASE_DOMAIN
            Access-Control-Allow-Origin *.nm.dreamchaser-luzeyu.cn
            # Enable HTTP Strict Transport Security (HSTS)
            Strict-Transport-Security "max-age=31536000;"
            # Enable cross-site filter (XSS) and tell browser to block detected attacks
            X-XSS-Protection "1; mode=block"
            # Disallow the site to be rendered within a frame on a foreign domain (clickjacking protection)
            X-Frame-Options "SAMEORIGIN"
            # Prevent search engines from indexing
            X-Robots-Tag "none"
            # Remove the server name
            -Server
    }

    reverse_proxy http://netmaker-ui
}
# API
https://api.nm.dreamchaser-luzeyu.cn {
        reverse_proxy http://netmaker:8081
}
# MQ
wss://broker.nm.dreamchaser-luzeyu.cn {
        reverse_proxy ws://mq:8883
}
EOF

# 将*.nm.dreamchaser-luzeyu.cn代理到10080和10443

docker-compose -f ./docker-compose.yml
```

```bash
#
sudo wget -qO /root/nm-quick.sh https://raw.githubusercontent.com/gravitl/netmaker/master/scripts/nm-quick.sh && sudo chmod +x /root/nm-quick.sh && sudo /root/nm-quick.sh
/root/nm-quick.sh -d
```