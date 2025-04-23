---
title: C Plus Plus study
date: 2021-09-19 16:48:09
tags: C++
categories: C++
cover: https://mks-1306588458.cos.ap-nanjing.myqcloud.com/cover.png
---

C++代码变成可执行的代码主要做的工作： 编译 & 链接
编译由`编译器`完成`，编译过程就是将`.c`, `.cpp`, `.h`文件转换为`.obj`文件的过程, `obj` 文件为二进制文件

`hello.c` -预处理-> `hello.i` -编译->`hello.s` (此为汇编代码) -汇编-> `hello.o` -链接-> `hello`

在与处理中`#include`即复制粘贴`include`的内容 , 同样的`#define Integer int`也是将所有`Integer`替换为`int`，
也可以 
```cpp
#if 1
code....
```
预处理
