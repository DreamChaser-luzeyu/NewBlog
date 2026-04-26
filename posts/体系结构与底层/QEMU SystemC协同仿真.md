---
date: 2026-04-26
tags:
- QEMU
- SystemC
- 协同仿真
- Buildroot
- 虚拟化
title: QEMU SystemC协同仿真
---

# QEMU SystemC协同仿真

环境：http://100.122.249.83:8080/

https://patchwork.kernel.org/

## 实验方法



## 实验命令

### 构建并运行官方Buildroot

```bash
make qemu_aarch64_virt_defconfig

```



### 运行SystemC端演示demo

```bash
# PWD at `/media/luzeyu/Files/ysyx/xilinx-cosim/systemctlm-cosim-demo`
LD_LIBRARY_PATH="/media/luzeyu/Files/ysyx/xilinx-cosim/systemc-2.3.2/install/lib-linux64/" ./zynq_demo unix:/media/luzeyu/Ext4Storage/cosim/buildroot/handles/qemu-rport-_cosim@0 1000000

# PWD at `/media/luzeyu/Files/ysyx/xilinx-cosim/qemu/install`
./usr/local/bin/qemu-system-aarch64 -M arm-generic-fdt-7series -m 1G \
-kernel /media/luzeyu/Ext4Storage/cosim/buildroot/output/images/uImage \
-dtb /media/luzeyu/Ext4Storage/cosim/buildroot/output/images/zynq-zc702.dtb \
--initrd /media/luzeyu/Ext4Storage/cosim/buildroot/output/images/rootfs.cpio.gz \
-serial /dev/null -serial mon:stdio -display none -net nic -net nic \
-machine-path /media/luzeyu/Ext4Storage/cosim/buildroot/handles/ \
-icount 0,sleep=off -rtc clock=vm -sync-quantum 1000000

```

## FAQ

- 使用Ctrl+A x退出QEMU

- clangd无法索引

  - 在buildroot根目录创建`.clangd`文件

    ```
    CompileFlags:
        Remove: -mabi=lp64
    ```

- 报错 内核header版本不符
  - 不要忘记修改Toolchain -> Kernel Headers

- `network backend 'user' is not compiled into this binary`
  - `--enable-slirp`即可