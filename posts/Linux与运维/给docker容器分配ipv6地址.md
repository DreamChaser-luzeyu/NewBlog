---
date: 2026-04-26
tags:
- Docker
- IPv6
- 容器网络
title: 给docker容器分配ipv6地址
---

# 给docker容器分配ipv6地址

还是用内网ipv6吧

`/etc/docker/daemon.json`

```
{
  "ipv6": true,
  "fixed-cidr-v6": "fd00:cafe::/64",
  "ip6tables": true
}
```

```bash
sudo sysctl -w net.ipv6.conf.all.forwarding=1
sudo ip6tables -t nat -A POSTROUTING -s fd00:cafe::/64 -o eth0 -j MASQUERADE
```

之后正常创建容器即可