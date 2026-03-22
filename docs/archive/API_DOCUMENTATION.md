# 离线网页下载器 - 后端 API 文档

> 本文档汇总了离线网页下载器的所有后端功能接口，供前端开发人员参考。
> 项目类型：Python + Tkinter 桌面应用
> 目标：为构建现代化 Web 前端提供接口说明

---

## 一、系统架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                      前端界面 (Web UI)                        │
├─────────────────────────────────────────────────────────────┤
│  Python HTTP Server / WebSocket / REST API                  │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ 下载模块     │ │ 打包模块     │ │ 许可证模块   │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │
│  │ 浏览器管理   │ │ 资源管理     │ │ 文献下载     │        │
│  └──────────────┘ └──────────────┘ └──────────────┘        │
└─────────────────────────────────────────────────────────────┘
```

---

## 二、核心功能模块 API

### 2.1 许可证管理模块 (license_manager.py)

**类名**: `LicenseManager`

#### 接口列表

| 方法名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `__init__()` | - | - | 初始化，获取机器ID |
| `validate_card_key(card_key)` | `card_key: str` | `bool` | 验证激活码格式 |
| `save_activation(card_key)` | `card_key: str` | `bool` | 保存激活信息到注册表 |
| `check_activation()` | - | `(bool, str)` | 检查激活状态 (是否激活, 消息) |
| `check_trial()` | - | `(bool, int, str)` | 检查试用状态 (是否可用, 剩余次数, 消息) |
| `get_trial_status()` | - | `(bool, int, int)` | 获取试用详情 (是否有效, 剩余, 总数) |
| `get_machine_id_display()` | - | `str` | 获取格式化的机器ID |
| `clear_activation()` | - | `bool` | 清除激活信息 |

#### 常量
```python
TRIAL_COUNT = 200  # 最大试用次数
```

#### 前端调用示例
```javascript
// 检查激活状态
const checkLicense = async () => {
  const response = await fetch('/api/license/check');
  const { is_activated, message, status } = await response.json();
  // status: 'activated' | 'trial' | 'none'
  return { is_activated, message, status };
};

// 激活软件
const activate = async (cardKey) => {
  const response = await fetch('/api/license/activate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ card_key: cardKey })
  });
  return await response.json();
};

// 获取机器ID
const getMachineId = async () => {
  const response = await fetch('/api/license/machine-id');
  const { machine_id } = await response.json();
  return machine_id;
};
```

---

### 2.2 浏览器管理模块 (browser_manager.py)

#### 接口列表

| 函数名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `is_browser_ready()` | - | `bool` | 检查浏览器是否就绪 |
| `check_browser_integrity()` | - | `(bool, str)` | 检查浏览器完整性 |
| `get_chromium_path()` | - | `str/None` | 获取Chromium路径 |
| `setup_browser_env()` | - | `str` | 设置浏览器环境变量 |
| `download_browser(progress_callback, use_mirror)` | `callback: func, use_mirror: bool` | `bool` | 下载浏览器 |

#### 前端调用示例
```javascript
// 检查浏览器状态
const checkBrowser = async () => {
  const response = await fetch('/api/browser/status');
  const { is_ready, message } = await response.json();
  return { is_ready, message };
};

// 下载浏览器（带进度）
const downloadBrowser = () => {
  const ws = new WebSocket('ws://localhost:8080/browser/download');
  ws.onmessage = (event) => {
    const { progress, status, message } = JSON.parse(event.data);
    updateProgress(progress, message);
  };
};
```

---

### 2.3 Playwright 下载模块 (playwright_downloader.py)

**类名**: `PlaywrightDownloader`

#### 构造函数
```python
PlaywrightDownloader(gui=None, log_callback=None, browser_type="auto")
```

#### 接口列表

| 方法名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `download_page(url, save_dir, filename, headless, process_resources)` | 见下方 | `str/None` | 下载单页 |
| `download_batch(urls, save_dir, headless, progress_callback, stop_check, download_mode)` | 见下方 | `list` | 批量下载 |
| `download_multiple(urls, save_dir, progress_callback, headless, stop_check, download_mode)` | 同上 | `list` | 批量下载别名 |
| `open_login_page(site)` | `site: str` | `bool` | 打开登录页面 |
| `connect_to_browser()` | - | `bool` | 连接浏览器 |
| `launch_browser(headless)` | `headless: bool` | `bool` | 启动浏览器 |
| `close(minimize_only)` | `minimize_only: bool` | - | 关闭浏览器 |

#### download_page 参数
```python
{
  "url": "string",           // 目标网址
  "save_dir": "string",      // 保存目录
  "filename": "string",      // 文件名（可选）
  "headless": true,          // 是否无头模式
  "process_resources": true  // 是否处理资源
}
```

#### download_batch 参数
```python
{
  "urls": ["string"],        // URL列表
  "save_dir": "string",      // 保存目录
  "headless": true,          // 是否无头模式
  "progress_callback": func, // 进度回调 (current, total, result, stage, url)
  "stop_check": func,        // 停止检查函数
  "download_mode": "html"    // 下载模式: html | pdf | both
}
```

#### 前端调用示例
```javascript
// 单页下载
const downloadPage = async (url, options) => {
  const response = await fetch('/api/download/page', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      url,
      save_dir: options.saveDir,
      headless: options.headless ?? true,
      process_resources: true
    })
  });
  return await response.json();
};

// 批量下载（WebSocket实时进度）
const batchDownload = (urls, options) => {
  const ws = new WebSocket('ws://localhost:8080/download/batch');
  ws.onopen = () => {
    ws.send(JSON.stringify({
      urls,
      save_dir: options.saveDir,
      download_mode: options.mode || 'html',
      headless: options.headless ?? true
    }));
  };
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    switch(data.type) {
      case 'progress':
        onProgress(data.current, data.total, data.url);
        break;
      case 'stage':
        onStageChange(data.stage); // 'download' | 'process'
        break;
      case 'complete':
        onComplete(data.results);
        break;
      case 'error':
        onError(data.url, data.error);
        break;
    }
  };
  
  return {
    stop: () => ws.send(JSON.stringify({ action: 'stop' })),
    close: () => ws.close()
  };
};

// 打开登录页面
const openLoginPage = async (site) => {
  const response = await fetch('/api/browser/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ site }) // 'zhihu' | 'csdn' | 'juejin' | 'jianshu'
  });
  return await response.json();
};
```

---

### 2.4 核心下载模块 (core_downloader.py)

**类名**: `CoreDownloader`

#### 构造函数参数
```python
{
  "url": "string",           // 起始URL
  "output_dir": "string",    // 输出目录
  "depth": 0,                // 爬取深度
  "mode": "full",            // 模式: full | media_only
  "convert_img": false,      // 是否转换图片
  "target_fmt": "PNG",       // 目标图片格式
  "filter_img": true,        // 是否过滤图片
  "filter_video": true,      // 是否过滤视频
  "max_pages": -1            // 最大页面数 (-1=无限)
}
```

#### 接口列表

| 方法名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `start()` | - | `bool` | 开始下载 |
| `stop()` | - | - | 停止下载 |
| `process_page(url, depth)` | `url: str, depth: int` | - | 处理单个页面 |
| `get_headers(url)` | `url: str` | `dict` | 获取请求头 |

#### 前端调用示例
```javascript
// 开始爬取下载
const startCrawl = async (config) => {
  const response = await fetch('/api/download/crawl', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      url: config.url,
      output_dir: config.outputDir,
      depth: config.depth || 0,
      mode: config.mode || 'full',
      convert_img: config.convertImg || false,
      target_fmt: config.targetFmt || 'PNG',
      filter_img: config.filterImg !== false,
      filter_video: config.filterVideo !== false,
      max_pages: config.maxPages || -1
    })
  });
  return await response.json();
};

// 停止下载
const stopDownload = async () => {
  await fetch('/api/download/stop', { method: 'POST' });
};
```

---

### 2.5 打包模块 (gui.py 中的打包功能)

#### 打包配置参数
```python
{
  // 基本配置
  "website_dir": "string",       // 网站目录
  "html_file": "string",         // HTML文件路径
  "app_name": "string",          // 应用名称
  "title": "string",             // 窗口标题
  
  // 窗口配置
  "width": 1200,                 // 窗口宽度
  "height": 850,                 // 窗口高度
  "title_bar_color": "#2d2d2d",  // 标题栏颜色
  "text_color": "#ffffff",       // 文字颜色
  "border_color": "#1a1a1a",     // 边框颜色
  "show_nav": true,              // 显示导航
  "show_window_controls": false, // 显示窗口控制按钮
  
  // 打包选项
  "mode": "onefile",             // 模式: onefile | onedir
  "force_internal": true,        // 强制内部导航
  "debug_mode": false,           // 调试模式
  
  // 版本信息
  "icon_path": "string",         // 图标路径
  "publisher": "Thanksplay",     // 发布者
  "version": "1.0",              // 版本号
  "file_description": "string",  // 文件描述
  "output_dir": "pack_output",   // 输出目录
  
  // 文件锁配置
  "enable_lock": false,          // 启用文件锁
  "lock_password": "string",     // 锁密码
  "lock_mode": "always",         // 锁模式: always | startup
  "lock_contact_type": "QQ",     // 联系类型
  "lock_contact_info": "string"  // 联系信息
}
```

#### 接口列表

| 方法名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `preview_pack()` | - | - | 预览打包效果 |
| `start_pack()` | - | - | 开始打包 |
| `auto_detect_website_dir()` | - | `list` | 自动检测网站目录 |
| `ensure_python_env()` | - | `bool` | 确保Python环境可用 |

#### 前端调用示例
```javascript
// 自动检测网站目录
const detectWebsites = async () => {
  const response = await fetch('/api/pack/detect');
  const { websites } = await response.json();
  return websites; // [{ name, path, html_files, size }]
};

// 预览打包
const previewPack = async (config) => {
  const response = await fetch('/api/pack/preview', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config)
  });
  return await response.json();
};

// 开始打包（WebSocket进度）
const startPack = (config) => {
  const ws = new WebSocket('ws://localhost:8080/pack/start');
  ws.onopen = () => {
    ws.send(JSON.stringify(config));
  };
  
  ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    switch(data.type) {
      case 'progress':
        onProgress(data.percent, data.message);
        break;
      case 'stage':
        onStageChange(data.stage);
        break;
      case 'complete':
        onComplete(data.output_path);
        break;
      case 'error':
        onError(data.message);
        break;
    }
  };
};
```

---

### 2.6 资源管理模块

#### 接口列表

| 方法名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `refresh_resource_list()` | - | `list` | 刷新资源列表 |
| `delete_resource(path)` | `path: str` | `bool` | 删除资源 |
| `open_resource_location(path)` | `path: str` | - | 打开资源位置 |
| `send_to_pack(path)` | `path: str` | - | 发送到打包 |
| `localize_resource(path)` | `path: str` | `bool` | 本地化部署 |

#### 前端调用示例
```javascript
// 获取资源列表
const getResources = async () => {
  const response = await fetch('/api/resources/list');
  const { resources } = await response.json();
  return resources.map(r => ({
    name: r.name,
    path: r.path,
    size: r.size,
    created_at: r.created_at,
    file_count: r.file_count,
    html_files: r.html_files
  }));
};

// 删除资源
const deleteResource = async (path) => {
  const response = await fetch('/api/resources/delete', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path })
  });
  return await response.json();
};

// 发送到打包
const sendToPack = async (path) => {
  await fetch('/api/resources/send-to-pack', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path })
  });
};
```

---

### 2.7 配置管理模块

#### 配置文件

**config.json**:
```json
{
  "path_mode": "absolute",      // 路径模式: absolute | relative
  "browser_type": "auto"        // 浏览器类型: auto | internal | chrome | edge | firefox
}
```

**window_config.json**:
```json
{
  "width": 1065,
  "height": 925,
  "x": 821,
  "y": 78
}
```

#### 接口列表

| 方法名 | 参数 | 返回值 | 说明 |
|--------|------|--------|------|
| `load_config()` | - | `dict` | 加载配置 |
| `save_config(config)` | `config: dict` | `bool` | 保存配置 |
| `_load_window_geometry()` | - | `tuple/None` | 加载窗口几何信息 |
| `_save_window_geometry(w, h, x, y)` | 宽高位置 | `bool` | 保存窗口几何信息 |

#### 前端调用示例
```javascript
// 加载配置
const loadConfig = async () => {
  const response = await fetch('/api/config');
  return await response.json();
};

// 保存配置
const saveConfig = async (config) => {
  const response = await fetch('/api/config', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(config)
  });
  return await response.json();
};
```

---

## 三、WebSocket 实时通信协议

### 3.1 下载进度推送

```javascript
// 客户端连接
const ws = new WebSocket('ws://localhost:8080/ws/download');

// 消息格式
{
  "type": "progress",      // 消息类型
  "current": 5,            // 当前进度
  "total": 10,             // 总数
  "url": "https://...",    // 当前URL
  "stage": "download"      // 阶段: download | process
}

// 阶段说明
// - download: 正在下载网页
// - process: 正在处理资源（内嵌图片/CSS等）
```

### 3.2 打包进度推送

```javascript
// 消息格式
{
  "type": "progress",
  "percent": 45,           // 进度百分比
  "stage": "collecting",   // 阶段
  "message": "正在收集文件..."
}

// 阶段列表
// - collecting: 收集文件
// - copying: 复制资源
// - generating: 生成启动器
// - compiling: 编译EXE
// - complete: 完成
```

---

## 四、REST API 端点汇总

### 4.1 许可证相关
```
GET  /api/license/check          # 检查许可证状态
GET  /api/license/machine-id     # 获取机器ID
POST /api/license/activate       # 激活软件
POST /api/license/clear          # 清除激活
```

### 4.2 浏览器相关
```
GET  /api/browser/status         # 获取浏览器状态
POST /api/browser/download       # 下载浏览器
POST /api/browser/login          # 打开登录页面
```

### 4.3 下载相关
```
POST /api/download/page          # 单页下载
POST /api/download/crawl         # 爬取下载
POST /api/download/batch         # 批量下载
POST /api/download/stop          # 停止下载
GET  /api/download/preview       # 爬取预览
```

### 4.4 打包相关
```
GET  /api/pack/detect            # 检测网站目录
POST /api/pack/preview           # 预览打包
POST /api/pack/start             # 开始打包
POST /api/pack/stop              # 停止打包
```

### 4.5 资源管理相关
```
GET  /api/resources/list         # 获取资源列表
POST /api/resources/delete       # 删除资源
POST /api/resources/open         # 打开资源位置
POST /api/resources/send-to-pack # 发送到打包
POST /api/resources/localize     # 本地化部署
```

### 4.6 配置相关
```
GET  /api/config                 # 获取配置
POST /api/config                 # 保存配置
GET  /api/config/window          # 获取窗口配置
POST /api/config/window          # 保存窗口配置
```

---

## 五、前端开发建议

### 5.1 技术栈推荐

```
框架: React / Vue 3 / Svelte
UI组件: Ant Design / Element Plus / shadcn/ui
状态管理: Zustand / Pinia
HTTP客户端: Axios / Fetch
WebSocket: Socket.io / 原生 WebSocket
打包: Vite / Webpack
```

### 5.2 页面结构建议

```
/src
├── components/           # 公共组件
│   ├── Header/          # 顶部导航
│   ├── Sidebar/         # 侧边栏
│   ├── ProgressBar/     # 进度条
│   └── LogViewer/       # 日志查看器
├── views/               # 页面视图
│   ├── Download/        # 下载模式
│   ├── Literature/      # 文献下载
│   ├── Resources/       # 资源管理
│   ├── Pack/            # 打包模式
│   ├── Localize/        # 本地化部署
│   └── Settings/        # 设置
├── api/                 # API接口
│   ├── license.js
│   ├── browser.js
│   ├── download.js
│   ├── pack.js
│   └── resources.js
├── stores/              # 状态管理
│   ├── downloadStore.js
│   ├── browserStore.js
│   └── configStore.js
└── utils/               # 工具函数
    ├── websocket.js
    └── format.js
```

### 5.3 关键交互设计

1. **下载进度显示**
   - 使用进度条 + 百分比
   - 显示当前下载的URL
   - 区分"下载阶段"和"处理阶段"
   - 提供停止按钮

2. **浏览器状态指示**
   - 红绿灯状态指示
   - 一键下载/安装浏览器
   - 登录状态提示

3. **资源管理**
   - 卡片式布局展示已下载网站
   - 右键菜单操作
   - 缩略图预览
   - 批量操作支持

4. **打包配置**
   - 可视化配置表单
   - 实时预览窗口
   - 颜色选择器
   - 图标上传

### 5.4 与 Python 后端集成

由于原项目是 Python Tkinter 桌面应用，要构建 Web 前端需要：

**方案1: HTTP API 服务器**
```python
# 使用 Flask/FastAPI 包装原有功能
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/api/download/page', methods=['POST'])
def download_page():
    data = request.json
    downloader = PlaywrightDownloader()
    result = downloader.download_page(**data)
    return jsonify({"success": result is not None, "path": result})
```

**方案2: WebSocket 实时通信**
```python
# 使用 Flask-SocketIO
from flask_socketio import SocketIO, emit

socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('download_batch')
def handle_batch_download(data):
    def progress_callback(current, total, result, stage, url):
        emit('progress', {
            'current': current,
            'total': total,
            'stage': stage,
            'url': url
        })
    
    downloader = PlaywrightDownloader()
    results = downloader.download_batch(
        urls=data['urls'],
        save_dir=data['save_dir'],
        progress_callback=progress_callback
    )
    emit('complete', {'results': results})
```

---

## 六、数据类型定义

### 6.1 TypeScript 接口定义

```typescript
// 许可证状态
interface LicenseStatus {
  is_activated: boolean;
  message: string;
  status: 'activated' | 'trial' | 'none';
  trial_remaining?: number;
  machine_id?: string;
}

// 浏览器状态
interface BrowserStatus {
  is_ready: boolean;
  is_internal_ready: boolean;
  detected_browsers: Array<{
    id: string;
    name: string;
    path: string;
  }>;
}

// 下载配置
interface DownloadConfig {
  url: string;
  output_dir: string;
  depth?: number;
  mode?: 'full' | 'media_only';
  convert_img?: boolean;
  target_fmt?: 'PNG' | 'JPEG' | 'WEBP';
  filter_img?: boolean;
  filter_video?: boolean;
  max_pages?: number;
}

// 批量下载配置
interface BatchDownloadConfig {
  urls: string[];
  save_dir: string;
  download_mode: 'html' | 'pdf' | 'both';
  output_mode: 'embedded' | 'external';
  structure: 'toc' | 'original';
  dedup: boolean;
  headless?: boolean;
}

// 打包配置
interface PackConfig {
  website_dir: string;
  html_file?: string;
  app_name: string;
  title: string;
  width: number;
  height: number;
  title_bar_color: string;
  text_color: string;
  border_color: string;
  show_nav: boolean;
  show_window_controls: boolean;
  mode: 'onefile' | 'onedir';
  force_internal: boolean;
  debug_mode: boolean;
  icon_path?: string;
  publisher: string;
  version: string;
  file_description?: string;
  output_dir: string;
  enable_lock?: boolean;
  lock_password?: string;
  lock_mode?: 'always' | 'startup';
  lock_contact_type?: string;
  lock_contact_info?: string;
}

// 资源项
interface ResourceItem {
  name: string;
  path: string;
  size: number;
  created_at: string;
  file_count: number;
  html_files: string[];
}

// 下载进度
interface DownloadProgress {
  type: 'progress' | 'stage' | 'complete' | 'error';
  current?: number;
  total?: number;
  url?: string;
  stage?: 'download' | 'process';
  results?: Array<{
    url: string;
    success: boolean;
    filepath?: string;
  }>;
  error?: string;
}

// 打包进度
interface PackProgress {
  type: 'progress' | 'stage' | 'complete' | 'error';
  percent?: number;
  stage?: string;
  message?: string;
  output_path?: string;
  error?: string;
}
```

---

## 七、错误处理

### 7.1 错误码定义

```typescript
enum ErrorCode {
  // 许可证错误
  LICENSE_INVALID = 1001,
  LICENSE_EXPIRED = 1002,
  LICENSE_MACHINE_MISMATCH = 1003,
  
  // 浏览器错误
  BROWSER_NOT_READY = 2001,
  BROWSER_DOWNLOAD_FAILED = 2002,
  BROWSER_LAUNCH_FAILED = 2003,
  
  // 下载错误
  DOWNLOAD_NETWORK_ERROR = 3001,
  DOWNLOAD_TIMEOUT = 3002,
  DOWNLOAD_SSL_ERROR = 3003,
  DOWNLOAD_RATE_LIMITED = 3004,
  
  // 打包错误
  PACK_RESOURCE_NOT_FOUND = 4001,
  PACK_COMPILATION_FAILED = 4002,
  PACK_PYTHON_ENV_MISSING = 4003,
}
```

### 7.2 错误响应格式

```json
{
  "success": false,
  "error_code": 3001,
  "message": "网络连接错误",
  "details": "无法连接到目标服务器",
  "timestamp": "2026-03-13T10:30:00Z"
}
```

---

## 八、附录

### 8.1 支持的网站

```javascript
const SUPPORTED_SITES = {
  'zhihu.com': '知乎',
  'csdn.net': 'CSDN',
  'juejin.cn': '掘金',
  'jianshu.com': '简书',
  'bilibili.com': '哔哩哔哩',
  'cnblogs.com': '博客园',
  'segmentfault.com': 'SegmentFault',
  'stackoverflow.com': 'Stack Overflow',
  'github.com': 'GitHub',
  'weixin.qq.com': '微信公众号',
  'baike.baidu.com': '百度百科',
  // ... 更多网站
};
```

### 8.2 浏览器类型

```javascript
const BROWSER_TYPES = [
  { value: 'auto', label: '自动检测' },
  { value: 'internal', label: '内置Chromium' },
  { value: 'chrome', label: 'Google Chrome' },
  { value: 'edge', label: 'Microsoft Edge' },
  { value: 'firefox', label: 'Firefox' }
];
```

### 8.3 下载模式

```javascript
const DOWNLOAD_MODES = [
  { value: 'single', label: '单页下载' },
  { value: 'crawl', label: '爬取下载' },
  { value: 'batch', label: '批量下载' }
];

const BATCH_OUTPUT_MODES = [
  { value: 'embedded', label: '单独HTML(内嵌资源)' },
  { value: 'external', label: '资源外置(CSS/JS单独存放)' }
];

const BATCH_STRUCTURE_MODES = [
  { value: 'toc', label: '目录模式(注入悬浮目录)' },
  { value: 'original', label: '网站原有结构' }
];
```

---

*文档版本: 1.0*
*最后更新: 2026-03-13*
*作者: AI Assistant*
