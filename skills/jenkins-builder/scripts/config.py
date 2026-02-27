# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml"]
# ///
"""
Jenkins Builder 配置读取工具。

读取项目配置 + 凭据，输出合并后的 JSON 供 AI 解析。
AI 根据输出的 jobs 列表自行语义匹配用户意图。

用法:
  uv run config.py [--dir PATH]
  uv run config.py --template
"""

import argparse
import json
import sys
from pathlib import Path

import yaml

CONFIG_PATH = Path.home() / ".config" / "jenkins-builder" / "config.yaml"
CONFIG_FILENAME = ".jenkins-build.yaml"


def load_config() -> dict:
    """加载 ~/.config/jenkins-builder/config.yaml"""
    if not CONFIG_PATH.exists():
        print(f"错误: 配置文件不存在: {CONFIG_PATH}", file=sys.stderr)
        print("请运行 init.py 进行初始化", file=sys.stderr)
        sys.exit(1)
    with open(CONFIG_PATH) as f:
        data = yaml.safe_load(f) or {}
    required = ["jenkins_url", "username", "token"]
    missing = [k for k in required if not data.get(k)]
    if missing:
        print(f"错误: 配置文件缺少字段: {', '.join(missing)}", file=sys.stderr)
        sys.exit(1)
    return data


def load_project_config(project_dir: Path) -> dict | None:
    """加载项目目录下的 .jenkins-build.yaml，不存在返回 None"""
    config_path = project_dir / CONFIG_FILENAME
    if not config_path.exists():
        return None
    with open(config_path) as f:
        return yaml.safe_load(f) or {}


def merge_configs(global_config: dict, project_dir: Path | None = None) -> dict:
    """
    合并配置。

    - 如果 project_dir 下有配置文件 → 只读该项目
    - 否则 → 从 global_config 的 projects 列表扫描所有项目并合并
    """
    result = {
        "jenkins_url": global_config["jenkins_url"],
        "jobs": {},
        "branch": {},
        "mode": "single",
    }

    if project_dir:
        config = load_project_config(project_dir)
        if config:
            result["jobs"] = {
                k: {**v, "source": str(project_dir)}
                for k, v in config.get("jobs", {}).items()
            }
            result["branch"] = config.get("branch", {})
            return result

    # 全局模式：扫描 projects 列表
    projects = global_config.get("projects", [])
    if not projects:
        print("错误: 当前目录无配置文件，且配置文件中未配置 projects 列表", file=sys.stderr)
        sys.exit(1)

    result["mode"] = "global"

    for proj_path_str in projects:
        proj_path = Path(proj_path_str).expanduser()
        config = load_project_config(proj_path)
        if not config:
            print(f"警告: {proj_path} 下无 {CONFIG_FILENAME}，跳过", file=sys.stderr)
            continue
        branch = config.get("branch", {})
        for key, job in config.get("jobs", {}).items():
            global_key = f"{proj_path.name}:{key}"
            result["jobs"][global_key] = {**job, "source": str(proj_path), "branch": branch}

    return result


CONFIG_TEMPLATE = """\
# Jenkins 构建配置
# 格式说明: test/prod 下必须是 job_name: "..." 的字典结构
# branch 是顶层字段，不要放在 job 内部

jobs:
  example-job:
    description: "项目描述"
    aliases: ["别名1", "别名2"]
    test:
      job_name: "test.example_job"
    prod:
      job_name: "example_job"

branch:
  default_test_branch: "master"   # 测试服默认分支（用户未指定时使用）
  auto_prefix: "*/"               # 分支名自动前缀
"""


def main():
    parser = argparse.ArgumentParser(description="Jenkins Builder 配置读取")
    parser.add_argument("--dir", help="项目目录路径（默认当前目录）")
    parser.add_argument("--template", action="store_true", help="输出配置文件模板")
    args = parser.parse_args()

    if args.template:
        print(CONFIG_TEMPLATE, end="")
        return

    global_config = load_config()
    target_dir = Path(args.dir).resolve() if args.dir else Path.cwd()

    project_config = load_project_config(target_dir)
    merged = merge_configs(global_config, target_dir if project_config else None)
    print(json.dumps(merged, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
