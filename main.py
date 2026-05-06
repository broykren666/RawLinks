import os
import subprocess
import re

def run_command(cmd):
    """封装执行系统命令的逻辑"""
    try:
        return subprocess.check_output(cmd, stderr=subprocess.STDOUT).decode().strip()
    except Exception:
        return None

def get_remote_info():
    """自动从 git remote 解析用户名和仓库名"""
    remote_url = run_command(["git", "remote", "get-url", "origin"])
    if not remote_url:
        return None, None
    
    # 匹配 HTTPS 格式: https://github.com
    # 匹配 SSH 格式: git@github.com:user/repo.git
    pattern = r"github\.com[:/](.+?)/(.+?)(\.git)?$"
    match = re.search(pattern, remote_url)
    if match:
        user = match.group(1)
        repo = match.group(2).replace(".git", "")
        return user, repo
    return None, None

def main():
    # 1. 路径识别
    path = input("请输入 Git 项目本地路径 (回车表示当前目录): ").strip() or "."
    if not os.path.exists(os.path.join(path, ".git")):
        print("❌ 错误：该路径不是一个有效的 Git 仓库。")
        return
    os.chdir(path)

    # 2. 自动获取关键信息
    branch = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"]) or "main"
    auto_user, auto_repo = get_remote_info()

    # 3. 如果自动获取失败，才提示用户输入
    user = auto_user or input("未检测到远程配置，请输入 GitHub 用户名: ").strip()
    repo = auto_repo or input("未检测到远程配置，请输入仓库名: ").strip()

    print(f"🚀 正在处理: {user}/{repo} (分支: {branch})")

    # 4. 获取被追踪的文件列表 (遵循 .gitignore)
    files_str = run_command(["git", "ls-files"])
    if not files_str:
        print("📭 仓库中没有被追踪的文件。")
        return
    files = files_str.splitlines()

    # 5. 生成内容
    base_url = f"https://githubusercontent.com{user}/{repo}/refs/heads/{branch}/"
    markdown_content = [f"# {repo} 自动生成的 Raw 链接列表\n"]
    
    for file in files:
        if file.startswith("."): continue # 过滤隐藏文件如 .gitignore
        url = base_url + file
        markdown_content.append(f"- [{file}]({url})")

    # 6. 写入文件
    output_file = "RAW_LINKS.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(markdown_content))

    print(f"\n✨ 生成成功！已排除 .gitignore 中的文件。")
    print(f"📂 结果文件: {os.path.abspath(output_file)}")

if __name__ == "__main__":
    main()
