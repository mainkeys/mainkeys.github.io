---
title: unix学习
date: 2021-09-11 19:32:43
tags: unix
categories: 笔记
---

登录：
telnet ip地址
Login：username
Password：

常用shell：
CShell,Kshell,Bshell





# 常用命令
- `dir` 显示当前信息
 - `whoami` 显示当前用户
- `ls *.c`   查找当前目录得.c文件

---


windows和dos的内部命令：`dir, cls, cd, copy, d el, date, md......`
windows和dos的外部命令：`format, fdisk, xcopy, ping`

unix内部: `ls, cp, cd, pwd, date......` (为shell程序的一部分，
由shell程序识别，并在shell中完成运行)

unix外部 :` gzip, cc, telnet, ftp` (是一些实用程序，系统启动不会加载到内存当中
运行时才需要调入内存)

--- 

几种不同的shell： B-，K-，C-shell:
B-它是UNIX最初使用的Shell并且在每种UNIX 上都可以使用。BShell在Shell编程方面相当优秀，但在处理与用户的交互方面作得不如其他几种Shell
C-它更多的考虑了用户界面的友好性,普遍认为Cshell的编程接口做的不如 BShell，但C Shell还是被很多C程序员使用,因为C Shell的语法和C语言很相似，这也是C Shell名称的由来;
K-它集合了C Shell和B Shell的优点并且和 BShell完全兼容。

---

多命令行，多行命令:
多命令行：`pwd; who; ls -l`
多行命令：用 \ 表示命令还未结束

---

系统关闭
- `reboot`：系统重新引导
`halt/ shuntdowm`: 系统关闭
`poweroff`： 系统关闭

- `passwd [username]` ：修改指定用户的密码，参数为空表示修改当前用户密码

- `su [- username] `：进行用户切换，参数为空表示切换为root用户
\# root用户
& 普通用户

- `cat [-AbET]` 将指定文件标准输出上显示 
-A显示所有控制符 
-b显示行号 
-E每一行结束显示行结束标志
cat可以改变输出流 `cat file1.txt flie2.txt>file3.txt`
`cat >file3.txt`    ：输出键入的键盘内容

- `pwd` 显示用户当前的工作目录 

ctlr+D结束

- cd：
`cd` 切换到主目录
`cd /usr/bin`
`cd ..` 上一级

- `ls`
`ls [-al] [dir/file]`
`-a` 列出当前所有文件 包含隐藏文件
`-l` 以长列表的形式显示详细信息
`[dir/file]`为空表示显示当前的文件
例：
`$ ls -la`
`-rw- r-- r-- 4 list list 4096 Oct 8 .`
`d rwx r-x r-x 4 root root 4096 Sep 12 ..`
`d rwx rwx r-x 2 list list 4096 Oct 8 aa`
用户访问权限 连接数 文件属主名 文件属组名 大小 修改日期 文件名


- `chmod` 用来修改指定文件或目录的访问权限
两种格式：   用符号标记进行更改   采用8进制指定新的访问权限
`chmod [ugoa][+ - =][rwx]  file/dir`
    指定用户组  +添加 -减少权限 =设置某些权限 rwx可读可写可执行 文件名/目录名
u 表示文件的属主user   o 表示其他的所有用户other user 
g 表示与文件属主同一个组的别的用户group user
例
`chmod ug+rx f1` 对属主及其同组增加可读可执行权限
`chmod g-x f2`  对同组其他用户减少执行的权限
采用8进制指定新的访问权限：
三个二进制表示用户的权限，每一位分别表示r, w, x
110：可读可写不可执行
三个八进制表示ugo三种用户的权限
777 表示三种用户都有 可读可写可执行
711 表示u用户又读写权限， 其他用户只有执行的权限
例：
`chmod 700 file2` 表示只有文件属主能读写读写执行该文件

- `cp -ir source dest`
进行拷贝-i 若文件存在，提示是否覆盖
-r 拷贝指定目录中的全部内容
例：
`cp aa.txt aaaa.txt`
`cp -r /home/list/src /home/root`

- `man` 命令名
查看该命令的使用说明和使用方法

- `who` 列出当前登录上操作系统的用户信息
`-h` 能显示用户信息每列的标题

- `cal -hmy [month [year] ]`
`-h` 单个月的日历 -m显示日历时将Monday作为每个星期第一天
`-y` 显示全年的日历

- `mkdir [-P] dirname` 
-p创建一个完整的目录结构，可以一次性建立多层目录结构

- `rmdir dirname` 用于删除一个目录

- `chgrp` 组名 文件名   用于改变用户组
`chgrp root file2.c`
![](./1.png)

- `chown` 用户名 文件名    改变指定文件的所属用户
![](./2.png)


- `ln -f-s  file target`创建快捷方式
`-f` 若存在则覆盖 否则创建
`-s` 只包含一个指向源文件的指针
![](./3.png)
![](./4.png)

- `cut` 按列或按域截取输入行中所指的内容
`cut [- c -f -d] list  [flie ]`
`-c` 按字符截取
![](./5.png)
`-f` 按域截取  默认为单词 间隔符号为tab
`-d` 按域截取 同时指定间隔符  间隔符跟在-d后面
![](./6.png)
![](./8.png)



- `find` 根据一定的条件查找文件 -a(and)或者-o(or)的逻辑关系 
`-name filename` 以文件名进行查找
`-type x` 以x类型的文件， x目前可取值有d(目录) f(文件)
`-user username` 查找属主为username的文件
`-atime n` 查找n天前被访问过的文件
`-mtime n` 查找n天前被修改的文件
对找到的文件还可以执行一些操作
`-print` 显示找到的文件的路径名称
`-exec Command{}` 执行一个命令，命令必须用 \\;结束
![](./8.png)
查找3天前被访问过的名称为core或者dump的文件并删除
()括号需要转义，最后的\\为多命令行换行符

- `grep  -c -i -l -L -n`按照指定的选项在指定的文件中搜索特定的内容
`-c` 打印匹配的行号
`-i` 模式不区分大小写
`-l` 只显示包含指定模式的文件名
`-L` 只显示不包含指定模式的文件名
`-n` 同时显示行号
![](./9.png)



- `tar` 储存或展开tar存档文件
![](./10.png)

---
- ![](./11.png)
---

- `ps`
 ![](./12.png)
![](./13.png)

- `df`
![](./14.png)
![](./15.png)

- `ftp`
  ![](./16.png)
![](./17.png)
- `telnet & ping`
![](./18.png)


- 访问其他文件系统
![](./19.png)
![](./20.png)

- 访问USB文件系统
![](./21.png)

- 访问光驱文件系统
![](./22.png)
