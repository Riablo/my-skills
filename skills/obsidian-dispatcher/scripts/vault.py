#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = ["pyyaml"]
# ///
"""obsidian-dispatcher 辅助脚本：Vault 配置管理"""
import os
import sys
import argparse
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "obsidian-dispatcher"
CONFIG_FILE = CONFIG_DIR / "config.yaml"


def resolve_path(p):
    """解析路径，支持 ~ 展开。"""
    return Path(os.path.expanduser(p)).resolve()


def cmd_init(args):
    """初始化配置文件。"""
    if CONFIG_FILE.exists() and not args.force:
        print(f"配置文件已存在: {CONFIG_FILE}")
        print("使用 --force 覆盖。")
        return

    if not args.vault_path:
        print("错误: 请指定 --vault-path", file=sys.stderr)
        sys.exit(1)

    vault_path = resolve_path(args.vault_path)
    if not vault_path.exists():
        print(f"错误: Vault 路径不存在 {vault_path}", file=sys.stderr)
        sys.exit(1)

    import yaml
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        yaml.dump({"vault_path": str(vault_path)}, f, allow_unicode=True)
    os.chmod(CONFIG_FILE, 0o600)
    print(f"已创建配置文件: {CONFIG_FILE}")
    print(f"Vault 路径: {vault_path}")


def cmd_path(args):
    """输出 Vault 路径。"""
    if not CONFIG_FILE.exists():
        print("错误: 未找到配置文件。请先运行 init 初始化：", file=sys.stderr)
        print(f"  uv run {sys.argv[0]} init --vault-path <VAULT_PATH>", file=sys.stderr)
        sys.exit(1)

    import yaml
    with open(CONFIG_FILE) as f:
        config = yaml.safe_load(f) or {}

    vault_path = config.get("vault_path", "")
    if not vault_path or not Path(vault_path).exists():
        print(f"错误: Vault 路径无效或不存在: {vault_path}", file=sys.stderr)
        sys.exit(1)

    print(vault_path)


def main():
    parser = argparse.ArgumentParser(description="obsidian-dispatcher Vault 辅助脚本")
    sub = parser.add_subparsers(dest="command")

    p_init = sub.add_parser("init", help="初始化配置文件")
    p_init.add_argument("--vault-path", required=False, help="Obsidian Vault 路径")
    p_init.add_argument("--force", action="store_true", help="覆盖已有配置")

    sub.add_parser("path", help="输出 Vault 路径")

    args = parser.parse_args()

    commands = {"init": cmd_init, "path": cmd_path}

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
