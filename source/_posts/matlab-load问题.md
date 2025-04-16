---
title: matlab—load命令读的数据问题
date: 2021-11-01 23:10:15
tags: matlab
categories: matlab
cover: https://mks-1306588458.cos.ap-nanjing.myqcloud.com/cover5.png
---
# load读取时遇到的问题

今天发现两个有趣的问题
- matlab读取使用load命令时有返回值则读取的数据为struct类型，无返回值则为原类型
例如`a=load(xxx.mat);`得到的a为struct类型，使用`a=cell2mat(struct2cell(load('xxx.mat')));`则为数据之前的类型  
- 文件名如果是以数字开头的`[1-9]+xxx.txt`,则load进工作区名字为data，如果以非数字形式开头则load进工作区名字为原文件名