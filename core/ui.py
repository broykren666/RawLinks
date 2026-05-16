import sys

class ConsoleUI:
    @staticmethod
    def success(msg):
        # 绿色
        print(f"\033[92m{msg}\033[0m")

    @staticmethod
    def error(msg):
        # 红色
        print(f"\033[91m❌ {msg}\033[0m")

    @staticmethod
    def info(msg):
        # 蓝色
        print(f"\033[94m💡 {msg}\033[0m")

    @staticmethod
    def warning(msg):
        # 黄色
        print(f"\033[93m⚠️ {msg}\033[0m")

    @staticmethod
    def section(title):
        print(f"\n--- {title} ---")
