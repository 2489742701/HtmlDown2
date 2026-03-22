# Nuitka 打包指南

## 问题背景

PyInstaller 在单文件模式下存在 TCL/TK 路径问题，无法正常启动。因此改用 Nuitka 进行打包。

## 重要限制

**Nuitka 编译时不支持中文路径！**

- 编译过程使用 gcc 编译器
- gcc 无法处理非 ASCII 字符（中文、特殊符号等）
- 路径中不能包含：中文、括号、空格等特殊字符

**但编译后的 exe 可以放在任何路径运行**，包括中文路径。

---

## 关于 python_env.zip

**重要说明：python_env.zip 是用于打包网页程序的独立环境，不是用于打包本程序！**

### 用途
- `python_env.zip` 是一个独立的 Python 环境
- 当用户使用本程序的"打包网页"功能时，程序会自动解压这个环境
- 这个环境包含 PyInstaller、pywebview 等打包网页所需的依赖

### 工作流程
1. 用户运行 WebDownloader.exe
2. 用户下载网页后，点击"打包成 EXE"功能
3. 程序自动解压 `python_env.zip` 到当前目录
4. 使用解压后的环境中的 PyInstaller 打包用户的网页

### 注意事项
- `python_env.zip` 需要和 `WebDownloader.exe` 放在同一目录
- 这个环境是独立的，不依赖用户电脑上的 Python 安装
- 如果缺少这个文件，打包功能将无法使用

---

## 打包步骤

### 1. 准备英文路径

将项目复制到纯英文路径，例如：
```
C:\WebDownloader
```

### 2. 创建 Python 3.12 虚拟环境

```powershell
cd C:\WebDownloader

# 创建虚拟环境
C:\Users\longyaosi\AppData\Local\Programs\Python\Python312\python.exe -m venv venv312

# 激活虚拟环境
.\venv312\Scripts\activate
```

### 3. 安装依赖

```powershell
# 安装项目依赖
pip install -r requirements.txt

# 安装 Nuitka 和压缩支持
pip install nuitka zstandard
```

### 4. 运行打包命令

```powershell
python -m nuitka --standalone --onefile --enable-plugin=tk-inter --include-data-file=assets/icon.ico=assets/icon.ico --include-data-file=config.json=config.json --include-data-file=inject.js=inject.js --windows-icon-from-ico=assets/icon.ico --output-filename=WebDownloader.exe --assume-yes-for-downloads main.py
```

### 5. 获取生成的 exe

编译完成后，exe 文件位于：
```
C:\WebDownloader\WebDownloader.exe
```

### 6. 分发

将 exe 复制到任意位置，包括中文路径，程序都能正常运行。

---

## 参数说明

| 参数 | 说明 |
|------|------|
| `--standalone` | 独立运行，包含所有依赖 |
| `--onefile` | 打包成单个 exe 文件 |
| `--enable-plugin=tk-inter` | 启用 tkinter 支持（自动处理 TCL/TK） |
| `--include-data-file` | 包含数据文件 |
| `--windows-icon-from-ico` | 设置 exe 图标 |
| `--output-filename` | 输出文件名 |
| `--assume-yes-for-downloads` | 自动下载依赖（gcc 等） |

---

## 常见问题

### Q: 编译报错 "Cannot convert character sequence"
**A:** 路径包含中文字符，需要移动到英文路径。

### Q: 第一次编译很慢
**A:** 第一次会下载 gcc 编译器（约 100MB），后续编译会快很多。

### Q: exe 文件很大
**A:** Nuitka 会包含所有 Python 运行时和依赖，单文件模式通常 50-150MB，这是正常的。

### Q: 需要安装 Playwright 浏览器吗？
**A:** 如果程序使用 Playwright，需要确保 `browsers` 目录和 exe 在一起，或者在用户机器上运行 `playwright install chromium`。

---

## 文件清单

打包需要的文件：
```
C:\WebDownloader\
├── main.py              # 主程序入口
├── gui.py               # GUI 界面
├── license_manager.py   # 许可证管理
├── activation_dialog.py # 激活对话框
├── secure_strings.py    # 字符串加密
├── key_generator.py     # 密钥生成
├── error_dialog.py      # 错误对话框
├── manual_data.py       # 手册数据
├── core_downloader.py   # 核心下载器
├── playwright_downloader.py # Playwright 下载器
├── browser_manager.py   # 浏览器管理
├── user_manual.py       # 用户手册
├── launch_browser_script.py # 浏览器启动脚本
├── config.json          # 配置文件
├── requirements.txt     # 依赖列表
├── assets/
│   └── icon.ico         # 程序图标
├── browsers/            # Playwright 浏览器（如果使用）
└── venv312/             # Python 虚拟环境
```

---

## 环境信息

- Python 版本：3.12.9
- Nuitka 版本：4.0.1
- 操作系统：Windows 10/11

---

## 更新日志

- 2026-02-17：创建文档，从 PyInstaller 迁移到 Nuitka
