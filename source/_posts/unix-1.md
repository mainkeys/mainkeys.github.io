---
title: unix学习2
date: 2021-09-18 12:02:22
tags: unix
categories: 笔记
cover: http://sunowc60i.hd-bkt.clouddn.com/cover7.png
---

# Unix中的编辑器

- 常用的编辑工具
- [x] ed：早期的UNIX系统中的行编辑器
- [x] ex：ed的替代产品
- [x] edit：ex的简化版本
- [x] vi：全屏幕编辑器，在ex上发展改进而来的
- [x] Emacs：可视化文本编辑环境
- [x] xemacs：可视化编辑工具，具有图形用户界面

这里主要以学习vi为主

--- 

![](./1.png)
### vi编辑器
vi三种模式
- 命令行方式：用户进入vi后的初始方式。
- 插入编辑方式：要使用vi的“i”“a”等命令进行切换，点击ESC键返回命令行方式。主要是在编写的文件中添加或输入文本及程序代码。
- 末行命令方式：命令输入出现在屏幕的最底部，命令输入完之后，vi自动返回到命令行方式。


如果希望在进入 vi 后，光标处于文件中特定的某行上，可在 vi 命令上加上行号和文件名，其格式如下：
`vi +行号  文件名`
#### 命令行方式下的常用命令
使vim进行输入模式的方式是在命令模式状态下输入i、I、a、A、o、O等插入命令（各指令的具体功能下表所示），当编辑文件完成后按esc键即可返回命令模式。
- i	在当前光标所在位置之前插入随后输入的文本，光标后的文本相应向右移动
- I	相当于光标移动到行首执行 i 命令
- o	在光标所在行的下面插入新的一行。光标停在空行首，等待输入文本
- O	在光标所在行的上面插入新的一行。光标停在空行的行首，等待输入文本
- a	在当前光标所在位置之后插入随后输入的文本
- A	相当于光标移动到行尾再执行a命令
- x 删除当前光标所在处的字符。
![](./2.png)
![](./3.png)

![](./4.png)


![](./5.png)
![](./6.png)
#### 编辑模式下的常用命令
![](./7.png)

#### 一般模式切换到指令行模式的可用的按钮说明
![](./8.png)
`ZZ`是修改过才保存，`:wq`是一定保存一次
![](./9.png)
出处：https://www.runoob.com/linux/linux-vim.html![](./10.png)

![](./11.png)
![在这里插入图片描述](./12.png)
![](./13.png)

![](./14.png)
### Shell的基本功能
- 命令的解释执行，接受用户的命令输入、解释分析执行用户命令
- 环境变量的设置
- 输入/输出的重定向管理：实现对系统标准流的修改
- Shell程序的设计

### B、C、K Shell的区别
![](./15.png)
### Unix系统定义的标准流及重定向方法
`< > >>，>>为追加，`等符号改变标准流的方向

--- 
# Shell程序设计

### Shell程序执行
![](./16.png)

- & `sh test.sh`
- & `sh <test.sh` (重定向方式输入)
- & `./test.sh`或`path/test.sh` (需要修改权限`chmod a+x test.sh`)
- & `. test.sh` 或 `source test.sh`


### Shell变量使用
shell 变量定义由字母开始，可以包含数字，字母和下划线。
##### Shell中引号说明
- `''`全部当作字符串信息处理  ：
   ![](./17.png)

### Shell中命令的位置变量
![](./18.png)
### shell中变量的替换
![](./19.png)
### test命令的使用
在shell中经常要对某些变量的值进行判断来决定分支程序的走向，如同C中使用 if( a == 0) 一样。Shell中通过test命令来完成这个功能。
`test expre`或者`test [expre]`
`test [-dfrwxs] file`
     -d  file : 文件file存在并且为目录文件
     -f  file：文件file存在并且为 普通文件
     -r  file: 文件file存在并且为可读文件
     -w  file: 文件file存在并且为可写文件
     -x  file: 文件file存在并且为可执行文件
     -s  file: 文件file存在并且文件长度为非0
     ![](./20.png)
### 条件控制语句
(1)if语句
分为无分支、二分支和多分支条件语句。

- 无分支条件语句
![](./21.png)

- 二分支条件语句
![](./22.png)
- 多分支语句
- ![](./23.png)
# Shell编程示例
![](./24.png)
```bash
   # showCfile.sh
  if test -d $HOME/a_sub
   then
     echo "-- the .c and .obj files in $HOME/a_sub: －-"
     for filename in `ls $HOME/a_sub`
     do
       case $filename in
        *.c)   echo $filename;;
        *.obj)  echo $filename;;    
       esac
     done
   else
     echo "$HOME/a_sub does not exist!!"
   fi 
if test -d $HOME/b_sub
   then
     echo "--- the .c and .obj files in $HOME/b_sub: ---"
     for filename in `ls $HOME/b_sub`
     do
       case $filename in
        *.c)   echo $filename is a C source file!;;
        *.obj)  echo $filename is an Object file!;;    
       esac
     done
   else
     echo "$HOME/b_sub does not exist!!"
   fi
```
![](./25.png)
```bash
while [test -r abc.txt]
   do
    echo "file abc.txt has not beed deleted !“
    sleep 10
   done
   echo "file abc.txt has beed deleted !"

```
![](./26.png)
```bash
count=0
   while read LINE
   do
    count=`expr $count + 1`
   done < file
   echo $count
   
   或者 cat file | wc -l
```

![](./27.png)
```bash

case $# in
     1) cat >> $1;;
     2) cat <$1 >>$2;;
     3) cat $1 $2 >>$3;;
     *) echo "To many param"
   esac

if [test $# -eq 1 ]
  then
   cat>>$1
  elif $#=2
   then
    cat <$1 >>$2
  elif $#=3
   then
    cat $1 $2 >>$3
  else
    echo “error”
  fi

```

![](./28.png)
![](./29.png)
```bash
echo
  echo "--- Disk Usage Condition ---"
  
  used_disk=`du -s /home | cut -f1`
  echo "Used Blocks:  $used_disk"
  
  free_disk=`df | head –2 |tail -1 | tr -s "[ ]" | cut -f4 -d" "`
  echo "Free Blocks:  $free_disk"
  
  total_disk=`expr $used_disk + $free_disk`
  echo "total blocks:$total_disk"
  
  echo
  echo "--- disk usage ratio ---"
  #计算出磁盘的利用率
  ratio=`echo "scale=6; $used_disk*100/$total_disk" | bc`
  echo -e "usage ratio: $ratio%"
  
  if [ `expr "$ratio < 50"` ]
   then
    echo "用户文件系统磁盘使用负荷小"
   elif [ `expr "$ratio > 90"`]
   then 
    echo "用户文件系统磁盘使用负荷偏大"
   else
    echo "用户文件系统磁盘使用负荷正常" 
  fi
  echo
```
![](./30.png)
```bash
echo  -e "Please enter the score:"
  while read SCORE
  do
    case $SCORE in
     ?|[1-5]? ) echo "Failed!"
                echo "Please enter the next score:";;
     6?)        echo "Passed!"
                echo "Please enter the next score:";;
     7?)        echo "Medium!"
                echo "Please enter the next score:";;
     8?)        echo "Good!"
                echo "Please enter the next score:";;
     9?|100)    echo "Great!"
                echo "Please enter the next score:";;
     *)         exit;;
    esac  
  done
```
![](./31.png)
```bash
#!/bin/sh
   #Averaterscore.sh
   SCORE1=0
   SCORE2=0
   SCORE3=0
   NUMBER1=0
   NUMBER2=0
   NUMBER3=0
   
   SAVED_IFS=$IFS
   IFS=:
   INPUT_FILE=score.txt
   
while read NAME CLASS SCORE   #循环读入各行
   do
    case $CLASS in
     class1) NUMBER1=`expr $NUMBER1+1`
             SCORE1=`expr $SCORE1+$SCORE`;;
     class2) NUMBER2=`expr $NUMBER2+1`
             SCORE2=`expr $SCORE2+$SCORE`;; 
     class3) NUMBER3=`expr $NUMBER3+1`
             SCORE3=`expr $SCORE3+$SCORE`;;          
     *)      echo "`basename $0`:Unknow class $CLASS" ;;
    esac
   done  < INPUT_FILE
#开始计算平均分数
   SCORE1=`echo "scale=2; $SCORE1/$NUMBER1" | bc`
   SCORE2=`echo "scale=2; $SCORE2/$NUMBER2" | bc`
   SCORE3=`echo "scale=2; $SCORE3/$NUMBER3" | bc`
   
   #显示计算的结果
   echo "  class       student num          average score"
   echo "===================================================="
   echo "    1           $NUMBER1             $SCORE1"
   echo "    2           $NUMBER2             $SCORE2"
   echo "    3           $NUMBER3             $SCORE3"
   IFS=$SAVED_IFS
```
![](./33.png)

```bash
ans=y
until [ "$ans" = n ]
do
echo "Enter a Student number:"
read  number
echo  The inputed number is:${number}

count=`grep ${number} score.dat | wc -l`
echo the Count found is ${count}
if test "$count" -eq 1
then
score=`grep ${number} score.dat | cut -d\| -f2`
echo The score is: ${score}
else
echo "Can not found this number !!"
fi

echo "Continue?"
echo "Enter y(yes) or n(no)"
read ans
done
```
