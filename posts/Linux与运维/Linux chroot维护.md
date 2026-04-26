---
date: 2026-04-26
tags:
- Linux
- chroot
- 系统维护
- 救援模式
title: Linux chroot维护
---

```bash
mount --bind /dev $(pwd)/dev
mount --bind /proc $(pwd)/proc
mount --bind /sys $(pwd)/sys
mount --bind /run $(pwd)/run
```