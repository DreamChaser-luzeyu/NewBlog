---
date: 2026-04-26
tags:
- ARM
- llama.cpp
- 交叉编译
- CMake
- 大模型
title: ARM上运行llama.cpp
---

# ARM上运行llama.cpp

## 编译

```bash
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# -DCMAKE_SYSTEM_NAME=Linux中的`Linux`一定要大写！

cmake -B build \
    -DCMAKE_SYSTEM_PROCESSOR=aarch64 \
    -DCMAKE_SYSTEM_NAME=Linux \
    -DCMAKE_CROSSCOMPILING=true \
    -DGGML_SVE:BOOL=ON \
    -DCMAKE_C_COMPILER="/usr/bin/aarch64-linux-gnu-gcc" \
    -DCMAKE_CXX_COMPILER="/usr/bin/aarch64-linux-gnu-g++"
# 如果使用CLion,可以在CMake options中加入这些选项。
cmake --build build --config Release
```

## 运行

使用`taskset -c 1`限制单核运行

## ggml源码梳理

llama.cpp使用ggml算子库，其源码位于`llama.cpp/ggml`。

以下说明基于checkout `fa42aa6d8902cc4eaf31866b3b3b7b61b69da930`

### 基本说明

ggml算子库整体使用C风格编写，使用封装了数个函数指针的结构体实现多态。

#### 文件说明

- `ggml.h`包含了供外部其他源文件调用的API

#### 类型说明

##### 算子相关类型

- `struct ggml_tensor`表示一个张量。在ggml中，张量是“懒计算”的，因此，此结构中还储存着源张量、运算类型等信息。

  此结构中包含数个“源张量”的指针以及运算类型信息，而“源张量”中可能也包含着其他张量的指针，这就形成了“计算图”。

  - `struct ggml_backend_buffer`描述一个计算后端，其中包含着计算后端相关的数个函数指针。

- `struct ggml_context`表示计算的上下文，其中包含着计算数据的指针。

##### 实现相关类型

- `struct ggml_backend_i`包含计算后端相关的函数指针，张量的据具体运算在其中定义的函数指针的实现里实现

### 流程说明

#### 初始化

- 调用`ggml_backend_cpu_init()`函数，返回一个`ggml_backend_t`对象
  - 根据需要调用`ggml_backend_***_init()`函数，可选CPU、CUDA、Vulkan等后端
  - 返回的`ggml_backend_t`对象中包含后端设备进行计算所需的函数指针
  - 这一部分目前并不是多态的，应根据需要直接调用对应的`ggml_backend_***_init()`函数

#### 计算流程

我们以算子`GGML_OP_ADD`为例梳理执行流程。

- 算子`GGML_OP_ADD`对应`ggml.h:861`函数

  ```cpp
  GGML_API struct ggml_tensor * ggml_add(
          struct ggml_context * ctx,
          struct ggml_tensor  * a,
          struct ggml_tensor  * b);
  ```

- `ggml_add`函数内调用`ggml_add_impl`函数，此函数返回一个新的`struct ggml_tensor *`对象指针，其中包含所有源`ggml_tensor`的指针以及运算类型信息。

  此函数并不进行实际的计算，只是对“计算图”做了延伸，并返回了新的计算图的根结点。