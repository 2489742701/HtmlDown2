import os
import re
import time
import threading
import platform
import subprocess
import sys
import shutil
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox, font as tkfont
import ctypes

script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)
from urllib.parse import urljoin, urlparse, unquote
from io import BytesIO
import requests
from bs4 import BeautifulSoup
from PIL import Image
import concurrent.futures
import traceback
import json
import multiprocessing
import sys

def is_frozen():
    return getattr(sys, 'frozen', False) or globals().get('__compiled__') is not None

def get_base_path():
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    if globals().get('__compiled__') is not None:
        return os.path.dirname(os.path.abspath(__file__))
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_external_base_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    if globals().get('__compiled__') is not None:
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

def set_window_top(hwnd):
    try:
        HWND_TOP = 0
        SWP_NOSIZE = 0x0001
        SWP_NOMOVE = 0x0002
        SWP_SHOWWINDOW = 0x0040
        ctypes.windll.user32.SetWindowPos(hwnd, HWND_TOP, 0, 0, 0, 0, SWP_NOSIZE | SWP_NOMOVE | SWP_SHOWWINDOW)
        ctypes.windll.user32.SetForegroundWindow(hwnd)
    except:
        pass

def get_browser_hwnd():
    try:
        result = subprocess.run(['powershell', '-Command', 
            f'Get-Process | Where-Object {{$_.MainWindowTitle -ne "" -and ($_.ProcessName -like "*chrome*" -or $_.ProcessName -like "*msedge*" -or $_.ProcessName -like "*chromium*")}} | Select-Object -First 1 -ExpandProperty MainWindowHandle'],
            capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            return int(result.stdout.strip())
    except:
        pass
    return None

try:
    from fake_useragent import UserAgent
    _ua_available = True
except Exception:
    _ua_available = False
    UserAgent = None

SITE_NAMES = {
    'zhihu.com': '知乎',
    'csdn.net': 'CSDN',
    'juejin.cn': '掘金',
    'jianshu.com': '简书',
    'bilibili.com': '哔哩哔哩',
    'cnblogs.com': '博客园',
    'segmentfault.com': 'SegmentFault',
    'stackoverflow.com': 'Stack Overflow',
    'github.com': 'GitHub',
    'gitee.com': 'Gitee',
    'weixin.qq.com': '微信公众号',
    'mp.weixin.qq.com': '微信公众号',
    'baike.baidu.com': '百度百科',
    'baidu.com': '百度',
    'taobao.com': '淘宝',
    'jd.com': '京东',
    'weibo.com': '微博',
    'douban.com': '豆瓣',
    'xiaohongshu.com': '小红书',
    'toutiao.com': '今日头条',
    '163.com': '网易',
    'qq.com': '腾讯',
    'sina.com.cn': '新浪',
    'sohu.com': '搜狐',
    'ifeng.com': '凤凰网',
    '36kr.com': '36氪',
    'infoq.cn': 'InfoQ',
    'oschina.net': '开源中国',
    'iteye.com': 'ITeye',
    'cnbeta.com': 'cnBeta',
    'ithome.com': 'IT之家',
}

def get_site_name(domain):
    if not domain:
        return None
    domain = domain.replace('www.', '')
    for site_domain, site_name in SITE_NAMES.items():
        if site_domain in domain:
            return site_name
    return domain

from user_manual import UserManual
from error_dialog import ErrorDialog
from core_downloader import CoreDownloader, save_crash_log

class WebDownloaderGUI:
    CONFIG_FILE = "window_config.json"
    
    def __init__(self, root):
        self.root = root
        
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        
        saved_geometry = self._load_window_geometry()
        if saved_geometry:
            window_width, window_height, pos_x, pos_y = saved_geometry
        else:
            window_width = 1065
            window_height = 925
            pos_x = 821
            pos_y = 78
        
        title = "🌐 网页资源离线下载器 - 专业美化版"
        trial_color = None
        trial_remaining = 0
        
        try:
            from license_manager import LicenseManager
            lm = LicenseManager()
            is_activated, _ = lm.check_activation()
            if not is_activated:
                is_trial, remaining, total = lm.get_trial_status()
                if is_trial and remaining > 0:
                    trial_remaining = remaining
                    if remaining > 15:
                        trial_color = "#27ae60"
                    elif remaining > 5:
                        trial_color = "#f39c12"
                    else:
                        trial_color = "#e74c3c"
                    title += f" | 剩余 {remaining} 次启动"
        except:
            pass
        
        self.root.title(title)
        self.root.geometry(f"{window_width}x{window_height}+{pos_x}+{pos_y}")
        self.root.configure(bg='#f5f5f5')
        
        self.root.bind("<Configure>", self._on_window_configure)
        self.root.bind("<FocusIn>", self._on_window_focus_in)
        
        self.trial_remaining = trial_remaining
        self.trial_color = trial_color
        
        icon_path = get_resource_path('assets/icon.ico')
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
                try:
                    from PIL import Image, ImageTk
                    img = Image.open(icon_path)
                    photo = ImageTk.PhotoImage(img)
                    self.root.iconphoto(False, photo)
                except:
                    pass
            except Exception as e:
                print(f"[Error] Cannot load icon: {e}")
                print(f"[错误] 无法加载图标: {e}")
        
        self.url_var = tk.StringVar()
        default_dir = "downloads"
        self.save_dir_var = tk.StringVar(value=default_dir)
        
        self.depth_var = tk.IntVar(value=0)
        self.mode_var = tk.StringVar(value="full")
        self.convert_img_var = tk.BooleanVar(value=False)
        self.target_fmt_var = tk.StringVar(value="PNG")
        self.filter_video_var = tk.BooleanVar(value=True)
        self.filter_img_var = tk.BooleanVar(value=True)
        self.auto_open_var = tk.BooleanVar(value=True)
        self.auto_localize_var = tk.BooleanVar(value=False)
        self.path_mode_var = tk.StringVar(value="relative")
        
        self.use_webview_var = tk.BooleanVar(value=False)
        self.device_var = tk.StringVar(value="desktop")
        self.wait_mode_var = tk.StringVar(value="no_wait")
        self.custom_wait_var = tk.IntVar(value=15)
        self.depth_mode_var = tk.StringVar(value="page_next2")
        self.custom_depth_var = tk.IntVar(value=5)
        self.max_pages_var = tk.IntVar(value=-1)
        self.custom_pages_var = tk.IntVar(value=100)
        
        self.browser_type_var = tk.StringVar(value="auto")
        self._detected_browsers = []
        self._browser_search_done = False
        self._pw_downloader = None
        
        self.is_running = False
        self.current_task_dir = ""
        
        self.pack_website_dir = tk.StringVar()
        self.pack_html_file = tk.StringVar()
        self.pack_app_name = tk.StringVar(value="我的应用")
        self.pack_title = tk.StringVar(value="我的应用")
        self.pack_width = tk.IntVar(value=1200)
        self.pack_height = tk.IntVar(value=850)
        self.pack_title_bar_color = tk.StringVar(value="#2d2d2d")
        self.pack_text_color = tk.StringVar(value="#ffffff")
        self.pack_border_color = tk.StringVar(value="#1a1a1a")
        self.pack_show_nav = tk.BooleanVar(value=True)
        self.pack_show_window_controls = tk.BooleanVar(value=False)
        self.pack_force_internal = tk.BooleanVar(value=True)
        self.pack_debug_mode = tk.BooleanVar(value=False)
        self.pack_mode = tk.StringVar(value="onefile")
        self.pack_icon_path = tk.StringVar()
        self.pack_publisher = tk.StringVar(value="Thanksplay")
        self.pack_version = tk.StringVar(value="1.0")
        self.pack_file_description = tk.StringVar(value="")
        self.pack_output_dir = tk.StringVar(value="pack_output")
        self.pack_preview_process = None
        
        self.pack_enable_lock = tk.BooleanVar(value=False)
        self.pack_lock_password = tk.StringVar()
        self.pack_lock_mode = tk.StringVar(value="always")
        # 文件锁联系人信息（用于密码忘记时的联系）
        self.pack_lock_contact_type = tk.StringVar(value="QQ")  # 联系类型：QQ、微信、电话等
        self.pack_lock_contact_info = tk.StringVar(value="")    # 联系信息
        
        self.localize_website_dir = tk.StringVar()
        
        self._browser_manager = None
        self._browser_process = None
        self._browser_context = None
        self._browser_data_dir = os.path.join(os.path.dirname(__file__), "browser_data")
        
        self.monitor_window = None
        self._batch_url_listbox = None
        self._batch_download_btn = None
        self._batch_stop_btn = None
        self._batch_log_area = None
        self._batch_should_stop = False
        self._batch_resource_cache = {}
        self._batch_output_var = None
        self._batch_output_mode_var = None
        self._batch_structure_var = None
        self._batch_dedup_var = None
        self._download_warning_result = None
        self._stop_monitor = False
        self._literature_downloader = None
        self._literature_should_stop = False
        self._floating_progress_window = None
        self._floating_log_text = None

        self.load_config()
        self.setup_styles()
        self.create_widgets()
        self.update_path_display()
        self.update_depth_value()
        
        self.root.after(500, self._check_browser_on_startup)
        
        self.manual = UserManual(root=self.root)
        self.manual_data = [
            {
                "title": "📖 快速入门",
                "content": "欢迎使用离线网页下载器！\n\n1. 在下载模式中输入网页URL\n2. 设置保存路径（支持相对路径和绝对路径）\n3. 配置下载参数（深度、过滤等）\n4. 点击开始下载\n\n下载完成后，可以在资源管理中查看已下载的网站。"
            },
            {
                "title": "🎯 下载模式",
                "content": "下载模式用于下载网页资源到本地。\n\n主要功能：\n- 输入URL：支持HTTP和HTTPS协议\n- 保存路径：支持相对路径（downloads）和绝对路径\n- 爬取深度：控制下载的页面层级\n- 资源过滤：可选择是否下载图片、视频等\n- 设备标识：模拟不同设备访问网页\n- 页数限制：控制最大下载页数（无限/10/50/100/自定义）\n\n提示：建议首次使用时先使用爬取预览功能，了解将要下载的内容。"
            },
            {
                "title": "📦 打包模式",
                "content": "打包模式可以将下载的网站打包成独立的EXE程序。\n\n主要功能：\n- 自动检测：自动查找已下载的HTML文件\n- 应用配置：设置应用名称、窗口大小、标题栏颜色等\n- 图标设置：选择自定义图标（默认使用程序图标）\n- 预览功能：在打包前预览效果\n- 内部导航：强制在应用内打开链接\n\n注意事项：\n- 打包后的EXE文件较大，包含所有网页资源\n- 需要安装PyInstaller和PyWebView\n- 输出目录默认为pack_output（相对路径）"
            },
            {
                "title": "🗂️ 资源管理",
                "content": "资源管理用于管理已下载的网站。\n\n主要功能：\n- 网站列表：显示所有已下载的网站\n- 文件信息：显示下载时间、文件大小等\n- 右键菜单：\n  - 打开位置：在文件管理器中打开\n  - 删除：删除选中的网站\n  - 发送到打包：将网站发送到打包模式\n  - 本地化部署：将网站转换为本地可浏览格式\n\n提示：使用颜色编码快速识别文件新旧程度（绿色=最新，黑色=最旧）"
            },
            {
                "title": "🔧 本地化部署",
                "content": "本地化部署可以将下载的网站转换为本地可浏览格式。\n\n主要功能：\n- 路径转换：将相对路径转换为绝对路径\n- 登录验证移除：自动移除登录相关脚本\n- 直接浏览：在浏览器中直接打开HTML文件\n\n注意事项：\n- 可能导致CSS样式问题\n- 某些网站功能可能失效\n- 建议先测试再使用\n\n提示：如果CSS样式出现问题，请使用打包模式代替。"
            },
            {
                "title": "⚙️ 路径模式",
                "content": "路径模式决定文件保存和查找的方式。\n\n相对路径：\n- 默认选项\n- 文件保存在程序目录下的downloads文件夹\n- 适合便携使用\n- 打包时建议使用相对路径\n\n绝对路径：\n- 可自定义保存位置\n- 默认为D:\\网页资源下载\n- 适合固定使用场景\n- 记住用户选择\n\n提示：所有模块（下载、打包、本地化部署）都支持路径模式切换。"
            },
            {
                "title": "🔍 爬取预览",
                "content": "爬取预览功能可以在下载前预估资源情况。\n\n预览信息：\n- 预计页面数：将要下载的页面数量\n- 预计资源数：将要下载的资源数量\n- 预计磁盘占用：预计需要的磁盘空间\n\n使用方法：\n1. 输入URL\n2. 设置爬取深度和页数限制\n3. 点击爬取预览按钮\n4. 查看预览结果\n5. 根据结果调整参数或开始下载\n\n提示：预览功能不会下载任何文件，只分析网页结构。"
            },
            {
                "title": "❓ 常见问题",
                "content": "Q: 下载速度慢怎么办？\nA: 可以尝试减少爬取深度或使用更快的网络。\n\nQ: 打包失败怎么办？\nA: 确保已安装PyInstaller和PyWebView，并检查Python环境。\n\nQ: CSS样式在本地化部署后失效？\nA: 这是正常现象，建议使用打包模式代替本地化部署。\n\nQ: 如何删除已下载的网站？\nA: 在资源管理中右键点击网站，选择删除。\n\nQ: 程序关闭后剪贴板内容被清空？\nA: 这是已知问题，建议在程序外复制重要内容。"
            },
            {
                "title": "💡 最佳实践",
                "content": "1. 首次使用建议：\n   - 先用爬取预览了解网站结构\n   - 从小网站开始测试\n   - 逐步增加爬取深度\n\n2. 打包建议：\n   - 使用相对路径确保可移植性\n   - 测试预览后再打包\n   - 启用内部导航提升体验\n\n3. 资源管理建议：\n   - 定期清理不需要的网站\n   - 使用颜色编码快速识别\n   - 合理组织文件结构\n\n4. 性能优化：\n   - 设置合理的页数限制\n   - 过滤不需要的资源类型\n   - 使用更快的网络连接"
            },
            {
                "title": "🆘 故障排除",
                "content": "下载失败：\n- 检查网络连接\n- 验证URL是否正确\n- 查看错误日志\n\n打包失败：\n- 检查PyInstaller和PyWebView安装\n- 检查磁盘空间\n- 查看打包日志\n\n预览失败：\n- 检查网站目录是否存在\n- 检查HTML文件是否有效\n- 查看错误信息\n\n程序崩溃：\n- 查看错误弹窗\n- 检查Python版本\n- 重新安装依赖包"
            },
            {
                "title": "📞 联系支持",
                "content": "如有问题或建议，请联系：\n\n开发者：Thanksplay\n\n遇到未知问题？\n- 如果本手册中没有找到解决方案\n- 如果程序出现异常或错误\n- 如果需要个性化定制或技术支持\n\n反馈渠道：\n- 闲鱼：搜索\"Thanksplay\"联系开发者\n- 在程序中提交问题反馈\n- 联系开发者获取技术支持\n\n更新说明：\n- 检查程序目录下的更新日志\n- 关注官方渠道获取最新版本\n\n感谢使用离线网页下载器！"
            },
            {
                "title": "📝 更新日志",
                "content": "版本 2.0\n- 新增打包模式，支持将网站打包成EXE\n- 新增资源管理功能\n- 新增本地化部署功能\n- 新增爬取预览功能\n- 新增路径模式切换\n- 优化用户界面\n- 修复已知问题\n\n版本 1.0\n- 基础下载功能\n- 网页资源提取\n- 图片格式转换"
            }
        ]
        self.manual.set_manual_data(self.manual_data)

    def load_config(self):
        base_path = get_base_path()
        config_file = os.path.join(base_path, "config.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    path_mode = config.get('path_mode', 'relative')
                    self.path_mode_var.set(path_mode)
                    browser_type = config.get('browser_type', 'auto')
                    self.browser_type_var.set(browser_type)
            except Exception as e:
                print(f"加载配置失败: {e}")

    def save_config(self):
        try:
            base_path = get_base_path()
            config_file = os.path.join(base_path, "config.json")
            
            config = {
                'path_mode': self.path_mode_var.get(),
                'browser_type': self.browser_type_var.get()
            }
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Error] Save config failed: {e}")
            print(f"[错误] 保存配置失败: {e}")
    
    def _load_window_geometry(self):
        try:
            base_path = get_base_path()
            
            config_path = os.path.join(base_path, self.CONFIG_FILE)
            
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                width = config.get('width')
                height = config.get('height')
                x = config.get('x')
                y = config.get('y')
                
                if width and height:
                    return int(width), int(height), int(x or 0), int(y or 0)
        except Exception as e:
            print(f"[Error] Load window geometry failed: {e}")
            print(f"[错误] 加载窗口配置失败: {e}")
        
        return None
    
    def _save_window_geometry(self, width, height, x, y):
        try:
            base_path = get_base_path()
            
            config_path = os.path.join(base_path, self.CONFIG_FILE)
            
            config = {}
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            config['width'] = width
            config['height'] = height
            config['x'] = x
            config['y'] = y
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            print(f"[Window] Saved geometry: {width}x{height}+{x}+{y}")
            print(f"[窗口] 已保存窗口大小: 宽{width} 高{height} 位置({x},{y})")
        except Exception as e:
            print(f"[Error] Save window geometry failed: {e}")
            print(f"[错误] 保存窗口配置失败: {e}")
    
    def _on_window_configure(self, event):
        if event.widget == self.root:
            if hasattr(self, '_configure_timer'):
                self.root.after_cancel(self._configure_timer)
            
            self._configure_timer = self.root.after(500, self._save_current_geometry)
    
    def _on_window_focus_in(self, event):
        if event.widget == self.root:
            if self.monitor_window and self.monitor_window.winfo_exists():
                self.monitor_window.lift()
                self.monitor_window.attributes('-topmost', True)
    
    def _save_current_geometry(self):
        try:
            geometry = self.root.geometry()
            import re
            match = re.match(r'(\d+)x(\d+)\+(-?\d+)\+(-?\d+)', geometry)
            if match:
                width, height, x, y = match.groups()
                self._save_window_geometry(int(width), int(height), int(x), int(y))
        except Exception as e:
            print(f"[Error] Save current geometry failed: {e}")

    def setup_styles(self):
        style = ttk.Style()
        style.configure("Header.TLabel", 
                       font=("Microsoft YaHei", 10, "bold"),
                       foreground="#2c3e50")
        style.configure("Bold.TLabel", 
                       font=("Microsoft YaHei", 9, "bold"),
                       foreground="#34495e")
        style.configure("Primary.TButton",
                       font=("Microsoft YaHei", 10, "bold"),
                       foreground="white",
                       background="#3498db")
        style.configure("Success.TButton",
                       font=("Microsoft YaHei", 10, "bold"),
                       foreground="white",
                       background="#27ae60")
        style.configure("Frame.TFrame", background="#f8f9fa")

    def create_widgets(self):
        main_container = ttk.Frame(self.root, style="Frame.TFrame")
        main_container.pack(fill="both", expand=True, padx=15, pady=15)
        
        self.create_header(main_container)
        
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill="both", expand=True, pady=10)
        
        self.download_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.download_tab, text="📥 下载模式")
        
        self.literature_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.literature_tab, text="📚 文献下载")
        
        self.browse_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.browse_tab, text="📁 资源管理")
        
        self.pack_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.pack_tab, text="📦 打包模式")
        
        self.localize_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.localize_tab, text="🌐 本地化部署")
        
        self.env_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.env_tab, text="🔧 环境管理")
        
        self.create_download_config_two_columns(self.download_tab)
        self.create_literature_config(self.literature_tab)
        self.create_browse_config(self.browse_tab)
        self.create_pack_config(self.pack_tab)
        self.create_localize_config(self.localize_tab)
        self.create_env_config(self.env_tab)
        
        self.create_status_bar(main_container)
        
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        
        self.root.after(100, self.show_announcement)
        self.root.after(200, self._auto_search_browsers)
        self.root.after(300, self._refresh_env_tab)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _on_tab_changed(self, event):
        selected_tab = self.notebook.index(self.notebook.select())
        tab_name = self.notebook.tab(selected_tab, "text")
        if "资源管理" in tab_name:
            self.refresh_resource_list()

    def create_header(self, parent):
        header_frame = ttk.Frame(parent, style="Frame.TFrame")
        header_frame.pack(fill="x", pady=(0, 15))
        
        title_label = ttk.Label(header_frame, 
                               text="🌐 网页资源离线下载器",
                               font=("Microsoft YaHei", 16, "bold"),
                               foreground="#2c3e50")
        title_label.pack(side="left")
        
        version_label = ttk.Label(header_frame,
                                 text="专业美化版 v2.0",
                                 font=("Microsoft YaHei", 10),
                                 foreground="#7f8c8d")
        version_label.pack(side="left", padx=(10, 0))
        
        manual_btn = ttk.Button(header_frame, text="用户手册", command=self.show_user_manual, width=8)
        manual_btn.pack(side="right", padx=(0, 5))
        
        about_btn = ttk.Button(header_frame, text="关于", command=self.show_about, width=8)
        about_btn.pack(side="right")
        
        self._create_menubar()
    
    def _create_menubar(self):
        pass
    
    def _search_system_browsers(self):
        browsers = []
        
        from browser_manager import is_browser_ready
        internal_ready = is_browser_ready()
        
        if internal_ready:
            browsers.append({
                'id': 'internal',
                'name': '内部浏览器',
                'path': '内置Chromium'
            })
        
        browser_paths = {
            'chrome': [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            ],
            'msedge': [
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            ],
            'firefox': [
                r"C:\Program Files\Mozilla Firefox\firefox.exe",
                r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
            ],
        }
        
        browser_names = {
            'chrome': 'Google Chrome',
            'msedge': 'Microsoft Edge',
            'firefox': 'Firefox'
        }
        
        for browser_id, paths in browser_paths.items():
            for path in paths:
                if os.path.exists(path):
                    browsers.append({
                        'id': browser_id,
                        'name': browser_names[browser_id],
                        'path': path
                    })
                    break
        
        self._detected_browsers = browsers
        self._browser_search_done = True
        return browsers
    
    def show_browser_env_manager(self, auto_start_download=False):
        self.notebook.select(self.env_tab)
        
        if auto_start_download and not self._browser_is_ready:
            self.root.after(100, self._start_env_download)
    
    def create_download_config_two_columns(self, parent):
        columns_container = ttk.Frame(parent)
        columns_container.pack(fill="both", expand=True)
        
        left_column = ttk.Frame(columns_container)
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        right_column = ttk.Frame(columns_container)
        right_column.pack(side="left", fill="both", expand=True, padx=(5, 0))
        
        self.create_left_column_content(left_column)
        self.create_right_column_content(right_column)
    
    def create_left_column_content(self, parent):
        basic_card = self.create_card(parent, "📋 基础配置")
        self.create_basic_config(basic_card)
        
        strategy_card = self.create_card(parent, "⚙️ 下载策略")
        self.create_strategy_config(strategy_card)
        
        resource_card = self.create_card(parent, "📁 资源控制")
        self.create_resource_config(resource_card)
        
        action_card = ttk.LabelFrame(parent, text=" 🚀 操作控制 ", padding=15)
        action_card.pack(fill="x", pady=10)
        
        options_row = ttk.Frame(action_card)
        options_row.pack(fill="x", pady=(0, 10))
        ttk.Checkbutton(options_row, text="📂 下载后自动打开文件夹", 
                       variable=self.auto_open_var).pack(side="left")
        
        start_row = ttk.Frame(action_card)
        start_row.pack(fill="x", pady=(0, 10))
        self.btn_start = ttk.Button(start_row, 
                                   text="🚀 开始下载", 
                                   command=self.start_thread,
                                   style="Success.TButton")
        self.btn_start.pack(side="left", fill="x", expand=True, padx=(0, 5))
        self.btn_stop = ttk.Button(start_row, 
                                  text="⏹️ 停止下载", 
                                  command=self.stop_download,
                                  style="Primary.TButton")
        self.btn_stop.pack(side="left", fill="x", expand=True, padx=(5, 0))
        self.btn_stop.config(state="disabled")
        self.btn_preview = ttk.Button(start_row, 
                                   text="👁️ 爬取预览", 
                                   command=self.preview_crawl,
                                   style="Primary.TButton")
        self.btn_preview.pack(side="left", fill="x", expand=True, padx=(5, 0))
        
        buttons_row = ttk.Frame(action_card)
        buttons_row.pack(fill="x")
        ttk.Button(buttons_row, 
                  text="🗑️ 清空日志", 
                  command=self.clear_log).pack(side="left", fill="x", expand=True, padx=5)
        ttk.Button(buttons_row, 
                  text="📂 打开保存目录", 
                  command=self.open_current_dir).pack(side="left", fill="x", expand=True, padx=5)
        
        if self.trial_remaining > 0 and self.trial_color:
            trial_frame = tk.Frame(action_card, bg="#f8f9fa")
            trial_frame.pack(fill="x", pady=(10, 0))
            
            trial_text = f"📅 剩余 {self.trial_remaining} 次启动"
            trial_label = tk.Label(
                trial_frame,
                text=trial_text,
                font=("Microsoft YaHei", 10, "bold"),
                bg="#f8f9fa",
                fg=self.trial_color
            )
            trial_label.pack(side="left")
            
            unlock_btn = tk.Button(
                trial_frame,
                text="🔓 点我解锁",
                font=("Microsoft YaHei", 9, "bold"),
                bg="#3498db",
                fg="white",
                relief="flat",
                cursor="hand2",
                command=self.show_activation_dialog
            )
            unlock_btn.pack(side="right", padx=10)
            
            if self.trial_remaining <= 5:
                warn_label = tk.Label(
                    trial_frame,
                    text="⚠️ 即将过期，请尽快激活",
                    font=("Microsoft YaHei", 9),
                    bg="#f8f9fa",
                    fg="#e74c3c"
                )
                warn_label.pack(side="right")
    
    def create_right_column_content(self, parent):
        log_card = ttk.LabelFrame(parent, text=" 📝 下载日志 ", padding=10)
        log_card.pack(fill="both", expand=True)
        
        self.log_area = scrolledtext.ScrolledText(log_card, 
                                                 height=40, 
                                                 state='disabled', 
                                                 font=("Consolas", 9), 
                                                 bg="#f8f9fa",
                                                 relief="flat")
        self.log_area.pack(fill="both", expand=True)
        self.log_area.bind("<Button-3>", self.show_log_context_menu)
        self.log_area.bind("<Control-a>", lambda e: self.log_area.tag_add("sel", "1.0", "end"))
        self.log_area.tag_config("success", foreground="#27ae60")
        self.log_area.tag_config("error", foreground="#e74c3c")
        self.log_area.tag_config("warning", foreground="#f39c12")
        self.log_area.tag_config("info", foreground="#3498db")
        
        log_control_frame = ttk.Frame(log_card)
        log_control_frame.pack(fill="x", pady=(5, 0))
        
        self.auto_scroll_var = tk.BooleanVar(value=True)
        auto_scroll_cb = ttk.Checkbutton(log_control_frame, 
                                       text="📜 自动滚动到最新日志", 
                                       variable=self.auto_scroll_var)
        auto_scroll_cb.pack(side="left", padx=5)
        
        clear_log_btn = ttk.Button(log_control_frame, 
                                text="🗑️ 清空日志", 
                                command=self.clear_log,
                                width=15)
        clear_log_btn.pack(side="right", padx=5)

    def create_download_config(self, parent):
        basic_card = self.create_card(parent, "📋 基础配置")
        self.create_basic_config(basic_card)
        strategy_card = self.create_card(parent, "⚙️ 下载策略")
        self.create_strategy_config(strategy_card)
        resource_card = self.create_card(parent, "📁 资源控制")
        self.create_resource_config(resource_card)

    def create_card(self, parent, title):
        card = ttk.LabelFrame(parent, text=f" {title} ", 
                             padding=15,
                             style="Frame.TFrame")
        card.pack(fill="x", pady=8)
        return card

    def create_basic_config(self, parent):
        url_row = ttk.Frame(parent)
        url_row.pack(fill="x", pady=5)
        ttk.Label(url_row, text="目标网址:", style="Bold.TLabel").pack(side="left")
        url_entry = ttk.Entry(url_row, textvariable=self.url_var, width=60, font=("Microsoft YaHei", 9))
        url_entry.pack(side="left", padx=10)
        ttk.Label(url_row, text="(例如: https://example.com)", foreground="#95a5a6").pack(side="left")
        
        path_row = ttk.Frame(parent)
        path_row.pack(fill="x", pady=5)
        ttk.Label(path_row, text="保存路径:", style="Bold.TLabel").pack(side="left")
        self.path_entry = ttk.Entry(path_row, textvariable=self.save_dir_var, width=60, font=("Microsoft YaHei", 9))
        self.path_entry.pack(side="left", padx=10)
        self.browse_btn = ttk.Button(path_row, text="📁 浏览", command=self.select_folder)
        self.browse_btn.pack(side="left", padx=5)
        self.open_dir_btn = ttk.Button(path_row, text="📂 打开", command=self.open_current_dir)
        self.open_dir_btn.pack(side="left", padx=2)
        
        path_mode_frame = ttk.Frame(parent)
        path_mode_frame.pack(fill="x", pady=5)
        ttk.Label(path_mode_frame, text="路径模式:", style="Bold.TLabel").pack(side="left")
        path_mode_options = ttk.Frame(path_mode_frame)
        path_mode_options.pack(side="left", padx=15)
        ttk.Radiobutton(path_mode_options, text="� 相对路径", 
                       variable=self.path_mode_var, value="relative",
                       command=self.update_path_display).pack(side="left", padx=10)
        ttk.Radiobutton(path_mode_options, text="� 绝对路径", 
                       variable=self.path_mode_var, value="absolute",
                       command=self.update_path_display).pack(side="left", padx=10)
        path_info = ttk.Label(path_mode_frame, 
                              text="(相对路径相对于程序所在目录)",
                              foreground="#95a5a6")
        path_info.pack(side="left", padx=10)

    def create_strategy_config(self, parent):
        mode_frame = ttk.Frame(parent)
        mode_frame.pack(fill="x", pady=8)
        ttk.Label(mode_frame, text="下载模式:", style="Bold.TLabel").pack(side="left")
        
        self.download_mode_var = tk.StringVar(value="single")
        
        mode_options = ttk.Frame(mode_frame)
        mode_options.pack(side="left", padx=15)
        ttk.Radiobutton(mode_options, text="📄 单页下载", 
                       variable=self.download_mode_var, value="single",
                       command=self._on_download_mode_change).pack(side="left", padx=10)
        ttk.Radiobutton(mode_options, text="🕷️ 爬取下载", 
                       variable=self.download_mode_var, value="crawl",
                       command=self._on_download_mode_change).pack(side="left", padx=10)
        
        ttk.Button(mode_options, text="📚 批量下载", command=self._open_batch_download_window).pack(side="left", padx=15)
        
        settings_btn = ttk.Button(mode_frame, text="⚙️ 设置", command=self._open_download_settings)
        settings_btn.pack(side="left", padx=20)
        
        self._mode_info_label = ttk.Label(mode_frame, text="", foreground="#7f8c8d", font=("Microsoft YaHei", 9))
        self._mode_info_label.pack(side="left", padx=10)
        
        pages_frame = ttk.Frame(parent)
        pages_frame.pack(fill="x", pady=8)
        ttk.Label(pages_frame, text="爬取页数:", style="Bold.TLabel").pack(side="left")
        pages_control = ttk.Frame(pages_frame)
        pages_control.pack(side="left", padx=15)
        self.max_pages_var = tk.IntVar(value=-1)
        self.radio_unlimited = ttk.Radiobutton(pages_control, text="♾️ 无限页", 
                       variable=self.max_pages_var, value=-1)
        self.radio_unlimited.pack(side="left", padx=8)
        self.radio_10 = ttk.Radiobutton(pages_control, text="📄 10页", 
                       variable=self.max_pages_var, value=10)
        self.radio_10.pack(side="left", padx=8)
        self.radio_50 = ttk.Radiobutton(pages_control, text="📄 50页", 
                       variable=self.max_pages_var, value=50)
        self.radio_50.pack(side="left", padx=8)
        self.radio_100 = ttk.Radiobutton(pages_control, text="📄 100页", 
                       variable=self.max_pages_var, value=100)
        self.radio_100.pack(side="left", padx=8)
        self.radio_custom = ttk.Radiobutton(pages_control, text="⚙️ 自定义", 
                       variable=self.max_pages_var, value=0)
        self.radio_custom.pack(side="left", padx=8)
        self.custom_pages_var = tk.IntVar(value=100)
        self.custom_pages_spin = ttk.Spinbox(pages_control, from_=1, to=1000, 
                                          textvariable=self.custom_pages_var, 
                                          width=4,
                                          state="disabled")
        self.custom_pages_spin.pack(side="left", padx=5)
        self.label_pages = ttk.Label(pages_control, text="页")
        self.label_pages.pack(side="left")
        self.max_pages_var.trace('w', self.update_pages_state)
        
        self._on_download_mode_change()
    
    def _on_download_mode_change(self):
        mode = self.download_mode_var.get()
        if mode == "single":
            self._mode_info_label.config(text="下载单个网页")
            state = 'disabled'
        else:
            self._mode_info_label.config(text="爬取整站内容")
            state = 'normal'
        
        try:
            self.radio_unlimited.config(state=state)
            self.radio_10.config(state=state)
            self.radio_50.config(state=state)
            self.radio_100.config(state=state)
            self.radio_custom.config(state=state)
            if state == 'disabled':
                self.custom_pages_spin.config(state='disabled')
            else:
                self.update_pages_state()
        except:
            pass
    
    def _open_batch_download_window(self):
        batch_window = tk.Toplevel(self.root)
        batch_window.title("📚 批量下载")
        batch_window.geometry("900x650")
        batch_window.resizable(True, True)
        batch_window.transient(self.root)
        batch_window.grab_set()
        
        batch_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 900) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 650) // 2
        batch_window.geometry(f"+{x}+{y}")
        
        main_frame = ttk.Frame(batch_window, padding=15)
        main_frame.pack(fill="both", expand=True)
        
        left_frame = ttk.Frame(main_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        right_frame = ttk.Frame(main_frame)
        right_frame.pack(side="left", fill="both", expand=True)
        
        url_card = ttk.LabelFrame(left_frame, text=" 📝 待下载网址列表 ", padding=10)
        url_card.pack(fill="both", expand=True, pady=5)
        
        ttk.Label(url_card, text="每行一个网址，使用核心下载器批量下载：", 
                 font=("Microsoft YaHei", 9, "bold")).pack(anchor="w")
        
        list_frame = ttk.Frame(url_card)
        list_frame.pack(fill="both", expand=True, pady=8)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        self._batch_url_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            selectmode=tk.EXTENDED,
            font=("Microsoft YaHei", 9),
            bg="#f8f9fa",
            activestyle="none"
        )
        self._batch_url_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self._batch_url_listbox.yview)
        
        self._batch_url_listbox.bind('<Delete>', lambda e: self._remove_batch_urls())
        
        btn_frame = ttk.Frame(url_card)
        btn_frame.pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="📋 从剪贴板添加", command=self._add_batch_urls_from_clipboard, width=14).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="🗑️ 删除选中", command=self._remove_batch_urls, width=12).pack(side="left", padx=2)
        ttk.Button(btn_frame, text="🧹 清空列表", command=self._clear_batch_urls, width=12).pack(side="left", padx=2)
        
        output_card = ttk.LabelFrame(left_frame, text=" 📁 输出设置 ", padding=10)
        output_card.pack(fill="x", pady=5)
        
        output_row = ttk.Frame(output_card)
        output_row.pack(fill="x", pady=3)
        ttk.Label(output_row, text="保存目录:", font=("Microsoft YaHei", 9, "bold")).pack(side="left")
        self._batch_output_var = tk.StringVar(value="batch_downloads")
        ttk.Entry(output_row, textvariable=self._batch_output_var, width=35).pack(side="left", padx=8)
        ttk.Button(output_row, text="📂", command=self._select_batch_output_dir, width=4).pack(side="left")
        
        mode_row = ttk.Frame(output_card)
        mode_row.pack(fill="x", pady=3)
        ttk.Label(mode_row, text="输出模式:", font=("Microsoft YaHei", 9, "bold")).pack(side="left")
        self._batch_output_mode_var = tk.StringVar(value="embedded")
        ttk.Radiobutton(mode_row, text="📄 单独HTML(内嵌)", variable=self._batch_output_mode_var, value="embedded").pack(side="left", padx=5)
        ttk.Radiobutton(mode_row, text="📦 资源外置(CSS/JS)", variable=self._batch_output_mode_var, value="external").pack(side="left", padx=5)
        
        structure_row = ttk.Frame(output_card)
        structure_row.pack(fill="x", pady=3)
        ttk.Label(structure_row, text="描述形式:", font=("Microsoft YaHei", 9, "bold")).pack(side="left")
        self._batch_structure_var = tk.StringVar(value="toc")
        ttk.Radiobutton(structure_row, text="📑 目录模式(注入目录)", variable=self._batch_structure_var, value="toc").pack(side="left", padx=5)
        ttk.Radiobutton(structure_row, text="🌐 网站原有结构", variable=self._batch_structure_var, value="original").pack(side="left", padx=5)
        
        dedup_row = ttk.Frame(output_card)
        dedup_row.pack(fill="x", pady=3)
        self._batch_dedup_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(dedup_row, text="🔄 资源去重(相同CSS/JS不重复下载)", 
                       variable=self._batch_dedup_var).pack(side="left")
        
        action_card = ttk.LabelFrame(left_frame, text=" 🚀 操作控制 ", padding=10)
        action_card.pack(fill="x", pady=5)
        
        self._batch_download_btn = ttk.Button(action_card, text="🚀 开始下载", 
                                             command=self._start_batch_download_core, width=15)
        self._batch_download_btn.pack(side="left", padx=5)
        
        self._batch_stop_btn = ttk.Button(action_card, text="⏹️ 停止", 
                                         command=self._stop_batch_download_core, width=10)
        self._batch_stop_btn.pack(side="left", padx=5)
        self._batch_stop_btn.config(state="disabled")
        
        ttk.Button(action_card, text="📂 打开目录", command=self._open_batch_output_dir, width=12).pack(side="left", padx=5)
        
        log_card = ttk.LabelFrame(right_frame, text=" 📝 下载日志 ", padding=10)
        log_card.pack(fill="both", expand=True, pady=5)
        
        self._batch_log_area = scrolledtext.ScrolledText(log_card, height=25, 
                                                         state='disabled',
                                                         font=("Consolas", 9),
                                                         bg="#f8f9fa")
        self._batch_log_area.pack(fill="both", expand=True)
        self._batch_log_area.tag_config("success", foreground="#27ae60")
        self._batch_log_area.tag_config("error", foreground="#e74c3c")
        self._batch_log_area.tag_config("warning", foreground="#f39c12")
        self._batch_log_area.tag_config("info", foreground="#3498db")
        
        info_card = ttk.LabelFrame(right_frame, text=" ℹ️ 使用说明 ", padding=10)
        info_card.pack(fill="x", pady=5)
        
        info_text = """• 输出模式：单独HTML(内嵌资源) 或 资源外置(CSS/JS单独存放)
• 目录模式：注入悬浮目录，方便导航
• 网站原有结构：保持原有链接关系，已下载内容自动连接
• 资源去重：相同CSS/JS只下载一次，节省空间"""
        
        ttk.Label(info_card, text=info_text, font=("Microsoft YaHei", 9), 
                 foreground="#7f8c8d", justify="left").pack(anchor="w")
        
        self._batch_should_stop = False
        self._batch_resource_cache = {}
    
    def _add_batch_urls_from_clipboard(self):
        try:
            clipboard = self.root.clipboard_get()
            urls = [url.strip() for url in clipboard.split('\n') if url.strip()]
            for url in urls:
                if url.startswith('http'):
                    self._batch_url_listbox.insert("end", url)
        except:
            pass
    
    def _remove_batch_urls(self):
        for i in reversed(self._batch_url_listbox.curselection()):
            self._batch_url_listbox.delete(i)
    
    def _clear_batch_urls(self):
        self._batch_url_listbox.delete(0, "end")
    
    def _select_batch_output_dir(self):
        folder = filedialog.askdirectory()
        if folder:
            self._batch_output_var.set(folder)
    
    def _batch_log(self, msg, tag="info"):
        self._batch_log_area.config(state='normal')
        timestamp = time.strftime("%H:%M:%S")
        self._batch_log_area.insert("end", f"[{timestamp}] {msg}\n", tag)
        self._batch_log_area.config(state='disabled')
        self._batch_log_area.see("end")
    
    def _start_batch_download_core(self):
        urls = list(self._batch_url_listbox.get(0, "end"))
        if not urls:
            messagebox.showwarning("警告", "请先添加网址！")
            return
        
        self._batch_download_btn.config(state="disabled")
        self._batch_stop_btn.config(state="normal")
        self._batch_should_stop = False
        self._batch_resource_cache = {}
        
        self._batch_log(f"开始批量下载 {len(urls)} 个页面...", "info")
        
        threading.Thread(target=self._run_batch_download_core, args=(urls,), daemon=True).start()
    
    def _run_batch_download_core(self, urls):
        try:
            output_dir = self._batch_output_var.get()
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            output_mode = self._batch_output_mode_var.get()
            structure_mode = self._batch_structure_var.get()
            dedup_enabled = self._batch_dedup_var.get()
            
            resources_dir = os.path.join(output_dir, "resources")
            if output_mode == "external" and not os.path.exists(resources_dir):
                os.makedirs(resources_dir)
            
            success_count = 0
            fail_count = 0
            downloaded_files = []
            
            for i, url in enumerate(urls):
                if self._batch_should_stop:
                    self.root.after(0, lambda: self._batch_log("下载已停止", "warning"))
                    break
                
                self.root.after(0, lambda idx=i+1, total=len(urls), u=url: 
                               self._batch_log(f"[{idx}/{total}] 开始: {u[:50]}...", "info"))
                
                try:
                    page_dir = output_dir
                    
                    params = {
                        'url': url,
                        'output_dir': page_dir,
                        'depth': 0,
                        'mode': 'full',
                        'convert_img': False,
                        'target_fmt': 'PNG',
                        'filter_img': True,
                        'filter_video': True,
                        'max_pages': 1,
                        'external_resources': output_mode == "external",
                        'resources_dir': resources_dir if output_mode == "external" else None,
                        'resource_cache': self._batch_resource_cache if dedup_enabled else None,
                        'dedup_enabled': dedup_enabled
                    }
                    
                    downloader = CoreDownloader(self, params)
                    result = downloader.start()
                    
                    if result:
                        downloaded_files.append(result)
                        success_count += 1
                        self.root.after(0, lambda idx=i+1, total=len(urls): 
                                       self._batch_log(f"[{idx}/{total}] ✅ 完成", "success"))
                    else:
                        fail_count += 1
                        self.root.after(0, lambda idx=i+1, total=len(urls): 
                                       self._batch_log(f"[{idx}/{total}] ⚠️ 内容为空，可能存在反爬虫机制", "warning"))
                    
                except Exception as e:
                    fail_count += 1
                    self.root.after(0, lambda idx=i+1, total=len(urls), err=str(e): 
                                   self._batch_log(f"[{idx}/{total}] ❌ 失败: {err}", "error"))
                
                time.sleep(1)
            
            if structure_mode == "toc" and downloaded_files:
                self.root.after(0, lambda: self._batch_log("正在生成目录...", "info"))
                self._generate_batch_toc(output_dir, downloaded_files)
            
            self.root.after(0, lambda: self._batch_log(
                f"\n下载完成！成功: {success_count}, 失败: {fail_count}", 
                "success" if fail_count == 0 else "warning"))
            
            if fail_count > 0 and success_count == 0:
                self.root.after(0, lambda: messagebox.showwarning(
                    "下载失败", 
                    "该网站可能应用了反爬虫机制，系统未能获取到有效内容。\n\n建议使用「文献下载」功能重试。"))
            elif fail_count > 0:
                self.root.after(0, lambda: messagebox.showwarning(
                    "部分下载失败", 
                    f"有 {fail_count} 个页面下载失败，可能存在反爬虫机制。\n\n建议使用「文献下载」功能下载失败的页面。"))
            
        except Exception as e:
            self.root.after(0, lambda: self._batch_log(f"错误: {str(e)}", "error"))
        finally:
            self.root.after(0, lambda: self._batch_download_btn.config(state="normal"))
            self.root.after(0, lambda: self._batch_stop_btn.config(state="disabled"))
    
    def _generate_batch_toc(self, output_dir, downloaded_files):
        try:
            from bs4 import BeautifulSoup
            from urllib.parse import urlparse
            
            site_names = {
                'zhihu.com': '知乎',
                'csdn.net': 'CSDN',
                'juejin.cn': '掘金',
                'jianshu.com': '简书',
                'bilibili.com': '哔哩哔哩',
                'cnblogs.com': '博客园',
                'segmentfault.com': 'SegmentFault',
                'stackoverflow.com': 'Stack Overflow',
                'github.com': 'GitHub',
                'gitee.com': 'Gitee',
                'weixin.qq.com': '微信公众号',
                'mp.weixin.qq.com': '微信公众号',
                'baike.baidu.com': '百度百科',
                'baidu.com': '百度',
            }
            
            items_html = ""
            sources_set = set()
            
            for i, filepath in enumerate(downloaded_files):
                filename = os.path.basename(filepath)
                title = os.path.splitext(filename)[0]
                source = ""
                
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read(50000)
                    
                    soup = BeautifulSoup(content, 'lxml')
                    
                    og_title = soup.find('meta', property='og:title')
                    if og_title and og_title.get('content'):
                        title = og_title['content'].strip()
                    
                    if not title or title == os.path.splitext(filename)[0]:
                        if soup.title and soup.title.string:
                            title = soup.title.string.strip()
                            for sep in ['_', '-', '|', '·', '–']:
                                if sep in title:
                                    parts = title.split(sep)
                                    title = parts[0].strip()
                                    break
                    
                    title = re.sub(r'[\\/*?:"<>|]', '_', title)
                    title = re.sub(r'\s+', ' ', title)
                    if len(title) > 60:
                        title = title[:60] + '...'
                    
                    canonical = soup.find('link', rel='canonical')
                    if canonical and canonical.get('href'):
                        domain = urlparse(canonical['href']).netloc
                        domain = domain.replace('www.', '')
                        for site_domain, site_name in site_names.items():
                            if site_domain in domain:
                                source = site_name
                                break
                        if not source:
                            source = domain
                    
                    if not source:
                        og_url = soup.find('meta', property='og:url')
                        if og_url and og_url.get('content'):
                            domain = urlparse(og_url['content']).netloc
                            domain = domain.replace('www.', '')
                            for site_domain, site_name in site_names.items():
                                if site_domain in domain:
                                    source = site_name
                                    break
                            if not source:
                                source = domain
                    
                    if source:
                        sources_set.add(source)
                        
                except:
                    pass
                
                rel_path = filename
                source_badge = f'<span class="source">{source}</span>' if source else ''
                items_html += f'        <div class="item"><span class="num">{i+1}.</span><a href="{rel_path}">{title}</a>{source_badge}</div>\n'
            
            sources_str = "、".join(sorted(sources_set)) if sources_set else "多个网站"
            
            toc_html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>下载目录</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: "Microsoft YaHei", sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; padding: 20px; }}
        .container {{ max-width: 900px; margin: 0 auto; background: white; border-radius: 15px; padding: 30px; box-shadow: 0 10px 40px rgba(0,0,0,0.2); }}
        h1 {{ color: #2c3e50; margin-bottom: 10px; font-size: 24px; }}
        .meta {{ color: #7f8c8d; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 2px solid #3498db; }}
        .meta span {{ margin-right: 15px; }}
        .item {{ padding: 15px; border-bottom: 1px solid #eee; display: flex; align-items: center; transition: all 0.2s; }}
        .item:hover {{ background: #f8f9fa; transform: translateX(5px); }}
        .item a {{ color: #2c3e50; text-decoration: none; flex: 1; font-size: 14px; }}
        .item a:hover {{ color: #3498db; }}
        .num {{ color: #3498db; margin-right: 12px; min-width: 35px; font-weight: bold; }}
        .source {{ background: #3498db; color: white; padding: 2px 8px; border-radius: 10px; font-size: 11px; margin-left: 10px; }}
        .footer {{ margin-top: 20px; padding-top: 15px; border-top: 1px solid #eee; color: #95a5a6; font-size: 12px; text-align: center; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 下载目录</h1>
        <div class="meta">
            <span>📄 共 {len(downloaded_files)} 个页面</span>
            <span>🌐 来源：{sources_str}</span>
        </div>
{items_html}        <div class="footer">由离线网页下载器生成 · {time.strftime("%Y-%m-%d %H:%M")}</div>
    </div>
</body>
</html>'''
            
            toc_path = os.path.join(output_dir, "index.html")
            with open(toc_path, 'w', encoding='utf-8') as f:
                f.write(toc_html)
            
            self.root.after(0, lambda: self._batch_log(f"目录已生成: index.html", "success"))
        except Exception as e:
            self.root.after(0, lambda: self._batch_log(f"生成目录失败: {e}", "error"))
    
    def _stop_batch_download_core(self):
        self._batch_should_stop = True
        self._batch_log("正在停止...", "warning")
    
    def _open_batch_output_dir(self):
        output_dir = self._batch_output_var.get()
        if os.path.exists(output_dir):
            self.open_file_explorer(output_dir)
        else:
            messagebox.showinfo("提示", "目录不存在，请先下载")
    
    def _open_download_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("下载设置")
        settings_window.geometry("600x500")
        settings_window.resizable(False, False)
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        settings_window.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - 600) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 500) // 2
        settings_window.geometry(f"+{x}+{y}")
        
        main_frame = ttk.Frame(settings_window, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        content_frame = ttk.LabelFrame(main_frame, text=" 📋 下载内容 ", padding=15)
        content_frame.pack(fill="x", pady=10)
        
        content_row = ttk.Frame(content_frame)
        content_row.pack(fill="x")
        ttk.Label(content_row, text="下载类型:", style="Bold.TLabel").pack(side="left")
        content_options = ttk.Frame(content_row)
        content_options.pack(side="left", padx=15)
        ttk.Radiobutton(content_options, text="🌐 整页离线 (HTML+资源)", 
                       variable=self.mode_var, value="full").pack(side="left", padx=10)
        ttk.Radiobutton(content_options, text="📁 仅提取素材", 
                       variable=self.mode_var, value="media_only").pack(side="left", padx=10)
        ttk.Radiobutton(content_options, text="📝 纯文本提取", 
                       variable=self.mode_var, value="text_only").pack(side="left", padx=10)
        
        anti_frame = ttk.LabelFrame(main_frame, text=" 🛡️ 反爬设置 ", padding=15)
        anti_frame.pack(fill="x", pady=10)
        
        webview_row = ttk.Frame(anti_frame)
        webview_row.pack(fill="x", pady=5)
        ttk.Label(webview_row, text="反爬模式:", style="Bold.TLabel").pack(side="left")
        self._settings_use_webview = tk.BooleanVar(value=self.use_webview_var.get())
        ttk.Checkbutton(webview_row, text="🌐 使用浏览器绕过反爬 (支持登录)", 
                       variable=self._settings_use_webview).pack(side="left", padx=15)
        ttk.Label(webview_row, text="(适用于知乎/CSDN等)", 
                 foreground="#95a5a6").pack(side="left", padx=5)
        
        device_row = ttk.Frame(anti_frame)
        device_row.pack(fill="x", pady=5)
        ttk.Label(device_row, text="设备标识:", style="Bold.TLabel").pack(side="left")
        device_options = ttk.Frame(device_row)
        device_options.pack(side="left", padx=15)
        ttk.Radiobutton(device_options, text="💻 电脑访问", 
                       variable=self.device_var, value="desktop").pack(side="left", padx=10)
        ttk.Radiobutton(device_options, text="📱 手机访问", 
                       variable=self.device_var, value="mobile").pack(side="left", padx=10)
        
        wait_frame = ttk.LabelFrame(main_frame, text=" ⏱️ 等待时间 ", padding=15)
        wait_frame.pack(fill="x", pady=10)
        
        wait_control = ttk.Frame(wait_frame)
        wait_control.pack(fill="x")
        ttk.Radiobutton(wait_control, text="⚡ 不等待", 
                       variable=self.wait_mode_var, value="no_wait").pack(side="left", padx=8)
        ttk.Radiobutton(wait_control, text="⏱️ 等待3秒", 
                       variable=self.wait_mode_var, value="wait_3").pack(side="left", padx=8)
        ttk.Radiobutton(wait_control, text="⏱️ 等待5秒", 
                       variable=self.wait_mode_var, value="wait_5").pack(side="left", padx=8)
        ttk.Radiobutton(wait_control, text="⏱️ 等待10秒", 
                       variable=self.wait_mode_var, value="wait_10").pack(side="left", padx=8)
        ttk.Radiobutton(wait_control, text="⚙️ 自定义", 
                       variable=self.wait_mode_var, value="custom").pack(side="left", padx=8)
        self._settings_custom_wait_spin = ttk.Spinbox(wait_control, from_=1, to=60, 
                                         textvariable=self.custom_wait_var, 
                                         width=3)
        self._settings_custom_wait_spin.pack(side="left", padx=5)
        ttk.Label(wait_control, text="秒").pack(side="left")
        
        crawl_frame = ttk.LabelFrame(main_frame, text=" 🕷️ 爬取设置 (仅爬取模式) ", padding=15)
        crawl_frame.pack(fill="x", pady=10)
        
        depth_row = ttk.Frame(crawl_frame)
        depth_row.pack(fill="x", pady=5)
        ttk.Label(depth_row, text="爬取深度:", style="Bold.TLabel").pack(side="left")
        depth_control = ttk.Frame(depth_row)
        depth_control.pack(side="left", padx=15)
        ttk.Radiobutton(depth_control, text="📄 仅本页", 
                       variable=self.depth_mode_var, value="page_only",
                       command=self.update_depth_value).pack(side="left", padx=8)
        ttk.Radiobutton(depth_control, text="📄+📄 本页+下页", 
                       variable=self.depth_mode_var, value="page_next",
                       command=self.update_depth_value).pack(side="left", padx=8)
        ttk.Radiobutton(depth_control, text="📄+📄+📄 本页+下2页", 
                       variable=self.depth_mode_var, value="page_next2",
                       command=self.update_depth_value).pack(side="left", padx=8)
        ttk.Radiobutton(depth_control, text="⚙️ 自定义", 
                       variable=self.depth_mode_var, value="custom",
                       command=self.update_depth_value).pack(side="left", padx=8)
        self._settings_custom_depth_spin = ttk.Spinbox(depth_control, from_=0, to=10, 
                                            textvariable=self.custom_depth_var, 
                                            width=3)
        self._settings_custom_depth_spin.pack(side="left", padx=5)
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=20)
        
        def apply_settings():
            self.use_webview_var.set(self._settings_use_webview.get())
            settings_window.destroy()
        
        ttk.Button(btn_frame, text="✅ 确定", command=apply_settings, style="Success.TButton").pack(side="right", padx=10)
        ttk.Button(btn_frame, text="❌ 取消", command=settings_window.destroy).pack(side="right", padx=10)

    def create_resource_config(self, parent):
        resource_frame = ttk.Frame(parent)
        resource_frame.pack(fill="x", pady=8)
        ttk.Label(resource_frame, text="下载内容:", style="Bold.TLabel").pack(side="left")
        resource_options = ttk.Frame(resource_frame)
        resource_options.pack(side="left", padx=15)
        ttk.Checkbutton(resource_options, text="🖼️ 图片", 
                       variable=self.filter_img_var).pack(side="left", padx=15)
        ttk.Checkbutton(resource_options, text="🎬 视频", 
                       variable=self.filter_video_var).pack(side="left", padx=15)
        
        convert_frame = ttk.Frame(parent)
        convert_frame.pack(fill="x", pady=8)
        ttk.Label(convert_frame, text="图片处理:", style="Bold.TLabel").pack(side="left")
        convert_options = ttk.Frame(convert_frame)
        convert_options.pack(side="left", padx=15)
        ttk.Checkbutton(convert_options, text="格式转换", 
                       variable=self.convert_img_var).pack(side="left")
        format_combo = ttk.Combobox(convert_options, 
                                   textvariable=self.target_fmt_var, 
                                   values=["PNG", "JPG"], 
                                   width=6, state="readonly")
        format_combo.pack(side="left", padx=5)
        
        localize_frame = ttk.Frame(parent)
        localize_frame.pack(fill="x", pady=8)
        ttk.Label(localize_frame, text="下载后处理:", style="Bold.TLabel").pack(side="left")
        localize_options = ttk.Frame(localize_frame)
        localize_options.pack(side="left", padx=15)
        ttk.Checkbutton(localize_options, text="🌐 自动本地化部署", 
                       variable=self.auto_localize_var).pack(side="left")
    
    def create_localize_config(self, parent):
        mode_card = ttk.LabelFrame(parent, text=" 🎯 部署模式 ", padding=15)
        mode_card.pack(fill="x", pady=10)
        
        mode_row = ttk.Frame(mode_card)
        mode_row.pack(fill="x")
        ttk.Label(mode_row, text="模式选择:", style="Bold.TLabel").pack(side="left")
        
        self.localize_mode_var = tk.StringVar(value="single")
        
        mode_options = ttk.Frame(mode_row)
        mode_options.pack(side="left", padx=15)
        ttk.Radiobutton(mode_options, text="📄 单HTML模式", 
                       variable=self.localize_mode_var, value="single",
                       command=self._update_localize_mode_ui).pack(side="left", padx=10)
        ttk.Radiobutton(mode_options, text="📚 目录模式（多选）", 
                       variable=self.localize_mode_var, value="directory",
                       command=self._update_localize_mode_ui).pack(side="left", padx=10)
        
        self._localize_single_frame = ttk.LabelFrame(parent, text=" 📁 网站目录（单选） ", padding=15)
        
        website_row = ttk.Frame(self._localize_single_frame)
        website_row.pack(fill="x")
        ttk.Label(website_row, text="网站目录:", style="Bold.TLabel").pack(side="left")
        website_entry = ttk.Entry(website_row, textvariable=self.localize_website_dir, width=60, font=("Microsoft YaHei", 9))
        website_entry.pack(side="left", padx=10, fill="x", expand=True)
        browse_btn = ttk.Button(website_row, text="📁 浏览", command=self.select_localize_website_dir)
        browse_btn.pack(side="left", padx=5)
        auto_detect_btn = ttk.Button(website_row, text="🔍 自动检测", command=self.auto_detect_localize_website_dir)
        auto_detect_btn.pack(side="left", padx=5)
        
        self._localize_multi_frame = ttk.LabelFrame(parent, text=" 📁 网站目录（多选） ", padding=15)
        
        multi_btn_row = ttk.Frame(self._localize_multi_frame)
        multi_btn_row.pack(fill="x", pady=(0, 10))
        ttk.Button(multi_btn_row, text="➕ 添加目录", command=self._add_localize_dir).pack(side="left", padx=5)
        ttk.Button(multi_btn_row, text="➖ 移除选中", command=self._remove_localize_dir).pack(side="left", padx=5)
        ttk.Button(multi_btn_row, text="🧹 清空列表", command=self._clear_localize_dirs).pack(side="left", padx=5)
        
        list_frame = ttk.Frame(self._localize_multi_frame)
        list_frame.pack(fill="both", expand=True)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.localize_dir_listbox = tk.Listbox(list_frame, height=6, yscrollcommand=scrollbar.set,
                                                selectmode=tk.EXTENDED, font=("Microsoft YaHei", 9))
        self.localize_dir_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.localize_dir_listbox.yview)
        
        self._localize_single_frame.pack(fill="x", pady=10)
        
        info_card = ttk.LabelFrame(parent, text=" ℹ️ 功能说明 ", padding=15)
        info_card.pack(fill="x", pady=10)
        self._localize_info_label = ttk.Label(info_card, text="", foreground="#7f8c8d", font=("Microsoft YaHei", 9))
        self._localize_info_label.pack(anchor="w")
        
        action_card = ttk.LabelFrame(parent, text=" 🚀 操作 ", padding=15)
        action_card.pack(fill="x", pady=10)
        button_row = ttk.Frame(action_card)
        button_row.pack(fill="x")
        self._localize_btn = ttk.Button(button_row, text="🌐 开始本地化部署", command=self.start_localize, style="Success.TButton")
        self._localize_btn.pack(side="left", padx=5)
        
        log_card = ttk.LabelFrame(parent, text=" 📝 本地化日志 ", padding=10)
        log_card.pack(fill="both", expand=True, pady=10)
        self.localize_log_area = scrolledtext.ScrolledText(log_card, height=15, state='disabled', font=("Consolas", 9), bg="#f8f9fa", relief="flat")
        self.localize_log_area.pack(fill="both", expand=True)
        self.localize_log_area.bind("<Button-3>", self.show_localize_log_context_menu)
        self.localize_log_area.tag_config("success", foreground="#27ae60")
        self.localize_log_area.tag_config("error", foreground="#e74c3c")
        self.localize_log_area.tag_config("warning", foreground="#f39c12")
        self.localize_log_area.tag_config("info", foreground="#3498db")
        
        self._update_localize_mode_ui()
    
    def _update_localize_mode_ui(self):
        mode = self.localize_mode_var.get()
        
        self._localize_single_frame.pack_forget()
        self._localize_multi_frame.pack_forget()
        
        if mode == "single":
            self._localize_single_frame.pack(fill="x", pady=10, before=self._localize_info_label.master)
            self._localize_info_label.config(text="""单HTML模式：将所有资源（图片、CSS、背景图）内嵌到HTML文件中。
优点：生成单文件，可直接用浏览器打开，无需服务器
⚠️ 注意：文件体积会变大，但便于分享和存档""")
            self._localize_btn.config(text="🌐 开始本地化部署")
        else:
            self._localize_multi_frame.pack(fill="x", pady=10, before=self._localize_info_label.master)
            self._localize_info_label.config(text="""目录模式：将多个网站合并成一个带目录的合集。
生成一个大目录页面 + 多个子页面，支持悬浮目录导航
适合整理多个相关网页，便于统一浏览和管理""")
            self._localize_btn.config(text="📚 生成目录合集")
    
    def _add_localize_dir(self):
        folder = filedialog.askdirectory(title="选择网站目录")
        if folder and folder not in self.localize_dir_listbox.get(0, tk.END):
            self.localize_dir_listbox.insert(tk.END, folder)
    
    def _remove_localize_dir(self):
        selection = self.localize_dir_listbox.curselection()
        for i in reversed(selection):
            self.localize_dir_listbox.delete(i)
    
    def _clear_localize_dirs(self):
        self.localize_dir_listbox.delete(0, tk.END)
    
    def create_env_config(self, parent):
        left_frame = ttk.Frame(parent)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        right_frame = ttk.Frame(parent, width=280)
        right_frame.pack(side="left", fill="y", padx=(5, 0))
        right_frame.pack_propagate(False)
        
        browser_card = ttk.LabelFrame(left_frame, text=" 🌐 浏览器环境 ", padding=10)
        browser_card.pack(fill="x", pady=5)
        
        from browser_manager import is_browser_ready, check_browser_integrity, get_chromium_path, get_browsers_path
        
        self._browser_is_ready = is_browser_ready()
        is_valid, status_msg = check_browser_integrity() if self._browser_is_ready else (False, "未安装")
        chromium_path = get_chromium_path()
        browsers_path = get_browsers_path()
        
        status_icon = "✅" if self._browser_is_ready else "❌"
        status_color = "#27ae60" if self._browser_is_ready else "#e74c3c"
        
        self._browser_status_label = ttk.Label(browser_card, text=f"内置浏览器: {status_icon} {status_msg}", 
                                               foreground=status_color, font=("Microsoft YaHei", 10, "bold"))
        self._browser_status_label.pack(anchor="w")
        
        ttk.Label(browser_card, text=f"路径: {chromium_path or '未安装'}", foreground="#7f8c8d", 
                 font=("Microsoft YaHei", 8), wraplength=350).pack(anchor="w", pady=(5, 0))
        
        self._env_download_status_var = tk.StringVar(value="就绪")
        self._env_download_progress_var = tk.StringVar(value="")
        
        ttk.Label(browser_card, textvariable=self._env_download_status_var, 
                 font=("Microsoft YaHei", 9, "bold")).pack(anchor="w", pady=(5, 0))
        ttk.Label(browser_card, textvariable=self._env_download_progress_var, 
                 foreground="#3498db", font=("Microsoft YaHei", 8), wraplength=350).pack(anchor="w")
        
        btn_frame = ttk.Frame(browser_card)
        btn_frame.pack(fill="x", pady=(8, 0))
        
        self._env_download_btn = ttk.Button(btn_frame, text="📥 下载浏览器", 
                                            command=self._start_env_download, width=12)
        self._env_download_btn.pack(side="left", padx=(0, 5))
        
        ttk.Button(btn_frame, text="🗑️卸载浏览器", command=self._clear_env_browser, width=12).pack(side="left", padx=(0, 5))
        ttk.Button(btn_frame, text="🔄刷新", command=self._refresh_browser_status, width=8).pack(side="left")
        
        system_browser_card = ttk.LabelFrame(left_frame, text=" 🖥️ 系统浏览器 ", padding=10)
        system_browser_card.pack(fill="x", pady=5)
        
        ttk.Label(system_browser_card, text="浏览器选择:", font=("Microsoft YaHei", 9, "bold")).pack(anchor="w")
        
        browser_select_frame = ttk.Frame(system_browser_card)
        browser_select_frame.pack(fill="x", pady=5)
        
        ttk.Radiobutton(browser_select_frame, text="自动选择", variable=self.browser_type_var, 
                       value="auto", command=self._on_browser_type_change).pack(side="left", padx=(0, 10))
        ttk.Radiobutton(browser_select_frame, text="内置浏览器", variable=self.browser_type_var, 
                       value="internal", command=self._on_browser_type_change).pack(side="left", padx=(0, 10))
        
        self._detected_browsers_label = ttk.Label(system_browser_card, text="正在检测系统浏览器...", 
                                                  foreground="#7f8c8d", font=("Microsoft YaHei", 8))
        self._detected_browsers_label.pack(anchor="w")
        
        self._browser_options_frame = ttk.Frame(system_browser_card)
        self._browser_options_frame.pack(fill="x", pady=5)
        
        search_btn_frame = ttk.Frame(system_browser_card)
        search_btn_frame.pack(fill="x")
        ttk.Button(search_btn_frame, text="🔍 搜索浏览器", command=self._search_and_show_browsers, width=14).pack(side="left")
        
        data_card = ttk.LabelFrame(left_frame, text=" 📁 浏览器数据 ", padding=10)
        data_card.pack(fill="x", pady=5)
        
        if is_frozen():
            browser_data_dir = os.path.join(get_base_path(), "browser_data")
        else:
            browser_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "browser_data")
        
        self._browser_data_dir_label = ttk.Label(data_card, text=f"目录: {browser_data_dir}", foreground="#3498db", 
                 font=("Microsoft YaHei", 8), wraplength=350)
        self._browser_data_dir_label.pack(anchor="w")
        self._browser_data_info_label = ttk.Label(data_card, text="（登录状态、Cookies、缓存、浏览记录）", 
                 foreground="#7f8c8d", font=("Microsoft YaHei", 8))
        self._browser_data_info_label.pack(anchor="w")
        
        data_btn_frame = ttk.Frame(data_card)
        data_btn_frame.pack(fill="x", pady=(8, 0))
        ttk.Button(data_btn_frame, text="📂 打开目录", 
                  command=lambda: self._open_env_dir(browser_data_dir), width=10).pack(side="left", padx=(0, 5))
        ttk.Button(data_btn_frame, text="🍪 清空Cookie", 
                  command=lambda: self._clear_browser_cookies(browser_data_dir), width=12).pack(side="left", padx=(0, 5))
        ttk.Button(data_btn_frame, text="🗑️ 清空全部", 
                  command=lambda: self._clear_env_browser_data(browser_data_dir), width=12).pack(side="left")
        
        python_card = ttk.LabelFrame(right_frame, text=" 🐍 Python环境（打包用） ", padding=10)
        python_card.pack(fill="x", pady=5)
        
        env_dir = self.get_python_env_path()
        python_exe = os.path.join(env_dir, 'python.exe')
        if not os.path.exists(python_exe):
            python_exe = os.path.join(env_dir, 'Scripts', 'python.exe')
        pyvenv_cfg = os.path.join(env_dir, 'pyvenv.cfg') if env_dir else None
        
        env_exists = python_exe and os.path.exists(python_exe)
        
        if env_exists:
            try:
                result = subprocess.run([python_exe, '--version'], capture_output=True, text=True, timeout=5)
                python_version = result.stdout.strip().replace('Python ', '') if result.returncode == 0 else '未知'
            except:
                python_version = '未知'
            
            ttk.Label(python_card, text=f"Python版本: {python_version}", 
                     font=("Microsoft YaHei", 10, "bold")).pack(anchor="w")
            ttk.Label(python_card, text=f"路径:", foreground="#7f8c8d").pack(anchor="w", pady=(5, 0))
            ttk.Label(python_card, text=env_dir, foreground="#3498db", 
                     font=("Microsoft YaHei", 8), wraplength=280).pack(anchor="w")
            ttk.Label(python_card, text="✅ 打包环境已就绪", foreground="#27ae60", 
                     font=("Microsoft YaHei", 9, "bold")).pack(anchor="w", pady=(10, 0))
        else:
            ttk.Label(python_card, text="Python版本: 未解压", 
                     font=("Microsoft YaHei", 10, "bold")).pack(anchor="w")
            ttk.Label(python_card, text=f"路径: {env_dir}", foreground="#7f8c8d").pack(anchor="w", pady=(5, 0))
            ttk.Label(python_card, text="⚠️ 打包环境未就绪", foreground="#f39c12", 
                     font=("Microsoft YaHei", 9, "bold")).pack(anchor="w", pady=(10, 0))
            
            python_btn_frame = ttk.Frame(python_card)
            python_btn_frame.pack(fill="x", pady=(5, 0))
            ttk.Button(python_btn_frame, text="📦 提前解压", 
                      command=self._extract_python_env, width=12).pack(side="left")
        
        info_card = ttk.LabelFrame(right_frame, text=" ℹ️ 说明 ", padding=15)
        info_card.pack(fill="x", pady=5)
        
        info_text = """浏览器环境：
• 内置Chromium浏览器（约300MB）
• 用于文献下载和网站登录
• 从官方源下载，安全可靠

Python环境（打包用）：
• 外部迷你Python环境
• 用于打包成单文件EXE
• 首次打包时自动解压"""
        
        ttk.Label(info_card, text=info_text, foreground="#7f8c8d", 
                 font=("Microsoft YaHei", 9), justify="left").pack(anchor="w")
    
    def _on_browser_type_change(self, show_warning=True):
        browser_type = self.browser_type_var.get()
        self.save_config()
        if browser_type == "internal":
            self._browser_data_dir_label.config(text="目录: browser_data（内置浏览器专用）")
            self._browser_data_info_label.config(text="（登录状态、Cookies、缓存、浏览记录）")
        elif browser_type == "auto":
            detected = getattr(self, '_detected_browsers', [])
            if detected:
                first_browser = detected[0]
                self._browser_data_dir_label.config(text=f"自动选择: {first_browser['name']}")
                if first_browser['id'] == 'internal':
                    self._browser_data_info_label.config(text="（使用内置浏览器，登录状态保存在本地）")
                else:
                    self._browser_data_info_label.config(text="（使用系统浏览器，数据由浏览器管理）")
            else:
                self._browser_data_dir_label.config(text="自动选择: 未检测到浏览器")
                self._browser_data_info_label.config(text="（请先下载内置浏览器或安装系统浏览器）")
        elif browser_type in ['chrome', 'msedge', 'firefox']:
            browser_names = {
                'chrome': 'Google Chrome',
                'msedge': 'Microsoft Edge',
                'firefox': 'Firefox'
            }
            browser_name = browser_names.get(browser_type, browser_type)
            self._browser_data_dir_label.config(text=f"⚠️ 使用系统浏览器: {browser_name}")
            self._browser_data_info_label.config(text="（数据由浏览器管理，请在浏览器中清理Cookie）")
            
            if show_warning and not getattr(self, '_external_browser_warning_shown', False):
                self._external_browser_warning_shown = True
                result = messagebox.askyesno(
                    "⚠️ 外部浏览器风险提示",
                    f"您选择使用 {browser_name}，可能会面临以下风险：\n\n"
                    "• 有概率被网站临时封禁\n"
                    "• 需要您主动清理浏览器Cookie或申诉\n"
                    "• 部分网站可能检测到自动化行为\n\n"
                    "💡 使用内置浏览器可以避免以上风险\n\n"
                    "使用外部浏览器可能获得更好的下载体验，\n"
                    "但风险与体验并存。\n\n"
                    "确定要使用外部浏览器吗？\n"
                    "（选择【是】后将不再提示）",
                    icon='warning'
                )
                if not result:
                    self.browser_type_var.set("internal")
                    self._on_browser_type_change(show_warning=False)
                    return
        else:
            if is_frozen():
                browser_data_dir = os.path.join(get_base_path(), "browser_data")
            else:
                browser_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "browser_data")
            self._browser_data_dir_label.config(text=f"目录: {browser_data_dir}")
            self._browser_data_info_label.config(text="（登录状态、Cookies、缓存、浏览记录）")
    
    def _auto_search_browsers(self):
        browsers = self._search_system_browsers()
        
        for widget in self._browser_options_frame.winfo_children():
            widget.destroy()
        
        if browsers:
            browser_names = [b['name'] for b in browsers]
            self._detected_browsers_label.config(text=f"检测到 {len(browsers)} 个浏览器: {', '.join(browser_names)}")
            
            saved_browser = self.browser_type_var.get()
            saved_browser_exists = any(b['id'] == saved_browser for b in browsers)
            
            for browser in browsers:
                rb = ttk.Radiobutton(self._browser_options_frame, 
                                     text=f"{browser['name']}", 
                                     variable=self.browser_type_var, 
                                     value=browser['id'],
                                     command=self._on_browser_select)
                rb.pack(side="left", padx=5)
            
            if saved_browser and saved_browser_exists:
                self.browser_type_var.set(saved_browser)
            elif browsers:
                self.browser_type_var.set(browsers[0]['id'])
        else:
            self._detected_browsers_label.config(text="未检测到系统浏览器，请使用内置浏览器")
            self.browser_type_var.set("internal")
    
    def _search_and_show_browsers(self):
        browsers = self._search_system_browsers()
        
        for widget in self._browser_options_frame.winfo_children():
            widget.destroy()
        
        if browsers:
            browser_names = [b['name'] for b in browsers]
            self._detected_browsers_label.config(text=f"检测到 {len(browsers)} 个浏览器: {', '.join(browser_names)}")
            
            for browser in browsers:
                rb = ttk.Radiobutton(self._browser_options_frame, 
                                     text=f"{browser['name']}", 
                                     variable=self.browser_type_var, 
                                     value=browser['id'],
                                     command=self._on_browser_select)
                rb.pack(side="left", padx=5)
        else:
            self._detected_browsers_label.config(text="未检测到系统浏览器，请使用内置浏览器")
    
    def _on_browser_select(self):
        self._on_browser_type_change()
    
    def _get_actual_browser_type(self):
        browser_type = self.browser_type_var.get()
        if browser_type == "auto":
            if not self._browser_search_done:
                self._detected_browsers = self._search_system_browsers()
                self._browser_search_done = True
            detected = getattr(self, '_detected_browsers', [])
            if detected:
                return detected[0]['id']
            else:
                return "internal"
        return browser_type
    
    def _start_env_download(self):
        self._env_download_btn.config(state="disabled")
        self._env_download_status_var.set("正在下载...")
        self._env_download_progress_var.set("从官方源下载，请耐心等待...")
        
        def do_download():
            from browser_manager import download_browser, is_browser_ready
            import time
            
            def progress_callback(msg):
                try:
                    clean_msg = msg.replace('■', '🟦').replace('□', '⬜').strip()
                    if clean_msg:
                        self.root.after(0, lambda: self._env_download_progress_var.set(clean_msg))
                except:
                    pass
            
            try:
                result = download_browser(progress_callback=progress_callback, use_mirror=False)
                
                time.sleep(0.5)
                
                ready = is_browser_ready()
                
                if result or ready:
                    self.root.after(0, lambda: self._env_download_status_var.set("✅ 下载完成！"))
                    self.root.after(0, lambda: self._env_download_progress_var.set("浏览器已成功安装"))
                    self.root.after(0, self._refresh_browser_status)
                else:
                    self.root.after(0, lambda: self._env_download_status_var.set("❌ 下载失败"))
                    self.root.after(0, lambda: self._env_download_progress_var.set("请检查网络连接后重试"))
            except Exception as e:
                self.root.after(0, lambda: self._env_download_status_var.set(f"❌ 错误: {str(e)[:20]}"))
            finally:
                self.root.after(0, lambda: self._env_download_btn.config(state="normal"))
        
        import threading
        threading.Thread(target=do_download, daemon=True).start()
    
    def _clear_env_browser(self):
        from browser_manager import get_browsers_path
        browsers_path = get_browsers_path()
        
        if not os.path.exists(browsers_path):
            messagebox.showinfo("提示", "浏览器目录不存在")
            return
        
        if messagebox.askyesno("确认", "确定要删除浏览器吗？\n这将删除所有浏览器文件（约300MB）。"):
            try:
                import shutil
                shutil.rmtree(browsers_path)
                self._refresh_browser_status()
                messagebox.showinfo("成功", "浏览器已删除")
            except Exception as e:
                messagebox.showerror("错误", f"删除失败: {e}")
    
    def _refresh_browser_status(self):
        from browser_manager import is_browser_ready, check_browser_integrity, get_chromium_path
        
        is_ready = is_browser_ready()
        print(f"[GUI] _refresh_browser_status: is_ready={is_ready}")
        
        if is_ready:
            is_valid, status_msg = check_browser_integrity()
        else:
            is_valid, status_msg = False, "未安装"
        
        chromium_path = get_chromium_path()
        print(f"[GUI] chromium_path={chromium_path}, status_msg={status_msg}")
        
        status_icon = "✅" if is_ready else "❌"
        status_color = "#27ae60" if is_ready else "#e74c3c"
        
        self._browser_status_label.config(text=f"状态: {status_icon} {status_msg}", foreground=status_color)
        self._browser_is_ready = is_ready
    
    def _open_env_dir(self, path):
        if os.path.exists(path):
            self.open_file_explorer(path)
        else:
            messagebox.showinfo("提示", "目录不存在（浏览器启动后会自动创建）")
    
    def _show_rate_limited_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("⚠️ 请求被拦截")
        dialog.geometry("400x220")
        dialog.resizable(False, False)
        dialog.configure(bg="white")
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 200
        y = (dialog.winfo_screenheight() // 2) - 110
        dialog.geometry(f"+{x}+{y}")
        
        header = tk.Frame(dialog, bg="#e74c3c", height=50)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(header, text="⚠️ 您的请求已被拦截", font=("Microsoft YaHei", 14, "bold"),
                bg="#e74c3c", fg="white").pack(expand=True)
        
        content = tk.Frame(dialog, bg="white", padx=20, pady=15)
        content.pack(fill="both", expand=True)
        
        tk.Label(content, text="可能原因：", font=("Microsoft YaHei", 10, "bold"),
                bg="white", fg="#2c3e50").pack(anchor="w")
        tk.Label(content, text="• Cookie/缓存问题导致被识别为异常\n• 访问频率过高触发反爬机制\n• 需要重新登录目标网站",
                font=("Microsoft YaHei", 9), bg="white", fg="#7f8c8d", justify="left").pack(anchor="w", pady=(5, 10))
        
        btn_frame = tk.Frame(content, bg="white")
        btn_frame.pack(fill="x", pady=(10, 0))
        
        def clear_cookie_and_close():
            dialog.destroy()
            if is_frozen():
                browser_data_dir = os.path.join(get_base_path(), "browser_data")
            else:
                browser_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "browser_data")
            self._clear_browser_cookies(browser_data_dir)
        
        def clear_all_and_restart():
            dialog.destroy()
            if is_frozen():
                browser_data_dir = os.path.join(get_base_path(), "browser_data")
            else:
                browser_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "browser_data")
            self._clear_env_browser_data(browser_data_dir)
            self.root.after(500, self._restart_app)
        
        def _restart_app():
            import subprocess
            python = sys.executable
            subprocess.Popen([python] + sys.argv)
            self.root.quit()
        
        ttk.Button(btn_frame, text="🍪 清空Cookie", command=clear_cookie_and_close, width=12).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="🗑️ 清空全部并重启", command=clear_all_and_restart, width=14).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="关闭", command=dialog.destroy, width=8).pack(side="right", padx=5)
    
    def _clear_browser_cookies(self, path):
        browser_type = self._get_actual_browser_type()
        if browser_type in ['chrome', 'msedge', 'firefox']:
            browser_names = {
                'chrome': 'Google Chrome',
                'msedge': 'Microsoft Edge',
                'firefox': 'Firefox'
            }
            browser_name = browser_names.get(browser_type, browser_type)
            
            result = messagebox.askyesno(
                "⚠️ 使用系统浏览器",
                f"您当前使用的是系统浏览器: {browser_name}\n\n"
                f"软件无法直接清理系统浏览器的数据，\n"
                f"因为这可能会影响您其他网站的登录状态。\n\n"
                f"您可以选择：\n"
                f"• 点击「是」打开浏览器设置页面\n"
                f"• 点击「否」取消操作\n\n"
                f"建议在浏览器中手动清理Cookie。",
                icon='warning'
            )
            
            if result:
                self._open_browser_settings(browser_type)
            return
        
        if not os.path.exists(path):
            messagebox.showinfo("提示", "目录不存在，无需清除")
            return
        
        result = messagebox.askyesno("确认", "确定要清除Cookie和缓存吗？\n这将删除所有登录状态，但保留其他数据。")
        if not result:
            return
        
        try:
            import shutil
            
            cookie_files = [
                'Cookies', 'Cookies-journal', 'Cookies',
                'Network/Cookies', 'Network/Cookies-journal',
                'Cache', 'Cache_Data',
                'Code Cache', 'GPUCache',
                'Service Worker', 'Session Storage',
                'IndexedDB', 'WebStorage'
            ]
            
            cleared = []
            failed = []
            for root, dirs, files in os.walk(path):
                for d in dirs:
                    if d in ['Cache', 'Cache_Data', 'Code Cache', 'GPUCache', 'Service Worker', 'Session Storage', 'IndexedDB']:
                        try:
                            shutil.rmtree(os.path.join(root, d))
                            cleared.append(d)
                        except Exception as e:
                            failed.append((d, str(e)))
                for f in files:
                    if 'Cookie' in f:
                        try:
                            os.remove(os.path.join(root, f))
                            cleared.append(f)
                        except Exception as e:
                            failed.append((f, str(e)))
            
            if cleared and not failed:
                messagebox.showinfo("成功", f"Cookie和缓存已清除\n\n已删除: {len(set(cleared))} 项")
            elif failed:
                self._show_clear_failed_dialog(path, failed)
            else:
                messagebox.showinfo("提示", "未找到Cookie或缓存文件")
        except Exception as e:
            self._show_clear_failed_dialog(path, [(path, str(e))])
    
    def _show_clear_failed_dialog(self, path, failed_items):
        """显示清除失败的自定义对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("清除失败")
        dialog.geometry("450x200")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = (screen_width - 450) // 2
        y = (screen_height - 200) // 2
        dialog.geometry(f"450x200+{x}+{y}")
        
        msg_frame = ttk.Frame(dialog, padding=15)
        msg_frame.pack(fill="both", expand=True)
        
        ttk.Label(msg_frame, text="⚠️ 此位置的缓存文件无法删除", 
                 font=("Microsoft YaHei", 11, "bold"), foreground="#e74c3c").pack(anchor="w")
        ttk.Label(msg_frame, text=f"共 {len(failed_items)} 个文件/文件夹删除失败", 
                 font=("Microsoft YaHei", 9), foreground="#7f8c8d").pack(anchor="w", pady=(5, 0))
        ttk.Label(msg_frame, text="可能原因：文件正在被使用或权限不足", 
                 font=("Microsoft YaHei", 9), foreground="#7f8c8d").pack(anchor="w")
        ttk.Label(msg_frame, text="您可以考虑手动删除这些文件", 
                 font=("Microsoft YaHei", 9), foreground="#3498db").pack(anchor="w", pady=(10, 0))
        
        btn_frame = ttk.Frame(dialog, padding=10)
        btn_frame.pack(fill="x")
        
        def open_folder():
            if os.path.exists(path):
                os.startfile(path)
            dialog.destroy()
        
        ttk.Button(btn_frame, text="📂 打开文件夹", command=open_folder, width=14).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="确定", command=dialog.destroy, width=10).pack(side="right", padx=5)
    
    def _open_browser_settings(self, browser_type):
        settings_urls = {
            'chrome': 'chrome://settings/clearBrowserData',
            'msedge': 'edge://settings/clearBrowserData',
            'firefox': 'about:preferences#privacy'
        }
        
        browser_paths = {
            'chrome': [
                r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
            ],
            'msedge': [
                r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
            ],
            'firefox': [
                r"C:\Program Files\Mozilla Firefox\firefox.exe",
                r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe",
            ],
        }
        
        paths = browser_paths.get(browser_type, [])
        for path in paths:
            if os.path.exists(path):
                try:
                    url = settings_urls.get(browser_type, '')
                    subprocess.Popen([path, url])
                    messagebox.showinfo("提示", f"已打开 {browser_type} 浏览器设置页面\n请在浏览器中手动清理Cookie")
                    return
                except Exception as e:
                    messagebox.showerror("错误", f"打开浏览器失败: {e}")
                    return
        
        messagebox.showwarning("警告", f"未找到 {browser_type} 浏览器")
    
    def _clear_env_browser_data(self, path):
        browser_type = self._get_actual_browser_type()
        if browser_type in ['chrome', 'msedge', 'firefox']:
            browser_names = {
                'chrome': 'Google Chrome',
                'msedge': 'Microsoft Edge',
                'firefox': 'Firefox'
            }
            browser_name = browser_names.get(browser_type, browser_type)
            
            result = messagebox.askyesno(
                "⚠️ 使用系统浏览器",
                f"您当前使用的是系统浏览器: {browser_name}\n\n"
                f"软件无法直接清理系统浏览器的数据，\n"
                f"因为这可能会影响您其他网站的登录状态。\n\n"
                f"您可以选择：\n"
                f"• 点击「是」打开浏览器设置页面\n"
                f"• 点击「否」取消操作\n\n"
                f"建议在浏览器中手动清理所有数据。",
                icon='warning'
            )
            
            if result:
                self._open_browser_settings(browser_type)
            return
        
        if os.path.exists(path):
            if messagebox.askyesno("确认", "确定要清除浏览器数据吗？\n这将删除所有登录状态和浏览记录。"):
                try:
                    import shutil
                    shutil.rmtree(path)
                    messagebox.showinfo("成功", "浏览器数据已清除")
                except Exception as e:
                    self._show_clear_failed_dialog(path, [(path, str(e))])
        else:
            messagebox.showinfo("提示", "目录不存在，无需清除")
    
    def create_browse_config(self, parent):
        path_mode_card = ttk.LabelFrame(parent, text=" 📁 路径模式 ", padding=15)
        path_mode_card.pack(fill="x", pady=10)
        
        path_mode_row = ttk.Frame(path_mode_card)
        path_mode_row.pack(fill="x")
        ttk.Label(path_mode_row, text="路径模式:", style="Bold.TLabel").pack(side="left")
        path_mode_options = ttk.Frame(path_mode_row)
        path_mode_options.pack(side="left", padx=15)
        ttk.Radiobutton(path_mode_options, text="📁 相对路径", 
                       variable=self.path_mode_var, value="relative",
                       command=self.refresh_resource_list).pack(side="left", padx=10)
        ttk.Radiobutton(path_mode_options, text="💾 绝对路径", 
                       variable=self.path_mode_var, value="absolute",
                       command=self.refresh_resource_list).pack(side="left", padx=10)
        path_info = ttk.Label(path_mode_row, 
                              text="(与下载模式中的路径保持一致)",
                              foreground="#95a5a6")
        path_info.pack(side="left", padx=10)
        
        action_card = ttk.LabelFrame(parent, text=" 🎯 操作 ", padding=15)
        action_card.pack(fill="x", pady=10)
        action_row = ttk.Frame(action_card)
        action_row.pack(fill="x")
        refresh_btn = ttk.Button(action_row, text="🔄 刷新列表", command=self.refresh_resource_list)
        refresh_btn.pack(side="left", padx=5)
        ttk.Button(action_row, text="📦 打包选中", command=self.pack_selected_resources).pack(side="left", padx=5)
        ttk.Button(action_row, text="🗑️ 删除选中", command=self.delete_selected_resources).pack(side="left", padx=5)
        
        list_card = ttk.LabelFrame(parent, text=" 📋 已下载网站 ", padding=15)
        list_card.pack(fill="both", expand=True, pady=10)
        
        columns = ("title", "source", "time", "size")
        self.resource_tree = ttk.Treeview(list_card, columns=columns, show="headings", selectmode="extended")
        self.resource_tree.heading("title", text="📄 网页主题")
        self.resource_tree.heading("source", text="🌐 来源")
        self.resource_tree.heading("time", text="⏰ 下载时间")
        self.resource_tree.heading("size", text="📊 大小")
        self.resource_tree.column("title", width=300)
        self.resource_tree.column("source", width=150)
        self.resource_tree.column("time", width=150)
        self.resource_tree.column("size", width=100)
        
        scrollbar = ttk.Scrollbar(list_card, orient="vertical", command=self.resource_tree.yview)
        self.resource_tree.configure(yscrollcommand=scrollbar.set)
        self.resource_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.resource_tree.bind("<Button-3>", self.show_resource_context_menu)
        
        self.refresh_resource_list()
    
    def refresh_resource_list(self):
        for item in self.resource_tree.get_children():
            self.resource_tree.delete(item)
        
        websites = []
        
        if self.path_mode_var.get() == "relative":
            search_dirs = ["downloads", "literature_downloads", "batch_downloads"]
        else:
            search_dirs = [self.save_dir_var.get(), self.literature_output_var.get()]
        
        print("\n" + "="*50)
        print("[资源扫描] 开始扫描...")
        print(f"[资源扫描] 扫描目录: {search_dirs}")
        
        for search_dir in search_dirs:
            if not os.path.exists(search_dir):
                print(f"[资源扫描] 目录不存在: {search_dir}")
                continue
            
            print(f"[资源扫描] 扫描目录: {search_dir}")
            
            for item in os.listdir(search_dir):
                item_path = os.path.join(search_dir, item)
                
                if os.path.isdir(item_path):
                    html_files = [f for f in os.listdir(item_path) if f.endswith('.html') and os.path.isfile(os.path.join(item_path, f))]
                    if html_files:
                        print(f"[资源扫描] 发现文件夹: {item}, HTML文件: {html_files[:3]}...")
                        page_title, source = self._get_page_info(item_path, html_files, item)
                        print(f"[资源扫描] 提取结果 - 标题: {page_title}, 来源: {source}")
                        mtime = os.path.getmtime(item_path)
                        time_str = self.format_time(mtime)
                        total_size = 0
                        for root, dirs, files in os.walk(item_path):
                            for file in files:
                                total_size += os.path.getsize(os.path.join(root, file))
                        if total_size < 1024 * 1024:
                            size_str = f"{total_size / 1024:.1f} KB"
                        else:
                            size_str = f"{total_size / (1024 * 1024):.1f} MB"
                        websites.append((mtime, page_title, source, item_path, time_str, size_str))
                
                elif item.endswith('.html') and os.path.isfile(item_path):
                    print(f"[资源扫描] 发现HTML文件: {item}")
                    page_title, source = self._get_single_html_info(item_path, item)
                    print(f"[资源扫描] 提取结果 - 标题: {page_title}, 来源: {source}")
                    mtime = os.path.getmtime(item_path)
                    time_str = self.format_time(mtime)
                    total_size = os.path.getsize(item_path)
                    if total_size < 1024 * 1024:
                        size_str = f"{total_size / 1024:.1f} KB"
                    else:
                        size_str = f"{total_size / (1024 * 1024):.1f} MB"
                    websites.append((mtime, page_title, source, item_path, time_str, size_str))
        
        print(f"[资源扫描] 共发现 {len(websites)} 个资源")
        print("="*50 + "\n")
        
        websites.sort(key=lambda x: x[0], reverse=True)
        for mtime, page_title, source, item_path, time_str, size_str in websites:
            self.resource_tree.insert("", "end", values=(page_title, source, time_str, size_str), tags=(item_path,))
    
    def _get_single_html_info(self, html_path, filename):
        try:
            from bs4 import BeautifulSoup
            from urllib.parse import urlparse
            
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read(100000)
            
            soup = BeautifulSoup(content, 'lxml')
            
            title = None
            og_title = soup.find('meta', property='og:title')
            if og_title and og_title.get('content'):
                title = og_title['content'].strip()
            
            if not title and soup.title and soup.title.string:
                title = soup.title.string.strip()
            
            if title:
                title = re.sub(r'[\\/*?:"<>|]', '_', title)
                title = re.sub(r'\s+', ' ', title)
                if len(title) > 80:
                    for sep in ['_', '-', '|', '·', '–']:
                        if sep in title:
                            parts = title.split(sep)
                            title = parts[0].strip()
                            break
                if len(title) > 80:
                    title = title[:80] + '...'
            
            source = None
            canonical = soup.find('link', rel='canonical')
            if canonical and canonical.get('href'):
                domain = urlparse(canonical['href']).netloc
                source = get_site_name(domain)
            
            return title or os.path.splitext(filename)[0], source or '未知来源'
        except:
            return os.path.splitext(filename)[0], '未知来源'
    
    def _get_page_info(self, folder_path, html_files, folder_name):
        try:
            from bs4 import BeautifulSoup
            from urllib.parse import urlparse
            
            for html_file in html_files:
                html_path = os.path.join(folder_path, html_file)
                try:
                    print(f"  [_get_page_info] 读取文件: {html_path}")
                    with open(html_path, 'r', encoding='utf-8') as f:
                        content = f.read(100000)
                    
                    soup = BeautifulSoup(content, 'lxml')
                    
                    title = None
                    
                    og_title = soup.find('meta', property='og:title')
                    if og_title and og_title.get('content'):
                        title = og_title['content'].strip()
                        print(f"  [_get_page_info] og:title: {title}")
                    
                    if not title:
                        twitter_title = soup.find('meta', attrs={'name': 'twitter:title'})
                        if twitter_title and twitter_title.get('content'):
                            title = twitter_title['content'].strip()
                            print(f"  [_get_page_info] twitter:title: {title}")
                    
                    if not title and soup.title and soup.title.string:
                        title = soup.title.string.strip()
                        print(f"  [_get_page_info] title标签: {title}")
                    
                    if title:
                        title = re.sub(r'[\\/*?:"<>|]', '_', title)
                        title = re.sub(r'\s+', ' ', title)
                        if len(title) > 80:
                            for sep in ['_', '-', '|', '·', '–']:
                                if sep in title:
                                    parts = title.split(sep)
                                    title = parts[0].strip()
                                    print(f"  [_get_page_info] 标题过长，分割后: {title}")
                                    break
                        if len(title) > 80:
                            title = title[:80] + '...'
                    
                    source = None
                    
                    article_sources = soup.find('meta', attrs={'name': 'article-sources'})
                    if article_sources and article_sources.get('content'):
                        sources_content = article_sources['content']
                        if sources_content:
                            sources_list = sources_content.split(',')
                            if len(sources_list) == 1:
                                source = sources_list[0]
                            else:
                                source = f"{sources_list[0]}等{len(sources_list)}个来源"
                            print(f"  [_get_page_info] 从article-sources获取: {source}")
                    
                    if not source:
                        canonical = soup.find('link', rel='canonical')
                        if canonical and canonical.get('href'):
                            domain = urlparse(canonical['href']).netloc
                            source = get_site_name(domain)
                            print(f"  [_get_page_info] canonical域名: {domain}, 来源: {source}")
                    
                    if not source:
                        og_url = soup.find('meta', property='og:url')
                        if og_url and og_url.get('content'):
                            domain = urlparse(og_url['content']).netloc
                            source = get_site_name(domain)
                            print(f"  [_get_page_info] og:url域名: {domain}, 来源: {source}")
                    
                    if not source:
                        for link in soup.find_all('a', href=True):
                            href = link['href']
                            if href.startswith('http'):
                                domain = urlparse(href).netloc
                                source = get_site_name(domain)
                            if source:
                                print(f"  [_get_page_info] 从链接获取来源: {source}")
                                break
                    
                    if not source:
                        for script in soup.find_all('script'):
                            if script.string and 'window.location' in script.string:
                                import re as re_module
                                match = re_module.search(r'window\.location\s*=\s*["\']([^"\']+)["\']', script.string)
                                if match:
                                    url = match.group(1)
                                    if url.startswith('http'):
                                        domain = urlparse(url).netloc
                                        source = get_site_name(domain)
                                        print(f"  [_get_page_info] 从跳转脚本获取来源: {source}")
                                        break
                    
                    print(f"  [_get_page_info] 最终结果 - 标题: {title}, 来源: {source}")
                    
                    if title:
                        return title, source or '未知来源'
                except Exception as e:
                    print(f"  [_get_page_info] 错误: {e}")
                    import traceback
                    traceback.print_exc()
            
            return folder_name, '未知来源'
        except Exception as e:
            print(f"[_get_page_info] 外层错误: {e}")
            return folder_name, '未知来源'
    
    def _get_website_title(self, folder_path, html_files, folder_name):
        title, _ = self._get_page_info(folder_path, html_files, folder_name)
        return title
    
    def show_resource_context_menu(self, event):
        selection = self.resource_tree.selection()
        if not selection:
            return
        item = selection[0]
        tags = self.resource_tree.item(item)['tags']
        path = tags[0] if tags else None
        if not path:
            return
        context_menu = tk.Menu(self.root, tearoff=0)
        context_menu.add_command(label="📂 打开位置", command=lambda: self.open_file_explorer(path))
        context_menu.add_command(label="🗑️ 删除", command=lambda: self.delete_resource(path, item))
        context_menu.add_separator()
        context_menu.add_command(label="🌐 本地化部署", command=lambda: self.send_to_localize(path))
        context_menu.add_command(label="📦 发送到打包", command=lambda: self.send_to_pack(path))
        context_menu.post(event.x_root, event.y_root)
    
    def delete_resource(self, path, item_id):
        if messagebox.askyesno("确认删除", "确定要删除这个网站吗？\n此操作不可恢复！"):
            try:
                import shutil
                shutil.rmtree(path)
                self.resource_tree.delete(item_id)
                messagebox.showinfo("成功", "删除成功！")
            except Exception as e:
                messagebox.showerror("错误", f"删除失败：{str(e)}")
    
    def delete_selected_resources(self):
        selection = self.resource_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择要删除的内容")
            return
        
        if not messagebox.askyesno("确认删除", f"确定要删除选中的 {len(selection)} 个项目吗？\n此操作不可恢复！"):
            return
        
        deleted = 0
        for item in selection:
            tags = self.resource_tree.item(item)['tags']
            path = tags[0] if tags else None
            if path and os.path.exists(path):
                try:
                    import shutil
                    shutil.rmtree(path)
                    self.resource_tree.delete(item)
                    deleted += 1
                except Exception as e:
                    pass
        
        messagebox.showinfo("完成", f"已删除 {deleted} 个项目")
    
    def pack_selected_resources(self):
        selection = self.resource_tree.selection()
        if not selection:
            messagebox.showinfo("提示", "请先选择要打包的内容")
            return
        
        paths = []
        for item in selection:
            tags = self.resource_tree.item(item)['tags']
            path = tags[0] if tags else None
            if path and os.path.exists(path):
                paths.append(path)
        
        if not paths:
            messagebox.showwarning("警告", "没有有效的路径可打包")
            return
        
        self._show_pack_selection_dialog(paths)
    
    def _show_pack_selection_dialog(self, paths):
        pack_dialog = tk.Toplevel(self.root)
        pack_dialog.title("打包选中内容")
        pack_dialog.geometry("500x400")
        pack_dialog.transient(self.root)
        pack_dialog.grab_set()
        
        main_frame = ttk.Frame(pack_dialog, padding=15)
        main_frame.pack(fill="both", expand=True)
        
        ttk.Label(main_frame, text=f"已选择 {len(paths)} 个项目：", font=("Microsoft YaHei", 11, "bold")).pack(anchor="w", pady=(0, 10))
        
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill="both", expand=True, pady=10)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        path_listbox = tk.Listbox(list_frame, yscrollcommand=scrollbar.set, font=("Microsoft YaHei", 9))
        path_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=path_listbox.yview)
        
        for path in paths:
            path_listbox.insert(tk.END, os.path.basename(path))
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=15)
        
        def do_pack():
            pack_dialog.destroy()
            self._pack_multiple_paths(paths)
        
        ttk.Button(btn_frame, text="📦 开始打包", command=do_pack).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="取消", command=pack_dialog.destroy).pack(side="right", padx=5)
    
    def _pack_multiple_paths(self, paths):
        output_dir = filedialog.askdirectory(title="选择打包输出目录")
        if not output_dir:
            return
        
        self.log(f"开始打包 {len(paths)} 个项目...", "info")
        
        import threading
        def do_pack():
            success_count = 0
            for i, path in enumerate(paths):
                self.root.after(0, lambda p=path, n=i+1: self.log(f"[{n}/{len(paths)}] 正在打包: {os.path.basename(p)}", "info"))
                try:
                    result = self._pack_single_website(path, output_dir)
                    if result:
                        success_count += 1
                        self.root.after(0, lambda p=path: self.log(f"✅ 打包完成: {os.path.basename(p)}", "success"))
                    else:
                        self.root.after(0, lambda p=path: self.log(f"❌ 打包失败: {os.path.basename(p)}", "error"))
                except Exception as e:
                    self.root.after(0, lambda p=path, e=e: self.log(f"❌ 打包错误 {os.path.basename(p)}: {e}", "error"))
            
            self.root.after(0, lambda: self.log(f"\n打包完成！成功: {success_count}/{len(paths)}", "success"))
            self.root.after(0, lambda: messagebox.showinfo("完成", f"打包完成！\n成功: {success_count}/{len(paths)}"))
        
        threading.Thread(target=do_pack, daemon=True).start()
    
    def _pack_single_website(self, website_dir, output_dir):
        try:
            import subprocess
            
            website_name = os.path.basename(website_dir)
            exe_path = os.path.join(output_dir, f"{website_name}.exe")
            
            cmd = [
                sys.executable, '-m', 'PyInstaller',
                '--onefile',
                '--windowed',
                '--name', website_name,
                '--distpath', output_dir,
                '--workpath', os.path.join(output_dir, 'build_temp'),
                '--specpath', output_dir,
                '--add-data', f'{website_dir};{website_name}',
                '-y',
                'preview_helper.py'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            return result.returncode == 0
        except Exception as e:
            self.log(f"打包错误: {e}", "error")
            return False
    
    def send_to_pack(self, path):
        self.notebook.select(self.pack_tab)
        self.pack_website_dir.set(path)
    
    def send_to_localize(self, path):
        self.notebook.select(self.localize_tab)
        self.localize_website_dir.set(path)
    
    def select_localize_website_dir(self):
        folder = filedialog.askdirectory()
        if folder:
            self.localize_website_dir.set(folder)
    
    def auto_detect_localize_website_dir(self):
        if self.path_mode_var.get() == "relative":
            search_dir = "downloads"
        else:
            search_dir = self.save_dir_var.get()
        if not os.path.exists(search_dir):
            messagebox.showwarning("警告", "未找到下载目录！")
            return
        
        websites = []
        for item in os.listdir(search_dir):
            item_path = os.path.join(search_dir, item)
            if not os.path.isdir(item_path):
                continue
            html_files = []
            for file in os.listdir(item_path):
                if file == 'index.html':
                    html_files.insert(0, file)
                elif file.endswith('.html'):
                    html_files.append(file)
            if html_files:
                html_file = html_files[0]
                file_path = os.path.join(item_path, html_file)
                websites.append((os.path.getmtime(file_path), item_path, item, html_file))
        
        if not websites:
            messagebox.showinfo("提示", "未找到已下载的网站！")
            return
        
        websites.sort(key=lambda x: x[0], reverse=True)
        index_websites = [w for w in websites if w[3] == 'index.html']
        if index_websites:
            websites = index_websites
        latest_website = websites[0]
        self.localize_website_dir.set(latest_website[1])
        self.localize_log(f"✅ 自动检测到网站: {latest_website[2]} ({latest_website[3]})", "success")
    
    def show_website_selector(self, websites):
        dialog = tk.Toplevel(self.root)
        dialog.title("选择网站")
        dialog.geometry("800x500")
        dialog.resizable(True, True)
        dialog.transient(self.root)
        dialog.grab_set()
        
        header_frame = ttk.Frame(dialog, padding=10)
        header_frame.pack(fill="x")
        ttk.Label(header_frame, 
                text=f"找到 {len(websites)} 个网站", 
                font=("Microsoft YaHei", 12, "bold"),
                foreground="#2c3e50").pack(side="left")
        ttk.Label(header_frame, 
                text="（按修改时间排序）", 
                font=("Microsoft YaHei", 9),
                foreground="#7f8c8d").pack(side="left", padx=10)
        
        list_frame = ttk.Frame(dialog)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        scroll_frame = ttk.Frame(list_frame)
        scroll_frame.pack(fill="both", expand=True)
        scrollbar = ttk.Scrollbar(scroll_frame)
        scrollbar.pack(side="right", fill="y")
        columns = ("website", "path", "mtime")
        tree = ttk.Treeview(scroll_frame, columns=columns, show="headings", yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=tree.yview)
        tree.heading("website", text="网站名称")
        tree.heading("path", text="路径")
        tree.heading("mtime", text="下载时间")
        tree.column("website", width=200)
        tree.column("path", width=400)
        tree.column("mtime", width=150)
        
        for mtime, item_path, item_name in websites:
            mtime_str = self.format_time(mtime)
            tree.insert("", "end", values=(item_name, item_path, mtime_str), tags=(item_path,))
        
        def on_double_click(event):
            selection = tree.selection()
            if selection:
                item = selection[0]
                values = tree.item(item)['values']
                self.localize_website_dir.set(values[1])
                self.localize_log(f"🔍 已选择网站: {values[0]}")
                dialog.destroy()
        tree.bind("<Double-1>", on_double_click)
        
        button_frame = ttk.Frame(dialog, padding=10)
        button_frame.pack(fill="x")
        ttk.Button(button_frame, text="取消", command=dialog.destroy, width=15).pack(side="right")
    
    def update_localize_path_display(self):
        if self.path_mode_var.get() == "relative":
            current_path = self.localize_website_dir.get()
            if current_path:
                relative_path = self.get_relative_path(current_path)
                if relative_path != current_path:
                    self.localize_website_dir.set(relative_path)
        else:
            current_path = self.localize_website_dir.get()
            if current_path:
                absolute_path = self.get_absolute_path_from_relative(current_path)
                if absolute_path != current_path:
                    self.localize_website_dir.set(absolute_path)
    
    def get_absolute_path_from_relative(self, path):
        if os.path.isabs(path):
            return path
        else:
            return os.path.abspath(os.path.join(os.getcwd(), path))
    
    def start_localize(self):
        mode = self.localize_mode_var.get()
        
        if mode == "single":
            website_path = self.localize_website_dir.get()
            if not website_path:
                messagebox.showwarning("警告", "请先选择网站目录！")
                return
            if not os.path.exists(website_path):
                messagebox.showerror("错误", "网站目录不存在！")
                return
            threading.Thread(target=self.run_localize, args=(website_path,), daemon=True).start()
        else:
            dirs = list(self.localize_dir_listbox.get(0, tk.END))
            if not dirs:
                messagebox.showwarning("警告", "请先添加网站目录！")
                return
            invalid_dirs = [d for d in dirs if not os.path.exists(d)]
            if invalid_dirs:
                messagebox.showerror("错误", f"以下目录不存在：\n" + "\n".join(invalid_dirs[:5]))
                return
            threading.Thread(target=self.run_localize_directory_mode, args=(dirs,), daemon=True).start()
    
    def run_localize(self, website_path, show_messagebox=True):
        try:
            self.localize_log(f"🌐 开始本地化部署（单文件模式）: {website_path}", "info")
            self.log(f"🌐 开始本地化部署（单文件模式）: {website_path}", "info")
            
            html_files = []
            for root, _, files in os.walk(website_path):
                for file in files:
                    if file.endswith('.html'):
                        html_files.append(os.path.join(root, file))
            
            if not html_files:
                self.localize_log("❌ 未找到HTML文件！", "error")
                return
            
            import base64
            import requests
            from urllib.parse import urljoin
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })
            
            def file_to_base64(file_path, mime_type='application/octet-stream'):
                try:
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    ext = os.path.splitext(file_path)[1].lower()
                    mime_map = {
                        '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                        '.gif': 'image/gif', '.svg': 'image/svg+xml', '.webp': 'image/webp',
                        '.ico': 'image/x-icon', '.css': 'text/css', '.js': 'application/javascript',
                        '.woff': 'font/woff', '.woff2': 'font/woff2', '.ttf': 'font/ttf',
                        '.eot': 'application/vnd.ms-fontobject'
                    }
                    mime_type = mime_map.get(ext, mime_type)
                    b64 = base64.b64encode(content).decode('utf-8')
                    return f'data:{mime_type};base64,{b64}'
                except:
                    return None
            
            html_processed = 0
            total_images = 0
            total_styles = 0
            total_bg = 0
            
            for html_file in html_files:
                try:
                    with open(html_file, 'r', encoding='utf-8') as f:
                        soup = BeautifulSoup(f.read(), 'html.parser')
                    
                    html_dir = os.path.dirname(os.path.abspath(html_file))
                    modified = False
                    
                    img_count = 0
                    for img in soup.find_all('img'):
                        src = img.get('src')
                        if src and not src.startswith(('data:', 'http://', 'https://', 'blob:')):
                            abs_path = os.path.normpath(os.path.join(html_dir, src))
                            if os.path.exists(abs_path):
                                data_uri = file_to_base64(abs_path)
                                if data_uri:
                                    img['src'] = data_uri
                                    img_count += 1
                                    modified = True
                    total_images += img_count
                    
                    style_count = 0
                    for link in soup.find_all('link', rel='stylesheet'):
                        href = link.get('href')
                        if href and not href.startswith(('data:', 'http://', 'https://')):
                            abs_path = os.path.normpath(os.path.join(html_dir, href))
                            if os.path.exists(abs_path):
                                data_uri = file_to_base64(abs_path, 'text/css')
                                if data_uri:
                                    try:
                                        with open(abs_path, 'r', encoding='utf-8') as f:
                                            css_content = f.read()
                                        style_tag = soup.new_tag('style')
                                        style_tag.string = css_content
                                        link.replace_with(style_tag)
                                        style_count += 1
                                        modified = True
                                    except:
                                        pass
                    total_styles += style_count
                    
                    bg_count = 0
                    url_pattern = re.compile(r'url\(["\']?([^)"\'\s]+)["\']?\)')
                    
                    def replace_css_urls(css_text, css_dir):
                        nonlocal bg_count
                        def repl(m):
                            url = m.group(1).strip('\'"')
                            if url.startswith(('data:', 'http://', 'https://', 'blob:', '#')):
                                return m.group(0)
                            abs_path = os.path.normpath(os.path.join(css_dir, url))
                            if os.path.exists(abs_path):
                                data_uri = file_to_base64(abs_path)
                                if data_uri:
                                    bg_count += 1
                                    return f'url({data_uri})'
                            return m.group(0)
                        return url_pattern.sub(repl, css_text)
                    
                    for el in soup.find_all(style=True):
                        el['style'] = replace_css_urls(el.get('style', ''), html_dir)
                        modified = True
                    
                    for style in soup.find_all('style'):
                        if style.string:
                            style.string = replace_css_urls(style.string, html_dir)
                            modified = True
                    
                    total_bg += bg_count
                    
                    for script in soup.find_all('script'):
                        script.decompose()
                        modified = True
                    
                    for iframe in soup.find_all('iframe'):
                        iframe.decompose()
                        modified = True
                    
                    inject_style = soup.new_tag('style')
                    inject_style.string = '''
html, body {
    overflow: auto !important;
    overflow-x: auto !important;
    overflow-y: auto !important;
    height: auto !important;
    max-height: none !important;
}
html, body, div, p, span, h1, h2, h3, h4, h5, h6, article, section, main, pre, code, td, th, li {
    -webkit-user-select: text !important;
    -moz-user-select: text !important;
    -ms-user-select: text !important;
    user-select: text !important;
}
'''
                    if soup.head:
                        soup.head.append(inject_style)
                    
                    if modified:
                        with open(html_file, 'w', encoding='utf-8') as f:
                            f.write(str(soup))
                        html_processed += 1
                        self.localize_log(f"✅ {os.path.basename(html_file)}: 图片{img_count} 样式{style_count} 背景图{bg_count}", "success")
                    else:
                        self.localize_log(f"⏩ 无需修改: {os.path.basename(html_file)}", "info")
                        
                except Exception as e:
                    self.localize_log(f"❌ 处理失败 {os.path.basename(html_file)}: {str(e)}", "error")
            
            self.localize_log("=" * 50, "info")
            self.localize_log(f"🎉 本地化部署完成！", "success")
            self.localize_log(f"📊 处理 {html_processed} 个HTML文件", "info")
            self.localize_log(f"📊 内嵌: 图片 {total_images}, 样式 {total_styles}, 背景图 {total_bg}", "info")
            self.log(f"🎉 本地化部署完成，已处理 {html_processed} 个HTML文件", "success")
            
            if show_messagebox:
                message = f"本地化部署完成！\n\n"
                message += f"已处理: {html_processed} 个HTML文件\n"
                message += f"内嵌资源: 图片 {total_images}, 样式 {total_styles}, 背景图 {total_bg}\n\n"
                message += "现在可以直接用浏览器打开HTML文件了！"
                messagebox.showinfo("完成", message)
                
        except Exception as e:
            self.localize_log(f"❌ 本地化部署失败: {str(e)}", "error")
            messagebox.showerror("错误", f"本地化部署失败：{str(e)}")
    
    def run_localize_directory_mode(self, dirs):
        try:
            output_dir = filedialog.askdirectory(title="选择输出目录")
            if not output_dir:
                return
            
            self.localize_log(f"📚 开始生成目录合集，共 {len(dirs)} 个目录", "info")
            
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            collection_dir = os.path.join(output_dir, f"网页合集_{timestamp}")
            os.makedirs(collection_dir, exist_ok=True)
            
            pages_dir = os.path.join(collection_dir, "pages")
            os.makedirs(pages_dir, exist_ok=True)
            
            all_pages = []
            
            for i, dir_path in enumerate(dirs):
                dir_name = os.path.basename(dir_path)
                self.localize_log(f"[{i+1}/{len(dirs)}] 处理: {dir_name}", "info")
                
                html_files = [f for f in os.listdir(dir_path) if f.endswith('.html') and os.path.isfile(os.path.join(dir_path, f))]
                
                for html_file in html_files:
                    if html_file in ['index.html', '文献合集.html']:
                        continue
                    
                    src_path = os.path.join(dir_path, html_file)
                    dst_path = os.path.join(pages_dir, f"{dir_name}_{html_file}")
                    
                    try:
                        import shutil
                        shutil.copy2(src_path, dst_path)
                        
                        page_title = self._get_html_title(dst_path)
                        page_source = self._get_html_source(dst_path)
                        
                        all_pages.append({
                            'file': f"{dir_name}_{html_file}",
                            'title': page_title or dir_name,
                            'source': page_source or '未知来源'
                        })
                        
                        self.localize_log(f"  ✅ {html_file}", "success")
                    except Exception as e:
                        self.localize_log(f"  ❌ {html_file}: {e}", "error")
            
            if all_pages:
                self._generate_collection_index(collection_dir, pages_dir, all_pages)
                self.localize_log(f"\n🎉 目录合集生成完成！", "success")
                self.localize_log(f"📁 输出目录: {collection_dir}", "info")
                self.localize_log(f"📊 共 {len(all_pages)} 个页面", "info")
                
                messagebox.showinfo("完成", f"目录合集生成完成！\n\n输出目录: {collection_dir}\n共 {len(all_pages)} 个页面")
                
                self.open_file_explorer(collection_dir)
            else:
                self.localize_log("❌ 未找到有效的HTML文件", "error")
                messagebox.showwarning("警告", "未找到有效的HTML文件")
                
        except Exception as e:
            self.localize_log(f"❌ 生成失败: {str(e)}", "error")
            messagebox.showerror("错误", f"生成失败：{str(e)}")
    
    def _get_html_title(self, html_path):
        try:
            from bs4 import BeautifulSoup
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read(30000)
            soup = BeautifulSoup(content, 'lxml')
            if soup.title and soup.title.string:
                title = soup.title.string.strip()
                title = re.sub(r'[\\/*?:"<>|]', '_', title)
                return title[:50] + '...' if len(title) > 50 else title
        except:
            pass
        return None
    
    def _get_html_source(self, html_path):
        try:
            from bs4 import BeautifulSoup
            from urllib.parse import urlparse
            with open(html_path, 'r', encoding='utf-8') as f:
                content = f.read(30000)
            soup = BeautifulSoup(content, 'lxml')
            canonical = soup.find('link', rel='canonical')
            if canonical and canonical.get('href'):
                domain = urlparse(canonical['href']).netloc
                site_names = {
                    'zhihu.com': '知乎',
                    'csdn.net': 'CSDN',
                    'juejin.cn': '掘金',
                    'jianshu.com': '简书',
                    'bilibili.com': '哔哩哔哩',
                }
                for site_domain, site_name in site_names.items():
                    if site_domain in domain:
                        return site_name
                return domain
        except:
            pass
        return None
    
    def _generate_collection_index(self, collection_dir, pages_dir, pages):
        from bs4 import BeautifulSoup
        
        toc_css = '''
        .floating-toc-panel {
            position: fixed;
            top: 50%;
            left: 20px;
            transform: translateY(-50%);
            width: 350px;
            max-height: 80vh;
            background: rgba(255, 255, 255, 0.98);
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            z-index: 999999;
            overflow: hidden;
        }
        .floating-toc-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            font-size: 16px;
            font-weight: bold;
        }
        .floating-toc-content {
            padding: 15px;
            max-height: calc(80vh - 60px);
            overflow-y: auto;
        }
        .floating-toc-item {
            padding: 12px 15px;
            margin: 8px 0;
            background: #f8f9fa;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        .floating-toc-item:hover {
            background: #e3f2fd;
            transform: translateX(3px);
        }
        .floating-toc-item-title {
            color: #333;
            font-size: 14px;
        }
        .floating-toc-item-source {
            color: #7f8c8d;
            font-size: 11px;
            margin-top: 3px;
        }
        '''
        
        items_html = ""
        for page in pages:
            items_html += f'''
            <div class="floating-toc-item" onclick="location.href='pages/{page['file']}'">
                <div class="floating-toc-item-title">{page['title']}</div>
                <div class="floating-toc-item-source">{page['source']}</div>
            </div>'''
        
        index_html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>网页合集</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: "Microsoft YaHei", sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .container {{
            text-align: center;
            color: white;
            padding: 40px;
        }}
        h1 {{ font-size: 48px; margin-bottom: 20px; }}
        p {{ font-size: 18px; opacity: 0.9; margin-bottom: 30px; }}
        .info {{ font-size: 14px; opacity: 0.7; }}
        {toc_css}
    </style>
</head>
<body>
    <div class="container">
        <h1>📚 网页合集</h1>
        <p>共收录 {len(pages)} 个页面</p>
        <p class="info">点击左侧目录导航浏览</p>
    </div>
    <div class="floating-toc-panel">
        <div class="floating-toc-header">📑 文章目录</div>
        <div class="floating-toc-content">
            {items_html}
        </div>
    </div>
</body>
</html>'''
        
        index_path = os.path.join(collection_dir, "index.html")
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_html)
        
        self.localize_log(f"✅ 生成目录页: index.html", "success")
    

    def localize_log(self, message, level="info"):
        self.localize_log_area.config(state="normal")
        self.localize_log_area.insert("end", message + "\n", level)
        self.localize_log_area.see("end")
        self.localize_log_area.config(state="disabled")
    
    def show_localize_log_context_menu(self, event):
        context_menu = tk.Menu(self.root, tearoff=0)
        context_menu.add_command(label="📋 复制全部", command=self.copy_all_localize_logs)
        context_menu.add_command(label="📄 复制选中", command=self.copy_selected_localize_logs)
        context_menu.add_separator()
        context_menu.add_command(label="🗑️ 清空日志", command=self.clear_localize_logs)
        context_menu.post(event.x_root, event.y_root)
    
    def copy_all_localize_logs(self):
        try:
            self.localize_log_area.config(state="normal")
            all_text = self.localize_log_area.get("1.0", "end-1c")
            self.localize_log_area.config(state="disabled")
            self.root.clipboard_clear()
            self.root.clipboard_append(all_text)
            self.root.update()
            self.localize_log("📋 已复制全部日志到剪贴板")
        except Exception as e:
            messagebox.showerror("错误", f"复制失败：{str(e)}")
    
    def copy_selected_localize_logs(self):
        try:
            selected_text = self.localize_log_area.get("sel.first", "sel.last")
            self.root.clipboard_clear()
            self.root.clipboard_append(selected_text)
            self.root.update()
            self.localize_log("📋 已复制选中内容到剪贴板")
        except Exception as e:
            messagebox.showerror("错误", f"复制失败：{str(e)}")
    
    def clear_localize_logs(self):
        self.localize_log_area.config(state="normal")
        self.localize_log_area.delete("1.0", "end")
        self.localize_log_area.config(state="disabled")
        self.localize_log("🗑️ 日志已清空")
    
    def show_about(self):
        about_window = tk.Toplevel(self.root)
        about_window.title("关于")
        about_window.geometry("600x700")
        about_window.resizable(False, False)
        
        canvas = tk.Canvas(about_window, bg="#ffffff", highlightthickness=0)
        scrollbar = ttk.Scrollbar(about_window, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        main_frame = ttk.Frame(scrollable_frame, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        image_paths = [
            get_resource_path("assets/作者.png"),
            get_resource_path("assets/author.jpg"),
            get_resource_path("作者图片.jpg")
        ]
        
        image_path = None
        for path in image_paths:
            if os.path.exists(path):
                image_path = path
                break
        
        if image_path:
            try:
                from PIL import Image, ImageTk
                image = Image.open(image_path)
                width = 300
                ratio = width / image.width
                height = int(image.height * ratio)
                image = image.resize((width, height), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(image)
                image_label = ttk.Label(main_frame, image=photo)
                image_label.image = photo
                image_label.pack(pady=10)
            except Exception as e:
                print(f"加载作者图片失败: {e}")
        
        title_label = ttk.Label(main_frame, 
                               text="网页资源离线下载器",
                               font=("Microsoft YaHei", 16, "bold"),
                               foreground="#2c3e50")
        title_label.pack(pady=(10, 5))
        version_label = ttk.Label(main_frame,
                               text="专业美化版 v2.0",
                               font=("Microsoft YaHei", 10),
                               foreground="#7f8c8d")
        version_label.pack(pady=5)
        author_label = ttk.Label(main_frame,
                              text="由 Thanksplay 开发",
                              font=("Microsoft YaHei", 9),
                              foreground="#3498db")
        author_label.pack(pady=5)
        separator = ttk.Separator(main_frame, orient='horizontal')
        separator.pack(fill='x', pady=15)
        info_text = """此商品在闲鱼上出售，售价为 15.88 元。

如果您不是从闲鱼店铺整点猫条购买的，则可能是盗版。

您可以凭此公告进行退款：
- 联系商家进行退款
- 也可以联系我进行申诉"""
        info_label = ttk.Label(main_frame, text=info_text, justify="left", font=("Microsoft YaHei", 9))
        info_label.pack(pady=10, padx=10)
        update_text = """⚠️ 重要提示：

此软件完全离线运行。

您通过购买获得此程序，有权利获取后续的更新。

由于购买人数较多，作者无法主动向每个人推送更新。

您需要主动关注作者以获取最新版本更新。"""
        update_label = ttk.Label(main_frame, text=update_text, justify="left", 
                               font=("Microsoft YaHei", 9), foreground="#e67e22")
        update_label.pack(pady=10, padx=10)
        separator2 = ttk.Separator(main_frame, orient='horizontal')
        separator2.pack(fill='x', pady=15)
        user_log_text = """📝 用户日志：

感谢您使用本软件！

如果您有任何问题或建议，欢迎联系作者。

请通过正规渠道购买，支持正版！"""
        user_log_label = ttk.Label(main_frame, text=user_log_text, justify="left", 
                                  font=("Microsoft YaHei", 9), foreground="#27ae60")
        user_log_label.pack(pady=10, padx=10)
        
        contact_frame = ttk.Frame(main_frame)
        contact_frame.pack(fill="x", pady=5, padx=20)
        
        qq_row = ttk.Frame(contact_frame)
        qq_row.pack(fill="x", pady=5)
        ttk.Label(qq_row, text="QQ:", font=("Microsoft YaHei", 9, "bold")).pack(side="left")
        qq_entry = ttk.Entry(qq_row, width=25, font=("Microsoft YaHei", 9))
        qq_entry.insert(0, "2979317248")
        qq_entry.config(state="readonly")
        qq_entry.pack(side="left", padx=10, fill="x", expand=True)
        ttk.Button(qq_row, text="📋 复制", width=8, command=lambda: self._copy_to_clipboard("2979317248")).pack(side="left")
        
        phone_row = ttk.Frame(contact_frame)
        phone_row.pack(fill="x", pady=5)
        ttk.Label(phone_row, text="电话:", font=("Microsoft YaHei", 9, "bold")).pack(side="left")
        phone_entry = ttk.Entry(phone_row, width=25, font=("Microsoft YaHei", 9))
        phone_entry.insert(0, "13357728293")
        phone_entry.config(state="readonly")
        phone_entry.pack(side="left", padx=10, fill="x", expand=True)
        ttk.Button(phone_row, text="📋 复制", width=8, command=lambda: self._copy_to_clipboard("13357728293")).pack(side="left")
        close_btn = ttk.Button(main_frame, text="关闭", command=about_window.destroy, width=15)
        close_btn.pack(pady=20)
        about_window.transient(self.root)
        about_window.grab_set()
        about_window.focus_set()
    
    def show_user_manual(self):
        self.manual.show_manual()
    
    def show_log_context_menu(self, event):
        context_menu = tk.Menu(self.root, tearoff=0)
        context_menu.add_command(label="📋 复制全部", command=self.copy_all_logs)
        context_menu.add_command(label="📄 复制选中", command=self.copy_selected_logs)
        context_menu.add_separator()
        context_menu.add_command(label="🗑️ 清空日志", command=self.clear_logs)
        context_menu.post(event.x_root, event.y_root)
    
    def copy_all_logs(self):
        try:
            self.log_area.config(state="normal")
            all_text = self.log_area.get("1.0", "end-1c")
            self.log_area.config(state="disabled")
            self.root.clipboard_clear()
            self.root.clipboard_append(all_text)
            self.root.update()
            self.log("📋 已复制全部日志到剪贴板", "info")
        except Exception as e:
            messagebox.showerror("错误", f"复制失败：{str(e)}")
    
    def copy_selected_logs(self):
        try:
            selected_text = self.log_area.get("sel.first", "sel.last")
            self.root.clipboard_clear()
            self.root.clipboard_append(selected_text)
            self.root.update()
            self.log("📋 已复制选中内容到剪贴板", "info")
        except Exception as e:
            messagebox.showerror("错误", f"复制失败：{str(e)}")
    
    def _copy_to_clipboard(self, text):
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.root.update()
            messagebox.showinfo("成功", f"已复制到剪贴板：{text}")
        except Exception as e:
            messagebox.showerror("错误", f"复制失败：{str(e)}")
    
    def clear_logs(self):
        if messagebox.askyesno("确认", "确定要清空所有日志吗？"):
            self.log_area.config(state="normal")
            self.log_area.delete("1.0", "end")
            self.log_area.config(state="disabled")
            self.log("🗑️ 日志已清空", "info")
    
    def show_pack_log_context_menu(self, event):
        context_menu = tk.Menu(self.root, tearoff=0)
        context_menu.add_command(label="📋 复制全部", command=self.copy_all_pack_logs)
        context_menu.add_command(label="📄 复制选中", command=self.copy_selected_pack_logs)
        context_menu.add_separator()
        context_menu.add_command(label="🗑️ 清空日志", command=self.clear_pack_logs)
        context_menu.post(event.x_root, event.y_root)
    
    def copy_all_pack_logs(self):
        try:
            self.pack_log_area.config(state="normal")
            all_text = self.pack_log_area.get("1.0", "end-1c")
            self.pack_log_area.config(state="disabled")
            self.root.clipboard_clear()
            self.root.clipboard_append(all_text)
            self.root.update()
            self.pack_log("📋 已复制全部日志到剪贴板")
        except Exception as e:
            messagebox.showerror("错误", f"复制失败：{str(e)}")
    
    def copy_selected_pack_logs(self):
        try:
            selected_text = self.pack_log_area.get("sel.first", "sel.last")
            self.root.clipboard_clear()
            self.root.clipboard_append(selected_text)
            self.root.update()
            self.pack_log("📋 已复制选中内容到剪贴板")
        except Exception as e:
            messagebox.showerror("错误", f"复制失败：{str(e)}")
    
    def clear_pack_logs(self):
        if messagebox.askyesno("确认", "确定要清空所有打包日志吗？"):
            self.pack_log_area.config(state="normal")
            self.pack_log_area.delete("1.0", "end")
            self.pack_log_area.config(state="disabled")
            self.pack_log("🗑️ 日志已清空")

    def show_announcement(self):
        try:
            base_path = get_external_base_path()
            
            no_show_file = os.path.join(base_path, "no_show_announcement.txt")
            if os.path.exists(no_show_file):
                return
        except:
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("📢 公告")
        dialog.geometry("600x650")
        dialog.resizable(False, False)
        dialog.configure(bg="white")
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 300
        y = (dialog.winfo_screenheight() // 2) - 325
        dialog.geometry(f"+{x}+{y}")
        
        header = tk.Frame(dialog, bg="#2196f3", height=80)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        title = tk.Label(
            header,
            text="🎉 版本更新公告",
            font=("Microsoft YaHei", 18, "bold"),
            bg="#2196f3",
            fg="white"
        )
        title.pack(expand=True)
        
        version_label = tk.Label(
            header,
            text="V2.1 最新版本",
            font=("Microsoft YaHei", 12),
            bg="#2196f3",
            fg="#bbdefb"
        )
        version_label.pack(pady=(0, 10))
        
        scroll_frame = tk.Frame(dialog, bg="white")
        scroll_frame.pack(fill="both", expand=True)
        
        canvas = tk.Canvas(scroll_frame, bg="white", highlightthickness=0)
        scrollbar = ttk.Scrollbar(scroll_frame, orient="vertical", command=canvas.yview)
        content_frame = tk.Frame(canvas, bg="white", padx=30, pady=15)
        
        content_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=content_frame, anchor="nw", width=540)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        updates = [
            ("📚", "批量下载增强", "支持输出模式、目录模式、资源去重"),
            ("🏷️", "来源标识系统", "自动识别网站来源，显示在目录中"),
            ("🔍", "资源管理优化", "扫描显示真实标题和来源信息"),
            ("🌐", "网站识别扩展", "支持30+网站自动识别来源"),
            ("⚙️", "环境管理功能", "浏览器环境管理，Cookie清理"),
            ("🐛", "修复线程安全", "GUI操作更稳定，避免崩溃"),
            ("🛡️", "资源释放保障", "确保浏览器进程正确关闭"),
            ("📦", "预览功能修复", "打包预览正常启动")
        ]
        
        for icon, title_text, desc in updates:
            item_frame = tk.Frame(content_frame, bg="white")
            item_frame.pack(fill="x", pady=8)
            
            tk.Label(item_frame, text=icon, font=("Microsoft YaHei", 16), bg="white").pack(side="left")
            
            text_frame = tk.Frame(item_frame, bg="white")
            text_frame.pack(side="left", padx=10)
            
            tk.Label(text_frame, text=title_text, font=("Microsoft YaHei", 11, "bold"), 
                    bg="white", fg="#2c3e50").pack(anchor="w")
            tk.Label(text_frame, text=desc, font=("Microsoft YaHei", 9), 
                    bg="white", fg="#7f8c8d").pack(anchor="w")
        
        contact_frame = tk.Frame(content_frame, bg="#e3f2fd", padx=20, pady=15)
        contact_frame.pack(fill="x", pady=(25, 15))
        
        tk.Label(
            contact_frame,
            text="💬 联系与反馈",
            font=("Microsoft YaHei", 11, "bold"),
            bg="#e3f2fd",
            fg="#1976d2"
        ).pack(anchor="w")
        
        tk.Label(
            contact_frame,
            text="• 闲鱼搜索「网页下载器」联系作者",
            font=("Microsoft YaHei", 10),
            bg="#e3f2fd",
            fg="#333"
        ).pack(anchor="w", pady=(8,0))
        
        tk.Label(
            contact_frame,
            text="• 加入粉丝群交流获取最新版本",
            font=("Microsoft YaHei", 10),
            bg="#e3f2fd",
            fg="#333"
        ).pack(anchor="w", pady=(5,0))
        
        btn_frame = tk.Frame(dialog, bg="white", padx=30, pady=15)
        btn_frame.pack(fill="x", side="bottom")
        
        def dont_show_again():
            try:
                base_path = get_external_base_path()
                
                no_show_file = os.path.join(base_path, "no_show_announcement.txt")
                with open(no_show_file, "w") as f:
                    f.write("1")
            except:
                pass
            dialog.destroy()
        
        def close_dialog():
            dialog.destroy()
        
        dont_show_btn = tk.Button(
            btn_frame,
            text="不再显示",
            font=("Microsoft YaHei", 10),
            bg="#9e9e9e",
            fg="white",
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2",
            command=dont_show_again
        )
        dont_show_btn.pack(side="left")
        
        ok_btn = tk.Button(
            btn_frame,
            text="确定",
            font=("Microsoft YaHei", 11, "bold"),
            bg="#2196f3",
            fg="white",
            relief="flat",
            padx=40,
            pady=10,
            cursor="hand2",
            command=close_dialog
        )
        ok_btn.pack(side="right")

    def create_status_bar(self, parent):
        status_frame = ttk.Frame(parent, relief="sunken")
        status_frame.pack(fill="x", side="bottom", pady=(10, 0))
        
        self.status_var = tk.StringVar(value="🟢 就绪 - 请输入网址开始下载")
        status_label = ttk.Label(status_frame, 
                                textvariable=self.status_var,
                                relief="sunken", 
                                anchor="w",
                                font=("Microsoft YaHei", 9),
                                background="#ecf0f1")
        status_label.pack(side="left", fill="x", expand=True, padx=(1, 0), pady=1)
        
        if self.trial_remaining > 0 and self.trial_color:
            trial_label = tk.Label(status_frame,
                                  text=f"📅 剩余 {self.trial_remaining} 次启动",
                                  font=("Microsoft YaHei", 9, "bold"),
                                  bg="#ecf0f1",
                                  fg=self.trial_color,
                                  padx=10)
            trial_label.pack(side="right", padx=(0, 1), pady=1)
        
        if self.trial_remaining == 1:
            self.root.after(500, lambda: messagebox.showwarning(
                "试用期提醒",
                "⚠️ 您的试用期仅剩最后1天！\n\n请尽快激活程序以继续使用。\n如有问题请联系客服。"
            ))

    def create_literature_config(self, parent):
        columns_container = ttk.Frame(parent)
        columns_container.pack(fill="both", expand=True)
        
        left_column = ttk.Frame(columns_container)
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        right_column = ttk.Frame(columns_container)
        right_column.pack(side="left", fill="both", expand=True, padx=(5, 0))
        
        url_card = ttk.LabelFrame(left_column, text=" 📝 待下载网址列表 ", padding=15)
        url_card.pack(fill="both", expand=True, pady=10)
        
        ttk.Label(url_card, text="支持知乎、CSDN等网站，每行一个网址：", 
                 style="Bold.TLabel").pack(anchor="w")
        
        list_frame = ttk.Frame(url_card)
        list_frame.pack(fill="both", expand=True, pady=10)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.literature_url_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            selectmode=tk.EXTENDED,
            font=("Microsoft YaHei", 9),
            bg="#f8f9fa",
            activestyle="none"
        )
        self.literature_url_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.literature_url_listbox.yview)
        
        self.literature_url_listbox.bind('<Delete>', lambda e: self.remove_selected_urls())
        
        btn_row = ttk.Frame(url_card)
        btn_row.pack(fill="x", pady=(10, 0))
        ttk.Button(btn_row, text="📋 从剪贴板添加", command=self.add_urls_from_clipboard).pack(side="left", padx=5)
        ttk.Button(btn_row, text="🔄 自动监听", command=self.show_auto_monitor_dialog).pack(side="left", padx=5)
        ttk.Button(btn_row, text="🗑️ 删除选中", command=self.remove_selected_urls).pack(side="left", padx=5)
        ttk.Button(btn_row, text="🧹 清空列表", command=self.clear_url_list).pack(side="left", padx=5)
        
        add_row = ttk.Frame(url_card)
        add_row.pack(fill="x", pady=(10, 0))
        self.literature_url_entry = ttk.Entry(add_row, font=("Microsoft YaHei", 9))
        self.literature_url_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Button(add_row, text="➕ 添加", command=self.add_single_url).pack(side="left")
        
        output_card = ttk.LabelFrame(left_column, text=" 📁 输出设置 ", padding=15)
        output_card.pack(fill="x", pady=10)
        
        output_row = ttk.Frame(output_card)
        output_row.pack(fill="x", pady=5)
        ttk.Label(output_row, text="保存目录:", style="Bold.TLabel").pack(side="left")
        self.literature_output_var = tk.StringVar(value="literature_downloads")
        ttk.Entry(output_row, textvariable=self.literature_output_var, width=40).pack(side="left", padx=10)
        ttk.Button(output_row, text="📁 浏览", command=self.select_literature_output).pack(side="left")
        
        subfolder_row = ttk.Frame(output_card)
        subfolder_row.pack(fill="x", pady=5)
        self.create_subfolder_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(subfolder_row, text="📁 每次下载创建新文件夹（避免覆盖）", 
                       variable=self.create_subfolder_var).pack(side="left")
        ttk.Label(subfolder_row, text="自动以时间戳命名", 
                 foreground="#7f8c8d", font=("Microsoft YaHei", 8)).pack(side="left", padx=10)
        
        action_card = ttk.LabelFrame(left_column, text=" 🚀 操作控制 ", padding=15)
        action_card.pack(fill="x", pady=10)
        
        control_row = ttk.Frame(action_card)
        control_row.pack(fill="x", pady=5)
        self.launch_browser_btn = ttk.Button(control_row, text="🚀 启动浏览器", 
                                             command=self.launch_browser, width=12)
        self.launch_browser_btn.pack(side="left", padx=(0, 5))
        ttk.Button(control_row, text="🔐 登录网站", command=self.show_login_menu, width=10).pack(side="left", padx=(0, 5))
        ttk.Button(control_row, text="📋 下载规则", command=self.show_download_rules, width=10).pack(side="left", padx=(0, 5))
        ttk.Button(control_row, text="⚙️ 设置", command=self.show_settings, width=8).pack(side="left", padx=(0, 5))
        ttk.Button(control_row, text="📖 用户手册", command=self.show_user_manual, width=10).pack(side="left")
        
        debug_row = ttk.Frame(action_card)
        debug_row.pack(fill="x", pady=5)
        self.debug_mode_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(debug_row, text="🐛 Debug模式（前台显示浏览器窗口）", 
                       variable=self.debug_mode_var).pack(side="left")
        
        mode_row = ttk.Frame(action_card)
        mode_row.pack(fill="x", pady=5)
        ttk.Label(mode_row, text="下载模式:", style="Bold.TLabel").pack(side="left")
        self.download_mode_var = tk.StringVar(value="html")
        ttk.Radiobutton(mode_row, text="📄 HTML", variable=self.download_mode_var, 
                       value="html").pack(side="left", padx=10)
        ttk.Radiobutton(mode_row, text="📑 PDF", variable=self.download_mode_var, 
                       value="pdf").pack(side="left", padx=10)
        ttk.Radiobutton(mode_row, text="📄📑 HTML+PDF", variable=self.download_mode_var, 
                       value="both").pack(side="left", padx=10)
        
        download_btn_row = ttk.Frame(action_card)
        download_btn_row.pack(fill="x", pady=5)
        
        self.literature_download_btn = ttk.Button(download_btn_row, text="📚 开始下载文献", 
                                                  command=self.show_download_options,
                                                  style="Success.TButton", width=16)
        self.literature_download_btn.pack(side="left", padx=(0, 5))
        
        self.literature_stop_btn = ttk.Button(download_btn_row, text="⏹ 终止", 
                                             command=self.stop_literature_download,
                                             state="disabled", width=10)
        self.literature_stop_btn.pack(side="right")
        
        self.literature_open_btn = ttk.Button(action_card, text="📂 打开下载目录", 
                                             command=self.open_literature_dir)
        self.literature_open_btn.pack(fill="x", pady=5)
        
        repair_btn_frame = ttk.Frame(action_card)
        repair_btn_frame.pack(fill="x", pady=5)
        
        self.literature_repair_btn = ttk.Button(repair_btn_frame, text="🔧 文献修复", 
                                               command=self.show_repair_options)
        self.literature_repair_btn.pack(fill="x")
        
        progress_frame = ttk.Frame(right_column)
        progress_frame.pack(fill="x", pady=(0, 5))
        
        self.literature_progress = ttk.Progressbar(
            progress_frame,
            mode='indeterminate',
            length=300
        )
        self.literature_progress.pack(side="left", padx=5)
        
        self.progress_label = ttk.Label(progress_frame, text="", foreground="#3498db")
        self.progress_label.pack(side="left")
        
        log_card = ttk.LabelFrame(right_column, text=" 📝 下载日志 ", padding=10)
        log_card.pack(fill="both", expand=True, pady=10)
        
        self.literature_log_area = scrolledtext.ScrolledText(log_card, height=30, 
                                                            state='disabled',
                                                            font=("Consolas", 9),
                                                            bg="#f8f9fa")
        self.literature_log_area.pack(fill="both", expand=True)
        self.literature_log_area.tag_config("success", foreground="#27ae60")
        self.literature_log_area.tag_config("error", foreground="#e74c3c")
        self.literature_log_area.tag_config("warning", foreground="#f39c12")
        self.literature_log_area.tag_config("info", foreground="#3498db")
        
        info_card = ttk.LabelFrame(right_column, text=" ℹ️ 使用说明 ", padding=15)
        info_card.pack(fill="both", expand=True, pady=10)
        
        info_text = """📚 文献下载功能说明：

每行输入一个网址，使用 Playwright 浏览器下载。

下载模式：
- HTML：保存为离线网页（默认）
- PDF：保存为PDF文档
- HTML+PDF：同时保存两种格式

功能特点：
- 自动处理登录弹窗
- 自动展开全文内容
- 内嵌图片和样式
- 完全离线可用

✅ 已完美支持网站：
- CSDN 博客（含海外 GDPR 弹窗）
- 知乎专栏/问答（自动展开全文）
- 掘金文章
- 简书文章
- 博客园
- 微信公众号
- 一般网站

💡 提示：
- 点击「启动浏览器」可观察下载过程
- 点击「连接已打开的浏览器」可复用登录态"""
        
        info_scroll = scrolledtext.ScrolledText(info_card, height=12,
                                                wrap="word", font=("Microsoft YaHei", 9),
                                                bg="#f8f9fa", state='normal')
        info_scroll.pack(fill="both", expand=True)
        info_scroll.insert("1.0", info_text)
        info_scroll.config(state='disabled')
    
    def literature_log(self, msg, tag="info"):
        self.literature_log_area.config(state='normal')
        timestamp = time.strftime("%H:%M:%S")
        self.literature_log_area.insert("end", f"[{timestamp}] {msg}\n", tag)
        self.literature_log_area.config(state='disabled')
        self.literature_log_area.see("end")
        self._save_literature_log(msg, tag)
    
    def _save_literature_log(self, msg, tag="info"):
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            logs_dir = os.path.join(base_dir, "logs")
            os.makedirs(logs_dir, exist_ok=True)
            
            import datetime
            current_date = datetime.datetime.now().strftime("%Y%m%d")
            log_file = os.path.join(logs_dir, f"literature_log_{current_date}.txt")
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] [{tag.upper()}] {msg}\n"
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except:
            pass
    
    def literature_log_update(self, msg, tag="info"):
        self.literature_log_area.config(state='normal')
        all_text = self.literature_log_area.get("1.0", "end-1c")
        lines = all_text.split('\n')
        if lines:
            last_line = lines[-1]
            if last_line.startswith('['):
                timestamp = last_line.split(']')[0] + ']'
                self.literature_log_area.delete(f"end-{len(last_line)}c", "end")
                self.literature_log_area.insert("end", f"{timestamp} {msg}\n", tag)
            else:
                timestamp = time.strftime("%H:%M:%S")
                self.literature_log_area.insert("end", f"[{timestamp}] {msg}\n", tag)
        else:
            timestamp = time.strftime("%H:%M:%S")
            self.literature_log_area.insert("end", f"[{timestamp}] {msg}\n", tag)
        self.literature_log_area.config(state='disabled')
        self.literature_log_area.see("end")
    
    def add_urls_from_clipboard(self):
        try:
            clipboard_text = self.root.clipboard_get()
            if not clipboard_text:
                return
            text = clipboard_text.replace('\r\n', '\n').replace('\r', '\n')
            urls = [url.strip() for url in text.split() if url.strip()]
            for url in urls:
                self.literature_url_listbox.insert(tk.END, url)
            self.literature_log(f"📋 已从剪贴板添加 {len(urls)} 个网址", "info")
        except Exception as e:
            self.literature_log(f"❌ 读取剪贴板失败: {e}", "error")
    
    def remove_selected_urls(self):
        selected_indices = self.literature_url_listbox.curselection()
        if not selected_indices:
            return
        for i in reversed(selected_indices):
            self.literature_url_listbox.delete(i)
        self.literature_log(f"🗑️ 已删除 {len(selected_indices)} 个网址", "info")
    
    def clear_url_list(self):
        self.literature_url_listbox.delete(0, tk.END)
        self.literature_log("🧹 已清空网址列表", "info")
    
    def add_single_url(self):
        url = self.literature_url_entry.get().strip()
        if url:
            self.literature_url_listbox.insert(tk.END, url)
            self.literature_url_entry.delete(0, tk.END)
            self.literature_log(f"➕ 已添加: {url}", "info")
    
    def show_auto_monitor_dialog(self):
        monitor_window = tk.Toplevel(self.root)
        monitor_window.title("自动监听剪贴板")
        monitor_window.geometry("600x550")
        monitor_window.resizable(False, False)
        monitor_window.attributes('-topmost', True)
        
        monitor_window.protocol("WM_DELETE_WINDOW", lambda: self.on_monitor_window_close(monitor_window))
        
        main_frame = ttk.Frame(monitor_window, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        title_label = ttk.Label(main_frame, text="🔄 自动监听剪贴板", 
                               font=("Microsoft YaHei", 14, "bold"),
                               foreground="#2c3e50")
        title_label.pack(pady=(0, 10))
        
        info_text = """自动监听会监听您的剪贴板，当您直接复制一个网页的时候，它就会自动加入。

使用说明：
• 在浏览器中复制任意网址
• 程序会自动检测并添加到列表
• 支持自动去重，避免重复添加

注意事项：
• 只识别有效的网页链接
• 每秒检查一次剪贴板
• 关闭此弹窗时，会自动关闭剪贴板监听功能"""
        
        info_frame = ttk.LabelFrame(main_frame, text=" ℹ️ 使用说明 ", padding=10)
        info_frame.pack(fill="x", pady=(0, 10))
        
        info_scroll = scrolledtext.ScrolledText(info_frame, height=6, 
                                          wrap="word", font=("Microsoft YaHei", 8),
                                          bg="#f8f9fa", state='disabled')
        info_scroll.pack(fill="both", expand=True)
        info_scroll.tag_config("info", foreground="#34495e")
        info_scroll.config(state='normal')
        info_scroll.insert("1.0", info_text, "info")
        info_scroll.config(state='disabled')
        
        list_frame = ttk.LabelFrame(main_frame, text=" 📋 监听到的网址 ", padding=10)
        list_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        self.monitor_url_listbox = tk.Listbox(
            list_frame,
            yscrollcommand=scrollbar.set,
            selectmode=tk.SINGLE,
            font=("Microsoft YaHei", 9),
            bg="#f8f9fa",
            activestyle="none",
            height=10
        )
        self.monitor_url_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.monitor_url_listbox.yview)
        
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill="x", pady=(0, 10))
        
        self.monitor_status_label = ttk.Label(status_frame, text="状态：未启动", 
                                           font=("Microsoft YaHei", 10, "bold"),
                                           foreground="#7f8c8d")
        self.monitor_status_label.pack(side="left")
        
        self.monitor_count_label = ttk.Label(status_frame, text="已添加：0 个", 
                                          font=("Microsoft YaHei", 10),
                                          foreground="#7f8c8d")
        self.monitor_count_label.pack(side="right")
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x")
        
        self.monitor_close_btn = ttk.Button(btn_frame, text="⏹ 关闭监听", 
                                          command=lambda: self.stop_monitor_from_dialog(monitor_window),
                                          width=15)
        self.monitor_close_btn.pack(side="left", padx=5)
        
        ttk.Button(btn_frame, text="❌ 关闭", 
                 command=lambda: self.on_monitor_window_close(monitor_window),
                 width=15).pack(side="right", padx=5)
        
        self.monitor_added_count = 0
        self.monitor_window = monitor_window
        
        self.start_monitor_from_dialog(monitor_window)
    
    def start_monitor_from_dialog(self, window):
        if not hasattr(self, '_clipboard_monitor_thread') or not self._clipboard_monitor_thread.is_alive():
            self._stop_monitor = False
            self._last_clipboard_text = ""
            self._clipboard_monitor_thread = threading.Thread(target=self._clipboard_monitor_loop, daemon=True)
            self._clipboard_monitor_thread.start()
            self.monitor_status_label.config(text="状态：运行中", foreground="#27ae60")
            self.monitor_close_btn.config(state="normal")
            self.monitor_added_count = 0
            self.monitor_count_label.config(text="已添加：0 个")
            self.literature_log("🔄 剪贴板监听已启动", "info")
    
    def stop_monitor_from_dialog(self, window):
        self._stop_monitor = True
        if hasattr(self, '_clipboard_monitor_thread'):
            self._clipboard_monitor_thread.join(timeout=1)
        self.monitor_status_label.config(text="状态：已停止", foreground="#7f8c8d")
        self.monitor_close_btn.config(state="disabled")
        self.literature_log("⏹ 剪贴板监听已停止", "info")
    
    def on_monitor_window_close(self, window):
        self.stop_monitor_from_dialog(window)
        window.destroy()
        if hasattr(self, 'monitor_window'):
            delattr(self, 'monitor_window')
    
    def _clipboard_monitor_loop(self):
        while not self._stop_monitor:
            try:
                current_text = self._safe_get_clipboard()
                if current_text and current_text != self._last_clipboard_text:
                    if self._looks_like_url(current_text):
                        self._last_clipboard_text = current_text
                        self.root.after(0, lambda t=current_text: self._add_single_url_auto(t))
                    else:
                        self._last_clipboard_text = current_text
            except Exception as e:
                pass
            time.sleep(1)
    
    def _safe_get_clipboard(self):
        try:
            return self.root.clipboard_get()
        except:
            return ""
    
    def _looks_like_url(self, text):
        text = text.strip()
        if not text:
            return False
        if text.startswith(('http://', 'https://')):
            return True
        if '.' in text and ' ' not in text and not text.startswith(('file:', 'mailto:')):
            return True
        return False
    
    def _add_single_url_auto(self, url):
        urls = list(self.literature_url_listbox.get(0, tk.END))
        if url not in urls:
            self.literature_url_listbox.insert(tk.END, url)
            self.literature_log(f"📋 自动添加: {url}", "info")
            if hasattr(self, 'monitor_added_count'):
                self.monitor_added_count += 1
            if hasattr(self, 'monitor_count_label'):
                self.monitor_count_label.config(text=f"已添加：{self.monitor_added_count} 个")
            if hasattr(self, 'monitor_url_listbox'):
                self.root.after(0, lambda u=url: self._add_to_monitor_list(u))
    
    def _add_to_monitor_list(self, url):
        if hasattr(self, 'monitor_url_listbox'):
            self.monitor_url_listbox.insert(tk.END, url)
            self.monitor_url_listbox.see(tk.END)
    
    def on_closing(self):
        self._stop_monitor = True
        if hasattr(self, '_clipboard_monitor_thread'):
            self._clipboard_monitor_thread.join(timeout=1)
        self.root.destroy()
    
    def select_literature_output(self):
        folder = filedialog.askdirectory()
        if folder:
            self.literature_output_var.set(folder)
    
    def open_literature_dir(self):
        output_dir = self.literature_output_var.get()
        if os.path.exists(output_dir):
            self.open_file_explorer(output_dir)
        else:
            messagebox.showinfo("提示", "目录不存在，请先下载文献")
    
    def show_repair_options(self):
        output_dir = self.literature_output_var.get()
        if not os.path.exists(output_dir):
            messagebox.showwarning("提示", "下载目录不存在，请先下载文献")
            return
        
        subdirs = [d for d in os.listdir(output_dir) 
                   if os.path.isdir(os.path.join(output_dir, d))]
        
        if not subdirs:
            messagebox.showinfo("提示", "未找到任何文献下载目录")
            return
        
        repair_dialog = tk.Toplevel(self.root)
        repair_dialog.title("🔧 文献修复")
        repair_dialog.geometry("550x550")
        repair_dialog.transient(self.root)
        repair_dialog.grab_set()
        
        main_frame = ttk.Frame(repair_dialog, padding=15)
        main_frame.pack(fill="both", expand=True)
        
        ttk.Label(main_frame, text="文献修复工具", font=("Microsoft YaHei UI", 14, "bold")).pack(anchor="w")
        ttk.Label(main_frame, text="自动检测并修复文献目录结构", foreground="#7f8c8d").pack(anchor="w", pady=(0, 10))
        
        ttk.Separator(main_frame, orient="horizontal").pack(fill="x", pady=10)
        
        ttk.Label(main_frame, text="选择要修复的目录：", font=("Microsoft YaHei UI", 10, "bold")).pack(anchor="w")
        
        list_frame = ttk.Frame(main_frame)
        list_frame.pack(fill="both", expand=True, pady=10)
        
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        dir_listbox = tk.Listbox(list_frame, selectmode="multiple", yscrollcommand=scrollbar.set,
                                 font=("Microsoft YaHei UI", 9))
        dir_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=dir_listbox.yview)
        
        for subdir in sorted(subdirs, reverse=True):
            pages_path = os.path.join(output_dir, subdir, "pages")
            if os.path.exists(pages_path):
                html_count = len([f for f in os.listdir(pages_path) if f.endswith('.html')])
                dir_listbox.insert("end", f"{subdir} ({html_count} 篇文章)")
            else:
                dir_listbox.insert("end", f"{subdir} (无pages目录)")
        
        ttk.Separator(main_frame, orient="horizontal").pack(fill="x", pady=10)
        
        ttk.Label(main_frame, text="修复选项：", font=("Microsoft YaHei UI", 10, "bold")).pack(anchor="w")
        
        repair_toc_var = tk.BooleanVar(value=True)
        repair_index_var = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(main_frame, text="重新生成悬浮目录（修复文章间跳转）", 
                       variable=repair_toc_var).pack(anchor="w", pady=2)
        ttk.Checkbutton(main_frame, text="重新生成文献合集主页", 
                       variable=repair_index_var).pack(anchor="w", pady=2)
        
        ttk.Separator(main_frame, orient="horizontal").pack(fill="x", pady=10)
        
        custom_frame = ttk.LabelFrame(main_frame, text=" 自定义设置 ", padding=10)
        custom_frame.pack(fill="x", pady=5)
        
        title_frame = ttk.Frame(custom_frame)
        title_frame.pack(fill="x", pady=5)
        ttk.Label(title_frame, text="合集标题：").pack(side="left")
        custom_title_var = tk.StringVar(value="文献合集")
        ttk.Entry(title_frame, textvariable=custom_title_var, width=30).pack(side="left", padx=5)
        
        ttk.Label(custom_frame, text="目录颜色主题：", font=("Microsoft YaHei UI", 9)).pack(anchor="w", pady=(10, 5))
        
        repair_theme_var = tk.StringVar(value="colorful")
        theme_row = ttk.Frame(custom_frame)
        theme_row.pack(fill="x", pady=5)
        ttk.Radiobutton(theme_row, text="🎨 彩色", variable=repair_theme_var, value="colorful").pack(side="left", padx=10)
        ttk.Radiobutton(theme_row, text="🌙 深色", variable=repair_theme_var, value="dark").pack(side="left", padx=10)
        ttk.Radiobutton(theme_row, text="⚪ 白色", variable=repair_theme_var, value="white").pack(side="left", padx=10)
        ttk.Radiobutton(theme_row, text="🔵 蓝色", variable=repair_theme_var, value="blue").pack(side="left", padx=10)
        
        custom_color_var = tk.BooleanVar(value=False)
        custom_color_frame = ttk.Frame(custom_frame)
        custom_color_frame.pack(fill="x", pady=5)
        
        ttk.Checkbutton(custom_color_frame, text="自定义颜色：", variable=custom_color_var,
                       command=lambda: toggle_custom_color()).pack(side="left")
        
        custom_color_picker_frame = ttk.Frame(custom_color_frame)
        custom_color_picker_frame.pack(side="left", padx=5)
        
        ttk.Label(custom_color_picker_frame, text="主色：").pack(side="left")
        primary_color_var = tk.StringVar(value="#667eea")
        primary_color_btn = tk.Button(custom_color_picker_frame, bg=primary_color_var.get(), width=3, height=1)
        primary_color_btn.pack(side="left", padx=2)
        
        ttk.Label(custom_color_picker_frame, text="背景：").pack(side="left", padx=(10, 0))
        bg_color_var = tk.StringVar(value="#ffffff")
        bg_color_btn = tk.Button(custom_color_picker_frame, bg=bg_color_var.get(), width=3, height=1)
        bg_color_btn.pack(side="left", padx=2)
        
        ttk.Label(custom_color_picker_frame, text="文字：").pack(side="left", padx=(10, 0))
        text_color_var = tk.StringVar(value="#333333")
        text_color_btn = tk.Button(custom_color_picker_frame, bg=text_color_var.get(), width=3, height=1)
        text_color_btn.pack(side="left", padx=2)
        
        def pick_color(color_var, btn):
            from tkinter import colorchooser
            color = colorchooser.askcolor(color=color_var.get(), title="选择颜色")
            if color[1]:
                color_var.set(color[1])
                btn.config(bg=color[1])
        
        primary_color_btn.config(command=lambda: pick_color(primary_color_var, primary_color_btn))
        bg_color_btn.config(command=lambda: pick_color(bg_color_var, bg_color_btn))
        text_color_btn.config(command=lambda: pick_color(text_color_var, text_color_btn))
        
        def toggle_custom_color():
            state = "normal" if custom_color_var.get() else "disabled"
            primary_color_btn.config(state=state)
            bg_color_btn.config(state=state)
            text_color_btn.config(state=state)
        
        toggle_custom_color()
        
        log_frame = ttk.LabelFrame(main_frame, text=" 修复日志 ", padding=5)
        log_frame.pack(fill="both", expand=True, pady=10)
        
        repair_log = scrolledtext.ScrolledText(log_frame, height=6, state='disabled',
                                               font=("Consolas", 9))
        repair_log.pack(fill="both", expand=True)
        repair_log.tag_config("success", foreground="#27ae60")
        repair_log.tag_config("error", foreground="#e74c3c")
        repair_log.tag_config("info", foreground="#3498db")
        
        def log_message(msg, tag="info"):
            repair_log.config(state='normal')
            repair_log.insert("end", msg + "\n", tag)
            repair_log.see("end")
            repair_log.config(state='disabled')
        
        def get_theme_config():
            if custom_color_var.get():
                return {
                    "header_bg": f"linear-gradient(135deg, {primary_color_var.get()} 0%, {primary_color_var.get()} 100%)",
                    "panel_bg": f"rgba({int(bg_color_var.get()[1:3], 16)}, {int(bg_color_var.get()[3:5], 16)}, {int(bg_color_var.get()[5:7], 16)}, 0.98)",
                    "item_bg": bg_color_var.get(),
                    "item_hover_bg": bg_color_var.get(),
                    "item_hover_border": primary_color_var.get(),
                    "title_color": text_color_var.get(),
                    "source_color": "#7f8c8d",
                    "float_btn_bg": f"linear-gradient(135deg, {primary_color_var.get()} 0%, {primary_color_var.get()} 100%)",
                    "shadow": "0 8px 32px rgba(0, 0, 0, 0.3)"
                }
            return repair_theme_var.get()
        
        def do_repair():
            selections = dir_listbox.curselection()
            if not selections:
                messagebox.showwarning("提示", "请选择至少一个目录")
                return
            
            repair_btn.config(state="disabled")
            log_message("开始修复...", "info")
            
            try:
                for idx in selections:
                    selected_text = dir_listbox.get(idx)
                    dir_name = selected_text.split(" (")[0]
                    dir_path = os.path.join(output_dir, dir_name)
                    pages_dir = os.path.join(dir_path, "pages")
                    
                    if not os.path.exists(pages_dir):
                        log_message(f"跳过 {dir_name}: 无pages目录", "error")
                        continue
                    
                    html_files = [f for f in os.listdir(pages_dir) if f.endswith('.html')]
                    
                    if not html_files:
                        log_message(f"跳过 {dir_name}: 无HTML文件", "error")
                        continue
                    
                    log_message(f"正在修复 {dir_name} ({len(html_files)} 篇文章)...", "info")
                    
                    theme_config = get_theme_config()
                    
                    if repair_toc_var.get():
                        log_message("  - 重新生成悬浮目录...", "info")
                        if isinstance(theme_config, dict):
                            self._inject_floating_toc_to_pages_custom(pages_dir, html_files, theme_config)
                        else:
                            self._inject_floating_toc_to_pages(pages_dir, html_files, theme_config)
                        log_message("  ✓ 悬浮目录已更新", "success")
                    
                    if repair_index_var.get():
                        log_message("  - 重新生成文献合集...", "info")
                        config = {
                            'title': custom_title_var.get(),
                            'create_time': dir_name.split('_')[0] + '-' + dir_name.split('_')[1][:2] + '-' + dir_name.split('_')[1][2:4]
                        }
                        pack_html = self.generate_packed_html(pages_dir, html_files, config)
                        pack_path = os.path.join(dir_path, "文献合集.html")
                        with open(pack_path, 'w', encoding='utf-8') as f:
                            f.write(pack_html)
                        log_message("  ✓ 文献合集已更新", "success")
                    
                    log_message(f"✓ {dir_name} 修复完成", "success")
                
                log_message("\n所有修复完成！", "success")
                messagebox.showinfo("完成", "文献修复完成！")
            except Exception as e:
                log_message(f"修复出错: {e}", "error")
                messagebox.showerror("错误", f"修复过程中出错: {e}")
            finally:
                repair_btn.config(state="normal")
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=10)
        
        ttk.Button(btn_frame, text="全选", 
                  command=lambda: dir_listbox.select_set(0, "end")).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="取消全选", 
                  command=lambda: dir_listbox.select_clear(0, "end")).pack(side="left", padx=5)
        
        repair_btn = ttk.Button(btn_frame, text="🔧 开始修复", command=do_repair,
                               style="Success.TButton")
        repair_btn.pack(side="right", padx=5)
        ttk.Button(btn_frame, text="关闭", command=repair_dialog.destroy).pack(side="right", padx=5)
    
    def _is_browser_running(self):
        if not hasattr(self, '_browser_context') or self._browser_context is None:
            return False
        try:
            pages = self._browser_context.pages
            
            if not pages or len(pages) == 0:
                self._browser_context = None
                return False
            
            test_page = pages[0]
            try:
                _ = test_page.evaluate("1+1")
                return True
            except:
                self._browser_context = None
                return False
                
        except:
            self._browser_context = None
            return False
    
    def _check_browser_on_startup(self):
        pass
    
    def _start_browser_with_url(self, url=None):
        import threading
        
        if self._is_browser_running():
            try:
                if self._browser_context.pages:
                    page = self._browser_context.pages[0]
                else:
                    page = self._browser_context.new_page()
                
                if url:
                    self.literature_log(f"复用现有浏览器打开: {url[:50]}...", "info")
                    page.goto(url, timeout=30000)
                    self.literature_log("✅ 页面已打开", "success")
                else:
                    self.literature_log("浏览器已在运行中", "info")
                return True
            except Exception as e:
                self.literature_log(f"复用浏览器失败，将启动新实例: {e}", "warning")
                self._browser_context = None
        
        def run_browser():
            try:
                browser_type = self._get_actual_browser_type()
                
                if browser_type in ['chrome', 'msedge', 'firefox']:
                    browser_names = {
                        'chrome': 'Google Chrome',
                        'msedge': 'Microsoft Edge',
                        'firefox': 'Firefox'
                    }
                    browser_name = browser_names.get(browser_type, browser_type)
                    self.root.after(0, lambda: self.literature_log(f"使用系统浏览器: {browser_name}", "info"))
                else:
                    from browser_manager import setup_browser_env, is_browser_ready
                    setup_browser_env()
                    
                    if not is_browser_ready():
                        self.root.after(0, lambda: self.literature_log("❌ 浏览器未安装，请先下载", "error"))
                        self.root.after(0, lambda: messagebox.showwarning(
                            "浏览器未安装",
                            "请先下载内置浏览器。\n\n点击「启动浏览器」按钮时会自动提示下载。"
                        ))
                        return
                
                from playwright.sync_api import sync_playwright
                
                if is_frozen():
                    browser_data_dir = os.path.join(get_base_path(), "browser_data")
                else:
                    browser_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "browser_data")
                
                p = sync_playwright().start()
                
                if browser_type == "internal":
                    channels_to_try = [None]
                elif browser_type in ['chrome', 'msedge']:
                    channels_to_try = [browser_type, None]
                else:
                    channels_to_try = ['msedge', 'chrome', None]
                
                browser_launched = False
                for channel in channels_to_try:
                    try:
                        launch_kwargs = {
                            'user_data_dir': browser_data_dir,
                            'headless': False,
                            'viewport': {'width': 1200, 'height': 800},
                            'args': [
                                '--window-position=360,140',
                                '--no-first-run',
                                '--no-default-browser-check',
                                '--disable-blink-features=AutomationControlled'
                            ],
                            'ignore_default_args': ['--enable-automation']
                        }
                        if channel:
                            launch_kwargs['channel'] = channel
                            browser_name = 'Edge' if channel == 'msedge' else 'Chrome'
                        else:
                            browser_name = '内置Chromium'
                        
                        self._browser_context = p.chromium.launch_persistent_context(**launch_kwargs)
                        self.root.after(0, lambda bn=browser_name: self.literature_log(f"✅ {bn} 浏览器已启动", "success"))
                        browser_launched = True
                        break
                    except Exception as e:
                        if channel:
                            self.root.after(0, lambda bn=browser_name, err=e: self.literature_log(f"{bn} 启动失败: {err}", "warning"))
                        continue
                
                if not browser_launched:
                    self.root.after(0, lambda: self.literature_log("❌ 无法启动任何浏览器", "error"))
                    return
                
                if len(self._browser_context.pages) > 0:
                    page = self._browser_context.pages[0]
                else:
                    page = self._browser_context.new_page()
                
                if url:
                    try:
                        page.goto(url, timeout=30000)
                    except Exception as e:
                        print(f"打开页面错误: {e}")
                
                while True:
                    import time
                    time.sleep(1)
                    try:
                        _ = self._browser_context.pages
                    except:
                        break
                
            except Exception as e:
                print(f"浏览器启动错误: {e}")
                self.root.after(0, lambda: self.literature_log(f"❌ 浏览器启动错误: {e}", "error"))
        
        threading.Thread(target=run_browser, daemon=True).start()
        return True
    
    def launch_browser(self):
        try:
            from playwright_downloader import PlaywrightDownloader
            browser_type = self._get_actual_browser_type()
            
            if self._pw_downloader and self._pw_downloader.connected:
                try:
                    if self._pw_downloader.context and self._pw_downloader.context.pages:
                        self.literature_log("✅ 浏览器已在运行中，复用现有实例", "success")
                        hwnd = get_browser_hwnd()
                        if hwnd:
                            set_window_top(hwnd)
                        return
                    else:
                        self._pw_downloader.connected = False
                        self._pw_downloader = None
                except:
                    self._pw_downloader = None
            
            if browser_type in ['chrome', 'msedge', 'firefox']:
                browser_names = {
                    'chrome': 'Google Chrome',
                    'msedge': 'Microsoft Edge',
                    'firefox': 'Firefox'
                }
                browser_name = browser_names.get(browser_type, browser_type)
                self.literature_log(f"使用系统浏览器: {browser_name}", "info")
            else:
                from browser_manager import setup_browser_env, is_browser_ready
                setup_browser_env()
                
                if not is_browser_ready():
                    result = messagebox.askyesno(
                        "浏览器未安装",
                        "您需要下载内置浏览器才能使用此功能。\n\n"
                        "程序将从官方源下载浏览器（约300MB）。\n\n"
                        "是否现在下载？",
                        icon='question'
                    )
                    if result:
                        self.show_browser_env_manager(auto_start_download=True)
                    return
            
            self._pw_downloader = PlaywrightDownloader(gui=self, browser_type=browser_type)
            result = self._pw_downloader._ensure_browser(headless=False)
            
            if result == True:
                self.literature_log("✅ 浏览器已启动", "success")
                self.literature_log("💡 浏览器在独立窗口运行，关闭窗口即可退出", "info")
            elif result == "need_download":
                self.literature_log("❌ 浏览器未安装，请先下载", "error")
            else:
                self.literature_log("❌ 浏览器启动失败", "error")
                
        except Exception as e:
            self.literature_log(f"❌ 启动错误: {str(e)}", "error")
    
    def show_login_menu(self):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="📘 知乎", command=lambda: self.login_site('zhihu'))
        menu.add_command(label="📙 CSDN", command=lambda: self.login_site('csdn'))
        menu.add_command(label="📕 掘金", command=lambda: self.login_site('juejin'))
        menu.add_command(label="📗 简书", command=lambda: self.login_site('jianshu'))
        menu.add_separator()
        menu.add_command(label="ℹ️ 关于登录安全", command=self.show_login_info)
        
        try:
            menu.tk_popup(self.root.winfo_pointerx(), self.root.winfo_pointery())
        finally:
            menu.grab_release()
    
    def show_login_info(self):
        info = """🔐 登录安全说明

• 登录数据全部存储在您的本地电脑
• 程序不会联网获取或上传任何登录信息
• 数据保存在程序目录的 browser_data 文件夹
• 您可以随时删除该文件夹清除登录状态

支持登录的网站：
• 知乎 - 可下载完整回答内容
• CSDN - 可跳过广告和登录提示
• 掘金 - 可下载完整文章
• 简书 - 可下载完整文章"""
        messagebox.showinfo("登录安全说明", info)
    
    def login_site(self, site):
        try:
            sites = {
                'zhihu': 'https://www.zhihu.com/signin',
                'csdn': 'https://passport.csdn.net/login',
                'juejin': 'https://juejin.cn/passport/login',
                'jianshu': 'https://www.jianshu.com/sign_in'
            }
            
            url = sites.get(site, sites['zhihu'])
            site_names = {'zhihu': '知乎', 'csdn': 'CSDN', 'juejin': '掘金', 'jianshu': '简书'}
            
            self.literature_log(f"正在打开 {site_names.get(site, site)} 登录页面...", "info")
            
            result = self._start_browser_with_url(url)
            if result:
                self.literature_log(f"✅ 已打开 {site_names.get(site, site)} 登录页面", "success")
                self.literature_log("💡 请在浏览器中完成登录，登录状态将自动保存", "info")
            else:
                self.literature_log("❌ 打开登录页面失败（浏览器进程已退出）", "error")
                
        except Exception as e:
            import traceback
            self.literature_log(f"❌ 打开登录页面失败: {str(e)}", "error")
            self.literature_log(traceback.format_exc(), "error")
    
    def show_download_rules(self):
        rules_window = tk.Toplevel(self.root)
        rules_window.title("下载规则配置")
        rules_window.geometry("500x400")
        rules_window.resizable(False, False)
        
        main_frame = ttk.Frame(rules_window, padding=15)
        main_frame.pack(fill="both", expand=True)
        
        ttk.Label(main_frame, text="📋 下载规则配置", font=("Microsoft YaHei", 14, "bold")).pack(pady=(0, 10))
        
        ttk.Label(main_frame, text="网址匹配规则：根据网址自动选择下载脚本", 
                 foreground="#7f8c8d").pack(pady=(0, 10))
        
        rules_frame = ttk.LabelFrame(main_frame, text="已配置规则", padding=10)
        rules_frame.pack(fill="both", expand=True, pady=5)
        
        rules_data = [
            ("zhihu.com", "知乎脚本", "✅ 已配置", "#27ae60"),
            ("csdn.net", "CSDN脚本", "⚠️ 需优化", "#f39c12"),
            ("juejin.cn", "通用脚本", "❌ 待配置", "#e74c3c"),
            ("jianshu.com", "通用脚本", "❌ 待配置", "#e74c3c"),
            ("其他网址", "通用脚本", "❌ 基础功能", "#e74c3c"),
        ]
        
        for pattern, script, status, color in rules_data:
            row = ttk.Frame(rules_frame)
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=pattern, width=15).pack(side="left")
            ttk.Label(row, text=script, width=15).pack(side="left")
            ttk.Label(row, text=status, foreground=color).pack(side="left")
        
        ttk.Separator(main_frame, orient="horizontal").pack(fill="x", pady=10)
        
        ttk.Label(main_frame, text="脚本说明：", font=("Microsoft YaHei", 10, "bold")).pack(anchor="w")
        ttk.Label(main_frame, text="• 知乎脚本：自动展开回答、隐藏登录提示、滚动加载图片", 
                 foreground="#7f8c8d").pack(anchor="w")
        ttk.Label(main_frame, text="• CSDN脚本：⚠️ 反爬严格，建议手动登录后下载", 
                 foreground="#f39c12").pack(anchor="w")
        ttk.Label(main_frame, text="• 通用脚本：❌ 基础功能，部分网站可能无法下载", 
                 foreground="#e74c3c").pack(anchor="w")
        
        ttk.Button(main_frame, text="关闭", command=rules_window.destroy).pack(pady=10)
    
    def show_settings(self):
        settings_window = tk.Toplevel(self.root)
        settings_window.title("⚙️ 设置")
        settings_window.geometry("550x450")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        main_frame = ttk.Frame(settings_window, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        data_frame = ttk.LabelFrame(main_frame, text=" 📁 用户数据管理 ", padding=15)
        data_frame.pack(fill="x", pady=10)
        
        if is_frozen():
            browser_data_dir = os.path.join(get_base_path(), "browser_data")
        else:
            browser_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "browser_data")
        
        ttk.Label(data_frame, text="浏览器数据目录:").pack(anchor="w")
        ttk.Label(data_frame, text=browser_data_dir, foreground="#3498db").pack(anchor="w")
        ttk.Label(data_frame, text="（包含登录状态、Cookies、浏览记录等）", 
                 foreground="#7f8c8d", font=("Microsoft YaHei", 8)).pack(anchor="w")
        
        def open_browser_data_dir():
            if os.path.exists(browser_data_dir):
                self.open_file_explorer(browser_data_dir)
            else:
                messagebox.showinfo("提示", "目录不存在（浏览器启动后会自动创建）")
        
        def clear_browser_data():
            if os.path.exists(browser_data_dir):
                if messagebox.askyesno("确认", "确定要清除浏览器数据吗？\n这将删除所有登录状态和浏览记录。"):
                    import shutil
                    try:
                        shutil.rmtree(browser_data_dir)
                        messagebox.showinfo("成功", "浏览器数据已清除")
                    except Exception as e:
                        messagebox.showerror("错误", f"清除失败: {e}")
            else:
                messagebox.showinfo("提示", "目录不存在，无需清除")
        
        btn_frame = ttk.Frame(data_frame)
        btn_frame.pack(fill="x", pady=10)
        ttk.Button(btn_frame, text="📂 打开目录", command=open_browser_data_dir, width=12).pack(side="left", padx=(0, 10))
        ttk.Button(btn_frame, text="🗑️ 清除数据", command=clear_browser_data, width=12).pack(side="left")
        
        test_frame = ttk.LabelFrame(main_frame, text=" 🧪 测试工具 ", padding=15)
        test_frame.pack(fill="x", pady=10)
        
        test_btn_row = ttk.Frame(test_frame)
        test_btn_row.pack(fill="x", pady=5)
        ttk.Button(test_btn_row, text="🧪 软件测试", command=self.show_software_test, width=15).pack(side="left", padx=(0, 10))
        ttk.Button(test_btn_row, text="🌐 网站测试", command=self.show_website_test, width=15).pack(side="left")
        
        ttk.Label(test_frame, text="软件测试：检测浏览器环境、Python依赖、文件系统权限等", 
                 foreground="#7f8c8d", font=("Microsoft YaHei", 8)).pack(anchor="w", pady=(5, 0))
        ttk.Label(test_frame, text="网站测试：测试特定网站的下载功能是否正常", 
                 foreground="#7f8c8d", font=("Microsoft YaHei", 8)).pack(anchor="w")
        
        ttk.Button(main_frame, text="关闭", command=settings_window.destroy, width=10).pack(pady=10)
    
    def show_user_manual(self):
        try:
            from manual_data import MANUAL_DATA
            from user_manual import UserManual
            
            if not hasattr(self, '_user_manual'):
                self._user_manual = UserManual(self.root, MANUAL_DATA)
            
            self._user_manual.show_manual()
        except ImportError:
            messagebox.showerror("错误", "用户手册模块未找到")
        except Exception as e:
            messagebox.showerror("错误", f"打开用户手册失败: {str(e)}")
    
    def show_download_options(self):
        urls = list(self.literature_url_listbox.get(0, tk.END))
        if not urls:
            messagebox.showwarning("警告", "请添加至少一个网址！")
            return
        
        need_verify_sites = []
        for url in urls:
            if 'csdn.net' in url.lower():
                if 'csdn' not in [s[0] for s in need_verify_sites]:
                    need_verify_sites.append(('csdn', 'CSDN', url))
            elif 'zhihu.com' in url.lower():
                if 'zhihu' not in [s[0] for s in need_verify_sites]:
                    need_verify_sites.append(('zhihu', '知乎', url))
        
        if need_verify_sites:
            verify_window = tk.Toplevel(self.root)
            verify_window.title("安全验证提示")
            verify_window.geometry("550x700")
            verify_window.resizable(False, False)
            
            verify_browser_threads = []
            
            def on_verify_window_close():
                for thread in verify_browser_threads:
                    if thread.is_alive():
                        pass
                verify_window.destroy()
            
            verify_window.protocol("WM_DELETE_WINDOW", on_verify_window_close)
            
            main_frame = ttk.Frame(verify_window, padding=20)
            main_frame.pack(fill="both", expand=True)
            
            ttk.Label(main_frame, text="⚠️ 检测到需要验证的网站", 
                     font=("Microsoft YaHei", 14, "bold")).pack(pady=(0, 10))
            
            ttk.Label(main_frame, text="以下网站可能需要人工通过安全验证（如滑块验证）：", 
                     foreground="#7f8c8d").pack(pady=(0, 5))
            
            ttk.Label(main_frame, text="⚠️ 重要提示：验证完成后请手动关闭浏览器窗口，登录状态会自动保存", 
                     foreground="#e74c3c", font=("Microsoft YaHei", 9, "bold")).pack(pady=(0, 10))
            
            verify_status = {'done': set()}
            self._verify_status = verify_status
            
            def skip_site(key, name, url, frame):
                if messagebox.askyesno("确认跳过", 
                    f"跳过 {name} 可能导致：\n\n"
                    "• 下载到验证码页面而非实际内容\n"
                    "• 下载到登录提示页面\n"
                    "• 内容不完整\n\n"
                    "确定要跳过此网站吗？"):
                    verify_status['done'].add(key)
                    for widget in frame.winfo_children():
                        widget.destroy()
                    ttk.Label(frame, text="✅ 已跳过", foreground="#27ae60", 
                             font=("Microsoft YaHei", 9, "bold")).pack(anchor="w")
                    if len(verify_status['done']) == len(need_verify_sites):
                        verify_window.after(100, lambda: self._continue_download_after_verify(verify_window, urls, need_verify_sites))
            
            for site_key, site_name, site_url in need_verify_sites:
                site_frame = ttk.LabelFrame(main_frame, text=f" {site_name} ", padding=10)
                site_frame.pack(fill="x", pady=5)
                
                url_label = ttk.Label(site_frame, text=f"网址: {site_url[:50]}...", 
                         foreground="#7f8c8d")
                url_label.pack(anchor="w")
                
                status_label = ttk.Label(site_frame, text="⏳ 待验证", foreground="#f39c12")
                status_label.pack(anchor="w", pady=(5, 0))
                
                def open_verify_in_browser(url=site_url, key=site_key, label=status_label):
                    try:
                        import threading
                        
                        def run_browser():
                            browser = None
                            p = None
                            try:
                                browser_type = self._get_actual_browser_type()
                                
                                if browser_type not in ['chrome', 'msedge', 'firefox']:
                                    from browser_manager import setup_browser_env, is_browser_ready
                                    setup_browser_env()
                                    
                                    if not is_browser_ready():
                                        label.config(text="❌ 浏览器未安装，请先下载", foreground="#e74c3c")
                                        return
                                
                                from playwright.sync_api import sync_playwright
                                
                                if is_frozen():
                                    browser_data_dir = os.path.join(get_base_path(), "browser_data")
                                else:
                                    browser_data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "browser_data")
                                
                                p = sync_playwright().start()
                                
                                if browser_type == "internal":
                                    channels_to_try = [None]
                                elif browser_type in ['chrome', 'msedge']:
                                    channels_to_try = [browser_type, None]
                                else:
                                    channels_to_try = ['msedge', 'chrome', None]
                                
                                browser_launched = False
                                for channel in channels_to_try:
                                    try:
                                        launch_kwargs = {
                                            'user_data_dir': browser_data_dir,
                                            'headless': False,
                                            'viewport': {'width': 1920, 'height': 1080},
                                            'args': [
                                                '--start-maximized',
                                                '--no-first-run',
                                                '--no-default-browser-check',
                                                '--disable-blink-features=AutomationControlled'
                                            ],
                                            'ignore_default_args': ['--enable-automation']
                                        }
                                        if channel:
                                            launch_kwargs['channel'] = channel
                                        browser = p.chromium.launch_persistent_context(**launch_kwargs)
                                        browser_launched = True
                                        break
                                    except:
                                        continue
                                
                                if not browser_launched:
                                    label.config(text="❌ 无法启动浏览器", foreground="#e74c3c")
                                    return
                                
                                if len(browser.pages) > 0:
                                    page = browser.pages[0]
                                else:
                                    page = browser.new_page()
                                page.goto(url)
                                label.config(text="⏳ 请在浏览器中完成验证...", foreground="#f39c12")
                                
                                verify_count = 0
                                max_verify = 10
                                verified = False
                                
                                while True:
                                    page.wait_for_timeout(1000)
                                    
                                    try:
                                        page_content = page.content()
                                        page_title = page.title()
                                        
                                        has_captcha = (
                                            "请完成安全验证" in page_content or
                                            "Security Verification" in page_content or
                                            "layui-layer" in page_content or
                                            "slide_v2" in page_content or
                                            "请拖动滑块" in page_content or
                                            "请求存在异常" in page_content or
                                            "暂时限制本次访问" in page_content or
                                            '"code":40362' in page_content
                                        )
                                        
                                        if has_captcha:
                                            verify_count += 1
                                            if "请求存在异常" in page_content or "暂时限制本次访问" in page_content or '"code":40362' in page_content:
                                                label.config(text="⚠️ 访问过于频繁，请稍后再试", foreground="#e74c3c")
                                            elif verify_count <= max_verify:
                                                label.config(text=f"⚠️ 检测到验证页面，请完成滑块验证 ({verify_count})", foreground="#e67e22")
                                            else:
                                                label.config(text="⚠️ 验证次数较多，请耐心完成", foreground="#e67e22")
                                        else:
                                            if "csdn.net" in url.lower():
                                                if "blog.csdn.net" in page.url or "article" in page.url:
                                                    label.config(text="✅ CSDN验证通过！正在关闭浏览器...", foreground="#27ae60")
                                                    verified = True
                                                else:
                                                    label.config(text="⏳ 页面加载中...", foreground="#3498db")
                                            elif "zhihu.com" in url.lower():
                                                if "404" not in page_title and "signin" not in page.url:
                                                    label.config(text="✅ 知乎验证通过！正在关闭浏览器...", foreground="#27ae60")
                                                    verified = True
                                                else:
                                                    label.config(text="⏳ 页面加载中...", foreground="#3498db")
                                            else:
                                                label.config(text="✅ 页面加载完成！正在关闭浏览器...", foreground="#27ae60")
                                                verified = True
                                            
                                            if verified:
                                                page.wait_for_timeout(2000)
                                                browser.close()
                                                p.stop()
                                                label.config(text="✅ 浏览器已关闭，登录状态已保存", foreground="#27ae60")
                                                break
                                    except:
                                        pass
                                        
                            except Exception as e:
                                error_str = str(e)
                                if "Target page" in error_str or "has been closed" in error_str or "disconnected" in error_str:
                                    label.config(text="✅ 浏览器已关闭，登录状态已保存", foreground="#27ae60")
                                else:
                                    label.config(text=f"❌ 错误: {str(e)[:30]}", foreground="#e74c3c")
                                    print(f"验证浏览器错误: {e}")
                            finally:
                                if p:
                                    try:
                                        p.stop()
                                    except:
                                        pass
                        
                        thread = threading.Thread(target=run_browser, daemon=True)
                        verify_browser_threads.append(thread)
                        thread.start()
                        label.config(text="⏳ 正在打开浏览器...", foreground="#3498db")
                    except Exception as e:
                        label.config(text=f"❌ 打开失败: {str(e)}", foreground="#e74c3c")
                        print(f"打开验证浏览器失败: {e}")
                
                btn_frame = ttk.Frame(site_frame)
                btn_frame.pack(fill="x", pady=5)
                ttk.Button(btn_frame, text="🌐 打开浏览器验证", command=open_verify_in_browser).pack(side="left")
                ttk.Button(btn_frame, text="🚫 跳过该网站", 
                         command=lambda f=site_frame, k=site_key, n=site_name, u=site_url: skip_site(k, n, u, f)).pack(side="right", padx=5)
                ttk.Label(btn_frame, text="使用已登录的浏览器数据", 
                         foreground="#7f8c8d", font=("Microsoft YaHei", 8)).pack(side="left", padx=10)
            
            ttk.Separator(main_frame, orient="horizontal").pack(fill="x", pady=15)
            
            ttk.Label(main_frame, text="💡 提示：完成验证后关闭浏览器窗口，然后点击下方按钮继续", 
                     foreground="#3498db").pack(pady=(0, 5))
            ttk.Label(main_frame, text="⚠️ 跳过验证可能导致下载到错误页面或验证码页面", 
                     foreground="#e74c3c").pack(pady=(0, 10))
            
            def continue_download():
                if messagebox.askyesno("确认继续", 
                    "请确保：\n\n"
                    "✅ 已完成所有验证\n"
                    "✅ 已手动关闭所有浏览器窗口\n\n"
                    "如果浏览器窗口未关闭，登录状态可能无法保存\n\n"
                    "确定要继续下载吗？"):
                    verify_window.destroy()
                    self._show_download_mode_selection(urls)
            
            def skip_verify():
                if messagebox.askyesno("确认跳过", 
                    "跳过验证可能导致：\n\n"
                    "• 下载到验证码页面而非实际内容\n"
                    "• 下载到登录提示页面\n"
                    "• 内容不完整\n\n"
                    "确定要跳过验证吗？"):
                    verify_window.destroy()
                    self._show_download_mode_selection(urls)
            
            def skip_download():
                if messagebox.askyesno("确认跳过下载", 
                    "跳过下载将不下载需要验证的网站，\n\n"
                    "包括：\n" + 
                    "\n".join([f"• {site_name}: {url[:40]}..." for _, site_name, url in need_verify_sites]) +
                    "\n\n确定要跳过这些网站吗？"):
                    verify_window.destroy()
                    filtered_urls = [url for url in urls if not any(site_key in url.lower() for site_key, _, _ in need_verify_sites)]
                    if filtered_urls:
                        self._show_download_mode_selection(filtered_urls)
                    else:
                        messagebox.showinfo("提示", "没有可下载的网址了")
            
            btn_frame = ttk.Frame(main_frame)
            btn_frame.pack(fill="x", pady=10)
            ttk.Button(btn_frame, text="取消", command=verify_window.destroy).pack(side="left", padx=10)
            ttk.Button(btn_frame, text="⏭️ 跳过验证", command=skip_verify).pack(side="left", padx=10)
            ttk.Button(btn_frame, text="🚫 跳过下载", command=skip_download).pack(side="left", padx=10)
            ttk.Button(btn_frame, text="✅ 已完成验证，继续下载", command=continue_download, 
                      style="Success.TButton").pack(side="right", padx=10)
        else:
            self._show_download_mode_selection(urls)
    
    def _continue_download_after_verify(self, verify_window, urls, need_verify_sites):
        verify_window.destroy()
        skipped_sites = [site_key for site_key, _, _ in need_verify_sites if site_key in self._verify_status.get('done', set())]
        filtered_urls = [url for url in urls if not any(site_key in url.lower() for site_key in skipped_sites)]
        if filtered_urls:
            self._show_download_mode_selection(filtered_urls)
        else:
            messagebox.showinfo("提示", "所有网站都已跳过，没有可下载的网址")
    
    def _show_download_mode_selection(self, urls):
        options_window = tk.Toplevel(self.root)
        options_window.title("选择下载模式")
        options_window.geometry("500x400")
        options_window.resizable(False, False)
        
        main_frame = ttk.Frame(options_window, padding=30)
        main_frame.pack(fill="both", expand=True)
        
        ttk.Label(main_frame, text="📚 选择下载模式", font=("Microsoft YaHei", 16, "bold")).pack(pady=(0, 20))
        
        ttk.Label(main_frame, text=f"将下载 {len(urls)} 个网页", foreground="#7f8c8d").pack(pady=(0, 20))
        
        mode_frame = ttk.Frame(main_frame)
        mode_frame.pack(fill="both", expand=True)
        
        def create_mode_card(parent, title, desc, icon, command, color):
            card = tk.Frame(parent, bg=color, cursor="hand2", relief="flat", bd=0)
            card.pack(fill="both", expand=True, padx=5, pady=5)
            
            inner = tk.Frame(card, bg=color)
            inner.pack(fill="both", expand=True, padx=20, pady=15)
            
            title_label = tk.Label(inner, text=f"{icon} {title}", font=("Microsoft YaHei", 14, "bold"), 
                                  bg=color, fg="white")
            title_label.pack(anchor="w")
            
            desc_label = tk.Label(inner, text=desc, font=("Microsoft YaHei", 10), 
                                 bg=color, fg="white", justify="left", wraplength=350)
            desc_label.pack(anchor="w", pady=(5, 0))
            
            def on_click(event):
                card.config(bg=self._darken_color(color))
                inner.config(bg=self._darken_color(color))
                title_label.config(bg=self._darken_color(color))
                desc_label.config(bg=self._darken_color(color))
                options_window.after(100, lambda: self._reset_card_color(card, inner, title_label, desc_label, color))
                options_window.after(150, command)
            
            def on_enter(event):
                card.config(bg=self._lighten_color(color))
                inner.config(bg=self._lighten_color(color))
                title_label.config(bg=self._lighten_color(color))
                desc_label.config(bg=self._lighten_color(color))
            
            def on_leave(event):
                card.config(bg=color)
                inner.config(bg=color)
                title_label.config(bg=color)
                desc_label.config(bg=color)
            
            card.bind("<Button-1>", on_click)
            inner.bind("<Button-1>", on_click)
            title_label.bind("<Button-1>", on_click)
            desc_label.bind("<Button-1>", on_click)
            card.bind("<Enter>", on_enter)
            card.bind("<Leave>", on_leave)
            
            return card
        
        def on_single_click():
            if messagebox.askyesno("确认下载", 
                "📄 单独HTML模式\n\n"
                "将每个网页保存为独立的HTML文件。\n\n"
                "特点：\n"
                "• 每个网页一个文件，方便单独查看\n"
                "• 文件名自动从网页标题获取\n"
                "• 生成index.html目录页便于导航\n\n"
                "确定开始下载？"):
                options_window.destroy()
                self.start_literature_download_single(urls)
        
        def on_pack_click():
            options_window.destroy()
            self.show_pack_config_for_download(urls)
        
        create_mode_card(mode_frame, "单独HTML", 
                        "每个网页保存为独立文件，生成目录页便于导航", 
                        "📄", on_single_click, "#3498db")
        
        ttk.Separator(mode_frame, orient="horizontal").pack(fill="x", pady=10)
        
        create_mode_card(mode_frame, "目录模式", 
                        "生成带目录的单个大HTML文件，左侧固定目录栏", 
                        "📚", on_pack_click, "#27ae60")
        
        close_btn = ttk.Button(main_frame, text="关闭", command=options_window.destroy)
        close_btn.pack(pady=(15, 0))
    
    def _darken_color(self, color):
        import colorsys
        color = color.lstrip('#')
        r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        r, g, b = int(r * 0.85), int(g * 0.85), int(b * 0.85)
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def _lighten_color(self, color):
        import colorsys
        color = color.lstrip('#')
        r, g, b = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        r, g, b = min(255, int(r * 1.1)), min(255, int(g * 1.1)), min(255, int(b * 1.1))
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def _reset_card_color(self, card, inner, title_label, desc_label, color):
        card.config(bg=color)
        inner.config(bg=color)
        title_label.config(bg=color)
        desc_label.config(bg=color)
    
    def show_pack_config_for_download(self, urls):
        config_window = tk.Toplevel(self.root)
        config_window.title("目录模式配置")
        config_window.geometry("550x620")
        config_window.resizable(False, False)
        
        main_frame = ttk.Frame(config_window, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        ttk.Label(main_frame, text="📚 目录模式配置", font=("Microsoft YaHei", 14, "bold")).pack(pady=(0, 15))
        
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill="x", pady=5)
        ttk.Label(title_frame, text="目录标题:").pack(side="left")
        title_var = tk.StringVar(value="网站目录")
        ttk.Entry(title_frame, textvariable=title_var, width=30).pack(side="right")
        
        bg_frame = ttk.LabelFrame(main_frame, text="背景颜色", padding=10)
        bg_frame.pack(fill="x", pady=10)
        
        bg_var = tk.StringVar(value="white")
        bg_row1 = ttk.Frame(bg_frame)
        bg_row1.pack(fill="x", pady=5)
        ttk.Radiobutton(bg_row1, text="白色", variable=bg_var, value="white").pack(side="left", padx=10)
        ttk.Radiobutton(bg_row1, text="黑色", variable=bg_var, value="black").pack(side="left", padx=10)
        ttk.Radiobutton(bg_row1, text="灰色", variable=bg_var, value="gray").pack(side="left", padx=10)
        ttk.Radiobutton(bg_row1, text="自定义", variable=bg_var, value="custom").pack(side="left", padx=10)
        
        bg_row2 = ttk.Frame(bg_frame)
        bg_row2.pack(fill="x", pady=5)
        ttk.Label(bg_row2, text="自定义颜色:").pack(side="left")
        custom_bg_var = tk.StringVar(value="#f5f6f7")
        bg_preview = tk.Label(bg_row2, text="  预览  ", bg="#f5f6f7", width=10, relief="solid")
        bg_preview.pack(side="left", padx=10)
        
        def choose_bg_color():
            from tkinter import colorchooser
            color = colorchooser.askcolor(title="选择背景颜色", initialcolor=custom_bg_var.get())
            if color[1]:
                custom_bg_var.set(color[1])
                bg_preview.config(bg=color[1])
                bg_var.set("custom")
        
        ttk.Button(bg_row2, text="选择颜色", command=choose_bg_color).pack(side="left", padx=5)
        
        font_frame = ttk.LabelFrame(main_frame, text="字体颜色", padding=10)
        font_frame.pack(fill="x", pady=10)
        
        font_var = tk.StringVar(value="black")
        font_row1 = ttk.Frame(font_frame)
        font_row1.pack(fill="x", pady=5)
        ttk.Radiobutton(font_row1, text="黑色", variable=font_var, value="black").pack(side="left", padx=10)
        ttk.Radiobutton(font_row1, text="白色", variable=font_var, value="white").pack(side="left", padx=10)
        ttk.Radiobutton(font_row1, text="自定义", variable=font_var, value="custom").pack(side="left", padx=10)
        
        font_row2 = ttk.Frame(font_frame)
        font_row2.pack(fill="x", pady=5)
        ttk.Label(font_row2, text="自定义颜色:").pack(side="left")
        custom_font_var = tk.StringVar(value="#333333")
        font_preview = tk.Label(font_row2, text="  预览  ", bg="#333333", fg="white", width=10, relief="solid")
        font_preview.pack(side="left", padx=10)
        
        def choose_font_color():
            from tkinter import colorchooser
            color = colorchooser.askcolor(title="选择字体颜色", initialcolor=custom_font_var.get())
            if color[1]:
                custom_font_var.set(color[1])
                font_preview.config(bg=color[1])
                font_var.set("custom")
        
        ttk.Button(font_row2, text="选择颜色", command=choose_font_color).pack(side="left", padx=5)
        
        info_label = ttk.Label(main_frame, text=f"将下载并生成目录 {len(urls)} 个网页", foreground="#7f8c8d")
        info_label.pack(pady=15)
        
        toc_theme_frame = ttk.LabelFrame(main_frame, text="目录颜色主题", padding=10)
        toc_theme_frame.pack(fill="x", pady=10)
        
        toc_theme_var = tk.StringVar(value="colorful")
        toc_theme_row = ttk.Frame(toc_theme_frame)
        toc_theme_row.pack(fill="x", pady=5)
        ttk.Radiobutton(toc_theme_row, text="🎨 彩色", variable=toc_theme_var, value="colorful").pack(side="left", padx=10)
        ttk.Radiobutton(toc_theme_row, text="🌙 深色", variable=toc_theme_var, value="dark").pack(side="left", padx=10)
        ttk.Radiobutton(toc_theme_row, text="⚪ 白色", variable=toc_theme_var, value="white").pack(side="left", padx=10)
        ttk.Radiobutton(toc_theme_row, text="🔵 蓝色", variable=toc_theme_var, value="blue").pack(side="left", padx=10)
        
        custom_theme_row = ttk.Frame(toc_theme_frame)
        custom_theme_row.pack(fill="x", pady=5)
        ttk.Label(custom_theme_row, text="🖼️ 自定义图片背景: ", foreground="#7f8c8d").pack(side="left")
        ttk.Label(custom_theme_row, text="(后续实现)", foreground="#95a5a6").pack(side="left")
        
        def do_download():
            config = {
                'title': title_var.get(),
                'bg_color': custom_bg_var.get() if bg_var.get() == 'custom' else bg_var.get(),
                'font_color': custom_font_var.get() if font_var.get() == 'custom' else font_var.get(),
                'toc_theme': toc_theme_var.get()
            }
            config_window.destroy()
            self.start_literature_download_pack(urls, config)
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=15)
        ttk.Button(btn_frame, text="取消", command=config_window.destroy).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="开始下载", command=do_download, style="Success.TButton").pack(side="right", padx=10)
    
    def stop_literature_download(self):
        self._stop_download = True
        self.root.after(0, self._stop_progress)
        self.literature_log("⏹ 正在终止下载...", "warning")
        self.literature_log("⏹ 请稍等，正在停止当前任务...", "warning")
    
    def _start_progress(self, text=""):
        self.literature_progress.start(10)
        self.progress_label.config(text=text)
    
    def _stop_progress(self):
        self.literature_progress.stop()
        self.progress_label.config(text="")
    
    def _show_floating_progress(self, title="正在下载..."):
        if self._floating_progress_window and self._floating_progress_window.winfo_exists():
            return
        
        self._floating_progress_window = tk.Toplevel(self.root)
        self._floating_progress_window.title("📥 下载进度")
        self._floating_progress_window.geometry("400x230")
        self._floating_progress_window.resizable(False, False)
        self._floating_progress_window.attributes('-topmost', True)
        self._floating_progress_window.overrideredirect(True)
        
        screen_width = self._floating_progress_window.winfo_screenwidth()
        screen_height = self._floating_progress_window.winfo_screenheight()
        x = screen_width - 420
        y = screen_height - 280
        self._floating_progress_window.geometry(f"400x230+{x}+{y}")
        
        header = tk.Frame(self._floating_progress_window, bg="#2196f3", height=40)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        self._floating_header_label = tk.Label(header, text=f"📥 {title}", font=("Microsoft YaHei", 11, "bold"),
                bg="#2196f3", fg="white")
        self._floating_header_label.pack(side="left", padx=10, pady=8)
        
        self._floating_progress_bar = ttk.Progressbar(self._floating_progress_window, 
                                                       mode='indeterminate', length=380)
        self._floating_progress_bar.pack(pady=10, padx=10)
        self._floating_progress_bar.start(10)
        
        self._floating_status_label = tk.Label(self._floating_progress_window, 
                                                text="自动化脚本正在执行下载命令...",
                                                font=("Microsoft YaHei", 9),
                                                fg="#333")
        self._floating_status_label.pack(pady=5)
        
        log_frame = tk.Frame(self._floating_progress_window, bg="#f5f5f5")
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self._floating_log_text = tk.Text(log_frame, height=4, font=("Consolas", 8),
                                          bg="#f5f5f5", relief="flat", wrap="word")
        self._floating_log_text.pack(fill="both", expand=True)
        
        btn_frame = tk.Frame(self._floating_progress_window)
        btn_frame.pack(fill="x", pady=8)
        
        tk.Button(btn_frame, text="⏹ 终止任务", command=self._stop_floating_download,
                 bg="#e74c3c", fg="white", font=("Microsoft YaHei", 9),
                 relief="flat", padx=15, pady=5).pack(side="right", padx=10)
        
        self._floating_progress_window.protocol("WM_DELETE_WINDOW", self._stop_floating_download)
        
        self._keep_floating_top()
    
    def _keep_floating_top(self):
        if self._floating_progress_window and self._floating_progress_window.winfo_exists():
            self._floating_progress_window.attributes('-topmost', True)
            self._floating_progress_window.lift()
            self.root.after(500, self._keep_floating_top)
    
    def _update_floating_log(self, msg, tag="info", phase=None):
        if self._floating_log_text:
            try:
                self._floating_log_text.insert("end", msg + "\n")
                self._floating_log_text.see("end")
                if self._floating_status_label:
                    self._floating_status_label.config(text=msg[:50] + "..." if len(msg) > 50 else msg)
                if phase and self._floating_header_label:
                    if phase == "download":
                        self._floating_header_label.config(text="📥 正在下载文献...")
                    elif phase == "process":
                        self._floating_header_label.config(text="⚙️ 正在处理资源...")
            except:
                pass
    
    def _stop_floating_download(self):
        self._stop_download = True
        self._close_floating_progress()
        self.stop_literature_download()
    
    def _close_floating_progress(self):
        if self._floating_progress_window:
            try:
                self._floating_progress_window.destroy()
            except:
                pass
            self._floating_progress_window = None
            self._floating_log_text = None
    
    def start_literature_download_single(self, urls):
        self._stop_download = False
        self.literature_download_btn.config(state="disabled")
        self.literature_stop_btn.config(state="normal")
        
        self._start_progress("📚 正在下载文献...")
        self._show_floating_progress("正在下载文献...")
        
        headless = not self.debug_mode_var.get()
        mode_str = "前台" if not headless else "后台"
        self.literature_log(f"开始下载 {len(urls)} 个文献（单独HTML模式，{mode_str}运行）...", "info")
        self._update_floating_log(f"开始下载 {len(urls)} 个文献...")
        
        if not self._show_download_warning():
            self.literature_download_btn.config(state="normal")
            self.literature_stop_btn.config(state="disabled")
            self._stop_progress()
            self._close_floating_progress()
            return
        
        threading.Thread(target=self.run_literature_download, args=(urls, False, None, headless), daemon=True).start()
    
    def start_literature_download_pack(self, urls, config=None):
        self._stop_download = False
        self.literature_download_btn.config(state="disabled")
        self.literature_stop_btn.config(state="normal")
        
        self._start_progress("📚 正在下载文献...")
        self._show_floating_progress("正在下载文献...")
        
        headless = not self.debug_mode_var.get()
        mode_str = "前台" if not headless else "后台"
        self.literature_log(f"开始下载 {len(urls)} 个文献（目录模式，{mode_str}运行）...", "info")
        self._update_floating_log(f"开始下载 {len(urls)} 个文献...")
        
        if not self._show_download_warning():
            self.literature_download_btn.config(state="normal")
            self.literature_stop_btn.config(state="disabled")
            self._stop_progress()
            self._close_floating_progress()
            return
        
        threading.Thread(target=self.run_literature_download, args=(urls, True, config, headless), daemon=True).start()
    
    def _show_download_warning(self):
        try:
            base_path = get_base_path()
            
            no_show_file = os.path.join(base_path, "no_show_download_warning.txt")
            if os.path.exists(no_show_file):
                return True
        except:
            pass
        
        browser_type = self._get_actual_browser_type()
        
        if browser_type in ['chrome', 'msedge', 'firefox']:
            browser_names = {
                'chrome': 'Google Chrome',
                'msedge': 'Microsoft Edge',
                'firefox': 'Firefox'
            }
            browser_name = browser_names.get(browser_type, browser_type)
            
            warning = f"""⚠️ 浏览器选择提醒

您当前选择使用系统浏览器: {browser_name}

📌 重要提示：
• 使用主流浏览器可能被部分网站临时封禁
• 建议使用内置浏览器以避免此问题
• 内置浏览器可在「环境管理」中下载安装

接下来程序将自动启动浏览器进行下载。

请您不要触碰任何东西，多余的操作可能会影响脚本工作。"""
        else:
            warning = """⚠️ 下载提示

接下来程序将会自动启动浏览器进行下载。

请您不要触碰任何东西，多余的操作可能会影响脚本工作。

您只需要在电脑桌前稍作等待，喝杯热茶放松一下即可。"""
        
        dialog = tk.Toplevel(self.root)
        dialog.title("下载提示")
        dialog.geometry("450x450")
        dialog.resizable(False, False)
        dialog.configure(bg="white")
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - 225
        y = (dialog.winfo_screenheight() // 2) - 225
        dialog.geometry(f"+{x}+{y}")
        
        header_color = "#ff9800" if browser_type in ['chrome', 'msedge', 'firefox'] else "#2196f3"
        header = tk.Frame(dialog, bg=header_color, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        tk.Label(
            header,
            text="⚠️ 下载提示",
            font=("Microsoft YaHei", 16, "bold"),
            bg=header_color,
            fg="white"
        ).pack(expand=True)
        
        content_frame = tk.Frame(dialog, bg="white", padx=30, pady=25)
        content_frame.pack(fill="both", expand=True)
        
        tk.Label(
            content_frame,
            text=warning,
            font=("Microsoft YaHei", 11),
            bg="white",
            fg="#333",
            justify="left"
        ).pack(anchor="w")
        
        btn_frame = tk.Frame(dialog, bg="white", padx=30, pady=20)
        btn_frame.pack(fill="x", side="bottom")
        
        self._download_warning_result = False
        
        def on_ok():
            self._download_warning_result = True
            dialog.destroy()
        
        def on_ok_and_dont_show():
            try:
                base_path = get_base_path()
                
                no_show_file = os.path.join(base_path, "no_show_download_warning.txt")
                with open(no_show_file, "w") as f:
                    f.write("1")
            except:
                pass
            self._download_warning_result = True
            dialog.destroy()
        
        def on_cancel():
            self._download_warning_result = False
            dialog.destroy()
        
        ttk.Button(btn_frame, text="确定", command=on_ok, width=10).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="确定，下次不再提醒", command=on_ok_and_dont_show, width=18).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="取消", command=on_cancel, width=10).pack(side="right", padx=5)
        
        dialog.wait_window()
        return self._download_warning_result
    
    def show_software_test(self):
        test_window = tk.Toplevel(self.root)
        test_window.title("🧪 软件测试")
        test_window.geometry("500x400")
        test_window.resizable(False, False)
        test_window.transient(self.root)
        
        main_frame = ttk.Frame(test_window, padding=15)
        main_frame.pack(fill="both", expand=True)
        
        ttk.Label(main_frame, text="🧪 软件功能测试", font=("Microsoft YaHei", 14, "bold")).pack(pady=(0, 10))
        
        tests_frame = ttk.LabelFrame(main_frame, text="测试项目", padding=10)
        tests_frame.pack(fill="both", expand=True, pady=5)
        
        test_items = [
            ("浏览器环境", "检查浏览器是否正确安装"),
            ("Python依赖", "检查核心依赖是否完整"),
            ("下载功能", "测试下载一个示例网页"),
            ("文件系统", "检查读写权限"),
        ]
        
        self._test_results = {}
        
        for i, (name, desc) in enumerate(test_items):
            row = ttk.Frame(tests_frame)
            row.pack(fill="x", pady=5)
            ttk.Label(row, text=name, width=12).pack(side="left")
            ttk.Label(row, text=desc, foreground="#7f8c8d").pack(side="left", padx=10)
            result_label = ttk.Label(row, text="待测试", foreground="#f39c12")
            result_label.pack(side="right")
            self._test_results[name] = result_label
        
        def run_tests():
            for name in self._test_results:
                self._test_results[name].config(text="测试中...", foreground="#3498db")
            
            browser_type = self._get_actual_browser_type()
            if browser_type in ['chrome', 'msedge', 'firefox']:
                browser_names = {
                    'chrome': 'Google Chrome',
                    'msedge': 'Microsoft Edge',
                    'firefox': 'Firefox'
                }
                browser_name = browser_names.get(browser_type, browser_type)
                self._test_results["浏览器环境"].config(text=f"✅ 使用{browser_name}", foreground="#27ae60")
            else:
                try:
                    from browser_manager import is_browser_ready
                    if is_browser_ready():
                        self._test_results["浏览器环境"].config(text="✅ 正常", foreground="#27ae60")
                    else:
                        self._test_results["浏览器环境"].config(text="❌ 未安装", foreground="#e74c3c")
                except:
                    self._test_results["浏览器环境"].config(text="❌ 错误", foreground="#e74c3c")
            
            try:
                import playwright, PIL, bs4, lxml
                self._test_results["Python依赖"].config(text="✅ 正常", foreground="#27ae60")
            except ImportError as e:
                self._test_results["Python依赖"].config(text=f"❌ 缺失: {e}", foreground="#e74c3c")
            
            try:
                test_dir = "test_write_permission"
                os.makedirs(test_dir, exist_ok=True)
                with open(os.path.join(test_dir, "test.txt"), "w") as f:
                    f.write("test")
                os.remove(os.path.join(test_dir, "test.txt"))
                os.rmdir(test_dir)
                self._test_results["文件系统"].config(text="✅ 正常", foreground="#27ae60")
            except:
                self._test_results["文件系统"].config(text="❌ 无权限", foreground="#e74c3c")
            
            self._test_results["下载功能"].config(text="⏭ 跳过", foreground="#7f8c8d")
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=10)
        ttk.Button(btn_frame, text="▶️ 开始测试", command=run_tests).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="关闭", command=test_window.destroy).pack(side="right", padx=5)
    
    def show_website_test(self):
        test_window = tk.Toplevel(self.root)
        test_window.title("🌐 网站测试")
        test_window.geometry("500x450")
        test_window.resizable(False, False)
        test_window.transient(self.root)
        
        main_frame = ttk.Frame(test_window, padding=15)
        main_frame.pack(fill="both", expand=True)
        
        ttk.Label(main_frame, text="🌐 网站兼容性测试", font=("Microsoft YaHei", 14, "bold")).pack(pady=(0, 10))
        
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill="x", pady=5)
        ttk.Label(input_frame, text="测试网址:").pack(side="left")
        test_url_var = tk.StringVar()
        ttk.Entry(input_frame, textvariable=test_url_var, width=50).pack(side="left", padx=10)
        
        result_frame = ttk.LabelFrame(main_frame, text="测试结果", padding=10)
        result_frame.pack(fill="both", expand=True, pady=10)
        
        result_text = scrolledtext.ScrolledText(result_frame, height=15, font=("Consolas", 9))
        result_text.pack(fill="both", expand=True)
        
        def run_test():
            url = test_url_var.get().strip()
            if not url:
                messagebox.showwarning("警告", "请输入测试网址")
                return
            
            result_text.delete("1.0", "end")
            result_text.insert("end", f"测试网址: {url}\n")
            result_text.insert("end", "="*40 + "\n\n")
            
            if not url.startswith("http"):
                url = "https://" + url
            
            try:
                import requests
                resp = requests.head(url, timeout=10, allow_redirects=True)
                result_text.insert("end", f"✅ 网站可访问\n")
                result_text.insert("end", f"状态码: {resp.status_code}\n")
                result_text.insert("end", f"最终URL: {resp.url}\n\n")
            except Exception as e:
                result_text.insert("end", f"❌ 无法访问: {e}\n\n")
            
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            site_name = get_site_name(domain)
            if site_name:
                result_text.insert("end", f"✅ 已识别网站: {site_name}\n")
                result_text.insert("end", f"将使用专用下载脚本\n")
            else:
                result_text.insert("end", f"⚠️ 未识别网站类型\n")
                result_text.insert("end", f"将使用通用下载脚本\n")
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=10)
        ttk.Button(btn_frame, text="▶️ 开始测试", command=run_test).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="关闭", command=test_window.destroy).pack(side="right", padx=5)
    
    def show_download_info(self):
        info = """📚 下载说明

• 每个网页将保存为单独的 HTML 文件
• 所有资源（图片、CSS）内嵌到文件中
• 文件可直接用浏览器打开，无需网络

下载完成后可使用「打包模式」整理成目录形式。"""
        if messagebox.askyesno("下载文献", info + "\n\n是否开始下载？"):
            self.start_literature_download()
    
    def start_literature_download(self):
        urls = list(self.literature_url_listbox.get(0, tk.END))
        if not urls:
            messagebox.showwarning("警告", "请添加至少一个网址！")
            return
        
        browser_type = self._get_actual_browser_type()
        
        if browser_type not in ['chrome', 'msedge', 'firefox']:
            from browser_manager import setup_browser_env, is_browser_ready
            setup_browser_env()
            
            if not is_browser_ready():
                result = messagebox.askyesno(
                    "浏览器未安装",
                    "您需要下载内置浏览器才能使用文献下载功能。\n\n"
                    "程序将从官方源下载浏览器（约300MB）。\n\n"
                    "是否现在下载？",
                    icon='question'
                )
                if result:
                    self.show_browser_env_manager(auto_start_download=True)
                return
        
        self.literature_download_btn.config(state="disabled")
        self.literature_log(f"开始下载 {len(urls)} 个文献...", "info")
        
        self._start_progress("📚 正在下载文献...")
        
        threading.Thread(target=self.run_literature_download, args=(urls, False, None, True), daemon=True).start()
    
    def _download_browser_with_progress(self):
        import tkinter.ttk as ttk
        from browser_manager import download_browser
        
        progress_window = tk.Toplevel(self.root)
        progress_window.title("下载浏览器")
        progress_window.geometry("500x180")
        progress_window.resizable(False, False)
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        screen_width = progress_window.winfo_screenwidth()
        screen_height = progress_window.winfo_screenheight()
        x = (screen_width - 500) // 2
        y = (screen_height - 180) // 2
        progress_window.geometry(f"500x180+{x}+{y}")
        
        label = tk.Label(progress_window, text="正在下载浏览器，请稍候...", font=("Microsoft YaHei", 10))
        label.pack(pady=(15, 5))
        
        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(progress_window, variable=progress_var, maximum=100, length=450, mode='indeterminate')
        progress_bar.pack(pady=10)
        progress_bar.start(10)
        
        status_label = tk.Label(progress_window, text="准备下载...", font=("Microsoft YaHei", 9), fg='gray')
        status_label.pack()
        
        progress_window.update()
        
        download_result = [False]
        
        def do_download():
            def progress_callback(msg):
                if progress_window.winfo_exists():
                    progress_window.after(0, lambda: status_label.config(text=msg[:80]))
            
            try:
                result = download_browser(progress_callback=progress_callback, use_mirror=True)
                download_result[0] = result
                
                if progress_window.winfo_exists():
                    progress_bar.stop()
                    if result:
                        label.config(text="✅ 下载完成！", fg='green')
                        status_label.config(text="浏览器已成功安装", fg='green')
                    else:
                        label.config(text="❌ 下载失败", fg='red')
                        status_label.config(text="请检查网络连接后重试", fg='red')
                    
                    btn_frame = tk.Frame(progress_window)
                    btn_frame.pack(pady=10)
                    tk.Button(btn_frame, text="确定", command=progress_window.destroy, width=10).pack()
                    
            except Exception as e:
                if progress_window.winfo_exists():
                    progress_bar.stop()
                    label.config(text="❌ 下载失败", fg='red')
                    status_label.config(text=f"错误: {str(e)[:50]}", fg='red')
                    
                    btn_frame = tk.Frame(progress_window)
                    btn_frame.pack(pady=10)
                    tk.Button(btn_frame, text="确定", command=progress_window.destroy, width=10).pack()
                    
                download_result[0] = False
        
        import threading
        download_thread = threading.Thread(target=do_download, daemon=True)
        download_thread.start()
        
        progress_window.wait_window()
        
        return download_result[0]
    
    def run_literature_download(self, urls, pack_mode=False, config=None, headless=True):
        downloader = None
        try:
            base_dir = self.literature_output_var.get()
            
            if self.create_subfolder_var.get():
                import time
                subfolder_name = time.strftime("%Y%m%d_%H%M%S")
                output_dir = os.path.join(base_dir, subfolder_name)
                self.root.after(0, lambda: self.literature_log(f"创建下载目录: {subfolder_name}", "info"))
            else:
                output_dir = base_dir
            
            if not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            pages_dir = os.path.join(output_dir, "pages")
            if not os.path.exists(pages_dir):
                os.makedirs(pages_dir)
            
            from playwright_downloader import PlaywrightDownloader
            browser_type = self._get_actual_browser_type()
            
            self._pw_downloader = PlaywrightDownloader(gui=self, browser_type=browser_type)
            downloader = self._pw_downloader
            
            downloaded_files = []
            rate_limited_count = [0]
            
            def progress_callback(current, total, result, phase="download", url=""):
                if phase == "download":
                    if result == "rate_limited":
                        rate_limited_count[0] += 1
                        self.root.after(0, lambda c=current, t=total: self.literature_log(
                            f"[{c}/{t}] ⚠️ 请求被拦截，可能需要清空Cookie", "warning"))
                        self.root.after(0, lambda c=current, t=total: self._update_floating_log(
                            f"[{c}/{t}] 请求被拦截", phase="download"))
                        if rate_limited_count[0] == 1:
                            self.root.after(0, self._show_rate_limited_dialog)
                    elif result:
                        filename = os.path.basename(result)
                        downloaded_files.append(filename)
                        self.root.after(0, lambda fn=filename, c=current, t=total: self.literature_log(
                            f"[{c}/{t}] 下载完成: {fn}", "success"))
                        self.root.after(0, lambda fn=filename, c=current, t=total: self._update_floating_log(
                            f"[{c}/{t}] 下载完成: {fn[:30]}", phase="download"))
                    else:
                        self.root.after(0, lambda c=current, t=total: self.literature_log(
                            f"[{c}/{t}] 下载失败", "error"))
                        self.root.after(0, lambda c=current, t=total: self._update_floating_log(
                            f"[{c}/{t}] 下载失败", phase="download"))
                elif phase == "process":
                    if result:
                        filename = os.path.basename(result)
                        self.root.after(0, lambda fn=filename, c=current, t=total: self.literature_log(
                            f"[{c}/{t}] 处理资源: {fn}", "info"))
                        self.root.after(0, lambda fn=filename, c=current, t=total: self._update_floating_log(
                            f"[{c}/{t}] 处理资源: {fn[:30]}", phase="process"))
            
            download_mode = self.download_mode_var.get()
            results = downloader.download_multiple(urls, pages_dir, progress_callback, 
                                                    headless=headless, stop_check=lambda: getattr(self, '_stop_download', False),
                                                    download_mode=download_mode)
            
            if getattr(self, '_stop_download', False):
                self.root.after(0, lambda: self.literature_log("⏹ 下载已终止", "warning"))
                return
            
            success_count = sum(1 for r in results if r['success'])
            
            self.root.after(0, lambda: self.literature_log(
                f"\n✅ 文献下载完成！成功: {success_count}/{len(urls)}", "success"))
            self.root.after(0, lambda: self.literature_log(
                "⏳ 正在进行后处理，请稍候...", "info"))
            self.root.after(0, lambda: self._update_floating_log(
                f"下载完成，正在后处理...", "info"))
            
            if pack_mode and downloaded_files:
                self.root.after(0, lambda: self.literature_log("正在生成未下载提示页面...", "info"))
                from playwright_downloader import PlaywrightDownloader
                not_downloaded_html = PlaywrightDownloader.generate_not_downloaded_page()
                not_downloaded_path = os.path.join(pages_dir, "未下载页面.html")
                with open(not_downloaded_path, 'w', encoding='utf-8') as f:
                    f.write(not_downloaded_html)
                
                self.root.after(0, lambda: self.literature_log("正在注入悬浮目录...", "info"))
                all_html_files = [f for f in os.listdir(pages_dir) if f.endswith('.html') and f != '未下载页面.html']
                toc_theme = config.get('toc_theme', 'colorful') if config else 'colorful'
                self._inject_floating_toc_to_pages(pages_dir, all_html_files, toc_theme)
                
                self.root.after(0, lambda: self.literature_log("正在生成目录文件...", "info"))
                pack_html = self.generate_packed_html(pages_dir, all_html_files, config, include_not_downloaded=False)
                pack_path = os.path.join(output_dir, "文献合集.html")
                with open(pack_path, 'w', encoding='utf-8') as f:
                    f.write(pack_html)
                self.root.after(0, lambda: self.literature_log(
                    f"目录生成完成: 文献合集.html ({len(all_html_files)} 篇)", "success"))
            elif downloaded_files:
                index_content = self.generate_literature_index(downloaded_files)
                index_path = os.path.join(output_dir, "index.html")
                with open(index_path, 'w', encoding='utf-8') as f:
                    f.write(index_content)
                self.root.after(0, lambda: self.literature_log(
                    f"已生成目录页: index.html", "info"))
            
            self.root.after(0, lambda: self.literature_log(
                "✅ 后处理完成！", "success"))
            self.root.after(0, lambda: self.literature_log(
                f"📁 保存位置: {os.path.abspath(output_dir)}", "info"))
            self.root.after(0, lambda: self._update_floating_log(
                f"全部完成！成功: {success_count}/{len(urls)}", "success"))
            
            if success_count > 0:
                self.root.after(0, lambda: self.open_file_explorer(output_dir))
            
            self.root.after(0, lambda: self.literature_log("🔒 浏览器已安全关闭", "info"))
            
        except Exception as e:
            import traceback
            error_msg = f"下载错误: {str(e)}\n{traceback.format_exc()}"
            self.root.after(0, lambda: self.literature_log(error_msg, "error"))
            self.root.after(0, lambda: self._update_floating_log(f"下载错误: {str(e)[:30]}", "error"))
        finally:
            if downloader:
                try:
                    downloader.close(minimize_only=True)
                except:
                    pass
            self.root.after(0, self._stop_progress)
            self.root.after(0, self._close_floating_progress)
            self.root.after(0, lambda: self.literature_download_btn.config(state="normal"))
            self.root.after(0, lambda: self.literature_stop_btn.config(state="disabled"))
            self.root.after(0, lambda: self.literature_log("✅ 下载任务已结束", "info"))
    
    def _get_toc_theme_css(self, theme="colorful"):
        themes = {
            "colorful": {
                "header_bg": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                "panel_bg": "rgba(255, 255, 255, 0.98)",
                "item_bg": "#f8f9fa",
                "item_hover_bg": "#e3f2fd",
                "item_hover_border": "#2196f3",
                "title_color": "#333",
                "source_color": "#7f8c8d",
                "float_btn_bg": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                "shadow": "0 8px 32px rgba(0, 0, 0, 0.3)"
            },
            "dark": {
                "header_bg": "linear-gradient(135deg, #2c3e50 0%, #1a1a2e 100%)",
                "panel_bg": "rgba(30, 30, 40, 0.98)",
                "item_bg": "#2d2d3a",
                "item_hover_bg": "#3d3d4a",
                "item_hover_border": "#9b59b6",
                "title_color": "#ecf0f1",
                "source_color": "#95a5a6",
                "float_btn_bg": "linear-gradient(135deg, #2c3e50 0%, #1a1a2e 100%)",
                "shadow": "0 8px 32px rgba(0, 0, 0, 0.5)"
            },
            "white": {
                "header_bg": "linear-gradient(135deg, #ecf0f1 0%, #bdc3c7 100%)",
                "panel_bg": "rgba(255, 255, 255, 0.98)",
                "item_bg": "#ffffff",
                "item_hover_bg": "#f5f5f5",
                "item_hover_border": "#95a5a6",
                "title_color": "#2c3e50",
                "source_color": "#7f8c8d",
                "float_btn_bg": "linear-gradient(135deg, #ecf0f1 0%, #bdc3c7 100%)",
                "shadow": "0 8px 32px rgba(0, 0, 0, 0.15)"
            },
            "blue": {
                "header_bg": "linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)",
                "panel_bg": "rgba(240, 248, 255, 0.98)",
                "item_bg": "#e8f4fc",
                "item_hover_bg": "#d0e8f7",
                "item_hover_border": "#1e3c72",
                "title_color": "#1e3c72",
                "source_color": "#5a7fa8",
                "float_btn_bg": "linear-gradient(135deg, #1e3c72 0%, #2a5298 100%)",
                "shadow": "0 8px 32px rgba(30, 60, 114, 0.3)"
            }
        }
        
        t = themes.get(theme, themes["colorful"])
        
        return f'''
        #floatingTocPanel {{
            position: fixed !important;
            top: 50% !important;
            left: 20px !important;
            transform: translateY(-50%) translateX(0) !important;
            width: 350px !important;
            max-height: 80vh !important;
            background: {t["panel_bg"]} !important;
            border-radius: 12px !important;
            box-shadow: {t["shadow"]} !important;
            z-index: 999999 !important;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
            overflow: hidden !important;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
            box-sizing: border-box !important;
            line-height: 1.5 !important;
        }}
        
        #floatingTocPanel.collapsed {{
            transform: translateY(-50%) translateX(-400px) !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }}
        
        #floatingTocPanel.expanded {{
            transform: translateY(-50%) translateX(0) !important;
            opacity: 1 !important;
            pointer-events: auto !important;
        }}
        
        #floatingTocPanel * {{
            box-sizing: border-box !important;
        }}
        
        #floatingTocHeader {{
            background: {t["header_bg"]} !important;
            color: white !important;
            padding: 15px 20px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: space-between !important;
            cursor: move !important;
            user-select: none !important;
        }}
        
        #floatingTocPanel .floating-toc-title {{
            font-size: 16px !important;
            font-weight: bold !important;
            display: flex !important;
            align-items: center !important;
            gap: 8px !important;
            color: white !important;
        }}
        
        #floatingTocPanel .floating-toc-toggle-btn {{
            background: rgba(255, 255, 255, 0.2) !important;
            border: none !important;
            color: white !important;
            width: 32px !important;
            height: 32px !important;
            border-radius: 50% !important;
            cursor: pointer !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            transition: all 0.3s ease !important;
            font-size: 18px !important;
        }}
        
        #floatingTocPanel .floating-toc-toggle-btn:hover {{
            background: rgba(255, 255, 255, 0.3) !important;
            transform: scale(1.1) !important;
        }}
        
        #floatingTocPanel .floating-toc-content {{
            padding: 15px !important;
            max-height: calc(80vh - 60px) !important;
            overflow-y: auto !important;
        }}
        
        #floatingTocPanel .floating-toc-content::-webkit-scrollbar {{
            width: 6px !important;
        }}
        
        #floatingTocPanel .floating-toc-content::-webkit-scrollbar-track {{
            background: #f1f1f1 !important;
            border-radius: 3px !important;
        }}
        
        #floatingTocPanel .floating-toc-content::-webkit-scrollbar-thumb {{
            background: #c1c1c1 !important;
            border-radius: 3px !important;
        }}
        
        #floatingTocPanel .floating-toc-current-article {{
            margin-bottom: 10px !important;
        }}
        
        #floatingTocPanel .floating-toc-current-label {{
            font-size: 11px !important;
            color: {t["source_color"]} !important;
            margin-bottom: 5px !important;
            font-weight: bold !important;
        }}
        
        #floatingTocPanel .floating-toc-divider {{
            height: 1px !important;
            background: linear-gradient(to right, transparent, #e0e0e0, transparent) !important;
            margin: 10px 0 !important;
        }}
        
        #floatingTocPanel .floating-toc-back {{
            display: flex !important;
            align-items: center !important;
            gap: 8px !important;
            padding: 10px 15px !important;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
            border-radius: 8px !important;
            cursor: pointer !important;
            color: white !important;
            font-size: 13px !important;
            font-weight: bold !important;
            transition: all 0.3s ease !important;
        }}
        
        #floatingTocPanel .floating-toc-back:hover {{
            transform: translateX(3px) !important;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4) !important;
        }}
        
        #floatingTocPanel .floating-toc-other-label {{
            font-size: 11px !important;
            color: {t["source_color"]} !important;
            margin-bottom: 8px !important;
            font-weight: bold !important;
        }}
        
        #floatingTocPanel .floating-toc-articles-scroll {{
            max-height: 300px !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
        }}
        
        #floatingTocPanel .floating-toc-articles-scroll::-webkit-scrollbar {{
            width: 4px !important;
        }}
        
        #floatingTocPanel .floating-toc-articles-scroll::-webkit-scrollbar-track {{
            background: #f1f1f1 !important;
            border-radius: 2px !important;
        }}
        
        #floatingTocPanel .floating-toc-articles-scroll::-webkit-scrollbar-thumb {{
            background: #c1c1c1 !important;
            border-radius: 2px !important;
        }}
        
        #floatingTocPanel .floating-toc-item {{
            padding: 12px 15px !important;
            margin: 8px 0 !important;
            background: {t["item_bg"]} !important;
            border-radius: 8px !important;
            cursor: pointer !important;
            transition: all 0.3s ease !important;
            border-left: 3px solid transparent !important;
        }}
        
        #floatingTocPanel .floating-toc-item:hover {{
            background: {t["item_hover_bg"]} !important;
            border-left-color: {t["item_hover_border"]} !important;
            transform: translateX(3px) !important;
        }}
        
        #floatingTocPanel .floating-toc-item.current {{
            background: {t["item_hover_bg"]} !important;
            border-left-color: {t["item_hover_border"]} !important;
        }}
        
        #floatingTocPanel .floating-toc-item-title {{
            color: {t["title_color"]} !important;
            font-size: 14px !important;
            line-height: 1.4 !important;
        }}
        
        #floatingTocPanel .floating-toc-source {{
            color: {t["source_color"]} !important;
            font-size: 11px !important;
            margin-top: 3px !important;
        }}
        
        #floatingTocFloatBtn {{
            position: fixed !important;
            top: 50% !important;
            left: 0 !important;
            transform: translateY(-50%) !important;
            width: 40px !important;
            height: 80px !important;
            background: {t["float_btn_bg"]} !important;
            border-radius: 0 12px 12px 0 !important;
            cursor: pointer !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            color: white !important;
            font-size: 20px !important;
            z-index: 999998 !important;
            transition: all 0.3s ease !important;
            box-shadow: 2px 0 10px rgba(0, 0, 0, 0.2) !important;
        }}
        
        #floatingTocFloatBtn:hover {{
            width: 50px !important;
            box-shadow: 4px 0 15px rgba(0, 0, 0, 0.3) !important;
        }}
        
        #floatingTocFloatBtn.hidden {{
            left: -50px !important;
        }}
        '''
    
    def _inject_floating_toc_to_pages(self, pages_dir, html_files, theme="colorful"):
        from bs4 import BeautifulSoup
        from urllib.parse import urlparse
        
        def get_source_info(html_file):
            file_path = os.path.join(pages_dir, html_file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                soup = BeautifulSoup(content, 'lxml')
                
                article_sources = soup.find('meta', attrs={'name': 'article-sources'})
                if article_sources and article_sources.get('content'):
                    sources_content = article_sources['content']
                    if sources_content:
                        sources_list = sources_content.split(',')
                        if len(sources_list) == 1:
                            return sources_list[0]
                        else:
                            return '、'.join(sources_list[:3]) + (f'等{len(sources_list)}个' if len(sources_list) > 3 else '')
                
                canonical = soup.find('link', rel='canonical')
                if canonical and canonical.get('href'):
                    url = canonical['href']
                else:
                    og_url = soup.find('meta', property='og:url')
                    if og_url and og_url.get('content'):
                        url = og_url['content']
                    else:
                        return None
                
                parsed = urlparse(url)
                domain = parsed.netloc
                
                site_names = {
                    'zhihu.com': '知乎',
                    'csdn.net': 'CSDN',
                    'juejin.cn': '掘金',
                    'jianshu.com': '简书',
                    'bilibili.com': '哔哩哔哩',
                    'blog.csdn.net': 'CSDN博客',
                    'zhuanlan.zhihu.com': '知乎专栏',
                }
                
                for site_domain, site_name in site_names.items():
                    if site_domain in domain:
                        return site_name
                
                return domain
            except:
                return None
        
        toc_css = self._get_toc_theme_css(theme)
        
        for current_html_file in html_files:
            file_path = os.path.join(pages_dir, current_html_file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                soup = BeautifulSoup(content, 'lxml')
                
                old_panel = soup.find(id='floatingTocPanel')
                if old_panel:
                    old_panel.decompose()
                old_float_btn = soup.find(id='floatingTocFloatBtn')
                if old_float_btn:
                    old_float_btn.decompose()
                
                current_file_title = current_html_file.replace('.html', '').replace('_', ' ')
                current_source = get_source_info(current_html_file)
                
                other_articles_list = ""
                for html_file in html_files:
                    if html_file == current_html_file:
                        continue
                    
                    file_title = html_file.replace('.html', '').replace('_', ' ')
                    source = get_source_info(html_file)
                    source_html = f'<div class="floating-toc-source">{source}</div>' if source else ''
                    
                    other_articles_list += f'''
                    <div class="floating-toc-item" onclick="openArticle('{html_file}')">
                        <div class="floating-toc-item-title">{file_title}</div>
                        {source_html}
                    </div>'''
                
                toc_html = f'''
                <div class="floating-toc-panel" id="floatingTocPanel">
                    <div class="floating-toc-header" id="floatingTocHeader">
                        <div class="floating-toc-title">
                            <span>📑</span>
                            <span>文章目录</span>
                        </div>
                        <button class="floating-toc-toggle-btn" onclick="toggleFloatingTOC()" title="折叠/展开">
                            ◀
                        </button>
                    </div>
                    <div class="floating-toc-content">
                        <div class="floating-toc-current-article">
                            <div class="floating-toc-current-label">当前文章</div>
                            <div class="floating-toc-item current">
                                <div class="floating-toc-item-title">{current_file_title}</div>
                                {f'<div class="floating-toc-source">' + current_source + '</div>' if current_source else ''}
                            </div>
                        </div>
                        <div class="floating-toc-divider"></div>
                        <div class="floating-toc-back" onclick="goBackToIndex()">
                            <span>🏠</span>
                            <span>返回文章合集</span>
                        </div>
                        <div class="floating-toc-divider"></div>
                        <div class="floating-toc-other-label">其他文章 ({len(html_files) - 1})</div>
                        <div class="floating-toc-articles-scroll">
                            {other_articles_list}
                        </div>
                    </div>
                </div>
                
                <div class="floating-toc-float-btn" id="floatingTocFloatBtn" onclick="toggleFloatingTOC()" title="展开目录">
                    ◀
                </div>
                '''
                
                toc_script = '''
                function goBackToIndex() {
                    window.location.href = '../文献合集.html';
                }
                
                function openArticle(filename) {
                    window.location.href = filename;
                }
                
                var floatingTocPanel = document.getElementById('floatingTocPanel');
                var floatingTocFloatBtn = document.getElementById('floatingTocFloatBtn');
                var isFloatingCollapsed = false;
                var floatingXOffset = 0;
                var floatingYOffset = 0;
                
                function toggleFloatingTOC() {
                    isFloatingCollapsed = !isFloatingCollapsed;
                    
                    if (isFloatingCollapsed) {
                        floatingTocPanel.classList.remove('expanded');
                        floatingTocPanel.classList.add('collapsed');
                        floatingTocFloatBtn.classList.remove('hidden');
                        floatingTocFloatBtn.innerHTML = '▶';
                    } else {
                        floatingTocPanel.classList.remove('collapsed');
                        floatingTocPanel.classList.add('expanded');
                        floatingTocFloatBtn.classList.add('hidden');
                    }
                }
                
                var floatingTocHeader = document.getElementById('floatingTocHeader');
                var isFloatingDragging = false;
                var floatingCurrentX;
                var floatingCurrentY;
                var floatingInitialX;
                var floatingInitialY;
                
                floatingTocHeader.addEventListener('mousedown', floatingDragStart);
                document.addEventListener('mouseup', floatingDragEnd);
                document.addEventListener('mousemove', floatingDrag);
                
                function floatingDragStart(e) {
                    if (e.target.classList.contains('floating-toc-toggle-btn') || e.target.closest('.floating-toc-toggle-btn')) {
                        return;
                    }
                    floatingInitialX = e.clientX - floatingXOffset;
                    floatingInitialY = e.clientY - floatingYOffset;
                    
                    if (e.target === floatingTocHeader || floatingTocHeader.contains(e.target)) {
                        isFloatingDragging = true;
                    }
                }
                
                function floatingDragEnd(e) {
                    floatingInitialX = floatingCurrentX;
                    floatingInitialY = floatingCurrentY;
                    isFloatingDragging = false;
                }
                
                function floatingDrag(e) {
                    if (isFloatingDragging) {
                        e.preventDefault();
                        floatingCurrentX = e.clientX - floatingInitialX;
                        floatingCurrentY = e.clientY - floatingInitialY;
                        floatingXOffset = floatingCurrentX;
                        floatingYOffset = floatingCurrentY;
                        
                        var collapseOffset = isFloatingCollapsed ? -400 : 0;
                        floatingTocPanel.style.transform = 'translate(' + (floatingCurrentX + collapseOffset) + 'px, calc(-50% + ' + floatingCurrentY + 'px))';
                    }
                }
                
                if (floatingTocPanel) {
                    floatingTocPanel.classList.add('expanded');
                    if (floatingTocFloatBtn) {
                        floatingTocFloatBtn.classList.add('hidden');
                    }
                }
                '''
                
                style_tag = soup.new_tag('style')
                style_tag.string = toc_css
                if soup.head:
                    soup.head.append(style_tag)
                
                toc_div = BeautifulSoup(toc_html, 'html.parser')
                if soup.body:
                    soup.body.append(toc_div)
                
                script_tag = soup.new_tag('script')
                script_tag.string = toc_script
                if soup.body:
                    soup.body.append(script_tag)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(str(soup))
                    
            except Exception as e:
                self.literature_log(f"注入悬浮目录失败 {current_html_file}: {e}", "warning")

    def _inject_floating_toc_to_pages_custom(self, pages_dir, html_files, theme_config):
        from bs4 import BeautifulSoup
        from urllib.parse import urlparse
        
        def get_source_info(html_file):
            file_path = os.path.join(pages_dir, html_file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                soup = BeautifulSoup(content, 'lxml')
                
                canonical = soup.find('link', rel='canonical')
                if canonical and canonical.get('href'):
                    url = canonical['href']
                else:
                    og_url = soup.find('meta', property='og:url')
                    if og_url and og_url.get('content'):
                        url = og_url['content']
                    else:
                        return None
                
                parsed = urlparse(url)
                domain = parsed.netloc
                
                site_names = {
                    'zhihu.com': '知乎',
                    'csdn.net': 'CSDN',
                    'juejin.cn': '掘金',
                    'jianshu.com': '简书',
                    'bilibili.com': '哔哩哔哩',
                    'blog.csdn.net': 'CSDN博客',
                    'zhuanlan.zhihu.com': '知乎专栏',
                }
                
                for site_domain, site_name in site_names.items():
                    if site_domain in domain:
                        return site_name
                
                return domain
            except:
                return None
        
        t = theme_config
        toc_css = f'''
        #floatingTocPanel {{
            position: fixed !important;
            top: 50% !important;
            left: 20px !important;
            transform: translateY(-50%) translateX(0) !important;
            width: 350px !important;
            max-height: 80vh !important;
            background: {t["panel_bg"]} !important;
            border-radius: 12px !important;
            box-shadow: {t["shadow"]} !important;
            z-index: 999999 !important;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1) !important;
            overflow: hidden !important;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
            box-sizing: border-box !important;
            line-height: 1.5 !important;
        }}
        
        #floatingTocPanel.collapsed {{
            transform: translateY(-50%) translateX(-400px) !important;
            opacity: 0 !important;
            pointer-events: none !important;
        }}
        
        #floatingTocPanel.expanded {{
            transform: translateY(-50%) translateX(0) !important;
            opacity: 1 !important;
            pointer-events: auto !important;
        }}
        
        #floatingTocPanel * {{
            box-sizing: border-box !important;
        }}
        
        #floatingTocHeader {{
            background: {t["header_bg"]} !important;
            color: white !important;
            padding: 15px 20px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: space-between !important;
            cursor: move !important;
            user-select: none !important;
        }}
        
        #floatingTocPanel .floating-toc-title {{
            font-size: 16px !important;
            font-weight: bold !important;
            display: flex !important;
            align-items: center !important;
            gap: 8px !important;
            color: white !important;
        }}
        
        #floatingTocPanel .floating-toc-toggle-btn {{
            background: rgba(255, 255, 255, 0.2) !important;
            border: none !important;
            color: white !important;
            width: 32px !important;
            height: 32px !important;
            border-radius: 50% !important;
            cursor: pointer !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            transition: all 0.3s ease !important;
            font-size: 18px !important;
        }}
        
        #floatingTocPanel .floating-toc-toggle-btn:hover {{
            background: rgba(255, 255, 255, 0.3) !important;
            transform: scale(1.1) !important;
        }}
        
        #floatingTocPanel .floating-toc-content {{
            padding: 15px !important;
            max-height: calc(80vh - 60px) !important;
            overflow-y: auto !important;
        }}
        
        #floatingTocPanel .floating-toc-content::-webkit-scrollbar {{
            width: 6px !important;
        }}
        
        #floatingTocPanel .floating-toc-content::-webkit-scrollbar-track {{
            background: #f1f1f1 !important;
            border-radius: 3px !important;
        }}
        
        #floatingTocPanel .floating-toc-content::-webkit-scrollbar-thumb {{
            background: #c1c1c1 !important;
            border-radius: 3px !important;
        }}
        
        #floatingTocPanel .floating-toc-current-article {{
            margin-bottom: 10px !important;
        }}
        
        #floatingTocPanel .floating-toc-current-label {{
            font-size: 11px !important;
            color: {t["source_color"]} !important;
            margin-bottom: 5px !important;
            font-weight: bold !important;
        }}
        
        #floatingTocPanel .floating-toc-divider {{
            height: 1px !important;
            background: linear-gradient(to right, transparent, #e0e0e0, transparent) !important;
            margin: 10px 0 !important;
        }}
        
        #floatingTocPanel .floating-toc-back {{
            display: flex !important;
            align-items: center !important;
            gap: 8px !important;
            padding: 10px 15px !important;
            background: {t["header_bg"]} !important;
            border-radius: 8px !important;
            cursor: pointer !important;
            color: white !important;
            font-size: 13px !important;
            font-weight: bold !important;
            transition: all 0.3s ease !important;
        }}
        
        #floatingTocPanel .floating-toc-back:hover {{
            transform: translateX(3px) !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3) !important;
        }}
        
        #floatingTocPanel .floating-toc-other-label {{
            font-size: 11px !important;
            color: {t["source_color"]} !important;
            margin-bottom: 8px !important;
            font-weight: bold !important;
        }}
        
        #floatingTocPanel .floating-toc-articles-scroll {{
            max-height: 300px !important;
            overflow-y: auto !important;
            overflow-x: hidden !important;
        }}
        
        #floatingTocPanel .floating-toc-articles-scroll::-webkit-scrollbar {{
            width: 4px !important;
        }}
        
        #floatingTocPanel .floating-toc-articles-scroll::-webkit-scrollbar-track {{
            background: #f1f1f1 !important;
            border-radius: 2px !important;
        }}
        
        #floatingTocPanel .floating-toc-articles-scroll::-webkit-scrollbar-thumb {{
            background: #c1c1c1 !important;
            border-radius: 2px !important;
        }}
        
        #floatingTocPanel .floating-toc-item {{
            padding: 12px 15px !important;
            margin: 8px 0 !important;
            background: {t["item_bg"]} !important;
            border-radius: 8px !important;
            cursor: pointer !important;
            transition: all 0.3s ease !important;
            border-left: 3px solid transparent !important;
        }}
        
        #floatingTocPanel .floating-toc-item:hover {{
            background: {t["item_hover_bg"]} !important;
            border-left-color: {t["item_hover_border"]} !important;
            transform: translateX(3px) !important;
        }}
        
        #floatingTocPanel .floating-toc-item.current {{
            background: {t["item_hover_bg"]} !important;
            border-left-color: {t["item_hover_border"]} !important;
        }}
        
        #floatingTocPanel .floating-toc-item-title {{
            color: {t["title_color"]} !important;
            font-size: 14px !important;
            line-height: 1.4 !important;
        }}
        
        #floatingTocPanel .floating-toc-source {{
            color: {t["source_color"]} !important;
            font-size: 11px !important;
            margin-top: 3px !important;
        }}
        
        #floatingTocFloatBtn {{
            position: fixed !important;
            top: 50% !important;
            left: 0 !important;
            transform: translateY(-50%) !important;
            width: 40px !important;
            height: 80px !important;
            background: {t["float_btn_bg"]} !important;
            border-radius: 0 12px 12px 0 !important;
            cursor: pointer !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            color: white !important;
            font-size: 20px !important;
            z-index: 999998 !important;
            transition: all 0.3s ease !important;
            box-shadow: 2px 0 10px rgba(0, 0, 0, 0.2) !important;
        }}
        
        #floatingTocFloatBtn:hover {{
            width: 50px !important;
            box-shadow: 4px 0 15px rgba(0, 0, 0, 0.3) !important;
        }}
        
        #floatingTocFloatBtn.hidden {{
            left: -50px !important;
        }}
        '''
        
        for current_html_file in html_files:
            file_path = os.path.join(pages_dir, current_html_file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                soup = BeautifulSoup(content, 'lxml')
                
                old_panel = soup.find(id='floatingTocPanel')
                if old_panel:
                    old_panel.decompose()
                old_float_btn = soup.find(id='floatingTocFloatBtn')
                if old_float_btn:
                    old_float_btn.decompose()
                
                current_file_title = current_html_file.replace('.html', '').replace('_', ' ')
                current_source = get_source_info(current_html_file)
                
                other_articles_list = ""
                for html_file in html_files:
                    if html_file == current_html_file:
                        continue
                    
                    file_title = html_file.replace('.html', '').replace('_', ' ')
                    source = get_source_info(html_file)
                    source_html = f'<div class="floating-toc-source">{source}</div>' if source else ''
                    
                    other_articles_list += f'''
                    <div class="floating-toc-item" onclick="openArticle('{html_file}')">
                        <div class="floating-toc-item-title">{file_title}</div>
                        {source_html}
                    </div>'''
                
                toc_html = f'''
                <div class="floating-toc-panel" id="floatingTocPanel">
                    <div class="floating-toc-header" id="floatingTocHeader">
                        <div class="floating-toc-title">
                            <span>📑</span>
                            <span>文章目录</span>
                        </div>
                        <button class="floating-toc-toggle-btn" onclick="toggleFloatingTOC()" title="折叠/展开">
                            ◀
                        </button>
                    </div>
                    <div class="floating-toc-content">
                        <div class="floating-toc-current-article">
                            <div class="floating-toc-current-label">当前文章</div>
                            <div class="floating-toc-item current">
                                <div class="floating-toc-item-title">{current_file_title}</div>
                                {f'<div class="floating-toc-source">' + current_source + '</div>' if current_source else ''}
                            </div>
                        </div>
                        <div class="floating-toc-divider"></div>
                        <div class="floating-toc-back" onclick="goBackToIndex()">
                            <span>🏠</span>
                            <span>返回文章合集</span>
                        </div>
                        <div class="floating-toc-divider"></div>
                        <div class="floating-toc-other-label">其他文章 ({len(html_files) - 1})</div>
                        <div class="floating-toc-articles-scroll">
                            {other_articles_list}
                        </div>
                    </div>
                </div>
                
                <div class="floating-toc-float-btn" id="floatingTocFloatBtn" onclick="toggleFloatingTOC()" title="展开目录">
                    ◀
                </div>
                '''
                
                toc_script = '''
                function goBackToIndex() {
                    window.location.href = '../文献合集.html';
                }
                
                function openArticle(filename) {
                    window.location.href = filename;
                }
                
                var floatingTocPanel = document.getElementById('floatingTocPanel');
                var floatingTocFloatBtn = document.getElementById('floatingTocFloatBtn');
                var isFloatingCollapsed = false;
                var floatingXOffset = 0;
                var floatingYOffset = 0;
                
                function toggleFloatingTOC() {
                    isFloatingCollapsed = !isFloatingCollapsed;
                    
                    if (isFloatingCollapsed) {
                        floatingTocPanel.classList.remove('expanded');
                        floatingTocPanel.classList.add('collapsed');
                        floatingTocFloatBtn.classList.remove('hidden');
                        floatingTocFloatBtn.innerHTML = '▶';
                    } else {
                        floatingTocPanel.classList.remove('collapsed');
                        floatingTocPanel.classList.add('expanded');
                        floatingTocFloatBtn.classList.add('hidden');
                    }
                }
                
                var floatingTocHeader = document.getElementById('floatingTocHeader');
                var isFloatingDragging = false;
                var floatingCurrentX;
                var floatingCurrentY;
                var floatingInitialX;
                var floatingInitialY;
                
                floatingTocHeader.addEventListener('mousedown', floatingDragStart);
                document.addEventListener('mouseup', floatingDragEnd);
                document.addEventListener('mousemove', floatingDrag);
                
                function floatingDragStart(e) {
                    if (e.target.classList.contains('floating-toc-toggle-btn') || e.target.closest('.floating-toc-toggle-btn')) {
                        return;
                    }
                    floatingInitialX = e.clientX - floatingXOffset;
                    floatingInitialY = e.clientY - floatingYOffset;
                    
                    if (e.target === floatingTocHeader || floatingTocHeader.contains(e.target)) {
                        isFloatingDragging = true;
                    }
                }
                
                function floatingDragEnd(e) {
                    floatingInitialX = floatingCurrentX;
                    floatingInitialY = floatingCurrentY;
                    isFloatingDragging = false;
                }
                
                function floatingDrag(e) {
                    if (isFloatingDragging) {
                        e.preventDefault();
                        floatingCurrentX = e.clientX - floatingInitialX;
                        floatingCurrentY = e.clientY - floatingInitialY;
                        floatingXOffset = floatingCurrentX;
                        floatingYOffset = floatingCurrentY;
                        
                        var collapseOffset = isFloatingCollapsed ? -400 : 0;
                        floatingTocPanel.style.transform = 'translate(' + (floatingCurrentX + collapseOffset) + 'px, calc(-50% + ' + floatingCurrentY + 'px))';
                    }
                }
                
                if (floatingTocPanel) {
                    floatingTocPanel.classList.add('expanded');
                    if (floatingTocFloatBtn) {
                        floatingTocFloatBtn.classList.add('hidden');
                    }
                }
                '''
                
                style_tag = soup.new_tag('style')
                style_tag.string = toc_css
                if soup.head:
                    soup.head.append(style_tag)
                
                toc_div = BeautifulSoup(toc_html, 'html.parser')
                if soup.body:
                    soup.body.append(toc_div)
                
                script_tag = soup.new_tag('script')
                script_tag.string = toc_script
                if soup.body:
                    soup.body.append(script_tag)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(str(soup))
                    
            except Exception as e:
                self.literature_log(f"注入悬浮目录失败 {current_html_file}: {e}", "warning")

    def generate_packed_html(self, pages_dir, html_files, config=None, include_not_downloaded=True):
        if config is None:
            config = {}
        
        title = config.get('title', '文章目录')
        bg_color = config.get('bg_color', 'white')
        font_color = config.get('font_color', 'black')
        
        bg_map = {'white': '#f5f6f7', 'black': '#1a1a1a', 'gray': '#e0e0e0'}
        font_map = {'white': '#ffffff', 'black': '#333333'}
        
        bg = bg_map.get(bg_color, bg_color)
        font = font_map.get(font_color, font_color)
        
        articles_list = ""
        sources_set = set()
        
        for i, html_file in enumerate(html_files):
            file_path = os.path.join(pages_dir, html_file)
            file_title = html_file.replace('.html', '').replace('_', ' ')
            source = ""
            
            try:
                from bs4 import BeautifulSoup
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read(50000)
                
                soup = BeautifulSoup(content, 'lxml')
                
                og_title = soup.find('meta', property='og:title')
                if og_title and og_title.get('content'):
                    file_title = og_title['content'].strip()
                elif soup.title and soup.title.string:
                    file_title = soup.title.string.strip()
                    if len(file_title) > 80:
                        for sep in ['_', '-', '|', '·', '–']:
                            if sep in file_title:
                                parts = file_title.split(sep)
                                file_title = parts[0].strip()
                                break
                
                file_title = re.sub(r'[\\/*?:"<>|]', '_', file_title)
                file_title = re.sub(r'\s+', ' ', file_title)
                if len(file_title) > 80:
                    file_title = file_title[:80] + '...'
                
                canonical = soup.find('link', rel='canonical')
                if canonical and canonical.get('href'):
                    from urllib.parse import urlparse
                    domain = urlparse(canonical['href']).netloc
                    source = get_site_name(domain)
                
                if not source:
                    og_url = soup.find('meta', property='og:url')
                    if og_url and og_url.get('content'):
                        from urllib.parse import urlparse
                        domain = urlparse(og_url['content']).netloc
                        source = get_site_name(domain)
                
                if not source:
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        if href.startswith('http'):
                            from urllib.parse import urlparse
                            domain = urlparse(href).netloc
                            source = get_site_name(domain)
                        if source:
                            break
                
                if source:
                    sources_set.add(source)
            except:
                pass
            
            source_badge = f'<span class="article-source">{source}</span>' if source else ''
            
            articles_list += f'''
            <a href="pages/{html_file}" class="article-link">
                <div class="article-item">
                    <div class="article-number">{i+1}</div>
                    <div class="article-info">
                        <div class="article-title-text">{file_title}</div>
                        <div class="article-meta">{html_file}{source_badge}</div>
                    </div>
                    <div class="article-arrow">→</div>
                </div>
            </a>'''
        
        if include_not_downloaded:
            articles_list += f'''
            <a href="未下载页面.html" class="article-link not-downloaded">
                <div class="article-item not-downloaded-item">
                    <div class="article-number warning">!</div>
                    <div class="article-info">
                        <div class="article-title-text">⚠️ 未下载页面</div>
                        <div class="article-meta">点击查看下载失败的页面</div>
                    </div>
                    <div class="article-arrow">→</div>
                </div>
            </a>'''
        
        sources_str = "、".join(sorted(sources_set)) if sources_set else "多个来源"
        sources_meta = ",".join(sorted(sources_set)) if sources_set else ""
        
        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="article-sources" content="{sources_meta}">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: "Microsoft YaHei", "PingFang SC", sans-serif;
            background: {bg};
            color: {font};
            line-height: 1.6;
            min-height: 100vh;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding-bottom: 20px;
            border-bottom: 2px solid #3498db;
        }}
        .header h1 {{
            font-size: 28px;
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        .header .count {{
            color: #7f8c8d;
            font-size: 14px;
        }}
        .header .sources {{
            color: #3498db;
            font-size: 13px;
            margin-top: 8px;
        }}
        .article-list {{
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}
        .article-link {{
            text-decoration: none;
            color: inherit;
        }}
        .article-item {{
            background: #fff;
            border-radius: 12px;
            padding: 20px 25px;
            display: flex;
            align-items: center;
            gap: 20px;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border: 1px solid #eee;
        }}
        .article-item:hover {{
            transform: translateX(8px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.15);
            border-color: #3498db;
        }}
        .article-number {{
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 16px;
            flex-shrink: 0;
        }}
        .article-info {{
            flex: 1;
            min-width: 0;
        }}
        .article-title-text {{
            font-size: 16px;
            font-weight: 500;
            color: #2c3e50;
            margin-bottom: 4px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}
        .article-meta {{
            font-size: 12px;
            color: #95a5a6;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .article-source {{
            background: #3498db;
            color: white;
            padding: 2px 8px;
            border-radius: 10px;
            font-size: 11px;
        }}
        .article-arrow {{
            color: #3498db;
            font-size: 20px;
            transition: transform 0.3s ease;
        }}
        .article-item:hover .article-arrow {{
            transform: translateX(5px);
        }}
        .not-downloaded-item {{
            background: #fff8e1;
            border-color: #ffc107;
        }}
        .not-downloaded-item:hover {{
            border-color: #ff9800;
            box-shadow: 0 4px 15px rgba(255, 152, 0, 0.2);
        }}
        .article-number.warning {{
            background: linear-gradient(135deg, #ff9800 0%, #f57c00 100%);
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #95a5a6;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 {title}</h1>
            <div class="count">共 {len(html_files)} 篇文章</div>
            <div class="sources">来源：{sources_str}</div>
        </div>
        <div class="article-list">
            {articles_list}
        </div>
        <div class="footer">
            点击文章标题即可跳转阅读
        </div>
    </div>
</body>
</html>'''
    
    def show_pack_config(self):
        output_dir = self.literature_output_var.get()
        if not os.path.exists(output_dir):
            messagebox.showwarning("警告", "请先下载文献！")
            return
        
        html_files = [f for f in os.listdir(output_dir) if f.endswith('.html') and f != 'index.html']
        if not html_files:
            messagebox.showwarning("警告", "未找到已下载的文献！")
            return
        
        config_window = tk.Toplevel(self.root)
        config_window.title("打包配置")
        config_window.geometry("400x350")
        config_window.resizable(False, False)
        
        main_frame = ttk.Frame(config_window, padding=20)
        main_frame.pack(fill="both", expand=True)
        
        ttk.Label(main_frame, text="📦 打包模式配置", font=("Microsoft YaHei", 14, "bold")).pack(pady=(0, 15))
        
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill="x", pady=5)
        ttk.Label(title_frame, text="目录标题:").pack(side="left")
        title_var = tk.StringVar(value="网站目录")
        ttk.Entry(title_frame, textvariable=title_var, width=30).pack(side="right")
        
        bg_frame = ttk.LabelFrame(main_frame, text="背景颜色", padding=10)
        bg_frame.pack(fill="x", pady=10)
        
        bg_var = tk.StringVar(value="white")
        ttk.Radiobutton(bg_frame, text="白色", variable=bg_var, value="white").pack(side="left", padx=10)
        ttk.Radiobutton(bg_frame, text="黑色", variable=bg_var, value="black").pack(side="left", padx=10)
        ttk.Radiobutton(bg_frame, text="灰色", variable=bg_var, value="gray").pack(side="left", padx=10)
        ttk.Radiobutton(bg_frame, text="自定义", variable=bg_var, value="custom").pack(side="left", padx=10)
        
        custom_bg_frame = ttk.Frame(bg_frame)
        custom_bg_frame.pack(fill="x", pady=5)
        ttk.Label(custom_bg_frame, text="自定义颜色:").pack(side="left")
        custom_bg_var = tk.StringVar(value="#f5f6f7")
        ttk.Entry(custom_bg_frame, textvariable=custom_bg_var, width=15).pack(side="left", padx=5)
        
        font_frame = ttk.LabelFrame(main_frame, text="字体颜色", padding=10)
        font_frame.pack(fill="x", pady=10)
        
        font_var = tk.StringVar(value="black")
        ttk.Radiobutton(font_frame, text="黑色", variable=font_var, value="black").pack(side="left", padx=10)
        ttk.Radiobutton(font_frame, text="白色", variable=font_var, value="white").pack(side="left", padx=10)
        ttk.Radiobutton(font_frame, text="自定义", variable=font_var, value="custom").pack(side="left", padx=10)
        
        custom_font_frame = ttk.Frame(font_frame)
        custom_font_frame.pack(fill="x", pady=5)
        ttk.Label(custom_font_frame, text="自定义颜色:").pack(side="left")
        custom_font_var = tk.StringVar(value="#333333")
        ttk.Entry(custom_font_frame, textvariable=custom_font_var, width=15).pack(side="left", padx=5)
        
        info_label = ttk.Label(main_frame, text=f"将打包 {len(html_files)} 篇文献", foreground="#7f8c8d")
        info_label.pack(pady=10)
        
        def do_pack():
            config = {
                'title': title_var.get(),
                'bg_color': custom_bg_var.get() if bg_var.get() == 'custom' else bg_var.get(),
                'font_color': custom_font_var.get() if font_var.get() == 'custom' else font_var.get()
            }
            config_window.destroy()
            self.pack_literature_with_config(output_dir, html_files, config)
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x", pady=10)
        ttk.Button(btn_frame, text="取消", command=config_window.destroy).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="开始打包", command=do_pack, style="Success.TButton").pack(side="right", padx=5)
    
    def pack_literature_with_config(self, output_dir, html_files, config):
        self.literature_log(f"开始打包文献集 ({len(html_files)} 篇)...", "info")
        threading.Thread(target=self.run_pack_literature, args=(output_dir, html_files, config), daemon=True).start()
    
    def pack_literature(self):
        output_dir = self.literature_output_var.get()
        if not os.path.exists(output_dir):
            messagebox.showwarning("警告", "请先下载文献！")
            return
        
        html_files = [f for f in os.listdir(output_dir) if f.endswith('.html')]
        if not html_files:
            messagebox.showwarning("警告", "未找到已下载的文献！")
            return
        
        self.literature_log("开始打包文献集...", "info")
        threading.Thread(target=self.run_pack_literature, args=(output_dir, html_files, {}), daemon=True).start()
    
    def run_pack_literature(self, output_dir, html_files, config=None):
        try:
            if config is None:
                config = {}
            
            pack_dir = os.path.join(output_dir, "literature_pack")
            if not os.path.exists(pack_dir):
                os.makedirs(pack_dir)
            
            articles_dir = os.path.join(pack_dir, "articles")
            if not os.path.exists(articles_dir):
                os.makedirs(articles_dir)
            
            import shutil
            for html_file in html_files:
                src = os.path.join(output_dir, html_file)
                dst = os.path.join(articles_dir, html_file)
                if not os.path.exists(dst):
                    shutil.copy2(src, dst)
            
            index_content = self.generate_literature_index(html_files, config)
            index_path = os.path.join(pack_dir, "index.html")
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(index_content)
            
            self.root.after(0, lambda: self.literature_log(
                f"打包完成！共 {len(html_files)} 篇文献", "success"))
            self.root.after(0, lambda: self.open_file_explorer(pack_dir))
            
        except Exception as e:
            self.root.after(0, lambda: self.literature_log(f"打包错误: {str(e)}", "error"))
    
    def generate_literature_index(self, html_files, config=None):
        if config is None:
            config = {}
        
        title = config.get('title', '文章目录')
        bg_color = config.get('bg_color', 'white')
        font_color = config.get('font_color', 'black')
        
        bg_map = {'white': '#ffffff', 'black': '#1a1a1a', 'gray': '#f5f6f7'}
        font_map = {'white': '#ffffff', 'black': '#333333'}
        
        bg = bg_map.get(bg_color, bg_color)
        font = font_map.get(font_color, font_color)
        
        def get_source_info(html_file):
            file_path = os.path.join('pages', html_file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(content, 'lxml')
                
                canonical = soup.find('link', rel='canonical')
                if canonical and canonical.get('href'):
                    url = canonical['href']
                else:
                    og_url = soup.find('meta', property='og:url')
                    if og_url and og_url.get('content'):
                        url = og_url['content']
                    else:
                        return None
                
                from urllib.parse import urlparse
                parsed = urlparse(url)
                domain = parsed.netloc
                
                site_names = {
                    'zhihu.com': '知乎',
                    'csdn.net': 'CSDN',
                    'juejin.cn': '掘金',
                    'jianshu.com': '简书',
                    'bilibili.com': '哔哩哔哩',
                    'blog.csdn.net': 'CSDN博客',
                    'zhuanlan.zhihu.com': '知乎专栏',
                }
                
                for site_domain, site_name in site_names.items():
                    if site_domain in domain:
                        return site_name
                
                return domain
            except:
                return None
        
        articles_html = ""
        for i, html_file in enumerate(html_files):
            file_title = html_file.replace('.html', '').replace('_', ' ')
            source = get_source_info(html_file)
            source_html = f'<span class="article-source">{source}</span>' if source else ''
            articles_html += f'''
            <div class="article-item" onclick="openArticle('{html_file}')">
                <span class="article-number">{i+1}</span>
                <div class="article-info">
                    <span class="article-title">{file_title}</span>
                    {source_html}
                </div>
                <span class="article-arrow">→</span>
            </div>'''
        
        return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: "Microsoft YaHei", "PingFang SC", "Hiragino Sans GB", sans-serif;
            background: {bg};
            color: {font};
            min-height: 100vh;
            padding: 20px;
        }}
        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            padding: 30px;
            background: rgba(255,255,255,0.95);
            border-radius: 15px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        .header h1 {{
            color: #2c3e50;
            font-size: 28px;
            margin-bottom: 10px;
        }}
        .header p {{
            color: #7f8c8d;
            font-size: 14px;
        }}
        .stats {{
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 15px;
        }}
        .stat-item {{
            text-align: center;
        }}
        .stat-number {{
            font-size: 24px;
            font-weight: bold;
            color: #3498db;
        }}
        .stat-label {{
            font-size: 12px;
            color: #95a5a6;
        }}
        .article-list {{
            background: rgba(255,255,255,0.95);
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }}
        .article-item {{
            background: #f8f9fa;
            padding: 18px 20px;
            margin: 10px 0;
            border-radius: 10px;
            cursor: pointer;
            display: flex;
            align-items: center;
            transition: all 0.3s ease;
            border-left: 4px solid transparent;
        }}
        .article-item:hover {{
            background: #e8f4fd;
            border-left-color: #3498db;
            transform: translateX(5px);
        }}
        .article-number {{
            background: linear-gradient(135deg, #3498db, #2980b9);
            color: white;
            min-width: 35px;
            height: 35px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-right: 15px;
            font-weight: bold;
            font-size: 14px;
        }}
        .article-title {{
            flex: 1;
            font-size: 15px;
            color: #2c3e50;
            line-height: 1.4;
        }}
        .article-info {{
            flex: 1;
            display: flex;
            flex-direction: column;
            gap: 3px;
        }}
        .article-source {{
            font-size: 11px;
            color: #7f8c8d;
            background: #ecf0f1;
            padding: 2px 8px;
            border-radius: 10px;
            display: inline-block;
            width: fit-content;
        }}
        .article-arrow {{
            color: #bdc3c7;
            font-size: 18px;
            transition: transform 0.3s ease;
        }}
        .article-item:hover .article-arrow {{
            transform: translateX(5px);
            color: #3498db;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: rgba(255,255,255,0.8);
            font-size: 12px;
        }}
        .empty-state {{
            text-align: center;
            padding: 40px;
            color: #95a5a6;
        }}
        
        /* 悬浮目录面板样式 */
        .toc-panel {{
            position: fixed;
            top: 50%;
            left: 20px;
            transform: translateY(-50%);
            width: 350px;
            max-height: 80vh;
            background: rgba(255, 255, 255, 0.98);
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            z-index: 999999;
            transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
            overflow: hidden;
        }}
        
        .toc-panel.collapsed {{
            left: -320px;
        }}
        
        .toc-panel.expanded {{
            left: 20px;
        }}
        
        .toc-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            cursor: move;
            user-select: none;
        }}
        
        .toc-title {{
            font-size: 16px;
            font-weight: bold;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .toc-toggle-btn {{
            background: rgba(255, 255, 255, 0.2);
            border: none;
            color: white;
            width: 32px;
            height: 32px;
            border-radius: 50%;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s ease;
            font-size: 18px;
        }}
        
        .toc-toggle-btn:hover {{
            background: rgba(255, 255, 255, 0.3);
            transform: scale(1.1);
        }}
        
        .toc-content {{
            padding: 15px;
            max-height: calc(80vh - 60px);
            overflow-y: auto;
        }}
        
        .toc-content::-webkit-scrollbar {{
            width: 6px;
        }}
        
        .toc-content::-webkit-scrollbar-track {{
            background: #f1f1f1;
            border-radius: 3px;
        }}
        
        .toc-content::-webkit-scrollbar-thumb {{
            background: #c1c1c1;
            border-radius: 3px;
        }}
        
        .toc-content::-webkit-scrollbar-thumb:hover {{
            background: #a1a1a1;
        }}
        
        .toc-article {{
            padding: 12px 15px;
            margin: 8px 0;
            background: #f8f9fa;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
            border-left: 3px solid transparent;
        }}
        
        .toc-article:hover {{
            background: #e3f2fd;
            border-left-color: #2196f3;
            transform: translateX(3px);
        }}
        
        .toc-article-number {{
            background: linear-gradient(135deg, #2196f3, #1976d2);
            color: white;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            font-weight: bold;
            margin-right: 10px;
        }}
        
        .toc-article-title {{
            color: #333;
            font-size: 14px;
            line-height: 1.4;
        }}
        
        /* 悬浮切换按钮 */
        .toc-float-btn {{
            position: fixed;
            top: 50%;
            left: 0;
            transform: translateY(-50%);
            width: 40px;
            height: 80px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 0 12px 12px 0;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 20px;
            z-index: 999998;
            transition: all 0.3s ease;
            box-shadow: 2px 0 10px rgba(0, 0, 0, 0.2);
        }}
        
        .toc-float-btn:hover {{
            width: 50px;
            box-shadow: 4px 0 15px rgba(0, 0, 0, 0.3);
        }}
        
        .toc-float-btn.hidden {{
            left: -50px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📚 文献收藏集</h1>
            <p>离线网页下载器 · 完全本地化浏览</p>
            <div class="stats">
                <div class="stat-item">
                    <div class="stat-number">{len(html_files)}</div>
                    <div class="stat-label">篇文献</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number">100%</div>
                    <div class="stat-label">离线可用</div>
                </div>
            </div>
        </div>
        <div class="article-list">
            {articles_html if articles_html else '<div class="empty-state">暂无文献</div>'}
        </div>
        <div class="footer">
            提示：点击文章标题打开阅读 · 支持鼠标滚轮浏览
        </div>
    </div>
    
    <!-- 悬浮目录面板 -->
    <div class="toc-panel" id="tocPanel">
        <div class="toc-header" id="tocHeader">
            <div class="toc-title">
                <span>📑</span>
                <span>文献目录</span>
            </div>
            <button class="toc-toggle-btn" onclick="toggleTOC()" title="折叠/展开">
                ◀
            </button>
        </div>
        <div class="toc-content">
            {self._generate_toc_articles(html_files)}
        </div>
    </div>
    
    <!-- 悬浮切换按钮 -->
    <div class="toc-float-btn" id="tocFloatBtn" onclick="toggleTOC()" title="展开目录">
        ◀
    </div>
    
    <script>
        function openArticle(file) {{
            window.location.href = 'pages/' + file;
        }}
        
        var tocPanel = document.getElementById('tocPanel');
        var tocFloatBtn = document.getElementById('tocFloatBtn');
        var isCollapsed = false;
        
        function toggleTOC() {{
            isCollapsed = !isCollapsed;
            
            if (isCollapsed) {{
                tocPanel.classList.add('collapsed');
                tocPanel.classList.remove('expanded');
                tocFloatBtn.classList.remove('hidden');
                tocFloatBtn.innerHTML = '▶';
            }} else {{
                tocPanel.classList.remove('collapsed');
                tocPanel.classList.add('expanded');
                tocFloatBtn.classList.add('hidden');
            }}
        }}
        
        // 初始化：默认展开
        tocPanel.classList.add('expanded');
        tocFloatBtn.classList.add('hidden');
        
        // 拖拽功能
        var tocHeader = document.getElementById('tocHeader');
        var isDragging = false;
        var currentX;
        var currentY;
        var initialX;
        var initialY;
        var xOffset = 0;
        var yOffset = 0;
        
        tocHeader.addEventListener('mousedown', dragStart);
        document.addEventListener('mouseup', dragEnd);
        document.addEventListener('mousemove', drag);
        
        function dragStart(e) {{
            initialX = e.clientX - xOffset;
            initialY = e.clientY - yOffset;
            
            if (e.target === tocHeader || tocHeader.contains(e.target)) {{
                isDragging = true;
            }}
        }}
        
        function dragEnd(e) {{
            initialX = currentX;
            initialY = currentY;
            isDragging = false;
        }}
        
        function drag(e) {{
            if (isDragging) {{
                e.preventDefault();
                currentX = e.clientX - initialX;
                currentY = e.clientY - initialY;
                xOffset = currentX;
                yOffset = currentY;
                
                tocPanel.style.transform = 'translate(' + currentX + 'px, ' + currentY + 'px)';
            }}
        }}
    </script>
</body>
</html>'''

    def _generate_toc_articles(self, html_files):
        articles_html = ""
        for i, html_file in enumerate(html_files):
            file_title = html_file.replace('.html', '').replace('_', ' ')
            articles_html += f'''
            <div class="toc-article" onclick="openArticle('{html_file}')">
                <span class="toc-article-number">{i+1}</span>
                <span class="toc-article-title">{file_title}</span>
            </div>'''
        return articles_html

    def select_folder(self):
        if self.path_mode_var.get() == "relative":
            messagebox.showinfo("提示", "相对路径模式下，文件将保存在程序所在目录下，无需修改路径。")
            return
        folder = filedialog.askdirectory(initialdir=self.save_dir_var.get())
        if folder:
            self.save_dir_var.set(folder)
            self.update_path_display()
            self.log("📁 保存路径已更新", "success")
    
    def open_current_dir(self):
        if self.path_mode_var.get() == "relative":
            messagebox.showinfo("提示", "相对路径模式下，文件将保存在程序所在目录下。")
            return
        path = self.get_absolute_path()
        if os.path.exists(path):
            self.open_file_explorer(path)
        else:
            messagebox.showwarning("提示", "目录不存在，请先选择有效的保存路径")
    
    def update_path_display(self):
        current_path = self.save_dir_var.get()
        if not current_path:
            return
        if self.path_mode_var.get() == "relative":
            relative_path = self.get_relative_path(current_path)
            if relative_path != current_path:
                self.save_dir_var.set(relative_path)
            self.path_entry.config(state="disabled")
            self.browse_btn.config(state="disabled")
            self.open_dir_btn.config(state="disabled")
        else:
            absolute_path = self.get_absolute_path()
            self.save_dir_var.set(absolute_path)
            self.path_entry.config(state="normal")
            self.browse_btn.config(state="normal")
            self.open_dir_btn.config(state="normal")
        self.save_config()
    
    def get_absolute_path(self):
        path = self.save_dir_var.get()
        if not path:
            return os.path.join(os.getcwd(), "downloads")
        if os.path.isabs(path):
            return path
        else:
            return os.path.abspath(os.path.join(os.getcwd(), path))
    
    def get_relative_path(self, path):
        try:
            if not os.path.isabs(path):
                return path
            cwd = os.getcwd()
            if path.startswith(cwd):
                relative = os.path.relpath(path, cwd)
                if relative == ".":
                    return "."
                return relative
            return path
        except Exception:
            return path
    
    def update_depth_value(self):
        mode = self.depth_mode_var.get()
        if mode == "page_only":
            self.depth_var.set(0)
        elif mode == "page_next":
            self.depth_var.set(1)
        elif mode == "page_next2":
            self.depth_var.set(2)
        elif mode == "custom":
            self.depth_var.set(self.custom_depth_var.get())
    
    def update_wait_state(self, *args):
        pass
    
    def update_pages_state(self, *args):
        pass
    
    def preview_crawl(self):
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("警告", "请输入目标网址")
            return
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            self.url_var.set(url)
        threading.Thread(target=self.run_preview_crawl, args=(url,), daemon=True).start()
    
    def run_preview_crawl(self, url):
        try:
            self.log("🔍 开始爬取预览...", "info")
            self.log(f"🌐 目标网址: {url}", "info")
            
            mode = self.mode_var.get()
            device_type = self.device_var.get()
            max_depth = self.depth_var.get()
            max_pages = self.max_pages_var.get()
            if max_pages == 0:
                max_pages = self.custom_pages_var.get()
            device_text = "💻 电脑访问" if device_type == "desktop" else "📱 手机访问"
            self.log(f"📱 设备标识: {device_text}", "info")
            self.log(f"📊 爬取深度: {max_depth}", "info")
            if max_pages == -1:
                self.log(f"📄 爬取页数: 无限", "info")
            else:
                self.log(f"📄 爬取页数: {max_pages}页", "info")
            
            headers = self.get_headers()
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code != 200:
                self.log(f"❌ 获取首页失败 (状态码: {response.status_code})", "error")
                return
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            all_links = soup.find_all('a', href=True)
            unique_links = set()
            for link in all_links:
                href = link['href']
                if href.startswith(('http://', 'https://')):
                    if urlparse(href).netloc == urlparse(url).netloc:
                        unique_links.add(href)
            
            all_images = soup.find_all('img', src=True)
            unique_images = set()
            for img in all_images:
                src = img['src']
                if src.startswith(('http://', 'https://', '/')):
                    unique_images.add(src)
            
            all_videos = soup.find_all(['video', 'source'], src=True)
            unique_videos = set()
            for video in all_videos:
                src = video['src']
                if src.startswith(('http://', 'https://', '/')):
                    unique_videos.add(src)
            
            self.log("=" * 50, "info")
            self.log("📊 爬取预览结果", "info")
            self.log("=" * 50, "info")
            self.log(f"🔗 内部链接: {len(unique_links)} 个", "success")
            self.log(f"🖼️ 图片资源: {len(unique_images)} 个", "success")
            self.log(f"🎬 视频资源: {len(unique_videos)} 个", "success")
            
            estimated_pages = len(unique_links)
            if max_pages != -1 and estimated_pages > max_pages:
                estimated_pages = max_pages
            self.log(f"📄 预计爬取页面: {estimated_pages} 页", "success")
            
            avg_page_size = 100 * 1024
            avg_image_size = 50 * 1024
            avg_video_size = 5 * 1024 * 1024
            total_size = estimated_pages * avg_page_size
            total_size += len(unique_images) * avg_image_size
            total_size += len(unique_videos) * avg_video_size
            if total_size < 1024 * 1024:
                size_str = f"{total_size / 1024:.1f} KB"
            elif total_size < 1024 * 1024 * 1024:
                size_str = f"{total_size / (1024 * 1024):.1f} MB"
            else:
                size_str = f"{total_size / (1024 * 1024 * 1024):.1f} GB"
            self.log(f"💾 预计占用空间: {size_str}", "success")
            self.log("=" * 50, "info")
            self.log("✅ 预览完成，可以开始下载", "success")
        except Exception as e:
            self.log(f"❌ 预览失败: {str(e)}", "error")
            import traceback
            self.log(traceback.format_exc(), "error")

    def show_activation_dialog(self):
        from activation_dialog import ActivationDialog
        from license_manager import LicenseManager
        lm = LicenseManager()
        is_activated, _ = lm.check_activation()
        if is_activated:
            return
        
        is_trial, remaining, total = lm.get_trial_status()
        trial_expired = not is_trial or remaining <= 0
        
        dialog = ActivationDialog(trial_expired=trial_expired, trial_remaining=remaining)
        result = dialog.show()
        
        if result:
            self.root.after(100, self._refresh_env_tab)

    def clear_log(self):
        self.log_area.config(state='normal')
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state='disabled')
        self.log("📝 日志已清空", "info")

    def log(self, msg, tag=None):
        self.log_area.config(state='normal')
        timestamp = time.strftime("%H:%M:%S")
        self.log_area.insert(tk.END, f"[{timestamp}] {msg}\n", tag)
        if self.auto_scroll_var.get():
            self.log_area.see(tk.END)
        self.log_area.config(state='disabled')
    
    def clear_log(self):
        self.log_area.config(state='normal')
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state='disabled')
        self.log("🗑️ 日志已清空", "info")

    def open_file_explorer(self, path):
        try:
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
            self.log(f"📂 已打开目录: {path}", "success")
        except Exception as e:
            self.log(f"⚠️ 无法自动打开目录: {e}", "warning")

    def start_thread(self):
        if self.is_running:
            messagebox.showwarning("提示", "当前有任务正在运行中！")
            return
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("提示", "请输入有效的网址！")
            return
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            self.url_var.set(url)
        
        domain_name = urlparse(url).netloc.replace("www.", "")
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        safe_name = f"{domain_name}_{timestamp}"
        self.current_task_dir = os.path.join(self.get_absolute_path(), safe_name)
        
        self.is_running = True
        self.btn_start.config(state="disabled", text="⏳ 下载中...")
        self.btn_stop.config(state="normal", text="⏹️ 停止下载")
        self.clear_log()
        self.status_var.set("🟡 正在下载中...")
        threading.Thread(target=self.run_logic, daemon=True).start()

    def run_logic(self):
        try:
            depth_mode = self.depth_mode_var.get()
            depth_value = self.depth_var.get()
            depth_description = {
                "page_only": "仅本页",
                "page_next": "本页+下页",
                "page_next2": "本页+下2页",
                "custom": f"自定义({depth_value}层)"
            }.get(depth_mode, f"深度{depth_value}")
            
            wait_mode = self.wait_mode_var.get()
            wait_time_map = {
                "no_wait": 0,
                "wait_3": 3,
                "wait_5": 5,
                "wait_10": 10,
                "custom": self.custom_wait_var.get()
            }
            wait_time = wait_time_map.get(wait_mode, 0)
            
            params = {
                'url': self.url_var.get(),
                'output_dir': self.current_task_dir,
                'depth': self.depth_var.get(),
                'mode': self.mode_var.get(),
                'filter_img': self.filter_img_var.get(),
                'filter_video': self.filter_video_var.get(),
                'convert_img': self.convert_img_var.get(),
                'target_fmt': self.target_fmt_var.get(),
                'device_type': self.device_var.get(),
                'wait_time': wait_time,
                'max_pages': self.max_pages_var.get(),
                'use_webview': self.use_webview_var.get()
            }
            
            self.root.after(0, lambda: self.log(f"📂 创建任务目录: {self.current_task_dir}", "info"))
            self.root.after(0, lambda: self.log(f"📊 爬取深度: {depth_description}", "info"))
            device_text = "💻 电脑访问" if self.device_var.get() == "desktop" else "📱 手机访问"
            self.root.after(0, lambda: self.log(f"📱 设备标识: {device_text}", "info"))
            if wait_time > 0:
                self.root.after(0, lambda: self.log(f"⏱️  页面等待: {wait_time} 秒", "info"))
            
            if self.use_webview_var.get():
                self.root.after(0, lambda: self.log("🌐 使用浏览器模式绕过反爬...", "info"))
                from webview_downloader import download_with_webview
                threading.Thread(target=self._run_webview_download, args=(params,), daemon=True).start()
            else:
                self.downloader = CoreDownloader(self, params)
                self.downloader.start()
                self.root.after(0, self.on_finish_success)
        except Exception as e:
            error_msg = f"下载过程中发生错误: {str(e)}"
            error_details = traceback.format_exc()
            self.root.after(0, lambda: self.log(f"❌ 发生错误: {str(e)}", "error"))
            self.root.after(0, lambda: self.status_var.set("🔴 下载失败"))
            self.root.after(0, lambda: ErrorDialog(self.root, "下载错误", error_msg, error_details))
        finally:
            self.is_running = False
            self.root.after(0, lambda: self.btn_start.config(state="normal", text="🚀 开始下载"))
            self.root.after(0, lambda: self.btn_stop.config(state="disabled", text="⏹️ 停止下载"))

    def _run_webview_download(self, params):
        try:
            from webview_downloader import download_with_webview
            success = download_with_webview(self, params)
            if success:
                self.root.after(0, self.on_finish_success)
            else:
                self.root.after(0, lambda: self.log("❌ WebView下载失败", "error"))
                self.root.after(0, lambda: self.status_var.set("🔴 下载失败"))
        except Exception as e:
            self.root.after(0, lambda: self.log(f"❌ WebView错误: {str(e)}", "error"))
        finally:
            self.is_running = False
            self.root.after(0, lambda: self.btn_start.config(state="normal", text="🚀 开始下载"))
            self.root.after(0, lambda: self.btn_stop.config(state="disabled", text="⏹️ 停止下载"))

    def on_finish_success(self):
        self.log("\n✨ ----------- 任务完成 -----------", "success")
        self.status_var.set("🟢 下载完成")
        if self.auto_open_var.get():
            self.open_file_explorer(self.current_task_dir)
        if self.auto_localize_var.get():
            self.log("\n🌐 开始自动本地化部署...", "info")
            threading.Thread(target=self.run_localize, args=(self.current_task_dir, False), daemon=True).start()
    
    def stop_download(self):
        if not self.is_running:
            messagebox.showinfo("提示", "当前没有正在运行的下载任务！")
            return
        
        self.log("⏹️ 正在停止下载任务...", "warning")
        self.btn_stop.config(state="disabled", text="⏹️ 停止中...")
        self.status_var.set("🟡 正在停止...")
        
        if hasattr(self, 'downloader') and self.downloader:
            self.downloader.stop()
    
    def create_pack_config(self, parent):
        main_container = ttk.Frame(parent)
        main_container.pack(fill="both", expand=True)
        
        left_column = ttk.Frame(main_container)
        left_column.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        right_column = ttk.Frame(main_container)
        right_column.pack(side="left", fill="both", expand=True, padx=(5, 0))
        
        website_card = ttk.LabelFrame(left_column, text=" 📁 网站目录 ", padding=15)
        website_card.pack(fill="x", pady=5)
        website_row = ttk.Frame(website_card)
        website_row.pack(fill="x")
        ttk.Label(website_row, text="网站目录:", style="Bold.TLabel").pack(side="left")
        website_entry = ttk.Entry(website_row, textvariable=self.pack_website_dir, width=40, font=("Microsoft YaHei", 9))
        website_entry.pack(side="left", padx=10, fill="x", expand=True)
        browse_btn = ttk.Button(website_row, text="📁 浏览", command=self.select_pack_website_dir)
        browse_btn.pack(side="left", padx=5)
        auto_detect_btn = ttk.Button(website_row, text="🔍 自动检测", command=self.auto_detect_website_dir)
        auto_detect_btn.pack(side="left", padx=5)
        
        path_mode_row = ttk.Frame(website_card)
        path_mode_row.pack(fill="x", pady=5)
        ttk.Label(path_mode_row, text="路径模式:", style="Bold.TLabel").pack(side="left")
        ttk.Radiobutton(path_mode_row, text="📁 相对路径", 
                       variable=self.path_mode_var, value="relative",
                       command=self.update_path_display).pack(side="left", padx=10)
        ttk.Radiobutton(path_mode_row, text="💾 绝对路径", 
                       variable=self.path_mode_var, value="absolute",
                       command=self.update_path_display).pack(side="left", padx=10)
        
        app_info_card = ttk.LabelFrame(left_column, text=" 📋 应用信息 ", padding=15)
        app_info_card.pack(fill="x", pady=5)
        
        self.app_info_labels = {}
        
        row1 = ttk.Frame(app_info_card)
        row1.pack(fill="x", pady=2)
        ttk.Label(row1, text="应用名称:", style="Bold.TLabel").pack(side="left")
        self.app_info_labels["app_name"] = ttk.Label(row1, text=self.pack_app_name.get() or "(未设置)", 
                                                       font=("Microsoft YaHei", 9))
        self.app_info_labels["app_name"].pack(side="left", padx=5)
        ttk.Label(row1, text="版本:", style="Bold.TLabel").pack(side="left", padx=(15, 0))
        self.app_info_labels["version"] = ttk.Label(row1, text=self.pack_version.get() or "1.0", 
                                                     font=("Microsoft YaHei", 9))
        self.app_info_labels["version"].pack(side="left", padx=5)
        ttk.Label(row1, text="发布者:", style="Bold.TLabel").pack(side="left", padx=(15, 0))
        self.app_info_labels["publisher"] = ttk.Label(row1, text=self.pack_publisher.get() or "(未设置)", 
                                                        font=("Microsoft YaHei", 9))
        self.app_info_labels["publisher"].pack(side="left", padx=5)
        
        row2 = ttk.Frame(app_info_card)
        row2.pack(fill="x", pady=2)
        ttk.Label(row2, text="文件说明:", style="Bold.TLabel").pack(side="left")
        self.app_info_labels["file_description"] = ttk.Label(row2, text=self.pack_file_description.get() or "(未设置)", 
                                                               font=("Microsoft YaHei", 9))
        self.app_info_labels["file_description"].pack(side="left", padx=5)
        ttk.Button(row2, text="✏️ 编辑", command=self._show_app_info_editor, 
                   width=8).pack(side="right")
        
        row3 = ttk.Frame(app_info_card)
        row3.pack(fill="x", pady=5)
        ttk.Label(row3, text="窗口标题:", style="Bold.TLabel").pack(side="left")
        title_entry = ttk.Entry(row3, textvariable=self.pack_title, width=25, font=("Microsoft YaHei", 9))
        title_entry.pack(side="left", padx=10)
        ttk.Label(row3, text="图标:", style="Bold.TLabel").pack(side="left", padx=(10, 0))
        icon_entry = ttk.Entry(row3, textvariable=self.pack_icon_path, width=20, font=("Microsoft YaHei", 9))
        icon_entry.pack(side="left", padx=10, fill="x", expand=True)
        icon_btn = ttk.Button(row3, text="📁", command=self.select_pack_icon, width=3)
        icon_btn.pack(side="left", padx=2)
        fetch_icon_btn = ttk.Button(row3, text="🌐", command=self.fetch_website_icon, width=3)
        fetch_icon_btn.pack(side="left", padx=2)
        
        window_card = ttk.LabelFrame(left_column, text=" 🖥️ 窗口配置 ", padding=15)
        window_card.pack(fill="x", pady=5)
        size_row = ttk.Frame(window_card)
        size_row.pack(fill="x", pady=5)
        ttk.Label(size_row, text="宽度:", style="Bold.TLabel").pack(side="left")
        width_spin = ttk.Spinbox(size_row, from_=800, to=1920, textvariable=self.pack_width, width=8)
        width_spin.pack(side="left", padx=10)
        ttk.Label(size_row, text="高度:", style="Bold.TLabel").pack(side="left", padx=(10, 0))
        height_spin = ttk.Spinbox(size_row, from_=600, to=1080, textvariable=self.pack_height, width=8)
        height_spin.pack(side="left", padx=10)
        ttk.Button(size_row, text="🎨 个性化", command=self._show_theme_editor, width=10).pack(side="left", padx=20)
        
        self.theme_preview_frame = ttk.Frame(window_card)
        self.theme_preview_frame.pack(fill="x", pady=5)
        self._update_theme_preview()
        
        option_row = ttk.Frame(window_card)
        option_row.pack(fill="x", pady=5)
        ttk.Checkbutton(option_row, text="显示导航按钮", variable=self.pack_show_nav).pack(side="left", padx=5)
        ttk.Checkbutton(option_row, text="🐛 调试模式", variable=self.pack_debug_mode).pack(side="left", padx=5)
        ttk.Checkbutton(option_row, text="🔒 内部跳转", variable=self.pack_force_internal).pack(side="left", padx=5)
        
        lock_card = ttk.LabelFrame(left_column, text=" 🔒 文件锁 (可选) ", padding=15)
        lock_card.pack(fill="x", pady=5)
        
        lock_row1 = ttk.Frame(lock_card)
        lock_row1.pack(fill="x", pady=5)
        ttk.Checkbutton(lock_row1, text="启用文件锁", variable=self.pack_enable_lock, 
                        command=self._toggle_lock_options).pack(side="left", padx=5)
        ttk.Label(lock_row1, text="密码:", style="Bold.TLabel").pack(side="left", padx=(20, 0))
        self.lock_password_entry = ttk.Entry(lock_row1, textvariable=self.pack_lock_password, 
                                              width=15, font=("Microsoft YaHei", 9), show="*")
        self.lock_password_entry.pack(side="left", padx=5)
        
        # 小眼睛按钮 - 显示/隐藏密码
        self.lock_password_visible = False
        def toggle_password_visibility():
            self.lock_password_visible = not self.lock_password_visible
            if self.lock_password_visible:
                self.lock_password_entry.config(show="")
                eye_btn.config(text="🙈")
            else:
                self.lock_password_entry.config(show="*")
                eye_btn.config(text="👁️")
        
        eye_btn = tk.Button(lock_row1, text="👁️", command=toggle_password_visibility,
                           font=("Microsoft YaHei", 8), width=2, relief="flat",
                           bg="#f0f0f0", cursor="hand2")
        eye_btn.pack(side="left", padx=2)
        
        ttk.Label(lock_row1, text="解锁模式:", style="Bold.TLabel").pack(side="left", padx=(15, 0))
        self.lock_mode_label = ttk.Label(lock_row1, text="每次启动都需要密码", font=("Microsoft YaHei", 9))
        self.lock_mode_label.pack(side="left", padx=5)
        ttk.Button(lock_row1, text="⚙️ 设置", command=self._show_lock_mode_editor, width=6).pack(side="left", padx=5)
        
        # 第二行：文件锁联系人信息
        lock_row2 = ttk.Frame(lock_card)
        lock_row2.pack(fill="x", pady=5)
        ttk.Label(lock_row2, text="忘记密码联系:", style="Bold.TLabel").pack(side="left", padx=5)
        
        # 联系类型选择（QQ、微信、电话等）
        contact_type_combo = ttk.Combobox(lock_row2, textvariable=self.pack_lock_contact_type, 
                                          values=["QQ", "微信", "电话", "邮箱"], 
                                          width=8, font=("Microsoft YaHei", 9), state="readonly")
        contact_type_combo.pack(side="left", padx=5)
        
        # 联系信息输入框
        contact_entry = ttk.Entry(lock_row2, textvariable=self.pack_lock_contact_info, 
                                  width=25, font=("Microsoft YaHei", 9))
        contact_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        # 提示标签
        ttk.Label(lock_row2, text="(用户忘记密码时显示)", font=("Microsoft YaHei", 8), foreground="#666").pack(side="left", padx=5)
        
        self._toggle_lock_options()
        
        output_card = ttk.LabelFrame(left_column, text=" 📂 输出目录 ", padding=15)
        output_card.pack(fill="x", pady=5)
        output_row = ttk.Frame(output_card)
        output_row.pack(fill="x")
        ttk.Label(output_row, text="输出目录:", style="Bold.TLabel").pack(side="left")
        output_entry = ttk.Entry(output_row, textvariable=self.pack_output_dir, width=30, font=("Microsoft YaHei", 9))
        output_entry.pack(side="left", padx=10, fill="x", expand=True)
        output_browse_btn = ttk.Button(output_row, text="📁 浏览", command=self.select_pack_output_dir)
        output_browse_btn.pack(side="left", padx=5)
        
        action_card = ttk.LabelFrame(left_column, text=" 🚀 操作 ", padding=15)
        action_card.pack(fill="x", pady=5)
        button_row = ttk.Frame(action_card)
        button_row.pack(fill="x")
        preview_btn = ttk.Button(button_row, text="👁️ 预览", command=self.preview_pack, style="Primary.TButton")
        preview_btn.pack(side="left", padx=5)
        pack_btn = ttk.Button(button_row, text="📦 开始打包", command=self.start_pack, style="Success.TButton")
        pack_btn.pack(side="left", padx=5)
        
        log_card = ttk.LabelFrame(right_column, text=" 📝 打包日志 ", padding=10)
        log_card.pack(fill="both", expand=True, pady=5)
        self.pack_log_area = scrolledtext.ScrolledText(log_card, height=30, state='disabled', font=("Consolas", 9), bg="#f8f9fa", relief="flat")
        self.pack_log_area.pack(fill="both", expand=True)
        self.pack_log_area.bind("<Button-3>", self.show_pack_log_context_menu)
        self.pack_log_area.tag_config("success", foreground="#27ae60")
        self.pack_log_area.tag_config("error", foreground="#e74c3c")
        self.pack_log_area.tag_config("warning", foreground="#f39c12")
        self.pack_log_area.tag_config("info", foreground="#3498db")
    
    def select_pack_website_dir(self):
        directory = filedialog.askdirectory(title="选择网站目录")
        if directory:
            self.pack_website_dir.set(directory)
            self.pack_log("✅ 已选择网站目录: " + directory, "info")
    
    def auto_detect_website_dir(self):
        search_dirs = []
        
        if self.path_mode_var.get() == "relative":
            base_search_dirs = ["downloads", "literature_downloads", "batch_downloads"]
            for dir_name in base_search_dirs:
                if os.path.exists(dir_name):
                    search_dirs.append(dir_name)
            
            for item in os.listdir('.'):
                item_path = os.path.join('.', item)
                if os.path.isdir(item_path) and item not in ['.', '..', 'assets', 'browser_data', 'python_env', 'logs', 'log', 'temp_pack', 'pack_output', '__pycache__']:
                    if item not in search_dirs:
                        search_dirs.append(item)
        else:
            base_dir = self.save_dir_var.get()
            if base_dir and os.path.exists(base_dir):
                search_dirs.append(base_dir)
            for dir_name in ["downloads", "literature_downloads", "batch_downloads"]:
                if os.path.exists(dir_name) and dir_name not in search_dirs:
                    search_dirs.append(dir_name)
        
        if not search_dirs:
            self.pack_log("❌ 未找到任何下载目录", "error")
            messagebox.showwarning("未找到", "未找到下载目录，请先下载网页")
            return
        
        html_files = []
        for default_dir in search_dirs:
            self.pack_log(f"🔍 搜索目录: {default_dir}", "info")
            if not os.path.exists(default_dir):
                continue
            for item in os.listdir(default_dir):
                item_path = os.path.join(default_dir, item)
                if os.path.isdir(item_path):
                    try:
                        for file in os.listdir(item_path):
                            if file.endswith('.html') and os.path.isfile(os.path.join(item_path, file)):
                                file_path = os.path.join(item_path, file)
                                html_files.append(file_path)
                    except:
                        pass
        
        if not html_files:
            self.pack_log("❌ 未找到HTML文件", "error")
            messagebox.showwarning("未找到", "在下载目录中未找到HTML文件")
            return
        
        html_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        self.pack_log(f"✅ 找到 {len(html_files)} 个HTML文件", "success")
        self.show_html_file_selector(html_files)
    
    def _get_website_title(self, item_path, html_files, default_name):
        try:
            for html_file in html_files:
                html_path = os.path.join(item_path, html_file)
                try:
                    with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read(50000)
                    
                    title_match = re.search(r'<title[^>]*>([^<]+)</title>', content, re.IGNORECASE | re.DOTALL)
                    if title_match:
                        title = title_match.group(1).strip()
                        title = re.sub(r'[\\/*?:"<>|]', '_', title)
                        title = re.sub(r'\s+', ' ', title)
                        title = title[:80]
                        if title and title != default_name:
                            return title
                except:
                    continue
        except:
            pass
        return default_name
    
    def format_time(self, timestamp):
        from datetime import datetime, timedelta
        now = datetime.now()
        file_time = datetime.fromtimestamp(timestamp)
        delta = now - file_time
        now_date = now.date()
        file_date = file_time.date()
        date_diff = (now_date - file_date).days
        print(f"时间戳: {timestamp}, 文件时间: {file_time}, 当前时间: {now}, 日期差: {date_diff}")
        if date_diff == 0:
            hours = delta.seconds // 3600
            if hours == 0:
                minutes = delta.seconds // 60
                if minutes == 0:
                    return "刚刚"
                return f"{minutes}分钟前"
            elif hours == 1:
                return "1小时前"
            else:
                return f"{hours}小时前"
        elif date_diff == 1:
            return "昨天"
        elif date_diff == 2:
            return "前天"
        elif date_diff == 3:
            return "大前天"
        elif date_diff < 7:
            return f"{date_diff}天前"
        elif date_diff < 30:
            weeks = date_diff // 7
            return f"{weeks}周前"
        elif date_diff < 365:
            months = date_diff // 30
            return f"{months}个月前"
        else:
            years = date_diff // 365
            return f"{years}年前"
    
    def choose_color(self, color_var):
        from tkinter import colorchooser
        current_color = color_var.get()
        color = colorchooser.askcolor(color=current_color, title="选择颜色")
        if color[1]:
            color_var.set(color[1])
            self.pack_log(f"✅ 颜色已更新: {color[1]}", "info")
    
    def get_time_color(self, timestamp):
        from datetime import datetime, timedelta
        now = datetime.now()
        file_time = datetime.fromtimestamp(timestamp)
        now_date = now.date()
        file_date = file_time.date()
        date_diff = (now_date - file_date).days
        if date_diff == 0:
            return "#27ae60"
        elif date_diff <= 3:
            return "#f39c12"
        elif date_diff <= 7:
            return "#e67e22"
        elif date_diff <= 30:
            return "#e74c3c"
        else:
            return "#2c3e50"
    
    def show_html_file_selector(self, html_files):
        dialog = tk.Toplevel(self.root)
        dialog.title("选择HTML文件")
        dialog.geometry("1000x600")
        dialog.resizable(True, True)
        dialog.transient(self.root)
        dialog.grab_set()
        
        header_frame = ttk.Frame(dialog, padding=10)
        header_frame.pack(fill="x")
        ttk.Label(header_frame, 
                text=f"找到 {len(html_files)} 个HTML文件", 
                font=("Microsoft YaHei", 12, "bold"),
                foreground="#2c3e50").pack(side="left")
        ttk.Label(header_frame, 
                text="（按修改时间排序）", 
                font=("Microsoft YaHei", 9),
                foreground="#7f8c8d").pack(side="left", padx=10)
        
        list_frame = ttk.Frame(dialog)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)
        scroll_frame = ttk.Frame(list_frame)
        scroll_frame.pack(fill="both", expand=True)
        scrollbar = ttk.Scrollbar(scroll_frame)
        scrollbar.pack(side="right", fill="y")
        columns = ("filename", "path", "mtime", "size")
        tree = ttk.Treeview(scroll_frame, columns=columns, show="headings", yscrollcommand=scrollbar.set)
        tree.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=tree.yview)
        tree.heading("filename", text="文件名")
        tree.heading("path", text="路径")
        tree.heading("mtime", text="下载时间")
        tree.heading("size", text="大小")
        tree.column("filename", width=250)
        tree.column("path", width=450)
        tree.column("mtime", width=150)
        tree.column("size", width=100)
        
        for i, file_path in enumerate(html_files):
            filename = os.path.basename(file_path)
            dir_path = os.path.dirname(file_path)
            mtime = os.path.getmtime(file_path)
            mtime_str = self.format_time(mtime)
            size = os.path.getsize(file_path)
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.1f} KB"
            else:
                size_str = f"{size / (1024 * 1024):.1f} MB"
            abs_path = os.path.abspath(file_path)
            if abs_path.startswith(os.path.abspath(os.getcwd())):
                path_display = f"相对路径: {file_path}"
            else:
                path_display = f"绝对路径: {file_path}"
            color = self.get_time_color(mtime)
            tree.insert("", "end", values=(filename, path_display, mtime_str, size_str), tags=(str(i),))
            tree.tag_configure(str(i), foreground=color)
        
        def on_double_click(event):
            selection = tree.selection()
            if selection:
                item = selection[0]
                values = tree.item(item)['values']
                path = values[1].replace("相对路径: ", "").replace("绝对路径: ", "")
                dir_path = os.path.dirname(path)
                self.pack_website_dir.set(dir_path)
                filename = os.path.basename(path)
                self.pack_html_file.set(filename)
                app_name = os.path.splitext(filename)[0]
                self.pack_app_name.set(app_name)
                self.pack_title.set(app_name)
                self.pack_log("✅ 已选择: " + path, "success")
                self.pack_log(f"   应用名称: {app_name}", "info")
                dialog.destroy()
        tree.bind("<Double-1>", on_double_click)
        
        button_frame = ttk.Frame(dialog, padding=10)
        button_frame.pack(fill="x")
        def on_select():
            selection = tree.selection()
            if selection:
                item = selection[0]
                values = tree.item(item)['values']
                path = values[1].replace("相对路径: ", "").replace("绝对路径: ", "")
                dir_path = os.path.dirname(path)
                self.pack_website_dir.set(dir_path)
                filename = os.path.basename(path)
                self.pack_html_file.set(filename)
                app_name = os.path.splitext(filename)[0]
                self.pack_app_name.set(app_name)
                self.pack_title.set(app_name)
                self.pack_log("✅ 已选择: " + path, "success")
                self.pack_log(f"   应用名称: {app_name}", "info")
                dialog.destroy()
            else:
                messagebox.showwarning("警告", "请先选择一个HTML文件")
        def on_cancel():
            dialog.destroy()
        ttk.Button(button_frame, text="✅ 选择", command=on_select, style="Success.TButton").pack(side="right", padx=5)
        ttk.Button(button_frame, text="❌ 取消", command=on_cancel).pack(side="right", padx=5)
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (dialog.winfo_width() // 2)
        y = (dialog.winfo_screenheight() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")
    
    def select_pack_icon(self):
        file_path = filedialog.askopenfilename(
            title="选择图片文件",
            filetypes=[
                ("图片文件", "*.png *.jpg *.jpeg *.bmp *.gif *.ico"),
                ("PNG文件", "*.png"),
                ("JPEG文件", "*.jpg *.jpeg"),
                ("BMP文件", "*.bmp"),
                ("ICO文件", "*.ico"),
                ("所有文件", "*.*")
            ]
        )
        if file_path:
            if file_path.lower().endswith('.ico'):
                self.pack_icon_path.set(file_path)
                self.pack_log("✅ 已选择ICO图标: " + file_path, "info")
            else:
                self.show_icon_editor(file_path)
    
    def show_icon_editor(self, image_path):
        from PIL import Image, ImageTk, ImageDraw
        
        editor = tk.Toplevel(self.root)
        editor.title("🎨 图标编辑器")
        editor.geometry("850x800")
        editor.resizable(True, True)
        editor.transient(self.root)
        editor.grab_set()
        
        screen_width = editor.winfo_screenwidth()
        screen_height = editor.winfo_screenheight()
        x = (screen_width - 850) // 2
        y = (screen_height - 800) // 2
        editor.geometry(f"850x800+{x}+{y}")
        
        try:
            original_image = Image.open(image_path)
            if original_image.mode in ('RGBA', 'LA', 'P'):
                original_image = original_image.convert('RGBA')
            else:
                original_image = original_image.convert('RGB')
        except Exception as e:
            messagebox.showerror("错误", f"无法打开图片: {e}")
            editor.destroy()
            return
        
        main_frame = ttk.Frame(editor, padding="10")
        main_frame.pack(fill="both", expand=True)
        
        toolbar = ttk.Frame(main_frame)
        toolbar.pack(fill="x", pady=(0, 10))
        
        ttk.Label(toolbar, text="📐 裁剪区域大小:", font=("Microsoft YaHei", 9)).pack(side="left", padx=(0, 5))
        crop_size_var = tk.IntVar(value=min(original_image.width, original_image.height))
        crop_spinbox = ttk.Spinbox(toolbar, from_=16, to=max(original_image.width, original_image.height), 
                                   textvariable=crop_size_var, width=8)
        crop_spinbox.pack(side="left", padx=5)
        ttk.Label(toolbar, text="像素", font=("Microsoft YaHei", 9)).pack(side="left")
        
        ttk.Button(toolbar, text="🔄 重置位置", command=lambda: reset_crop()).pack(side="left", padx=20)
        ttk.Button(toolbar, text="📐 自动裁剪", command=lambda: auto_crop()).pack(side="left", padx=5)
        
        canvas_frame = ttk.LabelFrame(main_frame, text=" 🖼️ 图片预览（拖动选择裁剪区域） ", padding="5")
        canvas_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        canvas = tk.Canvas(canvas_frame, bg="#2d2d2d", highlightthickness=0)
        canvas.pack(fill="both", expand=True)
        
        preview_frame = ttk.LabelFrame(main_frame, text=" 👁️ 图标预览 ", padding="10")
        preview_frame.pack(fill="x", pady=(0, 10))
        
        preview_labels = {}
        preview_sizes = [16, 32, 48, 64, 128, 256]
        preview_row = ttk.Frame(preview_frame)
        preview_row.pack(fill="x")
        
        for size in preview_sizes:
            frame = ttk.Frame(preview_row)
            frame.pack(side="left", padx=10, pady=5)
            ttk.Label(frame, text=f"{size}x{size}", font=("Microsoft YaHei", 8)).pack()
            preview_labels[size] = ttk.Label(frame, text="", width=size//8+2)
            preview_labels[size].pack()
        
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill="x")
        
        ttk.Button(btn_frame, text="❌ 取消", command=editor.destroy).pack(side="right", padx=5)
        
        save_btn = ttk.Button(btn_frame, text="💾 生成ICO图标", style="Success.TButton",
                             command=lambda: save_icon())
        save_btn.pack(side="right", padx=5)
        
        state = {
            'offset_x': 0,
            'offset_y': 0,
            'scale': 1.0,
            'dragging': False,
            'last_x': 0,
            'last_y': 0,
            'photo': None,
            'display_width': 0,
            'display_height': 0
        }
        
        def update_preview():
            crop_size = crop_size_var.get()
            x = state['offset_x']
            y = state['offset_y']
            
            for size in preview_sizes:
                try:
                    crop_region = original_image.crop((x, y, x + crop_size, y + crop_size))
                    resized = crop_region.resize((size, size), Image.Resampling.LANCZOS)
                    
                    if resized.mode == 'RGBA':
                        photo = ImageTk.PhotoImage(resized)
                    else:
                        photo = ImageTk.PhotoImage(resized.convert('RGBA'))
                    
                    preview_labels[size].config(image=photo, text="")
                    preview_labels[size].image = photo
                except Exception as e:
                    pass
        
        def draw_canvas():
            canvas.delete("all")
            
            canvas_width = canvas.winfo_width()
            canvas_height = canvas.winfo_height()
            
            if canvas_width < 10 or canvas_height < 10:
                editor.after(50, draw_canvas)
                return
            
            img_width, img_height = original_image.size
            
            scale_x = canvas_width / img_width
            scale_y = canvas_height / img_height
            scale = min(scale_x, scale_y, 1.0)
            state['scale'] = scale
            
            display_width = int(img_width * scale)
            display_height = int(img_height * scale)
            state['display_width'] = display_width
            state['display_height'] = display_height
            
            x_offset = (canvas_width - display_width) // 2
            y_offset = (canvas_height - display_height) // 2
            
            display_image = original_image.resize((display_width, display_height), Image.Resampling.LANCZOS)
            if display_image.mode != 'RGBA':
                display_image = display_image.convert('RGBA')
            
            state['photo'] = ImageTk.PhotoImage(display_image)
            canvas.create_image(x_offset, y_offset, anchor="nw", image=state['photo'])
            
            crop_size = crop_size_var.get()
            crop_display = int(crop_size * scale)
            
            crop_x = x_offset + int(state['offset_x'] * scale)
            crop_y = y_offset + int(state['offset_y'] * scale)
            
            canvas.create_rectangle(crop_x, crop_y, crop_x + crop_display, crop_y + crop_display,
                                   outline="#00ff00", width=2, dash=(5, 3))
            
            canvas.create_rectangle(crop_x - 1, crop_y - 1, crop_x + crop_display + 1, crop_y + crop_display + 1,
                                   outline="#000000", width=1)
            
            canvas.create_text(crop_x + crop_display // 2, crop_y - 10, 
                              text=f"{crop_size}x{crop_size}", fill="#00ff00", font=("Consolas", 9))
            
            state['canvas_offset_x'] = x_offset
            state['canvas_offset_y'] = y_offset
        
        def on_mouse_down(event):
            state['dragging'] = True
            state['last_x'] = event.x
            state['last_y'] = event.y
            canvas.config(cursor="fleur")
        
        def on_mouse_move(event):
            if not state['dragging']:
                return
            
            dx = event.x - state['last_x']
            dy = event.y - state['last_y']
            
            scale = state['scale']
            real_dx = int(dx / scale)
            real_dy = int(dy / scale)
            
            crop_size = crop_size_var.get()
            img_width, img_height = original_image.size
            
            new_x = state['offset_x'] + real_dx
            new_y = state['offset_y'] + real_dy
            
            new_x = max(0, min(new_x, img_width - crop_size))
            new_y = max(0, min(new_y, img_height - crop_size))
            
            state['offset_x'] = new_x
            state['offset_y'] = new_y
            state['last_x'] = event.x
            state['last_y'] = event.y
            
            draw_canvas()
            update_preview()
        
        def on_mouse_up(event):
            state['dragging'] = False
            canvas.config(cursor="")
        
        def on_mouse_wheel(event):
            delta = event.delta // 120
            crop_size = crop_size_var.get()
            new_size = crop_size + delta * 10
            new_size = max(16, min(new_size, min(original_image.width, original_image.height)))
            crop_size_var.set(new_size)
            
            img_width, img_height = original_image.size
            if state['offset_x'] + new_size > img_width:
                state['offset_x'] = img_width - new_size
            if state['offset_y'] + new_size > img_height:
                state['offset_y'] = img_height - new_size
            
            draw_canvas()
            update_preview()
        
        def reset_crop():
            img_width, img_height = original_image.size
            crop_size = min(img_width, img_height)
            crop_size_var.set(crop_size)
            state['offset_x'] = (img_width - crop_size) // 2
            state['offset_y'] = (img_height - crop_size) // 2
            draw_canvas()
            update_preview()
        
        def auto_crop():
            img_width, img_height = original_image.size
            crop_size = min(img_width, img_height)
            crop_size_var.set(crop_size)
            state['offset_x'] = (img_width - crop_size) // 2
            state['offset_y'] = (img_height - crop_size) // 2
            draw_canvas()
            update_preview()
        
        def save_icon():
            crop_size = crop_size_var.get()
            x = state['offset_x']
            y = state['offset_y']
            
            try:
                crop_region = original_image.crop((x, y, x + crop_size, y + crop_size))
                
                if crop_region.mode != 'RGBA':
                    crop_region = crop_region.convert('RGBA')
                
                if crop_size < 256:
                    self.pack_log(f"⚠️ 裁剪区域({crop_size}x{crop_size})小于推荐尺寸(256x256)", "warning")
                    self.pack_log(f"   建议：使用更大的裁剪区域或更高分辨率的原图", "info")
                
                icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
                icon_images = []
                
                for size in icon_sizes:
                    resized = crop_region.resize(size, Image.Resampling.LANCZOS)
                    if resized.mode != 'RGBA':
                        resized = resized.convert('RGBA')
                    icon_images.append(resized)
                
                base_path = get_external_base_path()
                ico_dir = os.path.join(base_path, 'ico')
                os.makedirs(ico_dir, exist_ok=True)
                
                save_path = os.path.join(ico_dir, 'icon.ico')
                
                if os.path.exists(save_path):
                    try:
                        os.remove(save_path)
                        self.pack_log(f"🗑️ 已删除旧图标文件", "info")
                    except Exception as del_e:
                        self.pack_log(f"⚠️ 无法删除旧图标: {del_e}", "warning")
                        messagebox.showwarning("警告", f"无法删除旧图标文件，可能被占用。\n请关闭其他程序后重试。\n\n错误: {del_e}")
                        return
                
                icon_images[0].save(save_path, format='ICO', sizes=[icon_sizes[0]])
                for img, size in zip(icon_images[1:], icon_sizes[1:]):
                    img.save(save_path, format='ICO', append=True)
                
                if not os.path.exists(save_path):
                    raise Exception("ICO文件保存失败，文件不存在")
                
                file_size = os.path.getsize(save_path)
                self.pack_log(f"✅ ICO文件大小: {file_size} 字节", "info")
                
                self.pack_icon_path.set(save_path)
                self.pack_log(f"✅ 已生成多尺寸ICO图标: {save_path}", "success")
                self.pack_log(f"   包含尺寸: 16x16, 32x32, 48x48, 64x64, 128x128, 256x256", "info")
                
                messagebox.showinfo("成功", f"图标已保存到:\n{save_path}\n\n软件已自动读取该图标。\n\n注意: 如果文件管理器中显示旧图标，是Windows图标缓存问题，\n实际文件已更新，打包时会使用新图标。")
                editor.destroy()
            
            except Exception as e:
                messagebox.showerror("错误", f"保存图标失败: {e}")
        
        def on_key_press(event):
            step = 5
            crop_size = crop_size_var.get()
            img_width, img_height = original_image.size
            
            key = event.keysym.lower()
            if key in ('left', 'a'):
                state['offset_x'] = max(0, state['offset_x'] - step)
            elif key in ('right', 'd'):
                state['offset_x'] = min(img_width - crop_size, state['offset_x'] + step)
            elif key in ('up', 'w'):
                state['offset_y'] = max(0, state['offset_y'] - step)
            elif key in ('down', 's'):
                state['offset_y'] = min(img_height - crop_size, state['offset_y'] + step)
            
            draw_canvas()
            update_preview()
        
        canvas.bind("<Button-1>", on_mouse_down)
        canvas.bind("<B1-Motion>", on_mouse_move)
        canvas.bind("<ButtonRelease-1>", on_mouse_up)
        canvas.bind("<MouseWheel>", on_mouse_wheel)
        editor.bind("<Key>", on_key_press)
        canvas.focus_set()
        
        def on_size_change(*args):
            img_width, img_height = original_image.size
            crop_size = crop_size_var.get()
            if state['offset_x'] + crop_size > img_width:
                state['offset_x'] = max(0, img_width - crop_size)
            if state['offset_y'] + crop_size > img_height:
                state['offset_y'] = max(0, img_height - crop_size)
            draw_canvas()
            update_preview()
        
        crop_size_var.trace_add('write', on_size_change)
        
        img_width, img_height = original_image.size
        crop_size = min(img_width, img_height)
        crop_size_var.set(crop_size)
        state['offset_x'] = (img_width - crop_size) // 2
        state['offset_y'] = (img_height - crop_size) // 2
        editor.after(100, lambda: [draw_canvas(), update_preview()])
    
    def fetch_website_icon(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("获取网站图标")
        dialog.geometry("450x350")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        screen_width = dialog.winfo_screenwidth()
        screen_height = dialog.winfo_screenheight()
        x = (screen_width - 450) // 2
        y = (screen_height - 350) // 2
        dialog.geometry(f"450x350+{x}+{y}")
        
        frame = ttk.Frame(dialog, padding="15")
        frame.pack(fill="both", expand=True)
        
        ttk.Label(frame, text="请输入网页地址:", font=("Microsoft YaHei", 10)).pack(anchor="w")
        
        url_var = tk.StringVar()
        if self.url_var.get():
            url_var.set(self.url_var.get())
        url_entry = ttk.Entry(frame, textvariable=url_var, width=55, font=("Microsoft YaHei", 10))
        url_entry.pack(fill="x", pady=(5, 15))
        url_entry.focus_set()
        
        preview_frame = ttk.LabelFrame(frame, text="图标预览", padding="10")
        preview_frame.pack(fill="both", expand=True, pady=(0, 10))
        
        preview_label = ttk.Label(preview_frame, text="输入URL后点击\"获取图标\"按钮", font=("Microsoft YaHei", 9))
        preview_label.pack(expand=True)
        
        icon_data_ref = {'data': None, 'img': None}
        
        def do_fetch():
            url = url_var.get().strip()
            if not url:
                messagebox.showwarning("警告", "请输入网页地址")
                return
            
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            try:
                preview_label.config(text="正在获取图标...")
                dialog.update()
                
                from urllib.parse import urlparse
                import requests
                from bs4 import BeautifulSoup
                from PIL import Image, ImageTk
                import io
                
                parsed = urlparse(url)
                base_url = f"{parsed.scheme}://{parsed.netloc}"
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                favicon_url = None
                
                try:
                    response = requests.get(url, headers=headers, timeout=10)
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    link_tags = soup.find_all('link', rel=lambda x: x and 'icon' in x.lower())
                    if link_tags:
                        for link in link_tags:
                            href = link.get('href')
                            if href:
                                favicon_url = href
                                if 'apple-touch-icon' in str(link.get('rel', '')):
                                    break
                    
                    if not favicon_url:
                        meta_tag = soup.find('meta', property='og:image')
                        if meta_tag:
                            favicon_url = meta_tag.get('content')
                except:
                    pass
                
                if not favicon_url:
                    favicon_url = f"{base_url}/favicon.ico"
                
                if favicon_url.startswith('//'):
                    favicon_url = 'https:' + favicon_url
                elif favicon_url.startswith('/'):
                    favicon_url = f"{base_url}{favicon_url}"
                elif not favicon_url.startswith(('http://', 'https://')):
                    favicon_url = f"{base_url}/{favicon_url}"
                
                self.pack_log(f"🌐 正在下载图标: {favicon_url}", "info")
                
                response = requests.get(favicon_url, headers=headers, timeout=10)
                response.raise_for_status()
                
                icon_data = response.content
                img = Image.open(io.BytesIO(icon_data))
                
                if img.mode == 'P':
                    img = img.convert('RGBA')
                elif img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                icon_data_ref['data'] = icon_data
                icon_data_ref['img'] = img
                
                display_img = img.copy()
                display_img.thumbnail((128, 128), Image.Resampling.LANCZOS)
                
                photo = ImageTk.PhotoImage(display_img)
                
                for widget in preview_frame.winfo_children():
                    widget.destroy()
                
                img_label = ttk.Label(preview_frame, image=photo)
                img_label.image = photo
                img_label.pack(expand=True)
                
                size_label = ttk.Label(preview_frame, text=f"原始尺寸: {img.size[0]} x {img.size[1]} 像素", font=("Microsoft YaHei", 9))
                size_label.pack(pady=(5, 0))
                
            except Exception as e:
                preview_label.config(text=f"获取失败: {e}")
                self.pack_log(f"❌ 获取图标失败: {e}", "error")
        
        def do_confirm():
            if icon_data_ref['img'] is None:
                messagebox.showwarning("警告", "请先获取图标")
                return
            
            try:
                from PIL import Image
                import io
                
                img = icon_data_ref['img']
                
                icon_dir = os.path.join(os.path.dirname(__file__), 'temp_icons')
                os.makedirs(icon_dir, exist_ok=True)
                
                icon_path = os.path.join(icon_dir, 'favicon.ico')
                
                sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
                
                if img.mode == 'RGBA':
                    save_img = img
                else:
                    save_img = img.convert('RGBA')
                
                save_img.save(icon_path, format='ICO', sizes=sizes)
                
                self.pack_icon_path.set(icon_path)
                self.pack_log(f"✅ 图标已保存: {icon_path}", "success")
                
                dialog.destroy()
                messagebox.showinfo("成功", f"网站图标已成功获取并保存！\n\n图标路径: {icon_path}")
                
            except Exception as e:
                self.pack_log(f"❌ 保存图标失败: {e}", "error")
                messagebox.showerror("错误", f"保存图标失败: {e}")
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x")
        
        ttk.Button(btn_frame, text="获取图标", command=do_fetch, width=12).pack(side="left", padx=(0, 10))
        ttk.Button(btn_frame, text="确定使用", command=do_confirm, width=12).pack(side="left", padx=(0, 10))
        ttk.Button(btn_frame, text="取消", command=dialog.destroy, width=12).pack(side="right")
    
    def _show_app_info_editor(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("编辑应用信息")
        dialog.geometry("400x250")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 400) // 2
        y = (dialog.winfo_screenheight() - 250) // 2
        dialog.geometry(f"+{x}+{y}")
        
        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill="both", expand=True)
        
        temp_vars = {
            "app_name": tk.StringVar(value=self.pack_app_name.get()),
            "version": tk.StringVar(value=self.pack_version.get()),
            "publisher": tk.StringVar(value=self.pack_publisher.get()),
            "file_description": tk.StringVar(value=self.pack_file_description.get()),
        }
        
        fields = [
            ("应用名称:", "app_name", 30),
            ("版本:", "version", 15),
            ("发布者:", "publisher", 30),
            ("文件说明:", "file_description", 35),
        ]
        
        entries = {}
        for label_text, key, width in fields:
            row = ttk.Frame(frame)
            row.pack(fill="x", pady=5)
            ttk.Label(row, text=label_text, width=10).pack(side="left")
            entry = ttk.Entry(row, textvariable=temp_vars[key], width=width, font=("Microsoft YaHei", 9))
            entry.pack(side="left", padx=10, fill="x", expand=True)
            entries[key] = entry
        
        def do_save():
            self.pack_app_name.set(temp_vars["app_name"].get())
            self.pack_version.set(temp_vars["version"].get())
            self.pack_publisher.set(temp_vars["publisher"].get())
            self.pack_file_description.set(temp_vars["file_description"].get())
            
            self.app_info_labels["app_name"].config(text=temp_vars["app_name"].get() or "(未设置)")
            self.app_info_labels["version"].config(text=temp_vars["version"].get() or "(未设置)")
            self.app_info_labels["publisher"].config(text=temp_vars["publisher"].get() or "(未设置)")
            self.app_info_labels["file_description"].config(text=temp_vars["file_description"].get() or "(未设置)")
            
            dialog.destroy()
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=(15, 0))
        ttk.Button(btn_frame, text="💾 保存", command=do_save, width=12).pack(side="left", padx=(0, 10))
        ttk.Button(btn_frame, text="取消", command=dialog.destroy, width=12).pack(side="left")
    
    def _toggle_lock_options(self):
        enabled = self.pack_enable_lock.get()
        state = 'normal' if enabled else 'disabled'
        try:
            self.lock_password_entry.config(state=state)
        except:
            pass
        # 同时控制联系人信息输入框的状态
        try:
            # 获取lock_row2中的子控件
            lock_card = self.lock_password_entry.master.master
            for child in lock_card.winfo_children():
                if isinstance(child, ttk.Frame) and child != self.lock_password_entry.master:
                    for widget in child.winfo_children():
                        if isinstance(widget, (ttk.Entry, ttk.Combobox)):
                            widget.config(state=state)
        except:
            pass
    
    def _show_lock_mode_editor(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("解锁模式设置")
        dialog.geometry("320x150")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 320) // 2
        y = (dialog.winfo_screenheight() - 150) // 2
        dialog.geometry(f"+{x}+{y}")
        
        frame = ttk.Frame(dialog, padding=15)
        frame.pack(fill="both", expand=True)
        
        ttk.Label(frame, text="选择解锁模式:", font=("Microsoft YaHei", 10, "bold")).pack(anchor="w", pady=(0, 10))
        
        # 创建两个按钮作为选项
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=5)
        
        def select_always():
            self.pack_lock_mode.set("always")
            self.lock_mode_label.config(text="每次启动都需要密码")
            dialog.destroy()
        
        def select_once():
            self.pack_lock_mode.set("once")
            self.lock_mode_label.config(text="每台电脑只需输入一次")
            dialog.destroy()
        
        # 根据当前选择高亮显示
        current_mode = self.pack_lock_mode.get()
        
        always_btn = tk.Button(btn_frame, text="🔒 每次启动都需要密码", 
                               command=select_always,
                               font=("Microsoft YaHei", 9),
                               bg="#3498db" if current_mode == "always" else "#f0f0f0",
                               fg="white" if current_mode == "always" else "#333",
                               relief="flat", padx=10, pady=5)
        always_btn.pack(fill="x", pady=3)
        
        once_btn = tk.Button(btn_frame, text="💻 每台电脑只需输入一次", 
                             command=select_once,
                             font=("Microsoft YaHei", 9),
                             bg="#3498db" if current_mode == "once" else "#f0f0f0",
                             fg="white" if current_mode == "once" else "#333",
                             relief="flat", padx=10, pady=5)
        once_btn.pack(fill="x", pady=3)
    
    def _show_theme_editor(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("个性化设置")
        dialog.geometry("400x200")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 400) // 2
        y = (dialog.winfo_screenheight() - 200) // 2
        dialog.geometry(f"+{x}+{y}")
        
        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill="both", expand=True)
        
        temp_vars = {
            "title_bar_color": tk.StringVar(value=self.pack_title_bar_color.get()),
            "text_color": tk.StringVar(value=self.pack_text_color.get()),
            "border_color": tk.StringVar(value=self.pack_border_color.get()),
        }
        
        def update_preview():
            try:
                preview_frame.config(bg=temp_vars["title_bar_color"].get())
                preview_label.config(bg=temp_vars["title_bar_color"].get(), fg=temp_vars["text_color"].get())
            except:
                pass
        
        row1 = ttk.Frame(frame)
        row1.pack(fill="x", pady=5)
        ttk.Label(row1, text="标题栏颜色:", width=12).pack(side="left")
        entry1 = ttk.Entry(row1, textvariable=temp_vars["title_bar_color"], width=10)
        entry1.pack(side="left", padx=5)
        ttk.Button(row1, text="🎨", width=3, command=lambda: self._choose_color_to_var(temp_vars["title_bar_color"], update_preview)).pack(side="left")
        
        row2 = ttk.Frame(frame)
        row2.pack(fill="x", pady=5)
        ttk.Label(row2, text="文字颜色:", width=12).pack(side="left")
        entry2 = ttk.Entry(row2, textvariable=temp_vars["text_color"], width=10)
        entry2.pack(side="left", padx=5)
        ttk.Button(row2, text="🎨", width=3, command=lambda: self._choose_color_to_var(temp_vars["text_color"], update_preview)).pack(side="left")
        
        row3 = ttk.Frame(frame)
        row3.pack(fill="x", pady=5)
        ttk.Label(row3, text="边框颜色:", width=12).pack(side="left")
        entry3 = ttk.Entry(row3, textvariable=temp_vars["border_color"], width=10)
        entry3.pack(side="left", padx=5)
        ttk.Button(row3, text="🎨", width=3, command=lambda: self._choose_color_to_var(temp_vars["border_color"], update_preview)).pack(side="left")
        
        preview_frame = tk.Frame(frame, height=30, bg=self.pack_title_bar_color.get())
        preview_frame.pack(fill="x", pady=10)
        preview_frame.pack_propagate(False)
        preview_label = tk.Label(preview_frame, text="预览效果：这是标题栏", bg=self.pack_title_bar_color.get(), fg=self.pack_text_color.get())
        preview_label.pack(expand=True)
        
        def do_save():
            self.pack_title_bar_color.set(temp_vars["title_bar_color"].get())
            self.pack_text_color.set(temp_vars["text_color"].get())
            self.pack_border_color.set(temp_vars["border_color"].get())
            self._update_theme_preview()
            dialog.destroy()
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill="x", pady=(5, 0))
        ttk.Button(btn_frame, text="确定", command=do_save, width=10).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="取消", command=dialog.destroy, width=10).pack(side="left")
    
    def _choose_color_to_var(self, var, callback=None):
        from tkinter import colorchooser
        color = colorchooser.askcolor(color=var.get(), title="选择颜色")
        if color[1]:
            var.set(color[1])
            if callback:
                callback()
    
    def _update_theme_preview(self):
        for widget in self.theme_preview_frame.winfo_children():
            widget.destroy()
        
        try:
            title_color = self.pack_title_bar_color.get()
            text_color = self.pack_text_color.get()
            border_color = self.pack_border_color.get()
            
            preview = tk.Frame(self.theme_preview_frame, height=25, bg=title_color, 
                              highlightbackground=border_color, highlightthickness=1)
            preview.pack(fill="x", padx=5, pady=2)
            preview.pack_propagate(False)
            
            label = tk.Label(preview, text="预览：标题栏效果", bg=title_color, fg=text_color, 
                           font=("Microsoft YaHei", 9))
            label.pack(expand=True)
        except Exception as e:
            pass
    
    def select_pack_output_dir(self):
        directory = filedialog.askdirectory(title="选择输出目录")
        if directory:
            self.pack_output_dir.set(directory)
            self.pack_log("✅ 已选择输出目录: " + directory, "info")
    
    def pack_log(self, msg, tag="info"):
        self.pack_log_area.config(state='normal')
        self.pack_log_area.insert('end', msg + '\n', tag)
        self.pack_log_area.see('end')
        self.pack_log_area.config(state='disabled')
        self._save_log_to_file(msg, tag, log_type="pack")
    
    def _save_log_to_file(self, msg, tag="info", log_type="preview"):
        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            logs_dir = os.path.join(base_dir, "logs")
            os.makedirs(logs_dir, exist_ok=True)
            
            import datetime
            current_date = datetime.datetime.now().strftime("%Y%m%d")
            if log_type == "pack":
                log_file = os.path.join(logs_dir, f"pack_log_{current_date}.txt")
            else:
                log_file = os.path.join(logs_dir, f"preview_log_{current_date}.txt")
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] [{tag.upper()}] {msg}\n"
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            pass
    
    def preview_pack(self):
        if not self.pack_website_dir.get():
            self.pack_log("ℹ️ 未选择网站目录，使用默认预览（必应主页）", "info")
            website_dir_abs = os.path.dirname(__file__)
            html_path_abs = "https://www.bing.com"
            html_path = "https://www.bing.com"
            is_remote = True
        else:
            if not os.path.exists(self.pack_website_dir.get()):
                messagebox.showerror("错误", "网站目录不存在")
                return
            if self.pack_html_file.get():
                html_path = os.path.join(self.pack_website_dir.get(), self.pack_html_file.get())
            else:
                html_path = os.path.join(self.pack_website_dir.get(), "index.html")
                if not os.path.exists(html_path):
                    html_files = [f for f in os.listdir(self.pack_website_dir.get()) if f.endswith('.html')]
                    if html_files:
                        html_path = os.path.join(self.pack_website_dir.get(), html_files[0])
                    else:
                        messagebox.showerror("错误", "网站目录中未找到HTML文件")
                        return
            if not os.path.exists(html_path):
                messagebox.showerror("错误", f"HTML文件不存在: {html_path}")
                return

            website_dir_abs = os.path.abspath(self.pack_website_dir.get())
            html_path_abs = os.path.abspath(html_path)
            is_remote = False

        config = {
            'website_dir': website_dir_abs if not is_remote else '',
            'html_path': html_path_abs,
            'width': self.pack_width.get(),
            'height': self.pack_height.get(),
            'title': self.pack_title.get() if self.pack_title.get() else '预览',
            'title_bar_color': self.pack_title_bar_color.get(),
            'text_color': self.pack_text_color.get(),
            'border_color': self.pack_border_color.get(),
            'show_nav': self.pack_show_nav.get(),
            'force_internal': self.pack_force_internal.get(),
            'enable_lock': self.pack_enable_lock.get(),
            'lock_password': self.pack_lock_password.get() if self.pack_enable_lock.get() else '',
            'lock_mode': self.pack_lock_mode.get(),
            # 文件锁联系人信息（用于密码忘记时联系）
            'lock_contact_type': self.pack_lock_contact_type.get() if self.pack_enable_lock.get() else '',
            'lock_contact_info': self.pack_lock_contact_info.get() if self.pack_enable_lock.get() else ''
        }

        import subprocess
        import json
        import tempfile
        import base64
        
        inject_js_path = get_resource_path('inject.js')
        if os.path.exists(inject_js_path):
            with open(inject_js_path, 'r', encoding='utf-8') as f:
                inject_js_content = f.read()
        else:
            inject_js_content = ''
        
        inject_js_b64 = base64.b64encode(inject_js_content.encode('utf-8')).decode('utf-8')
        
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
                config_file = f.name
            
            preview_script = f'''
import sys
import json
import os
import base64
import hashlib

config_file = r"{config_file}"
with open(config_file, 'r', encoding='utf-8') as f:
    config = json.load(f)

INJECT_JS_B64 = "{inject_js_b64}"
INJECT_JS = base64.b64decode(INJECT_JS_B64).decode('utf-8')

def get_machine_id():
    try:
        import platform
        import uuid
        machine_id = platform.node() + str(uuid.getnode())
        return hashlib.sha256(machine_id.encode()).hexdigest()[:16]
    except:
        return "default_machine"

def show_password_dialog():
    import tkinter as tk
    from tkinter import ttk, messagebox
    
    result = [False]
    
    dialog = tk.Tk()
    dialog.title("🔒 程序已锁定")
    # 增加窗口高度以容纳更多内容
    dialog.geometry("400x220")
    dialog.resizable(False, False)
    dialog.configure(bg="#f5f5f5")
    
    dialog.update_idletasks()
    width = dialog.winfo_width()
    height = dialog.winfo_height()
    x = (dialog.winfo_screenwidth() // 2) - (width // 2)
    y = (dialog.winfo_screenheight() // 2) - (height // 2)
    dialog.geometry(f'{{width}}x{{height}}+{{x}}+{{y}}')
    
    dialog.protocol("WM_DELETE_WINDOW", lambda: dialog.destroy())
    
    # 主框架
    frame = tk.Frame(dialog, bg="#f5f5f5", padx=20, pady=15)
    frame.pack(fill="both", expand=True)
    
    # 标题
    title_label = tk.Label(frame, text="🔒 程序已锁定", font=("Microsoft YaHei", 14, "bold"), bg="#f5f5f5", fg="#333")
    title_label.pack(pady=(0, 5))
    
    # 提示文字
    hint_label = tk.Label(frame, text="此程序已设置文件锁，需要输入密码才能访问", 
                          font=("Microsoft YaHei", 9), bg="#f5f5f5", fg="#666")
    hint_label.pack(pady=(0, 10))
    
    # 密码输入区域
    password_frame = tk.Frame(frame, bg="#f5f5f5")
    password_frame.pack(fill="x", pady=5)
    
    tk.Label(password_frame, text="解锁密码:", font=("Microsoft YaHei", 10), bg="#f5f5f5").pack(side="left", padx=(0, 10))
    
    password_var = tk.StringVar()
    password_entry = tk.Entry(password_frame, textvariable=password_var, show="*", 
                              width=20, font=("Microsoft YaHei", 10), relief="solid", bd=1)
    password_entry.pack(side="left", padx=5)
    password_entry.focus()
    
    # 小眼睛按钮 - 显示/隐藏密码
    password_visible = False
    def toggle_password():
        nonlocal password_visible
        password_visible = not password_visible
        if password_visible:
            password_entry.config(show="")
            eye_btn.config(text="🙈")
        else:
            password_entry.config(show="*")
            eye_btn.config(text="👁️")
    
    eye_btn = tk.Button(password_frame, text="👁️", command=toggle_password,
                       font=("Microsoft YaHei", 8), width=2, relief="flat",
                       bg="#f0f0f0", cursor="hand2")
    eye_btn.pack(side="left", padx=2)
    
    # 问号按钮 - 显示联系人信息
    def show_contact_info():
        contact_type = config.get('lock_contact_type', '')
        contact_info = config.get('lock_contact_info', '')
        
        if contact_type and contact_info:
            messagebox.showinfo("忘记密码？", 
                f"如果您忘记了密码，请联系程序发布者：\n\n"
                f"{contact_type}: {contact_info}\n\n"
                f"请提供您的机器码以获取帮助。", 
                parent=dialog)
        else:
            messagebox.showinfo("忘记密码？", 
                "程序发布者未设置联系方式。\n\n"
                "请尝试使用您设置密码时使用的常用密码，\n"
                "或联系程序发布者获取帮助。", 
                parent=dialog)
    
    help_btn = tk.Button(password_frame, text="❓", command=show_contact_info,
                        font=("Microsoft YaHei", 8), width=2, relief="flat",
                        bg="#e3f2fd", cursor="hand2", fg="#1976d2")
    help_btn.pack(side="left", padx=5)
    
    def verify():
        entered = password_var.get()
        if entered == config.get('lock_password', ''):
            result[0] = True
            dialog.destroy()
        else:
            messagebox.showerror("密码错误", "密码不正确，请重试\n\n提示：点击密码框旁边的 ❓ 可查看联系方式", parent=dialog)
            password_var.set("")
            password_entry.focus()
    
    def on_enter(event):
        verify()
    
    password_entry.bind('<Return>', on_enter)
    
    # 按钮区域
    btn_frame = tk.Frame(frame, bg="#f5f5f5")
    btn_frame.pack(pady=15)
    
    unlock_btn = tk.Button(btn_frame, text="🔓 解锁", command=verify, 
                          font=("Microsoft YaHei", 10), width=12,
                          bg="#4caf50", fg="white", relief="flat", cursor="hand2")
    unlock_btn.pack(side="left", padx=10)
    
    exit_btn = tk.Button(btn_frame, text="❌ 退出", command=dialog.destroy, 
                        font=("Microsoft YaHei", 10), width=12,
                        bg="#f44336", fg="white", relief="flat", cursor="hand2")
    exit_btn.pack(side="left", padx=10)
    
    dialog.mainloop()
    return result[0]

if config.get('enable_lock', False) and config.get('lock_password', ''):
    if not show_password_dialog():
        sys.exit(0)

try:
    import webview
    
    html_path = config.get('html_path', '')
    is_remote = html_path.startswith('http')
    
    if is_remote:
        html = html_path
    else:
        html = f'file:///{{html_path}}'
    
    window = webview.create_window(
        config.get('title', '预览'),
        html,
        width=config.get('width', 1200),
        height=config.get('height', 850),
        background_color=config.get('title_bar_color', '#2d2d2d')
    )
    
    def inject_ui():
        show_nav = config.get('show_nav', True)
        
        if show_nav:
            config_js = "window.__WEBEXE_CONFIG__ = {{"
            config_js += "titleBarColor: '" + config.get('title_bar_color', '#2d2d2d') + "',"
            config_js += "textColor: '" + config.get('text_color', '#ffffff') + "',"
            config_js += "borderColor: '" + config.get('border_color', '#1a1a1a') + "',"
            config_js += "showNav: " + str(show_nav).lower() + ","
            config_js += "showWindowControls: false,"
            config_js += "forceInternal: " + str(config.get('force_internal', False)).lower() + ","
            config_js += "customTitle: '" + config.get('title', '预览') + "'"
            config_js += "}};"
            window.evaluate_js(config_js)
            window.evaluate_js(INJECT_JS)
    
    try:
        window.events.loaded += inject_ui
    except AttributeError:
        try:
            window.loaded += inject_ui
        except AttributeError:
            inject_ui()
    
    webview.start()
except ImportError:
    print("请先安装 pywebview: pip install pywebview")
    input("按回车键退出...")
except Exception as e:
    print(f"预览错误: {{e}}")
    input("按回车键退出...")
finally:
    try:
        os.unlink(config_file)
    except:
        pass
'''
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='utf-8') as f:
                f.write(preview_script)
                script_file = f.name
            
            try:
                # 【关键】始终使用 python_env 中的独立 Python 解释器启动预览
                # 原因：在 Nuitka/PyInstaller 打包后，sys.executable 指向软件本身
                # 如果使用 sys.executable，会导致程序递归启动自身，造成无限循环
                # ensure_python_env() 确保返回的是 python_env/python.exe，而不是软件本身
                python_exe = self.ensure_python_env()
                self.pack_log(f"🔍 使用Python环境启动预览: {python_exe}", "info")
            except Exception as e:
                # 如果 python_env 不可用，检查是否是打包环境
                if hasattr(sys, 'frozen'):
                    # 在打包环境中，尝试找到 python_env 目录
                    # 这是后备方案，优先使用 ensure_python_env() 的返回值
                    exe_dir = os.path.dirname(sys.executable)
                    python_env_python = os.path.join(exe_dir, 'python_env', 'python.exe')
                    if os.path.exists(python_env_python):
                        python_exe = python_env_python
                        self.pack_log(f"🔍 使用打包环境Python启动预览: {python_exe}", "info")
                    else:
                        # 【警告】最后手段：使用系统 Python
                        # 注意：sys.executable 在打包环境中指向软件本身，会导致递归！
                        # 只有在开发环境（非打包）中才安全使用
                        python_exe = sys.executable
                        self.pack_log(f"⚠️ 使用系统Python启动预览: {python_exe}", "warning")
                else:
                    # 开发环境：sys.executable 是安全的（指向 python.exe）
                    python_exe = sys.executable
                    self.pack_log(f"⚠️ 使用系统Python启动预览: {python_exe}", "warning")
            
            subprocess.Popen(
                [python_exe, script_file],
                creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0,
                shell=False
            )
            messagebox.showinfo("预览", "预览窗口正在启动，请稍候...")
            self.pack_log(f"✅ 已启动预览进程: {html_path}", "normal")
        except Exception as e:
            error_msg = f"无法启动预览进程: {e}"
            messagebox.showerror("错误", error_msg)
            self.pack_log(f"❌ {error_msg}", "error")
    
    def start_pack(self):
        if not self.pack_website_dir.get():
            messagebox.showwarning("警告", "请先选择网站目录")
            return
        if not os.path.exists(self.pack_website_dir.get()):
            messagebox.showerror("错误", "网站目录不存在")
            return
        if self.pack_html_file.get():
            html_path = os.path.join(self.pack_website_dir.get(), self.pack_html_file.get())
        else:
            html_path = os.path.join(self.pack_website_dir.get(), "index.html")
            if not os.path.exists(html_path):
                html_files = [f for f in os.listdir(self.pack_website_dir.get()) if f.endswith('.html')]
                if html_files:
                    html_path = os.path.join(self.pack_website_dir.get(), html_files[0])
                else:
                    messagebox.showerror("错误", "网站目录中未找到HTML文件")
                    return
        if not os.path.exists(html_path):
            messagebox.showerror("错误", "HTML文件不存在: " + html_path)
            return
        threading.Thread(target=self.pack_to_exe, daemon=True).start()
    
    def get_python_env_path(self):
        """
        获取Python环境的目标路径 - 使用exe所在目录
        
        【重要说明】
        此方法返回的是独立的 Python 环境目录路径（python_env/），
        用于存放打包和预览所需的独立 Python 解释器。
        
        【与软件本身的区别】
        - python_env/python.exe：独立的 Python 解释器，用于执行 Python 脚本
        - sys.executable：在打包后指向软件本身（WebDownloader.exe）
        
        【为什么需要独立环境】
        1. 打包后的软件（WebDownloader.exe）不是 Python 解释器
        2. 如果尝试用软件本身执行 Python 脚本，会导致递归启动
        3. 独立的 python_env 包含完整的 Python 运行时和 PyInstaller 等工具
        
        【目录结构】
        python_env/
        ├── python.exe          # Python 解释器（关键）
        ├── python313.dll       # Python 运行时
        └── Lib/
            └── site-packages/  # 包含 PyInstaller、webview 等依赖
        """
        base_dir = get_external_base_path()
        env_dir = os.path.join(base_dir, 'python_env')
        return env_dir
    
    def _extract_python_env(self):
        """提前解压Python环境"""
        try:
            python_exe = self.ensure_python_env()
            if python_exe and os.path.exists(python_exe):
                messagebox.showinfo("成功", f"Python环境已解压完成！\n\n路径: {python_exe}")
                self._refresh_env_tab()
            else:
                messagebox.showerror("失败", "Python环境解压失败，请查看日志")
        except FileNotFoundError as e:
            error_msg = str(e)
            if "python_env.zip" in error_msg:
                self._show_download_dialog()
            else:
                messagebox.showerror("错误", f"解压失败: {error_msg}")
        except Exception as e:
            messagebox.showerror("错误", f"解压失败: {str(e)}")
    
    def _show_download_dialog(self):
        """显示下载提示对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("缺少 Python 环境")
        dialog.geometry("400x180")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() - 400) // 2
        y = (dialog.winfo_screenheight() - 180) // 2
        dialog.geometry(f"+{x}+{y}")
        
        main_frame = tk.Frame(dialog, bg="#f5f5f5", padx=20, pady=15)
        main_frame.pack(fill="both", expand=True)
        
        tk.Label(
            main_frame,
            text="⚠️ 找不到 Python 环境包",
            font=("Microsoft YaHei", 14, "bold"),
            bg="#f5f5f5",
            fg="#e74c3c"
        ).pack(pady=(0, 10))
        
        tk.Label(
            main_frame,
            text="请向作者获取最新的 python_env.zip 文件",
            font=("Microsoft YaHei", 10),
            bg="#f5f5f5",
            fg="#333"
        ).pack()
        
        tk.Label(
            main_frame,
            text="获取后将 python_env.zip 放置到程序所在目录即可。",
            font=("Microsoft YaHei", 9),
            bg="#f5f5f5",
            fg="#666"
        ).pack(pady=(10, 15))
        
        btn_frame = tk.Frame(main_frame, bg="#f5f5f5")
        btn_frame.pack(fill="x")
        
        def close_dialog():
            dialog.destroy()
        
        tk.Button(
            btn_frame,
            text="关闭",
            font=("Microsoft YaHei", 10),
            bg="#95a5a6",
            fg="white",
            relief="flat",
            padx=20,
            pady=8,
            cursor="hand2",
            command=close_dialog
        ).pack()
        
        dialog.protocol("WM_DELETE_WINDOW", close_dialog)
    
    def _refresh_env_tab(self):
        """刷新环境管理标签页"""
        try:
            for widget in self.env_tab.winfo_children():
                widget.destroy()
            self.create_env_config(self.env_tab)
        except Exception as e:
            print(f"刷新环境标签页失败: {e}")
    
    def _fix_pyvenv_cfg(self, env_dir, python_exe):
        """修复pyvenv.cfg中的绝对路径，使其可以在其他电脑上使用"""
        import re
        pyvenv_cfg_path = os.path.join(env_dir, 'pyvenv.cfg')
        
        if not os.path.exists(pyvenv_cfg_path):
            return
        
        try:
            with open(pyvenv_cfg_path, 'r', encoding='utf-8') as f:
                cfg_content = f.read()
            
            env_dir_escaped = env_dir.replace('\\', '\\\\')
            python_exe_escaped = python_exe.replace('\\', '\\\\')
            
            cfg_content = re.sub(r'^home\s*=.*$', 'home = ' + env_dir_escaped, cfg_content, flags=re.MULTILINE)
            cfg_content = re.sub(r'^executable\s*=.*$', 'executable = ' + python_exe_escaped, cfg_content, flags=re.MULTILINE)
            cfg_content = re.sub(r'^command\s*=.*$', 'command = ' + python_exe_escaped + ' -m venv --clear ' + env_dir_escaped, cfg_content, flags=re.MULTILINE)
            
            with open(pyvenv_cfg_path, 'w', encoding='utf-8') as f:
                f.write(cfg_content)
            self.pack_log(f"✅ 已修复pyvenv.cfg配置文件", "success")
        except Exception as e:
            self.pack_log(f"⚠️ 修复pyvenv.cfg失败: {e}", "warning")
    
    def ensure_python_env(self):
        """
        确保Python环境已解压，若未解压则从资源中解压（带进度条）
        
        【重要说明】
        此方法返回的必须是独立的 Python 解释器路径（python_env/python.exe），
        绝对不能使用 sys.executable（即本软件自身）。
        
        【原因】
        1. 在 Nuitka/PyInstaller 打包后的环境中，sys.executable 指向的是打包后的 EXE 文件本身
        2. 如果使用 sys.executable 来执行 Python 脚本，会导致程序递归启动自身
        3. 这会造成无限循环，最终耗尽系统资源
        
        【使用场景】
        - 打包预览（preview_pack）：需要启动独立的 Python 进程来运行预览脚本
        - 开始打包（start_pack）：需要调用 PyInstaller 等工具进行打包
        
        【正确用法】
        python_exe = self.ensure_python_env()  # ✅ 正确：返回 python_env/python.exe
        # 永远不要这样做：
        # python_exe = sys.executable  # ❌ 错误：在打包环境中会指向软件本身
        """
        import zipfile
        import shutil
        import subprocess
        import tkinter.ttk as ttk
        
        env_dir = self.get_python_env_path()
        
        # 优先查找 python_env/python.exe（独立Python环境）
        # 备选：python_env/Scripts/python.exe（某些venv结构的Python环境）
        python_exe = os.path.join(env_dir, 'python.exe')
        if not os.path.exists(python_exe):
            python_exe = os.path.join(env_dir, 'Scripts', 'python.exe')
        
        pyvenv_cfg = os.path.join(env_dir, 'pyvenv.cfg')
        
        if os.path.exists(python_exe):
            self.pack_log(f"✅ 使用已有的Python环境: {env_dir}", "success")
            if os.path.exists(pyvenv_cfg):
                self._fix_pyvenv_cfg(env_dir, python_exe)
            return python_exe
        
        progress_window = None
        progress_var = None
        progress_label = None
        progress_bar = None
        
        try:
            progress_window = tk.Toplevel(self.root)
            progress_window.title("初始化打包环境")
            progress_window.geometry("400x120")
            progress_window.resizable(False, False)
            progress_window.transient(self.root)
            progress_window.grab_set()
            
            window_width = 400
            window_height = 120
            screen_width = progress_window.winfo_screenwidth()
            screen_height = progress_window.winfo_screenheight()
            x = (screen_width - window_width) // 2
            y = (screen_height - window_height) // 2
            progress_window.geometry(f"{window_width}x{window_height}+{x}+{y}")
            
            progress_label = tk.Label(progress_window, text="正在解压打包所需的环境，请稍后...", font=("Microsoft YaHei", 10))
            progress_label.pack(pady=(15, 5))
            
            progress_var = tk.DoubleVar()
            progress_bar = ttk.Progressbar(progress_window, variable=progress_var, maximum=100, length=350, mode='determinate')
            progress_bar.pack(pady=10)
            
            percent_label = tk.Label(progress_window, text="0%", font=("Microsoft YaHei", 9))
            percent_label.pack()
            
            progress_window.update()
        except Exception as e:
            self.pack_log(f"⚠️ 无法创建进度窗口: {e}", "warning")
        
        def update_progress(value, text=None):
            if progress_window and progress_var:
                progress_var.set(value)
                if text and progress_label:
                    progress_label.config(text=text)
                if percent_label:
                    percent_label.config(text=f"{int(value)}%")
                progress_window.update()
        
        try:
            self.pack_log("📦 正在解压Python环境，请稍候...", "info")
            update_progress(5, "正在准备解压...")
            
            base_path = get_external_base_path()
            zip_path = os.path.join(base_path, 'python_env.zip')
            
            if not os.path.exists(zip_path):
                error_msg = """找不到 Python 环境包 python_env.zip

请从以下地址下载：
https://wwbfd.lanzoum.com/iyJBM3kb8coj

下载完成后，将 python_env.zip 放置到程序所在目录即可。"""
                raise FileNotFoundError(error_msg)
            
            if os.path.exists(env_dir):
                self.pack_log(f"🗑️ 删除旧的Python环境: {env_dir}", "info")
                update_progress(10, "正在清理旧环境...")
                shutil.rmtree(env_dir)
            
            os.makedirs(env_dir, exist_ok=True)
            
            update_progress(15, "正在解压打包所需的环境...")
            
            with zipfile.ZipFile(zip_path, 'r') as zf:
                file_list = zf.namelist()
                total_files = len(file_list)
                
                for i, file in enumerate(file_list):
                    if file.endswith('/'):
                        target_dir = os.path.join(env_dir, file)
                        os.makedirs(target_dir, exist_ok=True)
                    else:
                        target_path = os.path.join(env_dir, file)
                        target_dir = os.path.dirname(target_path)
                        if target_dir and not os.path.exists(target_dir):
                            os.makedirs(target_dir, exist_ok=True)
                        with zf.open(file) as src, open(target_path, 'wb') as dst:
                            dst.write(src.read())
                    
                    if i % 50 == 0 or i == total_files - 1:
                        progress = 15 + (i + 1) / total_files * 70
                        update_progress(progress, f"正在解压打包所需的环境... ({i+1}/{total_files})")
            
            update_progress(90, "正在验证环境...")
            
            python_exe = os.path.join(env_dir, 'python.exe')
            if not os.path.exists(python_exe):
                python_exe = os.path.join(env_dir, 'Scripts', 'python.exe')
            
            if not os.path.exists(python_exe):
                raise RuntimeError("解压后找不到python.exe，环境包可能损坏")
            
            self._fix_pyvenv_cfg(env_dir, python_exe)
            
            self.pack_log(f"✅ Python环境已解压到: {env_dir}", "success")
            
            update_progress(95, "正在验证Python环境...")
            
            self.pack_log("🔍 验证Python环境...", "info")
            test_cmd = [python_exe, '-c', 'import sys; print("Python环境验证通过")']
            result = subprocess.run(test_cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                self.pack_log(f"❌ Python环境验证失败: {result.stderr}", "error")
                raise RuntimeError(f"Python环境不完整: {result.stderr}")
            else:
                self.pack_log(f"✅ {result.stdout.strip()}", "success")
            
            update_progress(100, "环境准备完成！")
            
            try:
                self.root.after(100, self._refresh_env_tab)
            except:
                pass
            
            return python_exe
        except Exception as e:
            self.pack_log(f"❌ 解压Python环境失败: {e}", "error")
            raise
        finally:
            if progress_window:
                try:
                    progress_window.destroy()
                except:
                    pass
    
    def pack_to_exe(self):
        try:
            pack_mode = self.pack_mode.get()
            
            if pack_mode == "source":
                self.pack_to_source()
                return
            
            self.pack_log("🚀 开始打包（单文件EXE模式）...", "info")
            self.pack_log("=" * 50, "info")
            self.pack_log("📝 生成打包脚本...", "info")
            script_content = self.generate_pack_script()
            temp_dir = os.path.join(os.getcwd(), "temp_pack")
            
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                    self.pack_log("🗑️ 已清理旧的构建缓存", "info")
                except Exception as e:
                    self.pack_log(f"⚠️ 无法清理构建缓存: {e}", "warning")
            
            os.makedirs(temp_dir, exist_ok=True)
            app_name = self.pack_app_name.get().replace(' ', '_')
            script_path = os.path.join(temp_dir, f"{app_name}.py")
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            self.pack_log(f"✅ 脚本已保存: {script_path}", "success")
            
            output_dir = self.pack_output_dir.get()
            os.makedirs(output_dir, exist_ok=True)
            self.pack_log("🔨 开始PyInstaller打包...", "info")
            
            windowed_option = '--console' if self.pack_debug_mode.get() else '--windowed'
            self.pack_log(f"📋 打包模式: {'调试模式 (显示控制台)' if self.pack_debug_mode.get() else '正常模式 (无控制台)'}", "info")
            
            pyinstaller_args = [
                '--onefile',
                '--name=' + self.pack_app_name.get(),
                windowed_option,
                '--hidden-import=webview',
                '--hidden-import=webview.platforms.edgechromium',
                '--hidden-import=webview.platforms.winforms',
                '--hidden-import=webview.platforms.cef',
                '--hidden-import=webview.platforms.cocoa',
                '--hidden-import=webview.platforms.gtk',
                '--hidden-import=webview.platforms.qt',
                '--hidden-import=tkinter',
                '--hidden-import=tkinter.ttk',
                '--hidden-import=tkinter.messagebox',
                '--collect-all=webview',
                '--collect-all=certifi',
                '--add-data', f'{os.path.abspath(self.pack_website_dir.get())};website',
                '--distpath', output_dir,
                '--workpath', os.path.join(temp_dir, 'build'),
                '--specpath', temp_dir,
            ]
            
            version_info_path = os.path.join(temp_dir, 'version_info.txt')
            version_nums = self.pack_version.get().split(".")
            while len(version_nums) < 4:
                version_nums.append("0")
            filevers = ", ".join(version_nums[:4])
            
            version_info_content = f'''VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({filevers}),
    prodvers=({filevers}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'080404b0',
        [StringStruct(u'CompanyName', u'{self.pack_publisher.get()}'),
        StringStruct(u'FileDescription', u'{self.pack_file_description.get() or self.pack_app_name.get()}'),
        StringStruct(u'FileVersion', u'{self.pack_version.get()}'),
        StringStruct(u'InternalName', u'{self.pack_app_name.get()}'),
        StringStruct(u'LegalCopyright', u'Copyright (c) {self.pack_publisher.get()}'),
        StringStruct(u'OriginalFilename', u'{self.pack_app_name.get()}.exe'),
        StringStruct(u'ProductName', u'{self.pack_app_name.get()}'),
        StringStruct(u'ProductVersion', u'{self.pack_version.get()}')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [2052, 1200])])
  ]
)
'''
            with open(version_info_path, 'w', encoding='utf-8') as f:
                f.write(version_info_content)
            pyinstaller_args.append('--version-file=' + version_info_path)
            self.pack_log(f"✅ 版本信息: {self.pack_version.get()}, 发布者: {self.pack_publisher.get()}", "info")
            
            pyinstaller_args.append(script_path)
            
            if self.pack_icon_path.get() and os.path.exists(self.pack_icon_path.get()):
                pyinstaller_args.append('--icon=' + self.pack_icon_path.get())
                self.pack_log(f"✅ 使用图标: {self.pack_icon_path.get()}", "info")
            else:
                icon_path = get_resource_path('assets/icon.ico')
                if os.path.exists(icon_path):
                    pyinstaller_args.append('--icon=' + icon_path)
                    self.pack_log(f"✅ 使用内置图标: {icon_path}", "info")
                else:
                    self.pack_log("⚠️ 未找到图标文件，将使用默认图标", "warning")
            
            try:
                # 【关键】使用独立的 Python 环境进行打包，而不是软件本身
                # 原因：在 Nuitka/PyInstaller 打包后，sys.executable 指向软件本身
                # 如果使用 sys.executable，会导致程序递归启动自身，造成无限循环
                # ensure_python_env() 确保返回的是 python_env/python.exe
                python_exe = self.ensure_python_env()
                self.pack_log(f"🔍 使用本地Python环境: {python_exe}", "info")
            except Exception as e:
                self.pack_log(f"❌ 无法获取本地Python环境: {e}", "error")
                messagebox.showerror("错误", f"无法获取本地Python环境:\n{e}\n\n请确保 python_env.zip 文件存在并可以正常解压。")
                return
            
            self.pack_log(f"🔍 使用Python: {python_exe}", "info")
            # 使用 python_env 中的 PyInstaller 进行打包
            cmd = [python_exe, '-m', 'PyInstaller'] + pyinstaller_args
            
            self.pack_log(f"执行命令: {' '.join(cmd)}", "info")
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            for line in process.stdout:
                self.pack_log(line.strip(), "info")
            process.wait()
            if process.returncode == 0:
                exe_path = os.path.join(output_dir, self.pack_app_name.get() + ".exe")
                py_path = os.path.join(output_dir, self.pack_app_name.get() + ".py")
                script_output_path = os.path.join(output_dir, self.pack_app_name.get() + "_pack.py")
                
                self.pack_log("=" * 50, "info")
                self.pack_log(f"✅ 打包成功!", "success")
                self.pack_log(f"📁 EXE文件位置: {exe_path}", "success")
                
                try:
                    shutil.copy(script_path, py_path)
                    self.pack_log(f"📁 Python源文件位置: {py_path}", "success")
                except Exception as e:
                    self.pack_log(f"⚠️ 无法复制Python源文件: {e}", "warning")
                
                try:
                    shutil.copy(script_path, script_output_path)
                    self.pack_log(f"📁 打包脚本位置: {script_output_path}", "success")
                except Exception as e:
                    self.pack_log(f"⚠️ 无法复制打包脚本: {e}", "warning")
                
                try:
                    if os.name == 'nt':
                        os.startfile(output_dir)
                    else:
                        subprocess.Popen(['xdg-open', output_dir])
                    self.pack_log(f"✅ 已打开输出文件夹: {output_dir}", "success")
                except Exception as e:
                    self.pack_log(f"⚠️ 无法自动打开文件夹: {e}", "warning")
                
                messagebox.showinfo("成功", f"打包成功!\nEXE文件位置:\n{exe_path}\n\nPython源文件位置:\n{py_path}\n\n打包脚本位置:\n{script_output_path}\n\n已自动打开输出文件夹")
            else:
                self.pack_log("=" * 50, "info")
                self.pack_log(f"❌ 打包失败 (返回码: {process.returncode})", "error")
                messagebox.showerror("失败", "打包失败，请查看日志")
        except Exception as e:
            self.pack_log(f"❌ 打包过程出错: {str(e)}", "error")
            self.pack_log(traceback.format_exc(), "error")
            messagebox.showerror("错误", f"打包失败: {str(e)}")
    
    def pack_to_source(self):
        try:
            self.pack_log("🚀 开始打包（源代码模式）...", "info")
            self.pack_log("=" * 50, "info")
            self.pack_log("📝 生成打包脚本...", "info")
            
            output_dir = self.pack_output_dir.get()
            app_name = self.pack_app_name.get().replace(' ', '_')
            source_output_dir = os.path.join(output_dir, f"{app_name}_source")
            
            if os.path.exists(source_output_dir):
                shutil.rmtree(source_output_dir)
            os.makedirs(source_output_dir, exist_ok=True)
            
            script_content = self.generate_pack_script()
            script_path = os.path.join(source_output_dir, f"{app_name}.py")
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            self.pack_log(f"✅ 主脚本已保存: {script_path}", "success")
            
            website_source = self.pack_website_dir.get()
            website_dest = os.path.join(source_output_dir, "website")
            if os.path.exists(website_source):
                shutil.copytree(website_source, website_dest)
                self.pack_log(f"✅ 网站资源已复制: {website_dest}", "success")
            else:
                self.pack_log(f"⚠️ 网站目录不存在: {website_source}", "warning")
            
            if self.pack_icon_path.get() and os.path.exists(self.pack_icon_path.get()):
                icon_dest = os.path.join(source_output_dir, "icon.ico")
                shutil.copy(self.pack_icon_path.get(), icon_dest)
                self.pack_log(f"✅ 图标已复制: {icon_dest}", "success")
            else:
                default_icon = get_resource_path('assets/icon.ico')
                if os.path.exists(default_icon):
                    icon_dest = os.path.join(source_output_dir, "icon.ico")
                    shutil.copy(default_icon, icon_dest)
                    self.pack_log(f"✅ 默认图标已复制: {icon_dest}", "success")
            
            config = {
                "app_name": self.pack_app_name.get(),
                "website_dir": "website",
                "html_file": self.pack_html_file.get() if self.pack_html_file.get() else "index.html",
                "width": self.pack_width.get(),
                "height": self.pack_height.get(),
                "custom_title": self.pack_title.get(),
                "title_bar_color": self.pack_title_bar_color.get(),
                "text_color": self.pack_text_color.get(),
                "border_color": self.pack_border_color.get(),
                "show_nav": self.pack_show_nav.get(),
                "force_internal": self.pack_force_internal.get()
            }
            
            config_path = os.path.join(source_output_dir, "config.json")
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            self.pack_log(f"✅ 配置文件已保存: {config_path}", "success")
            
            run_bat_path = os.path.join(source_output_dir, "run.bat")
            run_bat_content = f'''@echo off
chcp 65001 >nul
echo 正在启动 {self.pack_app_name.get()}...
python "{app_name}.py"
if errorlevel 1 (
    echo.
    echo 程序运行出错，请检查是否安装了Python和所需依赖
    echo 需要安装: pip install pywebview
    pause
)
'''
            with open(run_bat_path, 'w', encoding='utf-8') as f:
                f.write(run_bat_content)
            self.pack_log(f"✅ 启动脚本已保存: {run_bat_path}", "success")
            
            readme_path = os.path.join(source_output_dir, "README.txt")
            readme_content = f'''{self.pack_app_name.get()} - 源代码模式
{'=' * 50}

运行方法:
1. 确保已安装 Python 3.8+
2. 安装依赖: pip install pywebview
3. 双击 run.bat 或运行: python {app_name}.py

文件说明:
- {app_name}.py: 主程序
- website/: 网站资源文件
- config.json: 配置文件
- icon.ico: 程序图标
- run.bat: 启动脚本

调试说明:
- 可以直接修改 {app_name}.py 进行调试
- 修改 website/ 目录下的文件会立即生效
- 查看日志文件: log/app_error.log
'''
            with open(readme_path, 'w', encoding='utf-8') as f:
                f.write(readme_content)
            self.pack_log(f"✅ 说明文件已保存: {readme_path}", "success")
            
            self.pack_log("=" * 50, "info")
            self.pack_log(f"✅ 源代码模式打包成功!", "success")
            self.pack_log(f"📁 输出目录: {source_output_dir}", "success")
            
            try:
                if os.name == 'nt':
                    os.startfile(source_output_dir)
                else:
                    subprocess.Popen(['xdg-open', source_output_dir])
                self.pack_log(f"✅ 已打开输出文件夹: {source_output_dir}", "success")
            except Exception as e:
                self.pack_log(f"⚠️ 无法自动打开文件夹: {e}", "warning")
            
            messagebox.showinfo("成功", f"源代码模式打包成功!\n\n输出目录:\n{source_output_dir}\n\n运行方法:\n1. 安装Python和pywebview\n2. 双击 run.bat 启动\n\n已自动打开输出文件夹")
            
        except Exception as e:
            self.pack_log(f"❌ 打包过程出错: {str(e)}", "error")
            self.pack_log(traceback.format_exc(), "error")
            messagebox.showerror("错误", f"打包失败: {str(e)}")
    
    def generate_pack_script(self):
        import base64
        import json
        import textwrap
        
        pack_mode = self.pack_mode.get()
        
        if self.pack_html_file.get():
            html_path = os.path.join(self.pack_website_dir.get(), self.pack_html_file.get())
        else:
            html_path = os.path.join(self.pack_website_dir.get(), "index.html")
            if not os.path.exists(html_path):
                html_files = [f for f in os.listdir(self.pack_website_dir.get()) if f.endswith('.html')]
                if html_files:
                    html_path = os.path.join(self.pack_website_dir.get(), html_files[0])
        
        html_rel_path = os.path.relpath(html_path, self.pack_website_dir.get())
        
        icon_path = None
        if self.pack_icon_path.get() and os.path.exists(self.pack_icon_path.get()):
            icon_path = self.pack_icon_path.get()
        else:
            default_icon = get_resource_path('assets/icon.ico')
            if os.path.exists(default_icon):
                icon_path = default_icon
        
        if pack_mode == "source":
            website_dir_for_config = "website"
        else:
            website_dir_for_config = self.pack_website_dir.get()
        
        config = {
            "app_name": self.pack_app_name.get(),
            "version": self.pack_version.get(),
            "publisher": self.pack_publisher.get(),
            "website_dir": website_dir_for_config,
            "html_file": html_rel_path,
            "width": self.pack_width.get(),
            "height": self.pack_height.get(),
            "custom_title": self.pack_title.get(),
            "title_bar_color": self.pack_title_bar_color.get(),
            "text_color": self.pack_text_color.get(),
            "border_color": self.pack_border_color.get(),
            "show_nav": self.pack_show_nav.get(),
            "force_internal": self.pack_force_internal.get(),
            "icon_path": icon_path,
            "enable_lock": self.pack_enable_lock.get(),
            "lock_password": self.pack_lock_password.get() if self.pack_enable_lock.get() else "",
            "lock_mode": self.pack_lock_mode.get(),
            # 文件锁联系人信息（用于密码忘记时联系）
            "lock_contact_type": self.pack_lock_contact_type.get() if self.pack_enable_lock.get() else "",
            "lock_contact_info": self.pack_lock_contact_info.get() if self.pack_enable_lock.get() else ""
        }
        
        config_json = json.dumps(config)
        config_b64 = base64.b64encode(config_json.encode('utf-8')).decode('utf-8')
        
        inject_js_path = get_resource_path('inject.js')
        if os.path.exists(inject_js_path):
            with open(inject_js_path, 'r', encoding='utf-8') as f:
                inject_js_content = f.read()
        else:
            inject_js_content = ''
        
        inject_js_b64 = base64.b64encode(inject_js_content.encode('utf-8')).decode('utf-8')
        
        script_template = '''
import webview
import json
import base64
import sys
import os
import http.server
import socketserver
import threading
import random
import traceback
import datetime
import hashlib

if getattr(sys, 'frozen', False) or globals().get('__compiled__'):
    base_dir = os.path.dirname(sys.executable)
    log_dir = os.path.join(base_dir, 'log')
    os.makedirs(log_dir, exist_ok=True)
    log_file = open(os.path.join(log_dir, 'app_error.log'), "a", encoding="utf-8")
    sys.stderr = log_file
    sys.stdout = log_file
else:
    log_dir = os.path.join(os.path.dirname(__file__), 'log')
    os.makedirs(log_dir, exist_ok=True)
    log_file = open(os.path.join(log_dir, 'app_error.log'), "a", encoding="utf-8")
    sys.stderr = log_file

def log_exception(exc_type, exc_value, exc_traceback):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file.write(f"\\n[{timestamp}] 未捕获的异常:\\n")
    traceback.print_exception(exc_type, exc_value, exc_traceback, file=log_file)
    log_file.flush()

sys.excepthook = log_exception

CONFIG_B64 = "{config_b64}"
CONFIG = json.loads(base64.b64decode(CONFIG_B64).decode('utf-8'))

INJECT_JS_B64 = "{inject_js_b64}"
INJECT_JS = base64.b64decode(INJECT_JS_B64).decode('utf-8')

def get_machine_id():
    try:
        import platform
        import uuid
        machine_id = platform.node() + str(uuid.getnode())
        return hashlib.sha256(machine_id.encode()).hexdigest()[:16]
    except:
        return "default_machine"

def get_lock_file_path():
    if getattr(sys, 'frozen', False) or globals().get('__compiled__'):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, '.unlock_token')

def check_unlock_token():
    lock_file = get_lock_file_path()
    if os.path.exists(lock_file):
        try:
            with open(lock_file, 'r') as f:
                token = f.read().strip()
            expected_token = hashlib.sha256((CONFIG.get('lock_password', '') + get_machine_id()).encode()).hexdigest()[:16]
            return token == expected_token
        except:
            pass
    return False

def save_unlock_token():
    lock_file = get_lock_file_path()
    try:
        token = hashlib.sha256((CONFIG.get('lock_password', '') + get_machine_id()).encode()).hexdigest()[:16]
        with open(lock_file, 'w') as f:
            f.write(token)
        return True
    except:
        return False

def show_password_dialog():
    import tkinter as tk
    from tkinter import ttk, messagebox
    
    result = [False]
    
    dialog = tk.Tk()
    dialog.title("🔒 程序已锁定")
    # 增加窗口高度以容纳更多内容
    dialog.geometry("400x220")
    dialog.resizable(False, False)
    dialog.configure(bg="#f5f5f5")
    
    dialog.update_idletasks()
    width = dialog.winfo_width()
    height = dialog.winfo_height()
    x = (dialog.winfo_screenwidth() // 2) - (width // 2)
    y = (dialog.winfo_screenheight() // 2) - (height // 2)
    dialog.geometry(f'{{width}}x{{height}}+{{x}}+{{y}}')
    
    dialog.protocol("WM_DELETE_WINDOW", lambda: dialog.destroy())
    
    # 主框架
    frame = tk.Frame(dialog, bg="#f5f5f5", padx=20, pady=15)
    frame.pack(fill="both", expand=True)
    
    # 标题
    title_label = tk.Label(frame, text="🔒 程序已锁定", font=("Microsoft YaHei", 14, "bold"), bg="#f5f5f5", fg="#333")
    title_label.pack(pady=(0, 5))
    
    # 提示文字
    hint_label = tk.Label(frame, text="此程序已设置文件锁，需要输入密码才能访问", 
                          font=("Microsoft YaHei", 9), bg="#f5f5f5", fg="#666")
    hint_label.pack(pady=(0, 10))
    
    # 密码输入区域
    password_frame = tk.Frame(frame, bg="#f5f5f5")
    password_frame.pack(fill="x", pady=5)
    
    tk.Label(password_frame, text="解锁密码:", font=("Microsoft YaHei", 10), bg="#f5f5f5").pack(side="left", padx=(0, 10))
    
    password_var = tk.StringVar()
    password_entry = tk.Entry(password_frame, textvariable=password_var, show="*", 
                              width=20, font=("Microsoft YaHei", 10), relief="solid", bd=1)
    password_entry.pack(side="left", padx=5)
    password_entry.focus()
    
    # 小眼睛按钮 - 显示/隐藏密码
    password_visible = False
    def toggle_password():
        nonlocal password_visible
        password_visible = not password_visible
        if password_visible:
            password_entry.config(show="")
            eye_btn.config(text="🙈")
        else:
            password_entry.config(show="*")
            eye_btn.config(text="👁️")
    
    eye_btn = tk.Button(password_frame, text="👁️", command=toggle_password,
                       font=("Microsoft YaHei", 8), width=2, relief="flat",
                       bg="#f0f0f0", cursor="hand2")
    eye_btn.pack(side="left", padx=2)
    
    # 问号按钮 - 显示联系人信息
    def show_contact_info():
        contact_type = CONFIG.get('lock_contact_type', '')
        contact_info = CONFIG.get('lock_contact_info', '')
        
        if contact_type and contact_info:
            messagebox.showinfo("忘记密码？", 
                f"如果您忘记了密码，请联系程序发布者：\n\n"
                f"{contact_type}: {contact_info}\n\n"
                f"请提供您的机器码以获取帮助。", 
                parent=dialog)
        else:
            messagebox.showinfo("忘记密码？", 
                "程序发布者未设置联系方式。\n\n"
                "请尝试使用您设置密码时使用的常用密码，\n"
                "或联系程序发布者获取帮助。", 
                parent=dialog)
    
    help_btn = tk.Button(password_frame, text="❓", command=show_contact_info,
                        font=("Microsoft YaHei", 8), width=2, relief="flat",
                        bg="#e3f2fd", cursor="hand2", fg="#1976d2")
    help_btn.pack(side="left", padx=5)
    
    def verify():
        entered = password_var.get()
        if entered == CONFIG.get('lock_password', ''):
            result[0] = True
            if CONFIG.get('lock_mode', 'always') == 'once':
                save_unlock_token()
            dialog.destroy()
        else:
            messagebox.showerror("密码错误", "密码不正确，请重试\n\n提示：点击密码框旁边的 ❓ 可查看联系方式", parent=dialog)
            password_var.set("")
            password_entry.focus()
    
    def on_enter(event):
        verify()
    
    password_entry.bind('<Return>', on_enter)
    
    # 按钮区域
    btn_frame = tk.Frame(frame, bg="#f5f5f5")
    btn_frame.pack(pady=15)
    
    unlock_btn = tk.Button(btn_frame, text="🔓 解锁", command=verify, 
                          font=("Microsoft YaHei", 10), width=12,
                          bg="#4caf50", fg="white", relief="flat", cursor="hand2")
    unlock_btn.pack(side="left", padx=10)
    
    exit_btn = tk.Button(btn_frame, text="❌ 退出", command=dialog.destroy, 
                        font=("Microsoft YaHei", 10), width=12,
                        bg="#f44336", fg="white", relief="flat", cursor="hand2")
    exit_btn.pack(side="left", padx=10)
    
    dialog.mainloop()
    return result[0]

class Api:
    def __init__(self, server):
        self.server = server
    
    def minimize(self):
        if webview.windows:
            webview.windows[0].minimize()
    
    def destroy(self):
        if webview.windows:
            webview.windows[0].destroy()
        if self.server:
            self.server.shutdown()

def main():
    try:
        if CONFIG.get('enable_lock', False) and CONFIG.get('lock_password', ''):
            lock_mode = CONFIG.get('lock_mode', 'always')
            if lock_mode == 'always':
                if not show_password_dialog():
                    sys.exit(0)
            elif lock_mode == 'once':
                if not check_unlock_token():
                    if not show_password_dialog():
                        sys.exit(0)
        
        if getattr(sys, 'frozen', False):
            if hasattr(sys, '_MEIPASS'):
                base_dir = sys._MEIPASS
            else:
                base_dir = os.path.dirname(sys.executable)
            website_dir = os.path.join(base_dir, "website")
        elif globals().get('__compiled__'):
            base_dir = os.path.dirname(sys.executable)
            website_dir = os.path.join(base_dir, "website")
        else:
            config_website_dir = CONFIG.get('website_dir', '')
            if config_website_dir and os.path.isabs(config_website_dir):
                website_dir = config_website_dir
            elif config_website_dir:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                website_dir = os.path.join(script_dir, config_website_dir)
            else:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                website_dir = os.path.join(script_dir, "website")
        
        if not os.path.exists(website_dir):
            print(f"错误: 网站目录不存在: {website_dir}")
            return
        
        port = random.randint(8000, 9000)
        html_file = CONFIG.get('html_file', 'index.html')
        
        original_dir = os.getcwd()
        os.chdir(website_dir)
        
        class QuietHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
            def log_message(self, format, *args):
                pass
            
            def guess_type(self, path):
                import mimetypes
                mimetypes.init()
                mtype, encoding = mimetypes.guess_type(path)
                if mtype is None:
                    if path.endswith('.css'):
                        return 'text/css'
                    elif path.endswith('.js'):
                        return 'application/javascript'
                    elif path.endswith('.json'):
                        return 'application/json'
                    elif path.endswith('.woff') or path.endswith('.woff2'):
                        return 'font/woff'
                    elif path.endswith('.ttf'):
                        return 'font/ttf'
                    elif path.endswith('.eot'):
                        return 'application/vnd.ms-fontobject'
                    elif path.endswith('.svg'):
                        return 'image/svg+xml'
                    return 'application/octet-stream'
                return mtype
            
            def end_headers(self):
                path = self.translate_path(self.path)
                if path.endswith('.css'):
                    self.send_header('Content-Type', 'text/css; charset=utf-8')
                elif path.endswith('.js'):
                    self.send_header('Content-Type', 'application/javascript; charset=utf-8')
                super().end_headers()
        
        handler = QuietHTTPRequestHandler
        server = socketserver.TCPServer(("127.0.0.1", port), handler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        
        api = Api(server)
        
        icon_path = CONFIG.get('icon_path')
        window_kwargs = {
            'title': CONFIG.get('custom_title', 'App'),
            'url': f"http://127.0.0.1:{port}/{html_file}",
            'width': CONFIG.get('width', 1200),
            'height': CONFIG.get('height', 850),
            'frameless': False,
            'easy_drag': True,
            'resizable': True
        }
        
        window = webview.create_window(**window_kwargs)
        
        def inject_ui():
            show_nav = CONFIG.get('show_nav', True)
            if show_nav:
                config_js = f"window.__WEBEXE_CONFIG__ = {{\
                    titleBarColor: '{CONFIG.get('title_bar_color', '#2d2d2d')}',\
                    textColor: '{CONFIG.get('text_color', '#ffffff')}',\
                    borderColor: '{CONFIG.get('border_color', '#1a1a1a')}',\
                    showNav: {str(show_nav).lower()},\
                    showWindowControls: false,\
                    forceInternal: {str(CONFIG.get('force_internal', False)).lower()},\
                    customTitle: '{CONFIG.get('custom_title', 'App')}'\
                }};"
                window.evaluate_js(config_js)
                window.evaluate_js(INJECT_JS)
        
        try:
            window.events.loaded += inject_ui
        except AttributeError:
            try:
                window.loaded += inject_ui
            except AttributeError:
                inject_ui()
        
        webview.start(gui='edgechromium', debug=False)
        
        server.shutdown()
        os.chdir(original_dir)
        
    except Exception as e:
        print("="*50)
        print(f"程序发生致命错误，详情已记录到 {os.path.join(log_dir, 'app_error.log')}")
        print("="*50)
        traceback.print_exc()
        import time
        time.sleep(5)
        sys.exit(1)

if __name__ == '__main__':
    main()
'''
        script = textwrap.dedent(script_template).replace('{config_b64}', config_b64).replace('{inject_js_b64}', inject_js_b64)
        return script