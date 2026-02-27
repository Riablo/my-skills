---
name: jenkins-builder
description: 触发和监控 Jenkins 构建任务。当用户提到构建、部署、发布项目时使用。支持语义匹配项目名称，自动读取项目配置文件确定 Job Name。未指定环境时默认测试服，仅当用户明确说「正式服」「生产环境」「线上」时才使用正式服 Job Name。匹配不到 Job 时禁止执行。
---

# Jenkins Builder

读取项目配置，触发 Jenkins 构建并监控结果。

## 这个技能只做一件事

**只触发 Jenkins 构建。不执行任何 git 操作（不创建分支、不 commit、不 push、不改任何文件）。**

用户说的"分支"和"版本"在这里是同一个意思——都是传给 Jenkins 的构建参数（branch 参数值），如 `feature/login`、`v2.1.0`。这不是 git 命令。

用户说的"发布""部署""构建""上线"在这里是同一个意思——都是触发 Jenkins 构建任务。

## 环境判断

**默认测试服。**

触发正式服的唯一条件：用户消息中明确含有「正式服」「生产环境」「线上」之一。

其他所有情况——无论用户说"发布"、"版本"、"分支"、还是什么都没说——都是测试服。

**正式服触发前必须向用户确认：**
> 即将触发**正式服**构建：`<job_name>`，确认继续？

用户确认后才执行。

**正式服不传分支参数**，Jenkins 使用固定默认分支。

## 必须使用子代理执行

所有构建**必须派生后台子代理**（Task tool, run_in_background: true）：
- 构建耗时 2-5 分钟，主会话不等待
- 多个 job 并行派生，同一消息发出所有 Task 调用

## 路径约定

`SKILL_DIR` 指本 SKILL.md 所在目录，可能是 `~/.claude/skills/jenkins-builder` 或 `skills/jenkins-builder`。

## 工作流

### 1. 读取配置

```bash
uv run SKILL_DIR/scripts/config.py
```

输出 JSON 包含所有可用 job 及别名。若提示无配置或配置缺失：

**初始化配置**（首次使用）：
```bash
uv run SKILL_DIR/scripts/init.py credentials --jenkins-url "URL" --username "USER" --token "TOKEN"
```

**注册项目**（每个项目一次）：
1. `uv run SKILL_DIR/scripts/config.py --template > .jenkins-build.yaml`
2. 询问用户填写 Job Name
3. `uv run SKILL_DIR/scripts/init.py register`

### 配置文件格式

```yaml
jobs:
  <job-key>:
    description: "描述文字"
    aliases: ["别名1", "别名2"]
    test:
      job_name: "测试服 Jenkins Job Name"
    prod:
      job_name: "正式服 Jenkins Job Name"

branch:
  default_test_branch: "master"
  auto_prefix: "*/"
```

`branch` 是顶层字段，不能放在 job 内部。

### 2. 语义匹配

按 `aliases` 和 `description` 匹配用户输入。一个词可匹配多个 job，全部并行触发。

**匹配不到 → 禁止执行**，告知用户列出可用 job，不得猜测替代。

### 3. 分支处理

- **测试服**：用户指定分支/版本 → 加 `auto_prefix`；未指定 → 用 `default_test_branch` + `auto_prefix`
- **正式服**：不传 `--branch`

示例：用户说 `v2.1.0` → 传 `*/v2.1.0`

### 4. 触发构建

**测试服**：
```bash
uv run SKILL_DIR/scripts/trigger_build.py --env test --job "<JOB_NAME>" --branch "<BRANCH>"
```

**正式服**：
```bash
uv run SKILL_DIR/scripts/trigger_build.py --env prod --job "<JOB_NAME>"
```

配置自动从 `~/.config/jenkins-builder/config.yaml` 读取。

### 5. 结果报告

- SUCCESS → 构建成功
- FAILURE → 构建失败 + 错误日志摘要
- ABORTED → 构建被取消

## 示例

> 用户：部署 <项目A> feature/login 分支
>
> 1. "分支"= Jenkins branch 参数，不是 git 操作
> 2. 未说正式服 → 测试服
> 3. 分支 feature/login → */feature/login
> 4. 派生子代理: `trigger_build.py --env test --job "..." --branch "*/feature/login"`

> 用户：发布 <项目A>（未说正式服）
>
> 1. 未说正式服 → 测试服，使用 default_test_branch
> 2. 匹配 <项目A> → 可能找到多个 job，全部并行触发

> 用户：正式服发布 <项目A>
>
> 1. 明确说了「正式服」→ prod job_name，不传分支
> 2. 先向用户确认，确认后执行

> 用户：发布 <项目X>（配置中无此 job）
>
> 1. 匹配 <项目X> → 无匹配
> 2. 禁止执行，告知用户可用 job 列表
