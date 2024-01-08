---
title: ES5标准
date: 2023-03-26 14:44:42
tags: [JavaScript, ES5]
---

```html
<!DOCTYPE html> 
<html>

<body>

    <h2>JavaScript 能做什么</h2>

    <p id="demo">JavaScript 能够改变 HTML 内容。</p>

    <!-- 改变HTML内容 -->
    <button type="button" onclick='document.getElementById("demo").innerHTML = "Hello JavaScript!"'>点击我！</button>

    <!-- 改变img的src -->
    <button onclick="document.getElementById('myImage').src='/i/eg_bulbon.gif'">开灯</button>
    <img id="myImage" border="0" src="/i/eg_bulboff.gif" style="text-align:center;">
    <button onclick="document.getElementById('myImage').src='/i/eg_bulboff.gif'">关灯</button>

    <!-- 改变样式 -->
    <button type="button" onclick="document.getElementById('demo').style.fontSize='35px'">
        点击我！
    </button>

    <!-- 隐藏HTML元素 style.display='none'  显示.style.display='block'-->
    <button type="button" onclick="document.getElementById('demo').style.display='none'">
        点击我！
    </button>
</body>

</html>

```