import os
import subprocess
import re
import json
import sys
from datetime import datetime

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

def get_file_icon(filename):
    """根据文件名或扩展名返回对应的 Emoji 图标"""
    fn_lower = filename.lower()

    # 1. 全名匹配 (优先级最高)
    full_name_mapping = {
        'dockerfile': '🐳',
        'docker-compose.yml': '🐳',
        'docker-compose.yaml': '🐳',
        'package.json': '📦',
        'package-lock.json': '🔒',
        'yarn.lock': '🔒',
        'pnpm-lock.yaml': '🔒',
        'composer.json': '📦',
        'composer.lock': '🔒',
        'requirements.txt': '📋',
        'makefile': '🛠️',
        'license': '⚖️',
        'readme.md': '📖',
        '.gitignore': '🚫',
        '.env': '🔑',
        '.editorconfig': '⚙️',
        '.prettierrc': '✨'
    }
    if fn_lower in full_name_mapping:
        return full_name_mapping[fn_lower]

    # 2. 扩展名匹配
    ext = os.path.splitext(fn_lower)[1]
    ext_mapping = {
        # 编程语言
        '.py': '🐍', '.js': '🟨', '.ts': '🟦', '.go': '🐹', '.rs': '🦀', 
        '.c': '🛠️', '.cpp': '🛠️', '.h': '🛠️', '.hpp': '🛠️', '.java': '☕', 
        '.php': '🐘', '.rb': '💎', '.swift': '🍎', '.kt': '🎯', '.dart': '🎯',
        '.sh': '📜', '.bat': '📜', '.ps1': '📜', '.sql': '🗄️', '.lua': '🌙',
        # Web
        '.html': '🌐', '.htm': '🌐', '.css': '🎨', '.scss': '🎨', '.sass': '🎨', '.less': '🎨',
        # 数据/配置
        '.json': '⚙️', '.yaml': '⚙️', '.yml': '⚙️', '.toml': '⚙️', '.xml': '⚙️',
        '.ini': '⚙️', '.conf': '⚙️', '.csv': '📊', '.xlsx': '📊', '.xls': '📊',
        # 文档
        '.md': '📝', '.txt': '📄', '.pdf': '📕', '.doc': '📘', '.docx': '📘',
        # 图片
        '.png': '🖼️', '.jpg': '🖼️', '.jpeg': '🖼️', '.gif': '🖼️', '.svg': '🖼️', 
        '.webp': '🖼️', '.ico': '🖼️', '.psd': '🎨', '.ai': '🎨',
        # 媒体
        '.mp3': '🎵', '.wav': '🎵', '.flac': '🎵', '.mp4': '🎬', '.avi': '🎬', '.mov': '🎬',
        # 压缩包
        '.zip': '📦', '.tar': '📦', '.gz': '📦', '.7z': '📦', '.rar': '📦',
        # 执行文件
        '.exe': '🚀', '.msi': '🚀', '.bin': '🚀', '.apk': '📱'
    }

    return ext_mapping.get(ext, '📄')

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

    # --- 4. 文件提取与分类 ---
    files_str = run_command(["git", "ls-files"])
    if not files_str:
        print("📭 仓库中没有被追踪的文件。")
        return
    
    files = files_str.splitlines()
    base_url = f"https://raw.githubusercontent.com/{user}/{repo}/refs/heads/{branch}/"
    
    # 按照文件夹对文件进行分组
    grouped_files = {}
    for f in files:
        if f.startswith("."): continue
        
        parts = f.split('/')
        folder = '/'.join(parts[:-1]) if len(parts) > 1 else "Root"
        
        if folder not in grouped_files:
            grouped_files[folder] = []
        grouped_files[folder].append(f)

    # --- 5. 构建 Markdown 内容 ---
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    md_content = [f"# 📦 {repo} Raw Links\n"]
    md_content.append(f"> **User**: `{user}` | **Branch**: `{branch}` | **Generated**: `{now_str}`\n")
    md_content.append("---")

    # 文件夹排序：Root 放在最前面，其他按字母顺序 (忽略大小写)
    sorted_folders = sorted(grouped_files.keys(), key=lambda x: (x != "Root", x.lower()))

    for folder in sorted_folders:
        md_content.append(f"\n## 📂 {folder}")
        # 对该文件夹下的文件进行排序 (忽略大小写)
        for f in sorted(grouped_files[folder], key=lambda x: os.path.basename(x).lower()):
            filename = os.path.basename(f)
            icon = get_file_icon(filename)
            url = f"{base_url}{f}"
            # 格式修改：文件名 (图标)
            # 紧接着下方显示 URL
            md_content.append(f"- {icon} **{filename}**")
            md_content.append(f"  `{url}`")

    # --- 6. 保存文件 ---
    links_dir = os.path.join(script_dir, "links")
    os.makedirs(links_dir, exist_ok=True)
    output_file = os.path.join(links_dir, f"{repo}.md")
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\n".join(md_content))

    print(f"\n✨ 生成成功！\n")
    print(f"👤 用户: {user} | 📦 仓库: {repo} | 🌿 分支: {branch}")
    print(f"🔗 生成链接: {len(files)}")
    print(f"📄 输出目录: {output_file}")

if __name__ == "__main__":
    main()
