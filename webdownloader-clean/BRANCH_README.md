# WebDownloader - 干净分支版本

> 这是一个经过整理的干净分支版本，包含所有核心功能和迷你Python环境
> 原始项目：离线网页下载器 v2.0
> 分支创建时间：2026-03-14

---

## 分支特点

✅ **完全干净** - 已移除所有测试文件、临时文件、版本备份
✅ **包含迷你环境** - python_env.zip 已包含，可直接打包网页为EXE
✅ **结构清晰** - 核心文件集中在根目录，文档分类明确
✅ **功能完整** - 包含所有核心功能模块

---

## 项目结构

```
webdownloader-clean/
├── 核心源码文件 (14个)
│   ├── main.py                    # 程序入口
│   ├── gui.py                     # 主界面逻辑
│   ├── playwright_downloader.py   # Playwright下载核心
│   ├── core_downloader.py         # 基础下载功能
│   ├── browser_manager.py         # 浏览器管理
│   ├── license_manager.py         # 许可证管理
│   ├── activation_dialog.py       # 激活对话框
│   ├── key_generator.py           # 密钥生成器
│   ├── secure_strings.py          # 安全字符串加密
│   ├── error_dialog.py            # 错误对话框
│   ├── user_manual.py             # 用户手册界面
│   ├── manual_data.py             # 用户手册数据
│   ├── ui_styles.py               # UI样式
│   ├── ui_components.py           # UI组件
│   └── hook_tcl.py               # TCL钩子
│
├── 配置文件 (5个)
│   ├── config.json                # 用户配置
│   ├── window_config.json         # 窗口配置
│   ├── requirements.txt           # 依赖列表
│   ├── inject.js                  # 浏览器注入脚本
│   └── .gitignore                 # Git忽略规则
│
├── 资源文件
│   ├── assets/                    # 资源目录
│   │   ├── icon.ico              # 程序图标
│   │   ├── icon_backup.ico       # 备用图标
│   │   ├── 作者.png              # 作者图片
│   │   └── package.svg           # 打包图标
│   ├── clean_scripts/             # 清理脚本
│   │   ├── csdn.json
│   │   ├── general.json
│   │   └── zhihu.json
│   └── browsers/                  # Playwright浏览器
│       ├── chromium-1208/
│       ├── ffmpeg-1011/
│       └── winldd-1007/
│
├── 迷你环境
│   └── python_env.zip             # 迷你Python环境（打包用）
│
├── 文档目录
│   └── docs/                     # 文档目录
│       ├── README.md              # 项目说明
│       ├── DEVELOPMENT.md         # 开发文档
│       ├── PROJECT_SPECIFICATION.md # 项目规范
│       └── NUITKA_PACKAGING.md    # 打包指南
│
└── BRANCH_README.md            # 本文档
```

---

## 核心功能

### 1. 文献下载
- 使用 Playwright 自动化下载网页内容
- 支持单页下载、批量下载
- 自动处理动态内容和弹窗
- 支持悬浮目录导航注入
- 支持多种颜色主题

### 2. 网页打包
- 将下载的网页打包为独立 EXE
- 使用迷你Python环境运行
- 支持自定义窗口样式
- 支持文件锁保护

### 3. 许可证管理
- 试用次数管理（200次）
- 激活码验证
- 机器ID绑定
- 安全加密存储

### 4. 浏览器管理
- 内置 Chromium 浏览器
- 支持 Chrome/Edge/Firefox
- 自动下载和配置
- 持久化用户数据

---

## 快速开始

### 1. 安装依赖

```bash
# 进入分支目录
cd webdownloader-clean

# 创建虚拟环境（可选）
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install chromium
```

### 2. 运行程序

```bash
# 直接运行
python main.py
```

### 3. 打包为 EXE

```bash
# 使用 Nuitka 打包
python -m nuitka `
  --standalone `
  --onefile `
  --enable-plugin=tk-inter `
  --include-data-file=assets/icon.ico=assets/icon.ico `
  --include-data-file=assets/作者.png=assets/作者.png `
  --include-data-file=assets/package.svg=assets/package.svg `
  --include-data-file=config.json=config.json `
  --include-data-file=inject.js=inject.js `
  --windows-icon-from-ico=assets/icon.ico `
  --output-filename=WebDownloader.exe `
  --assume-yes-for-downloads `
  main.py
```

---

## 迷你环境说明

### python_env.zip
这是一个精简的 Python 3.13 环境，用于在打包的 EXE 中运行网页。

**包含内容**:
- Python 3.13 运行时
- Tkinter GUI 库
- 必要的 DLL 文件
- 基础标准库

**使用场景**:
- 网页打包为 EXE 时作为内嵌环境
- 无需用户安装 Python 即可运行打包的网页

**注意事项**:
- 仅用于打包网页，不用于开发
- 开发时请使用完整 Python 环境
- 如需更新，重新打包 python_env/ 目录

---

## 开发说明

### 代码规范
- 类名使用大驼峰：`WebDownloaderGUI`
- 函数名使用小写下划线：`download_page`
- 常量使用全大写下划线：`TRIAL_COUNT`
- 私有方法使用单下划线前缀：`_url_to_b64`

### 路径处理
必须使用以下函数处理路径（兼容打包模式）:

```python
def get_base_path():
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    if globals().get('__compiled__') is not None:
        return os.path.dirname(os.path.abspath(__file__))
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_resource_path(relative_path):
    if globals().get('__compiled__') is not None:
        base = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base, relative_path)
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        bundled_path = os.path.join(exe_dir, relative_path)
        if os.path.exists(bundled_path):
            return bundled_path
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), relative_path)
```

### 错误处理
所有模块都应包含崩溃日志记录：

```python
def save_crash_log(module_name, error_info, context=None):
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        logs_dir = os.path.join(base_dir, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        
        import datetime
        current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        crash_file = os.path.join(logs_dir, f"crash_{current_time}.log")
        
        with open(crash_file, "w", encoding="utf-8") as f:
            f.write(f"=== CRASH LOG ===\n")
            f.write(f"时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"模块: {module_name}\n")
            f.write(f"\n=== 错误信息 ===\n")
            f.write(str(error_info))
            f.write(f"\n\n=== 上下文 ===\n")
            if context:
                f.write(str(context))
            else:
                f.write("无")
        return crash_file
    except:
        return None
```

---

## 版本控制

### .gitignore
已配置忽略以下内容：
```
venv/
venv312/
python_env/
browser_data/
logs/
literature_downloads/
*.pyc
__pycache__/
.DS_Store
```

### 提交建议
1. 只提交源码文件，不提交虚拟环境
2. 提交前运行测试确保功能正常
3. 更新版本号和文档
4. 使用清晰的提交信息

---

## 与主项目的区别

| 项目 | 主项目 | 干净分支 |
|------|--------|---------|
| 测试文件 | 包含 | 不包含 |
| 临时文件 | 包含 | 不包含 |
| 版本备份 | 包含 | 不包含 |
| 历史文档 | 根目录 | docs/archive/ |
| 迷你环境 | python_env.zip | python_env.zip |
| 项目结构 | 混乱 | 清晰 |
| 文件数量 | ~60个 | ~30个 |

---

## 注意事项

1. **不要修改核心源码** - 如需修改，请先备份
2. **保留迷你环境** - python_env.zip 是打包网页的关键
3. **测试环境** - 建议在虚拟环境中开发
4. **许可证机制** - 分支版本保持原有的许可证机制
5. **打包路径** - Nuitka 编译路径不能包含中文

---

## 常见问题

### Q: 如何更新迷你环境？
A: 重新打包 python_env/ 目录，然后压缩为 python_env.zip

### Q: 如何打包为 EXE？
A: 参考 docs/NUITKA_PACKAGING.md 中的详细说明

### Q: 如何添加新功能？
A: 在相应模块中添加功能，更新文档和配置文件

### Q: 如何调试？
A: 在 GUI 中勾选"Debug模式"，或查看 logs/ 目录中的日志

---

## 文件清单

### Python 源码 (14个)
- main.py
- gui.py
- playwright_downloader.py
- core_downloader.py
- browser_manager.py
- license_manager.py
- activation_dialog.py
- key_generator.py
- secure_strings.py
- error_dialog.py
- user_manual.py
- manual_data.py
- ui_styles.py
- ui_components.py
- hook_tcl.py

### 配置文件 (5个)
- config.json
- window_config.json
- requirements.txt
- inject.js
- .gitignore

### 资源文件
- assets/* (4个文件)
- clean_scripts/* (3个文件)
- browsers/* (3个目录)
- python_env.zip

### 文档 (4个)
- docs/README.md
- docs/DEVELOPMENT.md
- docs/PROJECT_SPECIFICATION.md
- docs/NUITKA_PACKAGING.md

---

## 联系方式

- 原始项目：离线网页下载器 v2.0
- 分支版本：webdownloader-clean v1.0
- 创建日期：2026-03-14

---

*分支版本: 1.0*
*创建日期: 2026-03-14*
*原始项目: 离线网页下载器 v2.0*
