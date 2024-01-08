---
title: git报错errno 10054
date: 2021-09-10 12:33:21
tags: [踩坑,git,github]
categories: [踩坑]
---
昨天还可以git push代码到远程仓库，今天使用hexo d上传git仓库是时报了这个错：fatal: unable to access 'https://github.com/.......': OpenSSL SSL_read: Connection was reset, errno 10054
![](https://img-blog.csdnimg.cn/0913af988d1c42539d611a0681cba738.png?process=image/watermark,type_ZHJvaWRzYW5zZmFsbGJhY2s,shadow_50,text_Q1NETiBAajogKQ==,size_20,color_FFFFFF,t_70,g_se,x_16)


产生原因：一般是这是因为服务器的SSL证书没有经过第三方机构的签署，所以才报错

参考网上解决办法：解除ssl验证后，再上传就OK了
`git config --global http.sslVerify "false"`
![](https://img-blog.csdnimg.cn/f389967d3ce94127b09feb5ee55a3e1c.png?process=image/watermark,type_ZHJvaWRzYW5zZmFsbGJhY2s,shadow_50,text_Q1NETiBAajogKQ==,size_20,color_FFFFFF,t_70,g_se,x_16)
