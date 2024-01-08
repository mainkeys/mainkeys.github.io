---
title: 快速排序-每日手撕
date: 2021-09-08 00:37:23
tags: [算法,AcWing,每日手撕,数据结构]
categories: [算法,每日手撕]
---


经典快速排序

```cpp
void quick_sort(int q[], int l, int r)
{
    //递归的终止情况
    if(l >= r) return;
    //第一步：分成子问题
    int i = l - 1, j = r + 1, x = q[l + r >> 1];
    while(i < j)
    {
        do i++; while(q[i] < x);
        do j--; while(q[j] > x);
        if(i < j) swap(q[i], q[j]);
    }
    //第二步：递归处理子问题
    quick_sort(q, l, j), quick_sort(q, j + 1, r);
    //第三步：子问题合并.快排这一步不需要操作，但归并排序的核心在这一步骤
}
```
完整代码
```cpp
#include<iostream>
#include<cstdio>
using namespace std;

const int N = 1e6;
int n;
int q[N];

void quick_sort(int q[], int l, int r){
    if(l >= r) return;
    int x = q[l+r >> 1], i = l-1, j = r+1;
    while(i < j){
        do i++; while(q[i]<x);
        do j--; while(q[j]>x);
        if(i<j) swap(q[i],q[j]);
    }
    quick_sort(q, l, j);
    quick_sort(q, j+1, r);
}

int main(){
    scanf("%d",&n);
    for(int i = 0; i < n; i++)  scanf("%d", &q[i]);
    quick_sort(q, 0, n-1);
    for(int i = 0; i < n; i++) printf("%d ", q[i]);
    return 0;
}

```
注意x的取值与边界问题，背一种模板即可，
若x=q[l],则必须为`quick_sort(q, l, j),quick_sort(q, j+1, r);`
若x=q[r],则必须为`quick_sort(q, l, i-1),quick_sort(q, i, r);`