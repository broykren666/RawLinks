import os
import sys
import subprocess
from core.ui import ConsoleUI as ui
from core.config import ConfigManager
from core.git_utils import (
    check_git_installed, run_command, get_git_branches, 
    get_git_remotes, parse_remote_info
)
from core.processor import RawLinkProcessor

def main():
    if not check_git_installed():
        ui.error("未检测到 Git 环境。")
        sys.exit(1)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_mgr = ConfigManager(script_dir)
    config = config_mgr.config

    # --- 路径识别 ---
    ui.section("路径选择")
    path = input("请输入 Git 项目路径 (回车表示当前目录): ").strip() or "."
    if not os.path.exists(os.path.join(path, ".git")):
        ui.error("该目录不是 Git 仓库。")
        return
    os.chdir(path)

    # --- 信息抓取与交互 ---
    ui.section("仓库信息配置")
    
    # 1. 分支选择
    branches = get_git_branches()
    current_branch = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"]) or "main"
    if len(branches) > 1:
        print("🌿 可用分支:")
        for i, b in enumerate(branches, 1):
            mark = "*" if b == current_branch else " "
            print(f"  {i}. {mark} {b}")
        branch_choice = input(f"请选择目标分支 (序号，直接回车使用 '{current_branch}'): ").strip()
        branch = branches[int(branch_choice) - 1] if branch_choice.isdigit() and 1 <= int(branch_choice) <= len(branches) else current_branch
    else:
        branch = current_branch
    ui.success(f"已选择分支: {branch}")

    # 2. 远端选择
    remotes = get_git_remotes()
    if not remotes:
        ui.error("该仓库尚未关联任何远端仓库。")
        ui.info("请先使用 `git remote add origin <url>` 关联远端仓库后再运行此脚本。")
        return

    if len(remotes) > 1:
        print("🌍 可用远端:")
        default_idx = next((i for i, r in enumerate(remotes, 1) if r == "origin"), 1)
        for i, r in enumerate(remotes, 1):
            print(f"  {i}. {r}")
        remote_choice = input(f"请选择远端 (序号，直接回车使用 '{remotes[default_idx-1]}'): ").strip()
        remote_name = remotes[int(remote_choice) - 1] if remote_choice.isdigit() and 1 <= int(remote_choice) <= len(remotes) else remotes[default_idx-1]
    else:
        remote_name = remotes[0]
    
    remote_url = run_command(["git", "remote", "get-url", remote_name])
    ui.success(f"已选择远端: {remote_name} ({remote_url})")

    # 3. 平台信息提取
    user, repo, platform, domain, mapped_domain = parse_remote_info(remote_url, config.get("host_map", []))
    
    if not platform:
        ui.warning("无法自动判断平台（GitHub/GitLab/Gitee/Codeberg/Bitbucket）。")
        choice = input("请选择平台 (1: GitHub, 2: GitLab, 3: Gitee, 4: Codeberg, 5: Bitbucket) [默认: 1]: ").strip()
        if choice == "2": platform = "gitlab"
        elif choice == "3": platform = "gitee"
        elif choice == "4": platform = "codeberg"
        elif choice == "5": platform = "bitbucket"
        else: platform = "github"

    if not user or not repo:
        ui.warning("无法自动获取用户或仓库信息。")
        user = user or input("请输入用户名: ").strip()
        repo = repo or input("请输入仓库名: ").strip()

    # 4. 构建 Base URL
    if platform == "github":
        # GitHub Raw 始终使用固定的 raw 域名
        base_url = f"https://raw.githubusercontent.com/{user}/{repo}/refs/heads/{branch}/"
    elif platform == "gitlab":
        # 优先级：1. 映射后的域名 -> 2. 原始域名 -> 3. 官方域名
        gl_host = mapped_domain or domain or "gitlab.com"
        base_url = f"https://{gl_host}/{user}/{repo}/-/raw/{branch}/"
    elif platform == "gitee":
        # 优先级：1. 映射后的域名 -> 2. 原始域名 -> 3. 官方域名
        gt_host = mapped_domain or domain or "gitee.com"
        base_url = f"https://{gt_host}/{user}/{repo}/raw/{branch}/"
    elif platform == "codeberg":
        # Codeberg (Forgejo/Gitea) 格式
        cb_host = mapped_domain or domain or "codeberg.org"
        base_url = f"https://{cb_host}/{user}/{repo}/raw/branch/{branch}/"
    elif platform == "bitbucket":
        # Bitbucket 格式
        bb_host = mapped_domain or domain or "bitbucket.org"
        base_url = f"https://{bb_host}/{user}/{repo}/raw/{branch}/"

    # --- 文件处理 ---
    ui.section("文件扫描与生成")
    processor = RawLinkProcessor(config)
    files_str = run_command(["git", "ls-files"])
    if not files_str:
        ui.warning("仓库中没有被追踪的文件。")
        return
    
    raw_files = files_str.splitlines()
    total_files = len(raw_files)
    grouped_files = {}
    processed_count = 0
    
    for f in raw_files:
        if processor.should_skip(f):
            continue
        processed_count += 1
        folder = '/'.join(f.split('/')[:-1]) if '/' in f else "Root"
        if folder not in grouped_files: grouped_files[folder] = []
        grouped_files[folder].append(f)

    ui.info(f"总文件数: {total_files} | 生成链接: {processed_count} | 过滤数量: {total_files - processed_count}")

    # --- 生成 Markdown ---
    md_content = processor.build_markdown(
        repo, user, branch, platform, total_files, 
        processed_count, grouped_files, base_url
    )

    # --- 保存 ---
    output_file = "link.md"
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(md_content)

    # 自动把link.md追加到项目路径下的忽略文件中
    gitignore_path = ".gitignore"
    gitignore_msg = ""
    try:
        if os.path.exists(gitignore_path):
            with open(gitignore_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.splitlines()
            if "link.md" not in lines:
                with open(gitignore_path, "a", encoding="utf-8") as f:
                    # 如果内容不为空且不以换行符结尾，先加一个换行符
                    if content and not content.endswith('\n'):
                        f.write("\n")
                    f.write("link.md\n")
                gitignore_msg = " (已更新 .gitignore)"
        else:
            with open(gitignore_path, "w", encoding="utf-8") as f:
                f.write("link.md\n")
            gitignore_msg = " (已创建 .gitignore 并添加忽略)"
    except Exception as e:
        ui.warning(f"无法更新 .gitignore: {e}")

    ui.section("生成报告")
    ui.success(f"生成成功！{gitignore_msg}")
    # print(f"项目平台: 🚀 平台:{platform.capitalize()} | 👤 用户:{user}")
    # print(f"仓库信息: 📦 仓库:{repo} | 🌿 分支:{branch}")
    # print(f"统计摘要: 📄 文件:{total_files} | 🔗 链接: {processed_count} | ⛓️‍💥 过滤: {total_files - processed_count}")
    # print(f"输出文件: {os.path.abspath(output_file)}")
    
    print(f"项目平台: 平台:{platform.capitalize()} | 用户:{user}")
    print(f"仓库信息: 仓库:{repo} | 分支:{branch}")
    print(f"统计摘要: 文件:{total_files} | 链接: {processed_count} | 过滤: {total_files - processed_count}")
    print(f"输出文件: {os.path.abspath(output_file)}")
    
    # 自动打开项目目录
    # try:
    #     project_dir = os.getcwd()
    #     if sys.platform == "win32":
    #         os.startfile(project_dir)
    #     elif sys.platform == "darwin":
    #         subprocess.run(["open", project_dir])
    #     else:
    #         subprocess.run(["xdg-open", project_dir])
    # except:
    #     pass

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 已退出。")
    except Exception as e:
        ui.error(f"运行出错: {e}")
