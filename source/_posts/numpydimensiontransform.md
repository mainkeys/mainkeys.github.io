---
title: numpy三维数组维度变换/提取
date: 2022-03-29 22:31:43
tags: [python,numpy]
categories: python
---

### 有时对多维numpy数组需要进行维度的转换/提取，遇到需要从（A,B,C）三维数组中提取（A,B）、（A,C）或者（B,C）或者（A,）这几个维度数据时，总是忘记该如何切片，记录一下

####  1. （A,B,C）——> (A,B)
`X_New = X[ :，:，0]`
![](https://img-blog.csdnimg.cn/ae56b4cd0b584ca49e4a06e85b9a37b4.png)
![](https://img-blog.csdnimg.cn/b00e48bd7b984c839bf058b0372a876e.png)
![](https://img-blog.csdnimg.cn/c39d960bc4964bc78cc29113f6a010fc.png)
![](https://img-blog.csdnimg.cn/33bafaca76554d7cb23209b901460665.png)






#### 2. （A,B,C）——> (A,C)
`X_New = X[ :，0，:]`

#### 3. （A,B,C）——> (B,C)
`X_New = X[ 0，:，:]`

####  4. （A,B,C）——> (A,)
`X_New = X[ :，0，0]`