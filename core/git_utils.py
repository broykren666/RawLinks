import subprocess
import re

def run_command(cmd):
    """执行终端命令并返回输出字符串"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except:
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
    host_map = {item["host"]: item["user"] for item in host_map_list}
    
    # 兼容 SSH 和 HTTPS 格式
    ssh_pattern = r"git@([^:]+):([^/]+)/(.+?)(\.git)?$"
    http_pattern = r"https?://([^/]+)/([^/]+)/(.+?)(\.git)?$"
    
    ssh_match = re.search(ssh_pattern, remote_url)
    http_match = re.search(http_pattern, remote_url)
    
    domain, user, repo = None, None, None
    if ssh_match:
        domain, user, repo = ssh_match.group(1), ssh_match.group(2), ssh_match.group(3)
    elif http_match:
        domain, user, repo = http_match.group(1), http_match.group(2), http_match.group(3)
        
    if domain and user and repo:
        repo = repo.replace(".git", "")
        # 处理别名映射
        if domain in host_map and host_map[domain]:
            user = host_map[domain]
            
        platform = None
        d_lower = domain.lower()
        if "github.com" in d_lower: platform = "github"
        elif "gitlab.com" in d_lower: platform = "gitlab"
        elif "gitee.com" in d_lower: platform = "gitee"
        
        return user, repo, platform, domain
    return None, None, None, None
