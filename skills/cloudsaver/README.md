# CloudSaver

从 Telegram 频道搜索网盘资源，并将 115 网盘分享链接一键转存到个人网盘。

## 前置要求

### 安装 CloudSaver CLI

本技能依赖 [CloudSaver CLI](https://github.com/Riablo/CloudSaver)：

```bash
cd ~/Projects
git clone https://github.com/Riablo/CloudSaver.git
cd CloudSaver
npm install
npm run build
```

安装完成后确认 `~/Projects/CloudSaver/dist/index.js` 存在即可。

### 配置 Telegram 搜索频道

```bash
cloudsaver config --add-channel
```

按提示添加用于搜索资源的 Telegram 频道。

### 配置 115 Cookie（转存功能必须）

```bash
cloudsaver config --set-cookie
```

Cookie 保存在 `~/.config/cloudsaver/local.json`。搜索功能不需要 Cookie，只有转存 115 资源时才需要。

---

## 使用方式

直接在 Claude Code 对话中描述需求即可：

```
帮我搜一下《星际穿越》
```

```
找找低俗小说有没有115资源
```

```
转存这个115链接：https://115cdn.com/s/xxxxx?password=xxx
```

AI 会自动调用技能完成搜索或转存操作。

---

## 支持的网盘

| 网盘 | 搜索 | 转存 |
|------|:----:|:----:|
| 115 网盘 | ✅ | ✅ |
| 阿里云盘 | ✅ | ❌ |
| 夸克网盘 | ✅ | ❌ |
| 百度网盘 | ✅ | ❌ |
| 天翼云盘 | ✅ | ❌ |
| 123 云盘 | ✅ | ❌ |

搜索结果按 115 > 阿里云盘 > 夸克网盘优先排序。

---

## 配置文件位置

| 文件 | 用途 |
|------|------|
| `~/.config/cloudsaver/config.json` | 频道等全局配置 |
| `~/.config/cloudsaver/local.json` | 115 Cookie |
