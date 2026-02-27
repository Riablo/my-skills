# 开发任务调度器

将代码开发任务自动派发到独立的 Claude Code 进程执行。技能会定位目标项目、创建 git worktree 隔离工作区，让子代理完成开发后推送分支，由你自行 review 和合并。

## 工作原理

本技能采用「传话官」模式：主进程不直接写代码，而是负责定位项目 → 创建 worktree → 派生子代理，子代理在隔离的 worktree 中运行 `claude` CLI 完成开发任务，完成后推送分支并清理 worktree。

```
用户描述任务
  → 语义匹配目标项目
  → 创建 git worktree（隔离工作区）
  → 派生子代理（独立 claude 进程）
      → 在 worktree 中执行开发任务
      → git push origin <branch>
      → 清理 worktree
  → 汇报分支名和状态
```

多个独立任务会并行派发，同时执行。

---

## 前置要求

- **claude CLI** 已安装（`claude` 命令可用）
- **uv** 已安装
- 目标项目已初始化 git 仓库

---

## 初始化配置

### 第一步：初始化全局配置

```bash
uv run ~/.claude/skills/project-dispatcher/scripts/workflow.py init
```

### 第二步：注册项目

```bash
uv run ~/.claude/skills/project-dispatcher/scripts/workflow.py add <项目名> \
  --path /path/to/project \
  --description "项目简短描述" \
  --aliases "别名1,别名2,别名3"
```

**示例：**

```bash
uv run ~/.claude/skills/project-dispatcher/scripts/workflow.py add frontend \
  --path ~/projects/my-frontend \
  --description "React 前端应用" \
  --aliases "前端,react,web"
```

配置保存在 `~/.config/project-dispatcher/config.yaml`。

### 查看已注册的项目

```bash
uv run ~/.claude/skills/project-dispatcher/scripts/workflow.py info
```

---

## 使用方式

直接在 Claude Code 对话中描述开发任务：

```
修复前端订单列表分页 bug
```

```
给后台管理系统加一个用户搜索功能，用模糊匹配
```

```
同时优化前端的首页加载速度，并修复后端的登录接口超时问题
```

AI 会语义匹配项目，创建分支（如 `main_fix-pagination-bug`），派代理执行，完成后报告分支名供你 review 合并。

---

## 注意事项

- 技能只推送分支，**不合并**，由你自行 review 后决定是否合并
- 项目目录下如果有 `CLAUDE.md`，子代理会自动读取其中的开发规范
- 匹配不到项目时会列出可用项目列表，不会猜测执行
- 本技能只处理代码开发类任务，笔记类任务请使用 `obsidian-dispatcher`
