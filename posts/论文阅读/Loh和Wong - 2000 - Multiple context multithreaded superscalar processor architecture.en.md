---
title: 论文阅读：Multiple context multithreaded superscalar processor architecture
date: 2026-04-27
tags:
- 论文阅读
---

# Abstract

Superscalar architecture is becoming the norm in today's high performance microprocessor design. However, achievable instruction level parallelism in programs limits the scalability of such architectures. In this paper, we introduce the Multiple Context Multithreaded Superscalar Processor (MCMS), which is an extension of conventional superscalar processor architecture to support multithreading. This is motivated by the enormous potential instruction level parallelism present in multithreaded programs. A hardware implementation of multithreaded constructs is also proposed. Results from trace-driven simulation show that with the MCMS, instruction level parallelism is indeed increased signi®cantly. A MCMS processor with four hardware contexts can produce a speedup of up to 2.5 times over superscalar processor with similar hardware resources. We found that the primary limitation shifts from data dependencies in the superscalar processor to resource contentions in MCMS. $^ { © }$ 2000 Elsevier Science B.V. All rights reserved.

Keywords: Superscalar processor; Multithreading; Multiple context; Simulation; Instruction level parallelism

# 1. Introduction

With advancements in semiconductor technology, we can pack more and more transistors into a processor. This allows more sophisticated tech-

niques such as multiple issue, out-of-order issue, speculative execution and register renaming to be implemented in hardware. In addition, multiple execution units and larger on-chip caches are now possible.

Most of the current high performance microprocessors make use of the above superscalar (SS) techniques. Superscalar architecture enables multiple instructions to be fetched, decoded and

executed concurrently in one cycle. In simple words, it widens the processor's execution pipeline. A wider pipeline can increase the instruction throughput. However, we have to extract enough instruction level parallelism from the programs to fully utilise the wider execution pipeline.

Dierent methods of increasing the instruction level parallelism have been explored. Both hardware and software techniques have been used. Hardware techniques include speculative execution, register renaming and out-of-order issue with instructions lookahead. Software techniques are usually incorporated into the compilers as optimisations. The instructions in a program are usually rearranged in hope to increase instruction level parallelism. Some of the common approaches are trace scheduling, loop unrolling, software pipelining, optimal register allocation algorithms and static branch prediction.

In this paper, we will investigate the feasibility of increasing instruction level parallelism using multithreading to better exploit the resources of a superscalar processor. As a programming paradigm, multithreaded programming is now supported at the kernel level by nearly every modern operating system. Instructions from dierent execution threads of a multithreaded application are largely independent. This can be exploited to increase the instruction level parallelism if instructions from multiple threads are allowed to be executed concurrently. Allowing this will require the processor to support multiple contexts. With this motivation, we introduce Multiple Context Multithreaded Superscalar (MCMS) processor architecture. The implementation of a hardware mechanism for ecient execution of multithreaded constructs is also proposed.

Section 2 describes some of the current work done on hardware-supported multithreading at the processor level. This will set a background to the work we have done. The design of the MCMS architecture and some implementation details will

be described in Section 3. The simulation technique used in our study will be brie¯y described in Section 4. Section 5 will presents the simulation results obtained together with some discussions. Finally, Section 6 draws the conclusion and summarises our ®ndings.

# 2. Multithreading at the processor level

Multithreading has been implemented in multiprocessor systems for two primary reasons. First it gives the programmer a ``lightweight'' mechanism to work with shared memory multiprocessors directly. Second, it is a mean of hiding the long latencies such as remote memory access [3]. The latencies range from tens to hundreds of processor cycles. Two common scheduling methods are the blocked and interleaved schemes. In the blocked scheme, a context switch occurs when a thread encounters a long latency operation. The interleaved scheme switches between contexts on a cycle-by-cycle basis. Each context takes turn to issue instructions. Some examples are APRIL [1], HEP [7], MASA [13] and TERA [2].

The blocked scheme does not help to reduce pipeline stall because it does not exploit the parallelism from multiple threads. The interleaved scheme can exploit the parallelism but there must be enough threads to fully utilise the pipeline. Most of the implementations have a strict interleaving scheme where a thread cannot be skipped even if it has no instruction to issue. Usually memory tags are used to enforce thread synchronisation in these multiprocessors.

Hirata et al. [8] proposed a multithreaded architecture to improve parallel instructions issue. Every thread has its own instruction decoder and instruction queue. Every thread may issue 1 instruction in each cycle. Simulation of a highly parallel ray-tracing program produced speedups of 3.72 and 5.79 for processors with four and eight

threads, respectively, relative to a single threaded processor. All cache accesses were assumed to be hits. Therefore, inter thread cache thrashing was not accounted for.

Simultaneous multithreading [17] was proposed to maximise the instruction issue slots of a superscalar processor. It exploits the instruction level parallelism obtained from several independent threads of execution. Both vertical and horizontal wastes of the instruction issue slots are minimised by allowing instructions from multiple threads to be issued in each cycle. In Ref. [18], Tullsen et al. showed that simultaneous multithreading can be made possible without adding undue complexity to a conventional superscalar processor design. We have adopted some of their approaches in MCMS but it diers from SMT in the details of the implementation, especially in the synchronisation mechanism.

Lo et al. [10] has reported almost similar speedups in SMT. They use a processor con®guration with huge amount of resources; a 4 ported data cache, 4 ALU units and 4 ¯oating point units. Due to these assumptions, they have missed to identify the occurrence of resource contention. Tullsen et al. [18] found that the limiting factor in SMT is the fetch throughput.

Hily and Seznec [9] investigate the contention on second level cache in SMT. They prove that ignoring second level cache contention may lead to over-estimating the performance of SMT. They also show that memory constraints may limits the number of threads. Their simulations assume perfect branch prediction and in®nite number of single cycle functional units.

Another similar work is the performance study of multithreaded superscalar processor done by Gulati and Bagherzadeh [6]. They simulated a processor con®guration with limited resources and reported a speedup of $20 \mathrm { - } 5 5 \%$ across a wide range of benchmarks. The data cache was only $8 \mathrm { ~ K ~ }$ in size and was single ported. Moreover, the register

®le of size 128 is shared among all the executing thread. Therefore, resource contentions and memory requirements could seriously limit any performance gain.

Most of these works have left out the implementation of thread synchronisation mechanism even though they do mention that ecient synchronisation is possible. Also, the number of software threads used is always equal to or less than the number of contexts of the processor architecture. In reality, the number of software threads may grow to exceed the number of supported hardware contexts.

The simulations performed on SMT and by Gulati used dierent numbers of software threads to test the eect of varying number of concurrent executing threads. We feel that the comparison is not very fair. Even if the same programs with the same data sets are used, the behaviour will still be dierent because the work is partitioned dierently. For example, the memory requirement for a program that is partitioned into two threads is de®nitely dierent from partitioning the same program using four or eight threads. We hope to address these and other issues with our work.

# 3. MCMS architecture

We will use a generic conventional superscalar processor architecture as the basis for our MCMS architecture. Extensions will be made to provide support for multiple contexts and multithreading. We wanted to make minimal extensions and so reduce any added complexity whenever possible. Fig. 1 shows the organisation of the MCMS architecture.

# 3.1. Multiple context

Multiple contexts are required to allow instructions for dierent threads to co-exist and

![](mineru_assets/Loh和Wong - 2000 - Multiple context multithreaded superscalar processor architecture/images/02c8423f82a405fbabc93eb6e9ba44106f6dbb1c01a77ade903867e2aa6c8e72.jpg)
Fig. 1. Organisation of MCMS architecture.

execute concurrently in the processor. In order to support multiple contexts, we have to ®rst replicate the resources that are context dependent. These include the PSR, PC and register ®les. In today's superscalar processors, these account for about $5- 1 0 \%$ of the overall die area. Every instructions fetched must also be augmented with a context id so that we can identify which thread an instruction is from. The context id is used to determine which PC to change when there is a change in control ¯ow and which register ®le to access and update.

Each context needs to keep some status information. We will augment them into the PSR. They are listed and described in Table 1. These ¯ags are useful in guiding the instruction fetch scheduling.

In order not to complicate the instruction fetch logic, we restricted the MCMS to fetch instructions from only one thread in a cycle. If we allow instructions from several threads to be fetched in the same cycle from a single instruction cache, the

instruction cache will have to be made multi-ported. Furthermore, a lockup-free instruction cache is required in MCMS. A thread that caused an instruction cache miss will have to wait until the cache miss has been re®lled. However, other threads that do not face an instruction cache miss

Table 1 Context status information in PSR

<table><tr><td>PSR flags</td><td>Status</td><td>Description</td></tr><tr><td rowspan="2">Free context</td><td>Set</td><td>The context is free</td></tr><tr><td>Reset</td><td>The context is used</td></tr><tr><td rowspan="2">I-cache miss</td><td>Set</td><td>Instruction cache miss</td></tr><tr><td>Reset</td><td>No instruction cache miss</td></tr><tr><td rowspan="2">Suspend</td><td>Set</td><td>Instruction fetch is suspended due to mutex lock or synchronisation</td></tr><tr><td>Reset</td><td>Instruction fetch is not suspended</td></tr><tr><td rowspan="2">Speculation</td><td>Set</td><td>Instruction fetch is on speculation due to branch prediction</td></tr><tr><td>Reset</td><td>Not on speculation</td></tr></table>

should be allowed to continue fetching instructions from the instruction cache. A lockup-free instruction cache will not delay the instruction fetch of a thread if another thread has caused an instruction cache miss.

Unlike a superscalar processor, which has only 1 PC, the MCMS has multiple PCs. Therefore, we need a scheduling mechanism to select a thread to fetch from in each cycle. We used the context status to assist the scheduling. Only occupied contexts are included in the selection and contexts with I-cache miss and suspend ¯ags set cannot be selected. First, the scheduler tries to ®nd a context with all the ¯ags listed in Table 1 cleared. If there is more than one candidate, they will be selected in a round robin manner to get a mixed of instructions. If none of the context have all the ¯ags cleared then contexts with only the speculation ¯ag set is chosen. Similarly, a round robin method is used when there is more than one candidate.

The decode unit performs instructions decoding, register renaming and result commit. The decode unit has an instruction width that is equal to that of the fetch unit so that all the instructions fetched in 1 cycle can be decoded in 1 cycle. Reorder buers [14] was used as the register renaming mechanism. Since we have multiple register ®les, we used multiple reorder buers, one for each register ®le. A branch history buer with 2-bit history is used to perform branch prediction. All the executing threads share the branch history buer.

The executing threads also share the instruction window and execution units. Decoded instructions will be placed in the instruction window. The instruction window could be made of a single instruction buer as in the UltraSparc [16,19] or several instruction queues as in the MIPS R10000 [21]. Instructions from dierent threads will be interspersed in the shared buer or queues. Instruction issue only needs to consider data dependencies. In particular, the context id does not

play a role in instruction issue. In other words, instructions from dierent threads can be issued in the same cycle. The context id is only used to determine which register ®le or reorder buer to access.

The data cache is also shared among all the executing threads. The multithreaded applications are assumed to execute in the same memory address space. If we use multiple data caches, one for each context, some form of cache coherence control will be required thereby increasing the complexity. Therefore, we have chosen to use a single shared data cache.

# 3.2. Hardware implementation of multithreaded constructs

We have identi®ed ®ve primitive multithreaded constructs. We assume that these are added into the instruction set architecture of MCMS. Thread create increases the number of executing threads while thread terminate decreases the number of executing threads. Mutex lock and mutex unlock can be used to create a critical section. This provides atomic modi®cations to the shared memory. Barrier synchronisation is a point where the threads can exchange information.

A thread unit is added into the MCMS architecture to execute all the above instructions. Three tables are used to store the status of mutex locks and barrier synchronisation. The lock table and sync table holds the status of mutex locks and barrier synchronisation respectively. The number of entries in the lock table and sync table corresponds to the number of supported hardware mutex locks and barrier respectively. The wait-for table records the lock or barrier that a context is currently waiting for. One entry is allocated to one context. This is sucient as one context can only wait for one mutex lock or one barrier at a time (see Table 2).

Table 2 Thread unit table's ®eld

<table><tr><td>Table</td><td>Field</td><td>Description</td></tr><tr><td>Lock</td><td>Lock/unlock</td><td>Set if the lock is used and clear if it is not</td></tr><tr><td rowspan="2">Sync</td><td>Max</td><td>Number of threads that will synchronise at this barrier</td></tr><tr><td>Remaining</td><td>Remaining number of threads that will synchronise at this barrier</td></tr><tr><td rowspan="2">Wait-for</td><td>Lock/sync</td><td>Waiting for a lock or barrier</td></tr><tr><td>Lock id/sync id</td><td>The id of the lock or sync the thread is waiting for</td></tr></table>

The decode unit will set the suspend ¯ag of the thread's PSR when a mutex lock or barrier synchronisation instruction is decoded. It also purges all the already fetched instructions beyond the mutex lock or barrier synchronisation instruction. Then, the PC is set to point to the next instruction. After the suspend ¯ag is set, no further instruction will be fetched from that thread. This ensures that no instruction beyond the mutex lock or barrier synchronisation is executed before the lock is successfully acquired or the barrier synchronisation has completed.

All the decoded multithreaded instructions will be stored in an instruction queue. Such an instruction can only be executed when its reorder buer entry reaches the head. This ensures that all previous instructions from the thread have already completed. This is to enforce correctness. Early execution of mutex lock instructions does not violate correctness but requires some exception handling. Therefore, we chose to avoid early execution of mutex lock instructions.

When a thread create instruction is executed, a new thread is created by allocating a free hardware context to it. The PSR and the PC of the selected context will be initialised. The new thread will then participate in the fetch scheduling for instruction fetch. When a thread terminate instruction is

executed, the resources of the context it is occupying is freed. Setting the free ¯ag in the PSR of the terminating thread does this.

For mutex lock, the decode unit would have set the suspend ¯ag of the PSR when the instruction is decoded. When a mutex lock is executed, we ®rst check the entry of the lock id in the lock table. If the status is clear, the lock is available. In this case, set the status of the entry in the lock table and clear the suspend ¯ag in its context's PSR. This will allow the thread to resume instruction fetch. If the status of the lock is already set then the lock has been acquired by another thread. In this case, the lock id is placed in its entry of the wait-for table. It will have to wait until the current owner of the lock releases the lock.

When a mutex unlock instruction is encountered, all the entries of the wait-for table are checked to see if there is any thread waiting for the lock. If a thread waiting for the lock is found, the suspend ¯ag of PSR and the wait-for entry of the waiting thread are cleared. Otherwise, the lock is released by resetting the status of the lock in the lock table.

For barrier synchronisation, the decode unit sets the suspend ¯ag of the PSR when the instruction is decoded. The entry of the sync id in the sync table is checked. If the ``max'' and ``remaining'' ®eld is 0, this is the ®rst thread that reaches the barrier synchronisation point. Both ®elds in the entry will have to be initialised to the number of threads to synchronise with. Then, the number in the ``remaining'' ®eld is decreased by 1 and the sync id is put into the entry of the context in the wait-for table. If the ``remaining'' ®eld is non zero, it is decremented and the sync id is stored into the corresponding entry in the wait-for table. When the number in the ``remaining'' ®eld becomes 0 after a decrement, the barrier synchronisation is complete. For every thread that is waiting for the sync id, the wait-for entry and the suspend ¯ag of the corresponding PSR are cleared. Also, the

``max'' ®eld is decreased by 1 for every thread that has been resumed.

# 3.3. Context switching

Context switching is required when the number of executing threads exceeds the number of available hardware contexts. As the number of hardware contexts limits the number of concurrent executing threads, additional threads have to be swapped out of the processor. Context switching is the process of replacing a thread in a context with another thread.

We need some criteria to determine when should a thread be swapped out. We have selected two criteria. The ®rst one is when a thread fails to acquire a mutex lock and the second is when a thread is waiting for the completion of a barrier synchronisation. The reason for choosing them is that no instruction has to be purged. In these cases, all previous instructions have completed and the following instructions have not been fetched yet. Furthermore, the thread cannot continue execution.

When a context switch occurs, we have to save the states of the thread to be swapped out and restore the states of the thread to be swapped in. The states include the PSR, PC, register ®le and its wait-for table entry. To reduce the overhead of saving and restoring the context's status, we added another ¯ag, ``swap-out'' ¯ag to the PSR. This ¯ag is set when a thread is to be swapped out. A context with its swap-out ¯ag set can be swapped out whenever the context is needed by another thread. Otherwise, it is allowed to continue occupying the context. If the thread can be resumed before it is swapped out, we do not have to save and restore its state.

If there is no free context when a thread is created, the newly created thread will have to be swapped out. A context will be freed when a thread terminates. After a context becomes free,

we can swap in a thread that is waiting to resume execution. To ®nd a thread that can resume execution, we will ®rst restore and check the wait-for entries of the swapped out threads. If a thread that can resume execution is found, its complete state will be restored and its execution subsequently resumed.

When a thread meets the criteria to be swapped out, its swap-out ¯ag is set. If there is a thread waiting to be swapped in, a context switch will occur. Otherwise, the thread is allowed continue occupying the context. After a mutex unlock or a barrier synchronisation completes, one or more swapped out threads may be allowed to continue execution if there are free contexts available.

# 4. Simulation technique

We will use simulations to quantify the performance of MCMS architecture. The bene®ts of simulations are the ¯exibility of recon®guring the processor's parameters and allowing for detailed collection of statistical information. We extended the SPATS simulator [11] to simulate MCMS architecture. SPATS is an accurate and ¯exible trace-driven cycle-by-cycle instruction level simulator for superscalar processors. The extensions are generating instruction traces for multithreaded applications and simulating the behaviour of MCMS architecture.

An instruction trace is the sequence of all the executed instructions when the application is executed. We used the instrumentation tool, ATOM [5,12] in Digital Unix to extract the instruction trace. For a sequential program, we will get one sequence of instructions in the trace. For multithreaded applications, we will generate one instruction trace for each execution thread. With multiple instruction traces, each thread has the ¯exibility to progress at its own pace during the simulation. The only exception is enforcement of

synchronisation constraint. We have written a simple user level multithreaded library, Uthread, to help extract the instruction traces of multithreaded applications using ATOM.

We used the benchmark programs from the Splash [15] and Splash 2 [20] as the workloads for the simulations. These are shared memory parallel applications that can be multithreaded. The programs were compiled with the Digital C compiler with the optimisation ¯ags ` $\mathbf { \bar { \Psi } } - O 5 ^ { \circ }$ and `` fast''. Two versions of the programs are used, the sequential and multithreaded versions. The sequential version does not use any multithreading facilities and executes as a single threaded program. The Uthread library is used for the multithreaded version instead of the usual system

multithreaded library. This is to allow for instruction trace generation using ATOM.

In order to compare the performance of MCMS with a superscalar architecture, we will ®rst simulate a superscalar processor. The con®guration for the superscalar architecture will be abbreviated as SS. We surveyed the current superscalar processors to identify a realistic processor con®guration to simulate. Table 3 shows a comparison of the simulated con®gurations with the MIPS R10000 [21], Ultra Sparc I [19] and Alpha 21164 [4]. In addition, a comparison of the instruction execution latencies is given in Table 4.

The cache con®gurations and latencies are shown in Table 5. The least recently used replacement policy was used for cache re®ll. A

Table 3 Comparisons of processors con®guration

<table><tr><td></td><td>Simulated</td><td>MIPS R10000</td><td>Ultra Sparc I</td><td>Alpha 21164</td></tr><tr><td>Instruction fetch with Functional units</td><td>4</td><td>4</td><td>4</td><td>4</td></tr><tr><td>Memory</td><td>2</td><td>1</td><td>1</td><td>Use integer</td></tr><tr><td>Integer</td><td>2</td><td>2</td><td>2</td><td>2</td></tr><tr><td>Integer multiply</td><td>1</td><td>1</td><td>Use integer</td><td>Use integer</td></tr><tr><td>Floating point</td><td>2</td><td>2</td><td>2</td><td>2</td></tr><tr><td>FP divide/sqrt</td><td>1</td><td>1</td><td>1</td><td>1</td></tr><tr><td colspan="5">Memory configuration</td></tr><tr><td>Instruction cache</td><td>32 K</td><td>32 K</td><td>16 K</td><td>8 K</td></tr><tr><td>Data cache</td><td>32 K</td><td>32 K</td><td>16 K</td><td>8 K</td></tr><tr><td>Second level cache</td><td>4 M</td><td>512 K - 16 M</td><td>512 K - 4 M</td><td>96 K (int)
1-64 M (ext)</td></tr><tr><td rowspan="2">TLB</td><td>64 entry (instr)</td><td>64 entry (shared)</td><td>64 entry (instr))</td><td>48 entry (instr)</td></tr><tr><td>64 entry (data)</td><td></td><td>64 entry (data)</td><td>64 entry (data)</td></tr><tr><td>Page size</td><td>64 K</td><td>4 K -16 M</td><td>8 K, 64 K, 512 K, 4 M</td><td>8 K, 64 K, 512 K, 4 M</td></tr><tr><td colspan="5">Instruction queue</td></tr><tr><td></td><td>Int: 16 entry</td><td>Int: 16 entry</td><td>Central buffer of 12 entry</td><td>2 buffer (slots) of 4
entry each</td></tr><tr><td></td><td>Fp: 16 entry</td><td>Fp: 16 entry</td><td></td><td></td></tr><tr><td></td><td>Mem: 16 entry</td><td>Mem: 16 entry</td><td></td><td></td></tr><tr><td colspan="5">Branch prediction</td></tr><tr><td>2-bit branch target buffer</td><td>2048 entries</td><td>512 entries</td><td>2048 entries</td><td>2048 entries</td></tr></table>

Table 4 Comparisons of instruction execution latencies

<table><tr><td></td><td>Simulated</td><td>MIPS R10000</td><td>Ultra Sparc</td><td>Alpha 21164</td></tr><tr><td rowspan="2">Integer multiply</td><td>6 (single)</td><td>6 (single)</td><td>5 (single)</td><td>8 (single)</td></tr><tr><td>10 (double)</td><td>10 (double)</td><td>10 (double)</td><td>14 (double)</td></tr><tr><td>Other integer</td><td>1</td><td>1</td><td>1</td><td>1</td></tr><tr><td rowspan="2">Fp divide</td><td>14 (single)</td><td>14 (single)</td><td>12 (single)</td><td>19 (single)</td></tr><tr><td>21 (double)</td><td>21 (double)</td><td>22 (double)</td><td>31 (double)</td></tr><tr><td>Other Fp</td><td>3 (pipelined)</td><td>3 (pipelined)</td><td>3 (pipelined)</td><td>4 (pipelined)</td></tr><tr><td>Memory (address computation)</td><td>1</td><td>1</td><td>1</td><td>1</td></tr><tr><td>First level cache (hit)</td><td>1</td><td>1</td><td>1</td><td>1</td></tr></table>

Table 5 Caches con®guration and latencies

<table><tr><td></td><td>Instruction cache</td><td>Data cache</td><td>Second level cache</td></tr><tr><td>Cache size</td><td>32 K</td><td>32 K</td><td>4 Mb</td></tr><tr><td>Block size</td><td>32 b</td><td>32 b</td><td>64 b</td></tr><tr><td>Associativity</td><td>2-way set assoc.</td><td>2-way set assoc.</td><td>2-way set assoc.</td></tr><tr><td>Access time (hit)</td><td>1 cycle</td><td>1 cycle</td><td>5 cycles</td></tr></table>

64-entry translation lookaside buer (TLB) was included in both the instruction cache and data cache. A penalty of 30 cycles was imposed for a TLB miss and 25 cycles for second level cache miss. Both the integer and ¯oating-point instruction queues can dispatch instructions out-of-order. The memory queue can only dispatch instructions in-order. Also, store instructions are only permitted to update the data cache after all its previous instructions have completed. For the simulation of SS, the sequential workloads are used.

For the MCMS architecture, we used four different con®gurations. Each supports a dierent number of hardware contexts. For the h1 con®guration, there is 1 hardware context, for the h2, h4 and h8 con®gurations, there are 2, 4 and 8 hardware contexts, respectively. This determines the maximum number of threads that can be executed

concurrently. The hardware resources of these con®gurations is the same as the SS con®guration with the addition of a thread unit and multiple contexts. The only resource advantage of the MCMS con®gurations over SS is the extra register ®les and reorder buers.

The simulation of MCMS con®gurations used the multithreaded workloads instead of the sequential ones. The workloads are set to run with 8 software threads in all the MCMS con®gurations. With this, the workloads used on dierent con®gurations of MCMS were identical. No context switching is required in $h 8$ as all the 8 threads can be accommodated by the hardware contexts. However, context switching is required for h1, h2 and $h 4$ because only 1, 2 and 4 threads may coexist in the processor at any one time, respectively. One diculty we had was to account for the

overhead in context switching. We opted not to account for this as this we believe is implementation dependent and since there have not been many such implementations, it is not possible to give a realistic approximation.

# 5. Simulation results

We ®rst simulated the sequential workloads on a superscalar processor (con®guration SS). The result was used to identify the limitations of instruction level parallelism in sequential programs. After that, the MCMS con®gurations were simulated using the multithreaded workloads. The number of threads used for our study is ®xed at 8. An analysis was made to identify the source of the performance improvements and the possible bottlenecks.

# 5.1. Limited instruction level parallelism in sequential programs

Our simulation results of the superscalar processor (con®guration SS) showed that the instructions per cycle (ipc) ranges from 0.71 to 0.97. This is less than a quarter of the peak performance of 4 ipc according to the simulated processor con®guration. The limitations of a superscalar processor can be categorised into data dependencies, control dependencies and resource con¯ict.

The graph in Fig. 2 shows the percentage of cycles where there are 0, 1, 2, 3 and 4 or more ready instructions in the instruction queues. A ready instruction is an instruction that has all its source operands value available and it can be dispatched for execution. Due to resource contentions, not all of the ready instructions may be dispatched for execution in each cycle. The graph

![](mineru_assets/Loh和Wong - 2000 - Multiple context multithreaded superscalar processor architecture/images/ee234986240ce246795ec5337073fd32e65b5fa1b5025304c47a3859cde57e54.jpg)
Fig. 2. Distributions of issue cycles and number of ready instructions.

also shows the percentage of cycles where 0, 1, 2, 3 and 4 or more instructions are issued for execution.

The instruction queues are empty in only less than $3 \%$ of the total execution time and there are more than four instructions in more than $70 \%$ of the total execution time. Therefore, there is no instruction starvation in the queues. The computation does not include the instructions that are fetched due to wrong branch prediction. As control dependency will cause instruction starvation, we can say that control dependency is not a severe limitation factor.

From the graph in Fig. 2, there is no ready instruction in $3 7 - 5 1 \%$ of the total execution time. When there is no ready instruction, no instruction can be issued for execution. This is the major limitation to the instruction throughput. The source of the problem is data dependency. Most of the instructions in the instruction queues are waiting for the values of their source operands. This shows that there is not enough instruction level parallelism in the programs to utilise the wider pipeline of superscalar processor. There is no severe resource contention as the number of ready instructions is low.

# 5.2. Performance of the MCMS

The speedup of MCMS (con®guration h1, h2, h4 and h8) relative to the superscalar processor (con®guration SS) is shown in the graph in Fig. 3. The results show no signi®cance speedup with 1 hardware context (h1) over the SS. The most obvious reason would be that both con®gurations only allow a single thread to be in execution at a time. No inter thread instruction level parallelism can be exploited in h1. The graph clearly shows an improvement in speedup (1.3±2.5 times) with 2 and 4 hardware contexts (h2 and h4). The speedup gained by having 8 hardware contexts is less signi®cance. In the cases of ocean and radix, h8 actually shows lower performance than h4. Ocean encounters high number of cache misses. The memory requirements limit its performance. Radix faces a huge increase in tlb misses when the number of context increases.

The graphs in Fig. 4 shows the average number of ready instructions per cycle and average number of instructions issued per cycle for each program with varying number of hardware contexts. From the graphs, we can see that the average number of ready instructions increases with the number of

![](mineru_assets/Loh和Wong - 2000 - Multiple context multithreaded superscalar processor architecture/images/7e1ad8684d2feec26e92df22c6c9b1b895f35ac7aee9196e4a355e478737c4e3.jpg)
Fig. 3. Speedup for dierent number of contexts.

![](mineru_assets/Loh和Wong - 2000 - Multiple context multithreaded superscalar processor architecture/images/389199c9d2b5226bc89311907c5a8df268495b3fe96b6df3ad1fb5d59f20d2b2.jpg)

![](mineru_assets/Loh和Wong - 2000 - Multiple context multithreaded superscalar processor architecture/images/f4cb93a807c21e336e28c64bcc92abbfca2932d9bc1583ca58a95263dda8e613.jpg)
Fig. 4. Average number of instructions per cycle (ready and issued).

hardware contexts. This shows that multiple contexts can increase the instruction level parallelism by exploiting inter thread parallelism. With more ready instructions, more instructions can now be issued for execution every cycle. Thus, increasing the overall instruction throughput.

As shown by the graphs, the gaps between the average number of ready instructions and average number of instructions issued get larger with the increasing number of hardware contexts. A ready instruction cannot be issued for execution if the required execution unit is busy or occupied by another instruction. The huge gaps show the occurrence of resource contention. With multiple contexts, we reduce instructions data dependencies but in turn cause an increase in resource contention.

When resource contention occurs, the average number of ready instructions will grow at a faster rate. The reason is that the ready instructions will stay in the instruction queues for a longer period of time. This will increase the average number of ready instructions per cycle. Therefore, the actual instruction level parallelism may not be as high as the average number of ready instructions. When more execution units are added, we expect the gaps to be narrowed. Instruction issue rate will increase while the number of ready instructions will decrease.

# 5.3. Cache misses

The caches are shared among all the executing threads. With multiple contexts, the memory

reference from multiple threads will interleave and mix with each other. As the same workload of 8 threads is used for dierent processor con®gurations (h1, h2, h4 and h8), the memory references for each thread is still the same. However, the actual order of the memory references made on the data cache will be dierent for the varying number of hardware contexts.

In h1, only the thread occupying the hardware context may reference the memory. In h8, the memory reference for all the eight threads will intersperse and mix with each other. With multiple threads referencing the data cache in an interleaved manner, locality may be destroyed. A thread may cause a cache line needed by another thread in the near future to be replaced. This will increase the miss ratio. On the other hand, a thread may reference a cache line that has been fetched by another thread, reducing the miss ratio. This occurs when multiple executing threads share the same piece of data.

Fig. 5 shows the number of data cache misses per thousand instructions. The misses are divided into intra thread and inter thread misses. Inter thread misses are misses that would have been hits if each thread is given a separate $3 2 \mathrm { ~ K ~ }$ data cache.

The data cache misses generally increases with the increasing number of context. The increase is mainly caused by inter thread misses. This shows that inter-thread interference may destroy the cache locality and cause severe cache thrashing.

# 5.4. Execution units

We have identi®ed earlier that resource contentions could be a limiting factor when the number of hardware contexts increases. Therefore, we furthered our investigation by increasing the number of execution units. We added two more integer units, two more ¯oating-point units and two more memory units. The number of ports of the data cache is increased to four to match the number of memory units. All other resources are kept unchanged.

The graph in Fig. 6 compares the performance of the base con®gurations and the con®gurations with extra execution units. The graphs show that generally the performance improvement is greater with higher number of contexts. For h1 and h2, the extra resources do not provide much improvement because the extra execution units are hardly utilised. The execution units in the base

![](mineru_assets/Loh和Wong - 2000 - Multiple context multithreaded superscalar processor architecture/images/ca02233204214e30e2a4d5fb5a03d63e5fd8858e5dcd944ae23c67021339e151.jpg)
Fig. 5. Data cache misses per thousand instructions.

![](mineru_assets/Loh和Wong - 2000 - Multiple context multithreaded superscalar processor architecture/images/9b91227df440248b4c5b9ee222098437badaf34e721c96bed42e9b6a681ba7a0.jpg)
Fig. 6. Performance with extra execution units.

con®gurations can already almost satisfy the resource requirements in h1 and $h 2$ . The performance improvement is more obvious in $h 4$ and h8 where resource contention is more severe. One exception is detected in ocean where there is no improvement in $h 8$ . This is because ocean faces memory limitation and not resource contention.

About $60 \%$ of the instructions in radix are ¯oating-point instructions. This has caused a huge resource contention on the ¯oating-point execution units in $h 4$ and $h 8$ . With the extra execution units, we can improve the overall performance of radix by $8 \%$ and $1 5 \%$ in $h 4$ and $h 8$ , respectively. There is also an increase of $7 \%$ and $1 1 \%$ in $h 4$ and $h 8$ , respectively, for $\tt m p 3 d$ .

# 6. Conclusion

In this paper, we have outlined the design of the MCMS architecture, which can be used to exploit the instruction level parallelism of multiple threads of execution. The main idea is to allow instructions

from multiple threads to be executed concurrently. Our proposal includes a mechanism to support multiple contexts, a hardware implementation of multithreaded constructs together with a context switching mechanism. All these can be built onto a conventional superscalar processor architecture.

Our simulation results veri®ed that sequential programs could not provide enough instruction level parallelism to fully utilise the wider pipeline of superscalar architecture. We have identi®ed that the main obstacle is data dependencies. Control dependencies and resource con¯icts do not give rise to any severe performance limitation in a superscalar processor architecture.

The results of simulating the execution of multithreaded applications on the MCMS architecture showed that allowing multiple threads to execute concurrently can increase the average number of ready instructions in the instruction queues. More concurrent threads will produce more ready instructions. This will in turn let more instructions to be issued for execution every cycle. Thus, instruction throughput will be increased.

A 4-context MCMS processor con®guration can achieve a speedup of 1.6±2.5 times over a superscalar processor with similar hardware resources.

With the increasing number of hardware contexts (up to 8), we found that the limitations started to shift from data dependencies to resource contentions. This is due to the higher resource requirements. A speedup of 2 will double the resource utilisation. At some stage, the speedup will be limited by the resource contention. Increasing the resources such as adding more execution units can alleviate this. Increasing number of hardware contexts also cause cache thrashing. Cache locality may be destroyed by multiple concurrent executing threads. Despite these caveats, we believe that in the current scenario where chip density is ever increasing, hardware multithreading in a superscalar processor is a promising approach. We hope this work will contribute to the understanding of the trade-os involved.

# References

[1] A. Agarwal, B.-H. Lim, D. Kranz, J. Kubiatowicz, APRIL: A processor architecture for multiprocessing, in: Proceedings of the 17th Annual International Symposium on Computer Architecture, May 1990.
[2] R. Alverson, D. Callahan, D. Cummings, B. Koblenz, A. Porter®eld, B. Smith, The tera computer systems, in: Proceedings of the International Conference of Supercomputing, June 1990.
[3] B. Boothe, A. Ranade, Improved multithreading techniques for hiding communication latency in multiprocessors, in: Proceedings of the 19th Annual International Symposium on Computer Architecture, 1992.
[4] H. John Edmondson, Paul Rubinfeld, Ronald Preston, Vidya Rajagopalan, Superscalar Instruction Execution in the 21164 Alpha Microprocessor, IEEE Micro, April 1995.
[5] A. Eustace, A. Srivastava, ATOM: A Flexible Interface for Building High Performance Program Analysis Tool, WRL Technical Note July 1994.
[6] M. Gulati, N. Bagherzadeh, Performance study of a multithreaded superscalar microprocessor, in: Proceedings of the International Symposium of High Performance Computer architecture, ACM, 1996.

[7] H.R. Halstead Jr., T. Fujita, MASA: A multithreaded processor architecture for parallel symbolic computing, in: Proceedings of the 15th Annual International Symposium of Computer Architecture, June 1988.
[8] H. Hirata, K. Kimura, S. Nagamine et al., An elementary processor architecture with simultaneous instruction issuing from multiple threads, in: Proceedings of the International Conference of Computer Architecture, 1992.
[9] S. Hily, A. Seznec, Contention on Second Level Cache may Limit the Eectiveness of Simultaneous Multithreading, Technical Report PI-1086, IRISA, France, 1997.
[10] J.L. Lo, S.J. Eggers, J.S. Emer, H.M. Levy, R.L. Stamm, D.M. Tullsen, Converting thread-level parallelism to instruction-level parallelism via simultaneous multithreading, ACM Transactions on Computer Systems, August 1997.
[11] K.S. Loh, M.K. Quek, W.F. Wong, SPATS ± Accurate and ¯exible simulation of superscalar processors, in: Third Australasian Computer Architecture Conference, February 1998, Perth, Australia.
[12] A. Srivastava, A. Eustace, ATOM: A System for Building Customized Program Analysis Tools, WRL Research Report March 1994.
[13] B.J. Smith, Architecture and applications of the HEP multiprocessors system, in: Proceedings of the SPIE ± Real Time Signal Processing, August 1981.
[14] E.J. Smith, A.R. Pleszkun, Implementation of precise interrupts in pipelined processors, in: Proceedings of the 12th Annual International Symposium on Computer Architecture, 1985.
[15] J.P. Singh, W.-D. Weber, A. Gupta, SPLASH: Stanford Parallel Applications for Shared Memory, Computer Architecture News, March 1992.
[16] The UltraSPARC Processor ± Technology White Paper The UltraSPARC Architecture, Sun Microsystems Inc., 1995.
[17] D.M. Tullsen, S.J. Eggers, H.M. Levy, Simultaneous multithreading: Maximizing on-Chip parallelism, in: Proceedings of the 22nd Annual International Symposium on Computer Architecture, June 1995.
[18] D.M. Tullsen, S.J. Eggers, J.S. Emer, H.M. Levy, J.L. Lo, R.L. Stamm, Exploiting choice: Instruction fetch and issue on an implementable simultaneous multithreading processor, in: Proceedings of the 23rd Annual International Symposium on Computer Architecture, May 1996.
[19] M. Trembly, J. Micheal O'Connor, UltraSparc I: A fourissue processor supporting multimedia, IEEE Micro, April 1996.
[20] S.C. Woo, M. Ohara, E. Torrie, J.P. Singh, A. Gupta, The SPLASH-2 programs: Characterization and methodolog-

ical considerations, in: Proceedings of the 22nd Annual International Symposium on Computer Architecture, June 1995.
[21] K.C. Yeager, The MIPS R10000 Superscalar Microprocessor, IEEE Micro, April 1996.

![](mineru_assets/Loh和Wong - 2000 - Multiple context multithreaded superscalar processor architecture/images/4ba08a9cab60362cc0aba933896b44c0f850ce490a58f97296e09089c4d32143.jpg)

Kim-Seong Loh received his B.Sc. (Hons) from the National University of Singapore in 1997 and his M.Sc in 1998. He is currently working for a company specialising in multilingual software. His research interest includes processor pipelining, optimisation and performance evaluation.

![](mineru_assets/Loh和Wong - 2000 - Multiple context multithreaded superscalar processor architecture/images/279eec5b96bd5a0f9025a4e8ab6409dc97a294e526de62693d231668b8d12ab9.jpg)

Weng-Fai Wong received his B.Sc. (Hons) and M.Sc. from the National University of Singapore in 1989 and 1991 respectively. He obtained his Dr. Eng. Sc. from the University of Tsukuba, Japan, in 1993. He is currently Assistant Professor at the Department of Computer Science of the National University of Singapore. His research interests include processor architecture, compiler optimisations and parallel processing.
