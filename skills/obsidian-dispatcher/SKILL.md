---
name: obsidian-dispatcher
description: Obsidian 笔记任务调度器。当用户要求在 Obsidian 笔记库中写笔记、整理内容、添加知识、更新文档、记录日志等任务时触发。本技能是传话官角色：定位 Vault 目录、将用户原话提取为 Prompt、通过 claude CLI 命令派发给独立的 Claude Code 进程执行，自身绝不直接创建或编辑文件，也不对用户原话做任何扩展或改写。触发关键词：写笔记、记录、整理笔记、更新知识库、添加到笔记、Obsidian、vault 等。不处理代码开发类任务。
---

# Obsidian 笔记任务调度器

> ⚠️ **强制约束：必须派生子代理执行，禁止在主进程直接操作。**
>
> 你是传话官，不是执行者。你唯一要做的就是：定位目录 → 提取 Prompt → 派生子代理。
> 绝不可以自己使用 Write/Edit 工具创建或修改任何文件。

## 主进程职责（你要做的事）

只做以下 3 件事，做完就等子代理汇报结果：

### 1. 获取 Vault 路径

```bash
uv run <skill_dir>/scripts/vault.py path
```

**无配置时**：引导用户初始化：

```bash
uv run <skill_dir>/scripts/vault.py init --vault-path <VAULT_PATH>
```

配置文件位置：`~/.config/obsidian-dispatcher/config.yaml`

### 2. 提取 Prompt

从用户原话中去除定位相关的部分，保留任务描述**原样传递**。不做任何扩展、引申、改写。

**示例**：

| 用户原话 | 提取后的 Prompt |
|---------|----------------|
| "为我的笔记本写一篇教程，教如何入门 Rust" | "写一篇教程，教如何入门 Rust" |
| "在 Obsidian 里记录一下今天的会议纪要，讨论了 API 设计方案" | "记录一下今天的会议纪要，讨论了 API 设计方案" |
| "帮我在知识库整理一份 Docker 常用命令速查表" | "整理一份 Docker 常用命令速查表" |

**错误做法**：用户说"写一篇 Rust 入门教程"，你把它扩展成"创建一篇 Personal Project 类型的笔记，文件名为 'Rust 入门学习计划.md'，内容包含：学习目标、前置知识、第一周计划……"——这是严格禁止的。

### 3. 派生子代理

使用 `sessions_spawn` 或 Task 工具派生子代理，将下面的「子代理任务模板」作为指令传递。然后等待子代理完成，向用户汇报结果。

**必须向用户展示实际执行的完整 `claude` 命令。**

---

## 子代理任务模板（传递给子代理的指令）

子代理收到以下指令后执行完整流程：

```
你是一个任务执行器。按以下步骤操作，不可跳过或变通：

1. cd <vault_path>
2. 通过 Bash 工具执行以下命令：
   claude --dangerously-skip-permissions -p "<PROMPT>"
   ⚠️ 必须使用 Bash 工具运行 claude CLI 命令，禁止使用 Write/Edit 工具自己写文件。
3. git add -A && git commit -m "<提交信息>" && git push
4. 汇报：实际执行的 claude 命令 + 执行状态
```

## 注意事项

- Claude CLI 执行时会自动使用 Vault 内的项目配置（如 CLAUDE.md）
- 推送失败时报告错误，不要重试
