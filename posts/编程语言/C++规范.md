---
date: 2026-04-26
tags:
- C++
- 编码规范
- 代码风格
title: 通用规范
---

# 通用规范

- 用path表示路径时，默认包含文件本身的名字；用dir表示路径时，默认只包含文件所在的文件夹。

- 对多行代码进行注释时，应使用如下格式

  ```cpp
  // Comment for the code line below
  int a = 1;  // Short Comment
  // ----- Comment for the code block until a blank line
  int b = 2;
  int c = 3;
  int d = 4; 
  
  // ----- L1 comment: define variables
  //   --- L2 comment: variables for module 1
  int var_1_for_m_1;
  int var_2_for_m_1;
  //   --- L2 comment: variables for module 2
  int var_1_for_m_2;
  int var_2_for_m_2;
  
  // ----- L1 comment: check condition and do procedure
  bool condition;
  if (condition) {
      // --- L2 comment: do procedure
      pre_do_process();
      do_process();
      post_do_process();
  }
  
  
  ```

  



# C++编程规范

C++语言的高级特性繁多，且十分灵活，如不加以限制，则很容易导致项目难以阅读和维护。

定义`int`、`float`、`uint16_t`等基本类型，不含成员函数的结构体类型，`std::pair<>`等简单STL容器类型为**简单类型**。

定义带有成员函数的类，`std::vector<>`、`std::map<>`等复杂STL容器类型为**复杂类型**。

值语义将指针作为数值对待，引用语义将指针作为引用对待。

## 通用规范

- 构造函数应标明`explicit`。
- 函数参数、局部变量使用下划线命名。
- 如果一个类中带有虚函数，则应创建只含有纯虚函数的接口，并实现该接口。
  - 接口的命名为大驼峰，并以`_I`结尾
  - 类或结构体成员使用小驼峰命名
- 对于不含有成员函数的类，应使用结构体。
  - 此时其成员也可使用下划线命名
- 为保证面向对象的封装性，应尽量不使用友元。
- 如无特殊需求，只使用`public`的方式继承。
- 尽量不在暴露给用户的头文件中定义宏。

## C-With-Class 规范

使用“值语义”，多在偏底层的项目中使用，为方便熟悉C但不熟悉C++高级语法的人员理解。

- 不使用智能指针等封装的指针。
- 不进行运算符重载。
- 不使用C++除面向对象外的其他高级特性。
- 只使用默认的拷贝构造函数，不使用移动构造。
  - 默认的拷贝构造函数符合“值语义”


## Java-like 规范

使用“引用语义”，多在注重业务逻辑的项目中使用，以在大型项目的开发中兼顾开发效率与内存安全。

- 如无必要，不使用宏。
  - 定义数值可使用`const static`类型的变量
  - 定义过程可使用`static inline`的函数
- 对于复杂类型，不使用裸指针，只使用智能指针。
- 对于简单类型，避免在堆区创建对象。
- 不在栈上创建复杂类型对象（这样也就避免了拷贝与移动），不考虑拷贝与移动。
  - 如必须拷贝，则创建`duplicate()`成员函数供用户构造新的对象
- 不使用引用。对于复杂类型，使用对象的智能指针来实现引用语义；对于简单类型，使用其裸指针实现引用语义。
- 对于复杂类型，不使用对象传参或作为返回值，只使用智能指针传参。
- 如果有复杂类型的成员，则应使用其引用（即其智能指针）。