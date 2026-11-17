# plain-release-notes

[English](README.md) | **简体中文**

一个帮助 AI 智能体撰写发布说明的技能：写出真正用户愿意读的发布说明，每一行都能追溯到真实改动，需要用户动手的改动一条不漏，内部杂音一律不进。

大多数发布说明要么是团队以外没人看得懂的提交记录，要么是编造细节、偏偏漏掉那条破坏性变更的漂亮文案。本技能让智能体用读者的语言为读者写，同时靠每行隐藏的追溯标记和严格的检查器保证内容真实。

## 功能特点

- **精确区间，不靠感觉。** `collect` 列出两个引用之间的每个合并 PR（或提交），并给破坏性变更、迁移、配置、安全、弃用、依赖等打上提示标记。
- **三种分类。** 每个改动归为 *act*（读者必须动手）、*see*（读者会注意到）或 *quiet*（仅内部）。act 永远放在最前面的“升级前须知”；quiet 只计数不展示。
- **可追溯的每一行。** 每条都带 `<!-- src: #ID -->`。没有追溯、追溯到区间外、或引用了改动里没有的数字，都会被拒绝。
- **覆盖率躲不掉。** 漏掉 act 是错误；未展示的 see 是警告；带 breaking 或 security 提示却被归为 quiet 的改动会被要求复查。
- **大白话检查**（面向终端用户）：标出“修复了一个 bug”式开头、术语、代码标识符、文件路径和过长的行。面向开发者的说明用 `--audience integrators`。
- **干净输出。** `render` 去掉追溯标记，只留一行覆盖率注释。
- 单个 Python 文件，仅用标准库。`collect` 另需 git。

## 安装

把文件夹复制到智能体的技能目录，例如：

```bash
git clone https://github.com/fangdididi/plain-release-notes ~/.claude/skills/plain-release-notes
```

然后说：*“帮我写 v1.5 的发布说明（从 v1.4.0 起）。”*

## 用法

```bash
python3 scripts/relnotes.py collect v1.4.0 v1.5.0 --repo . > changes.json   # 线性历史加 --all-commits
# 在 changes.json 里为每个改动填写 sort / heading / note
python3 scripts/relnotes.py skeleton changes.json --title "1.5 新功能" > draft.md
# 为读者重写每条，保留 src 标记
python3 scripts/relnotes.py lint draft.md changes.json [--audience users|integrators] [--max-words 32]
python3 scripts/relnotes.py render draft.md --changes changes.json > RELEASE_NOTES.md
```

## 示例

`examples/make_demo_repo.sh` 会生成一个演示笔记应用的仓库，`v1.4.0` 到 `v1.5.0` 之间有七个改动。

- `examples/draft.md` 检查通过，0 错误 0 警告。
- `examples/draft-bad.md`（“重构 NoteStore 后搜索快了 10 倍”、CI 缓存、只字未提同步服务器升级）未通过：

```
ERROR L6: '#45' is sorted quiet; readers never see it, so leave it out
ERROR L6: number 10 does not appear in the traced change(s); check it or remove it
ERROR L8: no trace tag <!-- src: ... --> (every line must point at a change)
ERROR missing: '#44' needs reader action but is not in the notes
WARN  L5: opens with 'fixed a bug'; say what now works for the reader
FAIL: 5 errors, 6 warnings. 7 changes: 1 act, 3 see, 3 quiet; 4 traced in the notes
```

渲染后的公开版本见 `examples/public.md`。

## 文件结构

```
plain-release-notes/
├── SKILL.md / SKILL.zh-CN.md      # 技能本体（英文 / 中文）
├── README.md / README.zh-CN.md
├── scripts/relnotes.py            # collect / skeleton / lint / render
├── examples/
│   ├── make_demo_repo.sh          # 生成演示 git 仓库
│   ├── changes.json               # v1.4.0..v1.5.0 已分类的改动
│   ├── draft.md / draft-bad.md    # 通过与未通过的草稿
│   ├── lint-draft*.txt            # 两份草稿的检查输出
│   └── public.md                  # 渲染后的说明
├── tests/test_relnotes.py         # 12 个测试：python3 -m unittest discover -s tests
└── LICENSE
```

## 许可证

MIT © fangdididi
