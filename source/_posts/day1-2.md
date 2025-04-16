---
title: 归并排序-每日手撕
date: 2021-09-08 12:55:13
tags: [算法,AcWing,每日手撕,数据结构]
categories: [算法,每日手撕]
cover: https://mks-1306588458.cos.ap-nanjing.myqcloud.com/cover9.png
---

# 归并排序
思想就是把两个有序数组归并为一个有序数组
```cpp
void merge_sort(int q[], int l, int r){
    if(l>=r) return;
    int mid = l+r >> 1;
    merge_sort(q, l , mid); merge_sort(q, mid+1, r);//排序
    
    int k = 0, i = l, j = mid+1;
    while(i <= mid && j <= r)//归并
        if(q[i]<q[j]) tmp[k++] = q[i++];
        else tmp[k++] = q[j++];
    //比较完后将其中某组多余的后续传入tmp[]
    while(i <= mid) tmp[k++] = q[i++];
    while(j <= r) tmp[k++] = q[j++];
    
    //将tmp[]传入q[]
    for(int i = l, j = 0; i <= r; i++, j++) q[i] = tmp[j];
   	//注意 <= 因为传进来的r是n-1
}


```

完整代码：
```cpp
#include<iostream>
using namespace std;
const int N = 1e6;
int n;
int q[N], tmp[N];

void merge_sort(int q[], int l, int r){
    if(l>=r) return;
    int mid = l+r >> 1;
    merge_sort(q, l , mid); merge_sort(q, mid+1, r);
    int k = 0, i = l, j = mid+1;
    while(i <= mid && j <= r)
        if(q[i]<q[j]) tmp[k++] = q[i++];
        else tmp[k++] = q[j++];
    while(i <= mid) tmp[k++] = q[i++];
    while(j <= r) tmp[k++] = q[j++];
    for(int i = l, j = 0; i <= r; i++, j++) q[i] = tmp[j];
}

int main(){
    scanf("%d", &n);
    for(int i = 0; i < n; i++) scanf("%d", &q[i]);
    merge_sort(q, 0, n-1);
    for(int i = 0; i < n; i++) printf("%d ",q[i]);
    return 0;
}
```


