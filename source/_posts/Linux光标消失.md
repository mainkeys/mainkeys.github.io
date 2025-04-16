---
title: Linux光标消失
date: 2023-04-13 16:32:02
tags: [Linux]
cover: https://mks-1306588458.cos.ap-nanjing.myqcloud.com/cover4.png
---

### 在Linux中隐藏光标
```shell
echo -e "\033[?25l"
```
### 在Linux中显示光标
```shell
echo -e "\033[?25h"
```
