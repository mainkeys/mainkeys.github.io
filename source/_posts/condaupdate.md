---
title: Anaconda报错，需更换镜像源
date: 2021-09-19 14:34:52
tags: [Anaconda,深度学习]
categories: 深度学习
cover: http://sunowc60i.hd-bkt.clouddn.com/cover8.png
---

遇到Anaconda报错
![](./1.png)
迟迟没想到是清华镜像源的问题，输入
```cmd
conda config --show 
```
查看channels，看到之前加入的清华镜像源
![=](./2.png)
```cmd
conda config --remove channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/

conda config --remove channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/
```
删除镜像源后，添加中科大的镜像源
```cmd
conda config --add channels https://mirrors.ustc.edu.cn/anaconda/pkgs/free/

conda config --add channels https://mirrors.ustc.edu.cn/anaconda/pkgs/main/
```

![](./3.png)

之后再进行conda更新
```cmd
conda update conda
```
![](./4.png)
![](./5.png)
之前所有遇到的问题包括pip命令全部解决了。
![](./6.png)



--- 
总结：（清华镜像慢，还容易出问题）
--
