---
title: JS数据类型及判断&typeof和instanceof的区别
date: 2024-03-07 22:10:34
tags: ['js', '前端']
categories: 技术
cover: http://sunowc60i.hd-bkt.clouddn.com/cover12.png
---
# 数据类型
JS 数据类型分为两大类：

1、**原始数据类型**：`String`、`Number`、`Boolean`、`Undefined`、`Null`、`Symbol`（es6 新增，表示独一无二的值）、`Bigint`（es10 新增）

2、**引用类型**：`Object`

其中 `Object` 中又包含了很多子类型（通过原型链继承），比如 `Array`、`Date`、`Function`、`Math`、`Map`、`Set`、`Regexp` 等等，总之除了原始数据类型皆为引用类型。

# 存储方式
原始数据类型：直接存储在栈（stack）中，占据空间小、大小固定，属于被频繁使用数据

引用数据类型：同时存储在栈（stack）和堆（heap）中，占据空间大、大小不固定。引用数据类型在**栈中存储指针**，指向**堆中存的实体**的地址。当解释器寻找引用值时，会首先检索其在栈中的地址，取得地址后从堆中获得实体。

ps：这样设计的原因在于
原始类型因为占据空间是固定的，可以将他们存在较小的内存中-栈中，这样便于迅速查询变量的值。引用数据类型大小不固定且会变化，固然不能直接放在栈中，但是其地址是固定的，可以将地址存在栈中。
# 类型判断
类型判断有以下几种方式
- `typeof`
- `instanceof`
- `constructor`
- `Object.prototype.toString.call()`

### typeof
原始类型中除了`null`会判断成Object，其它类型都可以通过 typeof 来判断
引用类型除了` 函数` 都会显示 Object
```javascript
console.log(typeof 1); // number
console.log(typeof true); // boolean
console.log(typeof "hello"); // string
console.log(typeof undefined); // undefined
console.log(typeof null); // 被 typeof 解释为 object
console.log(typeof {}); // object
console.log(typeof function () {}); // function
console.log(typeof []); // object 数组被解释为 object
```

### instanceof
能正确判断引用类型，不能精准判断原始数据类型
原理：通过递归查找原型链的方式来判断是否为构造函数的实例
```javascript
console.log({} instanceof Object); // true
console.log(function () {} instanceof Function); // true
console.log(1 instanceof Number); // false
console.log(true instanceof Boolean); // false
console.log("hello" instanceof String); // false
console.log(Array.isArray([])); // true
```

### constructor
通过判断 constructor 确定数据类型，不可靠在于，如果创建的对象更改了原型，就不准确了。
```javascript
console.log((1).constructor === Number); // true
console.log(true.constructor === Boolean); // true
console.log("str".constructor === String); // true
console.log([].constructor === Array); // true
console.log(function () {}.constructor === Function); // true
console.log({}.constructor === Object); // true

// 看个错误的例子
function Fn () {}

Fn.prototype = [];

const f = new Fn();

console.log(f.constructor === Fn); // false
console.log(f.constructor === Array); // true
```

### Object.prototype.toString.call()
前几种方式或多或少都存在一些缺陷，Object.prototype.toString.call() 综合来看是最佳选择，能判断的类型最完整也最准确。

```javascript
const oproto = Object.prototype;
const serialize = Object.prototype.toString;

console.log(serialize.call(1)); // [object Number]
console.log(serialize.call(true)); // [object Boolean]
console.log(serialize.call("hello")); // [object String]
console.log(serialize.call([])); // [object Array]
console.log(serialize.call({})); // [object Object]
console.log(serialize.call(() => {})); // [object Function]
console.log(serialize.call(null)); // [object Null]
console.log(serialize.call(undefined)); // [object Undefined]
```
例如判断一个对象是否为函数只需要使用`if (serialize.call(fn) === '[object Function])'`即可

### 其他
其余的还有es6引入的新的Array方法`Array.isArray`可以直接判断数组类型

> **综上**
> - **`typeof`可以判断基础数据类型，但是遇到`null`会误判为`object`，不能用于判断引用数据类型**
> - **`instanceof`可以用于检测引用数据类型，原理是根据原型链查找是否为构造函数的实例，不能用于判断基础数据类型**
> - **`constructor`直接根据构造函数进行判断类型，但是如果手动更改过对象的`prototype`，则不准确**
> - **`Object.prototype.toString.call()` 方法最好最通用**
