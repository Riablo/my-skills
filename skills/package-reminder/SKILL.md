---
name: package-reminder
description: 处理快递取件提醒，从文字或图片中提取取件码、存放地点等信息，自动计算提醒时间并添加到 Apple Reminders。当用户提到快递、取件码、驿站、快递柜等关键词时使用此 skill。
---

# 快递取件提醒 (Package Reminder)

自动提取快递信息并添加到提醒事项，确保不会忘记取件。

## 功能

- ✅ **文字输入**: 直接发送快递短信/通知内容
- ✅ **图片输入**: 识别快递柜/驿站的取件码截图
- ✅ **智能时间**: 根据当前时间自动选择 11:00、17:00 或次日 9:00
- ✅ **信息提取**: 自动识别取件码、存放地点、快递公司

## 使用方法

### 文字录入

```bash
uv run scripts/add_package.py "您的快递已到菜鸟驿站，取件码123456"
```

### 图片录入

```bash
uv run scripts/add_package_from_image.py /path/to/image.jpg
```

## 时间规则

| 当前时间 | 提醒时间 |
|----------|----------|
| 00:00 - 11:00 | 当天 11:00 |
| 11:00 - 17:00 | 当天 17:00 |
| 17:00 - 24:00 | 次日 09:00 |

## 识别能力

**取件码格式:**
- 6-8 位纯数字
- 字母+数字组合 (如 A123456)
- 带"取件码"前缀

**存放地点:**
- 菜鸟驿站、丰巢柜、快递柜
- 门卫、前台、超市代收点
- 京东快递、驿站等

**快递公司:**
- 顺丰、中通、圆通、申通、韵达
- 百世、极兔、京东、邮政、EMS

## 依赖

- Python 3
- uv (Python 包管理器)
- remindctl (Apple Reminders CLI)
- Tesseract OCR (可选，用于图片识别)

## 安装 OCR (可选)

```bash
brew install tesseract tesseract-lang
```

## 配置

确保 remindctl 已安装并有权限访问 Reminders：

```bash
brew install steipete/tap/remindctl
remindctl authorize  # 授权访问
```

首次使用会自动创建「快递取件」列表。

## 文件结构

```
package-reminder/
├── SKILL.md
└── scripts/
    ├── add_package.py           # 文字处理
    └── add_package_from_image.py # 图片处理
```
