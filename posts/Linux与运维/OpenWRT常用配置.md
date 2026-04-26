---
date: 2026-04-26
tags:
- OpenWRT
- SmartDNS
- MWAN3
- UPnP
- 路由器
title: OpenWRT常用配置
---

# OpenWRT常用配置

## 屏蔽AAAA记录

### DNSMasq

如果LuCI上有屏蔽AAAA记录的选项，启用即可，否则建议改用smartdns

### SmartDNS

在`/etc/smartdns/address.conf`里添加：

```
force-AAAA-SOA yes
```

也可以在LuCI操作。

## Linux上配置UPnP

```bash
apt install miniupnpd
# 根据提示输入WAN端口和LAN端口
```

## MWAN3分流

### 安装MWAN3

```bash
opkg update
opkg install luci-app-mwan3
```

### 配置分流IPSet

```bash
mkdir /etc/ipsets
cd /etc/ipsets
cat > ./gen_ipsets.sh << EOF
#!/bin/sh
wget -c http://ftp.apnic.net/apnic/stats/apnic/delegated-apnic-latest
cat delegated-apnic-latest | awk -F '|' '/CN/&&/ipv4/ {print "ipset add ipv4_CN " $4 "/" 32-log($5)/log(2)}' | cat > /tmp/ipv4_CN.sh
sed -i '1s/^/#!\/bin\/bash\nipset create ipv4_CN hash:net hashsize 16384\n/' ipv4_CN.sh
cat delegated-apnic-latest | awk -F '|' '/CN/&&/ipv6/ {print "ipset add ipv6_CN " $4 "/" $5}' | cat > /tmp/ipv6_CN.sh
sed -i '1s/^/#!\/bin\/bash\nipset create ipv6_CN hash:net family inet6 hashsize 4096\n/' ipv6_CN.sh
rm delegated-apnic-latest
EOF
chmod +x ./gen_ipsets.sh
sh /tmp/ipv4_CN.sh
sh /tmp/ipv6_CN.sh
```

可以将`/etc/ipsets/gen_ipsets.sh`加入计划任务

### 路由表分流

```bash
export V4_GATEWAY="192.168.1.1 dev enp1s0"
export V6_GATEWAY="fd00:520::1 dev enp1s0"
wget http://ftp.apnic.net/apnic/stats/apnic/delegated-apnic-latest -O /tmp/delegated-apnic-latest
cat /tmp/delegated-apnic-latest | awk -F '|' '/CN/&&/ipv4/ {print $4 "/" 32-log($5)/log(2)}' | cat > /tmp/Direct_v4
cat /tmp/delegated-apnic-latest | awk -F '|' '/CN/&&/ipv6/ {print $4 "/" $5}' | cat > /tmp/Direct_v6
sed 's/^/ip route add /' /tmp/Direct_v4 > /tmp/no_route_ipv4.sh
sed -i "s/$/ via ${V4_GATEWAY}/" /tmp/no_route_ipv4.sh
sed 's/^/ip -6 route add /' /tmp/Direct_v6 > /tmp/no_route_ipv6.sh
sed -i "s/$/ via ${V6_GATEWAY}/" /tmp/no_route_ipv6.sh
unset V4_GATEWAY
unset V6_GATEWAY
sh /tmp/no_route_ipv4.sh
sh /tmp/no_route_ipv6.sh
```





## DNS分流

### 配置规则

```bash
wget https://rawghuc.020124.xyz/felixonmars/dnsmasq-china-list/master/accelerated-domains.china.conf
# 在第一行增加force-AAAA-SOA yes
sed -i "1i force-AAAA-SOA yes" ./accelerated-domains.china.conf
# 把所有的114.114.114.114替换为119.29.29.29
sed -i "s/203.0.113.34/203.0.113.35/g" ./accelerated-domains.china.conf
# 把所有的"server="替换成"nameserver "
sed -i "s/server=/nameserver /g" ./accelerated-domains.china.conf
# 覆盖原配置文件
mv /etc/smartdns/address.conf /etc/smartdns/address.conf.bak
cp ./accelerated-domains.china.conf /etc/smartdns/address.conf
# 重启smartdns
/etc/init.d/smartdns restart
```

### 替换DNSMasq

将dnsmasq监听端口改为其他端口，然后将smartdns监听端口改为53

## MSS钳制

各个端口的MTU要配置正确。

```bash
# --- MTU配置
# 填入自定义防火墙规则
iptables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu
ip6tables -t mangle -A FORWARD -p tcp --tcp-flags SYN,RST SYN -j TCPMSS --clamp-mss-to-pmtu
```