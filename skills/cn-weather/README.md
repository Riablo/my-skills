# CN-Weather 中国城市天气查询

使用[和风天气](https://dev.qweather.com/) API 查询中国各城市的实时天气、预报和空气质量。

## 前置要求

需要和风天气 API Key：

1. 访问 [dev.qweather.com](https://dev.qweather.com/) 注册账号
2. 创建应用，获取 **Web API Key**
3. 免费版每天可查询 1000 次

---

## 初始化配置

在 Claude Code 对话中发送：

```
/cn-weather init
```

或在终端手动初始化：

```bash
uv run ~/.claude/skills/cn-weather/scripts/weather.py init --api-key "YOUR_API_KEY"
```

API Key 保存在 `~/.config/cn-weather/config.yaml`，不会提交到仓库。

---

## 使用方式

直接在对话中询问即可：

```
北京今天天气怎么样？
```

```
上海未来三天天气预报
```

```
深圳空气质量如何？
```

---

## 查询类型

| 查询类型 | 说明 |
|----------|------|
| 实时天气 | 当前温度、体感温度、天气状况、湿度、风速 |
| 3 天预报 | 未来三天白天/夜间天气、最高/最低温度 |
| 空气质量 | AQI 指数、PM2.5、PM10、主要污染物 |

所有结果以 JSON 格式输出后由 AI 整理展示。

---

## 限制

- 仅支持中国城市
- 免费版：1000 次/天
