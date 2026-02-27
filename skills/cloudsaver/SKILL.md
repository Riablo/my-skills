---
name: cloudsaver
description: 网盘资源搜索与115转存工具。当用户需要搜索电影/电视剧/资源、转存115网盘资源、查找网盘分享链接时使用此skill。支持从Telegram频道搜索115网盘、阿里云盘、夸克网盘等资源，并可直接转存115资源到个人网盘。
---

# CloudSaver Skill

网盘资源搜索与115转存工具，封装了 [CloudSaver CLI](https://github.com/Riablo/CloudSaver) 的核心功能。

## 前置依赖

此技能依赖 CloudSaver CLI。如果尚未安装，执行搜索或转存时脚本会输出安装指引。

安装方式：

```bash
cd ~/Projects
git clone https://github.com/Riablo/CloudSaver.git
cd CloudSaver
npm install
npm run build
```

安装完成后，确保 `~/Projects/CloudSaver/dist/index.js` 存在即可。

如需全局命令，可额外执行 `npm link`。

## 功能

1. **搜索资源** - 从配置的Telegram频道搜索网盘资源
2. **115转存** - 将115网盘分享链接转存到个人网盘

## 使用方法

### 搜索资源

```bash
node SKILL_DIR/scripts/search.js "资源名称"

# 示例
node SKILL_DIR/scripts/search.js "星际穿越"
node SKILL_DIR/scripts/search.js "低俗小说"
```

### 转存115资源

```bash
node SKILL_DIR/scripts/save.js "115分享链接"

# 示例
node SKILL_DIR/scripts/save.js "https://115cdn.com/s/xxxxx?password=xxx"
```

## 配置

- **搜索频道**: 由 CloudSaver CLI 管理，运行 `cloudsaver config --add-channel` 配置
- **115 Cookie**: 存储在 `~/.config/cloudsaver/local.json`，运行 `cloudsaver config --set-cookie` 设置
- **配置文件**: `~/.config/cloudsaver/config.json`

## 支持的网盘

| 网盘 | 搜索 | 转存 |
|------|------|------|
| 115网盘 | ✅ | ✅ |
| 阿里云盘 | ✅ | ❌ |
| 夸克网盘 | ✅ | ❌ |
| 百度网盘 | ✅ | ❌ |
| 天翼云盘 | ✅ | ❌ |
| 123云盘 | ✅ | ❌ |

## 注意事项

- 转存115资源需要提前设置Cookie
- 搜索功能不需要Cookie即可使用
- 资源优先按115 > 阿里云盘 > 夸克网盘排序
