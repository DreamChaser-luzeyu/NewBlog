---
date: 2026-04-26
tags:
- iproute2
- WireGuard
- 策略路由
- Linux网络
title: 注：ip rule add table <id>命令会同时创建一个路由表
---

## 常用ip命令

```bash
ip route # 打印main路由表
ip route show table main # 打印main路由表的路由
ip route show table all # 打印全部路由表的路由
ip route get 203.0.113.12 # 获得1.1.1.1使用的路由
ip rule # 打印路由策略，数字表示优先级（数字小的优先）
ip rule add table 20124 # 
ip rule add from 192.168.1.0/24 table 1 prio 10 # 对于来自192.168.1.0/24的流量查询路由表1,优先级10
ip rule add from 192.168.2.0/24 table 2 # 对于来自192.168.2.0/24的流量查询路由表2,优先级自动（从32766递减）
# 注：ip rule add table <id>命令会同时创建一个路由表
```

## ip rule示例

```bash
root@luzeyu-c92:~# ip -6 rule
0:      from all lookup local
32764:  from all lookup main suppress_prefixlength 0
32765:  not from all fwmark 0xca6c lookup 51820
32766:  from all lookup main
```

### 解释`32764:  from all lookup main suppress_prefixlength 0`：

- `32764`表示这条规则的优先级
- `from all`表示对任何来源生效，即不限制来源地址
- `lookup main`表示查询`main`路由表
- `suppress_prefixlength 0` 表示抑制其中（目的地址）前缀为0的条目，即抑制默认路由


### 解释`32765:  not from all fwmark 0xca6c lookup 51820`：

- `32765`表示这条规则的优先级
- `not from all fwmark 0xca6c`表示**不**匹配`from all fwmark 0xca6c`的数据包，即**不**匹配任意来源的标记为`0xca6c`的数据包
- `lookup 51280`表示查询`51280`路由表

其含义为：对于防火墙标记**不**为`0xca6c`的流量查询51820路由表（若标记为`0xca6c`则继续尝试匹配下一个规则，即本例中的`32766`）

这种做法常见于VPN等隧道软件的实现中，VPN软件修改路由表让所有流量都从VPN网卡路由，并将打包、加密后的数据包加上一个标记，以免VPN打包加密后的数据再次进入VPN网卡，形成回环。

## wg-quick脚本

```bash
[#] wg set wg0 fwmark 51820
[#] ip -4 route add 0.0.0.0/0 dev wg0 table 51820
[#] ip -4 rule add not fwmark 51820 table 51820
[#] ip -4 rule add table main suppress_prefixlength 0
[#] sysctl -q net.ipv4.conf.all.src_valid_mark=1
[#] nft -f /dev/fd/63

[#] ip -4 rule delete table 51820
[#] ip -4 rule delete table main suppress_prefixlength 0
[#] nft -f /dev/fd/63
```

```bash
[#] ip link add wg0 type wireguard
[#] wg setconf wg0 /dev/fd/63
[#] ip -4 address add 172.16.0.2/16 dev wg0
[#] ip -6 address add fdff:520::2/32 dev wg0
[#] ip -6 address add 2a12:ab80:3:2000::2/52 dev wg0
[#] ip link set mtu 65456 up dev wg0
[#] resolvconf -a tun.wg0 -m 0 -x
[#] wg set wg0 fwmark 51820
[#] ip -6 route add ::/0 dev wg0 table 51820
[#] ip -6 rule add not fwmark 51820 table 51820
[#] ip -6 rule add table main suppress_prefixlength 0
[#] nft -f /dev/fd/63
[#] ip -4 route add 0.0.0.0/0 dev wg0 table 51820
[#] ip -4 rule add not fwmark 51820 table 51820
[#] ip -4 rule add table main suppress_prefixlength 0
[#] sysctl -q net.ipv4.conf.all.src_valid_mark=1
[#] nft -f /dev/fd/63
[#] iptables -A FORWARD -i enp1s0 -j ACCEPT; iptables -A FORWARD -o enp1s0 -j ACCEPT; iptables -t nat -A POSTROUTING -o wg0 -j MASQUERADE; ip6tables -A FORWARD -i wg0 -o enp1s0 -j ACCEPT; ip6tables -A FORWARD -i enp1s0 -o wg0 -j ACCEPT

[#] ip -4 rule delete table 51820
[#] ip -4 rule delete table 51820
[#] ip -4 rule delete table main suppress_prefixlength 0
[#] ip -4 rule delete table main suppress_prefixlength 0
[#] ip -6 rule delete table 51820
[#] ip -6 rule delete table main suppress_prefixlength 0
[#] ip link delete dev wg0
[#] resolvconf -d tun.wg0 -f
[#] nft -f /dev/fd/63
[#] iptables -D FORWARD -i enp1s0 -j ACCEPT; iptables -D FORWARD -o enp1s0 -j ACCEPT; iptables -t nat -D POSTROUTING -o wg0 -j MASQUERADE; ip6tables -D FORWARD -i wg0 -o enp1s0 -j ACCEPT; ip6tables -D FORWARD -i enp1s0 -o wg0 -j ACCEPT
```