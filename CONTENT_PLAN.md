# 顺着一次 TEE 调用：第一季内容与交付记录

本文件是编辑工作记录，不进入博客正文。计划确认于 2026-09-18。

## 发布约定

- 六篇完整文章、公开实验资料、系列导航一起验证后发布。
- 最近技术聊天仅用于提炼问题；正文以公开资料和本次公开实验为依据。
- 不发布内部源码、项目细节、截图或私人聊天。
- 不把预计输出、源码推导、他人日志写成本次运行结果。
- 文章在实验通过后移入 `source/_posts`，保留 `render_drafts: false`；日期带明确时区，置顶路线图保留并接入六篇。首发日期及部署记录保留在本文，文章展示日期按用户后续要求错开，实验日期不随之改写。

## 第一季

| 序号 | 固定 slug | 主题 | 当前状态 | 需要的证据 |
|---|---|---|---|---|
| 01 | tee-01-ca-to-ta | 一次 CA 请求，到底怎么走到 TA？ | 正文、图与实测证据已完成 | hello_world 两侧日志、退出码 |
| 02 | tee-02-armv8-exception-levels | 看 TEE 代码之前，我先把 ARMv8 的异常级理清了 | 正文、图、实际配置与 EL1 启动记录已核对 | 架构资料、固定源码与第二次运行的启动记录 |
| 03 | tee-03-linux-tee-driver | 从 /dev/tee0 开始，追一次请求进入内核 | 正文、图与实测证据已完成 | strace、对应 UAPI 与驱动源码 |
| 04 | tee-04-shared-memory | 传给 TA 的参数，为什么不能只是一个指针？ | 正文、图与实测证据已完成 | 正常、零长、错误类型、短输出缓冲区测试 |
| 05 | tee-05-rpc-and-supplicant | TA 还没执行完，为什么又回到了 Linux？ | 正文、图与实测证据已完成 | REE TA 加载 RPC 的日志 |
| 06 | tee-06-before-the-first-call | 能调用 TA 之前，系统是怎样启动起来的？ | 正文、图、启动记录与源码核对完成 | 固定 TF-A 源码中的认证失败传播；不是 TBB 实测 |

## 实验前置状态

- 本机 WSL 未用于本轮实验。本机诊断与环境探测记录留在仓库外，不进入公开实验包；`tools/blog/diagnose-wsl.ps1` 提供通用只读诊断入口。
- OP-TEE manifest：4.10.0 稳定 tag；annotated tag 对象 `5dc349cf004db361afc70e76af1a947c88ea7cf8`，peeled commit `6d5849d5c1e4054980bf430ce1e96ebd0f532590`。其余组件见后续实验锁定文件。
- 实验使用本仓库标准 Ubuntu Actions runner。独立实验分支 `codex/tee-series-lab`，不触发现有 main Pages 流程。
- 首次运行：https://github.com/mainkeys/mainkeys.github.io/actions/runs/35250383576 ，源码提交 `f250232e5addc557f23f1fc039f18f667743fb7e`。源码、完整编译与启动成功，首个环境命令因 CRCRLF 状态解析失败而超时；尚未执行 hello_world。10 份原始证据已校验并归档在 `labs/optee-series/evidence/35250383576`。
- 第二次运行：https://github.com/mainkeys/mainkeys.github.io/actions/runs/35257180558 ，源码提交 `113865db3eb885c15f5d079db6b5dd12325a4c94`。双回车回归、固定组件完整重建和 QEMU 实验均成功。构建时间 18:14:06～19:09:48 UTC；实验时间 19:09:49～19:10:01 UTC。18 份原始证据已校验并归档在 `labs/optee-series/evidence/35257180558`。
- 仅使用公开仓库标准 runner，不使用付费 larger runner，不上传 artifact/cache。小型证据经压缩、摘要校验从 Actions 日志取回。

## 验收与部署

1. 在 GitHub 标准 Ubuntu runner 的 Linux 文件系统搭建固定版本 QEMU v8 实验。
2. 保存 resolved manifest、构建配置、命令和原始结果。实验包不携带整个上游源码或工具链。
3. 核对六篇文字、图、引用和实验结果，发布前清除编辑用待补标记。
4. 更新现有置顶路线图的阅读入口，补齐文章互链。
5. `npm run build`；检查 Hexo/Aurora 页面、数据、图片及桌面/手机显示。
6. 仅暂存本次明确列出的文章、图及公开实验资料；保留既有 package.json 改动、未跟踪封面及 doc 构建目录。
7. 推送 main，由现有 GitHub Actions 构建并部署 doc；不调用指向 master 的 hexo deploy。
8. Actions 成功且线上六篇逐一验收后，记录 commit、运行链接和文章地址。

## 后续选题

驱动并发与内存管理 → 设备树与设备模型 → RPMB 与可信存储 → 防回滚与安全升级状态管理。本轮不扩写、不设置自动发布。

## 发布前校验记录

- 六篇正文和六张本地 SVG 已完成；独立技术复核未发现架构阻断，修正了 probe 绑定时序、TBB 条件及回显哨兵的表述。
- 隔离预览保存在仓库外；六篇 HTML、Aurora JSON、SVG、文章互链、代码块已通过静态检查，置顶路线图和旧文回归通过。
- 发现 Aurora 的 `.html` 文章地址请求不存在的 `.html.json` 数据，新增 `scripts/article-html-aliases.js` 兼容现有地址；保留原始无扩展名数据入口。
- Aurora 2.5.3 的三处文章日期转换混用本地月份与 UTC 日/年，新增 `scripts/aurora-local-dates.js` 精确修复生成脚本；API 时间戳保持不变。独立构建与三个时区、跨年边界验证通过，保留现有模块 URL 和缓存策略。
- 移除 package.json 中将本站作为 Hexo 插件载入的 `hexo-site: file:` 自依赖，消除 EISDIR 构建错误；原有 `hexo.version` 改动仍属于用户未提交内容，不混入本次提交。
- 已观察桌面与六篇 390px 手机预览；图文完整，表格与代码局部滚动，页面没有横向溢出。截图与静态报告保存在仓库外的实验 QA 目录。
- 原置顶路线图本地增加六篇阅读顺序、公开实验包入口和后续选题；保持原有正文、置顶字段与旧文章。
- 发布前必须人工审阅真实 trace：运行脚本的字符串检查只作初筛，不能单独证明目标 TA 文件成功读取、特定 ioctl 成功或 42→43。必须与 UART、程序断言和固定源码交叉核对。
- 已逐一取回并审阅六篇引用的 29 个固定上游源码路径，修正 Client API 头文件的过时路径；其余关键调用与认证分支一致。
- 10 个去重官方文档链接均返回 200，三个页面锚点存在，固定版本链接未重定向到其他版本。
- 第二次 CI 使用的提交保持为 `113865db`。随后本地单独修正文件采集 shell 组的退出状态传播，采用 `&&` 防止 Base64 失败后仍输出结束标记；成功、部分输出后失败、缺文件三种 Git Bash 回归通过。这项修正没有冒充完整 QEMU 重跑，公开证据仍对应原运行提交。
- `labs/optee-series/.gitignore` 仅放行已人工检查的证据目录，原始字节由 `.gitattributes` 的 `-text` 保留；未审核的新运行默认忽略。
- hello_world 的 42→43、echo 五项断言、客户端 ioctl、两个 UUID 的 supplicant 成功文件读取及安全侧装载均已交叉核对。初筛字符串检查没有作为唯一证据。
- 六篇采用同一次成功实验的记录；首跑失败原样归档。TBB 认证失败仍仅为固定源码分析。
- 统一采用 2026-09-18 的实际发布时间与 +08:00 时区，移除编辑占位。生产构建、Actions 和线上核验按上述发布流程执行。
- 最终 `npm run build` 通过；`doc` 中六篇 HTML、Aurora 原始/别名数据及 SVG 完整。带时区的 front matter 日期使用引号，避免 YAML Date 被再次补时区；六篇在 UTC 与 Asia/Shanghai 两种环境下均得到正确时间。
- 预览工具保留仓库内的正常 source，只将 public_dir 放到仓库外，并强制生成；避免 Hexo 在仓库外 source 的资源 ID 错误及跨输出目录的缓存误判。

## 发布记录

- 发布日期：2026-09-18（Asia/Shanghai）。发布提交：[472cf654b427a8a2680e06169204e74cfbd80241](https://github.com/mainkeys/mainkeys.github.io/commit/472cf654b427a8a2680e06169204e74cfbd80241)。
- [Pages 工作流 35265689231](https://github.com/mainkeys/mainkeys.github.io/actions/runs/35265689231) 的构建、上传与部署均成功，部署于 2026-09-17 19:35:34 UTC 完成。
- 线上六篇 HTML、Aurora JSON 与 `.html.json` 别名、六张 SVG、文章互链及锚点检查通过；别名与原始数据一致。原置顶路线图保留置顶标记，新增六篇入口；旧文 `code` 的正文与 12 张图片返回正常。
- 浏览器逐篇核对了线上六篇的标题、图示与 390px 手机布局，无页面横向溢出；桌面结果表与代码显示正常。实际导航复测通过（桌面 06→05、手机 05→04）。
- 两次实验共 28 份原始文件的 Git 索引字节数与 SHA-256 全部匹配；用户原有 package.json 版本改动、未跟踪封面和 doc 目录均未混入发布提交。
- 六篇线上入口：[01 调用链](https://mainkeys.github.io/post/tee-01-ca-to-ta.html) · [02 异常级](https://mainkeys.github.io/post/tee-02-armv8-exception-levels.html) · [03 Linux 驱动](https://mainkeys.github.io/post/tee-03-linux-tee-driver.html) · [04 共享内存](https://mainkeys.github.io/post/tee-04-shared-memory.html) · [05 RPC](https://mainkeys.github.io/post/tee-05-rpc-and-supplicant.html) · [06 启动过程](https://mainkeys.github.io/post/tee-06-before-the-first-call.html)。

## 2026-09-18 文字修订

- 根据用户反馈，六篇减少模板化转场、刻意比喻和重复总结，改为更平实的技术笔记口吻；不增加个人经历，不改实验输出、代码及技术结论。
- 01～06 的展示日期依次调整为 2026-09-03、09-06、09-09、09-12、09-15、09-18，每篇相隔三天。`updated` 记录本次实际修订时间，首发和实验的真实日期仍为 9 月 18 日。
- 固定提交引用、公开证据、稳定链接和系列顺序沿用已发布版本；本轮只调整文字和文章日期，不重跑无关实验，不开启第二批或恢复自动续办。
- 修订预检：六篇代码/日志块、引用链接及其他 front matter 与首发版一致；`npm run build -- --force` 通过，Aurora 原始/别名数据和六个展示日期正确，图片与互链正常。桌面第一篇、390px 手机第四篇的文字及日期显示已核对。
