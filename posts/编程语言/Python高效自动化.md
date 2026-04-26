---
date: 2026-04-26
tags:
- Python
- 自动化
- Cython
- ctypes
title: Python高效开发
---

# Python高效开发

## Python调用C函数

### 不使用第三方工具

- 最繁琐，但调用开销最小

- 如果只是希望在自己的小项目里调用一些C函数，不建议使用这种方式
- 这种方式主要用于创建ctypes这样的工具，而不是给应用程序开发者使用

### 使用Cython

### 使用ctypes

- 最简单、最方便，调用开销最大