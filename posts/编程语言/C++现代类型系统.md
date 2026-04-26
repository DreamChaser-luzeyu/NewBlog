---
date: 2026-04-26
tags:
- C++
- 类型系统
- 类型萃取
- static_cast
- dynamic_cast
title: C++现代类型系统
---

# C++现代类型系统

## 类型转换

### `static_cast`

`static_cast`用于代替传统C风格的类型转换，建议使用`static_cast<T>(val)`替换C风格的类型转换。

- 其功能相当于C风格的强制转换

- 编译时检查，一般用于非多态的转换

- 没有运行时类型检查来保证转换的安全性

  ```cpp
  char ch = 'a';
  int b = static_cast<int>(ch);
  ```

- 相较于C风格的类型转换更加安全

  ```cpp
  const int a = 1;
  int* b = (int*)&a;              // 编译通过
  int* c = static_cast<int*>(&a); // 编译报错“Static_cast from 'const int *' to 'int *' is not allowed”
  ```

### `dynamic_cast`

`dynamic_cast`通常用于类层次间的上行转换和下行转换。

## 类型萃取

（个人理解）C++的类型萃取特性type traits直译为“类型的特性”，其实现的功能也和提取类型的特性有关。而什么是类型的特性？如对于类型`T`，`const T`、`T&`、`T&&`都是类型`T`的“变种”。类型萃取是纯编译期进行的，不涉及对数据的修改。

需要引入`<type_traits>`头文件，类型萃取主要用于在**编译期间**获得操作类型相关的信息，一般用于在泛型编程以及在编译时做出决策。以下是一些常用的类型萃取：

- `std::is_integral<T>`：判断类型 T 是否为整数类型。
- `std::is_floating_point<T>`：判断类型 T 是否为浮点数类型。
- `std::is_pointer<T>`：判断类型 T 是否为指针类型。
- `std::is_reference<T>`：判断类型 T 是否为引用类型。
- `std::is_const<T>`：判断类型 T 是否为 const 类型。
- `std::is_same<T, U>`：判断类型 T 和 U 是否相同。

这些类型萃取可以使用`::value`取出一个布尔值，当类型符合其条件时为true，否则为false。在函数模板或类模板中，我们可以借助这些布尔值对模板类型进行判断，并根据类型决定不同的执行逻辑。

当然，除了对类型trait的提取，此特性还能够”编辑“类型的trait，从而在进行模板编程时减少重复的代码，或避免错误。

举例：希望定义一个函数模板，并在函数中定义一个`T`类型的对象。下面的代码展示了不使用类型萃取带来的问题：

```cpp
template <typename T>
void test_type_traits_1(T obj) {
    T tmp;  // 错误，因为类型`T`被推理为`int&`，不能直接定义int&类型的变量
}

void caller() {
    int val = 1;
    int& val_ref = val;
    test_type_traits_1<int&>(val_ref);
}
```

使用类型萃取可以保证类型T不是一个引用类型，从而实现预期的逻辑，并规避这种错误：

```cpp
template <typename T>
void test_type_traits_2(T obj) {
    std::remove_reference<T> tmp;  // `T`是`int&`，但`std::move_reference<T>`是`int`
}

void caller() {
    int val = 1;
    int& val_ref = val;
    test_type_traits_1<int&>(val_ref);
}
```

以下是一些常用的类型“traits”的编辑：

- `std::remove_reference<T>`
- `std::remove_const<T>`
- ...

## 经典示例：`std::move`

`std::move`的功能是获得一个绑定到左值上的右值引用。

标准库对`std::move`的定义如下：

```cpp
template <typename T>
typename remove_reference<T>::type&& move(T&& t) {
    return static_cast<typename remove_reference<T>::type&&>(t);
}
```

### 示例分析

考虑以下代码中的`std::move`：

```cpp
string str_2;             // Obviously `str_2` is lvalue
str_2 = std::move(string("str 2"));
               // ^^^ `string("str 2")` is rvalue
```

该段代码中实例化的`std::move`函数定义如下：

```cpp
string&& move(string&&) {...}
```

于是此`std::move`什么都不做，相当于`str_2 = string("str 2");`，显而易见。然而，考虑`std::move`传入左值的情况：

```cpp
string str_1("str 1");
string str_2;             // Obviously `str_2` is lvalue
str_2 = std::move(str_1);
               // ^^^ `str_1` is lvalue
```

此时实例化的`std::move`函数定义如下：

```cpp
// 类型T被推断为string&
// string&& move(string& &&) {...}
// 由于没有`string& &&`类型，因此根据C++的规定，此处被“折叠”为`string&`
string&& move(string& t) {
    return static_cast<remove_reference<string&>&&>(t);
}
```

> C++的引用折叠规则：
>
> - C++不允许直接创建引用的引用，如：
>
>   ```cpp
>   int a;
>   int& & b = a;  // Error
>   int&& & b = a; // Error
>   int&& && b = a;// Error
>   // ...
>   ```
>
> - 但是允许间接创建引用的引用，因为基于现有的模板语法，间接创建引用的引用不可避免
>
>   ```cpp
>   template <typename T>
>   void func(T&& ref) { ... }
>              // ^^^ 此处间接创建了int& && ref
>   void caller() {
>       int a;
>       int& b = a;
>       func<int&>(b);
>   }
>   ```
>
>   - 于是规定`T& &`、`T& &&`、`T&& &`被折叠为`T&`
>   - 规定`T&& &&`被折叠为`T&&`

即通过`std::move`将`string&`类型的`t`通过`static_cast`转为`string&&`；

> - C++中允许显示地将左值引用转为右值引用

而将转为右值引用的`str_1`赋值给`str_2`时会调用`string`类的移动赋值函数（参数为`T&&`的`operator=`重载），区别于拷贝赋值，移动赋值不会对实际的字符串数据进行深拷贝，而只是让`str_2`中需要拷贝的字段指向`str_1`中的数据，同时将`str_1`置空。

值得注意的是，任何cast操作都不会导致`operator=`重载、拷贝构造函数或移动构造函数的调用，真正调用这些函数的一定是实际的构造或赋值，如：

```cpp
mytype_t obj_1("str 1");
mytype_t obj_2(std::move(str_1)); // 构造导致调用`mytype_t::mytype_t(mytype_t&&)`
```

```cpp
mytype_t obj_1("str 1");
mytype_t obj_2 = std::move(str_1); // 赋值导致调用`mytype_t::operator=(mytype_t&&)`
```


```cpp
mytype_t obj_1("str 1");
mytype_t obj_2(str_1); // 构造导致调用`mytype_t::mytype_t(mytype_t&)`
```
```cpp
mytype_t obj_1("str 1");
mytype_t obj_2 = str_1; // 赋值导致调用`mytype_t::operator=(mytype_t&)`
```

## 经典示例：以二维方式访问一维数组

```cpp
int arr[] = {0, 1, 2, 3, 4, 5, 6, 7, 8};
int* ptr = arr;                     // ptr指向一维数组的首元素

typedef int arr_2d_t[3][3];
arr_2d_t *new_ptr_2;
new_ptr_2 = static_cast<arr_2d_t*>((void*)ptr);
```

## 经典示例：从一个对象推导类型

```cpp
int arr_2d[3][3];
decltype(arr_2d) *new_ptr;
new_ptr = static_cast<decltype(arr_2d)*>((void*)ptr);
```