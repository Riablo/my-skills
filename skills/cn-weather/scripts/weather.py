#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = ["pyyaml"]
# ///
"""中国城市天气查询 - 使用和风天气 (QWeather) API"""
import sys
import os
import json
import gzip
import urllib.request
import urllib.error
import urllib.parse
import argparse
from pathlib import Path

import yaml

API_HOST = "kk78m29h8w.re.qweatherapi.com"
CONFIG_PATH = Path.home() / ".config" / "cn-weather" / "config.yaml"


def load_api_key():
    """从配置文件读取 API Key"""
    if not CONFIG_PATH.exists():
        print(f"错误: 未找到配置文件 {CONFIG_PATH}", file=sys.stderr)
        print("请先运行: uv run weather.py init --api-key <YOUR_KEY>", file=sys.stderr)
        sys.exit(1)
    with open(CONFIG_PATH) as f:
        config = yaml.safe_load(f)
    key = config.get("api_key", "")
    if not key:
        print("错误: 配置文件中缺少 api_key", file=sys.stderr)
        sys.exit(1)
    return key


def api_request(url):
    """发送 API 请求并处理 gzip 压缩"""
    req = urllib.request.Request(url, headers={"Accept-Encoding": "gzip"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = resp.read()
        if resp.headers.get("Content-Encoding") == "gzip":
            data = gzip.decompress(data)
        return json.loads(data.decode("utf-8"))


def get_location_id(api_key, city):
    """通过城市名获取 Location ID"""
    url = f"https://{API_HOST}/geo/v2/city/lookup?location={urllib.parse.quote(city)}&key={api_key}"
    data = api_request(url)
    if data.get("code") == "200" and data.get("location"):
        return data["location"][0]
    print(f"未找到城市: {city}", file=sys.stderr)
    sys.exit(1)


def cmd_init(args):
    """初始化配置"""
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    config = {}
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            config = yaml.safe_load(f) or {}
    config["api_key"] = args.api_key
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False)
    print(f"API Key 已保存到 {CONFIG_PATH}")


def cmd_now(args):
    """查询实时天气"""
    api_key = load_api_key()
    location = get_location_id(api_key, args.city)
    url = f"https://{API_HOST}/v7/weather/now?location={location['id']}&key={api_key}"
    data = api_request(url)
    if data.get("code") == "200":
        now = data["now"]
        print(json.dumps({
            "city": location["name"],
            "temp": now["temp"],
            "feelsLike": now["feelsLike"],
            "text": now["text"],
            "humidity": now["humidity"],
            "windDir": now["windDir"],
            "windScale": now["windScale"],
            "vis": now["vis"],
            "updateTime": data["updateTime"],
        }, ensure_ascii=False, indent=2))
    else:
        print(f"获取天气失败: {data.get('code')}", file=sys.stderr)
        sys.exit(1)


def cmd_forecast(args):
    """查询3天天气预报"""
    api_key = load_api_key()
    location = get_location_id(api_key, args.city)
    url = f"https://{API_HOST}/v7/weather/3d?location={location['id']}&key={api_key}"
    data = api_request(url)
    if data.get("code") == "200":
        result = {"city": location["name"], "daily": []}
        for day in data["daily"]:
            result["daily"].append({
                "date": day["fxDate"],
                "textDay": day["textDay"],
                "textNight": day["textNight"],
                "tempMax": day["tempMax"],
                "tempMin": day["tempMin"],
                "windDirDay": day["windDirDay"],
                "windScaleDay": day["windScaleDay"],
                "uvIndex": day.get("uvIndex", "N/A"),
            })
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"获取预报失败: {data.get('code')}", file=sys.stderr)
        sys.exit(1)


def cmd_air(args):
    """查询空气质量"""
    api_key = load_api_key()
    location = get_location_id(api_key, args.city)
    url = f"https://{API_HOST}/v7/air/now?location={location['id']}&key={api_key}"
    try:
        data = api_request(url)
    except urllib.error.HTTPError as e:
        print(f"空气质量查询失败: HTTP {e.code}（可能需要付费订阅）", file=sys.stderr)
        sys.exit(1)
    if data.get("code") == "200":
        aqi = data["now"]
        print(json.dumps({
            "city": location["name"],
            "aqi": aqi["aqi"],
            "category": aqi["category"],
            "pm2p5": aqi["pm2p5"],
            "pm10": aqi["pm10"],
            "no2": aqi["no2"],
            "so2": aqi["so2"],
            "o3": aqi["o3"],
            "co": aqi["co"],
        }, ensure_ascii=False, indent=2))
    else:
        print("该城市暂不支持空气质量查询", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="中国城市天气查询")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init
    p_init = subparsers.add_parser("init", help="初始化 API Key 配置")
    p_init.add_argument("--api-key", required=True, help="和风天气 API Key")
    p_init.set_defaults(func=cmd_init)

    # now
    p_now = subparsers.add_parser("now", help="查询实时天气")
    p_now.add_argument("city", help="城市名称")
    p_now.set_defaults(func=cmd_now)

    # forecast
    p_forecast = subparsers.add_parser("forecast", help="查询3天天气预报")
    p_forecast.add_argument("city", help="城市名称")
    p_forecast.set_defaults(func=cmd_forecast)

    # air
    p_air = subparsers.add_parser("air", help="查询空气质量")
    p_air.add_argument("city", help="城市名称")
    p_air.set_defaults(func=cmd_air)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
