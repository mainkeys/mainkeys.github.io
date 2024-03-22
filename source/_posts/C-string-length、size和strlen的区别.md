<!--
 * @Author: mainkeys dymainkeys@gmail.com
 * @Date: 2024-01-08 22:49:20
 * @LastEditors: mainkeys dymainkeys@gmail.com
 * @LastEditTime: 2024-03-22 00:01:18
 * @FilePath: \mainkeys.github.io\source\_posts\C-string-length、size和strlen的区别.md
 * @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
-->
---
title: 'C++string::length、size和strlen的区别'
date: 2022-01-16 12:31:24
tags: C++
categories: C++
---
# 函数声明
C++ string 成员函数 length() 等同于 size()，但是和 C 库函数 [strlen](https://so.csdn.net/so/search?q=strlen&spm=1001.2101.3001.7020)() 有着本质区别，使用时切勿混淆。首先看一下三个函数的申明：
string::length和string::size
![](./1.png)
再来看看cstring里面的strlen，返回的是C风格的字符串长度。
![](./2.png)
>它们之间的区别根本就在于strlen()遇到字符'\0'就停止，而string成员函数length()   size()会过滤掉空字符，输出不会被截断。
如下例子：
```cpp
#include<iostream>
#include<cstring>
using namespace std;
char b[30]={0};
int main(){
    b[0] = 5; b[1] = 5; b[3] = 5;
    string a(b,30);
 
    // strcpy(b,a.c_str());
    cout<<"a.length()="<<a.length()<<endl;
    cout<<"a.size()="<<a.size()<<endl;
    cout<<"strlen(b)="<<strlen(b)<<endl;
    return 0;
}
```

运行的结果是：
![](./3.png)
