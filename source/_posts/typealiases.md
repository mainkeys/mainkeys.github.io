---
title: 报错Could not resolve type alias ‘‘
date: 2021-09-13 23:25:28
tags: MyBatis
categories: 踩坑
top: false
cover: https://mks-1306588458.cos.ap-nanjing.myqcloud.com/cover6.png
---

看到这个问题，很可能以为是实体类未在mybatis-config.xml中配置别名（alias）导致的，所以加上这段代码

```xml
<typeAliases>
<!-- 通过package, 可以直接指定package的名字， mybatis会自动扫描你指定包下面的javabean,
      并且默认设置一个别名，默认的名字为： javabean 的首字母小写的非限定类名来作为它的别名。
      也可在javabean 加上注解@Alias 来自定义别名， 例如： @Alias(user) 
      <package name="com.dy.entity"/>
       -->
	<typeAlias type="com.test.domain.Student" alias="student"/> 
</typeAliases>
```
![](./1.png)
可以看到代码生效了。