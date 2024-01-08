---
title: unix学习2
date: 2021-09-18 12:02:22
tags: unix
categories: 笔记
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

![](https://img-blog.csdnimg.cn/8b30500059c249a4843d11edf7393a39.png?process=image/watermark,type_ZHJvaWRzYW5zZmFsbGJhY2s,shadow_50,text_Q1NETiBAajogKQ==,size_20,color_FFFFFF,t_70,g_se,x_16)
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
![](https://img-blog.csdnimg.cn/594bed31d67c4b0db4a7d75921f2de71.png?process=image/watermark,type_ZHJvaWRzYW5zZmFsbGJhY2s,shadow_50,text_Q1NETiBAajogKQ==,size_20,color_FFFFFF,t_70,g_se,x_16)
![](https://img-blog.csdnimg.cn/d9cd5d19d32a428cb4e575efd0ade5b4.png?process=image/watermark,type_ZHJvaWRzYW5zZmFsbGJhY2s,shadow_50,text_Q1NETiBAajogKQ==,size_20,color_FFFFFF,t_70,g_se,x_16)

![](https://img-blog.csdnimg.cn/ee4907a554f44c50b101320bbecb2142.png?process=image/watermark,type_ZHJvaWRzYW5zZmFsbGJhY2s,shadow_50,text_Q1NETiBAajogKQ==,size_20,color_FFFFFF,t_70,g_se,x_16)


![](https://img-blog.csdnimg.cn/18a05b612e5c4ffb80fabdaab06ea48f.png?process=image/watermark,type_ZHJvaWRzYW5zZmFsbGJhY2s,shadow_50,text_Q1NETiBAajogKQ==,size_20,color_FFFFFF,t_70,g_se,x_16)
![](https://img-blog.csdnimg.cn/599d6f1afb134ee39f9b44bc74168313.png?process=image/watermark,type_ZHJvaWRzYW5zZmFsbGJhY2s,shadow_50,text_Q1NETiBAajogKQ==,size_20,color_FFFFFF,t_70,g_se,x_16)
#### 编辑模式下的常用命令
![](https://img-blog.csdnimg.cn/daec1088c62145ae84bddebbd70dafdd.png?process=image/watermark,type_ZHJvaWRzYW5zZmFsbGJhY2s,shadow_50,text_Q1NETiBAajogKQ==,size_20,color_FFFFFF,t_70,g_se,x_16)

#### 一般模式切换到指令行模式的可用的按钮说明
![](https://img-blog.csdnimg.cn/e3600e11d8fc4d24b1964b8fd02e6445.png?process=image/watermark,type_ZHJvaWRzYW5zZmFsbGJhY2s,shadow_50,text_Q1NETiBAajogKQ==,size_20,color_FFFFFF,t_70,g_se,x_16)
`ZZ`是修改过才保存，`:wq`是一定保存一次
![](https://img-blog.csdnimg.cn/3df89d2473dc4d39975590561e143101.png)
出处：https://www.runoob.com/linux/linux-vim.html![](https://img-blog.csdnimg.cn/c4159697aa484927a8db2398a664f10a.png?process=image/watermark,type_ZHJvaWRzYW5zZmFsbGJhY2s,shadow_50,text_Q1NETiBAajogKQ==,size_20,color_FFFFFF,t_70,g_se,x_16)

![](https://img-blog.csdnimg.cn/cce7aed28fd045e6ad53d8094a052e91.png?process=image/watermark,type_ZHJvaWRzYW5zZmFsbGJhY2s,shadow_50,text_Q1NETiBAajogKQ==,size_20,color_FFFFFF,t_70,g_se,x_16)
![在这里插入图片描述](https://img-blog.csdnimg.cn/f6fb971fc2444585bb72205638e534ab.png?process=image/watermark,type_ZHJvaWRzYW5zZmFsbGJhY2s,shadow_50,text_Q1NETiBAajogKQ==,size_20,color_FFFFFF,t_70,g_se,x_16)
![](https://img-blog.csdnimg.cn/a263841b9fdf4eb49c31dfeebbb7eed8.png?x-oss-process=image/watermark,type_ZHJvaWRzYW5zZmFsbGJhY2s,shadow_50,text_Q1NETiBAajogKQ==,size_20,color_FFFFFF,t_70,g_se,x_16)

![](https://img-blog.csdnimg.cn/94a8024913b34d16bafe07fca4852446.png?process=image/watermark,type_ZHJvaWRzYW5zZmFsbGJhY2s,shadow_50,text_Q1NETiBAajogKQ==,size_20,color_FFFFFF,t_70,g_se,x_16)
### Shell的基本功能
- 命令的解释执行，接受用户的命令输入、解释分析执行用户命令
- 环境变量的设置
- 输入/输出的重定向管理：实现对系统标准流的修改
- Shell程序的设计

### B、C、K Shell的区别
![](https://img-blog.csdnimg.cn/4166ed3902434d158372e900e0e07d12.png?process=image/watermark,type_ZHJvaWRzYW5zZmFsbGJhY2s,shadow_50,text_Q1NETiBAajogKQ==,size_20,color_FFFFFF,t_70,g_se,x_16)
### Unix系统定义的标准流及重定向方法
`< > >>，>>为追加，`等符号改变标准流的方向

--- 
# Shell程序设计

### Shell程序执行
![](https://img-blog.csdnimg.cn/4679b124a005463094a0ce81fd584f56.png?process=image/watermark,type_ZHJvaWRzYW5zZmFsbGJhY2s,shadow_50,text_Q1NETiBAajogKQ==,size_20,color_FFFFFF,t_70,g_se,x_16)

- & `sh test.sh`
- & `sh <test.sh` (重定向方式输入)
- & `./test.sh`或`path/test.sh` (需要修改权限`chmod a+x test.sh`)
- & `. test.sh` 或 `source test.sh`


### Shell变量使用
shell 变量定义由字母开始，可以包含数字，字母和下划线。
##### Shell中引号说明
- `''`全部当作字符串信息处理  ：
   ![](https://img-blog.csdnimg.cn/461b1ecf56a4424a9289fe812916e6f2.png?process=image/watermark,type_ZHJvaWRzYW5zZmFsbGJhY2s,shadow_50,text_Q1NETiBAajogKQ==,size_20,color_FFFFFF,t_70,g_se,x_16)

### Shell中命令的位置变量
![](https://img-blog.csdnimg.cn/156d57b497d74ff9a72e68f743e951e8.png?process=image/watermark,type_ZHJvaWRzYW5zZmFsbGJhY2s,shadow_50,text_Q1NETiBAajogKQ==,size_20,color_FFFFFF,t_70,g_se,x_16)
### shell中变量的替换
![](https://img-blog.csdnimg.cn/12b185ba540745038da9772c2de16161.png?process=image/watermark,type_ZHJvaWRzYW5zZmFsbGJhY2s,shadow_50,text_Q1NETiBAajogKQ==,size_20,color_FFFFFF,t_70,g_se,x_16)
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
     ![](https://img-blog.csdnimg.cn/1fc264055fcc43e58c4b2056f7d6d94e.png?process=image/watermark,type_ZHJvaWRzYW5zZmFsbGJhY2s,shadow_50,text_Q1NETiBAajogKQ==,size_20,color_FFFFFF,t_70,g_se,x_16)
### 条件控制语句
(1)if语句
分为无分支、二分支和多分支条件语句。

- 无分支条件语句
![](https://img-blog.csdnimg.cn/cc682da617914928afab9b442bbf3961.png)

- 二分支条件语句
![](https://img-blog.csdnimg.cn/60a67d9f42f34319a7fd39ee56db360c.png)
- 多分支语句
- ![](https://img-blog.csdnimg.cn/5b6d9b43f31241e189e4d9251cdd7ee1.png?process=image/watermark,type_ZHJvaWRzYW5zZmFsbGJhY2s,shadow_50,text_Q1NETiBAajogKQ==,size_17,color_FFFFFF,t_70,g_se,x_16)
# Shell编程示例
![](https://img-blog.csdnimg.cn/8e57f6b33d914d0c9191249c59924c06.png)
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
![](https://img-blog.csdnimg.cn/84667a096402429a9325ebe344236bbf.png)
```bash
while [test -r abc.txt]
   do
    echo "file abc.txt has not beed deleted !“
    sleep 10
   done
   echo "file abc.txt has beed deleted !"

```
![](https://img-blog.csdnimg.cn/707176254f974ae9b875abe982221fe3.png)
```bash
count=0
   while read LINE
   do
    count=`expr $count + 1`
   done < file
   echo $count
   
   或者 cat file | wc -l
```

![](https://img-blog.csdnimg.cn/7d61f5071fbb4425a3d6b658161ce39c.png?process=image/watermark,type_ZHJvaWRzYW5zZmFsbGJhY2s,shadow_50,text_Q1NETiBAajogKQ==,size_20,color_FFFFFF,t_70,g_se,x_16)
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

![](https://img-blog.csdnimg.cn/e7db13f0d6d446599a7ed8e855fdf949.png?process=image/watermark,type_ZHJvaWRzYW5zZmFsbGJhY2s,shadow_50,text_Q1NETiBAajogKQ==,size_20,color_FFFFFF,t_70,g_se,x_16)
![](https://img-blog.csdnimg.cn/988d7bbabba94c838963b1242fe65434.png?process=image/watermark,type_ZHJvaWRzYW5zZmFsbGJhY2s,shadow_50,text_Q1NETiBAajogKQ==,size_20,color_FFFFFF,t_70,g_se,x_16)
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
![](https://img-blog.csdnimg.cn/ab943cf600354601b07079f9e1af9533.png)
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
![](https://img-blog.csdnimg.cn/79b45f262d504f11bdaaa5fd0b2e9c70.png)
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
![](https://img-blog.csdnimg.cn/79fc6f5ecc764e669de3066ef1116f44.png?process=image/watermark,type_ZHJvaWRzYW5zZmFsbGJhY2s,shadow_50,text_Q1NETiBAajogKQ==,size_20,color_FFFFFF,t_70,g_se,x_16)

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
欢迎大家放我我的个人博客[mainkeys.github.io](https://mainkeys.github.io)