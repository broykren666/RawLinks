import os
import subprocess
import re
import json
import sys
from datetime import datetime

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
    """加载配置文件，若不存在则返回默认配置"""
    config_path = os.path.join(script_dir, "config.json")
    # 默认配置 (兜底)
    default_config = {
        "host_map": [],
        "filters": {
            "ignore_dirs": [".git", "node_modules", "__pycache__", "venv"],
            "ignore_files": [".DS_Store"],
            "ignore_exts": [".pyc"],
            "include_dot_files": [".gitignore", ".github"]
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
    return default_config

def get_smart_info(config):
    remote_url = run_command(["git", "remote", "get-url", "origin"])
    if not remote_url:
        return None, None

    # 从配置中获取 host_map
    host_map = {item["host"]: item["user"] for item in config.get("host_map", [])}

    # 解析 SSH 别名逻辑
    ssh_match = re.search(r"git@(.+?):(.+?)/(.+?)(\.git)?$", remote_url)
    if ssh_match:
        host_part, user_part, repo_part = ssh_match.group(1), ssh_match.group(2), ssh_match.group(3)
        repo_part = repo_part.replace(".git", "")
        if host_part in host_map and host_map[host_part]:
            return host_map[host_part], repo_part
        return user_part, repo_part

    # 解析 HTTPS 逻辑
    http_match = re.search(r"github\.com/(.+?)/(.+?)(\.git)?$", remote_url)
    if http_match:
        return http_match.group(1), http_match.group(2).replace(".git", "")

    return None, None

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

    # --- 信息抓取 ---
    branch = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"]) or "main"
    user, repo = get_smart_info(config)

    if not user or not repo:
        print("💡 无法自动获取信息。")
        user = user or input("请输入用户名: ").strip()
        repo = repo or input("请输入仓库名: ").strip()

    # --- 文件提取与分类 ---
    files_str = run_command(["git", "ls-files"])
    if not files_str:
        print("📭 仓库中没有被追踪的文件。")
        return
    
    raw_files = files_str.splitlines()
    base_url = f"https://raw.githubusercontent.com/{user}/{repo}/refs/heads/{branch}/"
    
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
    md_content = [f"# 📦 {repo} Raw Links\n"]
    md_content.append(f"> **User**: `{user}` | **Branch**: `{branch}` | **Generated**: `{now_str}`")
    md_content.append(f"> **Summary**: | **Files**: `{total_files}` | **Links**: `{processed_count}` | **Filtered**: `{total_files - processed_count}`\n")
    
    md_content.append("---")

    sorted_folders = sorted(grouped_files.keys(), key=lambda x: (x != "Root", x.lower()))

    for folder in sorted_folders:
        md_content.append(f"\n## 📂 {folder}")
        for f in sorted(grouped_files[folder], key=lambda x: os.path.basename(x).lower()):
            filename = os.path.basename(f)
            icon = get_file_icon(filename, config)
            url = f"{base_url}{f}"
            md_content.append(f"- {icon} **{filename}**")
            md_content.append(f"  ```\n  {url}\n  ```")

    # --- 保存文件 ---
    links_dir = os.path.join(script_dir, "links")
    os.makedirs(links_dir, exist_ok=True)
    
    # 防止冲突：使用 repo_branch 命名
    safe_branch = branch.replace("/", "_").replace("\\", "_")
    output_file = os.path.join(links_dir, f"{repo}_{safe_branch}.md")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(md_content))

    print(f"\n✨ 生成成功！\n")
    print(f"👤 用户: {user} | 📦 仓库: {repo} | 🌿 分支: {branch}")
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
