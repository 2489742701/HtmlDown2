# 环境管理 - 最容易出错的地方

## ⚠️ 概述

这个项目的环境管理是最复杂、最容易出问题的部分。主要涉及三个环境：

1. **主程序运行环境** - 用户电脑上的 Python 或打包后的 EXE
2. **内置浏览器环境** - Playwright Chromium 浏览器
3. **打包网页用的迷你 Python 环境** - python_env.zip

---

## 🔴 问题一：路径处理混乱（最严重）

### 问题描述
代码中使用了多种不同的路径获取方式，导致打包后找不到资源文件。

### 错误代码示例
```python
# ❌ 错误：直接使用 __file__
base_dir = os.path.dirname(os.path.abspath(__file__))

# ❌ 错误：只在部分地方处理打包路径
if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
```

### 正确做法
```python
# ✅ 必须同时处理三种情况：
# 1. PyInstaller 打包 (_MEIPASS)
# 2. Nuitka 打包 (__compiled__)
# 3. 源代码运行

def get_base_path():
    if hasattr(sys, '_MEIPASS'):           # PyInstaller
        return sys._MEIPASS
    if globals().get('__compiled__') is not None:  # Nuitka
        return os.path.dirname(os.path.abspath(__file__))
    if getattr(sys, 'frozen', False):      # 其他打包
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))  # 源码

def get_external_base_path():
    """用于保存用户数据（配置、下载文件等）"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    if globals().get('__compiled__') is not None:
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))
```

### 常见错误场景
| 场景 | 错误表现 | 原因 |
|------|----------|------|
| Nuitka 打包后找不到 icon.ico | 程序无法启动或图标不显示 | 只处理了 `_MEIPASS`，没处理 `__compiled__` |
| 打包后找不到 config.json | 配置无法保存 | 使用了错误的 base_path |
| 预览功能递归调用 | 程序无限启动自己 | 使用了 `sys.executable` 而不是 `python_env` 中的 python |

---

## 🔴 问题二：Python 环境解压逻辑复杂

### 问题描述
`python_env.zip` 是用于打包网页的独立环境，解压逻辑容易出错。

### 核心代码位置
[gui.py:L9374-L9490](file:///c:/Users/longyaosi/Downloads/HtmlDownload/gui.py#L9374)

### 容易出错的地方

#### 1. 解压进度窗口可能创建失败
```python
# ❌ 问题：如果创建窗口失败，后面的代码会出错
try:
    progress_window = tk.Toplevel(self.root)
    # ... 创建窗口
except Exception as e:
    self.pack_log(f"⚠️ 无法创建进度窗口: {e}", "warning")
    # 这里应该 return，但代码继续执行了
```

#### 2. 解压后找不到 python.exe
```python
# 问题：python.exe 可能在不同位置
python_exe = os.path.join(env_dir, 'python.exe')
if not os.path.exists(python_exe):
    python_exe = os.path.join(env_dir, 'Scripts', 'python.exe')  # 备选位置
```

#### 3. pyvenv.cfg 路径问题
解压后的虚拟环境需要修复 `pyvenv.cfg` 中的路径，否则无法使用：
```python
def _fix_pyvenv_cfg(self, env_dir, python_exe):
    """修复 pyvenv.cfg 中的路径"""
    pyvenv_cfg = os.path.join(env_dir, 'pyvenv.cfg')
    if os.path.exists(pyvenv_cfg):
        # 需要把路径改为当前实际路径
        # 否则虚拟环境会指向打包时的路径
```

### 解决方案建议
```python
def ensure_python_env(self):
    """确保Python环境可用"""
    env_dir = self.get_python_env_path()
    
    # 1. 检查是否已解压
    python_exe = self._find_python_in_env(env_dir)
    if python_exe:
        self._fix_pyvenv_cfg(env_dir, python_exe)
        return python_exe
    
    # 2. 检查 zip 文件是否存在
    zip_path = self._get_python_env_zip_path()
    if not os.path.exists(zip_path):
        raise FileNotFoundError(f"找不到 {zip_path}，请下载后放置到程序目录")
    
    # 3. 解压（带错误处理）
    try:
        self._extract_with_progress(zip_path, env_dir)
    except Exception as e:
        # 清理半成品
        if os.path.exists(env_dir):
            shutil.rmtree(env_dir, ignore_errors=True)
        raise
    
    # 4. 验证
    python_exe = self._find_python_in_env(env_dir)
    if not python_exe:
        raise RuntimeError("解压后找不到 python.exe")
    
    return python_exe

def _find_python_in_env(self, env_dir):
    """在环境中查找 python.exe"""
    candidates = [
        os.path.join(env_dir, 'python.exe'),
        os.path.join(env_dir, 'Scripts', 'python.exe'),
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    return None
```

---

## 🔴 问题三：浏览器环境管理复杂

### 问题描述
Playwright 浏览器需要单独下载和管理，涉及多个环境变量和路径。

### 核心代码位置
[browser_manager.py](file:///c:/Users/longyaosi/Downloads/HtmlDownload/browser_manager.py)

### 容易出错的地方

#### 1. 浏览器路径检测不严谨
```python
# ❌ 问题：只检查目录存在，不检查关键文件
def get_chromium_path():
    for item in os.listdir(browsers_path):
        if item.startswith('chromium-'):
            return os.path.join(browsers_path, item, 'chrome-win64')
    # 没有验证 chrome.exe 是否存在！
```

#### 2. 打包模式和非打包模式逻辑不同
```python
def download_browser(progress_callback=None, use_mirror=True):
    if is_frozen():  # 打包模式
        # 使用 playwright._impl._driver 内部 API
        # 这个 API 可能随版本变化！
    else:  # 源码模式
        # 使用命令行 playwright install
```

#### 3. 环境变量设置问题
```python
# 问题：PLAYWRIGHT_BROWSERS_PATH 必须在导入 playwright 之前设置
os.environ['PLAYWRIGHT_BROWSERS_PATH'] = browsers_path

# 如果在导入后再设置，可能不生效
from playwright.sync_api import sync_playwright  # 必须在设置环境变量之后！
```

### 解决方案建议
```python
class BrowserManager:
    """统一管理浏览器环境"""
    
    REQUIRED_FILES = ['chrome.exe', 'chrome.dll', 'icudtl.dat']
    
    def __init__(self):
        self.browsers_path = self._get_browsers_path()
        os.environ['PLAYWRIGHT_BROWSERS_PATH'] = self.browsers_path
    
    def is_ready(self):
        """检查浏览器是否可用"""
        chromium_path = self._get_chromium_path()
        if not chromium_path:
            return False
        
        # 检查关键文件
        for f in self.REQUIRED_FILES:
            if not os.path.exists(os.path.join(chromium_path, f)):
                return False
        return True
    
    def download(self, callback=None):
        """下载浏览器（统一处理打包和源码模式）"""
        try:
            # 尝试使用 playwright 命令
            return self._download_via_cli(callback)
        except Exception as e:
            # 回退到手动下载提示
            return self._show_manual_download_guide()
```

---

## 🔴 问题四：预览模式递归调用

### 问题描述
打包后的程序使用 `sys.executable` 启动预览会导致无限递归。

### 错误代码
```python
# ❌ 严重错误：打包后 sys.executable 指向自己
subprocess.Popen([sys.executable, 'preview_script.py'])
# 结果：程序启动自己，无限循环！
```

### 正确做法
```python
# ✅ 必须使用 python_env 中的 Python
python_exe = self.ensure_python_env()  # 确保迷你环境已解压
subprocess.Popen([python_exe, 'preview_script.py'])
```

### 代码位置
[gui.py:L9199-L9210](file:///c:/Users/longyaosi/Downloads/HtmlDownload/gui.py#L9199)

---

## 🔴 问题五：临时目录清理

### 问题描述
PyInstaller 打包的程序会在临时目录解压，异常退出后可能残留。

### 解决方案
```python
def cleanup_pyinstaller_temp():
    """清理 PyInstaller 临时目录"""
    if not getattr(sys, 'frozen', False):
        return
    
    try:
        temp_base = tempfile.gettempdir()
        patterns = ['_MEI*', '_MEIPASS*']
        for pattern in patterns:
            for temp_dir in glob.glob(os.path.join(temp_base, pattern)):
                try:
                    shutil.rmtree(temp_dir, ignore_errors=True)
                except:
                    pass
    except:
        pass

# 在程序启动时调用
cleanup_pyinstaller_temp()
```

---

## 📋 环境管理检查清单

### 开发时检查
- [ ] 路径函数同时处理 `_MEIPASS`、`__compiled__` 和源码模式
- [ ] 所有资源文件使用 `get_resource_path()` 获取
- [ ] 用户数据使用 `get_external_base_path()` 保存
- [ ] 预览功能使用 `ensure_python_env()` 获取 Python 解释器

### 打包后检查
- [ ] 在纯英文路径下编译
- [ ] 验证图标能正常显示
- [ ] 验证 config.json 能正常读写
- [ ] 验证浏览器能正常下载和使用
- [ ] 验证预览功能不会递归调用
- [ ] 验证 python_env.zip 能正常解压

### 分发时检查
- [ ] 包含 python_env.zip（如果用户需要打包功能）
- [ ] 说明文档包含浏览器安装步骤
- [ ] 提供浏览器手动下载链接作为备选

---

## 🛠️ 改进建议

### 1. 统一路径管理模块
创建单独的 `path_utils.py`：
```python
# path_utils.py
import sys
import os

def is_frozen():
    return getattr(sys, 'frozen', False) or globals().get('__compiled__') is not None

def is_nuitka():
    return globals().get('__compiled__') is not None

def is_pyinstaller():
    return hasattr(sys, '_MEIPASS')

def get_resource_path(relative_path):
    """获取资源文件路径（只读）"""
    if is_nuitka():
        base = os.path.dirname(os.path.abspath(__file__))
    elif is_pyinstaller():
        base = sys._MEIPASS
    elif is_frozen():
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)

def get_data_path(relative_path):
    """获取数据文件路径（可读写）"""
    if is_frozen() or is_nuitka():
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)
```

### 2. 环境状态检查工具
```python
def check_environment():
    """检查所有环境状态，返回诊断报告"""
    report = {
        'python_env': {'exists': False, 'valid': False, 'path': None},
        'browser': {'exists': False, 'valid': False, 'path': None},
        'assets': {'exists': False, 'missing': []},
    }
    
    # 检查 python_env
    env_path = get_python_env_path()
    report['python_env']['path'] = env_path
    report['python_env']['exists'] = os.path.exists(env_path)
    if report['python_env']['exists']:
        report['python_env']['valid'] = find_python_exe(env_path) is not None
    
    # 检查浏览器
    browser_path = get_chromium_path()
    report['browser']['path'] = browser_path
    report['browser']['exists'] = browser_path is not None
    if report['browser']['exists']:
        report['browser']['valid'] = check_browser_files(browser_path)
    
    return report
```

---

## 📚 相关代码位置

| 功能 | 文件 | 行号 |
|------|------|------|
| 路径处理 | gui.py | L27-L57 |
| Python环境解压 | gui.py | L9374-L9490 |
| 浏览器管理 | browser_manager.py | 全部 |
| 预览功能 | gui.py | L9199-L9210 |
| 临时目录清理 | main.py | L29-L44 |

---

*文档版本：1.0*
*重点：环境管理是本项目最容易出错的地方，务必仔细测试*
