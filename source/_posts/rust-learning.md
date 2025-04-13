---
title: Rust 学习1
date: 2025-04-02 22:49:51
tags: "Rust"
cover: http://sunowc60i.hd-bkt.clouddn.com/rust.png
---


# Rust
Rust 语言真的好：连续八年成为全世界最受欢迎的语言、没有 GC 也无需手动内存管理、性能比肩 C++/C 还能直接调用它们的代码、安全性极高 - 总有公司说使用 Rust 后以前的大部分 bug 都将自动消失、全世界最好的包管理工具 Cargo 等等。但...

有人说: "Rust 太难了，学了也没用"

对于后面一句话我们持保留意见，如果以找工作为标准，那国内环境确实还不好，但如果你想成为更优秀的程序员或者是玩转开源，那 Rust 还真是不错的选择，具体原因见下一章。

- 性能
  `Rust`是一种高性能的编程语言，它的设计目标是提供可靠的内存安全和高性能的执行速度。Rust的编译器会在编译时进行静态分析和优化，以生成高效的机器码。此外，Rust的并发模型也是其优势之一，它提供了强大的线程和异步编程模型，可以轻松地处理并发任务。

   连续七年成为全世界最受欢迎的语言, 一门系统级, 多范式,赋予每个人构建可靠且高效软件能力的语言, 如今被越来越多的大公司所接受, 并成功进入 Windows, Linux, Android 等主流操作系统的内核开发, 也被用于开发高性能的服务端应用, 如 TikTok, 抖音, 飞书等。
- 内存安全
  `Rust`是一种内存安全的编程语言，它的设计目标是提供可靠的内存安全和高性能的执行速度。Rust的编译器会在编译时进行静态分析和优化，以生成高效的机器码。此外，Rust的并发模型也是其优势之一，它提供了强大的线程和异步编程模型，可以轻松地处理并发任务。
- 生态
  `Rust`拥有丰富的生态系统，包括丰富的第三方库和工具，如 `serde`、`tokio`、`actix` 等，可以方便地集成和使用。此外，Rust还有一套完善的文档和社区支持，可以帮助开发者快速了解和使用语言。
- 工具链
  `Rust`拥有一套完善的工具链，包括 `rustc` 编译器、`cargo` 包管理器、`rustup` 工具链管理工具等，可以方便地管理和开发 Rust 项目。此外，Rust还有一套完善的文档和社区支持，可以帮助开发者快速了解和使用语言。

# Rust环境搭建
## 安装C++build工具
Rust依赖于C++的build工具链，因此需要安装C++的build工具链。
### Windows
- 安装`Visual Studio` MSVC
> 注： 可以选择MinGW, 但是需要手动安装`make`，而且Windows下更多使用`MSVC`

### Linux
- 安装`gcc` 实际上`gcc`已经包含了`make`

---

## 安装Rustup
Rustup是Rust的官方安装工具，用于安装Rust的编译器、包管理器等工具。
### 配置镜像
Rustup默认使用的是官方源，国内网络环境可能不稳定，因此需要配置Rustup的镜像源。
```
# Windows直接在系统环境变量中配置
# 注意不是path变量
RUSTUP_UPDATE_ROOT
https://rsproxy.cn/rustup

# Mac & Linux可以直接在命令行中配置
export RUSTUP_UPDATE_ROOT=https://rsproxy.cn/rustup
export RUSTUP_DIST_SERVER=https://rsproxy.cn
```

### 安装Rust
在windows中直接在官网下载安装包并运行rustup-init.exe即可
在Mac & Linux中可以使用命令行安装
`curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh`

### 验证安装
`rustc -V` 查看版本
`cargo -V` 查看版本

---

## 认识Cargo
包管理工具最重要的意义就是任何用户拿到你的代码，都能运行起来，而不会因为各种包版本依赖焦头烂额。
`Go`语言在 1.10 版本之前，所有的包都是在 github.com 下存放，导致了所有的项目都公用一套依赖代码，在本地项目复杂后，这简直是一种灾难。
`Cargo`是Rust的包管理工具，它的设计目标是提供可靠的内存安全和高性能的执行速度。Rust的编译器会在编译时进行静态分析和优化，以生成高效的机器码。此外，Rust的并发模型也是其优势之一，它提供了强大的线程和异步编程模型，可以轻松地处理并发任务。

---

## 创建HelloWorld
`cargo new hello_world`
`cd hello_world`
`cargo run`

`cargo run`实际上是执行了`cargo build`然后执行了`target/debug/hello_world`

`cargo build`会将代码编译成二进制文件，然后将二进制文件放在`target/debug`目录下

运行：`target/debug/hello_world`
这里的build是debug模式，在release模式下，二进制文件会放在`target/release`目录下，运行：`target/release/hello_world`
> build模式：
> - debug: 开发模式，编译速度快，调试方便
> - release: 生产模式，编译速度快，调试困难 `cargo build --release`


### Cargo check
当项目大了后，`cargo run` 和 `cargo build` 不可避免的会变慢，编译时间会很长，因此可以使用`cargo check`来检查代码是否有错误，不会编译代码，也不会运行代码

### Cargo.toml和Cargo.lock
`Cargo.toml`是Rust的包管理文件，它的设计目标是提供可靠的内存安全和高性能的执行速度。Rust的编译器会在编译时进行静态分析和优化，以生成高效的机器码。此外，Rust的并发模型也是其优势之一，它提供了强大的线程和异步编程模型，可以轻松地处理并发任务。
`Cargo.lock`是Rust的包管理文件，它的设计目标是提供可靠的内存安全和高性能的执行速度。Rust的编译器会在编译时进行静态分析和优化，以生成高效的机器码。此外，Rust的并发模型也是其优势之一，它提供了强大的线程和异步编程模型，可以轻松地处理并发任务。
> 可以对比着npm的`package.json`和`package-lock.json`来理解`Cargo.toml`和`Cargo.lock`
> 什么情况下该把`Cargo.lock`提交到git中？ 很简单，当你的项目是可运行的程序时，就应该把`Cargo.lock`提交到git中。
> 如果你的项目是一个库，那么就不需要把`Cargo.lock`提交到git中。

### Cargo update
`Cargo.lock`是Rust的包管理文件，它的设计目标是提供可靠的内存安全和高性能的执行速度。Rust的编译器会在编译时进行静态分析和优化，以生成高效的机器码。此外，Rust的并发模型也是其优势之一，它提供了强大的线程和异步编程模型，可以轻松地处理并发任务。
> 1. 当你使用`cargo update`时，会更新`Cargo.lock`文件



---