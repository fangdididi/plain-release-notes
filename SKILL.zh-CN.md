---
name: plain-release-notes
description: 把一个精确的 git 区间写成真正用户看得懂的发布说明：每一行都能追溯到真实改动，需要用户动手的改动一条不漏，内部杂音一律不进。用于撰写发布说明、更新日志、“新功能”介绍、版本更新公告或应用商店更新文案。
---

# 说人话的发布说明

发布说明常见两种翻车方式。一种是直接把提交记录贴出来（“bump deps、重构 NoteStore、修复 #43”），团队以外没人看得懂。另一种是写成顺滑的营销文案，悄悄编造功能、把数字往大里说，还偏偏漏掉那条会让用户环境挂掉的改动。

本技能走中间路线：用读者的语言为读者写，但草稿的每一行都带一个隐藏的追溯标记，指向它来源的改动。遇到以下情况，检查器会拒绝通过：

- 某行追溯不到任何改动，或指向本次发布范围以外的改动；
- 引用了被追溯改动里根本没有的数字；
- 漏掉了需要读者采取行动的改动；
- 展示了读者永远不会察觉的内部工作。

## 何时使用

- “帮我写 v1.5 的发布说明” / “上个 tag 以来改了什么？”
- 更新日志条目、应用内“新功能”弹窗、应用商店更新文案、升级通知邮件。
- 在别人的发布说明上线前帮忙审一遍。

不适用：给团队内部看的迭代报告或工程更新日志，那些保留术语即可。

## 三种分类

区间内每个改动只归入一类。分类才是真正的工作，动笔前先分完。

| 分类 | 含义 | 放在哪 |
|------|------|--------|
| **act（要动手）** | 读者必须做点什么，否则会出问题：破坏性变更、数据迁移、新的必填配置、权限、最低版本要求 | 永远放在最上面的 **升级前须知** |
| **see（看得到）** | 读者会注意到：新能力、更快、某个烦恼消失了 | 按读者正在做的事分组（“搜索时”） |
| **quiet（无感）** | 团队以外没人会察觉：重构、测试、CI、内部工具、无可见影响的依赖升级 | 不写进说明，只计数，不展示 |

在 see 和 quiet 之间犹豫时，问：*一个从不看代码的用户，一周内会注意到吗？* 在 act 和 see 之间犹豫时，问：*如果他们什么都不看直接升级，会发生什么？*

## 步骤

1. **钉死区间。** 拿到精确的两个引用（上一个发布 tag、新 tag 或提交）。绝不凭“最近的提交”来写。
   ```bash
   python3 scripts/relnotes.py collect v1.4.0 v1.5.0 --repo . > changes.json
   ```
   以合并为主的仓库会列出合并的 PR；squash 或线性历史请加 `--all-commits`。每个改动带有提示标记（`breaking`、`migration`、`config`、`security`、`deprecation`、`dependency`）和一个 `guess`（breaking/migration 猜为 `act`，chore/test/ci/refactor 前缀猜为 `quiet`）。
2. **给每个改动分类。** 在 `changes.json` 中填写 `sort`（act/see/quiet）、`heading`（see 类按读者的活动命名）和 `note`（一句大白话）。猜测只是建议；凡是带风险提示的改动都要读正文和文件。若一个“quiet”改动带有 `breaking` 或 `security` 提示，先证明确实无人需要行动，再把它留在 quiet。
3. **从骨架起草。**
   ```bash
   python3 scripts/relnotes.py skeleton changes.json --title "Jotter 1.5 新功能" > draft.md
   ```
   为读者重写每一条。每条都保留 `<!-- src: ID -->` 标记；一个改动可以写成两条，一条也可以引用两个改动。
4. **按读者扫读的方式写。**
   - 每条以加粗的结果开头，后面最多一句细节。
   - 写他们现在能做什么，而不是你做了什么（“导出 Markdown 会保留换行”，而不是“修复了导出的一个 bug”）。
   - act 类要写清楚谁受影响、做什么、按什么顺序（“自建同步服务器？请先升级到 2.0”）。
   - 只有改动里写明的数字才能用，并带上基准（“1 万条笔记约 0.4 秒，原来 2.5 秒”）。
   - 用界面上看得到的词，不用类名、文件路径或工单黑话。
   - 开头一句话说明这个版本对读者意味着什么，不要“我们很激动”。
5. **反复检查直到通过。**
   ```bash
   python3 scripts/relnotes.py lint draft.md changes.json            # 面向终端用户（默认）
   python3 scripts/relnotes.py lint draft.md changes.json --audience integrators
   ```
   错误会阻止发布；警告需要你做判断。`--audience integrators` 允许在面向开发者的说明里出现代码名和路径。
6. **渲染并交付。**
   ```bash
   python3 scripts/relnotes.py render draft.md --changes changes.json > RELEASE_NOTES.md
   ```
   追溯标记会被去掉，只留一行隐藏的覆盖率注释（act/see/quiet 各多少、追溯了多少）。把 `changes.json` 和 `draft.md` 跟发布放在一起，以后任何人都能问“这一行是从哪来的？”

## 示例

一个演示笔记应用的 `v1.4.0..v1.5.0` 区间有七个改动：附件搜索（#41）、测试（#42）、导出修复（#43）、置顶笔记且需要同步服务器 2.0（#44）、重构（#45）、CI 缓存（#46）、跟随系统深色模式（#47）。

分类结果：#44 act；#41、#43、#47 see；#42、#45、#46 quiet。成稿：

```markdown
## Before you upgrade
- **Run your own sync server?** Upgrade it to 2.0 or newer first. Older servers refuse pinned notes and stop syncing.

## When you search
- **Search looks inside attachments.** Text in PDFs and images now turns up in results.
- **Results come back faster:** about 0.4 s on 10000 notes, down from 2.5 s.
```

同一版本的草率草稿（“重构 NoteStore 后搜索快了 10 倍”“CI 缓存了 wheel”，且只字未提同步服务器）会报 5 个错误：编造的数字、两条内部改动、一行无追溯、漏掉的 act 改动。见 `examples/`。

## 提示

- 本版本没有 act 改动，就不要提升级，别加一个空的“请放心”段落。
- 用户无法操作的安全修复，只要改变了他们的风险，仍算 see（“分享链接现在 30 天后过期”）。直白地写，不写利用细节。
- 弃用对宣布它的那个版本来说是 act：什么会停止工作、何时、用什么替代。
- 如果你没法用读者的话解释一个改动，它多半是 quiet；如果不是，去问作者，别猜。
- see 类宁短勿全。主动舍弃小改动时，未展示 see 的覆盖率警告可以接受；act 改动永远不能舍弃。
