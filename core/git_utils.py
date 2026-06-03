import subprocess
import re

def run_command(cmd):
    """执行终端命令并返回输出字符串"""
    try:
        # 1. 显式指定编码为 utf-8，并处理解码错误，防止在 Windows 等环境下出现 UnicodeDecodeError
        # 2. 移除 check=True，手动处理返回码以获得更多信息
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            encoding="utf-8", 
            errors="replace", 
            check=False
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except Exception:
        # 极少数情况下（如命令不存在）会抛出异常
        return None

def check_git_installed():
    """检查系统是否安装了 Git"""
    return run_command(["git", "--version"]) is not None

def get_git_branches():
    """获取本地分支列表"""
    branches_str = run_command(["git", "branch", "--format=%(refname:short)"])
    return branches_str.splitlines() if branches_str else []

def get_git_remotes():
    """获取远端仓库列表"""
    remotes_str = run_command(["git", "remote"])
    return remotes_str.splitlines() if remotes_str else []

def parse_remote_info(remote_url, host_map_list):
    """解析远端 URL 提取用户名、仓库名、平台及域名"""
    # 兼容 SSH 和 HTTPS 格式
    # 1. SSH: [ssh://]git@host[:/]path/to/repo[.git]
    # 2. HTTP: http[s]://host/path/to/repo[.git]
    ssh_pattern = r"(?:ssh://)?git@([^:/]+)[:/](.+)$"
    http_pattern = r"https?://([^/]+)/(.+)$"
    
    ssh_match = re.search(ssh_pattern, remote_url)
    http_match = re.search(http_pattern, remote_url)
    
    domain, full_path = None, None
    if ssh_match:
        domain, full_path = ssh_match.group(1), ssh_match.group(2)
    elif http_match:
        domain, full_path = http_match.group(1), http_match.group(2)
        
    if domain and full_path:
        # 去掉末尾的 .git
        full_path = re.sub(r"\.git$", "", full_path)
        parts = full_path.split("/")
        
        # 默认解析：最后一部分是 repo，前面的是 user/group
        if len(parts) >= 2:
            user = "/".join(parts[:-1])
            repo = parts[-1]
        else:
            user = None
            repo = parts[0]
            
        mapped_domain = None
        mapped_platform = None
        # 查找 host_map 映射（优先根据 host 匹配）
        for item in host_map_list:
            if item.get("host") == domain:
                user = item.get("user", user)
                mapped_domain = item.get("domain") # 获取映射后的域名
                mapped_platform = item.get("platform") # 获取映射后的平台
                break
            
        if user and repo:
            # 平台识别
            platform = mapped_platform # 优先使用映射中指定的平台
            if not platform:
                # 优先根据映射后的域名识别，否则根据原始域名
                check_domain = (mapped_domain or domain or "").lower()
                if "github.com" in check_domain: platform = "github"
                elif "gitlab.com" in check_domain: platform = "gitlab"
                elif "gitee.com" in check_domain: platform = "gitee"
                elif "codeberg.org" in check_domain: platform = "codeberg"
                elif "bitbucket.org" in check_domain: platform = "bitbucket"
            
            return user, repo, platform, domain, mapped_domain
            
    return None, None, None, None, None
