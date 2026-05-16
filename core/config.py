import os
import json

class ConfigManager:
    def __init__(self, script_dir):
        self.config_path = os.path.join(script_dir, "config.json")
        self.default_config = {
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
        self.config = self.load()

    def load(self):
        """加载或初始化配置"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    user_config = json.load(f)
                    # 深度合并
                    merged = self.default_config.copy()
                    for key, value in user_config.items():
                        if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                            merged[key].update(value)
                        else:
                            merged[key] = value
                    return merged
            except Exception as e:
                print(f"⚠️ 读取 config.json 失败: {e}")
        else:
            self.save(self.default_config)
            print(f"📝 已自动生成默认配置文件: {self.config_path}")
        return self.default_config

    def save(self, data):
        """保存配置到文件"""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ 保存配置文件失败: {e}")
