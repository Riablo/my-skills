# Obsidian 笔记任务调度器

将写笔记、整理知识、记录日志等 Obsidian 相关任务自动派发到独立的 Claude Code 进程执行，完成后自动 git commit 并推送。

## 工作原理

本技能采用「传话官」模式：主进程不直接操作 Vault 文件，而是派生一个独立的子代理，在 Vault 目录中运行 `claude` CLI 完成实际写作任务，执行完毕后自动提交推送。

```
用户发送任务
  → 主进程定位 Vault 路径
  → 派生子代理（独立 claude 进程）
      → 在 Vault 目录执行任务
      → git commit & push
  → 汇报结果
```

---

## 前置要求

- **Obsidian Vault** 已初始化为 git 仓库（`git init`，并配置好远程仓库）
- **claude CLI** 已安装（`claude` 命令可用）
- **uv** 已安装

---

## 初始化配置

首次使用，需要告诉技能你的 Vault 路径：

```bash
uv run ~/.claude/skills/obsidian-dispatcher/scripts/vault.py init \
  --vault-path "/path/to/your/obsidian/vault"
```

配置保存在 `~/.config/obsidian-dispatcher/config.yaml`。

---

## 使用方式

直接在 Claude Code 对话中描述笔记任务即可：

```
帮我写一篇 Rust 入门教程笔记
```

```
在 Obsidian 里记录一下今天的会议纪要，讨论了 API 设计方案
```

```
整理一份 Docker 常用命令速查表到知识库
```

AI 会自动提取任务描述、定位 Vault、派生子代理执行，完成后汇报结果。

---

## 注意事项

- Vault 目录下如果有 `CLAUDE.md`，子代理会自动读取并遵循其中的指令（如笔记格式规范）
- 推送失败时会报告错误，不会自动重试
- 本技能只处理笔记类任务，代码开发任务请使用 `project-dispatcher`
