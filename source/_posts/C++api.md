---
title: C++ 库对应的api
date: 2023-05-26 11:13:54
tags: ['C++']
cover: https://mks-1306588458.cos.ap-nanjing.myqcloud.com/cover11.png
---


```CPP
#include <iostream>
#include <sstream>      // istringstream iss(S);    
#include <vector> 
#include <numeric> // accumulate    积累求和
#include <iomanip>       // setprecision 控制精度
#include <vector>
```

istringstream是一个比较有用的c++的输入输出控制类。

C++引入了ostringstream、istringstream、stringstream这三个类，要使用他们创建对象就必须包含<sstream>这个头文件。
istringstream类用于执行C++风格的串流的输入操作。
ostringstream类用于执行C风格的串流的输出操作。
strstream类同时可以支持C风格的串流的输入输出操作。


istringstream的构造函数原形如下：
istringstream::istringstream(string str);
它的作用是从string对象str中读取字符。

```CPP
#include<iostream>  
#include<sstream>        //istringstream 必须包含这个头文件
#include<string>  
using namespace std;  
int main()  
{  
    string str="i an a boy";  
    istringstream is(str);  
    string s;  
    while(is>>s)  
    {  
        cout<<s<<endl;  
    }  
      
}
```

输出是:
```
i
am
a
boy
```
