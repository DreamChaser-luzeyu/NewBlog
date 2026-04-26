---
date: 2026-04-26
tags:
- Linux
- binfmt_misc
- QEMU
- 跨架构
- ELF
title: Linux binfmt_misc特性
---

# Linux binfmt_misc特性

## 启用binfmt_misc

如果之前装过其他体系架构的qemu-user软件包或是wine，此特性应该已经启用。

```bash
# 验证binfmt_misc是否启用
lsmod | grep binfmt_misc
# 如有输出，表示已启用
# 手动启用步骤如下
sudo modprobe binfmt_misc
# 或者
# sudo mount binfmt_misc -t binfmt_misc /proc/sys/fs/binfmt_misc
```

查看已有的binfmt_misc配置，并为QEMU注册binfmt_misc

```bash
# 查看已有binfmt_misc配置
ls /proc/sys/fs/binfmt_misc
# 检查有没有update-binfmts命令
which update-binfmts
# 如没有，安装
sudo apt install binfmt-support
# 启用qemu-aarch64支持
sudo apt install qemu-user-binfmt qemu-user -y
sudo update-binfmts --enable qemu-aarch64
ls /proc/sys/fs/binfmt_misc
```

## 执行其他架构的elf

对于多数elf，需要额外配置该架构库文件的路径。可以使用`LD_LIBRARY_PATH`环境变量。

对于搜索路径固定的动态链接库，QEMU还提供了`QEMU_LD_PREFIX`环境变量用于配置动态链接库搜索的根目录。如：

```bash
QEMU_LD_PREFIX=/usr/aarch64-linux-gnu ./llama-cli 
```