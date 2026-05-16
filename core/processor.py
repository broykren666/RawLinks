import os
from datetime import datetime
from urllib.parse import quote
from .git_utils import run_command

class RawLinkProcessor:
    """负责文件处理、过滤及 Markdown 生成的核心处理器"""
    def __init__(self, config):
        self.config = config
        self.filters = config.get("filters", {})
        self.icons = config.get("icons", {})

    def should_skip(self, file_path):
        """智能过滤逻辑"""
        parts = file_path.split('/')
        filename = parts[-1]
        fn_lower = filename.lower()
        
        # 1. 文件名忽略
        if fn_lower in [f.lower() for f in self.filters.get("ignore_files", [])]:
            return True
        
        # 2. 扩展名忽略
        ext = os.path.splitext(fn_lower)[1]
        if ext in [e.lower() for e in self.filters.get("ignore_exts", [])]:
            return True
        
        # 3. 目录忽略
        if any(d.lower() in [p.lower() for p in parts] for d in self.filters.get("ignore_dirs", [])):
            return True
        
        # 4. 点文件处理
        if filename.startswith('.') or any(p.startswith('.') for p in parts[:-1]):
            if any(inc.lower() in file_path.lower() for inc in self.filters.get("include_dot_files", [])):
                return False
            return True
        return False

    def get_file_icon(self, filename):
        """获取对应的图标"""
        fn_lower = filename.lower()
        if fn_lower in self.icons.get("full_name", {}):
            return self.icons["full_name"][fn_lower]
        ext = os.path.splitext(fn_lower)[1]
        if ext in self.icons.get("extension", {}):
            return self.icons["extension"][ext]
        return self.icons.get("default", "📄")

    def build_markdown(self, repo, user, branch, platform, total_files, processed_count, grouped_files, base_url):
        """构建最终的 Markdown 内容"""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        md = [f"# 📦 {repo}\n"]
        md.append(f"> **Generated**: `{now_str}` | **Files**: `{total_files}` | **Links**: `{processed_count}` | **Filtered**: `{total_files - processed_count}`")
        md.append(f"> **Platform**: `{platform.capitalize()}` | **User**: `{user}` | **Branch**: `{branch}`\n")
        md.append("---")

        sorted_folders = sorted(grouped_files.keys(), key=lambda x: (x != "Root", x.lower()))
        for folder in sorted_folders:
            md.append(f"\n## 📂 {folder}")
            for f in sorted(grouped_files[folder], key=lambda x: os.path.basename(x).lower()):
                filename = os.path.basename(f)
                icon = self.get_file_icon(filename)
                # 对路径进行 URL 编码，保留斜杠
                safe_path = quote(f, safe='/')
                url = f"{base_url}{safe_path}"
                md.append(f"- {icon} **{filename}**")
                md.append(f"  ```text\n  {url}\n  ```")
        return "\n".join(md)
