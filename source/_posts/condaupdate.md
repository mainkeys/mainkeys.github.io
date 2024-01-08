---
title: Anaconda报错，需更换镜像源
date: 2021-09-19 14:34:52
tags: [Anaconda,深度学习]
categories: 深度学习
---

遇到Anaconda报错
![=](https://img-blog.csdnimg.cn/db7ffaf3c1c94f1c8a70d0f57a2b51db.png?process=image/watermark,type_ZHJvaWRzYW5zZmFsbGJhY2s,shadow_50,text_Q1NETiBAajogKQ==,size_20,color_FFFFFF,t_70,g_se,x_16)
迟迟没想到是清华镜像源的问题，输入
```cmd
conda config --show 
```
查看channels，看到之前加入的清华镜像源
![=](https://img-blog.csdnimg.cn/6729b3cdab564e548d5217d7eef5a03c.png?=-=process=image/watermark,type_ZHJvaWRzYW5zZmFsbGJhY2s,shadow_50,text_Q1NETiBAajogKQ==,size_20,color_FFFFFF,t_70,g_se,x_16)
```cmd
conda config --remove channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/main/

conda config --remove channels https://mirrors.tuna.tsinghua.edu.cn/anaconda/pkgs/free/
```
删除镜像源后，添加中科大的镜像源
```cmd
conda config --add channels https://mirrors.ustc.edu.cn/anaconda/pkgs/free/

conda config --add channels https://mirrors.ustc.edu.cn/anaconda/pkgs/main/
```

![](https://img-blog.csdnimg.cn/df117d7408c94aeba22cffc0f9f9ec02.png?process=image/watermark,type_ZHJvaWRzYW5zZmFsbGJhY2s,shadow_50,text_Q1NETiBAajogKQ==,size_20,color_FFFFFF,t_70,g_se,x_16)

之后再进行conda更新
```cmd
conda update conda
```
![](https://img-blog.csdnimg.cn/f3e0d71d122e4bbcb5370d9369d21398.png?process=image/watermark,type_ZHJvaWRzYW5zZmFsbGJhY2s,shadow_50,text_Q1NETiBAajogKQ==,size_20,color_FFFFFF,t_70,g_se,x_16)
![](https://img-blog.csdnimg.cn/f303228888594b3a9bbb2a9575d5c215.png?process=image/watermark,type_ZHJvaWRzYW5zZmFsbGJhY2s,shadow_50,text_Q1NETiBAajogKQ==,size_20,color_FFFFFF,t_70,g_se,x_16)
之前所有遇到的问题包括pip命令全部解决了。
![](https://img-blog.csdnimg.cn/a5dbab03e8404a37866a2d92207bc576.png)



--- 
总结：（清华镜像慢，还容易出问题）
--
