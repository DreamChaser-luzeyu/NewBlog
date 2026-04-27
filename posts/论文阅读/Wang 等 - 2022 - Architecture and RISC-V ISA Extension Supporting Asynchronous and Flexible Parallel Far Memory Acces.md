---
title: 论文阅读：Architecture and RISC-V ISA Extension Supporting Asynchronous and Flexible Parallel Far Memory Access
date: 2026-04-27
tags:
- 论文阅读
---

文档由AI总结，可能有错误。

随着数据规模爆炸式增长，CPU处理速度远超内存访问速度，导致“内存墙”问题。远内存技术虽能提供更大容量，但访问延迟更高，传统CPU难以高效利用。本文提出一种基于RISC-V指令集扩展的架构，通过将内存访问的请求与响应解耦，支持非阻塞模式下的可变粒度异步加载/存储。软件可发出大量重叠内存请求，在等待响应时执行其他任务。在FPGA原型系统上测试表明，面对远内存额外延迟时，该方法平均实现1.1倍加速，在内存敏感基准测试和实际应用（如图计算）中均有改进。

# 摘要

如今，内存访问速度已显著落后于CPU性能的提升。随着数据集不断增大，远内存技术（如异构内存和内存池化）不断发展，“内存墙”问题变得愈发严重。远内存的访问延迟相比传统DRAM进一步增加，但它提供了更高的容量。然而，现代CPU对延迟敏感，无法高效地充分利用远内存资源。

我们提出了一种架构，该架构支持在远内存场景下显式操控大规模并行异步内存访问及其RISC-V ISA扩展（AME）。这项工作将内存访问操作的请求与响应解耦，并提供了非阻塞模式下可变粒度的异步加载/存储指令。软件可以使用AME发出大量重叠的内存访问请求，并在等待响应期间专注于其他工作，从而提升性能。

我们在 RISC-V CPU 上实现了 AME，并构建了基于 FPGA 的原型系统。评估结果表明，对于内存敏感的基准测试，当远内存引入的额外延迟相当于 2μs（面对 2GHz CPU 时）时，我们的方法平均实现了 $1.1\times$ 的加速比，且对于 HPCC Random Access，平均在途内存请求数达到 238。在其他实际内存受限的应用（如图计算和并发数据结构）中也显示出改进效果。

# 关键词

内存级并行性，异步内存访问

# 1 引言

如今，大数据应用对内存容量的需求日益增长（例如内存数据库、在线分析等）。为满足这一需求，各种新兴存储器正被引入数据中心。当前的一种解决方案是使用新型互连技术和协议来访问其他机器或内存池中的内存，例如CXL[2]、OpenCAPI[1]和GenZ[3]。另一个例子是非易失性主存（NVMM），它提供比DRAM更高的内存密度，并且仍能以缓存行粒度进行访问[4]。我们将上述所有存储器统称为远内存，因为它们通常连接松散，且访问延迟高于DRAM[24]。它们主要具有以下特征：

通过加载/存储指令直接访问。本文聚焦于应用通过加载/存储指令访问远内存的场景，而非将其用作交换设备。

• 广泛分布的延迟。应用可以访问远程节点或新型介质（如NVMM）上的内存，其访问延迟可分布在一个较宽的范围内。

• 潜在的大聚合容量与带宽。由于内存资源可来自多个节点，大量内存通道的总和使得聚合内存容量与带宽相比本地内存展现出显著优势，这对处理器充分利用丰富内存资源构成了挑战。

然而，现代CPU对内存访问延迟非常敏感。研究表明，当使用CXL在Azure中引入仅64ns的额外延迟时，内存密集型工作负载（如Redis和GAPBS）的平均性能下降超过30%[21]。现代CPU通过隐式发出并行内存请求来隐藏长访问延迟，其乱序执行机制会动态调度多个加载/存储指令并行执行。此外，非阻塞缓存通过未命中状态处理寄存器（MSHR）同时处理多个内存请求。在这种情况下，内存访问延迟通过内存级并行性（MLP）被隐藏。

延迟越长，所需的MLP（内存级并行度）就越高。典型DRAM延迟低于200纳秒，而远端内存延迟约为300纳秒至5微秒[4]。因此，远端内存系统上待处理的内存请求数量可能远大于本地DRAM系统。然而，为了发出并管理正在执行中的内存请求，CPU需要各种硬件资源，例如重排序缓冲区、物理寄存器文件、加载/存储队列和MSHR（缺失状态保持寄存器）。这些硬件资源限制了CPU的MLP，使其无法发出足够数量的请求来隐藏远端内存访问延迟。例如，单个英特尔Skylake核心最多只能支持12个正在执行中的DRAM内存访问[25]。此外，现有内存访问策略的粒度固定为缓存行大小，这对于小块数据的随机访问而言过大，而对于顺序和大块数据访问则不足。因此，在远端内存场景下，提升MLP面临两个挑战：

如何让CPU更充分、更灵活地利用高内存带宽？我们在CPU核心内部提出了异步内存访问单元（AMU）[27]。AMU将内存访问请求与响应的逻辑解耦，并使用比MSHR大得多的存储空间来记录正在处理的请求状态，从而支持并行发出大量请求。此外，由软件决定，加载/存储请求的大小也可从8B到1KB不等。AMU通过大量重叠请求并按需访问精确数据大小，帮助CPU充分利用带宽。

如何减少长延迟加载/存储指令对关键资源的占用？我们提出了RISC-V异步内存访问指令集扩展（AME）来解决这一问题。

长占用是由同步加载/存储指令在CPU流水线中等待响应并同时占用资源所导致的。作为AMU的软件接口，AME在概念上提供了来自CPU微架构的异步加载/存储指令（称为aload和astore）。Aload/astore指令无需等待数据响应即可提交。应用程序可以使用AME批量发出请求，并在等待响应期间执行其他计算以提升性能。

AMU 和 AME 均设计在 RISC-V 架构内部，因为 RISC-V 是一种开源且可扩展的指令集架构，且 RISC-V CPU 的架构更加简洁和现代化。我们基于 NutShell[5]（一个经过流片验证的按序开源 RISC-V64(IMACSU) SoC），使用 Chisel HDL[7] 实现了 AMU 和 AME。在此基础上，我们在 Xilinx ZYNQ UltraScale+ ZU19EG MPSoC 开发板上构建了一个基于 FPGA 的原型系统，其中还实现了一条支持高带宽和可变延迟的模拟远内存访问路径。在编程支持方面，我们提供了一个基于协程的敏捷编程框架，并在一系列内存敏感型基准测试上评估了性能。结果表明，当远内存引入的额外延迟为 2μs 且 CPU 主频为 2GHz 时，我们的方法平均实现了 $1.1\times$ 的加速比，对于 HPCC Random Access[22]，平均在途内存请求数达到 238，顺序内存访问达到 $63.48\times$，随机访问达到 $9.04\times$。并且我们发现，使用 AME 的应用程序对延迟变化不太敏感。

总之，本文做出了以下贡献：

(1) 提出一种RISC-V指令集扩展AME，并设计其架构AMU，通过可变粒度的异步访问来提升远内存的MLP。
(2) 设计一种利用AME开发MLP的编程范式。
(3) 在RISC-V CPU上实现AMU和AME，并搭建基于FPGA的原型系统。随后使用内存密集型工作负载对其进行评估。

# 2 背景

在本节中，我们首先介绍现有的掩盖长内存访问延迟的方法并分析其效果。然后概述我们设计的关键思路。

# 2.1 软件延迟容忍技术

远端内存相对较高的延迟给延迟敏感型应用带来了性能挑战。交错执行[20]是一种通用技术，通过运行多个协程（或轻量级线程）来隐藏延迟。由于现有CPU不具备异步访问指令，软件通过调用预取指令来实现类似异步访问的效果。软件首先发出预取指令，然后执行另一个协程。当预取操作预计完成时，再切换回来执行加载/存储指令以访问内存。

几种范式，如组预取（GP）、软件流水线预取（SPP）[12]和异步内存访问链（AMAC）[18]，被提出用于利用类查找操作的并行性。然而，将现有代码转换为应用这些范式是痛苦的[16]。要实现这种

范式容易，研究人员尝试使用 C++20 标准并发库[14, 16]或设计领域特定语言[17]。但这些方法的关键问题在于，应用程序无法知道数据是否已被提取到本地缓存，这既不智能也不具备可移植性。CPU能够同时处理的数据预取请求数量也是有限的。

# 2.2 硬件延迟容忍技术

基于乱序执行和非阻塞缓存，研究人员尝试通过多种不同方式提高处理器的延迟容忍能力（或提升内存级并行度）。

在实际中，MSHR 被实现为全相联阵列，这种结构难以扩展。为解决此问题，有研究提出用哈希阵列替代全相联 MSHR 阵列 [6, 26]。另一种思路是增加额外空间（如重排序缓冲区、指令队列等）来处理长加载延迟。例如，Load Slice Core[10] 和 Forward Slice Core[19] 通过 IBDA（一种依赖分析）支持，增加额外指令队列用于发射另一条加载/存储指令及其地址计算指令，且该过程对软件透明。通过这种方式，这些指令不再占用处理器中的关键资源。

所有这些技术的核心思想是让CPU能够动态调度并发出更多内存访问请求，以覆盖等待数据响应所导致的较长延迟。然而，它们都未能从根本上解决瓶颈问题——即关键硬件资源（如RF、ROB、IQ和MSHR）数量有限这一限制。假设CPU运行在2GHz频率下，远内存的1微秒访问延迟高达2000个时钟周期。当一条目标为远内存的加载指令被发出后，ROB需要数千级的条目来防止CPU流水线停顿，同时还需要数千个物理寄存器用于写回结果。如果后续还有大量加载指令，情况会变得更糟，可能还需要数百个MSHR。这些资源需求显然超出了当前技术所能提供的资源数量。因此，我们认为当前隐式发出并行内存请求的机制不足以应对远内存延迟。

# 2.3 AME 的核心思想

AME 是一种针对第 1 节所述问题的新颖解决方案，包含三项突破性的核心思想。核心思想 A 解决了传统加载和存储指令长时间占用关键硬件资源的问题。思想 B 允许 CPU 发出大批量内存访问请求，以充分利用带宽。而思想 C 以一种新方式解决了 CPU 流水线和缓存中关键资源不足的困境。

A. 可变粒度的异步内存访问指令。Aload 和 astore 指令在提交时无需等待内存响应，只需将请求写入 L2 缓存数据阵列中的异步内存请求队列（AMQ）。每个请求由一个 ID 标记。每个 ID 可重复使用，但要求软件在传输过程中保证其唯一性。对于远端内存访问路径，我们采用能够支持识别该 ID 的内存访问协议，大多数协议（例如 AXI4 中的 ID 信号）均支持此功能。我们还提供了一条指令 getfin 用于查询请求的完成状态。

该请求将返回一个已完成请求的ID。这是告知软件请求是否完成的方式。AME指令的异步设计可以极大地降低ROB和IQ的压力。

此外，`aload`和`astore`还支持从8B到1KB的可变粒度内存访问。粒度在AMU的控制寄存器中设置，这将在第3.3节中提及。这使得软件能够更灵活地按需进行小粒度随机访问，而无需适应缓存行大小。同时，单次加载或存储大量数据的请求可以更好地利用带宽。在第6节中，我们将通过实验证明可变粒度支持对AME的益处。

B. 解耦内存请求与响应。本工作将内存请求通道和响应通道的处理逻辑分离，而此前这两者是顺序耦合的。异步内存请求逻辑依次通过AMQ发出异步内存请求。异步内存响应逻辑还维护一个异步内存请求完成ID队列（AFQ），该逻辑处理数据响应并将完成ID写入AFQ。

C. 可配置的便签式存储器（SPM）。为解决关键资源短缺问题，AMU将L2缓存的一部分区域配置为SPM，以部分替代MSHR和物理寄存器文件（RF）的功能，因此AMQ和AFQ被放置在SPM中。此外，软件可以调整缓存与SPM区域的比例。这种设计具有两个优势：首先，L2缓存的容量（通常大于128KB）远大于MSHR和RF的容量，足以维护大量正在处理的内存访问请求。其次，SPM可用于存储数据，以减轻RF的压力。对于AMU支持的大粒度内存访问（如512B），RF没有足够容量存储响应数据，但SPM可以轻松容纳。第二，该设计与原始架构兼容：对于不使用AME的应用程序，SPM可以完全重新配置回缓存空间。这样，本文提出的AMU不会对传统应用程序产生任何性能影响。流水线的原始结构无需大幅改动，也不会引入大面积的存储和逻辑电路。

# 3 ISA 与微架构

在本节中，我们首先介绍表1所示的RISC-V AME扩展规范，使用custom-0（0001011）作为其操作码。然后我们介绍AMU的微架构。

## 3.1 ISA扩展

表1：RISCV64-AME ISA扩展规范

<table><tr><td>0000000</td><td>rs2</td><td>rs1</td><td>000</td><td>00000</td><td>0001011</td><td>ALOAD</td></tr><tr><td>0000000</td><td>rs2</td><td>rs1</td><td>001</td><td>00000</td><td>0001011</td><td>ASTORE</td></tr><tr><td>0000000</td><td>00000</td><td>00000</td><td>010</td><td>rd</td><td>0001011</td><td>GETFIN</td></tr><tr><td>0000000</td><td>00000</td><td>rs1</td><td>100</td><td>rd</td><td>0001011</td><td>ASETID</td></tr><tr><td>0000000</td><td>00000</td><td>rs1</td><td>101</td><td>rd</td><td>0001011</td><td>ACFGRD</td></tr><tr><td>0000000</td><td>rs2</td><td>rs1</td><td>110</td><td>00000</td><td>0001011</td><td>ACCFGWR</td></tr><tr><td>funct7</td><td>rs2</td><td>rs1</td><td>funct3</td><td>rd</td><td>AME</td><td></td></tr></table>

• asetid id 设置请求ID。设计独立ID设置指令的原因是RISC-V指令中只有2个源操作数。ID从1开始编号。

• aload spm_addr, mem_addr 使用设置的请求ID（最近一次asetid设置的值）发起异步加载请求，将数据从rs2指定的内存地址读取到rs1指定的SPM地址。
• astore spm_addr, mem_addr 异步存储请求指令，将数据从rs1指定的SPM地址写入rs2指定的内存地址。
• getfin id 从AFQ获取已完成请求的ID。如果没有已完成请求则返回0。
• acfgrd value, offset 读取AMU配置寄存器（表2）。
• acfgwr value, offset 写入AMU配置寄存器。

编程模型将在第4节中描述。这里我们首先关注AMU的微架构。图1展示了CPU核心中AMU逻辑的概览，该逻辑主要分布在CPU流水线和L2缓存中。

![](mineru_assets/Wang 等 - 2022 - Architecture and RISC-V ISA Extension Supporting Asynchronous and Flexible Parallel Far Memory Acces/images/f940c2de927af0c13a955a87365c2ac5b5556f643ade10a2cdb5b22d16562766.jpg)
图1：AMU微架构概览

# 3.2 流水线中的新功能

除了解码逻辑外，加载存储单元（LSU）需要将 `aload` 和 `astore` 请求直接转发至 L2 缓存。并且 `aload` 和 `astore` 将在请求写入 SPM 中的 AMQ 后提交。`getfin` 从 SPM 中的 AFQ 获取一个 ID，这与标准加载指令类似。`acfgrd` 和 `acfgwr` 也需要转发至 L2 缓存，因为 AMU 控制寄存器位于该处。对于常规的加载/存储指令，TLB 和内存访问路径应允许它们直接访问 L2 缓存中的 SPM。

# 3.3 L2缓存内部的AMU逻辑

这里我们首先介绍SPM的划分。根据AMU控制寄存器中的SPMWAY（见表2），SPM在数据阵列中占用连续的路（way），其地址由路号和组号的拼接进行编码。软件使用标准的加载/存储指令来访问SPM，并可以通过acfgwr调整其大小。此外，SPMWAY可以设置为0以保留所有缓存路。

元数据放置在SPM的开头，包括上述的两个循环队列AMQ和AFQ（见第2.3节），以及一个用于响应到达时查询的元数据表FIN_META。当CPU流水线转发的aload和astore请求到达L2缓存时，AMU将{spm_addr, mem_addr, ID, 请求类型（aload或astore）以及RWLEN中的粒度（见表2）}作为一项记录到AMQ中。FIN_META表设计用于支持来自远存储器的乱序响应，通过请求ID而非循环队列进行索引。当AMU发出请求时，处理响应所需的信息（spm地址、数据长度和请求类型）被记录到

FIN_META[请求ID]。这避免了当响应乱序到达时，新请求覆盖先前未完成请求的元数据。

表2：AMU控制寄存器

<table><tr><td>控制寄存器</td><td>描述</td></tr><tr><td>SPMWAY</td><td>SPM在数据阵列中连续占用的路数（从第0路开始）</td></tr><tr><td>AMQLEN</td><td>AMQ、AFQ和FIN_meta的长度</td></tr><tr><td>RWLEN</td><td>aload或astore访问的数据长度（需8字节对齐）</td></tr></table>

最后，我们介绍解耦的异步内存请求与响应逻辑，这些逻辑通过状态机（图1中的发送状态机和接收状态机）实现。发送状态机顺序读取AMQ中的请求项，并依次以其ID发出远内存访问请求，随后将其记录到FIN_META[请求ID]中。当远内存响应到达时，接收状态机开始工作。首先，根据响应ID查找FIN_META中的元数据。然后，如果请求类型为aload，接收状态机将响应数据写入SPM，并最终将响应ID放入AFQ。

# 4 编程模型

传统内存访问在代码层面都是串行且同步的，因此需要一种新颖的编程范式来支持AME中提供的异步内存访问。在本节中，我们首先展示使用AME进行编程的基本方法。然后，将介绍一种基于协程的敏捷编程框架CAP（用于AME编程的协程），该框架可以极大简化应用AME的代码。为便于使用，我们将AME指令封装为C/C++函数接口（见表3）。

表3：AME编程接口

<table><tr><td>指令</td><td>函数接口</td></tr><tr><td>aload</td><td>aload (int id, uintptr_t spm_addr, uintptr_t mem_addr)</td></tr><tr><td>astore</td><td>astore (int id, uintptr_t spm_addr, uintptr_t mem_addr)</td></tr><tr><td>getfin</td><td>int id = getfin()</td></tr><tr><td>acfgrd</td><td>uint64_t value = acfgrd (int offset)</td></tr><tr><td>acfgwr</td><td>void acfgwr (uint64_t value, int offset)</td></tr></table>

# 4.1 基本范式

列表1展示了AME的基本编程范式。它首先配置AMU，并执行一个无数据返回的加载操作。然后，在该请求尚未完成时处理其他工作，并根据需要使用`getfin`检查已完成的请求。完成后，可通过标准的加载/存储指令访问数据。

```c
define MAX_PARALLELISM 128
int *far_mem_to_access; // 假设位于远端内存
// AMU配置
acfgwr(MAX_PARALLELISM, AMQLLEN);
acfgwr(sizeof(int), RWLEN);
int *spm_data_area = (int *)alloc_spm_addr(sizeof(int));
int id = 1; // 分配一个请求ID
// 发起一个异步内存访问请求
load(id,spm_data_area, &far_mem_to_access);
while(id != getfin()) { /* 执行其他操作 */ }
// 通过标准的加载/存储指令访问
printf("%d\n", *spm_space);
```

```

![](mineru_assets/Wang 等 - 2022 - Architecture and RISC-V ISA Extension Supporting Asynchronous and Flexible Parallel Far Memory Acces/images/5708ae1eafc9e3c7e105c4effa2b1b717fe50c104360ed3e1fd39d26f78499ad.jpg)
列表 1：AME 的基本用法
图 2：使用 AME 发出大量请求的步骤

对于内存访问密集型程序，我们可以使用 AME 以这种方式发出大量内存访问请求：首先，将程序划分为若干部分 ❶。每个部分通常加载一个远程元素，然后对其进行计算，并重复此过程。其次，将这些加载转换为 aload 请求，批量发出这些请求，并为每个部分记录请求 ID ❷。当通过 getfin 检索到已完成的请求 ID 时，程序执行该 ID 对应部分的内存访问后计算 ❸，并在完成后继续对该部分执行 aload/astore 操作 ❹。

```c
/* 原始版本 */
for (int i = 0; i < n; ++i) L[i] ^= i;
/* 带状态机的 AME 版本 */
```

```c
#define NUM_PARTS 256
struct {
    int idx; // 该部分的当前索引
    int num_finish; // 已完成的更新次数
    int stage; // 0: 需要 aload, 1: 已完成 aload
} update[NUM_PARTS + 1]; // 状态记录结构体
// ① 划分初始化：部分 'j' (0..255) 持有 id 'j + 1' (1..256)
int *spm_addr = alloc_spm_addr (NUM_PARTS * sizeof(int));
for (int j = 0; j<NUM_PARTS; j++) {
update[j].idx = j * NUM_PARTS / n
update[j].num_finish = 0, update[j].stage = 1;
}
// ② 第一轮：利用 MLP 批量执行 aload
for (int j = 0; j<NUM_PARTS; j++) {
load(j + 1, &spm_addr[j], &L[update[j].idx++]');
// aload/astore 状态机
int remain_parts = NUM_PARTS;
while (remain_parts > 0) {
if ((j = getfin()) != 0) { // 收到一个响应
switch (update[j - 1].stage) {
case 0: // ④ 发起下一个 aload
if (update[j - 1].num_finish < n / NUM_PARTS) {
load(j, &spm_addr[j - 1], &L[update[j - 1].idx++]};
update[j - 1].stage = 1;
} else remain_parts--;
break;
case 1: // ⑧ 计算并 astore
spm_addr[j - 1] ^= update[j - 1].idx;
astore(j, &spm_addr[j - 1], &L[update[j - 1].idx]);
update[j - 1].stage = 0, update[j - 1].num_finish++;
break;
}
}
```

# 列表2：利用AME利用MLP的示例：一次更新

我们以一个顺序更新程序为例（列表2中的前两行）。该程序循环加载分配在远内存中的数组L的元素，并在异或操作后对其进行更新。我们首先通过❶将更新任务划分为NUM_PARTS个部分来修改它。每个部分的执行过程可以用一个状态机来描述：\(\pmb{\varrho}\) 发送批量加载请求，\(\otimes\) 表示一个请求完成后，计算并发送存储请求，\(\pmb{\mathfrak{o}}\) 表示存储完成并继续加载。为了支持这一想法，每个部分的状态、索引以及已完成更新的数量都需要记录在本地内存中。使用AME的状态机思想的修改内容见列表2的其余部分。

# 4.2 CAP 协程编程框架

使用上述范式（状态机）可以发出大量异步内存请求，但这需要精心设计状态机，并且对复杂程序进行大量修改。

因此，我们基于 C++20 中的协程库实现了一个敏捷编程框架 CAP。CAP 采用 AME 来实现协程的切换和调度方法（例如在 aload 和 astore 之后挂起，在 getfin 之后恢复）。并且 CAP 提供了基于地址哈希的本地锁实现，从而能够保护并发一致性。这使得使用 AME 进行修改变得更加容易，并且类似于多线程

![](mineru_assets/Wang 等 - 2022 - Architecture and RISC-V ISA Extension Supporting Asynchronous and Flexible Parallel Far Memory Acces/images/047c3c0f92b918f9e8b12d2382136d5610997c0a56ba418fa375a2c5025d4039.jpg)
图 4：模拟远端内存路径中的延迟器设计

程序，无需显式地使用步骤 \(\pmb{\varrho}\)、\(\otimes\) 和 ❹ 进行修改。程序员无需关注 ID 生命周期、getfin 和调度的细节（参见列表 3）。

```cpp
template<typename Scheduler>
coro::task<void> update (int idx, int *L, int eachNUPDATE, Scheduler &sched) {
    int *spm_addr = schedAllocator_spm_addr();
    for (int i = idx; i < idx + eachNUPDATE; ++i) {
        coAwait_load_coro(spm_addr, &L[i], sched);
        *spm_addr ^= i;
        co awaits_astore_coro(spm_addr, &L[i], sched);
    }
    sched.release_spm(spm_addr);
}

```

# 列表 3：使用 CAP 的示例更新程序

# 5 基于FPGA的原型系统

我们对NutShell[5]（一款经过流片验证的顺序流水线RISC-V CPU）进行了扩展，以支持AME。并在Xilinx ZYNQ UltraScale+ ZU19EG MPSoC 开发板上构建了基于FPGA的原型系统用于评估。该开发板在处理系统（PS）侧拥有四核ARM Cortex A53处理器，可帮助我们访问通用输入输出接口（GPIO）或监控可编程逻辑（PL）中的数据流。

我们的FPGA原型系统为实现了AME的NutShell提供了两条内存路径（图3）。它们映射到不同的地址空间，特性如下：

![](mineru_assets/Wang 等 - 2022 - Architecture and RISC-V ISA Extension Supporting Asynchronous and Flexible Parallel Far Memory Acces/images/6b1c0f21601d235f71527232ffb18f6e1d5b628aa332bebfec21f720ab12c3fa.jpg)
图3：基于FPGA的原型系统上的内存路径

本地内存路径 $\pmb{①}$（图3中） 我们使用ZYNQ PS侧的AXI_HP接口。该HP端口仅支持64个并发请求，但其内存控制器为硬逻辑，具有高时钟频率。因此，路径①符合低延迟、低并发度的本地内存特性。

图 3 中的模拟远端内存路径 \(\pmb{\varrho}\) 我们使用外推的 DDR4 内存作为远端内存。实例化了一个软内存接口生成器（MIG）作为内存控制器，其 AXI AxID 宽度为 32 位，支持高并发。此外，远端内存响应将经过模块 Delayer，该模块为 AXI B 和 R 通道中所有重叠的响应添加相等且可调的延迟。图 4 描述了 Delayer 的结构和访问方式。它包含一个具有 256 个条目（我们系统中最大并发请求数）的 AXI FIFO，用于临时保存响应，并通过 xUSER 信号记录每个响应进入 FIFO 时的时间戳，以精确控制为其添加的延迟。模块 "GateKeeper" 负责在 FIFO 出口处通过控制 AXI 的握手信号，释放等待时间足够的请求。此外，我们将寄存器 "Delay"（我们设置的延迟值）作为 AXI GPIO，并将其映射到 PS 端 ARM 内核的地址空间中。因此，ARM 内核上的软件可以通过访问该地址随时调整此值。

为了从硬件实时观察在途请求的数量，我们在 AMU 中添加了一个计数器，该计数器记录已发送与已接收请求数量的差值。我们还将此计数器设置为 AXI GPIO，并将其映射到 ARM 核的地址空间以便观察。

<table><tr><td>项目</td><td>原始</td><td>AME</td><td>+/-</td><td>项目</td><td>原始</td><td>AME</td><td>+/-</td></tr><tr><td>LUT</td><td>14040</td><td>16130</td><td>+14.9%</td><td>BRAM + URAM</td><td>7.5+12</td><td>6+14</td><td>+2.5%</td></tr><tr><td>FF</td><td>12073</td><td>14656</td><td>+21.4%</td><td>LUTRAM</td><td>539</td><td>587</td><td>+8.9%</td></tr></table>

注意：工具：Vivado 2019.2，core_clk 为 200MHz，uncore_clk 为 100MHz。

# 表 4：实现后资源利用率对比

表 4 展示了在 FPGA 项目中实现 AME 前后 SoC 层级上的资源利用率对比。可以看出，AME 对原始 SoC 的影响很小，尤其是在存储方面，这是由于复用了 L2 缓存中的 SPM。

# 6 评估

# 6.1 基准测试

我们使用6个基准测试来验证AME在不同内存访问延迟场景下在我们原型系统上的性能。描述和工作负载如下：

随机访问 (GUPS) 我们采用HPCC随机访问基准测试的单节点版本[22]。它持续随机选择内存中表的元素进行更新。该程序以GUPS（每秒十亿次更新）作为性能评估指标。该表分配在远内存中，大小为256MB（总共32M个uint64_t元素），更新次数为$2^{20}$。

顺序访问 (SA) SA是从GUPS修改而来的顺序内存访问基准测试。它顺序更新表中的元素，而非随机访问。工作负载与GUPS相同。

哈希连接 (HJ) 我们采用ETH系统组的多核哈希连接基准测试[9]。它首先基于包含一组元组的关系构建哈希表，然后使用另一个关系进行检测。HJ将哈希表和关系分配在远内存中，每个关系随机包含512,000个元组（7.812MB）。性能以每秒处理的元组数量来衡量。

整数排序（IS） IS 是 NAS 并行基准测试套件（NPB）v3.3.0[8]中的一项并行性能基准测试。它采用基数排序算法，首先使用中等大小的桶对元素的高位进行预排序，然后对所有元素进行排序以减少随机访问。我们选择工作负载 W：待排序数组大小为 $2^{20}$（8MB，uint64_t 类型），桶大小为 $2^{10}$，最大元素值为 $2^{16}$，其中数组放置在远内存中，桶放置在本地内存中。性能通过其运行时间来衡量。

带手递手链表的哈希表（HL） 我们采用来自 ASYCLIB[13]的链式哈希表，这是一种由锁保护的并发数据结构。每个哈希表桶指向一个手递手锁链表[15]，其中包含冲突项。哈希表分配在本地内存中，包含 32768 个桶，而链表分配在远内存中，包含 102400 个键（2MB）。HL 启动 256 个协程，每个协程执行 100 个随机键操作，其中 $70\%$ 为查找操作，$30\%$ 为插入操作。性能以每秒操作数（\(\mathrm{op/s}\)）来衡量。

图(A)展示了所有基准测试在最大并发数为256时的性能对比。\(x\) 轴表示模拟延迟（微秒），y 轴表示归一化后的性能值。柱状图上的标签表示在此特定延迟下AME相对于原始方案的加速比。特别地，图(A).g中不同柱状图表示AME在不同粒度的aload和astore操作下的性能表现。
![](mineru_assets/Wang 等 - 2022 - Architecture and RISC-V ISA Extension Supporting Asynchronous and Flexible Parallel Far Memory Acces/images/a67b02154a5cd8bc90a119077879ad6e6caa4bbd2a042c6807296eefc1e13d80.jpg)
图(B)展示了当GUPS在最大并发数为256且额外模拟延迟为2微秒时，飞行中请求数量随时间的变化情况。
图(C)展示了GUPS在不同最大并发数设置下的性能表现。

# 图5：评估结果

Graph500 (G500)[23] 我们使用Kronecker算法构建了一个包含$2^{16}$个节点（16MB）的图，其中每个节点的度数为16。G500使用顺序列表作为其数据结构构建了8棵BFS树。该图和顶点列表被分配在远端内存中。我们通过其运行时间来衡量性能。

# 6.2 评估设置

我们使用基于FPGA的原型系统来模拟一个2GHz处理器面对不同远端内存访问延迟时的性能。在我们的系统中，NutShell运行在200MHz，其时钟周期是2GHz的10倍。两条AXI4内存路径的频率均为100MHz，这参考了一些真实处理器中最后一级缓存及外部部分（非核心部分）的频率降至核心频率一半的情况。

在我们的实验中，模拟远端内存引入的额外延迟在0到10,000个时钟周期之间，这相当于一个 2GHz 处理器面临 0 到 \(10 \mu s\) 的情况。在实际应用中，NVMM 的访问延迟约为 \(0.5 \mu s\)，而具有网络延迟或更远距离的机器可能达到 \(10 \mu s\)。下图中 \(x\) 轴显示的模拟额外延迟均已转换为该 2GHz 处理器的对应值。

为了进行比较，我们将原始版本（标记为"Origin"）和实现了AME的NutShell（标记为"AME"）部署到我们的基于FPGA的原型系统中。为了在更真实的运行时环境中进行模拟，所有基准测试均在Debian 11上运行。

# 6.3 结果

为清晰起见，我们将原始 NutShell 在每个基准测试中无额外延迟的性能归一化为 1。

**基本情况。** 我们首先关注纯远内存访问性能，其中 SA 和 GUPS 分别侧重于随机访问和顺序访问。在 AME 上，SA 的性能不如采用缓存的原始设计，因为当粒度为 8B 时，缓存利用了局部性。但大粒度访问（例如一次 512KB）可以更充分地利用带宽，因此当延迟大于 $1 \mu s$ 时，AME 可以将性能提升 ${ \sim } 6 0 \times$（图 5 (A).g）。至于随机访问，图 5 (A).f 表明，即使在无额外延迟的情况下，在 8B 小粒度下使用 AME 也比传统方法更灵活高效，并且在有额外延迟时性能可提升 ${ \sim } 9 \times$。

**AME 的并发性。** 支持 AME 的应用程序可以维持比传统架构多得多的请求，如图 5 (B) 所示，其中平均在途请求数达到 238。更大的内存访问并发性可以显著提升性能（见图 5 (C)）。

实用基准测试。仅需瞥一眼图5（A）即可发现，使用AME的应用程序对延迟变化的敏感度较低。G500展示了AME在图计算上的显著加速效果，这类计算拥有大数据集并包含海量内存访问。HL表明AME能够通过异步内存访问提升并发数据结构的吞吐量。凭借可变粒度，即使是像IS这样包含大量顺序访问的应用程序，AME也能帮助提升性能。

# 7 结论与未来工作

本文提出了一项研究，支持具有可变粒度的显式异步内存访问，以隐藏远内存的延迟并提升MLP。我们提出了异步内存访问单元（AMU）及其ISA扩展AME。评估结果表明，采用异步编程范式后，内存密集型应用能够更充分地利用远内存的能力。

本工作仅提供了实现异步内存访问的基本指令与结构。在操作系统和编译器层面，仍需开展更多工作以适配实际应用。此外，若远内存子系统支持更丰富的内存语义[11]，该异步设计可轻松扩展以支持更多内存扩展功能，例如复杂访问模式与内存内处理（PIM）机制。

# 参考文献

[1] 2017. OpenCAPI 规范. http://opencapi.org [在线; 访问日期：2022年2月].
[2] 2018. Compute Express Link. https://www.computeexpresslink.org/ [在线; 访问日期：2022年2月].
[3] 2018. Gen-Z 规范. https://genzconsortium.org/specifications [在线; 访问日期：2022年2月].
[4] 2019. 英特尔傲腾持久内存. https://www.intel.com/content/www/us/en/architecture-and-technology/optane-dc-persistent-memory.html [在线; 访问日期：2022年2月].
[5] 2020. NutShell：大学开源芯片项目. https://github.com/OSCPU/NutShell [在线; 访问日期：2022年2月].
[6] Mikhail Asiatici 和 Paolo Ienne. 2019. 别再为缓存缺失率哭泣：在FPGA中高效处理数千个未命中请求. 载于《2019年ACM/SIGDA国际现场可编程门阵列研讨会论文集》. 第310–319页.
[7] Jonathan Bachrach, Huy Vo, Brian Richards, Yunsup Lee, Andrew Waterman, Rimas Avižienis, John Wawrzynek 和 Krste Asanović. 2012. Chisel：在Scala嵌入式语言中构建硬件. 载于《2012年DAC设计自动化会议》. IEEE, 第1212–1221页.

[8] David Bailey, Tim Harris, William Saphir, Rob Van Der Wijngaart, Alex Woo, and Maurice Yarrow. 1995. The NAS parallel benchmarks 2.0. Technical Report. Technical Report NAS-95-020, NASA Ames Research Center.

[9] Cagri Balkesen, Jens Teubner, Gustavo Alonso, and M Tamer Özsu. 2013. Mainmemory hash joins on multi-core CPUs: Tuning to the underlying hardware. In 2013 IEEE 29th International Conference on Data Engineering (ICDE). IEEE, 362–373.

[10] Trevor E Carlson, Wim Heirman, Osman Allam, Stefanos Kaxiras, and Lieven Eeckhout. 2015. The load slice core microarchitecture. In 2015 ACM/IEEE 42nd Annual International Symposium on Computer Architecture (ISCA). IEEE, 272–284.

[11] Li-Cheng Chen, Ming-Yu Chen, Yuan Ruan, Yong-Bing Huang, Ze-Han Cui, Tian-Yue Lu, and Yun-Gang Bao. 2014. MIMS: Towards a Message Interface Based Memory System. Journal of Computer Science and Technology 29, 2 (March 2014), 255–272. https://doi.org/10.1007/s11390-014-1428-7

[12] Shimin Chen, Anastassia Ailamaki, Phillip B Gibbons, and Todd C Mowry. 2007. Improving hash join performance through prefetching. ACM Transactions on Database Systems (TODS) 32, 3 (2007), 17–es.

[13] Tudor David, Rachid Guerraoui, 和 Vasileios Trigonakis. 2015. 异步并发：扩展并发搜索数据结构的秘诀. ACM SIGARCH 计算机体系结构新闻 43, 1 (2015), 631–644.
[14] Yongjun He, Jiacheng Lu, 和 Tianzheng Wang. 2020. CoroBase：面向协程的主存数据库引擎. VLDB 捐赠会议论文集 14, 3 (2020), 431–444.

[15] Maurice Herlihy 和 Nir Shavit。2012 年。《多处理器编程的艺术》，修订第一版。Morgan Kaufmann 出版社。

[16] Christopher Jonathan、Umar Farooq Minhas、James Hunter、Justin Levandoski 和 Gor Nishanov。2018 年。《利用协程攻克“杀手级纳秒”》。VLDB 基金会会刊 11 卷，第 11 期（2018 年），第 1702–1714 页。

[17] Vladimir Kiriansky、Haoran Xu、Martin Rinard 和 Saman Amarasinghe。2018 年。《Cimple：指令级与内存级并行性——一种用于发掘 ILP 和 MLP 的领域特定语言》。载于《第 27 届并行架构与编译技术国际会议论文集》，第 1–16 页。

[18] Onur Kocberber、Babak Falsafi 和 Boris Grot。2015 年。《异步内存访问链式化》。VLDB 基金会会刊 9 卷，第 4 期（2015 年），第 252–263 页。

[19] Kartik Lakshminarasimhan、Ajeya Naithani、Josué Feliu 和 Lieven Eeckhout。2020 年。《前向切片核心微架构》。载于《ACM 并行架构与编译技术国际会议论文集》（美国佐治亚州亚特兰大市，虚拟会议）（PACT '20）。美国纽约州纽约市：计算机协会，第 361–372 页。https://doi.org/10.1145/3410463.3414629

[20] J. Laudon, A. Gupta, and M. Horowitz. 1994. Interleaving: A Multithreading Technique Targeting Multiprocessors and Workstations. In International Conference on Architectural Support for Programming Languages & Operating Systems.

[21] Huaicheng Li, Daniel S Berger, Stanko Novakovic, Lisa Hsu, Dan Ernst, Pantea Zardoshti, Monish Shah, Ishwar Agarwal, Mark Hill, Marcus Fontoura, et al. 2022. First-generation Memory Disaggregation for Cloud Platforms. arXiv preprint arXiv:2203.00241 (2022).

[22] Piotr R Luszczek, David H Bailey, Jack J Dongarra, Jeremy Kepner, Robert F Lucas, Rolf Rabenseifner, and Daisuke Takahashi. 2006. The HPC Challenge (HPCC) benchmark suite. In Proceedings of the 2006 ACM/IEEE conference on Supercomputing, Vol. 213. 1188455–1188677.

[23] Richard C Murphy, Kyle B Wheeler, Brian W Barrett, and James A Ang. 2010. Introducing the graph 500. Cray Users Group (CUG) 19 (2010), 45–74.

[24] Christian Pinto, Dimitris Syrivelis, Michele Gazzetti, Panos Koutsovasilis, Andrea Reale, Kostas Katrinis, 和 H. Peter Hofstee. 2020. ThymesisFlow：一种用于机架级内存解耦的软件定义、硬件/软件协同设计的互连栈. 载于《2020年第53届IEEE/ACM国际微架构研讨会（MICRO）》. 第868–880页. https://doi.org/10.1109/MICRO50266.2020.00075
[25] Michael Schwarz, Moritz Lipp, Daniel Moghimi, Jo Van Bulck, Julian Stecklina, Thomas Prescher, 和 Daniel Gruss. 2019. ZombieLoad：跨特权边界数据采样. 载于《2019年ACM SIGSAC计算机与通信安全会议论文集》. 第753–768页.
[26] James Tuck, Luis Ceze, 和 Josep Torrellas. 2006. 面向高内存级并行性的可扩展缓存未命中处理. 载于《2006年第39届IEEE/ACM国际微架构研讨会（MICRO'06）》. IEEE, 第409–422页.
[27] Luming Wang, Xu Zhang, Tianyue Lu, 和 Mingyu Chen. 2022. 通用处理器的异步内存访问单元. 《BenchCouncil基准测试、标准与评估汇刊》第2卷第2期（2022年），第100061页. https://doi.org/10.1016/j.tbench.2022.100061
