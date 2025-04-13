---
title: JS原型、原型链、继承、new运算符、Object.create
date: 2024-03-21 21:54:39
tags: ['js', '前端']
cover: http://sunowc60i.hd-bkt.clouddn.com/cover3.png
---


**_这篇文章可能较长，因为想要讲清楚JS原型和原型链，不得不讲讲原型和原型链产生的历史因素，他们到底是为什么而设计出来的？如果你希望对原型和原型链有比较深刻理解而不是每一次看完一篇文章下次遇到又忘了的话，请耐心一些听我细细道来。_** *文章中历史因素部分大多来源阮大神的博客*
# 历史因素
JS诞生之初，是因为网景公司需要一种脚本语言，使得用户可以与网页互动。1994年当时最新发布的浏览器Navigator0.9只能用来浏览，不能用来交互，那么到底采用什么语言呢，当时网景公司有两个选择，一个是采用现有的语言，比如Perl、Python、Tcl、Scheme等等，允许它们直接嵌入网页；另一个是发明一种全新的语言。就在这时，1995年，Sun公司将Oak语言改名为Java，正式向市场推出。Sun公司大肆宣传，许诺这种语言可以"一次编写，到处运行"（Write Once, Run Anywhere），它看上去很可能成为未来的主宰。

网景公司决定与SUN公司结盟，它不仅允许Java程序以applet（小程序）的形式，直接在浏览器中运行；甚至还考虑直接将Java作为脚本语言嵌入网页，只是因为这样会使HTML网页过于复杂，后来才不得不放弃。

总之，当时的形势就是，网景公司的整个管理层，都是Java语言的信徒，Sun公司完全介入网页脚本语言的决策。因此，Javascript后来就是网景和Sun两家公司一起携手推向市场的，这种语言被命名为"Java+script"并不是偶然的。

此时，34岁的系统程序员Brendan Eich登场了。1995年4月，网景公司录用了他。

Brendan Eich的主要方向和兴趣是函数式编程，网景公司招聘他的目的，是研究将Scheme语言作为网页脚本语言的可能性。Brendan Eich本人也是这样想的，以为进入新公司后，会主要与Scheme语言打交道。

仅仅一个月之后，**1995年5月，网景公司做出决策，未来的网页脚本语言必须"看上去与Java足够相似"，但是比Java简单**，使得非专业的网页作者也能很快上手。这个决策实际上将Perl、Python、Tcl、Scheme等非面向对象编程的语言都排除在外了。

Brendan Eich被指定为这种"简化版Java语言"的设计师。

总的来说，他的设计思路是这样的：
> （1）借鉴C语言的基本语法；
> （2）借鉴Java语言的数据类型和内存管理；
> （3）借鉴Scheme语言，将函数提升到"第一等公民"（first class）的地位；
> （4）借鉴Self语言，使用基于原型（prototype）的继承机制。

所以，**Javascript语言实际上是两种语言风格的混合产物----（简化的）函数式编程+（简化的）面向对象编程**。这是由Brendan Eich（函数式编程）与网景公司（面向对象编程）共同决定的。

# Javascript继承机制的设计思想

### 一、面向对象思想

当时C++是最流行的语言，而Java刚刚诞生，他们都是面向对象编程(OOP)语言，熟知面向对象的人都知道，面向对象的三个基本特征：`封装、继承、多态`。Brendan Eich无疑受到了影响，Javascript里面所有的所有数据类型都是对象，或者说能当作对象使用更为准确（除了null和undefinded），这一点与Java非常相似。但是，他随即就遇到了一个难题，到底要不要设计"继承"机制呢？

如果真的是一种简易的脚本语言，其实不需要有"继承"机制。但是，Javascript里面都是对象，必须有一种机制，将所有对象联系起来。所以，Brendan Eich最后还是设计了"继承"。

但是，他不打算引入"类"（class）的概念，因为一旦有了"类"，Javascript就是一种完整的面向对象编程语言了，这好像有点太正式了，而且增加了初学者的入门难度。

他考虑到，C++和Java语言都使用new命令，生成实例。
C++:
```cpp
CTest*  pTest = new  CTest();
```
Java
```java
Foo foo = new Foo();
```
于是，他就把new命令引入Javascript，用来从原型对象，生成一个实例对象，但是Javascript没有“类”，怎么来表示原型对象呢，他想到C++和Java调用new命令时，都会调用“类”的构造函数（constructor），于是Javascript中就作了一个简化设计，new后面跟的不是类，而是构造函数，举例说：
```javascript
function Person(name) {
  this.name = name;   // 这就是javascript中的构造函数，
}
```
所以直接对这个构造函数使用new，就会生成一个人对象的实例

```javascript
var p1 = new Person('张三');
console.log(p1.name); // 张三

```
注意构造函数中的`this`关键字，它就代表了新创建的实例对象。

但是，用构造函数生成实例对象，有一个缺点，那就是无法共享属性和方法。

比如，在Girl对象的构造函数中，设置一个实例对象的共有属性gender。
```javascript
function Girl(name) {
  this.name = name   // 这就是javascript中的构造函数，
  this.gender = '女'
}
```
如果此时生成两个对象实例：
```javascript
var g1 = new Girl('小丽');
var g2 = new Girl('Alice');
```
这两个对象的gender属性是独立的，修改其中一个，不会影响到另一个，这样不仅不能实现数据的共享，每个实例都会创建自己的属性和方法副本，会造成内存空间的浪费。
### 二、prototype属性的引入
考虑到这一点，Brendan Eich决定为构造函数设置一个prototype属性。这个属性是一个对象，所有的共享属性和方法，都放在这个对象里面，不需要共享的属性和方法，就放在构造函数里，类似于C++和Java类中的三种访问修饰符`public private protected`只不过JS的prototype设计很简单。
实例对象一旦创建，将自动引用prototype对象的属性和方法。也就是说，实例对象的属性和方法，分成两种，一种是私有(private)的，另一种是共有(public)的。
还是以Girl构造函数为例，现在用prototype属性进行改写：
```javascript
function Girl(name) {
  this.name = name;   // 这就是javascript中的构造函数，
  this.gender = '女';
}
Girl.prototype = {
  gender = '女';
}
```
现在，gender属性放在prototype对象里，是两个实例对象共享的。只要修改了prototype对象，就会同时影响到两个实例对象。
### 三、\_\_proto\_\_(前后各双下划线)是啥
我们先看一个例子：


```javascript
// 创建一个构造函数
function Person(name) {
    this.name = name;
}

// 通过原型对象添加方法
Person.prototype.sayHello = function() {
    console.log("Hello, my name is " + this.name);
};

// 创建对象实例
var person1 = new Person("Alice");
var person2 = new Person("Bob");

// 调用对象实例的方法
person1.sayHello(); // 输出：Hello, my name is Alice
person2.sayHello(); // 输出：Hello, my name is Bob
```
在上面的例子中，我们创建了一个名为 Person 的构造函数，并通过原型对象 Person.prototype 添加了一个方法 sayHello。然后，我们使用该构造函数创建了两个对象实例 person1 和 person2，并分别调用了 sayHello 方法。
在这个例子中，person1 和 person2 对象实例都没有 sayHello 方法，但是它们可以访问到构造函数中prototype原型对象的sayHello，那它们是怎么访问的呢？答案就是通过 `__proto__` 属性链接到了原型对象 Person.prototype，
我们一般在控制台打印对象的时候会有个`[[prototype]]`隐藏属性，`__proto__` 是 `[[Prototype]]` 的因历史原因而留下来的 getter/setter，也就是可以通过`__proto__`来访问和修改`[[prototype]]`。

需要注意的是，`__proto__`是非标准的属性，尽管大多数浏览器都支持这个属性，但它不属于Javascript规范的一部分。该属性没有写入 ES6 的正文，而是写入了附录，`__proto__`前后的双下划线，说明它本质上是一个内部属性，而不是一个正式的对外的 API，只是由于浏览器广泛支持，才被加入了 ES6。标准明确规定，只有浏览器必须部署这个属性，其他运行环境不一定需要部署，而且新的代码最好认为这个属性是不存在的。因此，无论从语义的角度，还是从兼容性的角度，都不要使用这个属性，而是使用`Object.setPrototypeOf()`（写操作）、`Object.getPrototypeOf()`（读操作）、`Object.create()`（生成操作）代替。
> 所以说用一句话来概括__proto__：**__proto__指向了生成该对象的构造函数的原型对象(prototype)**

### 四、 原型链
那么\_\_proto__和我们以上例子中person1和person2能访问到sayHello有什么关系呢
> **When accessing the properties of an object, JavaScript will traverse the prototype chain upwards until it finds a property with the requested name.** *- JavaScript Garden*
> **当查找一个对象的属性时，JavaScript 会向上遍历原型链，直到找到给定名称的属性为止。** *- JavaScript 秘密花园*


这句话就说明了我们在查找一个对象的属性时，JavaScript 会向上遍历原型链，直到找到给定名称的属性为止。到查找到达原型链的顶部 - 也就是 Object.prototype - 但是仍然没有找到指定的属性，就会返回 undefined。下面代码展示了JS是如何寻找一个对象的属性的:
```javascript
function getProperty(obj, prop) {
  if (obj.hasOwnProperty(prop))
    return obj[prop];
 
  else if (obj.__proto__ !== null)
    return getProperty(obj.__proto__, prop);
 
  else
    return undefined;
}
```
我们甚至可以直接通过设置一个对象的`__proto__`来修改它的原型
```javascript
var Point = {
  x: 0,
  y: 0,
  print: function () { console.log(this.x, this.y); }
};
 
var p = {x: 10, y: 20, __proto__: Point};
p.print(); // 10 20
```
总结：通常情况下，我们将共享的方法和属性定义在构造函数的 prototype 属性下，这样它们可以被所有实例对象共享。而构造函数内部定义的属性则是每个实例对象私有的，它们在每个对象创建时都会被重新创建。

JavaScript 遵循原型继承的设计原则，即通过原型链来实现对象之间的继承关系。当我们访问一个对象的属性或方法时，JavaScript 引擎会先在对象自身查找，如果找不到则会沿着`__proto__` 链向上查找，直到找到匹配的属性或方法，或者到达原型链的终点 Object.prototype，如果仍然找不到，则返回 undefined。

为了防止原型链的无限循环，JavaScript 在原型链的终点 Object.prototype 上设置了 `__proto__` 属性为 null。


### 五、new操作符到底干了啥
结合着本文的第三、四点，new操作干了什么事就大概清楚了，
总的来说，通过new创建对象可以细分为以下5步：
- 1.创建一个空的对象。 {}
- 2.将新创建的空对象的原型设置为构造函数的prototype属性值。
- 3.将构造函数的this指向新创建的对象。
- 4.执行构造函数中的代码，给新创建的对象添加属性和方法。
- 5.如果构造函数没有显式地返回一个对象，则返回新创建的对象。

根据上述规则手动实现一个New运算
```javascript
function New(constructorFn) {
  var n = { '__proto__': constructorFn.prototype };
  return function () {
    constructorFn.apply(n, arguments);
    return n;
  }
}
```
测试一下以上代码：
```javascript
function Point(x, y) {
  this.x = x;
  this.y = y;
}
Point.prototype = {
  print: function () { console.log(this.x, this.y); }
};
 
var p1 = new Point(10, 20);
p1.print(); // 10 20
console.log(p1 instanceof Point); // true
 
var p2 = New (Point)(10, 20);
p2.print(); // 10 20
console.log(p2 instanceof Point); // true
```

###  六、Object.create(obj)
Javascript 规范只为我们提供了`new`操作符。然而，Douglas Crockford（JSON创建者、Javascript宗师）找到了利用`new`操作符实现真正的原型继承的方法(无需使用构造函数和new运算符)！他编写了 `Object.create` 函数。
```javascript
Object.create = function (parent) {
  function F() {}
  F.prototype = parent;
  return new F();
};
```
这看起来很奇怪，但其实很简单。它只是创建一个新对象，并将其原型设置为你想要的任何内容。如果我们允许使用 `__proto__`，它可以这样写：
```javascript
Object.create = function (parent) {
  return { '__proto__': parent };
};
```

下面的代码是我们使用真正原型继承的 Point 示例。
```javascript
var Point = {
  x: 0,
  y: 0,
  print: function () { console.log(this.x, this.y); }
};
 
var p = Object.create(Point);
p.x = 10;
p.y = 20;
p.print(); // 10 20
```
用 `Object.create` 创建的对象所包含的属性全都是prototype中的公有属性，可以使用原型链方式来访问，可以通过给对象自身设置属性来添加私有属性。





参考资料：
[Javascript诞生记-阮一峰的网络日志](https://www.ruanyifeng.com/blog/2011/06/birth_of_javascript.html)
[阮一峰 ECMAScript 6 (ES6) 标准入门教程 第三版](https://www.bookstack.cn/read/es6-3rd/spilt.4.docs-object-methods.md)
[JS创始人-Brendan Eich的自述](https://brendaneich.com/2008/04/popularity/)
[Javascript – How Prototypal Inheritance really works](https://blog.vjeux.com/2011/javascript/how-prototypal-inheritance-really-works.html)
[JavaScript-Garden](https://shamansir.github.io/JavaScript-Garden/)
[原型继承](https://zh.javascript.info/prototype-inheritance)