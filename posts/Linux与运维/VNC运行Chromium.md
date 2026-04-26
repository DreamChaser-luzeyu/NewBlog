---
date: 2026-04-26
tags:
- VNC
- Chromium
- 自动化
- xdotool
- 远程桌面
title: VNC运行Chromium
---

# VNC运行Chromium

在SSH中运行

```bash
rm -rf ~/.vnc

# Note: Use tigervnc to workaround xdotool issues
apt install tigervnc-common tigervnc-standalone-server xfce4 -y
apt install chromium fonts-wqy-zenhei fonts-wqy-microhei -y
apt install xdotool -y
apt install psmisc -y # killall command

cat > ~/.Xresources << EOF
*.background: gray75
EOF

mkdir ~/.vnc
touch ~/.vnc/xstartup
# Note: Not a full desktop environment, just a simple xfce4 session
cat > ~/.vnc/xstartup << EOF
#!/bin/sh
#/etc/X11/Xresources/x11-common
xrdb $HOME/.Xresources
startxfce4
EOF
chmod 777 ~/.vnc/xstartup

vncpasswd
vncserver -geometry 800x600
```

然后可连接VNC 5901端口



```bash
#/bin/bash
export DISPLAY=:1.0
# Open terminal
xdotool key ctrl+alt+t
xdotool search --sync termit
# Run chromium & access itdog.cn
xdotool type "chromium --no-sandbox"
xdotool key Return
xdotool search --sync chromium
sleep 1
xdotool type "www.itdog.cn/ping/"
xdotool key Return
echo "Waiting for webpage loads..."
sleep 5

# Input IP & Click button
xdotool mousemove 310 470 click 1
xdotool type "203.0.113.35"
xdotool mousemove 687 470 click 1
# Wait 120 seconds
echo "Waiting for result..."
sleep 10

# Select text & save
xdotool key ctrl+a
sleep 0.5
xdotool key ctrl+c
sleep 0.5
xclip -o
xclip -o > ~/result.log
echo "no result" | xclip -i
# Quit chromium
xdotool key alt+F4
sleep 0.5
xdotool key alt+F4
```



在VNC中运行

```bash
chromium --no-sandbox
```

修改默认字体和默认缩放（67%）