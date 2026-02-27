# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 仓库用途

存放个人 AI 技能（Skills）集合，供 Claude Code 等 AI 工具调用。每个技能是一个独立的目录，定义 AI 在特定场景下的行为和工作流。

## 技能结构

每个技能位于 `skills/<skill-name>/` 下，必须包含：

- `SKILL.md` — 技能定义文件，顶部有 YAML frontmatter（`name`、`description`），正文是 AI 执行时遵循的指令
- 可选的辅助脚本（如 `scripts/`）、配置文件等

### SKILL.md frontmatter 格式

```yaml
---
name: skill-name
description: 触发条件和用途描述，AI 根据此字段判断何时调用该技能
---
```

## 新增技能

1. 在 `skills/` 下创建新目录，目录名即技能名
2. 编写 `SKILL.md`，frontmatter 的 `description` 要清晰描述触发场景
3. 在 `README.md` 的技能列表中补充说明

## Python 脚本规范

技能中的 Python 辅助脚本统一使用 `uv` 运行，脚本头部格式：

```python
#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///
```

调用方式：`uv run <script_path> [args]`

## 敏感信息管理

API Key、Token 等敏感信息**禁止**硬编码在代码或 SKILL.md 中，统一存放在用户级配置文件：

- 路径：`~/.config/<skill-name>/config.yaml`
- 格式：YAML
- 权限：建议 `chmod 600`

每个技能的脚本应提供 `init` 子命令用于初始化配置，示例：

```bash
uv run SKILL_DIR/scripts/<script>.py init --api-key "<KEY>"
```

SKILL.md 中只说明配置方法，不包含实际密钥值。

## 参考示例

`skills/720yun-workflow/` — 工作空间调度器技能，包含：
- `SKILL.md`：定义完整的 worktree 工作流（定位项目 → 创建 worktree → 启动 Claude Code → 推送 → 清理）
- `scripts/workflow.py`：辅助脚本，提供 `info`、`worktree`、`remove`、`list` 子命令
