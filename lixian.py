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

class WebDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("网页资源离线下载器 (Python专业版)")
        self.root.geometry("720x600")
        
        # --- 变量绑定 ---
        self.url_var = tk.StringVar()
        # 默认保存到当前目录下的 downloads 文件夹
        default_dir = os.path.join(os.getcwd(), "downloads")
        self.save_dir_var = tk.StringVar(value=default_dir)
        
        self.depth_var = tk.IntVar(value=0)
        self.mode_var = tk.StringVar(value="full")
        self.convert_img_var = tk.BooleanVar(value=False)
        self.target_fmt_var = tk.StringVar(value="PNG")
        self.filter_video_var = tk.BooleanVar(value=True)
        self.filter_img_var = tk.BooleanVar(value=True)
        
        # 新增：是否自动打开文件夹
        self.auto_open_var = tk.BooleanVar(value=True)
        
        self.is_running = False
        self.current_task_dir = "" # 记录当前任务的具体保存路径

        self.create_widgets()

    def create_widgets(self):
        # 样式调整
        style = ttk.Style()
        style.configure("Bold.TLabel", font=("Microsoft YaHei", 9, "bold"))

        # --- 1. 基础设置区 ---
        input_frame = ttk.LabelFrame(self.root, text=" 基础设置 ", padding=10)
        input_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(input_frame, text="目标网址:", style="Bold.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Entry(input_frame, textvariable=self.url_var, width=55).grid(row=0, column=1, padx=5)
        ttk.Label(input_frame, text="(例如 https://...)").grid(row=0, column=2)

        ttk.Label(input_frame, text="保存根目录:", style="Bold.TLabel").grid(row=1, column=0, sticky="w", pady=5)
        ttk.Entry(input_frame, textvariable=self.save_dir_var, width=55).grid(row=1, column=1, padx=5)
        ttk.Button(input_frame, text="浏览...", command=self.select_folder).grid(row=1, column=2)

        # --- 2. 高级策略区 ---
        opts_frame = ttk.LabelFrame(self.root, text=" 下载策略 ", padding=10)
        opts_frame.pack(fill="x", padx=10, pady=5)

        # 模式
        ttk.Label(opts_frame, text="下载模式:").grid(row=0, column=0, sticky="w")
        rb1 = ttk.Radiobutton(opts_frame, text="整页离线 (资源+HTML修正)", variable=self.mode_var, value="full")
        rb1.grid(row=0, column=1, sticky="w")
        rb2 = ttk.Radiobutton(opts_frame, text="仅提取素材 (不存HTML)", variable=self.mode_var, value="media_only")
        rb2.grid(row=0, column=2, sticky="w")

        # 深度
        ttk.Label(opts_frame, text="爬取深度:").grid(row=1, column=0, sticky="w", pady=8)
        depth_frame = ttk.Frame(opts_frame)
        depth_frame.grid(row=1, column=1, columnspan=2, sticky="w")
        ttk.Spinbox(depth_frame, from_=0, to=5, textvariable=self.depth_var, width=5).pack(side="left")
        ttk.Label(depth_frame, text=" (0=仅当前页, 1=抓取当前页及下一层链接)", foreground="gray").pack(side="left", padx=5)

        # 资源与转换
        ttk.Label(opts_frame, text="资源控制:").grid(row=2, column=0, sticky="w", pady=5)
        res_frame = ttk.Frame(opts_frame)
        res_frame.grid(row=2, column=1, columnspan=3, sticky="w")
        
        ttk.Checkbutton(res_frame, text="下载图片", variable=self.filter_img_var).pack(side="left", padx=2)
        ttk.Checkbutton(res_frame, text="下载视频", variable=self.filter_video_var).pack(side="left", padx=10)
        
        ttk.Separator(res_frame, orient="vertical").pack(side="left", fill="y", padx=10)
        
        ttk.Checkbutton(res_frame, text="图片转格式 ->", variable=self.convert_img_var).pack(side="left")
        ttk.Combobox(res_frame, textvariable=self.target_fmt_var, values=["PNG", "JPG"], width=5, state="readonly").pack(side="left", padx=2)

        # --- 3. 操作区 ---
        action_frame = ttk.Frame(self.root, padding=10)
        action_frame.pack(fill="x")
        
        # 自动打开文件夹选项
        ttk.Checkbutton(action_frame, text="下载完成后自动打开文件夹", variable=self.auto_open_var).pack(side="left")
        
        self.btn_start = ttk.Button(action_frame, text="🚀 开始下载", command=self.start_thread)
        self.btn_start.pack(side="right", padx=5, ipadx=20, ipady=5)

        # --- 4. 日志区 ---
        self.log_area = scrolledtext.ScrolledText(self.root, height=12, state='disabled', font=("Consolas", 9), bg="#f0f0f0")
        self.log_area.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        ttk.Label(self.root, textvariable=self.status_var, relief="sunken", anchor="w").pack(fill="x")

    def select_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.save_dir_var.set(folder)

    def log(self, msg, tag=None):
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, msg + "\n", tag)
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def open_file_explorer(self, path):
        """跨平台打开文件夹"""
        try:
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin": # macOS
                subprocess.Popen(["open", path])
            else: # Linux
                subprocess.Popen(["xdg-open", path])
            self.log(f"📂 已打开目录: {path}")
        except Exception as e:
            self.log(f"⚠️ 无法自动打开目录: {e}")

    def start_thread(self):
        if self.is_running: return
        
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("提示", "请输入有效的网址！")
            return
        
        # 创建一个独立的任务文件夹，避免混淆
        domain_name = urlparse(url).netloc.replace("www.", "")
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        safe_name = f"{domain_name}_{timestamp}"
        self.current_task_dir = os.path.join(self.save_dir_var.get(), safe_name)
        
        self.is_running = True
        self.btn_start.config(state="disabled", text="下载中...")
        self.log_area.config(state='normal', bg="white")
        self.log_area.delete(1.0, tk.END)
        self.log_area.config(state='disabled')
        self.status_var.set(f"正在下载: {url}")
        
        threading.Thread(target=self.run_logic, daemon=True).start()

    def run_logic(self):
        try:
            params = {
                'url': self.url_var.get(),
                'output_dir': self.current_task_dir, # 使用生成的独立目录
                'depth': self.depth_var.get(),
                'mode': self.mode_var.get(),
                'filter_img': self.filter_img_var.get(),
                'filter_video': self.filter_video_var.get(),
                'convert_img': self.convert_img_var.get(),
                'target_fmt': self.target_fmt_var.get()
            }
            
            self.root.after(0, lambda: self.log(f"📂 创建任务目录: {self.current_task_dir}"))
            downloader = CoreDownloader(self, params)
            downloader.start()
            
            self.root.after(0, self.on_finish_success)
            
        except Exception as e:
            self.root.after(0, lambda: self.log(f"❌ 发生错误: {str(e)}", "error"))
            self.root.after(0, lambda: self.status_var.set("下载失败"))
        finally:
            self.is_running = False
            self.root.after(0, lambda: self.btn_start.config(state="normal", text="🚀 开始下载"))

    def on_finish_success(self):
        self.log("\n✨ ----------- 任务完成 -----------")
        self.status_var.set("完成")
        
        # 弹窗提示
        # messagebox.showinfo("完成", "所有文件下载完毕！") 
        
        # 自动打开文件夹
        if self.auto_open_var.get():
            self.open_file_explorer(self.current_task_dir)

# ================= 核心下载逻辑 (保持不变) =================

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

    def log(self, msg):
        self.gui.root.after(0, lambda: self.gui.log(msg))

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

            self.log(f"   ⬇️ {filename}")
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
                    except:
                        pass 

                with open(local_path, 'wb') as f:
                    for chunk in resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                return relative_path
        except Exception:
            pass
        return None

    def process_page(self, url, depth):
        if url in self.visited_urls or depth > self.max_depth: return
        self.visited_urls.add(url)
        
        self.log(f"🌍 分析页面 [深度{depth}]: {url}")
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
                    
                    page_name = self.safe_filename(url)
                    if not page_name.endswith('.html'): page_name += '.html'
                    with open(os.path.join(self.output_dir, page_name), 'w', encoding='utf-8') as f:
                        f.write(str(soup))
                    self.log(f"✅ 保存页面: {page_name}")

            if depth < self.max_depth:
                links = soup.find_all('a', href=True)
                for link in links:
                    next_url = urljoin(url, link['href'])
                    if urlparse(next_url).netloc == urlparse(self.start_url).netloc:
                        self.process_page(next_url, depth + 1)

        except Exception as e:
            self.log(f"❌ 页面错误: {e}")

    def start(self):
        self.process_page(self.start_url, 0)

# ================= 启动 =================

if __name__ == "__main__":
    root = tk.Tk()
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1) # 开启高分屏支持
    except:
        pass
    app = WebDownloaderGUI(root)
    root.mainloop()