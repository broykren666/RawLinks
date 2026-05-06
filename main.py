import os
import subprocess
import re
import json
import sys

def check_git_installed():
    """检查系统是否安装了 Git"""
    try:
        # 尝试运行 git --version
        subprocess.check_output(["git", "--version"], stderr=subprocess.STDOUT)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False

def run_command(cmd):
    try:
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode().strip()
    except:
        return None

def load_host_map(script_dir):
    js_path = os.path.join(script_dir, "host_user.js")
    host_map = {}
    if os.path.exists(js_path):
        try:
            with open(js_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                host_map = {item["host"]: item["user"] for item in data}
        except Exception as e:
            print(f"⚠️ 读取 host_user.js 失败: {e}")
    return host_map

def get_smart_info(host_map):
    remote_url = run_command(["git", "remote", "get-url", "origin"])
    if not remote_url:
        return None, None

    # 解析 SSH 别名逻辑
    ssh_match = re.search(r"git@(.+?):(.+?)/(.+?)(\.git)?$", remote_url)
    if ssh_match:
        host_part, user_part, repo_part = ssh_match.group(1), ssh_match.group(2), ssh_match.group(3)
        repo_part = repo_part.replace(".git", "")
        if host_part in host_map:
            return host_map[host_part], repo_part
        return user_part, repo_part

    # 解析 HTTPS 逻辑
    http_match = re.search(r"github\.com/(.+?)/(.+?)(\.git)?$", remote_url)
    if http_match:
        return http_match.group(1), http_match.group(2).replace(".git", "")

    return None, None

def main():
    # --- 1. 环境自检 ---
    if not check_git_installed():
        print("❌ 错误：未检测到 Git 环境。")
        print("👉 请先安装 Git 并配置到环境变量中。")
        print("🔗 下载地址: https://git-scm.com")
        sys.exit(1)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    host_map = load_host_map(script_dir)

    # --- 2. 路径识别 ---
    path = input("请输入 Git 项目路径 (回车表示当前目录): ").strip() or "."
    if not os.path.exists(os.path.join(path, ".git")):
        print("❌ 错误：该目录不是 Git 仓库或路径不存在。")
        return
    os.chdir(path)

    # --- 3. 自动抓取信息 ---
    branch = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"]) or "main"
    user, repo = get_smart_info(host_map)

    if not user or not repo:
        print("💡 无法从 remote 自动获取信息。")
        user = input("请输入用户名: ").strip()
        repo = input("请输入仓库名: ").strip()

    # --- 4. 文件提取与生成 ---
    files_str = run_command(["git", "ls-files"])
    if not files_str:
        print("📭 仓库中没有被追踪的文件。")
        return
    
    files = files_str.splitlines()
    base_url = f"https://raw.githubusercontent.com/{user}/{repo}/refs/heads/{branch}/"
    
    md_content = [f"# {repo} Raw Links (Branch: {branch})\n"]
    for f in files:
        if f.startswith("."): continue
        md_content.append(f"- [{f}]({base_url}{f})")

    output_file = "RAW_LINKS.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(md_content))

    print(f"\n✨ 生成成功！")
    print(f"👤 用户: {user} | 📦 仓库: {repo} | 🌿 分支: {branch}")
    print(f"📄 文件已保存至: {os.path.abspath(output_file)}")

if __name__ == "__main__":
    main()
