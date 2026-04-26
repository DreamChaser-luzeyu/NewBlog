---
date: 2026-04-26
tags:
- SoftEther VPN
- 自动化脚本
- DHCP
- Linux网络
title: SoftEther VPN Server + DHCPD
---

# SoftEther VPN Server + DHCPD

```bash
#!/bin/bash

# ----- 全部要用到的配置
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
# --- VPN用户名
export VPN_USERNAME="luzeyu"
export VPN_PASSWD="luzeyu"

# ----- 安装
apt install softether-vpnserver

# ----- 配置
# --- 配置VPN Server
# vpncmd
# "1\n" 1. Management of VPN Server or VPN Bridge 
# "127.0.0.1:5555\n" the host name or IP address of the VPN Server 
# "\n" If connecting by server admin mode


```