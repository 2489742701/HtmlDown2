import os
import re
import time
import threading
import platform
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
from urllib.parse import urljoin, urlparse, unquote
from io import BytesIO
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from PIL import Image
import concurrent.futures
import traceback

class ErrorDialog:
    """可复制错误的弹窗对话框"""
    def __init__(self, parent, title, error_message, error_details=None):
        self.window = tk.Toplevel(parent)
        self.window.title(title)
        self.window.geometry("600x400")
        self.window.resizable(True, True)
        
        # 设置模态
        self.window.transient(parent)
        self.window.grab_set()
        
        # 创建界面
        self.create_widgets(error_message, error_details)
        
        # 居中显示
        self.center_window(parent)
    
    def create_widgets(self, error_message, error_details):
        """创建对话框组件"""
        # 标题
        header_frame = ttk.Frame(self.window, padding=10)
        header_frame.pack(fill="x")
        
        title_label = ttk.Label(header_frame, 
                                text="❌ 发生错误",
                                font=("Microsoft YaHei", 14, "bold"),
                                foreground="#e74c3c")
        title_label.pack()
        
        # 错误信息
        msg_frame = ttk.LabelFrame(self.window, text=" 错误信息 ", padding=10)
        msg_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 简短错误信息
        short_msg = scrolledtext.ScrolledText(msg_frame, height=3, 
                                               font=("Microsoft YaHei", 10),
                                               bg="#f8f9fa",
                                               relief="flat")
        short_msg.pack(fill="x", pady=5)
        short_msg.insert("1.0", error_message)
        short_msg.config(state="disabled")
        
        # 详细错误信息
        if error_details:
            ttk.Label(msg_frame, text="详细错误堆栈:", 
                     font=("Microsoft YaHei", 9, "bold")).pack(anchor="w")
            
            detail_msg = scrolledtext.ScrolledText(msg_frame, height=12, 
                                                   font=("Consolas", 9),
                                                   bg="#2c3e50",
                                                   fg="#ecf0f1",
                                                   relief="flat")
            detail_msg.pack(fill="both", expand=True, pady=5)
            detail_msg.insert("1.0", error_details)
            detail_msg.config(state="disabled")
        
        # 按钮区域
        button_frame = ttk.Frame(self.window, padding=10)
        button_frame.pack(fill="x")
        
        # 复制按钮
        if error_details:
            copy_btn = ttk.Button(button_frame, text="📋 复制错误信息", 
                                 command=self.copy_error)
            copy_btn.pack(side="left", padx=5)
        
        # 关闭按钮
        close_btn = ttk.Button(button_frame, text="关闭", 
                              command=self.window.destroy)
        close_btn.pack(side="right", padx=5)
    
    def copy_error(self):
        """复制错误信息到剪贴板"""
        try:
            error_text = f"错误信息:\n{self.window.winfo_children()[1].winfo_children()[1].get('1.0', 'end')}"
            if len(self.window.winfo_children()[1].winfo_children()) > 3:
                error_text += f"\n\n详细堆栈:\n{self.window.winfo_children()[1].winfo_children()[3].get('1.0', 'end')}"
            
            self.window.clipboard_clear()
            self.window.clipboard_append(error_text)
            messagebox.showinfo("成功", "错误信息已复制到剪贴板！")
        except Exception as e:
            messagebox.showerror("错误", f"复制失败: {e}")
    
    def center_window(self, parent):
        """窗口居中显示"""
        self.window.update_idletasks()
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        x = (self.window.winfo_screenwidth() // 2) - (width // 2)
        y = (self.window.winfo_screenheight() // 2) - (height // 2)
        self.window.geometry(f'{width}x{height}+{x}+{y}')

class WebDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🌐 网页资源离线下载器 - 专业美化版")
        self.root.geometry("800x700")
        self.root.configure(bg='#f5f5f5')
        
        # 设置图标
        icon_path = os.path.join(os.path.dirname(__file__), 'icon.ico')
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception as e:
                print(f"无法加载图标: {e}")
        
        # --- 变量绑定 ---
        self.url_var = tk.StringVar()
        default_dir = os.path.join(os.getcwd(), "downloads")
        self.save_dir_var = tk.StringVar(value=default_dir)
        
        self.depth_var = tk.IntVar(value=0)
        self.mode_var = tk.StringVar(value="full")
        self.convert_img_var = tk.BooleanVar(value=False)
        self.target_fmt_var = tk.StringVar(value="PNG")
        self.filter_video_var = tk.BooleanVar(value=True)
        self.filter_img_var = tk.BooleanVar(value=True)
        self.auto_open_var = tk.BooleanVar(value=True)
        self.path_mode_var = tk.StringVar(value="absolute")
        
        self.is_running = False
        self.current_task_dir = ""

        self.setup_styles()
        self.create_widgets()
        self.update_path_display()
        self.update_depth_value()

    def setup_styles(self):
        """设置现代化样式"""
        style = ttk.Style()
        
        # 配置不同样式
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
        """创建界面组件"""
        # 主容器
        main_container = ttk.Frame(self.root, style="Frame.TFrame")
        main_container.pack(fill="both", expand=True, padx=15, pady=15)
        
        # 标题区域
        self.create_header(main_container)
        
        # 配置区域
        self.create_config_section(main_container)
        
        # 操作区域
        self.create_action_section(main_container)
        
        # 日志区域
        self.create_log_section(main_container)
        
        # 状态栏
        self.create_status_bar(main_container)

    def create_header(self, parent):
        """创建标题区域"""
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

    def create_config_section(self, parent):
        """创建配置区域"""
        # 基础配置卡片
        basic_card = self.create_card(parent, "📋 基础配置")
        self.create_basic_config(basic_card)
        
        # 下载策略卡片
        strategy_card = self.create_card(parent, "⚙️ 下载策略")
        self.create_strategy_config(strategy_card)
        
        # 资源控制卡片
        resource_card = self.create_card(parent, "📁 资源控制")
        self.create_resource_config(resource_card)

    def create_card(self, parent, title):
        """创建卡片式容器"""
        card = ttk.LabelFrame(parent, text=f" {title} ", 
                             padding=15,
                             style="Frame.TFrame")
        card.pack(fill="x", pady=8)
        return card

    def create_basic_config(self, parent):
        """基础配置区域"""
        # 网址输入行
        url_row = ttk.Frame(parent)
        url_row.pack(fill="x", pady=5)
        
        ttk.Label(url_row, text="目标网址:", style="Bold.TLabel").pack(side="left")
        url_entry = ttk.Entry(url_row, textvariable=self.url_var, width=60, font=("Microsoft YaHei", 9))
        url_entry.pack(side="left", padx=10)
        ttk.Label(url_row, text="(例如: https://example.com)", foreground="#95a5a6").pack(side="left")
        
        # 保存路径行
        path_row = ttk.Frame(parent)
        path_row.pack(fill="x", pady=5)
        
        ttk.Label(path_row, text="保存路径:", style="Bold.TLabel").pack(side="left")
        path_entry = ttk.Entry(path_row, textvariable=self.save_dir_var, width=60, font=("Microsoft YaHei", 9))
        path_entry.pack(side="left", padx=10)
        browse_btn = ttk.Button(path_row, text="📁 浏览", command=self.select_folder)
        browse_btn.pack(side="left", padx=5)
        open_dir_btn = ttk.Button(path_row, text="📂 打开", command=self.open_current_dir)
        open_dir_btn.pack(side="left", padx=2)
        
        # 路径模式选择
        path_mode_frame = ttk.Frame(parent)
        path_mode_frame.pack(fill="x", pady=5)
        
        ttk.Label(path_mode_frame, text="路径模式:", style="Bold.TLabel").pack(side="left")
        
        path_mode_options = ttk.Frame(path_mode_frame)
        path_mode_options.pack(side="left", padx=15)
        
        ttk.Radiobutton(path_mode_options, text="📂 绝对路径", 
                       variable=self.path_mode_var, value="absolute",
                       command=self.update_path_display).pack(side="left", padx=10)
        ttk.Radiobutton(path_mode_options, text="📁 相对路径", 
                       variable=self.path_mode_var, value="relative",
                       command=self.update_path_display).pack(side="left")
        
        path_info = ttk.Label(path_mode_frame, 
                              text="(相对路径相对于程序所在目录)",
                              foreground="#95a5a6")
        path_info.pack(side="left", padx=10)

    def create_strategy_config(self, parent):
        """下载策略配置"""
        # 下载模式选择
        mode_frame = ttk.Frame(parent)
        mode_frame.pack(fill="x", pady=8)
        
        ttk.Label(mode_frame, text="下载模式:", style="Bold.TLabel").pack(side="left")
        
        mode_options = ttk.Frame(mode_frame)
        mode_options.pack(side="left", padx=15)
        
        ttk.Radiobutton(mode_options, text="🌐 整页离线 (HTML+资源)", 
                       variable=self.mode_var, value="full").pack(side="left", padx=10)
        ttk.Radiobutton(mode_options, text="📁 仅提取素材", 
                       variable=self.mode_var, value="media_only").pack(side="left")
        
        # 爬取深度设置
        depth_frame = ttk.Frame(parent)
        depth_frame.pack(fill="x", pady=8)
        
        ttk.Label(depth_frame, text="爬取深度:", style="Bold.TLabel").pack(side="left")
        
        depth_control = ttk.Frame(depth_frame)
        depth_control.pack(side="left", padx=15)
        
        self.depth_mode_var = tk.StringVar(value="page_only")
        
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
        
        # 自定义深度输入框
        self.custom_depth_var = tk.IntVar(value=5)
        self.custom_depth_spin = ttk.Spinbox(depth_control, from_=0, to=10, 
                                            textvariable=self.custom_depth_var, 
                                            width=3,
                                            state="disabled")
        self.custom_depth_spin.pack(side="left", padx=5)
        self.custom_depth_spin.bind('<KeyRelease>', lambda e: self.depth_var.set(self.custom_depth_var.get()))

    def create_resource_config(self, parent):
        """资源控制配置"""
        # 资源类型选择
        resource_frame = ttk.Frame(parent)
        resource_frame.pack(fill="x", pady=8)
        
        ttk.Label(resource_frame, text="下载内容:", style="Bold.TLabel").pack(side="left")
        
        resource_options = ttk.Frame(resource_frame)
        resource_options.pack(side="left", padx=15)
        
        ttk.Checkbutton(resource_options, text="🖼️ 图片", 
                       variable=self.filter_img_var).pack(side="left", padx=15)
        ttk.Checkbutton(resource_options, text="🎬 视频", 
                       variable=self.filter_video_var).pack(side="left", padx=15)
        
        # 图片转换设置
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

    def create_action_section(self, parent):
        """创建操作区域"""
        action_card = ttk.LabelFrame(parent, text=" 🚀 操作控制 ", padding=15)
        action_card.pack(fill="x", pady=10)
        
        # 选项和按钮行
        action_row = ttk.Frame(action_card)
        action_row.pack(fill="x")
        
        # 左侧选项
        options_frame = ttk.Frame(action_row)
        options_frame.pack(side="left")
        
        ttk.Checkbutton(options_frame, text="📂 下载后自动打开文件夹", 
                       variable=self.auto_open_var).pack(side="left")
        
        # 右侧按钮
        buttons_frame = ttk.Frame(action_row)
        buttons_frame.pack(side="right")
        
        self.btn_start = ttk.Button(buttons_frame, 
                                   text="🚀 开始下载", 
                                   command=self.start_thread,
                                   style="Success.TButton")
        self.btn_start.pack(side="left", padx=5)
        
        ttk.Button(buttons_frame, 
                  text="🗑️ 清空日志", 
                  command=self.clear_log).pack(side="left")

    def create_log_section(self, parent):
        """创建日志区域"""
        log_card = ttk.LabelFrame(parent, text=" 📝 下载日志 ", padding=10)
        log_card.pack(fill="both", expand=True, pady=10)
        
        # 日志区域
        self.log_area = scrolledtext.ScrolledText(log_card, 
                                                 height=15, 
                                                 state='disabled', 
                                                 font=("Consolas", 9), 
                                                 bg="#f8f9fa",
                                                 relief="flat")
        self.log_area.pack(fill="both", expand=True)
        
        # 添加一些样式标签
        self.log_area.tag_config("success", foreground="#27ae60")
        self.log_area.tag_config("error", foreground="#e74c3c")
        self.log_area.tag_config("warning", foreground="#f39c12")
        self.log_area.tag_config("info", foreground="#3498db")

    def create_status_bar(self, parent):
        """创建状态栏"""
        status_frame = ttk.Frame(parent, relief="sunken")
        status_frame.pack(fill="x", side="bottom", pady=(10, 0))
        
        self.status_var = tk.StringVar(value="🟢 就绪 - 请输入网址开始下载")
        status_label = ttk.Label(status_frame, 
                                textvariable=self.status_var,
                                relief="sunken", 
                                anchor="w",
                                font=("Microsoft YaHei", 9),
                                background="#ecf0f1")
        status_label.pack(fill="x", padx=1, pady=1)

    def select_folder(self):
        """选择保存文件夹"""
        folder = filedialog.askdirectory(initialdir=self.save_dir_var.get())
        if folder:
            self.save_dir_var.set(folder)
            self.update_path_display()
            self.log("📁 保存路径已更新", "success")
    
    def open_current_dir(self):
        """打开当前设置的保存目录"""
        path = self.get_absolute_path()
        if os.path.exists(path):
            self.open_file_explorer(path)
        else:
            messagebox.showwarning("提示", "目录不存在，请先选择有效的保存路径")
    
    def update_path_display(self):
        """根据路径模式更新路径显示"""
        current_path = self.save_dir_var.get()
        if not current_path:
            return
            
        if self.path_mode_var.get() == "relative":
            relative_path = self.get_relative_path(current_path)
            if relative_path != current_path:
                self.save_dir_var.set(relative_path)
        else:
            absolute_path = self.get_absolute_path()
            self.save_dir_var.set(absolute_path)
    
    def get_absolute_path(self):
        """获取绝对路径"""
        path = self.save_dir_var.get()
        if not path:
            return os.path.join(os.getcwd(), "downloads")
        
        if os.path.isabs(path):
            return path
        else:
            return os.path.abspath(os.path.join(os.getcwd(), path))
    
    def get_relative_path(self, path):
        """获取相对路径（相对于程序所在目录）"""
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
        """根据选择的模式更新深度值"""
        mode = self.depth_mode_var.get()
        
        if mode == "page_only":
            self.depth_var.set(0)
            self.custom_depth_spin.config(state="disabled")
        elif mode == "page_next":
            self.depth_var.set(1)
            self.custom_depth_spin.config(state="disabled")
        elif mode == "page_next2":
            self.depth_var.set(2)
            self.custom_depth_spin.config(state="disabled")
        elif mode == "custom":
            self.custom_depth_spin.config(state="normal")
            self.depth_var.set(self.custom_depth_var.get())

    def clear_log(self):
        """清空日志"""
        self.log_area.config(state='normal')
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state='disabled')
        self.log("📝 日志已清空", "info")

    def log(self, msg, tag=None):
        """添加日志"""
        self.log_area.config(state='normal')
        timestamp = time.strftime("%H:%M:%S")
        self.log_area.insert(tk.END, f"[{timestamp}] {msg}\n", tag)
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def open_file_explorer(self, path):
        """跨平台打开文件夹"""
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
        """启动下载线程"""
        if self.is_running:
            messagebox.showwarning("提示", "当前有任务正在运行中！")
            return
        
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("提示", "请输入有效的网址！")
            return
        
        # 验证网址格式
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
            self.url_var.set(url)
        
        # 创建任务目录
        domain_name = urlparse(url).netloc.replace("www.", "")
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        safe_name = f"{domain_name}_{timestamp}"
        self.current_task_dir = os.path.join(self.get_absolute_path(), safe_name)
        
        self.is_running = True
        self.btn_start.config(state="disabled", text="⏳ 下载中...")
        self.clear_log()
        self.status_var.set("🟡 正在下载中...")
        
        threading.Thread(target=self.run_logic, daemon=True).start()

    def run_logic(self):
        """运行下载逻辑"""
        try:
            depth_mode = self.depth_mode_var.get()
            depth_value = self.depth_var.get()
            
            depth_description = {
                "page_only": "仅本页",
                "page_next": "本页+下页",
                "page_next2": "本页+下2页",
                "custom": f"自定义({depth_value}层)"
            }.get(depth_mode, f"深度{depth_value}")
            
            params = {
                'url': self.url_var.get(),
                'output_dir': self.current_task_dir,
                'depth': self.depth_var.get(),
                'mode': self.mode_var.get(),
                'filter_img': self.filter_img_var.get(),
                'filter_video': self.filter_video_var.get(),
                'convert_img': self.convert_img_var.get(),
                'target_fmt': self.target_fmt_var.get()
            }
            
            self.root.after(0, lambda: self.log(f"📂 创建任务目录: {self.current_task_dir}", "info"))
            self.root.after(0, lambda: self.log(f"📊 爬取深度: {depth_description}", "info"))
            downloader = CoreDownloader(self, params)
            downloader.start()
            
            self.root.after(0, self.on_finish_success)
            
        except Exception as e:
            error_msg = f"下载过程中发生错误: {str(e)}"
            error_details = traceback.format_exc()
            
            # 在日志中显示错误
            self.root.after(0, lambda: self.log(f"❌ 发生错误: {str(e)}", "error"))
            self.root.after(0, lambda: self.status_var.set("🔴 下载失败"))
            
            # 弹出错误对话框
            self.root.after(0, lambda: ErrorDialog(self.root, "下载错误", error_msg, error_details))
        finally:
            self.is_running = False
            self.root.after(0, lambda: self.btn_start.config(state="normal", text="🚀 开始下载"))

    def on_finish_success(self):
        """下载完成处理"""
        self.log("\n✨ ----------- 任务完成 -----------", "success")
        self.status_var.set("🟢 下载完成")
        
        # 自动打开文件夹
        if self.auto_open_var.get():
            self.open_file_explorer(self.current_task_dir)

# ================= 核心下载逻辑 =================

class CoreDownloader:
    def __init__(self, gui, params):
        self.gui = gui
        self.start_url = params['url']
        self.output_dir = params['output_dir']
        self.max_depth = params['depth']
        self.mode = params['mode']
        self.convert_images = params['convert_img']
        self.target_img_fmt = params['target_fmt']
        self.allow_img = params['filter_img']
        self.allow_video = params['filter_video']
        
        self.ua = UserAgent()
        self.visited_urls = set()
        
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        self.media_exts = {
            'img': ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'],
            'video': ['.mp4', '.webm', '.mkv', '.avi', '.mov']
        }

    def log(self, msg, tag="info"):
        self.gui.root.after(0, lambda: self.gui.log(msg, tag))

    def get_headers(self):
        return {'User-Agent': self.ua.random, 'Referer': self.start_url}

    def safe_filename(self, url):
        path = urlparse(url).path
        filename = unquote(os.path.basename(path))
        if not filename or '.' not in filename:
            filename = f"file_{int(time.time())}.dat"
        filename = re.sub(r'[\\/*?:"<>|]', "", filename)
        if len(filename) > 100: filename = filename[-50:]
        return filename

    def download_resource(self, url, sub_folder):
        try:
            is_video = any(url.lower().endswith(ext) for ext in self.media_exts['video'])
            is_img = any(url.lower().endswith(ext) for ext in self.media_exts['img'])
            
            if is_video and not self.allow_video: return None
            if is_img and not self.allow_img: return None
            if not is_video and not is_img and self.mode == 'media_only': return None

            folder_path = os.path.join(self.output_dir, sub_folder)
            if not os.path.exists(folder_path): os.makedirs(folder_path)
            
            filename = self.safe_filename(url)
            local_path = os.path.join(folder_path, filename)
            relative_path = f"{sub_folder}/{filename}"

            if os.path.exists(local_path): return relative_path

            self.log(f"   ⬇️ {filename}", "info")
            resp = requests.get(url, headers=self.get_headers(), stream=True, timeout=10, verify=False)
            
            if resp.status_code == 200:
                if is_img and self.convert_images:
                    try:
                        img = Image.open(BytesIO(resp.content))
                        fname_no_ext = os.path.splitext(filename)[0]
                        new_fname = f"{fname_no_ext}.{self.target_img_fmt.lower()}"
                        local_path = os.path.join(folder_path, new_fname)
                        if img.mode in ("RGBA", "P"): img = img.convert("RGB")
                        img.save(local_path, self.target_img_fmt)
                        return f"{sub_folder}/{new_fname}"
                    except Exception as img_error:
                        self.log(f"   ⚠️ 图片转换失败: {img_error}", "warning")

                with open(local_path, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                return relative_path
            else:
                self.log(f"   ⚠️ 下载失败: HTTP {resp.status_code}", "warning")
        except requests.exceptions.ConnectionError as e:
            self.log(f"   ⚠️ 连接错误: {url}", "warning")
        except requests.exceptions.Timeout as e:
            self.log(f"   ⚠️ 超时: {url}", "warning")
        except Exception as e:
            self.log(f"   ⚠️ 下载错误: {str(e)}", "warning")
        return None

    def post_process_html(self, html_content, base_url):
        """后处理HTML，修复脚本和样式引用"""
        try:
            soup = BeautifulSoup(html_content, 'lxml')
            
            # 处理script标签
            for script in soup.find_all('script'):
                src = script.get('src')
                if src and not src.startswith('data:'):
                    abs_url = urljoin(base_url, src)
                    script_filename = self.safe_filename(abs_url)
                    script_path = os.path.join(self.output_dir, 'js', script_filename)
                    
                    if os.path.exists(script_path):
                        script['src'] = f"js/{script_filename}"
                        self.log(f"   🔧 修复脚本引用: {script_filename}", "info")
                    else:
                        # 尝试下载缺失的脚本
                        rel_path = self.download_resource(abs_url, 'js')
                        if rel_path:
                            script['src'] = rel_path
                            self.log(f"   ⬇️ 补充下载脚本: {script_filename}", "info")
            
            # 处理link标签（CSS）
            for link in soup.find_all('link'):
                href = link.get('href')
                if href and not href.startswith('data:'):
                    abs_url = urljoin(base_url, href)
                    link_filename = self.safe_filename(abs_url)
                    link_path = os.path.join(self.output_dir, 'css', link_filename)
                    
                    if os.path.exists(link_path):
                        link['href'] = f"css/{link_filename}"
                        self.log(f"   🔧 修复样式引用: {link_filename}", "info")
                    else:
                        # 尝试下载缺失的样式
                        rel_path = self.download_resource(abs_url, 'css')
                        if rel_path:
                            link['href'] = rel_path
                            self.log(f"   ⬇️ 补充下载样式: {link_filename}", "info")
            
            # 处理style标签中的url()引用
            for style in soup.find_all('style'):
                if style.string:
                    style_content = style.string
                    # 替换url()中的相对路径
                    import re
                    def replace_url(match):
                        url = match.group(1)
                        if url.startswith('data:'):
                            return match.group(0)
                        abs_url = urljoin(base_url, url)
                        filename = self.safe_filename(abs_url)
                        # 尝试下载资源
                        rel_path = self.download_resource(abs_url, 'images')
                        if rel_path:
                            return f'url({rel_path})'
                        return match.group(0)
                    
                    style_content = re.sub(r'url\(["\']?([^)"\']+)["\']?\)', replace_url, style_content)
                    style.string = style_content
            
            return str(soup)
        except Exception as e:
            self.log(f"   ⚠️ HTML后处理失败: {e}", "warning")
            return html_content

    def process_page(self, url, depth):
        if url in self.visited_urls or depth > self.max_depth: return
        self.visited_urls.add(url)
        
        self.log(f"🌍 分析页面 [深度{depth}]: {url}", "info")
        try:
            requests.packages.urllib3.disable_warnings()
            resp = requests.get(url, headers=self.get_headers(), verify=False, timeout=10)
            if resp.status_code != 200: return
            
            soup = BeautifulSoup(resp.text, 'lxml')
            
            tags_to_find = [
                ('img', 'src', 'images'),
                ('video', 'src', 'videos'),
                ('source', 'src', 'videos')
            ]
            if self.mode == 'full':
                tags_to_find.extend([('script', 'src', 'js'), ('link', 'href', 'css')])

            futures = []
            with concurrent.futures.ThreadPoolExecutor(max_workers=6) as executor:
                for tag_name, attr, folder in tags_to_find:
                    for tag in soup.find_all(tag_name):
                        val = tag.get(attr)
                        if val and not val.startswith('data:'):
                            abs_url = urljoin(url, val)
                            f = executor.submit(self.download_resource, abs_url, folder)
                            futures.append((tag, attr, f))

                if self.mode == 'full':
                    for tag, attr, f in futures:
                        rel_path = f.result()
                        if rel_path: tag[attr] = rel_path
                    
                    # 后处理HTML，修复脚本和样式引用
                    processed_html = self.post_process_html(str(soup), url)
                    
                    page_name = self.safe_filename(url)
                    if not page_name.endswith('.html'): page_name += '.html'
                    with open(os.path.join(self.output_dir, page_name), 'w', encoding='utf-8') as f:
                        f.write(processed_html)
                    self.log(f"✅ 保存页面: {page_name}", "success")

            if depth < self.max_depth:
                links = soup.find_all('a', href=True)
                for link in links:
                    next_url = urljoin(url, link['href'])
                    if urlparse(next_url).netloc == urlparse(self.start_url).netloc:
                        self.process_page(next_url, depth + 1)

        except Exception as e:
            error_msg = f"页面处理错误: {str(e)}"
            error_details = traceback.format_exc()
            self.log(f"❌ 页面错误: {e}", "error")
            
            # 如果是严重错误，弹出对话框
            if "ConnectionError" in str(e) or "Timeout" in str(e):
                self.gui.root.after(0, lambda: ErrorDialog(self.gui.root, "网络错误", error_msg, error_details))

    def start(self):
        self.process_page(self.start_url, 0)

# ================= 启动 =================

if __name__ == "__main__":
    root = tk.Tk()
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    
    app = WebDownloaderGUI(root)
    root.mainloop()