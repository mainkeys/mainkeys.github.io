---
title: leetcode1305二叉搜索树
date: 2022-05-16 21:20:50
tags: [算法,Leetcode,每日手撕]
categories: [算法,每日手撕] 
cover: https://mks-1306588458.cos.ap-nanjing.myqcloud.com/cover11.png
---
### 题目描述

![](./1.png)
> 此题需要熟悉二叉搜索树的一个性质，二叉搜索树中序遍历出的数组是有序数组，因此使用中序遍历两个二叉搜索树后就将问题转化为了将两个有序数组合并

##### 中序遍历代码：
```cpp
void inorder(TreeNode *root, vector<int>& res){
        if(!root) return;
        inorder(root->left, res);
        res.push_back(root->val);
        inorder(root->right, res);
    }
```
### 合并两个有序数组时使用的方法可以很多种，常见的有暴力排序和双指针方法（归并排序），归并排序本质上就是双指针。
#### 暴力
直接将数组拼接后sort
#### 双指针（这里的细节实现可以有好几种，以下三种较为实用，有助于拓展思路）
##### ①
```cpp
 vector<int> getAllElements(TreeNode* root1, TreeNode* root2) {
        int INF = 0x3f3f3f3f;
        vector<int> vec1, vec2, ans;
        inorder(root1, vec1);
        inorder(root2, vec2);
        int l1 = vec1.size();
        int l2 = vec2.size();
        int i = 0 , j = 0;
        while(i<l1||j<l2){
            int a = i<l1 ? vec1[i] : INF, b = j<l2 ? vec2[j] : INF;
            if(a<=b) {ans.push_back(a); i++;}
            else {ans.push_back(b); j++;}
        }
        return ans;
    }
```

##### ②
```cpp
vector<int> getAllElements(TreeNode* root1, TreeNode* root2) {
        vector<int> vec1, vec2, ans;
        inorder(root1, vec1);
        inorder(root2, vec2);
        int l1 = vec1.size();
        int l2 = vec2.size();
        int i = 0 , j = 0, cur = 0;
        while(i<l1||j<l2){
            if(i == l1) cur = vec2[j++];
            else if(j == l2) cur = vec1[i++];
            else if(vec1[i] < vec2[j]) cur = vec1[i++];
            else cur = vec2[j++];
            ans.push_back(cur);
        }
        return ans;
    }
```

##### ③归并排序
```cpp
vector<int> getAllElements(TreeNode* root1, TreeNode* root2) {
        vector<int> vec1, vec2, ans;
        inorder(root1, vec1);
        inorder(root2, vec2);
        int l1 = vec1.size();
        int l2 = vec2.size();
        int i = 0 , j = 0;
        while(i<l1&&j<l2){
            if(vec1[i]<=vec2[j]) ans.push_back(vec1[i++]);
            else ans.push_back(vec2[j++]);
        }
        while(i < vec1.size())ans.push_back(vec1[i++]);
        while(j < vec2.size())ans.push_back(vec2[j++]);
        return ans;
    }
```
