---
title: leetcode20. 有效的括号
date: 2025-03-23 16:16:23
tags: ['leetcode']
---
![](./image.png)
括号匹配问题即括号消消乐
如果字符串长度为奇数，则必然不能构成有效括号字符串
unordered_map 容器，直译过来就是"无序 map 容器"的意思，unordered_map 容器不会像 map 容器那样对存储的数据进行排序。 `map是基于红黑树实现的，而unordered_map是使用哈希表实现的，查找时间复杂度为O(1)`  **一般有排序需求的话就是用map，如果只会使用到查找功能则使用unordered_map**

unordered_map::count(key) 就是查看是否有该键值对，因为unordered_map没有重复元素，
C++20提供了unordered_map::find()
```cpp
class Solution {
public:
    bool isValid(string s) {
        if(s.size() % 2) return false;
        unordered_map<char, char> pairs = {
            {')', '('},
            {']', '['},
            {'}', '{'}
        };
        stack<char> stk; // 栈用来存储左括号进行消消乐
        for(char c:s) {
            // 若匹配到了右括号
            if(pairs.count(c)) {// 也可以是pairs.find(c) != pairs.end()
            // 若栈为空或此时栈顶不能匹配该右括号即stk.top() != pairs[c]
                if(stk.empty() || stk.top() != pairs[c]) return false;
                stk.pop();
            } else { // 若是左括号
                stk.push(c);
            }
        }
        return stk.empty(); // 栈中还剩余则返回false， 栈为空则为true
    }
};
```