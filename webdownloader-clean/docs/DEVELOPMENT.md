# 离线网页下载器 Beta版 开发文档

## 版本信息
- 版本号：Beta v2.0
- 发布日期：2026年2月18日
- 开发语言：Python 3.12
- 主要框架：Tkinter + Playwright
- 打包工具：Nuitka 4.0.1

---

## 最新更新 (2026-02-18)

### 修复问题
| 问题 | 描述 | 解决方案 |
|------|------|----------|
| 版本公告按钮不显示 | 公告内容过长导致按钮被遮挡 | 添加滚动区域，确保按钮始终可见 |
| 浏览器选择不保存 | 每次启动需要重新扫描浏览器 | 启动时自动搜索并恢复保存的选择 |
| 预览模式CSS注入失败 | f-string格式错误导致NameError | 修复字符串拼接方式 |
| 打包后资源缺失 | 关于页面作者图片不显示 | 添加get_resource_path()函数处理Nuitka资源路径 |
| 配置文件路径不一致 | 打包后配置保存位置错误 | 统一使用get_base_path()和get_external_base_path() |

### 新增功能
1. **条件性JS注入**：只在"显示导航按钮"开启时才注入CSS/JS
2. **移除窗口控制选项**：简化打包配置界面
3. **默认窗口大小优化**：调整为1065x925，位置(821, 78)
4. **源代码模式公告显示**：开发时也能查看版本公告

### 打包优化
- 使用Nuitka替代PyInstaller，生成更小的可执行文件
- 资源文件正确打包：assets/icon.ico, assets/作者.png, assets/package.svg, inject.js
- 最终文件大小：约42MB（不含python_env.zip）

---

## 一、项目概述

### 1.1 项目目标
开发一款专业的网页离线保存工具，支持批量下载网页、自动处理动态内容、生成目录索引等功能。

### 1.2 技术栈
- **GUI框架**：Tkinter（ttk样式）
- **浏览器自动化**：Playwright
- **HTML解析**：BeautifulSoup + lxml
- **网络请求**：requests
- **打包工具**：PyInstaller

### 1.3 项目结构
```
离线网页下载器（版本2）/
├── gui.py                    # 主界面逻辑
├── main.py                   # 程序入口
├── playwright_downloader.py  # 下载核心模块
├── core_downloader.py        # 基础下载功能
├── browser_manager.py        # 浏览器管理
├── user_manual.py            # 用户手册界面
├── manual_data.py            # 用户手册数据
├── error_dialog.py           # 错误对话框
├── license_manager.py        # 许可证管理
├── activation_dialog.py      # 激活对话框
├── key_generator.py          # 密钥生成
├── secure_strings.py         # 安全字符串处理
├── python_env.zip            # 迷你Python环境（打包用）
└── assets/                   # 资源文件
    ├── icon.ico              # 程序图标
    └── 作者.png              # 作者图片
```

---

## 二、Beta版开发内容

### 2.1 新增功能

#### 2.1.1 文献修复功能
**位置**：文献下载页面 → 文献修复按钮

**功能描述**：
- 自动检测下载目录中的文献文件夹
- 支持多选批量修复
- 重新生成悬浮目录面板
- 重新生成文献合集主页
- 支持选择目录颜色主题

**代码位置**：
- `gui.py` - `show_repair_options()` 方法
- `gui.py` - `_inject_floating_toc_to_pages()` 方法

#### 2.1.2 目录颜色主题
**位置**：下载配置 → 目录颜色主题选择

**支持主题**：
| 主题 | 样式描述 |
|------|----------|
| 彩色 | 紫色渐变，活泼现代 |
| 深色 | 深灰暗色，护眼舒适 |
| 白色 | 浅色简约，清爽干净 |
| 蓝色 | 专业蓝色，商务风格 |

**代码位置**：
- `gui.py` - `_get_toc_theme_css()` 方法

#### 2.1.3 浏览器类型选择
**位置**：文献下载页面 → 浏览器选择下拉框

**支持类型**：
- 内置浏览器（推荐）
- Google Chrome
- Microsoft Edge
- Firefox

**代码位置**：
- `gui.py` - `browser_type_var` 变量
- `playwright_downloader.py` - `browser_type` 参数

#### 2.1.4 用户提醒功能
**位置**：下载前警告对话框

**提醒内容**：
- 使用主流浏览器可能被临时封禁
- 建议使用内置浏览器
- 下载过程中请勿操作

**代码位置**：
- `gui.py` - `_show_download_warning()` 方法

#### 2.1.5 SSL错误智能检测
**位置**：文献下载资源处理阶段

**功能描述**：
- 检测SSL/TLS握手错误
- 连续3次失败后弹窗询问用户
- 用户可选择跳过图片或继续尝试

**代码位置**：
- `playwright_downloader.py` - `_url_to_b64()` 返回错误类型
- `playwright_downloader.py` - `_embed_resources()` 检测SSL错误
- `playwright_downloader.py` - `_ask_ssl_skip_dialog()` 弹窗

#### 2.1.6 浏览器选择持久化
**位置**：环境管理页面

**功能描述**：
- 浏览器选择自动保存到config.json
- 下次启动自动恢复上次选择

**代码位置**：
- `gui.py` - `load_config()` 加载浏览器类型
- `gui.py` - `save_config()` 保存浏览器类型
- `gui.py` - `_on_browser_type_change()` 自动保存

#### 2.1.7 Python环境提前解压
**位置**：环境管理页面 → Python环境卡片

**功能描述**：
- 未解压状态显示"📦 提前解压"按钮
- 用户可主动解压Python环境
- 避免打包时等待

**代码位置**：
- `gui.py` - `_extract_python_env()` 方法
- `gui.py` - `ensure_python_env()` 复用解压逻辑

#### 2.1.8 缓存删除失败友好提示
**位置**：环境管理页面 → 清空Cookie/清空全部

**功能描述**：
- 删除失败时显示自定义对话框
- 提示可能原因（文件被占用/权限不足）
- 提供"打开文件夹"按钮让用户手动删除

**代码位置**：
- `gui.py` - `_show_clear_failed_dialog()` 方法
- `gui.py` - `_clear_browser_cookies()` 调用失败对话框
- `gui.py` - `_clear_env_browser_data()` 调用失败对话框

### 2.2 优化改进

#### 2.2.1 目录联动修复
**问题**：分多次下载时，每次下载的文件目录只显示本次下载的文章

**解决方案**：
```python
# 修改前
self._inject_floating_toc_to_pages(pages_dir, downloaded_files)

# 修改后
all_html_files = [f for f in os.listdir(pages_dir) if f.endswith('.html')]
self._inject_floating_toc_to_pages(pages_dir, all_html_files)
```

#### 2.2.2 浏览器选择逻辑优化
**问题**：代码中多处重复检查浏览器类型，导致管理混乱

**解决方案**：
- 添加 `_get_actual_browser_type()` 辅助函数
- "自动选择"优先使用检测到的第一个浏览器（包括内部浏览器）
- "内置浏览器"直接使用内部Chromium
- 统一使用 `_get_actual_browser_type()` 获取实际浏览器类型

**涉及函数**：
- `_get_actual_browser_type()` - 新增辅助函数
- `launch_browser()`
- `_start_browser_with_url()`
- `start_literature_download()`
- `show_download_options()` 中的验证浏览器
- `show_software_test()`

#### 2.2.3 浏览器窗口位置优化
**问题**：下载时浏览器窗口显示在屏幕中央，影响用户操作

**解决方案**：
- 下载时浏览器窗口移至屏幕外（坐标 -3000,-3000）
- 登录/手动操作时窗口移回屏幕中央
- 添加 `_move_window_to_center()` 方法实现窗口重定位

**代码位置**：
- `playwright_downloader.py` - `_move_window_to_center()` 方法
- `playwright_downloader.py` - `open_login_page()` 调用窗口居中
- `gui.py` - `_start_browser_with_url()` 窗口居中显示

#### 2.2.4 下载流程优化
**问题**：每个网页下载后立即处理资源，用户等待时间长

**解决方案**：
采用两阶段下载模式：
1. **第一阶段**：下载所有网页HTML（不处理资源）
2. **第二阶段**：批量处理所有资源（图片、样式、背景图）

**优点**：
- 用户可以更快看到下载进度
- 减少浏览器切换开销
- 便于中断和恢复

**代码位置**：
- `playwright_downloader.py` - `download_batch()` 方法
- `playwright_downloader.py` - `download_page()` 添加 `process_resources` 参数

#### 2.2.5 设置页面整合
**改进**：将软件测试和网站测试移至设置页面

**代码位置**：
- `gui.py` - `show_settings()` 方法

#### 2.2.6 核心下载器请求头改进
**问题**：CSDN等网站检测到爬虫特征，返回SSL错误

**解决方案**：
- 添加完整浏览器请求头（Accept、Accept-Language、Sec-Fetch-*等）
- 添加重试机制（最多3次）
- 每次重试前等待递增时间

**代码位置**：
- `core_downloader.py` - `get_headers()` 方法
- `core_downloader.py` - `process_page()` 重试逻辑

#### 2.2.7 打包模式智能目录检测
**问题**：打包模式只检测downloads目录，不检测文献下载目录

**解决方案**：
- 搜索所有可能的下载目录
- 智能扫描当前目录下的所有文件夹
- 排除系统目录（assets、browser_data、python_env等）

**代码位置**：
- `gui.py` - `auto_detect_website_dir()` 方法

#### 2.2.8 打包预览使用迷你Python环境
**问题**：打包后预览使用sys.executable会递归调用自己

**解决方案**：
- 预览时使用ensure_python_env()获取迷你Python环境
- 如果迷你环境不可用，回退到系统Python

**代码位置**：
- `gui.py` - `preview_pack()` 方法

### 2.3 修复问题

| 问题 | 描述 | 解决方案 |
|------|------|----------|
| 目录不完整 | 分次下载时目录只显示本次文章 | 获取目录下所有HTML文件 |
| 浏览器选择不一致 | 多处代码重复检查浏览器 | 统一使用browser_type变量 |
| 悬浮目录样式单一 | 只有一种颜色主题 | 添加四种主题选择 |
| SSL错误无提示 | 资源下载失败无用户反馈 | 添加智能检测和弹窗 |
| 浏览器选择不保存 | 每次启动重新选择 | 保存到config.json |
| PyInstaller临时目录残留 | 异常退出后临时目录未清理 | 启动时清理旧临时目录 |
| 打包预览递归调用 | 打包后预览启动自己 | 使用迷你Python环境 |

---

## 三、核心模块说明

### 3.1 GUI模块 (gui.py)
主界面模块，包含所有用户交互逻辑。

**主要类**：`WebDownloaderGUI`

**主要方法**：
```python
# 文献下载
def show_download_options(self)
def start_literature_download_pack(self, urls, config)
def run_literature_download(self, urls, pack_mode, config, headless)

# 文献修复
def show_repair_options(self)

# 目录生成
def _inject_floating_toc_to_pages(self, pages_dir, html_files, theme)
def _get_toc_theme_css(self, theme)
def generate_packed_html(self, pages_dir, html_files, config)

# 浏览器管理
def launch_browser(self)
def _start_browser_with_url(self, url)
def _on_browser_type_change(self, show_warning)

# 配置管理
def load_config(self)
def save_config(self)

# 打包功能
def preview_pack(self)
def start_pack(self)
def auto_detect_website_dir(self)
def ensure_python_env(self)

# 环境管理
def _extract_python_env(self)
def _show_clear_failed_dialog(self, path, failed_items)
```

### 3.2 下载模块 (playwright_downloader.py)
核心下载逻辑，使用Playwright进行浏览器自动化。

**主要类**：`PlaywrightDownloader`

**初始化参数**：
```python
def __init__(self, gui=None, log_callback=None, browser_type="auto")
```

**主要方法**：
```python
def download_page(self, url, output_path, headless)
def download_multiple(self, urls, output_dir, progress_callback, headless, stop_check)
def _url_to_b64(self, url, base_url)  # 返回 (data_uri, content, error_type)
def _embed_resources(self, soup, base_url)  # 资源嵌入，含SSL错误检测
def _ask_ssl_skip_dialog(self, domain)  # SSL错误弹窗
def close(self)
```

### 3.3 核心下载器 (core_downloader.py)
基础下载功能，使用requests库。

**主要类**：`CoreDownloader`

**主要方法**：
```python
def get_headers(self, url=None)  # 返回完整浏览器请求头
def process_page(self, url, depth)  # 带重试的页面处理
```

### 3.4 浏览器管理模块 (browser_manager.py)
管理内置浏览器的下载、检测和配置。

**主要函数**：
```python
def is_browser_ready()
def check_browser_integrity()
def get_chromium_path()
def setup_browser_env()
def download_browser(progress_callback)
```

### 3.5 程序入口 (main.py)
程序启动入口，包含临时目录清理。

**主要函数**：
```python
def cleanup_pyinstaller_temp()  # 清理PyInstaller临时目录
def main()  # 程序入口
```

---

## 四、配置文件

### 4.1 PyInstaller配置 (离线网页下载器.spec)
```python
a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),
        ('browser_data', 'browser_data'),
    ],
    hiddenimports=[
        'playwright.sync_api',
        'PIL',
        'bs4',
        'lxml',
    ],
    ...
)
```

### 4.2 用户配置 (config.json)
```json
{
    "path_mode": "relative",
    "browser_type": "auto"
}
```

### 4.3 用户手册数据 (manual_data.py)
```python
MANUAL_DATA = [
    {
        "title": "标题",
        "content": "内容..."
    },
    ...
]
```

---

## 五、重要注意事项

### 5.1 打包预览注意事项
**重要**：打包预览必须使用迷你Python环境（ensure_python_env()），不能使用sys.executable。打包后sys.executable指向程序本身，会导致递归调用。

```python
# 正确做法
python_exe = self.ensure_python_env()
subprocess.Popen([python_exe, script_file])

# 错误做法（会导致递归）
subprocess.Popen([sys.executable, script_file])
```

### 5.2 临时目录清理
程序启动时会自动清理PyInstaller的_MEI*临时目录，防止异常退出后残留。

### 5.3 浏览器选择持久化
浏览器选择会自动保存到config.json，确保用户体验一致性。

---

## 六、后续开发计划

### 6.1 待实现功能
- [ ] 自定义图片背景作为目录背景
- [ ] 下载进度百分比显示
- [ ] 下载历史记录
- [ ] 导出/导入下载列表
- [ ] 多线程下载支持

### 6.2 待优化项目
- [ ] 下载速度优化
- [ ] 内存占用优化
- [ ] 错误处理完善
- [ ] 日志系统改进

---

## 七、已知问题

1. **大文件下载**：超大网页可能导致内存占用过高
2. **网络超时**：部分网站响应慢可能导致下载失败
3. **验证码处理**：复杂验证码需要手动处理
4. **SSL限制**：部分网站（如CSDN）可能限制自动化访问

---

## 八、开发者备注

### 8.1 调试模式
勾选Debug模式可以显示浏览器窗口，便于观察下载过程和调试问题。

### 8.2 日志查看
程序底部有日志区域，显示下载过程中的详细信息。

### 8.3 测试功能
设置页面中有软件测试和网站测试功能，用于检测环境问题。

---

*文档编写日期：2026年2月*
*版本：Beta*
