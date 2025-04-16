---
title: TS_any_unknown
date: 2024-05-21 16:20:34
tags: ['TypeScript']
cover: https://mks-1306588458.cos.ap-nanjing.myqcloud.com/cover5.png
---

# TS中的unknown、any和never类型
### any
**any** 类型表示没有任何限制，该类型的变量可以赋予任意类型的值。

```typescript
let x: any;

x = 1; // 正确
x = "foo"; // 正确
x = true; // 正确
```
上面类型中, 变量x的类型是any, 就可以被赋值为任意类型的值
变量类型一但设为any, TS实际上会关闭这个变量的类型检查,只要语法正确, 都不会报错
### unknown
**unknown**类型, 为了解决any类型"污染"其他变量, TS3.0引入了unknown类型,它与any含义相似, 表示类型不确定,可以是任意类型,但是它的使用有一些限制,不像any那样自由, 可以视为严格版的any, unknown跟any的相似之处,在于所有类型的值可以分配给unknown类型

```typescript
let x: unknown;

x = true; // 正确
x = 42; // 正确
x = "Hello World"; // 正确
```

上面实例中, 变量x是unknown类型, 所有类型的值可以赋值给它, 但是与any类型的区别在于, 它不能直接使用, 主要有以下几个限制

1. unknown类型的变量, 不能直接赋值给其他类型的变量(除了any和unknown类型)
```typescript
let v: unknown = 123;

let v1: boolean = v; // 报错
let v2: number = v; // 报错
```
2. 其次, 不能直接调用unknown类型变量的方法和属性
```typescript
let v1: unknown = { foo: 123 };
v1.foo; // 报错

let v2: unknown = "hello";
v2.trim(); // 报错

let v3: unknown = (n = 0) => n + 1;
v3(); // 报错
```
3. 再次,unknown类型变量能够进行的运算是有限的, 只能进行比较运算(`==`, `===`, `!=`, `!==`, `||`, `&&`, `?`, `!`), typeof运算符和instanceof运算符这几种, 其他运算都会报错


### never类型
为了保持与集合论的对应关系，以及类型运算的完整性，TS引入了空类型never，即该类型为空，不包含任何值。
由于不存在任何属于“空类型”的值，所以该类型被称为`never`,即不可能有这样的值.
```typescript
let x: never;
```
上面的示例中,变量x的类型是never,就不可能赋给它任何值,否则都会报错.
never类型的使用场景,主要是在一些类型运算之中,保证类型运算的完整性, 另,不可能返回值的函数, 返回值的类型就可以写成never.如果一个变量可能有多种类型（即联合类型），通常需要使用分支处理每一种类型。这时，处理所有可能的类型之后，剩余的情况就属于never类型。
```typescript
function fn(x: string | number) {
  if (typeof x === "string") {
    // ...
  } else if (typeof x === "number") {
    // ...
  } else {
    x; // never 类型
  }
}
```
上面示例中，参数变量x可能是字符串，也可能是数值，判断了这两种情况后，剩下的最后那个else分支里面，x就是never类型了。