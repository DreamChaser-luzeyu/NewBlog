---
date: 2026-04-26
tags:
- C++
- 模板
- 元编程
title: C++ 模板和元编程
---

# C++ 模板和元编程

### 示例：函数装饰器

```cpp
#include <iostream>
/**
 * @brief 要被修饰的函数
 */
int add_func(int a, int b) {
    return a + b;
}

/**
 * 装饰后的函数对象的生成器
 */
class FunctionGenerator;

/**
 * @brief 修饰后的函数类
 */
template <typename T> class DecoratedFunction; // 主模板声明
template <typename Ret, typename... Args> // 偏特化定义
class DecoratedFunction<Ret(Args...)> {
public:
    typedef Ret (*func_ptr_t)(Args...);
    explicit DecoratedFunction(FunctionGenerator *d, func_ptr_t func) : dev(d), func(func) {}
    Ret operator()(Args&&... args) {
        std::cout << "Call presudo func" << std::endl;
        return (*func)(args...);
    }
private:
    func_ptr_t func;
    FunctionGenerator *dev;
};

class FunctionGenerator {
public:
    explicit FunctionGenerator() = default;
    template <typename FuncType> DecoratedFunction<FuncType> getFunc(FuncType* func) {
        return DecoratedFunction<FuncType>(this, func);
    }
};

int main() {
    FunctionGenerator generator;
	// 生成add_func装饰后的仿函数对象
    auto func = generator.getFunc<decltype(add_func)>(&add_func);
    std::cout << func(3, 4) << std::endl;

    return 0;
}
```