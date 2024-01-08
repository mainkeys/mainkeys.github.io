---
title: VScode通过ssh连接远程服务器
date: 2023-04-10 17:40:49
tags: ['VScode', 'ssh']
---


### 前言
先说一下，VScode通过ssh连接远程服务器的操作和Linux上配置SSH config和免密登录的操作几乎一致。只不过有一些细微的操作方式可能不太一样，不过基本原理都是一样的，如果熟悉Linux SSH config配置的应该很容易理解本文内容。如果不了解也没关系，同理如果了解了本文的操作也就会在Linux上配置快捷免密登录了。
[这里是Linux配置免密登录的操作指南]()
### 1、确保安装了ssh
先打开终端，这里的终端可以是 cmd || VScode Terminal || PowerShell || macOS Terminal || git bash 的其中一种，输入ssh，出现如下提示则表明已具备ssh

![](./1.png)


### 2、添加插件
VScode安装`Remote-SSH插件`，注意不要看错了
![](./2.png)
安装完后左侧边栏就可以看到`Remote Explorer`图标了
![](./3.png)

### 3、配置SSH密钥
> 如果对密码学的知识具有一定了解，理解起以下内容会更加容易，[这篇文章是公钥和私钥使用的一些理解]()

**1、生成密钥**密钥文件一般生成的路径为`C:\Users\user\.ssh`
如果能在此文件夹下看到![](./4.png)这两个文件说明之前已经生成过ssh密钥对了，直接跳到下一步，如果没有这两个文件，则打开终端输入`ssh-keygen`则会生成密钥。
**2、配置免密登录**之后我们需要将本地公钥上传至目标服务器的`~/.ssh/authorized_keys`里，这个操作等同于免密登录配置时在Linux中输入`ssh-copy-id user@server`
这里的话可以手动复制公钥里的内容（以.pub结尾，开头一般是ssh-rsa），然后登录到远程服务器，粘贴到`~/.ssh/authorized_keys`里，没有这个文件则创建一个，进入`~/.ssh/`里输入`vi authorized_keys`
按`i`进入编辑模式`shift + Insert`粘贴， `Esc`进入命令行模式，输入`:wq`保存，此时配置免密登录成功了，可在本地终端进行ssh登录验证，如果通过`ssh user@server`进行远程登陆不需要进行密码验证则说明配置成功

**3、配置config文件**
此步和Linux中在`~/.ssh/`下对config文件进行修改是同等操作，
点击左侧边栏的`Remote Exporer`然后点击此图标![](./5.png)
接着点击![](./6.png)
此文件的格式为
![](./7.png)
```config
Host <远程主机名称>(自己取)
    HostName <远程主机IP>
    User <用户名>
    Port <ssh端口，默认22>
    IdentityFile <本机SSH私钥路径>
    ForwardAgent yes <VSCode 自己添加的，不用管>
```
保存后，配置就结束了，以后便可以通过VScode SSH直接连接远程服务器了
![](./8.png)
最终我们就可以直接用本地Vscode打开远程服务器的文件夹和文件愉快的进行coding了。
**后话**
登录远程服务器后，可以根据需要从本地移植扩展插件到远程
![](./9.png)
