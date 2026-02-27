#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = []
# ///
"""
快递取件提醒 - 主脚本
处理文字或图片输入，提取取件信息并添加到提醒事项
"""
import sys
import os
import re
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

def extract_from_text(text):
    """从文字中提取取件信息"""
    result = {
        'code': None,
        'location': None,
        'source': None,  # 快递公司/驿站
        'raw': text
    }

    # 提取取件码：常见格式
    # - 纯数字 6-8位
    # - 字母+数字组合
    # - 带"取件码"前缀
    # - 带横线分隔，如 25-3-4306
    patterns = [
        r'取件码[：:]?\s*([A-Za-z0-9\-]+)',  # 取件码: xxx 或 取件码xxx
        r'([0-9]{1,2}-[0-9]{1,2}-[0-9]{4,})',  # 格式如 25-3-4306
        r'([0-9]{6,8})',  # 6-8位数字
        r'([A-Z]{1,2}[0-9]{6,})',  # 字母+数字，如 A123456
        r'[码号][：:]\s*([A-Za-z0-9\-]+)',  # 码/号: xxx
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result['code'] = match.group(1)
            break

    # 提取存放地点
    location_patterns = [
        r'([\u4e00-\u9fa5]{2,}驿站)',  # xx驿站
        r'([\u4e00-\u9fa5]{2,}快递柜)',  # xx快递柜
        r'([\u4e00-\u9fa5]{2,}超市)',  # xx超市代收点
        r'([\u4e00-\u9fa5]{2,}门卫)',  # xx门卫
        r'([\u4e00-\u9fa5]{2,}前台)',  # xx前台
        r'丰巢[柜箱]?',  # 丰巢
        r'菜鸟[驿站]?',  # 菜鸟
        r'京东快递',  # 京东
        r'([\u4e00-\u9fa5]{2,}店)',  # xx店
    ]

    for pattern in location_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result['location'] = match.group(0)
            break

    # 提取快递公司
    express_patterns = [
        r'(顺丰|中通|圆通|申通|韵达|百世|极兔|京东|邮政|EMS|德邦|菜鸟|丰巢)',
    ]

    for pattern in express_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result['source'] = match.group(1)
            break

    return result

def calculate_reminder_time():
    """
    计算提醒时间
    - 11:00 前 → 当天 11:00
    - 11:00-17:00 → 当天 17:00
    - 17:00 后 → 明天 09:00
    """
    now = datetime.now()

    morning = now.replace(hour=11, minute=0, second=0, microsecond=0)
    afternoon = now.replace(hour=17, minute=0, second=0, microsecond=0)

    if now < morning:
        # 早上 11 点前，提醒 11 点
        return morning
    elif now < afternoon:
        # 11-17 点之间，提醒 17 点
        return afternoon
    else:
        # 17 点后，明天 9 点
        tomorrow = now + timedelta(days=1)
        return tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)

def add_to_reminders(info, reminder_time):
    """添加到 Apple Reminders"""
    # 构建提醒标题
    parts = []
    if info['source']:
        parts.append(f"【{info['source']}】")
    if info['code']:
        parts.append(f"取件码: {info['code']}")
    if info['location']:
        parts.append(f"@{info['location']}")

    if not parts:
        title = f"快递取件 - {info['raw'][:30]}"
    else:
        title = " ".join(parts)

    # 格式化时间 - 包含完整日期时间
    time_str = reminder_time.strftime('%Y-%m-%d %H:%M')
    # remindctl 支持 YYYY-MM-DD HH:mm 格式
    due_str = reminder_time.strftime('%Y-%m-%d %H:%M')

    # 构建 remindctl 命令
    cmd = [
        'remindctl', 'add',
        '--title', title,
        '--due', due_str,
        '--list', '快递取件'
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ 已添加提醒")
            print(f"📦 {title}")
            print(f"⏰ {time_str}")
            print(f"📝 列表: 快递取件")
            return True
        else:
            print(f"❌ 添加失败: {result.stderr}", file=sys.stderr)
            return False
    except Exception as e:
        print(f"❌ 执行失败: {e}", file=sys.stderr)
        return False

def main():
    if len(sys.argv) < 2:
        print("用法: uv run add_package.py \"<快递信息>\"")
        print("示例: uv run add_package.py \"您的快递已到菜鸟驿站，取件码123456\"")
        sys.exit(1)

    input_text = sys.argv[1]

    # 提取信息
    info = extract_from_text(input_text)

    # 检查是否提取到有效信息
    if not info['code'] and not info['location']:
        print("⚠️  未能提取到取件码或地点信息")
        print(f"原始内容: {input_text}")
        response = input("是否仍要添加提醒? (y/n): ")
        if response.lower() != 'y':
            sys.exit(0)

    # 计算提醒时间
    reminder_time = calculate_reminder_time()

    # 添加到提醒事项
    add_to_reminders(info, reminder_time)

if __name__ == '__main__':
    main()
