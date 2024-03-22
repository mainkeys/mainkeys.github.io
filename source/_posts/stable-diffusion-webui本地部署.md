---
title: stable-diffusion-webui
date: 2023-02-28 17:51:17
tags: [AI, stable-diffusion-webui]
---

**本文章适用于:**

1. 有一定学习能力和钻研能力，遇到问题能合理使用搜索引擎尝试解决问题的人

2. 想在windows系统中尝试使用AI作画工具stable-diffusion-webui进行绘画的人

3. 有一定的计算机基础（会~~魔法上网~~、~~知道~~ python和Git）和英文阅读能力的人

4. 显卡为Nvidia（或采用CUDA架构），且性能 ≥ GTX1060

5. 对官方文档`https://github.com/AUTOMATIC1111/stable-diffusion-webui`有一定阅读困难的人
   
   > - 本文不提供任何全局代理的教程
   > - 显卡越好作出的画，质量上限越高，最好是能显存在8GB以上
   > - 不一定能列举所有报错情况和所有安装和使用的坑，只
   
   序言：导师有个GPU服务器双3090，常年GPU使用率在个位数，想让它干点活，自己也想拥有一点背景和插画素材，就想着在服务器上装个ai画图，但是由于服务器需要连接学校的远程登陆系统（V**）才能进行远程登录，造成了一定的障碍，就先在本地的环境装一个试试给我的矿卡训练训练，没准就能突破到下一个阶段（30系）了。

**系统和环境：**
操作系统：Windows 11 专业版 22H2
CPU：AMD Ryzen 7 5800X3D 8-Core Processor  3.40 GHz
显卡：2070Super 矿区老兵
内存：16G
如果安装运行错误（瓶颈一般只出现在显卡和网络上）

---

### 正式开始安装

1、首先在python官网下载对应操作系统3.10.* 版本的python，在**安装的过程中勾选上将python加入到PATH**，其他都是默认配置，可以自定义安装在其他磁盘
2、在Git官网安装对应操作系统的最新版Git，很多代码都会调用到git指令进行下载，所以必须安装，可以选择安装在其他磁盘所有选项为默认就行。

3、下载 Stable-Diffusion-webui [【链接地址】](https://github.com/AUTOMATIC1111/stable-diffusion-webui)  Github开源项目并解压

* （可选）[中文语言包](https://github.com/VinsonLaro/stable-diffusion-webui-chinese)
  ![](./1.png)

4、 进入目录找到`webui-user.bat`右键打开编辑，设置python路径，将刚安好的python路径写上去
![](./2.png)
![](./3.png)
5、首先，如果实在国内是无法正常安装程序的，需要通过一些手段（可以魔法＋全局，但我这里尝试失败了）才能进行下载，这里提供一些方法以供参考
我们可以看到`webui-user.bat`里面调用的是`webui.bat` 我们打开`webui.bat`可以看到其实最后用python打开了`launch.py`这个程序，然后通过`pip`和`git`指令安装了一堆所需文件
，所以解决方法就是针对其进行一些设置比如说采用国内镜像手段可以解决大部分问题

6、我们打开`launch.py`进行修改，可以通过记事本也可以通过各类IDE，ctrl+f查找出所有`github.com`并替换为国内镜像`kgithub.com`如果此镜像挂了，可以替换为其他镜像，同样也可以供github代理进行加速，具体参考[githubproxy官网](https://ghproxy.com/)（实际上在地址前面加上一个`https://ghproxy.com/`）就可以了

![](./4.png)
7、设置完双击运行`webui-user.bat`等待下载，一般会在gfpgan、Clip、open_clip的下载卡一会，在下载官方自带的模型包卡一会（文件很大，要下很久），最后是这个样子的，此时命令行窗口在运行的时候不能关闭。
![](./5.png)
8、这时候打开浏览器照着提示输入网址`http://127.0.0.1:7860`就可以进入stable-diffusion-webui界面了

![](./6.png)

9 、AUTOMATIC1111官方是提供了一个基础模型包（现在是v1-5版本）的，可以直接用训练好的模型进行绘画，我们先输入几个正负面提示词尝试一下，这里说明一下，默认设置是每次画完图都会自动保存在stable-diffusion-webui根目录里的outputs里面，可以把它设置为不保存，如果之前装了中文语音包也可以再设置里拉到最下面的locallization改成中文包。

![](./7.png)
![](./8.png)

![](./9.png)

## 到此，你已经可以顺利打开stable-diffusion-webui并运行了，更多详细使用方式和进阶玩法（ 如何下载替换选择其他模型包，如何采用loRA模型训练，如何vea进行面部修复，泽阳通过设置权重混用多个模型进行训练，参数该如何设置，如何获取插件以及配置插件）下次再写。

### 每一次进行GPU的渲染生成的绘图都是独一无二的，版权全归自己所有，终于实现素材自由（~~图片自由~~ ）了。

欢迎大家讨论配置过程中遇到的问题。

参考链接：
https://www.bilibili.com/read/cv20716170
https://www.freedidi.com/8474.html
https://github.com/AUTOMATIC1111/stable-diffusion-webui
https://stable-diffusion-art.com/
