---
title: hexo使用七牛图床 放到github pages上无法显示
date: 2025-04-16 22:37:22
tags: [hexo, github]
---

> 问题的根源在于 浏览器 ， 在https的网站里面放http格式的图片，那么http的链接会被自动转为https，从而导致找不到链接，会出现图片无法显示的情况

### 解决方案：
换`腾讯云COS` or `阿里云OSS`
