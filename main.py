import os
import subprocess
import re
import json

def run_command(cmd):
    try:
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode().strip()
    except:
        return None

def load_host_map(script_dir):
    """读取 host_user.js 并生成映射字典"""
    js_path = os.path.join(script_dir, "host_user.js")
    host_map = {}
    if os.path.exists(js_path):
        try:
            with open(js_path, "r", encoding="utf-8") as f:
                # 假设 JS 文件内容是纯 JSON 数组
                data = json.load(f)
                host_map = {item["host"]: item["user"] for item in data}
        except Exception as e:
            print(f"⚠️ 读取 host_user.js 失败: {e}")
    return host_map

def get_smart_info(host_map):
    """解析远程仓库并自动替换 Host 别名"""
    remote_url = run_command(["git", "remote", "get-url", "origin"])
    if not remote_url:
        return None, None

    # 1. 尝试匹配 SSH 格式: git@host_alias:user/repo.git
    ssh_match = re.search(r"git@(.+?):(.+?)/(.+?)(\.git)?$", remote_url)
    if ssh_match:
        host_part = ssh_match.group(1)
        user_part = ssh_match.group(2)
        repo_part = ssh_match.group(3).replace(".git", "")
        
        # 如果 host_part 在我们的映射表里，执行替换
        if host_part in host_map:
            print(f"🔄 检测到 SSH 别名 [{host_part}]，已自动映射为用户: {host_map[host_part]}")
            return host_map[host_part], repo_part
        return user_part, repo_part

    # 2. 尝试匹配 HTTPS 格式: https://github.com
    http_match = re.search(r"github\.com/(.+?)/(.+?)(\.git)?$", remote_url)
    if http_match:
        return http_match.group(1), http_match.group(2).replace(".git", "")

    return None, None

def main():
    # 获取脚本所在目录，用于定位 host_user.js
    script_dir = os.path.dirname(os.path.abspath(__file__))
    host_map = load_host_map(script_dir)

    path = input("请输入 Git 项目路径 (回车表示当前目录): ").strip() or "."
    if not os.path.exists(os.path.join(path, ".git")):
        print("❌ 错误：无效的 Git 仓库")
        return
    os.chdir(path)

    # 自动获取信息
    branch = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"]) or "main"
    user, repo = get_smart_info(host_map)

    if not user or not repo:
        print("❌ 无法自动获取用户信息，请手动检查远程仓库配置")
        user = input("请输入用户名: ")
        repo = input("请输入仓库名: ")

    # 获取文件并生成链接
    files = run_command(["git", "ls-files"]).splitlines()
    base_url = f"https://githubusercontent.com{user}/{repo}/refs/heads/{branch}/"
    
    md_list = [f"# {repo} Raw Links\n"]
    for f_path in files:
        if f_path.startswith("."): continue
        md_list.append(f"- [{f_path}]({base_url}{f_path})")

    with open("RAW_LINKS.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md_list))

    print(f"\n✅ 成功！已使用用户 [{user}] 生成 {len(md_list)-1} 个链接。")

if __name__ == "__main__":
    main()
