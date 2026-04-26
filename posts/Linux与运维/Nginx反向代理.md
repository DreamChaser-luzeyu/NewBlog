---
date: 2026-04-26
tags:
- Nginx
- 反向代理
- WebSocket
- TLS
- V2Ray
title: Nginx反向代理笔记
---

# Nginx反向代理笔记

## 名词规范

- 源站：实际部署有网站或应用的服务器，也就是Nginx要请求的服务器
- 代理站：装有Nginx的服务器，也就是暴露给用户访问的服务器
- 代理域名：用户用来访问代理站的域名

## TCP层代理

### 特性

- 不是HTTP层的代理，Nginx服务器无法对SSL进行解密，显然也就无法支持缓存，以及需要修改HTTP报文的功能
- 不是我们通常说的反向代理，更像是根据SNI分流进行的端口转发
- 可以根据SNI选取upstream
- 若源站支持SSL，则代理站域名与源站域名必须相同，代理站无需管理证书

### 步骤

- 运行`sudo apt install libnginx-mod-stream`

- 编辑`/etc/nginx/nginx.conf`

- 在`stream{...}`中添加上游（使用域名或IP均可）并指定端口

  在`stream{...}`中添加映射（可使用正则表达式）

  - 支持使用正则表达式，如需匹配`*.dreamchaser-luzeyu.cn`可写`~^(?<subdomain>\w+)\.dreamchaser-luzeyu\.cn$`
  - 这一步完成后，重启nginx，将域名通过hosts或修改DNS解析来解析到nginx服务器，此时应该已经可以访问到源站
  - 但是80端口还是nginx的默认页面，还需让http请求重定向到https

  ```nginx
  stream {
          map $ssl_preread_server_name $backend {
                  ~^(?<subdomain>\w+)\.dreamchaser-luzeyu\.cn$ dreamchaser-luzeyu-cn;
          }
          upstream dreamchaser-luzeyu-cn {
                  server 203.0.113.22:443;
          }
  }
  ```

- 添加`/etc/nginx/conf.d/force_https.conf`，修改如下

  ```nginx
  server {
      listen 80 default_server;
      server_name _;
      return 301 https://$host$request_uri;
  }
  ```

  - 此时对所有域名的http请求都会重定向到https上

  - 若只希望针对某个域名进行重定向，可去除`default_server`选项，并在`server_name`后指定域名

  - 如果对所有域名的请求都重定向，此时重启nginx可能报错，因为还有一个默认服务器也监听了80端口

    编辑`/etc/nginx/sites-available/default`，删除掉这个网站的80端口监听即可

  - 如果服务器还有其他需求，希望仅仅对几个`host_name`进行重定向，可以修改如下：

    ```nginx
    server {
        listen 80;
        # 填写需要跳转的域名
        server_name storage.020124.xyz storage.dreamchaser-luzeyu.cn cloud.020124.xyz cloud.dreamchaser-luzeyu.cn www.020124.xyz www.dreamchaser-luzeyu.cn static.020124.xyz static.dreamchaser-luzeyu.cn;
        # 使用正则表达式匹配子域名的访问
        # server_name ~^(?<subdomain>\w+)\.dreamchaser-luzeyu\.cn$;
        # 使用星号匹配
        # server_name *.dreamchaser-luzeyu.cn *.020124.xyz;
        return 301 https://$host$request_uri;
    }
    ```

    

- 重启Nginx

## 应用层反向代理

### 特性

- 我们常说的反向代理一般指这种，CDN也是类似的原理（GCore CDN甚至直接用的Nginx）
- 可以修改HTTP报文，支持缓存功能
- 源站域名可以与代理站不同
  - 因此可以用来代理运行在同一服务器上的Tomcat、Flask、Docker应用
- 需要在代理站上配置代理域名的SSL证书

### 步骤

- 在`/etc/nginx/conf.d`创建`site.conf`

- 编辑内容如下

  - 可手动修改SSL端口，以及HTTP端口
  - 填入域名，配置证书的路径
  - 根据应用的需要修改其他配置

  ```nginx
  server {
      listen 80;
      listen 443 ssl;                # 监听443 SSL
      server_name tc.hk.020124.xyz;  # 域名
      ssl_certificate /etc/letsencrypt/live/tc.hk.020124.xyz/fullchain.pem;
      ssl_certificate_key /etc/letsencrypt/live/tc.hk.020124.xyz/privkey.pem;
      ssl_session_timeout 5m;
      ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
      ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:HIGH:!aNULL:!MD5:!RC4:!DHE;
      ssl_prefer_server_ciphers on;
      location / {
          root html;
          index  index.html index.htm;
          proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
          proxy_set_header X-Forwarded-Proto $scheme;
          proxy_set_header Host $http_host;
          proxy_set_header X-Real-IP $remote_addr;
          proxy_set_header Range $http_range;
          proxy_set_header If-Range $http_if_range;
          proxy_redirect off;
          # 配置代理 指向tomcat/flask/docker/...服务
          proxy_pass http://127.0.0.1:8899;
          client_max_body_size 40000m;
      }
  }
  ```

- 重启Nginx

# acme.sh证书申请

- 将域名解析到服务器IP

- 安装acme.sh，确保服务器上有Nginx

- 创建server_name为该域名的server，示例如下：

  ```nginx
  server {
      listen       80;
      listen       [::]:80;
      # listen       4443 ssl http2;
      # listen       [::]:4443 ssl http2;
      server_name  example.dreamchaser-luzeyu.cn;
      root         /usr/share/nginx/html;
      # ssl_certificate "/root/.acme.sh/example.dreamchaserluzeyu.cn_ecc/fullchain.cer";
      # ssl_certificate_key "/root/.acme.sh/example.dreamchaserluzeyu.cn_ecc/example.dreamchaser-luzeyu.cn.key";
      # ssl_session_cache shared:SSL:1m;
      # ssl_session_timeout  10m;
      # ssl_ciphers HIGH:!aNULL:!MD5;
      # ssl_prefer_server_ciphers on;
      
      error_page 404 /404.html;
      location = /404.html {
      }
  
      error_page 500 502 503 504 /50x.html;
      location = /50x.html {
      }
  }    
  ```

- 使用acme.sh申请并安装ssl证书

  ```bash
  # --- 申请证书
  acme.sh --issue --domain example.dreamchaser-luzeyu.cn --nginx
  # --- 安装证书
  acme.sh --install-cert --domain example.dreamchaser-luzeyu.cn \
          --key-file /etc/nginx/ssl/example.dreamchaser-luzeyu.cn/example.dreamchaser-luzeyu.cn.key \
          --fullchain-file /etc/nginx/ssl/example.dreamchaser-luzeyu.cn/fullchain.cer \
          --reloadcmd "service nginx force-reload"
  ```

- 自动更新证书

  ```bash
  acme.sh --install-cronjob
  ```

  



# 典型配置

## 规范

- 清除`/etc/nginx/sites-available/default`中的网站
- REALITY协议监听8443端口
- VMess WS协议监听8080端口，路径为`/data`
- VMess WS域名规定为`<vps_info>data.020124.xyz`以及`<vps_info>data.dreamchaser-luzeyu.cn`，代理路径为`/rpc_warpper`
- 对于其他的`http://*.020124.xyz`以及`http://*.dreamchaser-luzeyu.cn`的请求，统一重定向到https

##  代理WebSocket

`nano /etc/nginx/conf.d/ws_proxy.conf`

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name hk1data.020124.xyz;            # 连接时指定此host
    location /rpc_warpper {                    # 连接时指定此path
        proxy_pass http://127.0.0.1:8880/data; # V2Ray监听的端口以及配置的路径
        proxy_connect_timeout 5s;              # 连接超时时间
        proxy_send_timeout 7s;                 # 发送超时时间
        proxy_next_upstream error timeout;     # 超时转移
        proxy_intercept_errors on;
        error_page 400 500 404 502 https://volunteer.cdn-go.cn/404/latest/404.html;
        # 代理 WebSocket 连接
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 600s;
        # 传递客户端 IP 地址
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
	}
     location /rpc_warpperr {                  # Used for Tor node
        proxy_pass http://127.0.0.1:8881/data; # V2Ray监听的端口以及配置的路径
        proxy_connect_timeout 5s;              # 连接超时时间
        proxy_send_timeout 7s;                 # 发送超时时间
        proxy_next_upstream error timeout;     # 超时转移
        proxy_intercept_errors on;
        error_page 400 500 404 502 https://volunteer.cdn-go.cn/404/latest/404.html;
        # 代理 WebSocket 连接
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 600s;
        # 传递客户端 IP 地址
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

## 强制https

`/etc/nginx/conf.d/force_https.conf`

```nginx
server {
    listen 80;
    # 使用星号匹配
    server_name *.dreamchaser-luzeyu.cn *.020124.xyz;
    return 301 https://$host$request_uri;
}
```





## 代理Cloudflare

`nano /etc/nginx/nginx.conf`在最外层添加：

```nginx
stream {
        map $ssl_preread_server_name $backend {
                # aws.amazon.com reality;
                ~^(?<subdomain>\w+)\.dreamchaser-luzeyu\.cn$ cf-ip-https;
                ~^(?<subdomain>\w+)\.020124\.xyz$ cf-ip-https;
        }
        upstream cf-ip-https {
                server 203.0.113.22:443;
                server 203.0.113.23:443;
        }
        upstream gcore-ip-https {
                server 203.0.113.24:443;
        }
        upstream reality {
                server 127.0.0.1:8443;
        }
        server {
                listen 443      reuseport;
                listen [::]:443 reuseport;
                proxy_pass      $backend;
                ssl_preread     on;
        }
}
```

如果报错`[emerg] unknown directive "stream" `，则使用命令`sudo apt install libnginx-mod-stream`安装stream模块。

如果还需要代理cloudflare的80端口，则需要配置应用层代理，因为Nginx的TCP代理只支持具有SNI的SSL流量。

`touch /etc/nginx/conf.d/cf_proxy.conf && nano /etc/nginx/conf.d/cf_proxy.conf`

```nginx
# Create variable `upstream_server` based on passed $host
map $host $upstream_server {
    hostnames;
    ~^(?<subdomain>\w+)\.dreamchaser-luzeyu\.cn$ cf-ip-http;
    ~^(?<subdomain>\w+)\.020124\.xyz$ cf-ip-http;
}

# 为 connection_upgrade 变量映射值
map $http_upgrade $connection_upgrade {
    default upgrade;
    ''      close;
}

# Upstream servers
upstream cf-ip-http {
    server 203.0.113.22:80;
    server 203.0.113.23:80;
}

server {
    listen 80;
    listen [::]:80;
    location / {
        proxy_pass http://$upstream_server; # 使用变量选择上游服务器
        # --- 其他proxy设置 ...
        proxy_http_version 1.1;
        # WebSocket 相关的请求头设置
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Sec-WebSocket-Key $http_sec_websocket_key;
        proxy_set_header Sec-WebSocket-Version $http_sec_websocket_version;
        # 当需要让 Nginx 支持较复杂的 WebSocket 握手时使用
        proxy_set_header Sec-WebSocket-Extensions $http_sec_websocket_extensions;
        proxy_set_header Sec-WebSocket-Protocol $http_sec_websocket_protocol;
        # 维持与后端的长连接，对 WebSocket 很重要
        proxy_read_timeout 600s;
        # 此选项允许 Nginx 将 Upgrade 字段的头部传递给上游服务器
        proxy_pass_request_headers on;
    }
}
```

注：

- `server_name`似乎不支持域名的正则匹配，因此使用map进行匹配
- nginx将优先匹配有`server_name`的server，如果无一匹配，才会匹配端口相同、无`server_name`的server，因此这个配置不会影响其他服务
- `map`命令用于创建一个新的变量，举例如下：

  ```nginx
  # 创建一个名为$upstream_server的变量
  map $host $upstream_server {
      default                     default_server;
      # 如果传入的请求的host为example.com,那么$upstream_server就为server1
      example.com                 server1;
      # 如果传入的请求的host为another-example.com,那么$upstream_server就为server2
      another-example.com         server2;
  }
  ```

  

还应注释`/etc/nginx/nginx.conf`中的这一行：

```nginx
include /etc/nginx/sites-enabled/*;
```



# nginx上游节点

对于国内服务器

```nginx
upstream my-cf-http {
    # --- My Nodes
    server 203.0.113.10:80 max_fails=1 fail_timeout=30;   # HKBGP EPYC
    server 203.0.113.25:80 max_fails=1 fail_timeout=3600; # JPAWS
    server 203.0.113.26:80   max_fails=1 fail_timeout=30;   # HK CMI WePC
    server 203.0.113.27:80 max_fails=1 fail_timeout=30;   # US CN2
    server 203.0.113.28:80 backup;  # HK Tencent
    # --- Cloudflare Official Nodes
    server 203.0.113.23:80 backup;
    server 203.0.113.29:80 backup;
    server 203.0.113.30:80   backup;
    server 203.0.113.31:80  backup;
    server 203.0.113.22:80  backup;
    server 203.0.113.32:80  backup;
}
```

注意端口要根据实际情况进行修改。

# 常用文本

## 常用命令

```bash
sudo apt update && sudo apt install nginx libnginx-mod-stream lsb-release gpg coreutils tor nano -y

# --- Nginx
cd /etc/nginx && sudo mv ./nginx.conf ./nginx.conf.bak && sudo nano ./nginx.conf

# --- Cloudflare warp
sudo apt update && sudo apt install lsb-release gpg coreutils -y
# Check if all commands needed exists
which gpg
which lsb_release
which tee
# Add cloudflare warp repo
curl -fsSL https://pkg.cloudflareclient.com/pubkey.gpg | sudo gpg --yes --dearmor --output /usr/share/keyrings/cloudflare-warp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/cloudflare-warp-archive-keyring.gpg] https://pkg.cloudflareclient.com/ $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/cloudflare-client.list
# Install cloudflare-warp
sudo apt-get update && sudo apt-get install cloudflare-warp -y
# Configure cloudflare-warp
warp-cli register
warp-cli mode proxy
warp-cli status
warp-cli connect
# --- x-ui
sudo bash <(wget -qO- https://raw.githubusercontent.com/sing-web/x-ui/main/install.sh)
```

## Nginx配置文件

`/etc/nginx/nginx.conf`

```nginx
user www-data;
worker_processes auto;
pid /run/nginx.pid;
error_log /var/log/nginx/error.log;
include /etc/nginx/modules-enabled/*.conf;

stream {
    map $ssl_preread_server_name $backend {
        # 使用REALITY时取消注释
        aws.amazon.com reality;
        ~^(?<subdomain>\w+)\.dreamchaser-luzeyu\.cn$ cf-ip-https;
        ~^(?<subdomain>\w+)\.020124\.xyz$ cf-ip-https;
    }
    upstream cf-ip-https {
        server 203.0.113.22:443;
        server 203.0.113.23:443;
    }
    upstream gcore-ip-https {
        server 203.0.113.24:443;
    }
    upstream reality {
        server 127.0.0.1:8443;
    }
    server {
        listen 443      reuseport;
        listen [::]:443 reuseport;
        proxy_pass      $backend;
        ssl_preread     on;
    }
}

events {
	worker_connections 768;
	# multi_accept on;
}

http {
	# Basic Settings
	sendfile on;
	tcp_nopush on;
	types_hash_max_size 2048;
	include /etc/nginx/mime.types;
	default_type application/octet-stream;

	# SSL Settings
	ssl_protocols TLSv1 TLSv1.1 TLSv1.2 TLSv1.3; # Dropping SSLv3, ref: POODLE
	ssl_prefer_server_ciphers on;

	# Logging Settings
	access_log /var/log/nginx/access.log;

	# Gzip Settings
	gzip on;

	# Virtual Host Configs
	# --- 代理Xray Websocket
    server {
        listen 80;
        listen [::]:80;
        server_name hk1data.020124.xyz;            # 连接时指定此host
        location /rpc_warpper {                    # 连接时指定此path
            proxy_pass http://127.0.0.1:8880/data; # V2Ray监听的端口以及配置的路径
            proxy_connect_timeout 5s;              # 连接超时时间
            proxy_send_timeout 7s;                 # 发送超时时间
            proxy_next_upstream error timeout;     # 超时转移
            proxy_intercept_errors on;
            error_page 400 500 404 502 https://volunteer.cdn-go.cn/404/latest/404.html;
            # 代理 WebSocket 连接
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_read_timeout 600s;
            # 传递客户端 IP 地址
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
     }
		# 代理Xray Websocket (Tor)
        location /rpc_warpperr {
            proxy_pass http://127.0.0.1:8881/data;
            proxy_connect_timeout 5s;
            proxy_send_timeout 7s;
            proxy_next_upstream error timeout;
            proxy_intercept_errors on;
            error_page 400 500 404 502 https://volunteer.cdn-go.cn/404/latest/404.html;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_read_timeout 600s;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }
    }

	# --- 代理Cloudflare HTTP
    map $http_upgrade $connection_upgrade {
        default upgrade;
        ''      close;
    }
    upstream cf-ip-http {
        server 203.0.113.22:80;
        server 203.0.113.23:80;
    }
    server {
        listen 80;
        listen [::]:80;
        server_name *.020124.xyz *.dreamchaser-luzeyu.cn;
        location / {
            proxy_pass http://$cf-ip-http; 
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection $connection_upgrade;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header Sec-WebSocket-Key $http_sec_websocket_key;
            proxy_set_header Sec-WebSocket-Version $http_sec_websocket_version;
            proxy_set_header Sec-WebSocket-Extensions $http_sec_websocket_extensions;
            proxy_set_header Sec-WebSocket-Protocol $http_sec_websocket_protocol;
            proxy_read_timeout 600s;
            proxy_pass_request_headers on;
        }
    }

	include /etc/nginx/conf.d/*.conf;
#	include /etc/nginx/sites-enabled/*;
}
```



## xray配置模板

### 海外VPS

```json
{
  "api": {
    "services": [
      "HandlerService",
      "LoggerService",
      "StatsService"
    ],
    "tag": "api"
  },
  "inbounds": [
    {
      "listen": "127.0.0.1",
      "port": 62789,
      "protocol": "dokodemo-door",
      "settings": {
        "address": "127.0.0.1"
      },
      "tag": "api"
    },
    // Tor inbound
    {
      "listen": "127.0.0.1",
      "port": 8881,
      "protocol": "vmess",
      "settings": {
        "clients": [
          {
            "id": "f46c0039-302a-4bae-d968-a0e545aa0ef7"
          }
        ],
        "disableInsecureEncryption": false
      },
      "streamSettings": {
        "network": "ws",
        "security": "none",
        "wsSettings": {
          "path": "/data",
          "headers": {}
        },
        "sockopt": {
          "tcpMaxSeg": 1440,
          "tcpFastOpen": false,
          "domainStrategy": "AsIs",
          "tcpcongestion": "",
          "acceptProxyProtocol": false,
          "tcpKeepAliveIdle": 0,
          "tcpKeepAliveInterval": 0,
          "tcpUserTimeout": 10000,
          "interface": ""
        }
      },
      "tag": "inbound-tor",
      "sniffing": {
        "enabled": true,
        "destOverride": [
          "http",
          "tls",
          "quic"
        ]
      }
    }
  ],
  "policy": {
    "system": {
      "statsInboundDownlink": true,
      "statsInboundUplink": true
    }
  },
  "outbounds": [
    {
      "protocol": "blackhole",
      "settings": {},
      "tag": "blocked"
    },
    {
      "tag": "ipv4-out",
      "protocol": "freedom",
      "settings": {
        "domainStrategy": "UseIPv4"
      }
    },
    {
      "tag": "direct",
      "protocol": "freedom",
      "settings": {}
    },
    {
      "tag": "ipv6-out",
      "protocol": "freedom",
      "settings": {
        "domainStrategy": "UseIPv6"
      }
    },
    {
      "domainStrategy": "PreferIPv4",
      "protocol": "vless",
      "settings": {
        "vnext": [
          {
            "address": "203.0.113.16",
            "port": 34164,
            "users": [
              {
                "encryption": "none",
                "flow": "",
                "id": "b3231433-0937-4e75-9242-0107d5df76f7"
              }
            ]
          }
        ]
      },
      "streamSettings": {
        "network": "tcp"
      },
      "tag": "proxy-ca"
    },
    {
      "domainStrategy": "PreferIPv4",
      "protocol": "vmess",
      "settings": {
        "vnext": [
          {
            "address": "203.0.113.33",
            "port": 80,
            "users": [
              {
                "alterId": 0,
                "id": "f46c0039-302a-4bae-d968-a0e545aa0ef7",
                "security": "auto"
              }
            ]
          }
        ]
      },
      "streamSettings": {
        "network": "ws",
        "wsSettings": {
          "headers": {
            "Host": "us3data.020124.xyz"
          },
          "path": "/rpc_warpper?ed=2048"
        }
      },
      "tag": "proxy-us"
    },
    {
      "tag": "socks5-warp",
      "protocol": "socks",
      "settings": {
        "servers": [
          {
            "address": "127.0.0.1",
            "port": 40000
          }
        ]
      }
    },
    {
      "tag": "tor",
      "protocol": "socks",
      "settings": {
        "servers": [
          {
            "address": "127.0.0.1",
            "port": 9050
          }
        ]
      }
    },
    {
      "tag": "wireguard-warp",
      "protocol": "wireguard",
      "settings": {
        "secretKey": "wBgj79mhiENspSFQHIULqHP8IKFJJcdq37R51DJvDlk=",
        "address": [
          "172.16.0.2/32",
          "2606:4700:110:845b:e753:d262:c6f:db5b/128"
        ],
        "peers": [
          {
            "publicKey": "bmXOC+F1FxEMF9dyiK2H5/1SUtzH0JuVo51h2wPfgyo=",
            "allowedIPs": [
              "0.0.0.0/0",
              "::/0"
            ],
            "endpoint": "engage.cloudflareclient.com:2408"
          }
        ],
        "reserved": [
          249,
          159,
          96
        ]
      }
    }
  ],
  "routing": {
    "domainStrategy": "AsIs",
    "rules": [
      {
        "inboundTag": [
          "api"
        ],
        "outboundTag": "api",
        "type": "field"
      },
      {
        "inboundTag": [
          "inbound-tor"
        ],
        "outboundTag": "tor",
        "type": "field"
      },
      {
        "domain": [
          "domain:youtube.com",
          "domain:www.google.com"
        ],
        "outboundTag": "ipv4-out",
        "type": "field"
      },
      {
        "domain": [
          "domain:bing.com",
          "geosite:google",
          "domain:coze.com"
        ],
        "outboundTag": "socks5-warp",
        "type": "field"
      },
      {
        "domain": [
          "geosite:cn"
        ],
        "outboundTag": "socks5-warp",
        "type": "field"
      },
      {
        "ip": [
          "geoip:cn"
        ],
        "outboundTag": "socks5-warp",
        "type": "field"
      },
      // Set to direct if BT allowed
      {
        "outboundTag": "socks5-warp",
        "protocol": [
          "bittorrent"
        ],
        "type": "field"
      },
      // Remove if already unlocked
      {
        "type": "field",
        "outboundTag": "proxy-us",
        "domain": [
          "geosite:openai",
          "domain:chatgpt.com",
          "domain:sentry.io"
        ]
      },
      // Remove if already unlocked
      {
        "type": "field",
        "outboundTag": "proxy-ca",
        "domain": [
          "geosite:netflix"
        ]
      },
      {
        "type": "field",
        "outboundTag": "proxy-ca",
        "ip": [
          "geoip:netflix"
        ]
      },
      {
        "type": "field",
        "outboundTag": "direct",
        "network": "udp,tcp"
      }
    ]
  },
  "stats": {}
}
```

### 中转VPS

```json
{
  "api": {
    "services": [
      "HandlerService",
      "LoggerService",
      "StatsService"
    ],
    "tag": "api"
  },
  "inbounds": [
    {
      "listen": "127.0.0.1",
      "port": 62789,
      "protocol": "dokodemo-door",
      "settings": {
        "address": "127.0.0.1"
      },
      "tag": "api"
    }
  ],
  "policy": {
    "system": {
      "statsInboundDownlink": true,
      "statsInboundUplink": true
    }
  },
  "outbounds": [
    {
      "protocol": "blackhole",
      "settings": {},
      "tag": "blocked"
    },
    {
      "tag": "ipv4-out",
      "protocol": "freedom",
      "settings": {
        "domainStrategy": "UseIPv4"
      }
    },
    {
      "tag": "direct",
      "protocol": "freedom",
      "settings": {}
    },
    {
      "tag": "ipv6-out",
      "protocol": "freedom",
      "settings": {
        "domainStrategy": "UseIPv6"
      }
    },
    {
      "domainStrategy": "PreferIPv4",
      "protocol": "vmess",
      "settings": {
        "vnext": [
          {
            "address": "127.0.0.1",
            "port": 4079,
            "users": [
              {
                "alterId": 0,
                "id": "f46c0039-302a-4bae-d968-a0e545aa0ef7",
                "security": "auto"
              }
            ]
          }
        ]
      },
      "streamSettings": {
        "network": "ws",
        "wsSettings": {
          "headers": {
            "Host": "hk1data.020124.xyz"
          },
          "path": "/rpc_warpper?ed=2048"
        }
      },
      "tag": "hk-hostyun"
    }
  ],
  "routing": {
    "domainStrategy": "AsIs",
    "rules": [
      {
        "inboundTag": [
          "api"
        ],
        "outboundTag": "api",
        "type": "field"
      },
      {
        "type": "field",
        "outboundTag": "hk-hostyun",
        "network": "udp,tcp"
      }
    ]
  },
  "stats": {}
}
```

## 服务模板

```
[Unit]
Description=MPTCP Listen
After=network.target          # 服务依赖（再这些服务后启动本服务）

[Service]
Type=forking                  # 服务类型 simple/forking/oneshot/dbus/notify/idle
ExecStart=socat TCP4-LISTEN:4079,fork TCP:203.0.113.10:79,protocol=0x106,nodelay
                              # 启动命令
#ExecStop=                    # 终止命令，可以省略
#ExecReload=                  # 重启命令，可以省略

[Install]
WantedBy=multi-user.target    # 服务安装设置，multi-user.target是默认的自启动target
                              # 这个组里的所有服务都将开机启动
```