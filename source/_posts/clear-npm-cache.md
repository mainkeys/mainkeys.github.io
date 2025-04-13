---
title: 清除npm缓存重新安装npm依赖
date: 2024-02-28 23:10:55
tags: ['前端', 'npm']
categories: 技术
cover: http://sunowc60i.hd-bkt.clouddn.com/cover6.png
---

### 最近在运行前端项目时遇到如下报错
```
npm ERR! code ELIFECYCLE
npm ERR! errno 1
npm ERR! lianshan@2.0.0 serve: `vue-cli-service serve`
npm ERR! Exit status 1
npm ERR! 
npm ERR! Failed at the lianshan@2.0.0 serve script.
npm ERR! This is probably not a problem with npm. There is likely additional logging output above.

npm ERR! A complete log of this run can be found in:
npm ERR!     /Users/xxx/.npm/_logs/2024-03-15A53_03_05_072Z-debug.log

```

原因时node_modules依赖出了问题，这种时候重新安装依赖包是最好的方法，谁知道哪个依赖包多了哪个依赖包少了呢？重新来过最稳妥。
其余npm报错有时也可用这种方法进行实验

### 解决方法
1、删除node_modules文件夹

2、文件夹下运行`npm cache clean --force`命令清除npm缓存

3、`npm i`重新下载依赖包

4、再尝试重启项目即可
