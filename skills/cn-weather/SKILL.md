---
name: cn-weather
description: 查询中国各城市天气信息，使用和风天气(QWeather) API。支持实时天气、天气预报、空气质量查询。当用户询问中国城市天气时使用此技能。
---

# 中国天气查询 (CN-Weather)

使用和风天气 API 查询中国各城市天气。

## 路径约定

`SKILL_DIR` 指本 SKILL.md 所在目录。

## 首次配置

```bash
uv run SKILL_DIR/scripts/weather.py init --api-key "<YOUR_QWEATHER_API_KEY>"
```

API Key 保存在 `~/.config/cn-weather/config.yaml`，不会提交到仓库。

如需获取 API Key：
1. 访问 https://dev.qweather.com/
2. 注册账号并创建应用
3. 获取 Web API Key

## 使用方法

### 查询实时天气

```bash
uv run SKILL_DIR/scripts/weather.py now <城市名>
```

### 查询3天预报

```bash
uv run SKILL_DIR/scripts/weather.py forecast <城市名>
```

### 查询空气质量

```bash
uv run SKILL_DIR/scripts/weather.py air <城市名>
```

## 输出格式

所有查询结果以 JSON 格式输出，方便解析和展示。

## 限制

- 免费版: 1000次/天
- 仅支持中国城市

API 文档: https://dev.qweather.com/docs/api/
