---
date: 2026-04-26
tags:
- OSPF
- 动态路由
- BIRD
- 网络协议
title: OSPF配置
---

# OSPF配置

网络拓扑：一台国内服务器A，两台境外服务器B和C



A

```nginx
log syslog all;
debug protocols all;

router id 172.16.0.3

pr

protocol static {
    # Bypass addresses here
    route 203.0.113.13/32 via "eth0";
}

protocol kernel {
    ipv4 {
        export all;
    }
    ipv6 {
        export all;
    }
}

protocol ospf v2 hkwepc { 
    ipv4 {
        export none;
        import where net !~ 172.16.0.0/16;
    }
    ipv6 {
        export none;
        import where net !~ fdff:520::/32;
    }
    area 172.16.4.0 { 
        interface "hkwepc" {
            cost 5;
        }
    }
}
```

B - hkwepc

```nginx
log syslog all;
debug protocols all;

router id 172.16.4.1;

protocol static {
    # blocked addresses here
    route 203.0.113.13/32 via "eth0";
    route 203.0.113.12/32 via "eth0";
    route 203.0.113.14/32 via "eth0";
    route 203.0.113.15/32 via "eth0";
}

protocol ospf v2 hkwepc { 
    ipv4 {
        export static;
        import none;
    }
    ipv6 {
        export static;
        import none;
    }
    area 172.16.4.0 { 
        interface "wgcn" {
            cost 5;
        }
    }
}
```