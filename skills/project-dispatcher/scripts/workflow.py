#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.8"
# dependencies = ["pyyaml"]
# ///
"""project-dispatcher 工作流辅助脚本：项目定位、worktree 管理、配置初始化"""
import os
import sys
import subprocess
import json
import argparse
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "project-dispatcher"
CONFIG_FILE = CONFIG_DIR / "config.yaml"


def load_config():
    """加载配置文件，返回 dict。无配置文件时返回 None。"""
    if not CONFIG_FILE.exists():
        return None
    import yaml
    with open(CONFIG_FILE) as f:
        return yaml.safe_load(f) or {}


def save_config(config):
    """保存配置文件。"""
    import yaml
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    os.chmod(CONFIG_FILE, 0o600)


def require_config():
    """加载配置，无配置时报错退出。"""
    config = load_config()
    if config is None:
        print("错误: 未找到配置文件。请先运行 init 初始化：", file=sys.stderr)
        print(f"  uv run {sys.argv[0]} init", file=sys.stderr)
        sys.exit(1)
    return config


def get_projects(config):
    """从配置中获取项目字典。"""
    return config.get("projects", {})


def resolve_path(p):
    """解析路径，支持 ~ 展开。"""
    return Path(os.path.expanduser(p)).resolve()


def get_worktree_base(config, project_name, project_path):
    """获取 worktree 存放的基础目录。"""
    suffix = config.get("worktree", {}).get("dir_suffix", "-worktrees")
    return project_path.parent / f"{project_name}{suffix}"


# ── 子命令 ──────────────────────────────────────────────


def cmd_init(args):
    """初始化配置文件。"""
    if CONFIG_FILE.exists() and not args.force:
        print(f"配置文件已存在: {CONFIG_FILE}")
        print("使用 --force 覆盖。")
        return

    config = {
        "projects": {},
        "worktree": {
            "dir_suffix": "-worktrees",
        },
    }
    save_config(config)
    print(f"已创建配置文件: {CONFIG_FILE}")
    print(f"请使用 add 命令添加项目：")
    print(f'  uv run {sys.argv[0]} add <name> --path <path> --description "描述" --aliases "别名1,别名2"')


def cmd_add(args):
    """添加项目到配置。"""
    config = load_config()
    if config is None:
        config = {"projects": {}, "worktree": {"dir_suffix": "-worktrees"}}

    projects = config.setdefault("projects", {})

    path = resolve_path(args.path)
    aliases = [a.strip() for a in args.aliases.split(",") if a.strip()] if args.aliases else []

    projects[args.name] = {
        "path": str(path),
        "description": args.description or "",
        "aliases": aliases,
    }

    save_config(config)
    print(f"已添加项目: {args.name}")
    print(f"  路径: {path}")
    print(f"  描述: {args.description or '(无)'}")
    print(f"  别名: {aliases or '(无)'}")


def cmd_remove_project(args):
    """从配置中移除项目。"""
    config = require_config()
    projects = get_projects(config)

    if args.name not in projects:
        print(f"错误: 未找到项目 {args.name}", file=sys.stderr)
        print(f"可用项目: {', '.join(projects.keys()) or '(无)'}", file=sys.stderr)
        sys.exit(1)

    del config["projects"][args.name]
    save_config(config)
    print(f"已移除项目: {args.name}")


def cmd_info(args):
    """输出所有已配置项目的 JSON 信息。"""
    config = require_config()
    projects = get_projects(config)

    if not projects:
        print(json.dumps({"projects": {}, "message": "无已配置项目，请使用 add 命令添加。"}))
        return

    info = {}
    for name, proj in projects.items():
        path = resolve_path(proj["path"])
        exists = path.exists()
        git_dir = (path / ".git").exists() if exists else False

        branches = []
        if git_dir:
            try:
                result = subprocess.run(
                    ["git", "-C", str(path), "branch", "-a"],
                    capture_output=True, text=True,
                )
                branches = [
                    b.strip().replace("* ", "").replace("remotes/origin/", "")
                    for b in result.stdout.strip().split("\n")
                    if b.strip()
                ]
            except Exception:
                pass

        info[name] = {
            "path": str(path),
            "exists": exists,
            "git": git_dir,
            "branches": sorted(set(branches)),
            "description": proj.get("description", ""),
            "aliases": proj.get("aliases", []),
        }

    print(json.dumps(info, indent=2, ensure_ascii=False))


def cmd_worktree(args):
    """创建 worktree。"""
    config = require_config()
    projects = get_projects(config)

    if args.project not in projects:
        print(f"错误: 未知项目 {args.project}", file=sys.stderr)
        print(f"可用项目: {', '.join(projects.keys())}", file=sys.stderr)
        sys.exit(1)

    proj = projects[args.project]
    project_path = resolve_path(proj["path"])

    if not project_path.exists():
        print(f"错误: 项目目录不存在 {project_path}", file=sys.stderr)
        sys.exit(1)

    branch = f"{args.base_branch}_{args.feature_name}"
    worktree_base = get_worktree_base(config, args.project, project_path)
    worktree_path = worktree_base / branch

    if worktree_path.exists():
        print(f"错误: worktree 已存在 {worktree_path}", file=sys.stderr)
        sys.exit(1)

    worktree_base.mkdir(parents=True, exist_ok=True)

    # Fetch and update base branch
    subprocess.run(["git", "-C", str(project_path), "fetch", "origin"], capture_output=True)
    subprocess.run(["git", "-C", str(project_path), "checkout", args.base_branch], capture_output=True)
    subprocess.run(["git", "-C", str(project_path), "pull", "origin", args.base_branch], capture_output=True)

    # Create worktree
    cmd = [
        "git", "-C", str(project_path), "worktree", "add",
        "-b", branch,
        str(worktree_path),
        f"origin/{args.base_branch}",
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"错误: {result.stderr}", file=sys.stderr)
            sys.exit(1)

        print(json.dumps({
            "project": args.project,
            "branch": branch,
            "worktree": str(worktree_path),
            "base": args.base_branch,
        }, indent=2))

    except Exception as e:
        print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


def cmd_remove_worktree(args):
    """删除 worktree。"""
    config = require_config()
    projects = get_projects(config)

    if args.project not in projects:
        print(f"错误: 未知项目 {args.project}", file=sys.stderr)
        sys.exit(1)

    proj = projects[args.project]
    project_path = resolve_path(proj["path"])
    worktree_base = get_worktree_base(config, args.project, project_path)
    worktree_path = worktree_base / args.branch

    cmd = ["git", "-C", str(project_path), "worktree", "remove", str(worktree_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print(f"错误: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    print(f"已删除 worktree: {worktree_path}")


def cmd_list_worktrees(args):
    """列出 worktree。"""
    config = require_config()
    projects = get_projects(config)

    target = [args.project] if args.project and args.project in projects else list(projects.keys())

    for name in target:
        proj = projects[name]
        path = resolve_path(proj["path"])
        if not path.exists():
            continue
        try:
            result = subprocess.run(
                ["git", "-C", str(path), "worktree", "list"],
                capture_output=True, text=True,
            )
            if result.returncode == 0 and result.stdout.strip():
                print(f"\n{name}:")
                print(result.stdout)
        except Exception:
            pass


def main():
    parser = argparse.ArgumentParser(description="project-dispatcher 工作流辅助脚本")
    sub = parser.add_subparsers(dest="command")

    # init
    p_init = sub.add_parser("init", help="初始化配置文件")
    p_init.add_argument("--force", action="store_true", help="覆盖已有配置")

    # add
    p_add = sub.add_parser("add", help="添加项目到配置")
    p_add.add_argument("name", help="项目名称")
    p_add.add_argument("--path", required=True, help="项目路径")
    p_add.add_argument("--description", default="", help="项目描述")
    p_add.add_argument("--aliases", default="", help="别名列表，逗号分隔")

    # remove-project
    p_rmp = sub.add_parser("remove-project", help="从配置中移除项目")
    p_rmp.add_argument("name", help="项目名称")

    # info
    sub.add_parser("info", help="输出所有项目信息 (JSON)")

    # worktree
    p_wt = sub.add_parser("worktree", help="创建 worktree")
    p_wt.add_argument("project", help="项目名称")
    p_wt.add_argument("base_branch", help="基础分支")
    p_wt.add_argument("feature_name", help="功能名称")

    # remove
    p_rm = sub.add_parser("remove", help="删除 worktree")
    p_rm.add_argument("project", help="项目名称")
    p_rm.add_argument("branch", help="分支名")

    # list
    p_ls = sub.add_parser("list", help="列出 worktree")
    p_ls.add_argument("project", nargs="?", default=None, help="项目名称（可选）")

    args = parser.parse_args()

    commands = {
        "init": cmd_init,
        "add": cmd_add,
        "remove-project": cmd_remove_project,
        "info": cmd_info,
        "worktree": cmd_worktree,
        "remove": cmd_remove_worktree,
        "list": cmd_list_worktrees,
    }

    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
