---
date: 2026-04-26
tags:
- Hysteria2
- udp2raw
- UDP加速
- 网络代理
title: UDP加速
---

# UDP加速

## Hysteria2+udp2raw

### Hysteria2

#### Server

```bash
# 安装
bash <(curl -fsSL https://get.hy2.sh/)
# 生成自签名证书
openssl req -x509 -nodes -newkey ec:<(openssl ecparam -name prime256v1) -keyout /etc/hysteria/server.key -out /etc/hysteria/server.crt -subj "/CN=bing.com" -days 36500
# 记录指纹
openssl x509 -noout -fingerprint -sha256 -in /etc/hysteria/server.crt
chown hysteria /etc/hysteria/server.key 
chown hysteria /etc/hysteria/server.crt
# 写配置
cat > /etc/hysteria/config.yaml << EOF
listen: :8443 #监听端口

#有域名，使用CA证书 
#acme:
#  domains:
#    - test.heybro.bid #你的域名，需要先解析到服务器ip
#  email: augustdoit@gmail.com

#使用自签名证书
tls:
  cert: /etc/hysteria/server.crt
  key: /etc/hysteria/server.key

auth:
  type: password
  password: 020124 #设置认证密码

#伪装
masquerade:
  type: proxy
  proxy:
    url: https://bing.com/ #伪装网址
    rewriteHost: true
EOF
# 启用服务
systemctl enable hysteria-server
systemctl restart hysteria-server

```
端口跳跃配置
```bash
# 端口跳跃
export WAN_IF="ens3"
export HY2_DST_PORT="8443"
iptables -t nat -A PREROUTING -i ${WAN_IF} -p udp --dport 20000:30000 -j REDIRECT --to-ports ${HY2_DST_PORT}
ip6tables -t nat -A PREROUTING -i ${WAN_IF} -p udp --dport 20000:30000 -j REDIRECT --to-ports ${HY2_DST_PORT}
unset WAN_IF
unset HY2_DST_PORT
```



#### Client

```bash
bash <(curl -fsSL https://get.hy2.sh/)
# 切换为客户端模式
sed -i "s/hysteria server/hysteria client/g" /etc/systemd/system/hysteria-server.service
sed -i "s/hysteria server/hysteria client/g" /etc/systemd/system/hysteria-server@.service
mv /etc/systemd/system/hysteria-server.service /etc/systemd/system/hysteria-client.service
# 写配置
export HY2_SERVER="203.0.113.10:20000-30000"
export HY2_AUTH="020124"
export HY2_REMOTE_PORT="51280"
export HY2_LISTEN_PORT="51283"
cat > /etc/hysteria/config.yaml << EOF 
server: ${HY2_SERVER}
auth: ${HY2_AUTH}
tls:
  insecure: true
  pinSHA256: 5C:33:AD:AF:A5:FB:B4:6B:0B:AE:99:24:B2:9D:DD:49:9D:B9:02:F3:21:54:06:C5:9C:A7:81:85:BF:B4:58:9E
bandwidth:
  up: 60 mbps
  down: 200 mbps
socks5:
  listen: 127.0.0.1:1080
udpForwarding:
  - listen: 127.0.0.1:${HY2_LISTEN_PORT}
    remote: 127.0.0.1:${HY2_REMOTE_PORT}
    timeout: 20s
EOF
unset HY2_SERVER
unset HY2_AUTH
unset HY2_REMOTE_PORT
unset HY2_LISTEN_PORT
# 启用服务
systemctl enable hysteria-client
systemctl restart hysteria-client
```

### udp2raw

#### Server

```bash
export SERVICE_PORT="51280"
export COMM_PORT="51281"

./udp2raw_amd64 \
-s \
-l0.0.0.0:${COMM_PORT} \
-r127.0.0.1:${SERVICE_PORT} \
-k "020124" \
--raw-mode faketcp \
--cipher-mode xor \
-a
```

#### Client

```bash
export COMM_PORT="51281"
export CLIENT_LISTEN_PORT="51281"
export SERVER_IP="203.0.113.10"

./udp2raw_amd64 \
-c \
-l0.0.0.0:${CLIENT_LISTEN_PORT} \
-r${SERVER_IP}:${COMM_PORT} \
-k "020124" \
--raw-mode faketcp \
--cipher-mode xor \
-a
```

建议把上层的MTU设成1200