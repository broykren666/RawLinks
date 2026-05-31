# 📦 RawLinks

自动识别本地 Git 仓库，并生成一份包含该仓库所有文件 **Raw 链接** 的 Markdown 文档。

它目前支持 **GitHub**、**GitLab**、**Gitee** 和 **Codeberg** 平台。它不仅能自动分类文件夹，还能根据文件类型匹配精美的图标，非常适合用于分享资源、整理脚本清单或文档索引。

---

## ✨ 核心特性

- 🚀 **高度自动化**：自动识别 Git Remote URL，智能提取用户名、仓库名及当前分支。
- 📂 **智能分类**：按文件夹层级对文件进行分组，并支持“Root 目录”置顶显示。
- 🔍 **忽略大小写排序**：文件夹和文件均按字母顺序排序，符合人类浏览习惯。
- 🎨 **丰富图标**：内置强大的 Emoji 映射系统，支持 `Dockerfile`、`LICENSE` 等特定文件识别。
- ⚙️ **配置分离**：提供 `config.json`，无需修改源码即可自定义过滤规则、图标映射和主机配置。
- 🧹 **智能过滤**：自动跳过 `node_modules`、`.git`、缓存及二进制文件，支持显式保留 `.github` 等重要点文件。
- 📦 **零依赖**：仅需 Python 3 环境和 Git，无需安装任何第三方库。

---

## 🚀 快速开始

### 1. 准备环境

确保您的系统已安装：

- **Python 3.x**
- **Git** (已配置到环境变量)

### 2. 下载脚本

重命名 `e.config.json` 为`config.json`，将 `main.py` 和 `config.json` 放置在同一个目录下。

### 3. 运行脚本

在终端执行：

```bash
python main.py
```

### 4. 操作步骤

1. 输入本地 Git 项目的绝对路径（直接回车则表示当前目录）。
2. 脚本将自动识别信息。如果识别失败，会提示手动输入用户名和仓库名。
3. 检查生成的链接数量和输出路径。

---

## 🛠️ 配置说明 (`config.json`)

通过修改同目录下的 `config.json`，您可以完全掌控脚本的行为：

### 1. 过滤规则 (`filters`)

- `ignore_dirs`: 要跳过的目录名（如 `dist`, `build`）。
- `ignore_files`: 要跳过的特定文件名（如 `.DS_Store`）。
- `ignore_exts`: 要跳过的文件后缀（如 `.exe`, `.pyc`）。
- `include_dot_files`: 默认跳过所有 `.` 开头的文件，除非其路径包含在此名单中（如 `.github`）。

### 2. 图标映射 (`icons`)

- `full_name`: 针对特定文件名的精确匹配（优先级最高）。
- `extension`: 针对文件后缀的匹配。
- `default`: 未识别类型时的默认图标。

### 3. 主机映射 (`host_map`)

用于处理复杂的 SSH 别名。如果您在 `.gitconfig` 中配置了非标准 Host，可以在此建立对应关系。

---

## 📁 目录结构

```text
.
├── main.py            # 主逻辑脚本
├── config.json        # 配置文件 (图标、过滤、主机)
└── links/             # 自动生成的 Markdown 文件存放目录
    ├── MyRepo.md
    └── AnotherRepo.md
```

---

## 📄 输出示例

生成的 Markdown 文档格式如下：

```markdown
# 📦 MyRepo Raw Links
> **User**: `username` | **Branch**: `main` | **Generated**: `2023-10-27 10:30:00`

## 📂 Root
- 📖 **README.md**
  `https://raw.githubusercontent.com/user/repo/refs/heads/main/README.md`

## 📂 src/
- 🐍 **main.py**
  `https://raw.githubusercontent.com/user/repo/refs/heads/main/src/main.py`
```

---

## ⚖️ 许可证

根据 MIT 许可证分发。详情请参阅 `LICENSE`。
