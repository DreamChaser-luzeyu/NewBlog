---
date: 2026-04-26
tags:
- MPTCP
- 多路径传输
- socat
- gost
- 网络优化
title: MPTCP 内核配置
---

# MPTCP 内核配置

## 服务端

```bash
sudo -i sysctl net.mptcp.enabled
sudo ip mptcp endpoint add [Another Path IP] signal  # Add path 203.0.113.17
ip mptcp limits show
sudo ip mptcp limits set subflow 2

sudo sed -i 's/# addr-flags=subflow/addr-flags=subflow/' /etc/mptcpd/mptcpd.conf # 编辑配置
sudo systemctl restart mptcp # 重启
ip mptcp limits show # 检查

# Convert MPTCP stream to normal TCP stream
socat TCP4-LISTEN:[MPTCP Port],fork,protocol=0x106,nodelay TCP:127.0.0.1:[Server Port]
# Run server on [Server Port]
```

```bash
sudo -i sysctl net.mptcp.enabled
sudo ip mptcp endpoint add 203.0.113.11 signal
sudo ip mptcp endpoint add 203.0.113.18 signal
ip mptcp limits show
# 似乎重启后就是8
# sudo ip mptcp limits set subflow 3

sudo sed -i 's/# addr-flags=subflow/addr-flags=subflow/' /etc/mptcpd/mptcpd.conf
sudo systemctl restart mptcp
ip mptcp limits show

# Convert MPTCP stream to normal TCP stream
socat TCP4-LISTEN:10079,fork,protocol=0x106,nodelay TCP:127.0.0.1:80
# Run server on [Server Port]
```



## 客户端

```bash
sudo -i sysctl net.mptcp.enabled
sudo ip mptcp endpoint add [Another Path IP] subflow # 应该可省略
ip mptcp limits show
sudo ip mptcp limits set add_addr_accepted 2
sudo ip mptcp limits set subflow 2

sudo sed -i 's/# addr-flags=subflow/addr-flags=subflow/' /etc/mptcpd/mptcpd.conf # 编辑配置
sudo systemctl restart mptcp # 重启
ip mptcp limits show # 检查

# Convert normal TCP stream to MPTCP stream
socat TCP4-LISTEN:[Local MPTCP Port],fork TCP:[Server_IP]:[Server_MPTCP_Port],protocol=0x106,nodelay
# Run client and connect to 127.0.0.1:[Local MPTCP Port]
```

```bash
sudo -i sysctl net.mptcp.enabled
# sudo ip mptcp endpoint add 203.0.113.10 subflow 
ip mptcp limits show
sudo ip mptcp limits set add_addr_accepted 2
sudo ip mptcp limits set subflow 2

sudo sed -i 's/# addr-flags=subflow/addr-flags=subflow/' /etc/mptcpd/mptcpd.conf
sudo systemctl restart mptcp
ip mptcp limits show

# Convert normal TCP stream to MPTCP stream
socat TCP4-LISTEN:4079,fork TCP:203.0.113.10:8079,protocol=0x106,nodelay
# Run client and connect to 127.0.0.1:[Local MPTCP Port]
```

# MPTCP aggligator配置

## 服务端

```bash
sudo apt update
# sudo apt install cargo -y
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
cargo install aggligator-util

# Multipath Port: 用于接收来自不同路径TCP子流的监听端口
# Server Port: 要使用MPTCP的服务的端口
agg-tunnel server --tcp [Multipath Port] --port [Server Port]
```

```bash
agg-tunnel server --tcp 79 --port 80  # HK Hostyun
```

## 客户端

```bash
sudo apt update
# sudo apt install cargo -y
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
# CN
export RUSTUP_DIST_SERVER="https://rsproxy.cn"
export RUSTUP_UPDATE_ROOT="https://rsproxy.cn/rustup"
curl --proto '=https' --tlsv1.2 -sSf https://rsproxy.cn/rustup-init.sh | sh
cargo install aggligator-util


# [Transit IP]:[Port] : 接收子流的IP和端口，可以写中转机的IP:端口，或是服务机的Multipath Port
# [Remote Server Port]: 远程服务的端口
# [Local Listen Port]: 本地监听的端口，访问此端口相当于通过MPTCP连接远程服务
agg-tunnel client \
--tcp [Transit IP]:[Port] \
--tcp [Transit IP]:[Port] \
--port [Remote Server Port]:[Local Listen Port]

```

```bash
agg-tunnel client \
--tcp 203.0.113.10:79 \
--tcp 203.0.113.11:79 \
--tcp 203.0.113.18:79 \
--port 80:4080
```

# 中转机

```bash
echo 1 > /proc/sys/net/ipv4/ip_forward
sysctl -p
# iptables -t nat -A PREROUTING -p tcp --dport 79 -j DNAT --to-destination 203.0.113.10:79
iptables -t nat -A PREROUTING -p tcp --dport 10079 -j DNAT --to-destination 203.0.113.10:10079
iptables -t nat -A POSTROUTING -j MASQUERADE  # 动态伪装，修改来源IP为本机
```

# 服务器端口号对应关系

各个vps将通过何端口转发到指定vps，这些端口都是MPTCP的端口

GOST统一使用16400端口，GOST的MPTCP端口使用79~75端口

```
[VPS]             [HTTP] [Local Port]
HK Hostyun  ---    10079   10079 
HK WePC     ---    10078    
JP YxVM     ---    10077    
SG Azure    ---    10076    
US Racknerd ---    10075    
```

# 其他

## cargo换源

`nano ~/.cargo/config`

```toml
[source.crates-io]
registry = "https://github.com/rust-lang/crates.io-index"
# 指定镜像
replace-with = 'ustc' # 如：tuna、sjtu、ustc，或者 rustcc

# 注：以下源配置一个即可，无需全部

# 中国科学技术大学
[source.ustc]
registry = "https://mirrors.ustc.edu.cn/crates.io-index"
# >>> 或者 <<<
# registry = "git://mirrors.ustc.edu.cn/crates.io-index"

# 上海交通大学
[source.sjtu]
registry = "https://mirrors.sjtug.sjtu.edu.cn/git/crates.io-index/"

# 清华大学
[source.tuna]
registry = "https://mirrors.tuna.tsinghua.edu.cn/git/crates.io-index.git"

# rustcc社区
[source.rustcc]
registry = "https://code.aliyun.com/rustcc/crates.io-index.git"
```

## Daemonize

### 远程

`mptcp-http80.service`

```
[Unit]
Description=MPTCP HTTP80
After=network.target          # 服务依赖（再这些服务后启动本服务）

[Service]
Type=forking                  # 服务类型 simple/forking/oneshot/dbus/notify/idle
ExecStart=socat TCP4-LISTEN:8079,fork,protocol=0x106,nodelay TCP:127.0.0.1:80
                              # 启动命令

[Install]
WantedBy=multi-user.target    # 服务安装设置，multi-user.target是默认的自启动target
                              # 这个组里的所有服务都将开机启动
```

`mptcp-ssgost.service`

```
[Unit]
Description=MPTCP ssgost
After=network.target          # 服务依赖（再这些服务后启动本服务）

[Service]
Type=forking                  # 服务类型 simple/forking/oneshot/dbus/notify/idle
ExecStart=socat TCP4-LISTEN:79,fork,protocol=0x106,nodelay TCP:127.0.0.1:16400
                              # 启动命令

[Install]
WantedBy=multi-user.target    # 服务安装设置，multi-user.target是默认的自启动target
                              # 这个组里的所有服务都将开机启动
```

`gost-tunnel.service`

```
[Unit]
Description=Gost Tunnel Global
After=network.target          # 服务依赖（再这些服务后启动本服务）

[Service]
Type=forking                  # 服务类型 simple/forking/oneshot/dbus/notify/idle
ExecStart=gost -L=mwss://:16400/127.0.0.1:8964
                              # 启动命令

[Install]
WantedBy=multi-user.target    # 服务安装设置，multi-user.target是默认的自启动target
                              # 这个组里的所有服务都将开机启动
```

或者使用脚本

```bash
#!/bin/bash
nohup gost -L=mwss://:16400/127.0.0.1:8964 >> ./gost.log 2>&1 &
nohup socat TCP4-LISTEN:8079,fork,protocol=0x106,nodelay TCP:127.0.0.1:80 >> ./mptcp80.log 2>&1 &
nohup socat TCP4-LISTEN:79,fork,protocol=0x106,nodelay TCP:127.0.0.1:16400 >> ./mptcpssgost.log 2>&1 &
```

### 本地

`mptcp-http80.service`

```
[Unit]
Description=MPTCP ssgost
After=network.target          # 服务依赖（再这些服务后启动本服务）

[Service]
Type=forking                  # 服务类型 simple/forking/oneshot/dbus/notify/idle
ExecStart=socat TCP4-LISTEN:8079,fork TCP:203.0.113.10:8079,protocol=0x106,nodelay
                              # 启动命令

[Install]
WantedBy=multi-user.target    # 服务安装设置，multi-user.target是默认的自启动target
                              # 这个组里的所有服务都将开机启动
```

`gost-tunnel.service`

```
[Unit]
Description=Gost Tunnel Local
After=network.target          # 服务依赖（再这些服务后启动本服务）

[Service]
Type=forking                  # 服务类型 simple/forking/oneshot/dbus/notify/idle
ExecStart=gost -L=tcp://:4079 -F=mwss://127.0.0.1:16400
                              # 启动命令

[Install]
WantedBy=multi-user.target    # 服务安装设置，multi-user.target是默认的自启动target
                              # 这个组里的所有服务都将开机启动
```

或者使用脚本

```bash
#!/bin/bash
nohup socat TCP4-LISTEN:8079,fork TCP:203.0.113.10:8079,protocol=0x106,nodelay >> ./mptcp80.log 2>&1 &
nohup socat TCP4-LISTEN:16400,fork TCP:203.0.113.10:79,protocol=0x106,nodelay >> ./mptcpssgost.log 2>&1 &
nohup gost -L=tcp://:4079 -F=mwss://127.0.0.1:16400 >> ./gost.log 2>&1 &
```

###