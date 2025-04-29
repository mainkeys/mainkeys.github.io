---
title: leetcode231 - 2 的幂
date: 2025-04-28 21:20:50
tags: [算法,Leetcode,每日手撕]
categories: [算法,每日手撕] 
cover: https://mks-1306588458.cos.ap-nanjing.myqcloud.com/cover11.png
---
### 题目描述
> 给你一个整数 n，请你判断该整数是否是 2 的幂次方。如果是，返回 true ；否则，返回 false 。

  如果存在一个整数 x 使得 n == 2x ，则认为 n 是 2 的幂次方。
  示例 1：
  输入：n = 1
  输出：true
  解释：20 = 1
  示例 2：

  输入：n = 16
  输出：true
  解释：24 = 16
  示例 3：

  输入：n = 3
  输出：false
  提示：
  -231 <= n <= 231 - 1


本质就是判断十进制对应的二进制是否满足有且仅有一个 `1`
```cpp
class Solution {
public:
    bool isPowerOfTwo(int n) {
         return n > 0 && std::bitset<32>(n).count() == 1;
    }
};
```
实际上，一般地，如果 n 是 2 的幂，把 n 减一会使 n 的最高位变成 0，其余低位变成 1，所以 `n&(n−1)=0` 一定成立，即代码也可以写为
```cpp
class Solution {
public:
    bool isPowerOfTwo(int n) {
         return n > 0 && !(n & (n - 1));
    }
};
```
