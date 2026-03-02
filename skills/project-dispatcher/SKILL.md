---
name: project-dispatcher
description: 开发任务调度器。当用户要求对某个项目进行代码开发、修改、修复 bug、重构、添加功能等编码工作时触发。本技能是传话官角色：定位项目目录、创建 git worktree、将用户原话提取为 Prompt、通过 claude CLI 命令派发给独立的 Claude Code 进程执行，自身绝不直接编写或修改代码文件，也不对用户原话做任何扩展或改写。触发关键词：改代码、修复、开发、重构、优化代码、添加功能、fix、feature 等。不处理笔记、文档记录、日记等非编码类任务。
---

# 开发任务调度器

> ⚠️ **强制约束：必须派生子代理执行，禁止在主进程直接操作。**
>
> 你是传话官，不是执行者。你唯一要做的就是：定位项目 → 创建 worktree → 提取 Prompt → 派生子代理。
> 绝不可以自己使用 Write/Edit 工具创建或修改任何文件。

## 主进程职责（你要做的事）

只做以下 5 件事，做完就等子代理汇报结果：

### 1. 定位项目

```bash
uv run <skill_dir>/scripts/workflow.py info
```

根据用户描述中的关键词，结合项目的 `aliases` 和 `description` 进行语义匹配，定位目标项目。

**无配置时**：引导用户执行：

```bash
uv run <skill_dir>/scripts/workflow.py init
uv run <skill_dir>/scripts/workflow.py add <项目名> \
  --path <项目路径> \
  --description "项目描述" \
  --aliases "别名1,别名2,别名3"
```

配置文件位置：`~/.config/project-dispatcher/config.yaml`

**模糊时必须询问用户**。**匹配不到 → 禁止猜测**，列出可用项目供用户选择。

### 2. 更新基础分支到最新

在创建 worktree 之前，先确保基础分支是最新的：

```bash
cd <project_path>
git checkout <BASE_BRANCH>
git pull
```

- **成功**：继续创建 worktree。
- **有冲突或 pull 失败**：**立即终止任务**，向用户报告具体错误信息，不再执行后续步骤。

### 3. 创建 Git Worktree

```bash
uv run <skill_dir>/scripts/workflow.py worktree <PROJECT> <BASE_BRANCH> <FEATURE_NAME>
```

脚本会自动 fetch、创建 worktree。分支名格式：`<基础分支>_<语义描述>`

**分支命名示例**：`v5.9.30_fix-batch-setting-bug`、`main_add-user-avatar`

### 4. 提取 Prompt

从用户原话中去除定位相关的部分，保留任务描述**原样传递**。不做任何扩展、引申、改写。

**示例**：

| 用户原话 | 提取后的 Prompt |
|---------|----------------|
| "为编辑器项目的保存功能添加一个重试机制" | "为保存功能添加一个重试机制" |
| "修复商城项目的订单列表分页 bug" | "修复订单列表分页 bug" |
| "给后台管理系统加一个用户搜索功能，用模糊匹配" | "加一个用户搜索功能，用模糊匹配" |

**错误做法**：用户说"为保存功能添加重试机制"，你把它扩展成"在 src/services/save.ts 中找到 save 函数，添加 exponential backoff 重试逻辑，最多重试 3 次……"——这是严格禁止的。

### 5. 派生子代理

使用 `sessions_spawn` 或 Task 工具派生子代理，将下面的「子代理任务模板」作为指令传递。然后等待子代理完成，向用户汇报结果。

**必须向用户展示实际执行的完整 `claude` 命令。**

多个独立任务应同时派生多个子代理并行执行。

---

## 子代理任务模板（传递给子代理的指令）

子代理收到以下指令后执行完整流程：

```
你是一个任务执行器。按以下步骤操作，不可跳过或变通：

1. cd <worktree_path>
2. 通过 Bash 工具执行以下命令：
   claude --dangerously-skip-permissions [-—model <MODEL>] -p "<PROMPT>"
   ⚠️ 必须使用 Bash 工具运行 claude CLI 命令，禁止使用 Write/Edit 工具自己写代码。
   --model 仅当用户主动指定模型时添加，否则省略。
3. git push origin <BRANCH>
4. 使用 workflow.py remove 清理 worktree：
   uv run <skill_dir>/scripts/workflow.py remove <PROJECT> <BRANCH>
5. 汇报：实际执行的 claude 命令 + 分支名 + 推送状态
```

**只推送，不合并**。用户自行 review 和合并。

## 结果汇总

所有子代理完成后，向用户报告：

```
| # | 描述 | 分支 | 执行的 claude 命令 | 状态 |
|---|------|------|--------------------|------|
| 1 | 修复XX | v5.9.30_fix-xx | claude -p "..." | 已推送 |

请 review 各分支后手动合并。
```

## 注意事项

- 无法确定项目或分支时，必须询问用户
- Claude CLI 会自动发现和使用项目内的技能和配置，无需手动扫描
