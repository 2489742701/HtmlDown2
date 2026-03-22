# PyInstaller 单文件模式 tkinter TCL/TK 打包问题

## 问题描述

使用 PyInstaller 打包包含 tkinter 的 Python 程序时：
- **目录模式（onedir）**：正常工作 ✅
- **单文件模式（onefile）**：运行时报错 ❌

## 错误信息

```
_tkinter.TclError: Can't find a usable init.tcl in the following directories:
    {C:\Users\LONGYA~1\AppData\Local\Temp\_MEIxxxxx\_tcl_data} 
    C:/Users/LONGYA~1/AppData/Local/Temp/lib/tcl8.6 
    ...

This probably means that Tcl wasn't installed properly.
```

## 环境信息

- Python: 3.13.2
- PyInstaller: 6.17.0
- 操作系统: Windows 10
- TCL 版本: 8.6.12

## 已尝试的解决方案

### 1. 依赖 PyInstaller 内置的 tkinter hook（失败）

spec 文件：
```python
# 离线网页下载器_单文件.spec
datas = [
    ('assets/icon.ico', '.'),
    ('config.json', '.'),
]

hiddenimports = [
    'tkinter',
    'tkinter.ttk',
    # ... 其他模块
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # ...
)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='离线网页下载器_单文件',
    # ...
)
```

**结果**：目录模式正常，单文件模式报 TCL 错误

### 2. 手动添加 TCL 数据文件（失败）

尝试使用 `tcltk_info.data_files` 手动添加 TCL 数据：

```python
from PyInstaller.utils.hooks.tcl_tk import tcltk_info

datas = [
    ('assets/icon.ico', '.'),
    ('config.json', '.'),
]

for item in tcltk_info.data_files:
    dest, src, typ = item
    datas.append((src, dest_dir))  # 多种路径格式都试过
```

**结果**：打包时报错 `Failed to extract _tcl_data\auto.tcl\auto.tcl: failed to open target file!`

### 3. 添加自定义 runtime hook（失败）

创建 `rthook_tkinter.py`：
```python
import os
import sys

if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
    tcl_dir = os.path.join(base_path, '_tcl_data')
    tk_dir = os.path.join(base_path, '_tk_data')
    
    if os.path.isdir(tcl_dir):
        os.environ['TCL_LIBRARY'] = tcl_dir
    if os.path.isdir(tk_dir):
        os.environ['TK_LIBRARY'] = tk_dir
```

**结果**：同样失败，TCL 数据文件路径问题

### 4. 在 main.py 中设置 TCL_LIBRARY（失败）

```python
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
    tcl_paths = [
        os.path.join(base_path, '_tcl_data'),
        os.path.join(base_path, 'tcl8.6'),
        # ...
    ]
    for tcl_path in tcl_paths:
        if os.path.exists(os.path.join(tcl_path, 'init.tcl')):
            os.environ['TCL_LIBRARY'] = tcl_path
            break
```

**结果**：目录模式正常，单文件模式仍然失败

## 关键发现

### PyInstaller 的 tkinter hook 行为

1. PyInstaller 有内置的 `hook-_tkinter.py`，会自动调用 `tcltk_info.data_files` 收集 TCL 数据
2. 内置的 runtime hook `pyi_rth__tkinter.py` 会设置 `TCL_LIBRARY` 和 `TK_LIBRARY` 环境变量
3. 目录模式下这些机制工作正常

### 目录模式 vs 单文件模式的区别

**目录模式**：
- 文件解压到 `dist\程序名\_internal\` 目录
- TCL 数据在 `_internal\_tcl_data\` 和 `_internal\_tk_data\`
- 运行时直接从目录读取

**单文件模式**：
- 所有文件打包到一个 EXE
- 运行时解压到临时目录 `C:\Users\...\AppData\Local\Temp\_MEIxxxxx\`
- TCL 数据应该在 `_MEIxxxxx\_tcl_data\` 目录

### 调试信息

目录模式下 `tcl_debug.txt` 显示：
```
base_path: C:\Users\...\dist\离线网页下载器\_internal
Contents: [..., '_tcl_data', '_tk_data', ...]
```

单文件模式下错误信息显示：
```
base_path: C:\Users\LONGYA~1\AppData\Local\Temp\_MEIxxxxx
Can't find a usable init.tcl in the following directories:
    {C:\Users\LONGYA~1\AppData\Local\Temp\_MEIxxxxx\_tcl_data}
```

注意：错误信息中 `_tcl_data` 路径被大括号包围 `{...}`，这可能表示路径格式问题。

## 相关文件

### 目录模式 spec 文件（正常工作）

文件：`离线网页下载器.spec`

```python
# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None

tkinter_datas = collect_data_files('tkinter')

datas = [
    ('assets/icon.ico', '.'),
    ('config.json', '.'),
] + tkinter_datas

hiddenimports = [
    'tkinter',
    'tkinter.ttk',
    # ... 其他模块
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    # ...
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,  # 目录模式关键
    name='离线网页下载器',
    console=True,
    icon='assets/icon.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    name='离线网页下载器',
)
```

### 单文件模式 spec 文件（失败）

文件：`离线网页下载器_单文件.spec`

```python
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

datas = [
    ('assets/icon.ico', '.'),
    ('config.json', '.'),
]

hiddenimports = [
    'tkinter',
    'tkinter.ttk',
    # ... 其他模块
]

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    # ...
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='离线网页下载器_单文件',
    console=True,
    icon='assets/icon.ico',
)
```

## 可能的原因

1. **路径分隔符问题**：Windows 使用 `\`，但 TCL 可能期望 `/`
2. **临时目录路径格式**：`_MEIxxxxx` 路径可能包含特殊字符
3. **PyInstaller 单文件模式的 TCL 数据提取问题**
4. **Python 3.13 与 PyInstaller 6.17.0 的兼容性问题**

## 需要帮助

1. 如何在 PyInstaller 单文件模式下正确打包 tkinter/TCL？
2. 是否有已知的 Python 3.13 + PyInstaller 6.17.0 + tkinter 单文件打包问题？
3. 是否有其他打包工具（如 cx_Freeze, Nuitka）可以解决这个问题？

## 临时解决方案

目前使用**目录模式**作为临时解决方案：
```bash
python -m PyInstaller --clean "离线网页下载器.spec"
```

生成的程序在 `dist\离线网页下载器\` 目录中，可以正常运行。
