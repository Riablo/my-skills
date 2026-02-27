# my-skills

个人 AI 技能集合，供 Claude Code 等 AI 工具调用。

## 结构

```
skills/
  <skill-name>/
    SKILL.md          # 技能定义（必须）
    scripts/          # 辅助脚本（可选）
```

每个技能的 `SKILL.md` 顶部包含 YAML frontmatter，定义技能名称和触发条件，正文是 AI 执行时遵循的指令。

## 约定

**Python 脚本统一使用 `uv` 执行。** 所有技能中的 Python 辅助脚本均通过 `uv run <script>` 调用，无需手动安装依赖，`uv` 会自动处理。使用前请确保已安装 [uv](https://docs.astral.sh/uv/)：

```bash
brew install uv
# 或
pip install uv
```

## 特别声明

本项目仅供学习交流使用，请勿用于非法用途。

- 仅支持个人使用，不支持任何形式的商业使用
- 禁止在项目页面进行任何形式的广告宣传
- 所有涉及第三方服务的技能，其搜索到的资源均来自第三方，本项目不对其真实性、合法性做出任何保证

## 技能列表

### [cn-weather](skills/cn-weather/README.md)

中国城市天气查询。使用和风天气 (QWeather) API 查询实时天气、3天预报、空气质量。API Key 存放在 `~/.config/cn-weather/config.yaml`。

### [cloudsaver](skills/cloudsaver/README.md)

网盘资源搜索与115转存工具。从 Telegram 频道搜索115网盘、阿里云盘、夸克网盘等资源，并可直接转存115资源到个人网盘。依赖 [CloudSaver CLI](https://github.com/Riablo/CloudSaver)。

### [jenkins-builder](skills/jenkins-builder/README.md)

Jenkins 构建触发工具。通过语义匹配触发 Jenkins 构建任务，支持测试服/正式服环境、自动轮询构建状态、失败时提取错误日志。配置与凭据分离：项目级 `.jenkins-build.yaml` 定义 Job 映射，用户级 `~/.config/jenkins-builder/config.yaml` 存放敏感信息。

### [obsidian-dispatcher](skills/obsidian-dispatcher/README.md)

Obsidian 笔记任务调度器。将写笔记、整理知识、记录日志等任务派发到独立的 Claude Code 进程执行，完成后自动 git commit 并推送。

### [package-reminder](skills/package-reminder/README.md)

快递取件提醒工具。自动提取取件码和存放地点，按智能时间规则添加到 Apple Reminders。

### [project-dispatcher](skills/project-dispatcher/README.md)

开发任务调度器。语义匹配目标项目、创建 git worktree 隔离工作区，将编码任务派发到独立的 Claude Code 进程执行，完成后推送分支供 review 合并。
