---
date: 2026-04-26
tags:
- SoftEther VPN
- Sing-box
- REALITY
- DHCP
- 策略路由
title: SoftEther VPN 配置
---

# SoftEther VPN 配置

## TCP窗口优化

```bash
export WINDOW_SIZE=22000000  # 计算：800(Mbps) * 0.15(s) / 8(bits/byte) = 15(MB)
sysctl -w net.core.rmem_max=${WINDOW_SIZE} # 系统限制
sysctl -w net.core.wmem_max=${WINDOW_SIZE}
sysctl -w net.ipv4.tcp_rmem="4096 87380 ${WINDOW_SIZE}" # 单个应用限制
sysctl -w net.ipv4.tcp_wmem="4096 87380 ${WINDOW_SIZE}"
sysctl -p
```

## 服务端配置

### 初始化环境变量

```bash
# 重新连接以确保清除先前的环境变量
# 要配置到VPN Tap设备上的IP,需要写成CIDR形式
export SERVER_IP_CIDR="192.168.88.1/24"
# --- dhcpd.conf中的格式
export SERVER_IP="192.168.88.1"
export SUBNET="192.168.88.0"
export SUBNET_NETMASK="255.255.255.0"
export DHCP_RANGE="192.168.88.100 192.168.88.254"
export BROADCAST_ADDR="192.168.88.255"
export GATEWAY_IP=${SERVER_IP}
# --- VPN端口名，与创建的Tap设备保持一致
export VPN_IF_NAME="tap_softether"
# --- iptables规则所需环境变量
export VPN_IF=${VPN_IF_NAME}
export WAN_IF="eth0"
export WAN6_IF="eth0"
```

### 安装VPN Server

```bash
sudo apt update && sudo apt install isc-dhcp-server softether-vpnserver
```

### 安装Sing-box REALITY

```bash
cat /tmp/sing-box.py << EOF
import os
from string import Template

GITHUB_MIRROR = 'https://app.dreamchaser-luzeyu.cn/gh/'

INSTALL_PATH = '/usr/local/bin'
SERVICE_PATH = '/usr/lib/systemd/system/'
CFG_FILE_DIR = '/etc/'

SERVICE_TEMPLATE = '''
[Unit]
Description={service_desc}
After=network.target

[Service]
Type=simple
ExecStart={service_cmd}
Restart=always

[Install]
WantedBy=multi-user.target
'''

SINGBOX_TEMPLATE = '''
{
    "log": {
        "disabled": false,
        "level": "info",
        "timestamp": true
    },
    "inbounds": [
        {
            "type": "vless",
            "tag": "vless-brutal-reality-in",
            "listen": "::",
            "listen_port": ${server_listen_port},
            "sniff": true,
            "sniff_override_destination": true,
            "users": [
                {
                    "uuid": "${vless_uuid}",
                    "flow": ""
                }
            ],
            "tls": {
                "enabled": true,
                // 可自定义修改，可以不改，但是推荐用https://bgp.tools/去扫你VPS或独服同IP网段里的网站延迟低
                "server_name": "${reality_server_name}",
                "reality": {
                    "enabled": true,
                    "handshake": {
                        // 可自定义修改，可以不改，但是推荐用https://bgp.tools/去扫你VPS或独服同IP网段里的网站延迟低
                        "server": "${reality_server_name}",
                        "server_port": 443
                    },
                    // 执行 sing-box generate reality-keypair 生成
                    "private_key": "${priv_key}",
                    "short_id": [
                        // 0 到 f，长度为 2 的倍数，长度上限为 16，可留空，或执行 sing-box generate rand 8 --hex 生成
                        "${short_id}"
                    ]
                }
            },
            "multiplex": {
                "enabled": true,
                // V2rayN自定义的sing-box内核中，VLESS-Vision-REALITY 不能启用 padding，会造成连接错误无法上网。单纯内核启动可以启用，暂时属于V2rayN的某个问题。
                "padding": false,
                "brutal": {
                    "enabled": ${brutal_enabled},
                    "up_mbps": ${up_mbps},
                    "down_mbps": ${down_mbps}
                }
            }
        }
    ],
    "outbounds": [
        {
            "type": "direct",
            "tag": "direct"
        }
    ],
    "route": {
        "rules": [
            {
                "inbound": ["vless-brutal-reality-in"],
                "outbound": "direct"
            }
        ]
    }
}
'''

def install_singbox_reality_server() : 
    # --- 基本配置
    bin_name = 'sing-box'
    config_file_name = 'sing-box.json'
    service_name = 'sing-box-reality-server'
    download_cmd = f'wget {GITHUB_MIRROR}https://github.com/SagerNet/sing-box/releases/download/v1.10.3/sing-box-1.10.3-linux-amd64.tar.gz -O /tmp/singbox.tar.gz'
    install_bin_cmd = f'cd /tmp && tar -zxvf ./singbox.tar.gz && cd sing-box* && cp sing-box {INSTALL_PATH}/ && chmod +x {INSTALL_PATH}/sing-box'
    service_file_content = SERVICE_TEMPLATE.format(service_desc = 'sing-box REALITY', service_cmd = f'{bin_name} run -c {CFG_FILE_DIR}/{config_file_name}')
    
    # --- 下载
    ret = os.system(download_cmd)
    if ret != 0 : 
        print("Error downloading sing-box, try switching GitHub mirror\n")
        exit(ret)
    # --- 安装可执行文件
    ret = os.system(install_bin_cmd)
    if ret != 0 : 
        print("Error installing sing-box binary\n")
        exit(ret)
    # --- 测试
    ret = os.system(f'{bin_name} > /dev/null 2>&1')
    if ret != 0 : 
        print("Warn: Test run bin failed\n")
    # --- 安装服务
    with open(f'{SERVICE_PATH}/{service_name}.service', 'w') as file:
        file.write(service_file_content)
    os.system(f'systemctl daemon-reload && systemctl status {service_name}')
    # --- 生成默认配置
    with open(f'{CFG_FILE_DIR}/{config_file_name}', 'w') as file:
        file.write(config_singbox_reality_server({
            "server_listen_port" : "8443",
            "vless_uuid" : "a60aa17c-7ce6-4ec0-a2c9-8db730f15bf4",
            "reality_server_name" : "aws.amazon.com",
            "priv_key" : "-FVDzv68IC17fJVlNDlhrrgX44WeBfbhwjWpCQVXGHE",
            "short_id" : "a9aa79f2",
            "brutal_enabled" : "true",
            "up_mbps" : "500",
            "down_mbps" : "500"
            }))
    # --- 启动服务
    os.system(f'systemctl enable {service_name} && systemctl restart {service_name} && systemctl status {service_name}')

def config_singbox_reality_server(fmt : dict[str, str]) -> str :
    if fmt != None: return Template(SINGBOX_TEMPLATE).substitute(fmt)
    else:
        return ""    

install_singbox_reality_server()
EOF

python3 /tmp/sing-box.py
```

### 启用转发

```bash
echo 1 > /proc/sys/net/ipv4/ip_forward
sysctl -w net.ipv4.ip_forward=1
sysctl -w net.ipv6.conf.all.forwarding=1
sysctl -p
# 也可手动编辑/etc/sysctl.conf
# sed -i "s/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/g" /etc/sysctl.conf
# sed -i "s/#net.ipv6.conf.all.forwarding=1/net.ipv6.conf.all.forwarding=1/g" /etc/sysctl.conf
# sysctl -p
```

### 配置VPN Server（手动操作）

本地桥设置-创建Tap设备；确保Tap设备名称与VPN_IF_NAME一致（VPN_IF_NAME为填入的名称前面加上`tap_`）

密码不能太长，太长连不上

### 配置VPN Server证书

```bash
export DOMAIN_NAME="ct.dreamchaser-luzeyu.cn"
sudo apt update && sudo apt install certbot -y
certbot certonly -d ${DOMAIN_NAME} --manual --preferred-challenges dns
```



### 启用DHCP服务

```bash
# --- 为VPN端口设置静态IP
ip addr add ${SERVER_IP_CIDR} dev ${VPN_IF_NAME}
# --- 备份旧的配置
mv /etc/dhcp/dhcpd.conf /etc/dhcp/dhcpd.conf.bak
# --- 生成新的配置
cat > /tmp/dhcpd.py << EOF
import os
from string import Template
DHCPD_CFG_TEMPLATE = '''
subnet ${SUBNET} netmask ${SUBNET_NETMASK} {
   range ${DHCP_RANGE};
   option routers ${GATEWAY_IP};
   option broadcast-address ${BROADCAST_ADDR};
   default-lease-time 600;
   max-lease-time 7200;
}
'''
with open('/etc/dhcp/dhcpd.conf', 'w') as f:
    f.write(Template(DHCPD_CFG_TEMPLATE).substitute({
        "SUBNET" : os.getenv("SUBNET"),
        "SUBNET_MASK" : os.getenv("SUBNET_MASK"),
        "DHCP_RANGE" : os.getenv("DHCP_RANGE"),
        "GATEWAY_IP" : os.getenv("GATEWAY_IP"),
        "BROADCAST_ADDR" : os.getenv("BROADCAST_ADDR"),
    }))
quit()
EOF
python3 /tmp/dhcpd.py
# --- 配置端口
mv /etc/default/isc-dhcp-server /etc/default/isc-dhcp-server.bak
cat > /etc/default/isc-dhcp-server << EOF
INTERFACESv4="${VPN_IF_NAME}"
INTERFACESv6="${VPN_IF_NAME}"
EOF

# --- 启动服务
systemctl restart isc-dhcp-server
systemctl status isc-dhcp-server
```

### 允许转发流量

在每个境外VPS上执行：

```bash
iptables -A FORWARD -i ${VPN_IF} -j ACCEPT
iptables -A FORWARD -o ${VPN_IF} -j ACCEPT
iptables -t nat -A POSTROUTING -o ${WAN_IF} -j MASQUERADE
ip6tables -A FORWARD -i ${VPN_IF} -j ACCEPT
ip6tables -A FORWARD -o ${VPN_IF} -j ACCEPT
ip6tables -t nat -A POSTROUTING -o ${WAN6_IF} -j MASQUERADE
```

## 客户端配置

### 初始化环境变量

```bash
export PASSWD="lzy_chAnGED-PwD2c"
export REMOTE_IP="203.0.113.19"

```

### 安装VPN Client

```bash
sudo apt update && sudo apt install softether-vpnclient
cat > /tmp/vpncmd.stdin << EOF
2
localhost
RemoteEnable
PasswordSet
${PASSWD}
${PASSWD}

EOF
vpncmd < /tmp/vpncmd.stdin
```

### 安装REALITY客户端

```bash
sudo apt update && sudo apt install unzip

mkdir /usr/local/xray
wget https://app.dreamchaser-luzeyu.cn/gh/https://github.com/XTLS/Xray-core/releases/download/v1.8.24/Xray-linux-64.zip -O /tmp/xray.zip
#wget https://helper.020124.xyz/-----https://github.com/XTLS/Xray-core/releases/download/v1.8.24/Xray-linux-64.zip -O /tmp/xray.zip

unzip /tmp/xray.zip -d /tmp/xray
cp /tmp/xray/* /usr/local/xray/
#wget https://app.dreamchaser-luzeyu.cn/caalist/d/StaticFiles/ipv6f46c0039-302a-4bae-d968-a0e545aa0ef7.json -O /usr/local/xray/config.json
#wget https://app.dreamchaser-luzeyu.cn/caalist/d/StaticFiles/ipallf46c0039-302a-4bae-d968-a0e545aa0ef7.json -O /usr/local/xray/config.json

cat > /usr/lib/systemd/system/xray.service << EOF
[Unit]
Description=Xray
After=systemd-networkd-wait-online.service

[Service]
Type=simple
StartLimitIntervalSec=0
Restart=always
RestartSec=1
ExecStart=/usr/local/xray/xray run -c /usr/local/xray/config.json

[Install]
WantedBy=multi-user.target
EOF

cat > /usr/local/xray/config.json << EOF
{
    "dns": {
        "disableFallback": true,
        "servers": [
            {
                "address": "https://203.0.113.14/dns-query",
                "domains": [],
                "queryStrategy": ""
            },
            {
                "address": "localhost",
                "domains": [],
                "queryStrategy": ""
            }
        ],
        "tag": "dns"
    },
    "inbounds": [
        {
            "listen": "127.0.0.1",
            "port": 2080,
            "protocol": "socks",
            "settings": {
                "udp": true
            },
            "sniffing": {
                "destOverride": [
                    "http",
                    "tls",
                    "quic"
                ],
                "enabled": true,
                "metadataOnly": false,
                "routeOnly": true
            },
            "tag": "socks-in"
        },
        {
            "listen": "127.0.0.1",
            "port": 2081,
            "protocol": "http",
            "sniffing": {
                "destOverride": [
                    "http",
                    "tls",
                    "quic"
                ],
                "enabled": true,
                "metadataOnly": false,
                "routeOnly": true
            },
            "tag": "http-in"
        }
    ],
    "log": {
        "loglevel": "warning"
    },
    "outbounds": [
        {
            "domainStrategy": "AsIs",
            "flow": null,
            "protocol": "vless",
            "settings": {
                "vnext": [
                    {
                        "address": "203.0.113.19",
                        "port": 8443,
                        "users": [
                            {
                                "encryption": "none",
                                "flow": "",
                                "id": "a60aa17c-7ce6-4ec0-a2c9-8db730f15bf4"
                            }
                        ]
                    }
                ]
            },
            "streamSettings": {
                "network": "tcp",
                "realitySettings": {
                    "fingerprint": "random",
                    "publicKey": "PGG2EYOvsFt2lAQTD7lqHeRxz2KxvllEDKcUrtizPBU",
                    "serverName": "aws.amazon.com",
                    "shortId": "a9aa79f2",
                    "spiderX": ""
                },
                "security": "reality"
            },
            "tag": "proxy"
        },
        {
            "domainStrategy": "",
            "protocol": "freedom",
            "tag": "direct"
        },
        {
            "domainStrategy": "",
            "protocol": "freedom",
            "tag": "bypass"
        },
        {
            "protocol": "blackhole",
            "tag": "block"
        },
        {
            "protocol": "dns",
            "proxySettings": {
                "tag": "proxy",
                "transportLayer": true
            },
            "settings": {
                "address": "203.0.113.14",
                "network": "tcp",
                "port": 53,
                "userLevel": 1
            },
            "tag": "dns-out"
        }
    ],
    "policy": {
        "levels": {
            "1": {
                "connIdle": 30
            }
        },
        "system": {
            "statsOutboundDownlink": true,
            "statsOutboundUplink": true
        }
    },
    "routing": {
        "domainStrategy": "AsIs",
        "rules": [
            {
                "inboundTag": [
                    "socks-in",
                    "http-in"
                ],
                "outboundTag": "dns-out",
                "port": "53",
                "type": "field"
            },
            {
                "outboundTag": "proxy",
                "port": "0-65535",
                "type": "field"
            }
        ]
    },
    "stats": {}
}
EOF

systemctl enable xray
systemctl restart xray
systemctl status xray
curl ip.sb -4 --proxy socks5://127.0.0.1:2080
```

### 配置端口转发

此步骤实测不需要，只需连接时通过socks5代理即可

```bash
cat > /tmp/config_xray.py << EOF
import json

json_obj = {}
with open("/usr/local/xray/config.json", 'r') as file:
    json_obj = json.load(file)

remote_server_ip = input("远程服务器IP: ")
while True:
    port_fwd = input("是否继续添加使用端口转发？(y/n)")
    if port_fwd != 'y': break
    protocol = input("转发协议: (tcp/udp)")
    if protocol != "tcp" and protocol != "udp":
        print("协议输入错误")
        continue
    local_listen_ip = input("本地监听IP: ")
    local_listen_port = input("本地监听端口: ")
    remote_ip = input("远程IP: ")
    remote_port = input("远程端口: ")
    port_fwd_obj = {
        "address": local_listen_ip,
        "port": int(local_listen_port),
        "protocol": "dokodemo-door",
        "settings": {
            "address": remote_ip,
            "port": int(remote_port),
            "network": "tcp"
        }
    }
    json_obj['inbounds'].append(port_fwd_obj)
    json_obj['outbounds'][0]['settings']['vnext'][0]['address'] = remote_server_ip

with open("/usr/local/xray/config.json", 'w') as file:
    json.dump(json_obj, file, indent=4)
EOF
clear
python3 /tmp/config_xray.py
systemctl restart xray
systemctl status xray
curl ip.sb -4 --proxy socks5://127.0.0.1:2080

```

### 连接VPN（手动操作）

不改变路由表；禁用UDP加速；修改连接数

### 配置VPN端口为DHCP

配置netplan

### 路由境外IP

### 源IP策略路由

这样配置好后，只有前面添加过静态路由的源IP才能访问到服务器，为了让所有来源IP都能访问到服务器，应配置策略路由，让源IP为本机公网IP的数据包不经过VPN。

```bash
export CN_TABLE="100"
export PUBLIC_IPV4="203.0.113.20/32"
export PUBLIC_IPV6="240e:f7:a020:204::4eb6/112"
export IPV4_GATEWAY="203.0.113.21"
export IPV6_GATEWAY="240e:f7:a020:204::1"

ip route add default via ${IPV4_GATEWAY} dev eth0 table ${CN_TABLE}
ip -6 route add default via ${IPV6_GATEWAY} dev eth0 table ${CN_TABLE}
ip rule add from ${PUBLIC_IPV4} table ${CN_TABLE}
ip -6 rule add from ${PUBLIC_IPV6} table ${CN_TABLE}
```