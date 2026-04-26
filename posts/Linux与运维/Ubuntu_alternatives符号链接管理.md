---
date: 2026-04-26
tags:
- Ubuntu
- update-alternatives
- 符号链接
- 工具链
title: 'Usage:'
---

```bash
# Usage: 
# 安装符号链接 update-alternatives --install <link> <name> <path> <priority>
# 注：priority数值越大，优先级越高？需要确认
# 删除符号链接 update-alternatives --remove <name> <path>

# Example: 切换aarch64-linux-gnu-gcc版本
# 假设$PATH里存在aarch64-linux-gnu-gcc-11和aarch64-linux-gnu-gcc-12
update-alternatives --install \
    $(which aarch64-linux-gnu-gcc) \
    aarch64-linux-gnu-gcc \
    $(which aarch64-linux-gnu-gcc-11) 50
update-alternatives --install \
    $(which aarch64-linux-gnu-gcc) \
    aarch64-linux-gnu-gcc \
    $(which aarch64-linux-gnu-gcc-12) 40
update-alternatives --config aarch64-linux-gnu-gcc
# 选取一个即可
aarch64-linux-gnu-gcc --version
```