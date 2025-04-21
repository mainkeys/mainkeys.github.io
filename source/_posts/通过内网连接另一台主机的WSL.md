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
   至此，**wsl**的**ssh**服务已经启动，我们需要知道ip地址才能连接ssh，但是我们通过windows系统的`powershell`/`cmd`**ipconfig**命令访问到的是`台式机`的ip地址，而`wsl`的ip地址是对外不可见的，也就是说暴露出来的对局域网可见的只有主机的地址，那么我们还需要用主机作为桥梁才能访问（连接）到wsl，那么其中一个思路就是通过端口转发将台式机的某个端口例如: `2222`绑定到wsl主机的`22`端口这样就能通过 `ssh wsl用户名@台式机ip地址 -p 2222` 来连接wsl了

4. 在主机中创建`powershell` ps脚本
```powershell
# 保存为 wsl_ssh.ps1
$wsl_ip = (wsl hostname -I).trim()
netsh interface portproxy delete v4tov4 listenport=2222
netsh interface portproxy add v4tov4 listenport=2222 listenaddress=0.0.0.0 connectport=22 connectaddress=$wsl_ip
```
设置脚本开机自动运行（可选）：
- 按 Win + R 输入 shell:startup，将脚本快捷方式放入启动文件夹。
- 首次手动运行脚本（以管理员身份）。

5. 允许防火墙规则
   powershell中输入
```powershell
New-NetFirewallRule -DisplayName "WSL2 SSH" -Direction Inbound -Action Allow -Protocol TCP -LocalPort 2222
```
6. 查看主机地址
在台式机上打开命令提示符，输入 ipconfig，查看 IPv4 地址（如 `192.168.1.100`）

7. final
   在笔记本上打开命令提示符，输入 `ssh username@192.168.1.100 -p 2222`，即可连接到台式机的 WSL。
ps: 可选： 配置SSH 密钥登录