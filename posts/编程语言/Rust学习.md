---
date: 2026-04-26
tags:
- Rust
- Macro
- 元编程
title: Rust学习
---

# Rust学习

## Macro

### 常见的 fragment 类型

| 片段类型            | 含义                     | 匹配示例                                               |
| ------------------- | ------------------------ | ------------------------------------------------------ |
| `expr`              | 表达式                   | `1 + 2`, `"hi"`, `vec![1,2]`                           |
| `ident`             | 标识符                   | `foo`, `x`, `Bar`                                      |
| `ty`                | 类型                     | `i32`, `Option<String>`                                |
| `path`              | 路径                     | `std::io::Result`, `self::foo`                         |
| `pat` / `pat_param` | 模式匹配                 | `Some(x)`, `_`, `(a, b)`                               |
| `stmt`              | 语句                     | `let x = 5;`, `return y;`                              |
| `block`             | 代码块                   | `{ println!("hi"); }`                                  |
| `item`              | 顶层项                   | `fn foo() {}`, `struct A;`, `impl X {}`                |
| `meta`              | 属性元数据               | `derive(Debug)`, `path = "a"`                          |
| `tt`                | 语法树标记（token tree） | 任意一段合法的 token，比如 `a + b`, `{ x }`, `#[attr]` |
| `vis`               | 可见性修饰符             | `pub`, `pub(crate)`                                    |
| `literal`           | 字面量                   | `42`, `"hi"`, `true`                                   |
| `lifetime`          | 生命周期                 | `'a`, `'static`                                        |
| `func_call`         | 方法调用                 | `func(1, 2)`                                           |

### 重复与分隔符

宏的强大在于它能匹配**可重复的语法模式**：

```
$( pattern ),*      // 逗号分隔的 0..n 次
$( pattern );+      // 分号分隔的 1..n 次
$( pattern )*       // 无分隔符，0..n 次
$( pattern )?       // 可选（0 或 1 次）
```