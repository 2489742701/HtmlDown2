# 离线网页下载器 - 项目规范文档

## 一、项目概述

### 1.1 项目基本信息
| 属性 | 内容 |
|------|------|
| 项目名称 | 离线网页下载器 v2 (WebDownloader) |
| 版本号 | Beta v2.0 |
| 开发语言 | Python 3.12 |
| 主要框架 | Tkinter + Playwright |
| 打包工具 | Nuitka 4.0.1 |
| 目标平台 | Windows 10/11 |

### 1.2 项目目标
开发一款专业的网页离线保存工具，支持：
- 完整网页下载（包括CSS、JS、图片等资源）
- 浏览器自动化（Playwright）
- 批量下载和打包为EXE
- 生成悬浮目录导航
- 许可证管理和激活机制

### 1.3 核心功能
1. **文献下载**：使用Playwright自动化下载网页内容
2. **网页打包**：将下载的网页打包为独立EXE文件
3. **浏览器管理**：内置Chromium浏览器管理
4. **许可证系统**：试用次数限制 + 激活码验证
5. **用户手册**：内置使用说明文档

---

## 二、项目结构

### 2.1 目录结构
```
HtmlDownload/
├── 核心源码文件
│   ├── main.py                    # 程序入口
│   ├── gui.py                     # 主界面逻辑 (WebDownloaderGUI类)
│   ├── playwright_downloader.py   # Playwright下载核心
│   ├── core_downloader.py         # 基础下载功能
│   ├── browser_manager.py         # 浏览器管理
│   ├── license_manager.py         # 许可证管理ww
│   ├── activation_dialog.py       # 激活对话框
│   ├── key_generator.py           # 密钥生成器
│   ├── secure_strings.py          # 安全字符串加密
│   ├── error_dialog.py            # 错误对话框
│   ├── user_manual.py             # 用户手册界面
│   └── manual_data.py             # 用户手册数据
│
├── 配置文件
│   ├── config.json                # 用户配置
│   ├── window_config.json         # 窗口配置
│   └── requirements.txt           # 依赖列表
│
├── 资源文件
│   ├── assets/
│   │   ├── icon.ico               # 程序图标
│   │   ├── 作者.png               # 作者图片
│   │   └── package.svg            # 打包图标
│   ├── ico/
│   │   └── icon.ico               # 备用图标
│   └── inject.js                  # 浏览器注入脚本
│
├── 数据目录
│   ├── browser_data/              # 浏览器数据（Cookie、缓存等）
│   ├── browsers/                  # Playwright浏览器
│   ├── clean_scripts/             # 清理脚本
│   │   ├── csdn.json
│   │   ├── general.json
│   │   └── zhihu.json
│   ├── literature_downloads/      # 文献下载输出
│   ├── literature_test/           # 测试目录
│   └── logs/                      # 日志文件
│
├── 打包相关
│   ├── python_env.zip             # 迷你Python环境（用于打包网页）
│   ├── hook_tcl.py                # TCL钩子
│   └── pack_output/               # 打包输出
│
├── 文档
│   ├── README.md                  # 项目说明
│   ├── DEVELOPMENT.md             # 开发文档
│   ├── NUITKA_PACKAGING.md        # Nuitka打包指南
│   ├── PROJECT_SPECIFICATION.md   # 本规范文档
│   └── .trae/rules/main.md        # AI助手规则
│
└── 版本备份
    ├── Alpha原始版本，不要误删/
    └── Beta原始版本_20260218/
```

### 2.2 核心模块依赖关系
```
main.py
  ├── gui.py (WebDownloaderGUI)
  │     ├── playwright_downloader.py (PlaywrightDownloader)
  │     ├── core_downloader.py (CoreDownloader)
  │     ├── browser_manager.py
  │     ├── user_manual.py
  │     └── error_dialog.py
  ├── license_manager.py (LicenseManager)
  ├── activation_dialog.py (ActivationDialog)
  └── secure_strings.py
```

---

## 三、核心模块规范

### 3.1 main.py - 程序入口

**职责**：程序启动、异常处理、临时目录清理、激活检查

**关键函数**：
```python
def cleanup_pyinstaller_temp()     # 清理PyInstaller临时目录
def check_activation()             # 检查激活状态
def run_preview_mode(config_file)  # 预览模式运行
def global_exception_handler()     # 全局异常处理
```

**启动流程**：
1. 冻结多进程支持 (`multiprocessing.freeze_support()`)
2. 清理临时目录
3. 检查激活状态（试用/已激活）
4. 显示激活对话框（如需要）
5. 启动主界面

---

### 3.2 gui.py - 主界面模块

**类名**：`WebDownloaderGUI`

**职责**：所有用户交互、界面渲染、功能调度

**主要方法分类**：

#### 3.2.1 文献下载相关
```python
def show_download_options(self)                    # 显示下载选项对话框
def start_literature_download_pack(self, urls, config)  # 启动打包下载
def run_literature_download(self, urls, pack_mode, config, headless)  # 运行下载
def _inject_floating_toc_to_pages(self, pages_dir, html_files, theme)  # 注入悬浮目录
def _get_toc_theme_css(self, theme)                # 获取目录主题CSS
```

#### 3.2.2 打包功能
```python
def preview_pack(self)                             # 预览打包效果
def start_pack(self)                               # 开始打包
def auto_detect_website_dir(self)                  # 自动检测网站目录
def ensure_python_env(self)                        # 确保Python环境可用
```

#### 3.2.3 浏览器管理
```python
def launch_browser(self)                           # 启动浏览器
def _start_browser_with_url(self, url)             # 带URL启动浏览器
def _on_browser_type_change(self, show_warning)    # 浏览器类型变更
def _get_actual_browser_type(self)                 # 获取实际浏览器类型
```

#### 3.2.4 配置管理
```python
def load_config(self)                              # 加载配置
def save_config(self)                              # 保存配置
def _load_window_geometry(self)                    # 加载窗口几何信息
def _save_window_geometry(self)                    # 保存窗口几何信息
```

---

### 3.3 playwright_downloader.py - Playwright下载核心

**类名**：`PlaywrightDownloader`

**职责**：使用Playwright进行浏览器自动化下载

**核心方法**：
```python
def __init__(self, gui=None, log_callback=None, browser_type="auto")
def download_page(self, url, output_path, headless, process_resources=True)  # 下载单页
def download_multiple(self, urls, output_dir, progress_callback, headless, stop_check)  # 批量下载
def _url_to_b64(self, url, base_url)  # 返回 (data_uri, content, error_type)
def _embed_resources(self, soup, base_url)  # 资源嵌入，含SSL错误检测
```

**关键常量**：
```python
POPUP_SELECTORS          # 弹窗选择器列表
GDPR_BUTTON_SELECTORS    # GDPR同意按钮选择器
REMOVE_SELECTORS         # 需要移除的元素选择器
```

---

### 3.4 core_downloader.py - 基础下载器

**类名**：`CoreDownloader`

**职责**：使用requests进行基础网页下载

**核心方法**：
```python
def __init__(self, gui, params)                    # 初始化参数
def get_headers(self, url=None)                    # 获取请求头（含完整浏览器UA）
def process_page(self, url, depth)                 # 处理页面（带重试机制）
def _download_resource(self, url, res_type)        # 下载资源
```

**参数结构**：
```python
params = {
    'url': str,           # 起始URL
    'output_dir': str,    # 输出目录
    'depth': int,         # 爬取深度
    'mode': str,          # 路径模式 (absolute/relative)
    'convert_img': bool,  # 是否转换图片
    'target_fmt': str,    # 目标图片格式
    'filter_img': bool,   # 是否过滤图片
    'filter_video': bool, # 是否过滤视频
    'max_pages': int      # 最大页面数
}
```

---

### 3.5 browser_manager.py - 浏览器管理

**职责**：管理内置Chromium浏览器的下载、检测和配置

**核心函数**：
```python
def is_browser_ready()             # 检查浏览器是否就绪
def check_browser_integrity()      # 检查浏览器完整性
def get_chromium_path()            # 获取Chromium路径
def setup_browser_env()            # 设置浏览器环境
def download_browser(progress_callback, use_mirror=True)  # 下载浏览器
```

---

### 3.6 license_manager.py - 许可证管理

**类名**：`LicenseManager`

**职责**：管理软件激活状态和试用次数

**核心方法**：
```python
def __init__(self)
def _get_machine_id(self)                          # 获取机器唯一ID
def validate_card_key(self, card_key)              # 验证激活码格式
def save_activation(self, card_key)                # 保存激活信息
def check_activation(self)                         # 检查激活状态 (is_activated, msg)
def check_trial(self)                              # 检查试用状态 (is_trial, remaining, msg)
def get_trial_status(self)                         # 获取试用详情
```

**常量**：
```python
TRIAL_COUNT = 200        # 最大试用次数
```

---

### 3.7 secure_strings.py - 安全字符串

**职责**：加密存储敏感字符串，防止直接读取

**核心函数**：
```python
def get_registry_path()        # 获取注册表路径
def get_registry_name()        # 获取注册表项名称
def get_trial_registry_name()  # 获取试用注册表项名称
def get_activation_key()       # 获取激活密钥
```

---

## 四、配置文件规范

### 4.1 config.json - 用户配置
```json
{
  "path_mode": "absolute",      // 路径模式: absolute | relative
  "browser_type": "auto"        // 浏览器类型: auto | internal | chrome | edge | firefox
}
```

### 4.2 window_config.json - 窗口配置
```json
{
  "width": 1065,
  "height": 925,
  "x": 821,
  "y": 78
}
```

### 4.3 requirements.txt - 依赖列表
```
beautifulsoup4
playwright
requests
lxml
pillow
pywebview
fake-useragent
pyperclip
pycryptodome
```

---

## 五、编码规范

### 5.1 命名规范
| 类型 | 规范 | 示例 |
|------|------|------|
| 类名 | 大驼峰 | `WebDownloaderGUI`, `PlaywrightDownloader` |
| 函数/方法 | 小写下划线 | `download_page`, `check_activation` |
| 常量 | 全大写下划线 | `TRIAL_COUNT`, `POPUP_SELECTORS` |
| 私有方法 | 单下划线前缀 | `_url_to_b64`, `_embed_resources` |
| 模块变量 | 小写下划线 | `script_dir`, `browser_type` |

### 5.2 路径处理规范

**必须使用以下函数处理路径**：
```python
# 获取基础路径（打包/非打包模式兼容）
def get_base_path():
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    if globals().get('__compiled__') is not None:
        return os.path.dirname(os.path.abspath(__file__))
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

# 获取外部基础路径（用于保存用户数据）
def get_external_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    if globals().get('__compiled__') is not None:
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

# 获取资源路径
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

### 5.3 错误处理规范

**必须包含崩溃日志记录**：
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

## 六、打包规范

### 6.1 Nuitka打包命令
```powershell
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

### 6.2 打包前检查清单
- [ ] 所有资源文件已放入assets目录
- [ ] config.json配置正确
- [ ] secure_strings.py已加密敏感信息
- [ ] 版本号已更新
- [ ] 在英文路径下编译

### 6.3 分发文件清单
```
WebDownloader.exe          # 主程序
python_env.zip             # 迷你Python环境（用于打包网页）
assets/icon.ico            # 图标（可选，已打包进exe）
browsers/                  # Playwright浏览器（如使用）
```

---

## 七、开发工作流

### 7.1 开发环境搭建
```powershell
# 1. 创建虚拟环境
python -m venv venv312

# 2. 激活环境
.\venv312\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 安装Playwright浏览器
playwright install chromium
```

### 7.2 调试模式
- 勾选GUI中的"Debug模式"可显示浏览器窗口
- 查看logs目录中的日志文件
- 使用源代码运行查看完整错误堆栈

### 7.3 版本发布流程
1. 更新版本号（代码中 + DEVELOPMENT.md）
2. 运行完整测试（下载、打包、激活）
3. 在英文路径下执行Nuitka打包
4. 验证打包后的exe可正常运行
5. 创建版本备份目录

---

## 八、注意事项

### 8.1 重要限制
1. **Nuitka编译路径不能包含中文**
2. **打包预览必须使用迷你Python环境**，不能使用sys.executable
3. **Playwright浏览器需单独分发**或使用用户机器上的浏览器

### 8.2 常见问题
| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 打包后资源缺失 | 路径处理不正确 | 使用get_resource_path()函数 |
| 激活失效 | 机器ID变化 | 重新输入激活码 |
| 浏览器启动失败 | 浏览器未下载 | 运行playwright install chromium |
| SSL错误 | 网站限制 | 使用内置浏览器或跳过图片 |

---

## 九、更新日志

### v2.0 Beta (2026-02-18)
- 添加文献修复功能
- 添加目录颜色主题
- 添加浏览器类型选择
- 添加SSL错误智能检测
- 优化两阶段下载流程
- 迁移到Nuitka打包

---

*文档版本：1.0*
*最后更新：2026-03-11*
*作者：AI Assistant*
