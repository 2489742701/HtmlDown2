# 离线网页下载器 v2

一个功能强大的离线网页下载工具，支持完整的网页内容保存，包括脚本、样式和多媒体资源。

## 功能特点

- 🌐 **完整网页下载**：下载网页及其所有关联资源（CSS、JS、图片等）
- 🎨 **保留脚本和样式**：通过后处理保留网页的交互功能和样式
- 📁 **灵活的路径选择**：支持绝对路径和相对路径保存
- 🔢 **可配置爬取深度**：支持单页、多页或自定义深度爬取
- 🖼️ **美观的图形界面**：基于 Tkinter 的现代化 GUI
- 💾 **软盘图标**：专业的软盘+下载图标设计
- 📦 **打包为可执行文件**：无需 Python 环境即可运行

## 系统要求

- Windows 10/11
- Python 3.8+（如果从源码运行）
- 或直接使用打包好的 `.exe` 文件

## 安装方法

### 方法 1：使用可执行文件（推荐）

1. 下载 `离线网页下载器.exe`
2. 双击运行即可使用

### 方法 2：从源码运行

1. 克隆仓库：
```bash
git clone https://github.com/2489742701/HtmlDown2.git
cd HtmlDown2
```

2. 安装依赖：
```bash
pip install requests beautifulsoup4 lxml pillow
```

3. 运行程序：
```bash
python lixian_gui_beautified.py
```

## 使用说明

1. **输入 URL**：在输入框中输入要下载的网页地址
2. **选择保存路径**：点击"浏览"按钮选择保存位置
3. **选择路径模式**：
   - 绝对路径：使用完整路径保存
   - 相对路径：相对于当前目录保存
4. **设置爬取深度**：
   - 仅本页：只下载当前页面
   - 本页+下页：下载当前页面和下一页
   - 本页+下2页：下载当前页面和接下来的两页
   - 自定义：自定义爬取深度
5. **开始下载**：点击"开始下载"按钮
6. **打开目录**：点击"打开目录"按钮查看下载的文件

## 技术栈

- **GUI 框架**：Tkinter
- **HTTP 请求**：requests
- **HTML 解析**：BeautifulSoup4, lxml
- **图像处理**：Pillow
- **打包工具**：PyInstaller

## 项目结构

```
离线网页下载器（版本2）/
├── lixian_gui_beautified.py    # 主程序文件
├── lixian.py                    # 核心下载逻辑
├── icon.ico                     # 程序图标
├── create_floppy_icon.py        # 图标生成脚本
├── Git安装指南.md               # Git 安装说明
├── README.md                    # 项目说明
├── .gitignore                   # Git 忽略文件
├── dist/                        # 打包输出目录
│   └── 离线网页下载器.exe       # 可执行文件
└── downloads/                   # 默认下载目录
```

## 打包说明

使用 PyInstaller 打包：

```bash
pyinstaller --onefile --windowed --icon=icon.ico --name="离线网页下载器" lixian_gui_beautified.py
```

## 许可证

MIT License

## 作者

2489742701

## 更新日志

### v2.0
- 添加图形界面
- 支持脚本和样式保留
- 添加绝对/相对路径选择
- 改进爬取深度选项
- 添加软盘图标
- 打包为可执行文件

## 贡献

欢迎提交 Issue 和 Pull Request！

## 联系方式

- GitHub: https://github.com/2489742701/HtmlDown2
