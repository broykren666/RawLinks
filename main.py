import os
import subprocess
import re
import json
import sys
from datetime import datetime
from urllib.parse import quote

def check_git_installed():
    """检查系统是否安装了 Git"""
    try:
        subprocess.check_output(["git", "--version"], stderr=subprocess.STDOUT)
        return True
    except:
        return False

def run_command(cmd):
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None
    except Exception:
        return None

def load_config(script_dir):
    """加载配置文件，若不存在则生成并返回默认配置"""
    config_path = os.path.join(script_dir, "config.json")
    
    # 使用你优化后的过滤规则作为默认配置
    default_config = {
        "host_map": [],
        "filters": {
            "ignore_dirs": ["node_modules", "__pycache__", "dist", "build", "target", ".git", ".idea", ".vscode", "venv", ".venv", "wheels", ".wrangler"],
            "ignore_files": [".DS_Store", "Thumbs.db", "desktop.ini", ".python-version", "uv.lock", "package-lock.json", ".env", ".dev.vars"],
            "ignore_exts": [".pyc", ".pyo", ".exe", ".dll", ".obj", ".bin"],
            "include_dot_files": [".github", ".env.example", ".editorconfig", ".prettierrc"]
        },
        "icons": {
            "full_name": {"readme.md": "📖"},
            "extension": {".py": "🐍", ".md": "📝"},
            "default": "📄"
        }
    }
    
    if os.path.exists(config_path):
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                user_config = json.load(f)
                # 简单合并配置
                for key in default_config:
                    if key in user_config:
                        if isinstance(default_config[key], dict):
                            default_config[key].update(user_config[key])
                        else:
                            default_config[key] = user_config[key]
                return default_config
        except Exception as e:
            print(f"⚠️ 读取 config.json 失败: {e}，将使用默认配置。")
    else:
        # 自动生成配置文件
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(default_config, f, indent=4, ensure_ascii=False)
            print(f"📝 已自动生成默认配置文件: {config_path}")
        except Exception as e:
            print(f"⚠️ 自动生成配置文件失败: {e}")
            
    return default_config

def get_smart_info(remote_url, config):
    if not remote_url:
        return None, None, None, None

    # 从配置中获取 host_map
    host_map = {item["host"]: item["user"] for item in config.get("host_map", [])}

    # 尝试匹配多种格式 (SSH 和 HTTPS)
    # Pattern 1: SSH (git@domain:user/repo.git)
    ssh_match = re.search(r"git@([^:]+):([^/]+)/(.+?)(\.git)?$", remote_url)
    # Pattern 2: HTTPS (https://domain/user/repo.git)
    http_match = re.search(r"https?://([^/]+)/([^/]+)/(.+?)(\.git)?$", remote_url)
    
    domain, user, repo = None, None, None
    
    if ssh_match:
        domain, user, repo = ssh_match.group(1), ssh_match.group(2), ssh_match.group(3)
    elif http_match:
        domain, user, repo = http_match.group(1), http_match.group(2), http_match.group(3)
        
    if domain and user and repo:
        repo = repo.replace(".git", "")
        # 处理 SSH 别名映射
        if domain in host_map and host_map[domain]:
            user = host_map[domain]
            
        # 平台识别
        platform = None
        d_lower = domain.lower()
        if "github.com" in d_lower: platform = "github"
        elif "gitlab.com" in d_lower: platform = "gitlab"
        elif "gitee.com" in d_lower: platform = "gitee"
        
        return user, repo, platform, domain

    return None, None, None, None

def should_skip(file_path, config):
    """智能过滤逻辑"""
    filters = config.get("filters", {})
    parts = file_path.split('/')
    filename = parts[-1]
    fn_lower = filename.lower()
    
    # 1. 检查是否在忽略的文件名中
    if fn_lower in [f.lower() for f in filters.get("ignore_files", [])]:
        return True
    
    # 2. 检查扩展名
    ext = os.path.splitext(fn_lower)[1]
    if ext in [e.lower() for e in filters.get("ignore_exts", [])]:
        return True
    
    # 3. 检查路径中是否包含被忽略的目录
    if any(d.lower() in [p.lower() for p in parts] for d in filters.get("ignore_dirs", [])):
        return True
    
    # 4. 处理点文件逻辑
    if filename.startswith('.') or any(p.startswith('.') for p in parts[:-1]):
        # 显式保留
        if any(inc.lower() in file_path.lower() for inc in filters.get("include_dot_files", [])):
            return False
        return True
        
    return False

def get_file_icon(filename, config):
    """根据配置获取图标"""
    icons = config.get("icons", {})
    fn_lower = filename.lower()
    
    # 1. 全名匹配
    if fn_lower in icons.get("full_name", {}):
        return icons["full_name"][fn_lower]
        
    # 2. 扩展名匹配
    ext = os.path.splitext(fn_lower)[1]
    if ext in icons.get("extension", {}):
        return icons["extension"][ext]
        
    return icons.get("default", "📄")

def main():
    if not check_git_installed():
        print("❌ 错误：未检测到 Git 环境。")
        sys.exit(1)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    config = load_config(script_dir)

    # --- 路径识别 ---
    path = input("请输入 Git 项目路径 (回车表示当前目录): ").strip() or "."
    if not os.path.exists(os.path.join(path, ".git")):
        print("❌ 错误：该目录不是 Git 仓库。")
        return
    os.chdir(path)

    # --- 分支识别与选择 ---
    branches_str = run_command(["git", "branch", "--format=%(refname:short)"])
    branches = branches_str.splitlines() if branches_str else []
    current_branch = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"]) or "main"
    
    if len(branches) > 1:
        print("\n🌿 可用分支:")
        for i, b in enumerate(branches, 1):
            mark = "*" if b == current_branch else " "
            print(f"  {i}. {mark} {b}")
        branch_choice = input(f"请选择目标分支 (序号，直接回车使用 '{current_branch}'): ").strip()
        if branch_choice.isdigit() and 1 <= int(branch_choice) <= len(branches):
            branch = branches[int(branch_choice) - 1]
        else:
            branch = current_branch
    else:
        branch = current_branch

    # --- 远端仓库识别 ---
    remotes_str = run_command(["git", "remote"])
    remotes = remotes_str.splitlines() if remotes_str else []
    
    if not remotes:
        print("❌ 错误：该仓库尚未关联任何远端仓库。")
        print("💡 请先使用 `git remote add origin <url>` 关联远端仓库后再运行此脚本。")
        return

    if len(remotes) > 1:
        print("\n🌍 可用远端:")
        default_remote_idx = 1
        for i, r in enumerate(remotes, 1):
            if r == "origin": default_remote_idx = i
            print(f"  {i}. {r}")
        
        default_name = remotes[default_remote_idx - 1]
        remote_choice = input(f"请选择要使用的远端 (序号，直接回车使用 '{default_name}'): ").strip()
        if remote_choice.isdigit() and 1 <= int(remote_choice) <= len(remotes):
            remote_name = remotes[int(remote_choice) - 1]
        else:
            remote_name = default_name
    else:
        remote_name = remotes[0]
    
    remote_url = run_command(["git", "remote", "get-url", remote_name])
    if not remote_url:
        print(f"❌ 错误：无法获取远端 '{remote_name}' 的 URL。")
        return

    user, repo, platform, domain = get_smart_info(remote_url, config)

    # 平台识别回退逻辑
    if not platform:
        print("💡 无法自动判断平台（GitHub/GitLab/Gitee）。")
        choice = input("请选择平台 (1: GitHub, 2: GitLab, 3: Gitee) [默认: 1]: ").strip()
        if choice == "2":
            platform = "gitlab"
        elif choice == "3":
            platform = "gitee"
        else:
            platform = "github"

    if not user or not repo:
        print("💡 无法自动获取用户或仓库信息。")
        user = user or input("请输入用户名: ").strip()
        repo = repo or input("请输入仓库名: ").strip()

    # --- 构建 Base URL ---
    if platform == "github":
        base_url = f"https://raw.githubusercontent.com/{user}/{repo}/refs/heads/{branch}/"
    elif platform == "gitlab":
        # 优先使用检测到的域名，支持私有部署
        gl_host = domain if domain else "gitlab.com"
        base_url = f"https://{gl_host}/{user}/{repo}/-/raw/{branch}/"
    elif platform == "gitee":
        base_url = f"https://gitee.com/{user}/{repo}/raw/{branch}/"
    else:
        # 兜底 GitHub
        base_url = f"https://raw.githubusercontent.com/{user}/{repo}/refs/heads/{branch}/"

    # --- 文件提取与分类 ---
    files_str = run_command(["git", "ls-files"])
    if not files_str:
        print("📭 仓库中没有被追踪的文件。")
        return
    
    raw_files = files_str.splitlines()
    
    grouped_files = {}
    total_files = len(raw_files)
    processed_count = 0
    
    for f in raw_files:
        if should_skip(f, config):
            continue
        
        processed_count += 1
        parts = f.split('/')
        folder = '/'.join(parts[:-1]) if len(parts) > 1 else "Root"
        
        if folder not in grouped_files:
            grouped_files[folder] = []
        grouped_files[folder].append(f)

    # --- 构建 Markdown ---
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    md_content = [f"# 📦 {repo}\n"]
    md_content.append(f"> **Generated**: `{now_str}` | **Files**: `{total_files}` | **Links**: `{processed_count}` | **Filtered**: `{total_files - processed_count}`")
    md_content.append(f"> **Platform**: `{platform.capitalize()}` | **User**: `{user}` | **Branch**: `{branch}`\n")
    
    md_content.append("---")

    sorted_folders = sorted(grouped_files.keys(), key=lambda x: (x != "Root", x.lower()))

    for folder in sorted_folders:
        md_content.append(f"\n## 📂 {folder}")
        for f in sorted(grouped_files[folder], key=lambda x: os.path.basename(x).lower()):
            filename = os.path.basename(f)
            icon = get_file_icon(filename, config)
            # 对路径进行 URL 编码，保留斜杠
            safe_path = quote(f, safe='/')
            url = f"{base_url}{safe_path}"
            md_content.append(f"- {icon} **{filename}**")
            md_content.append(f"  ```text\n  {url}\n  ```")

    # --- 保存文件 ---
    links_dir = os.path.join(script_dir, "links")
    os.makedirs(links_dir, exist_ok=True)
    
    # 防止冲突：使用 repo_branch 命名
    safe_branch = branch.replace("/", "_").replace("\\", "_")
    output_file = os.path.join(links_dir, f"{repo}_{safe_branch}.md")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(md_content))

    print(f"\n✨ 生成成功！\n")
    print(f"🌍 平台: {platform.capitalize()} | 👤 用户: {user} | 📦 仓库: {repo} | 🌿 分支: {branch}")
    print(f"🔗 生成链接: {processed_count} (过滤掉 {total_files - processed_count} 个文件)")
    print(f"📄 输出文件: {output_file}")

    # 自动打开目录
    try:
        if sys.platform == "win32":
            os.startfile(links_dir)
        elif sys.platform == "darwin":
            subprocess.run(["open", links_dir])
        else:
            subprocess.run(["xdg-open", links_dir])
    except:
        pass

if __name__ == "__main__":
    main()
