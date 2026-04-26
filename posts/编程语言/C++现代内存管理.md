---
date: 2026-04-26
tags:
- C++
- 内存管理
- 智能指针
- 右值引用
title: C++现代内存管理
---

# C++现代内存管理

## 左值和右值

### 左值

- 可以取地址的常量或变量就是左值
- 可以放在等号左边的值一定是左值
- 可以取地址的常量也是左值

### 右值

- 只能放在等号右边
- 不能取地址
- 如：（返回值的）函数返回值、字面量

## 左值引用和右值引用

### 左值引用 `T&`

- 通常说的“引用”
- 只能引用左值，也可以理解为给左值取别名
- 用const修饰后也可引用右值
  - 好怪，为什么需要这个特性？
    - 为了避免对象拷贝，通常使用传引用代替传值
    - 传字面量等右值也是客观需求，如果不允许引用右值，那么右值就必须拷贝
    - 在C++11标准之前，没有右值引用的概念，因此规定了`const T&`也可引用一个右值，由于有const修饰，因此是安全的
  - 使用`const T&`引用一个右值时，能取地址吗，我猜不行
- 作为参数传递、作为返回值返回都不改变原对象的生命周期
  - 因此作为返回值返回时，如果返回了局部变量的引用，那么这个引用所引的对象已被释放
  - 因此返回左值引用有内存安全问题

### 右值引用 `T&&`

- C++11的新特性

- 用于引用一个右值

- 引用左值时需要使用`std::move(l_val)`

  - 因此就引出了“移动构造函数”的概念（当然，还有另一种对赋值运算符`=`的重载）

    ```cpp
    class TestClass {
    private:
        uint8_t* mem;
        size_t len;
    public:
        // Copy constructor
        TestClass(TestClass& old_obj) { /*...*/ }
        // Move constructor
    	TestClass(TestClass&& old_obj) { 
            // The `old_obj` does not have the ownership to `mem` any longer
            old_obj.mem = nullptr;
        }
        // Destructor
        ~TestClass() {
            if(mem) delete mem;
        }
    }
    ```

    在使用`std::move(l_val)`时，移动构造函数会被调用，默认的移动构造函数和拷贝构造函数都相当于浅拷贝，是吗？？

  - 通常，在移动构造函数中，我们不会拷贝对象中指向堆内存的数据，而是让指针仍指向原有堆内存

    - C++仍然是值语义的语言（尽管可以用指针等来表达引用语义），因此对栈上数值的拷贝无法避免
    - 当然，由于对象的所有权转移到了新的引用上，因此为避免重复析构，通常将已不再拥有所有权的对象中的指针值为`nullptr`

- 会延长对象的生命周期，可以延长到作用域之外

  - 因此，返回一个右值引用总是安全的

- 右值引用本身是一个左值，可以进行取地址和赋值操作（没有const修饰时）

  - 因此，当右值引用引用一个右值时，这个右值会被存储到某处，取地址就是取该处的地址

### `std::move()`移动赋值



## 智能指针

使用智能指针的目的是为了更容易、更安全地管理动态内存。与容器类似，智能指针也是模板。

后续代码以自定义类型`rand_n_t`为例。

```cpp
class rand_n_t {
private:
    int* rand_arr = nullptr;
public:
    const static int DEFAULT_NUM = 10;
    rand_n_t() {
        std::cout << "Calling rand_n_t()" << std::endl;
        rand_arr = new int[DEFAULT_NUM];
        for(int i = 0; i < DEFAULT_NUM; i++) {
            rand_arr[i] = random();
        }
    }
    rand_n_t(int num) {
        std::cout << "Calling rand_n_t(int)" << std::endl;
        rand_arr = new int[num];
        for(int i = 0; i < num; i++) {
            rand_arr[i] = random();
        }
    }
    ~rand_n_t() {
        if(rand_arr) delete[] rand_arr;
        std::cout << "destruct" << std::endl;
    }
};
```

### 基本使用

使用方式与普通指针类似，解引用一个智能指针将返回它指向的对象，也支持使用`->`运算符。

- `*`、`->`运算符的使用与裸指针类似。

- `.get()`方法

  - 调用其`.get()`方法将返回其裸指针类型，但不会改变其引用计数。

  - 对不指向任何内存的智能指针使用`get()`方法将返回`nullptr`。

    ```cpp
    std::shared_ptr<int> sp;
    auto* rp = sp.get();     // rp == nullptr
    ```

  - 使用`get()`方法获得的裸指针可能无效，如在下列情况：

    - 从`shared_ptr`中获得的裸指针，而所有`shared_ptr`对象都已被销毁

- 调用智能指针的拷贝构造函数或赋值运算符`=`会增加引用计数

- 返回一个智能指针时会增加其管理的对象的引用计数

- 销毁（包括但不限于离开作用域）一个智能指针时会减少其管理的对象的引用计数，

### `shared_ptr`

我想，`shared_ptr`该会是最常用的一种智能指针类型，因为基本上可以直接用它来替换原本的裸指针，因为它具有以下特性或功能：

- 在最后一个`shared_ptr`被销毁前，其管理的对象不会释放。
  - `shared_ptr`保证只要有任何`shared_ptr`对象引用某对象，那么该对象就不会被释放

- 使用`std::make_shared<T>(...)`方法创建对象，返回指向`T`类型对象的指针。

  ```cpp
  void test_shared_ptr_1() {
    int* raw_ptr = new int(ANY_INT_VAL);
    std::shared_ptr<int> sp = std::make_shared<int>(ANY_INT_VAL);
    std::shared_ptr<int> sp_2(sp);
    auto* rp = sp_2.get();
    // `raw_ptr` memory leaks after return
    // `sp` destructs upon return
  }
  ```

- 使用`std::make_shared<T>(...)`方法创建对象时，会自动调用构造函数，也可以传参。

  ```cpp
  void test_shared_ptr_2() {
      rand_n_t* raw_ptr = new rand_n_t();
      auto sp = std::make_shared<rand_n_t>(20);
  }
  // Output:
  // Calling rand_n_t()
  // Calling rand_n_t(int)
  // destruct
  ```

- 一旦一个`shared_ptr`的计数器变为0，它就会自动释放自己所管理的对象（调用析构函数）。

  ```cpp
  void test_shared_ptr_3() {
      auto sp = std::make_shared<rand_n_t>(20);
  }
  // Output:
  // Calling rand_n_t(int)
  // destruct
  ```

### `unique_ptr`

### `weak_ptr`

`weak_ptr`是一种不控制所指对象生存期的智能指针，它指向一个受到`shared_ptr`管理的对象。

- 将一个`weak_ptr`绑定到一个`shared_ptr`不会改变`shared_ptr`的引用计数；最后一个`shared_ptr`被销毁，对象就会被释放

- 为了保证内存安全，我们不能直接访问`weak_ptr`指向的对象，因为它可能已经被释放

  - 使用`.lock()`方法，此方法将返回一个指向共享对象的`shared_ptr`

    ```cpp
    void test_shared_ptr_5() {
        std::shared_ptr<rand_n_t> sp;
        sp = std::make_shared<rand_n_t>(20);
        std::weak_ptr wp(sp);
        if(auto ret = wp.lock()) {
            // access wp via ret, ret valid in this case
        }
    }
    ```

    - 只要此`shared_ptr`存在，它所指向的对象就不会被释放，因此当访问它所指的对象时，还是会增加引用计数
    - 当获得了`shared_ptr`后，即使其他原始的`shared_ptr`都已被销毁，对象也将保留，直到此`shared_ptr`被销毁

  - 可以使用`if`语句判断`.lock()`的返回值（这是C++什么机制？是`operator bool`的重载）

    ```cpp
    std::weak_ptr<rand_n_t> func2(int num) {
        auto sp = std::make_shared<rand_n_t>(num);
        return std::weak_ptr(sp);
    }
    
    void test_shared_ptr_6() {
        auto wp = func2(20);
        if(auto ret = wp.lock()) {
            std::cout << "ret valid" << std::endl;
        } else {
            std::cout << "ret invalid" << std::endl;
            // invalid in this case
        }
    }
    ```

    

## 容器与智能指针