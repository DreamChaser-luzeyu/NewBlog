---
date: 2026-04-26
tags:
- Docker
- Tailscale
- DERP
- 容器部署
- 网络代理
title: Docker部署derp
---

# Docker部署derp

## 配置docker pull代理

```bash
mkdir -p /etc/systemd/system/docker.service.d
touch /etc/systemd/system/docker.service.d/http-proxy.conf
cat > /etc/systemd/system/docker.service.d/http-proxy.conf << EOF
[Service]
Environment="HTTP_PROXY=127.0.0.1:7897"
Environment="HTTPS_PROXY=127.0.0.1:7897"
EOF
systemctl daemon-reload
systemctl restart docker
systemctl show --property=Environment docker
```

## 搭建derp

```bash
docker run -d --name tailscale-derp -p 36666:36666 -p 3478:3478/udp --restart=always javaow/tailscale-derp
# a backup image
# docker run --restart always --net host --name derper -d ghcr.io/yangchuansheng/ip_derper
```

如果是NAT机，需映射36666和3478端口

## 控制台ACL配置

```json
    "derpMap": {
		"OmitDefaultRegions": false,
		"Regions": {
			"910": {
				"RegionID":   910,
				"RegionCode": "CN163",
				"Nodes": [
					{
						"Name": "BigChick-ChinaNet-IPv4",
						"RegionID": 910,
						"HostName": "ddns.163.bigchick.dreamchaser-luzeyu.cn",
						"InsecureForTests": true,
						"DERPPort": 10072,
                        "STUNPort": 10003
					},
                    {
						"Name": "BigChick-ChinaNet-IPv6",
						"RegionID": 910,
						"HostName": "240e:974:eb00:908::5064:118",
						"InsecureForTests": true,
						"DERPPort": 36666,
                        "STUNPort": 3478
					},
				],
				"RegionName": "CN163-BigChick",
			},
            "911": {
				"RegionID":   911,
				"RegionCode": "CMCC",
				"Nodes": [
					{
						"Name": "BigChick-CMCC-IPv4",
						"RegionID": 911,
						"HostName": "ddns.cmcc.bigchick.dreamchaser-luzeyu.cn",
						"InsecureForTests": true,
						"DERPPort": 10097,
                        "STUNPort": 10000
					},
                    {
						"Name": "BigChick-CMCC-IPv6",
						"RegionID": 911,
						"HostName": "2409:8c60:2400:2:0:4:1:556",
						"InsecureForTests": true,
						"DERPPort": 36666,
                        "STUNPort": 3478
					},
				],
				"RegionName": "CMCC-BigChick",
			},
            "912": {
				"RegionID":   912,
				"RegionCode": "HK",
				"Nodes": [
					{
						"Name": "HK-Hostyun-IPv6-1",
						"RegionID": 912,
						"HostName": "2a12:ab80:3:1000::124:521",
						"InsecureForTests": true,
						"DERPPort": 36666,
                        "STUNPort": 3478
					},
					{
						"Name": "HK-Hostyun-IPv6-2",
						"RegionID": 912,
						"HostName": "2a12:ab80:3:1000::124:522",
						"InsecureForTests": true,
						"DERPPort": 36666,
                        "STUNPort": 3478
					},   
					{
						"Name": "HK-Hostyun-IPv6-3",
						"RegionID": 912,
						"HostName": "2a12:ab80:3:1000::124:523",
						"InsecureForTests": true,
						"DERPPort": 36666,
                        "STUNPort": 3478
					},
					{
						"Name": "HK-Hostyun-IPv6-4",
						"RegionID": 912,
						"HostName": "2a12:ab80:3:1000::124:524",
						"InsecureForTests": true,
						"DERPPort": 36666,
                        "STUNPort": 3478
					},
					{
						"Name": "HK-Hostyun-IPv6-5",
						"RegionID": 912,
						"HostName": "2a12:ab80:3:1000::124:525",
						"InsecureForTests": true,
						"DERPPort": 36666,
                        "STUNPort": 3478
					},
				],
				"RegionName": "HK-Hostyun-IPv6",
			},
            "913": {
				"RegionID":   913,
				"RegionCode": "HK",
				"Nodes": [
                    {
						"Name": "HK-Hostyun-IPv4",
						"RegionID": 913,
						"HostName": "203.0.113.10",
						"InsecureForTests": true,
						"DERPPort": 36666,
                        "STUNPort": 3478
					},
                    {
						"Name": "HK-WePC-IPv4",
						"RegionID": 913,
						"HostName": "203.0.113.11",
						"InsecureForTests": true,
						"DERPPort": 36666,
                        "STUNPort": 3478
					},                    
				],
				"RegionName": "CN-Opt",
			},            
		},
	},
```

# 路由流量

## 声明路由

```bash
curl -fsSL https://tailscale.com/install.sh | sh

cd /tmp
mkdir ts_routes
cd ts_routes
# 电信、联通IP
wget https://gaoyifan.github.io/china-operator-ip/chinanet.txt
wget https://gaoyifan.github.io/china-operator-ip/chinanet6.txt
wget https://gaoyifan.github.io/china-operator-ip/drpeng.txt
wget https://gaoyifan.github.io/china-operator-ip/drpeng6.txt
wget https://gaoyifan.github.io/china-operator-ip/unicom.txt
wget https://gaoyifan.github.io/china-operator-ip/unicom6.txt
wget https://gaoyifan.github.io/china-operator-ip/tietong.txt
wget https://gaoyifan.github.io/china-operator-ip/tietong6.txt
# 移动IP
wget https://gaoyifan.github.io/china-operator-ip/cmcc.txt
wget https://gaoyifan.github.io/china-operator-ip/cmcc6.txt
# CERNET
wget https://gaoyifan.github.io/china-operator-ip/cernet.txt
wget https://gaoyifan.github.io/china-operator-ip/cernet6.txt
# Global IP
wget https://github.com/Loyalsoldier/geoip/raw/release/text/cloudflare.txt
wget https://github.com/Loyalsoldier/geoip/raw/release/text/cloudfront.txt
wget https://github.com/Loyalsoldier/geoip/raw/release/text/google.txt
wget https://gaoyifan.github.io/china-operator-ip/googlecn.txt
wget https://gaoyifan.github.io/china-operator-ip/googlecn6.txt
wget https://github.com/Loyalsoldier/geoip/raw/release/text/telegram.txt
wget https://github.com/Loyalsoldier/geoip/raw/release/text/twitter.txt
wget https://github.com/Loyalsoldier/geoip/raw/release/text/fastly.txt
wget https://github.com/Loyalsoldier/geoip/raw/release/text/facebook.txt
wget https://app.dreamchaser-luzeyu.cn/caalist/d/StaticFiles/github_cidr.txt
wget https://app.dreamchaser-luzeyu.cn/caalist/d/StaticFiles/wikimedia_cidr.txt
wget https://app.dreamchaser-luzeyu.cn/caalist/d/StaticFiles/pixiv_cidr.txt
wget https://app.dreamchaser-luzeyu.cn/caalist/d/StaticFiles/vercel_cidr.txt
# US & JP
wget https://github.com/Loyalsoldier/geoip/raw/release/text/us.txt
wget https://github.com/Loyalsoldier/geoip/raw/release/text/jp.txt
# Global DNS
cat > ./dns.txt << EOF
203.0.113.12/32
203.0.113.13/32
203.0.113.14/32
203.0.113.15/32
2001:4860:4860::8888/128
2001:4860:4860::8844/128
203.0.113.16/32
EOF
# Netflix IP
wget https://github.com/Loyalsoldier/geoip/raw/release/text/netflix.txt

# 合并要转发的IP
rm ./routed.txt
cat ./*.txt > ./routed.txt
tailscale set --advertise-routes $(cat ./routed.txt | tr "\n" "," | sed "s/,$//g")

# 禁止路由netflix ipv6
cat netflix.txt | grep ":" > netflix6.txt
ip6tables --flush
sed -i 's/^/ip6tables -I FORWARD -d /g' ./netflix6.txt
sed -i 's/$/ -j REJECT/g' ./netflix6.txt
cat ./netflix6.txt | sed "s/FORWARD/OUTPUT/g" >> netflix6.txt
mv ./netflix6.txt ./reject_nf6.sh
bash ./reject_nf6.sh
```

## 开启转发

```bash
sed -i "s/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/g" /etc/sysctl.conf
sed -i "s/#net.ipv6.conf.all.forwarding=1/net.ipv6.conf.all.forwarding=1/g" /etc/sysctl.conf
sysctl -p

# --- 让来自其他机器的流量走tun接口
ip route add default dev tun_if table 90
ip -6 route add default dev tun_if table 90
ip rule add from 100.64.0.0/10 table 90
ip -6 rule add from fd7a:115c:a1e0::/48 table 90
```