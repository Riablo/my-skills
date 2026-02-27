# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml"]
# ///
"""
Jenkins Builder 初始化工具（非交互式）。

子命令:
  credentials  配置或更新 Jenkins 连接信息
  register     注册项目到全局列表

用法:
  uv run init.py credentials --jenkins-url URL --username USER --token TOKEN
  uv run init.py register --dir PATH
"""

import argparse
import os
import sys
from pathlib import Path

import yaml

CONFIG_DIR = Path.home() / ".config" / "jenkins-builder"
CONFIG_PATH = CONFIG_DIR / "config.yaml"


def cmd_credentials(args):
    """初始化配置 — 已有字段保留，只更新传入的字段"""
    creds = {}
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            creds = yaml.safe_load(f) or {}

    # 只更新明确传入的字段
    if args.jenkins_url:
        creds["jenkins_url"] = args.jenkins_url
    if args.username:
        creds["username"] = args.username
    if args.token:
        creds["token"] = args.token

    # 检查必填字段
    required = ["jenkins_url", "username", "token"]
    missing = [k for k in required if not creds.get(k)]
    if missing:
        print(f"错误: 缺少必填字段: {', '.join(missing)}", file=sys.stderr)
        print("用法: init.py credentials --jenkins-url URL --username USER --token TOKEN", file=sys.stderr)
        sys.exit(1)

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        yaml.dump(creds, f, default_flow_style=False, allow_unicode=True)
    os.chmod(CONFIG_PATH, 0o600)
    print(f"✓ 配置已保存: {CONFIG_PATH}")


def cmd_register(args):
    """注册项目路径到配置文件的 projects 列表"""
    project_dir = Path(args.dir).resolve() if args.dir else Path.cwd()

    if not project_dir.is_dir():
        print(f"错误: 目录不存在: {project_dir}", file=sys.stderr)
        sys.exit(1)

    if not CONFIG_PATH.exists():
        print(f"错误: 配置文件不存在: {CONFIG_PATH}", file=sys.stderr)
        print("请先运行: init.py credentials --jenkins-url URL --username USER --token TOKEN", file=sys.stderr)
        sys.exit(1)

    with open(CONFIG_PATH) as f:
        creds = yaml.safe_load(f) or {}

    project_path = str(project_dir)
    projects = creds.get("projects", [])

    if project_path in projects:
        print(f"✓ 项目已在列表中: {project_path}")
        return

    projects.append(project_path)
    creds["projects"] = projects

    with open(CONFIG_PATH, "w") as f:
        yaml.dump(creds, f, default_flow_style=False, allow_unicode=True)
    print(f"✓ 已注册: {project_path}")


def main():
    parser = argparse.ArgumentParser(description="Jenkins Builder 初始化工具")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # credentials
    p_cred = subparsers.add_parser("credentials", help="配置 Jenkins 连接信息")
    p_cred.add_argument("--jenkins-url", help="Jenkins URL")
    p_cred.add_argument("--username", help="用户名")
    p_cred.add_argument("--token", help="API Token")
    p_cred.set_defaults(func=cmd_credentials)

    # register
    p_reg = subparsers.add_parser("register", help="注册项目到全局列表")
    p_reg.add_argument("--dir", help="项目目录路径（默认当前目录）")
    p_reg.set_defaults(func=cmd_register)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
