# Jenkins Builder

通过自然语言触发和监控 Jenkins 构建任务。说「部署 xxx」「发布 yyy feature/login 分支」，AI 自动匹配项目、触发构建、等待结果。

## 目录

- [前置要求](#前置要求)
- [安装技能](#安装技能)
- [两种使用场景](#两种使用场景)
- [Jenkins 端配置](#jenkins-端配置)
- [初始化凭据](#初始化凭据)
- [注册项目（OpenClaw 场景）](#注册项目openclaw-场景)
- [使用示例](#使用示例)
- [配置文件参考](#配置文件参考)

---

## 前置要求

| 依赖 | 说明 |
|------|------|
| [uv](https://docs.astral.sh/uv/) | Python 脚本运行器，`pip install uv` 或 `brew install uv` |
| Jenkins | 需要可访问的 Jenkins 实例，且 Job 支持 API 触发 |
| Claude Code | 需安装并登录 |

---

## 安装技能

将技能目录复制到 Claude Code 技能路径：

```bash
# 克隆到 my-skills 仓库（如果还没有）
git clone <your-skills-repo> ~/.claude/skills-repo

# 或直接软链 / 复制到 Claude Code 技能目录
cp -r skills/jenkins-builder ~/.claude/skills/jenkins-builder
```

> Claude Code 技能默认加载路径为 `~/.claude/skills/`，具体以你的 Claude Code 配置为准。

---

## 两种使用场景

本技能支持两种工作方式，配置需求略有不同：

### 场景一：在项目目录中运行 Claude Code

直接在项目根目录打开 Claude Code 会话。技能会自动读取当前目录下的 `.jenkins-build.yaml`，**无需注册项目**。

```
/your-project/          ← Claude Code 在这里运行
└── .jenkins-build.yaml ← 技能直接读取这个文件
```

适合：只需要构建单个项目，或习惯在项目目录中工作。

### 场景二：使用 OpenClaw

[OpenClaw](https://openclaw.ai) 的执行目录不在具体项目下，技能无法直接找到项目配置。此时需要将各项目**注册到全局配置**，技能会扫描所有注册的项目路径，合并所有 Job 供语义匹配。

```
~/.config/jenkins-builder/config.yaml
  └── projects:
        - /your-project-a/   ← 扫描这里的 .jenkins-build.yaml
        - /your-project-b/   ← 扫描这里的 .jenkins-build.yaml
```

适合：跨项目操作，或通过 OpenClaw 统一管理多个项目的构建。

---

## Jenkins 端配置

### 1. 创建 API Token

1. 登录 Jenkins → 右上角点击你的用户名 → **Configure**
2. 找到 **API Token** 区域 → 点击 **Add new Token**
3. 输入名称（如 `claude-code`）→ **Generate** → 复制 Token 值

> Token 只显示一次，生成后立即保存。

### 2. 配置 Job 构建方式

正式服和测试服使用不同的 API，Job 配置也不同：

**正式服 Job**

构建时使用固定分支（在 Job 的 SCM 配置中写死），触发时不传分支参数，使用普通 `build` API。无需参数化，保持默认配置即可。

**测试服 Job**

构建时需要动态指定分支，使用 `buildWithParameters` API 传入分支名，需要以下配置：

1. 勾选 **「This project is parameterized」**
2. 添加一个 **String Parameter**，名称固定为 `BRANCH_NAME`
3. 在 SCM 配置的 **Branch Specifier** 中填写 `${BRANCH_NAME}`，让 Jenkins 使用传入的分支名构建

### 3. 开放 API 权限

确认 Jenkins 全局安全设置中，你的用户对目标 Job 有以下权限：

- **Job / Build** — 触发构建
- **Job / Read** — 查询构建状态
- **Job / Workspace** — 读取控制台日志（可选，失败时用于提取错误）

---

## 初始化凭据

### 方式一：在对话中初始化（推荐）

直接在 Claude Code 对话中发送：

```
/jenkins-builder init
```

AI 会引导你输入 Jenkins URL、用户名和 API Token，自动完成配置。

### 方式二：手动在终端运行

```bash
uv run ~/.claude/skills/jenkins-builder/scripts/init.py credentials \
  --jenkins-url "https://jenkins.example.com" \
  --username "your-username" \
  --token "your-api-token"
```

凭据保存在 `~/.config/jenkins-builder/config.yaml`，权限自动设为 `600`。

### 方式三：手动编写配置文件

直接创建 `~/.config/jenkins-builder/config.yaml`：

```bash
mkdir -p ~/.config/jenkins-builder
```

```yaml
jenkins_url: "https://jenkins.example.com"
username: "your-username"
token: "your-api-token"
```

建议设置文件权限：

```bash
chmod 600 ~/.config/jenkins-builder/config.yaml
```

**验证配置：**

```bash
cat ~/.config/jenkins-builder/config.yaml
```

---

## 注册项目（OpenClaw 场景）

> 如果你在项目目录中直接运行 Claude Code，技能会自动读取当前目录的 `.jenkins-build.yaml`，**跳过此步骤**。
>
> 以下步骤仅适用于 **OpenClaw** 或其他执行目录不在项目下的场景。

每个需要通过 AI 构建的项目需要：

1. 在项目根目录生成配置模板
2. 填写 Job Name
3. 注册到全局配置

### 第一步：生成配置模板

```bash
cd /path/to/your-project
uv run ~/.claude/skills/jenkins-builder/scripts/config.py --template > .jenkins-build.yaml
```

### 第二步：编辑配置文件

打开 `.jenkins-build.yaml`，填写你的 Jenkins Job 名称：

```yaml
jobs:
  # key 是内部标识符，可自定义
  frontend:
    description: "前端 Web 应用"          # AI 语义匹配用的描述
    aliases: ["前端", "web", "h5"]        # 触发关键词，用户说这些词会匹配到该 job
    test:
      job_name: "test.frontend_build"     # 测试服 Jenkins Job 的完整名称
    prod:
      job_name: "frontend_build"          # 正式服 Jenkins Job 的完整名称

branch:
  default_test_branch: "master"           # 用户未指定分支时，测试服默认使用该分支
  auto_prefix: "*/"                       # 分支名自动添加的前缀（Jenkins 通配符格式）
```

> **Job Name 从哪里找？** 打开 Jenkins → 点击目标 Job → 地址栏中 `/job/` 后面的部分即为 Job Name。
> 如果 Job 在文件夹内，名称包含斜杠，如 `folder/my-job`。

### 第三步：注册项目

```bash
# 在项目根目录执行（自动读取当前目录）
uv run ~/.claude/skills/jenkins-builder/scripts/init.py register

# 或指定路径
uv run ~/.claude/skills/jenkins-builder/scripts/init.py register --dir /path/to/your-project
```

注册成功后，该项目路径会记录在 `~/.config/jenkins-builder/config.yaml` 的 `projects` 列表中。

---

## 使用示例

注册完成后，直接在 Claude Code 对话中说：

```
部署 前端 feature/login 分支
```

```
发布 web 项目到测试服，用 v2.1.0 版本
```

```
正式服发布前端
```

```
同时部署前端和后端 develop 分支
```

AI 会：

1. 读取配置，语义匹配项目名称
2. 测试服自动添加分支前缀（`feature/login` → `*/feature/login`）
3. 正式服**先向你确认**，再触发
4. 多个 Job 并行触发，后台运行不阻塞对话
5. 构建完成后报告结果，失败时展示错误日志摘要

### 环境判断规则

| 用户说了什么 | 触发环境 |
|------------|---------|
| 未提及环境 | 测试服 |
| "发布"、"部署"、"构建" | 测试服 |
| "正式服"、"生产环境"、"线上" | 正式服（需确认）|

---

## 配置文件参考

### `~/.config/jenkins-builder/config.yaml`（全局凭据）

```yaml
jenkins_url: "https://jenkins.example.com"
username: "your-username"
token: "your-api-token"
projects:
  - "/Users/you/projects/frontend"
  - "/Users/you/projects/backend"
```

### `.jenkins-build.yaml`（项目级配置）

```yaml
jobs:
  # 支持配置多个 Job
  frontend:
    description: "前端 Web 应用"
    aliases: ["前端", "web", "h5", "react"]
    test:
      job_name: "test.frontend_build"
    prod:
      job_name: "frontend_build"

  backend:
    description: "后端 API 服务"
    aliases: ["后端", "api", "server"]
    test:
      job_name: "test.backend_build"
    prod:
      job_name: "backend_build"

# branch 是顶层字段，不要放在 job 内部
branch:
  default_test_branch: "master"
  auto_prefix: "*/"
```

### 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| `jobs.<key>.description` | 推荐 | AI 语义匹配的主要依据 |
| `jobs.<key>.aliases` | 推荐 | 触发关键词列表，支持中英文 |
| `jobs.<key>.test.job_name` | 是 | 测试服 Jenkins Job 完整名称 |
| `jobs.<key>.prod.job_name` | 是 | 正式服 Jenkins Job 完整名称 |
| `branch.default_test_branch` | 否 | 测试服默认分支，默认 `master` |
| `branch.auto_prefix` | 否 | 分支前缀，默认 `*/` |

---

## 常见问题

**Q: 触发构建时报 403 错误？**
检查 Jenkins 用户权限，以及是否启用了 CSRF 保护（Crumb）。如果 Jenkins 开启了 Crumb，当前脚本不支持，需联系管理员关闭或调整。

**Q: AI 说「匹配不到项目」？**
确认你的 `.jenkins-build.yaml` 中 `aliases` 包含了你说的关键词，且该项目已通过 `init.py register` 注册。

**Q: 正式服没有询问确认就直接触发了？**
不会。技能强制要求正式服触发前向用户确认，这是内置约束。

**Q: 构建一直显示「等待中」？**
Jenkins Job 可能在队列中等待 executor。脚本最多重试 3 次，每次间隔 3-10 秒。如果 Jenkins 负载过高，可能需要等待更长时间。
