---
title: 腾讯云轻量级服务器Valheim英灵神殿服务器搭建
date: 2023-02-03 06:09:01
tags: [Linux]
---
### 云服务器搭建游戏私服
一开始是朋友想自己建个服务器一起玩游戏，无奈如果使用某人主机当服务器的话，只要他关机了其他人都不能玩，而且作为服务器的主机需要一定的配置要求，并且这种方式会有很大的延迟波动，所以考虑到使用云服务器来搭建游戏服务器，最终选择了腾讯云的轻量级服务，这么便宜的价格感觉是赚到了。![](./1.png)

##### 服务器配置
我首选的2核4G带宽6M，玩英灵神殿足够了


![](./2.png)
服务器开好，直接开搞
这里我选择了使用linux系统搭建，使用linuxGSM管理
系统选的Ubuntu20.04LTS
设置防火墙允许UDP和TCP访问，端口为2456-2458，改完密码后就直接用ssh登录
##### ssh登录
使用MobaXterm直接搞
使用Xshell配合xftp一起食用（个人不太习惯）
登陆后
#更新服务器系统软件
`sudo dpkg --add-architecture i386`
`sudo apt -y update`
`sudo apt -y upgrade`
#添加32位支持库
`sudo apt -y install libsdl2-2.0-0:i386`
#安装steamcmd等相关支持（这里是一句完整代码）

`sudo apt -y install curl wget file tar bzip2 gzip unzip bsdmainutils python util-linux ca-certificates binutils bc jq tmux netcat lib32gcc1 lib32stdc++6 steamcmd`
![](./3.png)
![](./4.png)
#创建一个新用户vhserver，用来专门运行英灵神殿服务器
`sudo adduser vhserver`
`su - vhserver`
#cd进入目录
#这是下载LinuxGSM（LG）创建器
`wget -O linuxgsm.sh https://linuxgsm.sh`
#给你的创建器赋予运行权限
`chmod +x linuxgsm.sh`
#运行创建器，创建一个叫vhserver的文件，这就是你的服务器控制软件，对你来说就是LG的本体
`bash linuxgsm.sh vhserver`
#运行LG本体中的安装程序，下载补全LG，会出现一个这种企鹅，会要你输入很多Y+回车，你等着输入就好了，别忘了要点一下黑色界面再输入
`./vhserver install`
#全绿色就对了，可惜我这里报了许多红ERROR，可能github服务器波动了，重启云服务器尝试也失败，没办法，身在蔷内只能认命。还是不甘心，不想等其他时间段搞，想一次弄完，然后想给服务器挂个梯子继续访问，我觉得没有问题能难道我。
### 开始寻找科学上网之路
##### 环境要求
1. 连接网络的linux
2. 代理，非SS，而是SSR，否则因兼容性导致无效
3. git
4. python3
#下载git
` sudo apt-get install git`
#下载vim
sudo apt-get install vim
配置git
#下载ssr
`git clone https://github.com/ssrbackup/shadowsocksr`
报错了，说是2021年8月13号之后不再支持密码认证登录，无奈只好另找方法

![](./5.png)
#配置完ssh密钥后试着采用ssh密钥登陆结果成功
![](./6.png)
#再git clone试一下，还是失败，再换个方式使用令牌下载
打开github，找到Setting，最后Developer setting
![](./7.png)
添加一个令牌就可以通过git clone `https://<TOKEN>@github.com/<user_name>/<repo_name>.git`

下载了。
#没弄好，发现python可以直接pip一个shadowsocksr，不得不说python真铜模强大。![ ](./9.png)
#在科学上网工具配置的过程中，又测试了一下服务器的安装补全
直接输入`./vhserver install`，又报错了‘’‘’‘
显示版本Ubuntu20.04不支持vhserver服务器。。
重装系统Ubuntu18.04LTS，重复上述步骤
勾⑧腾讯云轻量服务器国内机器无法使用Github，改了hosts，再试一次
![](./10.png)

终于成功了，燃起来了！
![](./11.png)
虽说一堆ERROR，但是不要紧，我持最大信任态度相信它能跑起来
![](./12.png)
功夫不负有心人，搞好了，设置配置文件，开服关服，生成存档文件，然后替换存档, 调整mods兼容性
#设置虚拟内存
#查看内存
`free`
`free -m`

#在var下常见swapfile文件
`touch /var/swapfile`

#设置4G内存，一般为物理内存的两倍
`dd if=/dev/zero of=/var/swapfile bs=1M count=4096`

#查看设置的内存
`du -sh /var/swapfile`

#格式化交换文件
`mkswap /var/swapfile`

#启用交换文件
`swapon /var/swapfile`

#执行完上面命令报错  **mkswap: /var/swapfile: insecure permissions 0644, 0600 suggested.**
#执行完上面如果报错  执行一下命令，否则就忽略
`chmod 0600 /var/swapfile`

#重新执行
`swapon /var/swapfile`

#开机自动加载虚拟内存
`vi /etc/fstab`
最后一行加上`/var/swapfile swap swap defaults 0 0`

#重启
reboot

#重启完成过后使用free -m 命令来查看现在的内存是否挂在上了
`free -m `
![](./13.png)
#开玩!
[](./14.png)
