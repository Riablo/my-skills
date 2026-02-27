# /// script
# requires-python = ">=3.10"
# dependencies = ["requests", "pyyaml"]
# ///
"""
Jenkins 构建触发与监控脚本。

触发 Jenkins 构建任务，轮询等待完成，失败时自动提取错误日志。

用法:
  uv run trigger_build.py --env test --job "test.my_project" --branch "*/v5.9.33"
  uv run trigger_build.py --env prod --job "my_project"
"""

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path
from urllib.parse import quote

import requests
import yaml

CONFIG_PATH = Path.home() / ".config" / "jenkins-builder" / "config.yaml"


def load_config(config_file: Path) -> dict:
    """加载凭据文件"""
    if not config_file.exists():
        return {}
    with open(config_file) as f:
        return yaml.safe_load(f) or {}


def extract_queue_id_from_url(url: str) -> str | None:
    """从 Jenkins queue URL 提取 queue ID"""
    match = re.search(r"/item/(\d+)", url)
    return match.group(1) if match else None


def trigger_build(jenkins_url: str, job_name: str, branch: str | None, auth: tuple) -> str:
    """触发构建，返回 queue ID"""
    encoded_job = quote(job_name, safe="")

    if branch:
        url = f"{jenkins_url}/job/{encoded_job}/buildWithParameters?BRANCH_NAME={branch}"
    else:
        url = f"{jenkins_url}/job/{encoded_job}/build"

    print(f"触发构建: {url}")
    response = requests.post(
        url,
        auth=auth,
        headers={"User-Agent": "Jenkins-Build-Script/2.0"},
        timeout=30,
    )
    response.raise_for_status()

    location = response.headers.get("Location")
    if not location:
        raise RuntimeError("响应中无 Location header")

    queue_id = extract_queue_id_from_url(location)
    if not queue_id:
        raise RuntimeError(f"无法从 URL 提取 queue ID: {location}")

    print(f"已加入队列, Queue ID: {queue_id}")
    return queue_id


def get_build_number(jenkins_url: str, queue_id: str, auth: tuple, max_retries: int = 3) -> int:
    """从队列获取 build number"""
    url = f"{jenkins_url}/queue/item/{queue_id}/api/json"

    for attempt in range(max_retries):
        delay = 3 if attempt == 0 else 10
        print(f"等待 {delay}s 检查队列状态... (第 {attempt + 1}/{max_retries} 次)")
        time.sleep(delay)

        try:
            response = requests.get(url, auth=auth, timeout=30)
            data = response.json()

            executable = data.get("executable")
            if executable and "number" in executable:
                build_number = executable["number"]
                print(f"构建已开始, Build Number: {build_number}")
                return build_number

            if data.get("cancelled"):
                raise RuntimeError("构建在队列中被取消")

            print(f"构建尚未开始: {data.get('why', '等待中...')}")

        except requests.RequestException as e:
            if attempt == max_retries - 1:
                raise RuntimeError(f"获取 build number 失败 ({max_retries} 次尝试): {e}")
            print(f"检查队列出错: {e}")

    raise RuntimeError("无法获取 build number，构建可能仍在队列中")


def get_console_log(jenkins_url: str, job_name: str, build_number: int, auth: tuple, tail_lines: int = 100) -> str:
    """获取构建控制台日志"""
    encoded_job = quote(job_name, safe="")
    url = f"{jenkins_url}/job/{encoded_job}/{build_number}/consoleText"

    try:
        response = requests.get(url, auth=auth, timeout=30)
        lines = response.text.split("\n")
        if len(lines) > tail_lines:
            lines = lines[-tail_lines:]
        return "\n".join(lines)
    except Exception as e:
        return f"获取控制台日志失败: {e}"


def extract_errors_from_log(log_text: str) -> str:
    """从控制台日志提取错误信息"""
    errors = []
    lines = log_text.split("\n")

    error_patterns = [
        r"ERROR\s+in",
        r"Error:",
        r"Failed",
        r"FAILED",
        r"Build step .* marked build as failure",
        r"Module not found:",
        r"Cannot find module",
        r"SyntaxError",
        r"TypeError",
        r"Compilation error",
    ]

    for i, line in enumerate(lines):
        for pattern in error_patterns:
            if re.search(pattern, line, re.IGNORECASE):
                context = "\n".join(lines[max(0, i) : min(len(lines), i + 5)])
                if context not in errors:
                    errors.append(context)
                break

    if errors:
        return "\n---\n".join(errors[-5:])
    return log_text[-2000:]


def poll_build_status(jenkins_url: str, job_name: str, build_number: int, auth: tuple, poll_interval: int = 5, timeout: int = 1200) -> dict:
    """轮询构建状态直到完成"""
    encoded_job = quote(job_name, safe="")
    url = f"{jenkins_url}/job/{encoded_job}/{build_number}/api/json"

    print(f"每 {poll_interval}s 轮询构建状态 (超时: {timeout}s)...")
    start_time = time.time()

    while True:
        if time.time() - start_time > timeout:
            return {"status": "timeout", "build_number": build_number, "result": "TIMEOUT"}
        try:
            response = requests.get(url, auth=auth, timeout=30)
            data = response.json()

            if data.get("inProgress", False):
                print(f"Build #{build_number} 进行中...")
                time.sleep(poll_interval)
                continue

            result = data.get("result")

            if result == "SUCCESS":
                print(f"✅ Build #{build_number} 成功")
                return {"status": "success", "build_number": build_number, "result": result}

            elif result == "FAILURE":
                print(f"❌ Build #{build_number} 失败")
                console_log = get_console_log(jenkins_url, job_name, build_number, auth)
                error_summary = extract_errors_from_log(console_log)
                print(f"\n错误摘要:\n{'=' * 50}")
                print(error_summary)
                print(f"{'=' * 50}")
                return {
                    "status": "failed",
                    "build_number": build_number,
                    "result": result,
                    "error_log": error_summary,
                }

            elif result == "ABORTED":
                print(f"⚠️ Build #{build_number} 被取消")
                return {"status": "aborted", "build_number": build_number, "result": result}

            else:
                print(f"⚠️ Build #{build_number} 未知结果: {result}")
                return {"status": "unknown", "build_number": build_number, "result": result}

        except requests.RequestException as e:
            print(f"轮询出错: {e}")
            time.sleep(poll_interval)


def main():
    parser = argparse.ArgumentParser(description="Jenkins 构建触发与监控")
    parser.add_argument("--job", required=True, help="Jenkins Job Name")
    parser.add_argument("--env", choices=["prod", "test"], required=True, help="环境: prod 或 test")
    parser.add_argument("--branch", help="分支名 (测试服必填)")
    parser.add_argument("--jenkins-url", help="Jenkins URL (默认从凭据文件读取)")
    parser.add_argument("--username", help="用户名 (默认从凭据文件读取)")
    parser.add_argument("--token", help="API Token (默认从凭据文件读取)")
    parser.add_argument(
        "--config-file",
        default=str(CONFIG_PATH),
        help=f"凭据文件路径 (默认: {CONFIG_PATH})",
    )
    parser.add_argument("--poll-interval", type=int, default=5, help="轮询间隔秒数 (默认: 5)")
    parser.add_argument("--timeout", type=int, default=1200, help="轮询超时秒数 (默认: 1200)")
    parser.add_argument("--json", action="store_true", help="仅输出 JSON 结果")

    args = parser.parse_args()

    # 凭据优先级: CLI > 环境变量 > config.yaml
    creds = load_config(Path(args.config_file))

    jenkins_url = (
        args.jenkins_url
        or os.environ.get("JENKINS_URL")
        or creds.get("jenkins_url")
    )
    username = (
        args.username
        or os.environ.get("JENKINS_USER")
        or creds.get("username")
    )
    token = (
        args.token
        or os.environ.get("JENKINS_TOKEN")
        or creds.get("token")
    )

    if not all([jenkins_url, username, token]):
        missing = []
        if not jenkins_url:
            missing.append("jenkins_url")
        if not username:
            missing.append("username")
        if not token:
            missing.append("token")
        print(f"错误: 缺少凭据: {', '.join(missing)}", file=sys.stderr)
        print(f"请配置 {CONFIG_PATH} 或通过命令行参数提供", file=sys.stderr)
        sys.exit(1)

    auth = (username, token)

    try:
        branch = args.branch
        queue_id = trigger_build(jenkins_url, args.job, branch, auth)
        build_number = get_build_number(jenkins_url, queue_id, auth)
        result = poll_build_status(jenkins_url, args.job, build_number, auth, args.poll_interval, args.timeout)

        if args.json:
            print(json.dumps(result, ensure_ascii=False))

        sys.exit(0 if result["status"] == "success" else 1)

    except Exception as e:
        if args.json:
            print(json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False))
        else:
            print(f"错误: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
