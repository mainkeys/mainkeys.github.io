---
title: 通过内网连接另一台主机的WSL
date: 2025-04-018 14:28:51
tags: "Rust"
cover: https://mks-1306588458.cos.ap-nanjing.myqcloud.com/cover1.png
---


# 背景
人太懒，想在床上躺着使用台式机的**wsl** `coding`

# 如何操作
### 前提准备

1. 台式机有**wsl**
2. 台式机和笔记本电脑在同一局域网内
3. 台式机内网ip已知
   注意： 我们其实不需要windows开启**ssh**服务，只需要在**wsl**中开启ssh服务即可，也就是绕过windows直接使用**wsl**的**ssh**服务。
### 操作步骤
1. 台式机开启**wsl**
2. 输入**wsl**命令，进入**wsl**, 输入**sudo apt update && sudo apt install openssh-server**命令，安装**ssh**服务
3. 输入**sudo service ssh start**命令，启动**ssh**服务
   至此，**wsl**的**ssh**服务已经启动，此时我们需要知道ip地址才能连接ssh，但是我们通过**ipconfig**命令访问到的是
