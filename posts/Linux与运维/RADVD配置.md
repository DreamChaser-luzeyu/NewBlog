---
date: 2026-04-26
tags:
- RADVD
- IPv6
- 路由通告
- Linux网络
title: RADVD配置
---

# RADVD配置

```bash
apt install radvd

export RA_IF="enp1s0"
# 前缀必须是64
export RA_IPV6_CIDR="2a12:ab80:3:2100::/64"
cat > /etc/radvd.conf << EOF
interface ${RA_IF} {
    AdvSendAdvert on;
    AdvManagedFlag on;
    AdvOtherConfigFlag on;
    prefix ${RA_IPV6_CIDR} {
        AdvOnLink on;
        AdvAutonomous on;
        AdvRouterAddr off;  
    };
    # 对于旁路由还需配置route，2000::/3是全球单拨地址范围
    # 如果希望IPv6不流经旁路由，可以略去这部分
    route 2000::/3 {
        AdvRouteLifetime 1800;
        AdvRoutePreference high;  # 宣称为高优先级，旁路由掉线可自动切换为主路由
    };
};
EOF
unset RA_IF
unset RA_IPV6_CIDR
cat /etc/radvd.conf
# 启动服务
systemctl enable radvd
systemctl restart radvd
systemctl status radvd
```